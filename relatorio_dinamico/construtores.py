from django.apps import apps
from django.db.models import Q, Count, Sum, Avg, Min, Max
from django.core.exceptions import ValidationError
from functools import reduce
import operator
import json
from bs4 import BeautifulSoup
from django.template.loader import render_to_string

# mapa de funções de agregação permitidas 
MAPA_AGREGACAO = {
    'Count': Count,
    'Sum': Sum, 
    'Avg': Avg, 
    'Min': Min, 
    'Max': Max
}

LIMITE_MAXIMO = 1000

class ConstrutorConsulta:
    def __init__(self, esquema, configuracao_consulta):
        """
        :param esquema: Dicionário representando o esquema do BD
        :param configuracao_consulta: JSON especificando os metadados da consulta
        """
        self.esquema = esquema
        self.configuracao_consulta = configuracao_consulta
        # verifica se a tabela raiz existe no esquema
        self.nome_entidade_raiz = configuracao_consulta.get('fonte_principal')

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
        Ex: Procura em 'conexoes': 'campo_relacao' == 'unidade'
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
        
        # navega pelas relações (todas as partes exceto a última)
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
            entidade_atual = conexao['model_destino']
            
        # resolve o campo final
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
        
        for filtro in self.configuracao_consulta.get('filtros', []):
            # 1. resolve o caminho (validação de segurança)
            caminho_orm, tipo_campo = self._resolver_caminho(filtro['campo'])
            sufixo_operador = filtro['operador']
            valor = filtro['valor']
            
            # 2. tratamento de tipos específicos
            if tipo_campo == 'bool' and isinstance(valor, str):
                valor = valor.lower() == 'true'
            
            # 3. monta o lookup do Django (ex: base__cidade__icontains)
            consulta_orm = f"{caminho_orm}__{sufixo_operador}"
            lista_q.append(Q(**{consulta_orm: valor}))
            
        return lista_q

    def _contruir_ordenacao(self):
        """Constrói a lista de campos para o order_by() do Django"""
        ordenacao_final = []
        ordenacoes = self.configuracao_consulta.get('ordenacoes', [])
        for ord_item in ordenacoes:
            campo_input = ord_item['campo']
            direcao = ord_item.get('ordem', 'asc').lower()
            
            # se o campo for uma métrica, usa o alias gerado
            if campo_input in self._mapa_apelidos_metricas:
                campo_ordenar = self._mapa_apelidos_metricas[campo_input]
            else:
                # caso contrário, resolve o caminho normal
                campo_ordenar, _ = self._resolver_caminho(campo_input)
            
            prefixo = "-" if direcao == "desc" else ""
            ordenacao_final.append(f"{prefixo}{campo_ordenar}")
        
        return ordenacao_final

    def _processar_colunas(self, dimensoes, metricas):
        """Processa as colunas da configuração, preenchendo as listas de dimensões e métricas."""
        colunas = self.configuracao_consulta.get('colunas', [])

        if len(colunas) == 0:
            raise ValidationError(
                f"Nenhuma coluna foi especificada para a consulta."
            )

        for coluna in colunas:
            caminho_orm, tipo_campo = self._resolver_caminho(coluna['campo'])
            rotulo = coluna.get('rotulo', coluna['campo'])
            func_agregacao = coluna.get('agregacao')
            
            if func_agregacao:
                if func_agregacao not in MAPA_AGREGACAO:
                    raise ValidationError(f"Função de agregação inválida: {func_agregacao}")
                
                # alias único para o Django não se perder
                # Ex: solicitante__id torna-se solicitante_id_count
                apelido = f"{caminho_orm.replace('__', '_')}_{func_agregacao.lower()}"
                # cria a métrica (ex: Count('id'))
                metricas[apelido] = MAPA_AGREGACAO[func_agregacao](caminho_orm, distinct=True)
                self._mapa_apelidos_metricas[coluna['campo']] = apelido
                self._mapa_saida.append({
                    'chave_db': apelido, 
                    'rotulo': rotulo, 
                    'tipo': 'number' # agregações são sempre numéricas
                })
            else:
                # é uma dimensão (agrupamento)
                dimensoes.append(caminho_orm)
                self._mapa_saida.append({
                    'chave_db': caminho_orm, 
                    'rotulo': rotulo, 
                    'tipo': tipo_campo
                })

    def criar_queryset(self):
        """
        Gera o objeto QuerySet do Django sem executar a consulta no banco.
        Prepara também o self._mapa_saida.
        """
        queryset = self.modelo_classe.objects.all()
        # aplica os filtros
        filtros = self._construir_filtros()

        if filtros:
            # combina todos os filtros com AND
            queryset = queryset.filter(reduce(operator.and_, filtros))
            
        # prepara as colunas
        self._mapa_apelidos_metricas = {}  # para mapear campos de ordenação
        self._mapa_saida = []  # para formatar o resultado final e manter a ordem
        dimensoes = []   # para o Group By (.values)
        metricas = {}    # para agregações (.annotate)
        self._processar_colunas(dimensoes, metricas)

        # constrói a QuerySet na ordem correta: values() -> annotate() -> values()
        
        if dimensoes:
            # define os campos para o GROUP BY (agrupamento)
            queryset = queryset.values(*dimensoes)
        
        if metricas:
            # calcula as funções de agregação para cada grupo
            queryset = queryset.annotate(**metricas)
            
        # limpa o SELECT final para trazer apenas o solicitado
        chaves_selecao_final = dimensoes + list(metricas.keys())
        if chaves_selecao_final:
            queryset = queryset.values(*chaves_selecao_final)

        queryset = queryset.distinct()
        # ordenação
        ordenacao_final = self._contruir_ordenacao()
        
        if ordenacao_final:
            queryset = queryset.order_by(*ordenacao_final)

        # limite 
        limite = self.configuracao_consulta.get('limite')
        if limite and isinstance(limite, int) and limite > 0 and limite <= LIMITE_MAXIMO:
            queryset = queryset[:limite]
        else:
            queryset = queryset[:LIMITE_MAXIMO]

        return queryset

    def executar(self):
        """
        Executa a consulta no banco de dados e formata o resultado.
        """
        queryset = self.criar_queryset()
        dados_formatados = []

        for linha in queryset:
            nova_linha = {}
            for item_mapa in self._mapa_saida:
                valor = linha.get(item_mapa['chave_db'])
                
                # formatações visuais
                if item_mapa['tipo'] == 'bool':
                    valor = "Sim" if valor else "Não"
                elif item_mapa['tipo'] == 'date' and valor:
                    valor = valor.strftime("%d/%m/%Y") if hasattr(valor, 'strftime') else valor
                elif item_mapa['tipo'] == 'datetime' and valor:
                    valor = valor.strftime("%d/%m/%Y %H:%M") if hasattr(valor, 'strftime') else valor
                    
                nova_linha[item_mapa['rotulo']] = valor
            dados_formatados.append(nova_linha)
            
        return dados_formatados


class ConstrutorHTML:
    def __init__(self, esquema_bd, html_inicial, caminho_template):
        """ Classe para construir o HTML final do relatório dinâmico.
        :param esquema_bd: Dicionário representando o esquema do BD
        :param html_inicial: HTML parcial contendo os componentes do documento, incluindo as tabelas a serem preenchidas
        :param caminho_template: Caminho do template base do relatório
        """
        self._esquema_bd = esquema_bd
        self.html_inicial = html_inicial
        self._caminho_template = caminho_template

    def gerar_html(self):
        template = render_to_string(self._caminho_template)
        estrutura_html = BeautifulSoup(template, 'html.parser')
        body = estrutura_html.find('body')
        html_preenchido = self._inserir_dados_no_html()
        body.append(html_preenchido)

        return str(estrutura_html)

    def _inserir_dados_no_html(self):
        conteudo_html = BeautifulSoup(self.html_inicial, 'html.parser')
        tabelas = conteudo_html.find_all(attrs={'data-config-consulta': True})

        for tab in tabelas:
            dados_consulta_str = tab['data-config-consulta']
            dados_consulta = json.loads(dados_consulta_str)
            # retorna lista de dicts: [{'Nome': 'João', 'Idade': 30}, ...]
            construtor_consulta = ConstrutorConsulta(self._esquema_bd, dados_consulta)
            dados = construtor_consulta.executar()
            
            if dados:
                self._preencher_tabela(tab, dados, conteudo_html)

            # remove o atributo de dados para limpar o HTML final
            del tab['data-config-consulta']

        return conteudo_html

    def _preencher_tabela(self, tabela, lista_dados, conteudo_html):
        cabecalhos = lista_dados[0].keys()
        tr = tabela.thead.tr
        ths = tr.find_all('th')
        
        for th, cabecalho in zip(ths, cabecalhos):
            th.string = cabecalho

        tbody = tabela.tbody
        estilo_tr = tbody.tr['style'] if 'style' in tbody.tr.attrs else ''

        tbody.clear()
        for linha in lista_dados:
            linha_tabela = conteudo_html.new_tag('tr')
            linha_tabela['style'] = estilo_tr
            
            for valor in linha.values():
                td = conteudo_html.new_tag('td')
                td.string = str(valor) if valor is not None else "-"
                linha_tabela.append(td)

            tbody.append(linha_tabela)

