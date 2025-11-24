from django.apps import apps
from django.db.models import Q, Count, Sum, Avg, Min, Max
from django.core.exceptions import ValidationError
from functools import reduce
import operator
from bs4 import BeautifulSoup
import json

# mapa de funções de agregação permitidas 
MAPA_AGREGACAO = {
    'Count': Count,
    'Sum': Sum, 
    'Avg': Avg, 
    'Min': Min, 
    'Max': Max
}

class ConstrutorConsulta:
    def __init__(self, esquema, dados_entrada):
        """
        :param esquema: Dicionário representando o esquema do BD
        :param dados_entrada: JSON especificando os metadados da consulta
        """
        self.esquema = esquema
        self.dados_entrada = dados_entrada
        
        # verifica se a tabela raiz existe no esquema
        self.nome_entidade_raiz = dados_entrada.get('fonte_principal')
        if self.nome_entidade_raiz not in self.esquema:
            raise ValidationError(f"Entidade raiz '{self.nome_entidade_raiz}' inválida.")
            
        self.config_raiz = self.esquema[self.nome_entidade_raiz]
        
        # carrega o modelo dinamicamente
        try:
            self.modelo_classe = apps.get_model(self.config_raiz['app_model'])
        except LookupError:
            raise ValidationError(f"Modelo do Django não encontrado: {self.config_raiz['app_model']}")


    def _buscar_na_lista(self, lista, chave_identificadora, valor_buscado):
        """
        Função auxiliar para encontrar um dicionário dentro de uma lista.
        Ex: Procura em 'conexoes' onde 'campo_relacao' == 'unidade'
        """
        for item in lista:
            if item.get(chave_identificadora) == valor_buscado:
                return item
        return None


    def _resolver_caminho(self, caminho_str):
        """
        Traduz o caminho do JSON (ex: "solicitante__usuario__email") 
        para o caminho do Django ORM, validando cada passo no esquema.
        
        Retorna: (caminho_orm, tipo_dado)
        """
        partes = caminho_str.split('__')
        entidade_atual = self.nome_entidade_raiz
        partes_caminho_orm = []
        
        # 1. Navegação pelas relações (todas as partes exceto a última)
        for i in range(len(partes) - 1):
            campo_relacao = partes[i]
            config_entidade = self.esquema.get(entidade_atual)
            
            # verifica se a conexão existe no esquema
            lista_conexoes = config_entidade.get('conexoes', [])
            
            conexao = self._buscar_na_lista(lista_conexoes, 'campo_relacao', campo_relacao)

            if not conexao:
                raise ValidationError(
                    f"Relação '{campo_relacao}' não existe ou não é permitida em '{entidade_atual}'."
                )
            
            # adiciona o caminho real (ex: 'solicitante_id' ou 'atendimentos_set')
            partes_caminho_orm.append(conexao['campo_relacao'])
            # avança para a próxima entidade (muda o contexto)
            entidade_atual = conexao['model_destino']
            
        # 2. Resolução do campo final (última parte)
        nome_campo = partes[-1]
        config_entidade_final = self.esquema.get(entidade_atual)
        lista_campos = config_entidade_final.get('campos', [])
        
        config_campo = self._buscar_na_lista(lista_campos, 'valor', nome_campo)
        
        if not config_campo:
            raise ValidationError(
                f"Campo '{nome_campo}' não encontrado na entidade '{entidade_atual}'."
            )
            
        partes_caminho_orm.append(config_campo['valor'])
        
        # retorna o caminho unido (ex: solicitante__email), o tipo (ex: string)
        return "__".join(partes_caminho_orm), config_campo['tipo']


    def _construir_filtros(self):
        """Constrói a lista de objetos Q() para usar no .filter() do Django"""
        lista_q = []
        
        for filtro in self.dados_entrada.get('filtros', []):
            # 1. resolve o caminho (Validação de Segurança)
            caminho_orm, tipo_campo = self._resolver_caminho(filtro['campo'])
            
            sufixo_operador = filtro['operador']
            valor = filtro['valor']
            
            # 2. tratamento de tipos específicos
            if tipo_campo == 'boolean' and isinstance(valor, str):
                valor = valor.lower() == 'true'
            
            # 3. monta o lookup do Django (ex: base__cidade__icontains)
            consulta_orm = f"{caminho_orm}__{sufixo_operador}"
            lista_q.append(Q(**{consulta_orm: valor}))
            
        print(lista_q)
        return lista_q


    def executar(self):
        """
        Método principal que gera e executa a consulta.
        Retorna uma lista de dicionários formatados.
        """
        queryset = self.modelo_classe.objects.all()
        
        filtros = self._construir_filtros()
        if filtros:
            # combina todos os filtros com AND
            queryset = queryset.filter(reduce(operator.and_, filtros))
            print("queryset 1:", queryset.query)
            
        # 2. Prepara colunas
        dimensoes = []   # para o Group By (.values)
        metricas = {}    # para agregações (.annotate)
        mapa_saida = []  # para formatar o resultado final e manter a ordem
        
        for coluna in self.dados_entrada.get('colunas', []):
            caminho_orm, tipo_campo = self._resolver_caminho(coluna['campo'])
            rotulo = coluna.get('label', coluna['campo'])
            func_agregacao = coluna.get('agregacao')
            
            if func_agregacao:
                if func_agregacao not in MAPA_AGREGACAO:
                    raise ValidationError(f"Função de agregação inválida: {func_agregacao}")
                
                # alias único para o Django não se perder
                # Ex: solicitante__id vira solicitante_id_count
                apelido = f"{caminho_orm.replace('__', '_')}_{func_agregacao.lower()}"
                
                # cria a métrica (ex: Count('id'))
                metricas[apelido] = MAPA_AGREGACAO[func_agregacao](caminho_orm)
                
                mapa_saida.append({
                    'chave_db': apelido, 
                    'rotulo': rotulo, 
                    'tipo': 'number' # agregações são sempre numéricas
                })
            else:
                # é uma dimensão (agrupamento)
                dimensoes.append(caminho_orm)
                mapa_saida.append({
                    'chave_db': caminho_orm, 
                    'rotulo': rotulo, 
                    'tipo': tipo_campo
                })
        print("mapa_saida:", mapa_saida)
        # 3. Constrói a QuerySet na ordem correta
        # ORDEM CRÍTICA: values() -> annotate() -> values()
        
        if dimensoes:
            print("dimensões:", dimensoes)
            # define os campos para o GROUP BY (agrupamento)
            queryset = queryset.values(*dimensoes)
            print("queryset 2:", queryset.query)
        
        if metricas:
            print("metricas", metricas)
            # calcula as funções de agregação para cada grupo
            queryset = queryset.annotate(**metricas)
            print("queryset 3:", queryset.query)
            
        # limpa o SELECT final para trazer apenas o solicitado
        chaves_select_final = dimensoes + list(metricas.keys())
        if chaves_select_final:
            queryset = queryset.values(*chaves_select_final)
            print("queryset 4:", queryset.query)

        # 4. Formatação dos dados
        # transforma o resultado bruto do banco no formato legível (dict)
        dados_formatados = []
        
        for linha in queryset:
            nova_linha = {}
            for item_mapa in mapa_saida:
                valor = linha.get(item_mapa['chave_db'])
                print("itera pelo mapa_saida")
                
                # formatações visuais (opcional)
                if item_mapa['tipo'] == 'boolean':
                    valor = "Sim" if valor else "Não"
                elif item_mapa['tipo'] == 'datetime' and valor:
                    valor = valor.strftime("%d/%m/%Y %H:%M") if hasattr(valor, 'strftime') else valor
                    
                nova_linha[item_mapa['rotulo']] = valor
            dados_formatados.append(nova_linha)
            
        return dados_formatados


class ConstrutorHTML:
    
    @staticmethod
    def inserir_dados_no_html(esquema_bd, html_template):
        soup = BeautifulSoup(html_template, 'html.parser')
        tabela_divs = soup.find_all(attrs={'data-config-consulta': True})

        for tab_div in tabela_divs:
            # recupera e processa a configuração
            dados_consulta_str = tab_div['data-config-consulta']
            dados_consulta = json.loads(dados_consulta_str)
            
            # retorna lista de dicts: [{'Nome': 'João', 'Idade': 30}, ...]
            dados = ConstrutorConsulta(esquema_bd, dados_consulta).executar()
            tab_div.clear()
            
            if dados:
                # cria a tabela estilizada
                tabela_tag = ConstrutorHTML._criar_tabela(soup, dados)
                tab_div.append(tabela_tag)
                
            # remove o atributo de dados para limpar o HTML final
            del tab_div['data-config-consulta']

        return str(soup)

    @staticmethod
    def _criar_tabela(soup, lista_dados):
        """
        Gera uma tag <table> usando métodos nativos do BeautifulSoup.
        Recebe: soup (objeto pai), lista_dados (lista de dicts)
        """
        # cria a estrutura da tabela
        table = soup.new_tag('table')
        thead = soup.new_tag('thead')
        tr_head = soup.new_tag('tr')
        
        # pega as chaves do primeiro dicionário como cabeçalho
        # O ConstrutorConsulta já retorna as chaves com os rótulos
        colunas = lista_dados[0].keys()
        
        for col in colunas:
            th = soup.new_tag('th')
            th.string = str(col)
            tr_head.append(th)
        
        thead.append(tr_head)
        table.append(thead)
        
        tbody = soup.new_tag('tbody')
        
        for linha in lista_dados:
            tr = soup.new_tag('tr')
            for valor in linha.values():
                td = soup.new_tag('td')
                # trata valores None/Null para não aparecer "None" no PDF
                td.string = str(valor) if valor is not None else "-" 
                tr.append(td)
            tbody.append(tr)
            
        table.append(tbody)
        
        return table