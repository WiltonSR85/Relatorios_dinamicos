from django.apps import apps
from django.db.models import Q, Count, Sum, Avg, Min, Max
from django.db.models.functions import TruncDay, TruncMonth, TruncYear
from django.core.exceptions import ValidationError
from functools import reduce
import operator
import json
from bs4 import BeautifulSoup
from django.template.loader import render_to_string

FUNCOES_DE_AGREGACAO = {
    'count': Count,
    'sum': Sum, 
    'avg': Avg, 
    'min': Min, 
    'max': Max
}

FUNCOES_DE_TRUNCAMENTO_DATA = {
    'truncday': TruncDay,
    'truncmonth': TruncMonth,
    'truncyear': TruncYear
}

# limite máximo de registros retornados em uma consulta
LIMITE_MAXIMO = 1000

class ValidadorConsulta:
    def __init__(self, esquema):
        """
        :param esquema: Dicionário representando o esquema do BD
        """
        self.esquema = esquema
        self._campos_validados = {} # para evitar validação repetida de campos

    
    def _buscar_na_lista(self, lista, chave_identificadora, valor_buscado):
        """
        Função auxiliar para encontrar um dicionário dentro de uma lista.
        Ex: Procura em 'conexoes': 'campo_relacao' == 'unidade'
        """
        for item in lista:
            if item.get(chave_identificadora) == valor_buscado:
                return item
        return None


    def _validar_caminho(self, nome_entidade_raiz, caminho_str):
        """
        Verifica se o caminho do campo (ex: "solicitante__usuario__email") 
        é válido dentro do esquema fornecido.
        
        Retorna o tipo do campo (ex: "string", "number", "date", etc).
        """
        if caminho_str in self._campos_validados:
            return self._campos_validados[caminho_str]

        partes = caminho_str.split('__')
        entidade_atual = nome_entidade_raiz
        
        # navega pelas relações (todas as partes exceto a última, que é o nome da coluna no BD)
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
            
            # avança para a próxima entidade no caminho
            entidade_atual = conexao['model_destino']
            
        nome_campo = partes[-1]
        config_entidade_final = self.esquema.get(entidade_atual)
        lista_campos = config_entidade_final.get('campos', [])
        config_campo = self._buscar_na_lista(lista_campos, 'valor', nome_campo)
        
        if not config_campo:
            raise ValidationError(
                f"Campo '{nome_campo}' não encontrado na entidade '{entidade_atual}'."
            )
        
        tipo_campo = config_campo['tipo']
        self._campos_validados[caminho_str] = tipo_campo
        
        return tipo_campo


    def _validar_funcao(self, nome_funcao, campo, tipo_campo):
        """Valida se a função de agregação ou truncamento é válida para o campo"""
        if nome_funcao:
            if nome_funcao not in FUNCOES_DE_AGREGACAO and nome_funcao not in FUNCOES_DE_TRUNCAMENTO_DATA:
                raise ValidationError(f"Função inválida no campo '{campo}': {nome_funcao}")

            if nome_funcao in FUNCOES_DE_TRUNCAMENTO_DATA and tipo_campo not in ['date', 'datetime']:
                raise ValidationError(
                        f"Truncamento de data só pode ser aplicado a campos 'date' ou 'datetime'. "
                        f"Campo é do tipo '{tipo_campo}'."
                    )
        
        return nome_funcao

    
    def _obter_tipo_exibicao(self, nome_funcao):
        """ Determina o tipo de exibição com base na função aplicada, para formatação visual correta. """
        if nome_funcao in FUNCOES_DE_AGREGACAO:
            return 'number' # funções de agregação sempre retornam números
        elif nome_funcao in FUNCOES_DE_TRUNCAMENTO_DATA:
            if nome_funcao.endswith("month"):
                return 'month'
            elif nome_funcao.endswith("year"):
                return 'year'
            else:
                return 'date'


    def _criar_apelido_campo(self, campo, nome_funcao=None):
        """Cria um apelido único para o campo, considerando agregações e truncamentos"""
        apelido = campo.replace('__', '_')

        if nome_funcao:
            apelido = f"{apelido}_{nome_funcao}"
        
        return apelido


    def _processar_tipos_exibicao_colunas(self, colunas):
        """Processa e define o tipo de exibição para cada coluna"""
        for coluna in colunas:
            nome_funcao = coluna.get('agregacao') or coluna.get('truncamento')
            
            if nome_funcao:
                coluna['tipo_exibicao'] = self._obter_tipo_exibicao(nome_funcao)


    def _processar_valores_filtros(self, filtros):
        """Processa e normaliza os valores dos filtros"""
        for filtro in filtros:
            tipo_campo = filtro['tipo']
            valor = filtro['valor']
            
            if tipo_campo == 'bool':
                valor = bool(valor)

            filtro['valor'] = valor


    def _validar_limite(self, limite):
        if limite and isinstance(limite, int) and limite > 0 and limite <= LIMITE_MAXIMO:
            return limite
        else:
            return LIMITE_MAXIMO


    def validar(self, configuracao_consulta):
        """Valida todos os campos usados na consulta"""
        if not isinstance(configuracao_consulta, dict):
            raise ValidationError("Configuração de consulta inválida.")
        
        nome_entidade_raiz = configuracao_consulta.get('fonte_principal')
        
        if nome_entidade_raiz not in self.esquema:
            raise ValidationError(f"Entidade raiz '{nome_entidade_raiz}' inválida.")
        
        # armazena o nome do app_model no dicionário da consulta
        configuracao_consulta['app_model'] = self.esquema[nome_entidade_raiz]['app_model']
        
        if self._campos_validados:
            self._campos_validados.clear()

        colunas = configuracao_consulta.get('colunas', [])

        if len(colunas) == 0:
            raise ValidationError("Nenhuma coluna foi especificada para a consulta.")

        filtros = configuracao_consulta.get('filtros', [])
        ordenacoes = configuracao_consulta.get('ordenacoes', [])
        lista_elementos = colunas + filtros + ordenacoes

        for elemento in lista_elementos:
            campo = elemento['campo']
            tipo = self._validar_caminho(nome_entidade_raiz, campo)
            elemento['tipo'] = tipo # armazena o tipo do campo validado
            nome_funcao = elemento.get('agregacao') or elemento.get('truncamento')
            nome_funcao = self._validar_funcao(nome_funcao, campo, tipo)
            elemento['apelido'] = self._criar_apelido_campo(campo, nome_funcao) # armazena o apelido do campo

        # tratamento específico para colunas
        self._processar_tipos_exibicao_colunas(colunas)
        # tratamento específico para filtros
        self._processar_valores_filtros(filtros)

        limite = configuracao_consulta.get('limite')
        configuracao_consulta['limite'] = self._validar_limite(limite)

        return configuracao_consulta

class ConstrutorConsulta:
    def __init__(self, configuracao_consulta):
        """
        :param configuracao_consulta: Dicionário especificando os metadados da consulta
        """
        self.configuracao_consulta = configuracao_consulta
        
        # carrega o modelo dinamicamente
        try:
            self.modelo_classe = apps.get_model(self.configuracao_consulta['app_model'])
        except LookupError:
            raise ValidationError(f"Modelo do Django não encontrado: {self.configuracao_consulta['app_model']}")

        self._mapa_saida = [] # para formatar o resultado final e manter a ordem


    def _processar_colunas(self):
        """Processa as colunas da configuração"""
        campos_truncados = {} # para campos com truncamento de data (.annotate)
        campos = []   # para o Group By (.values)
        metricas = {}    # para agregações (.annotate)
        colunas = self.configuracao_consulta.get('colunas', [])

        for coluna in colunas:
            caminho_orm = coluna['campo']
            tipo = coluna['tipo']
            rotulo = coluna.get('rotulo', coluna['campo'])
            nome_func_agregacao = coluna.get('agregacao')
            nome_func_truncamento = coluna.get('truncamento')
            apelido = coluna.get('apelido')
            
            if nome_func_agregacao:
                func_agregacao = FUNCOES_DE_AGREGACAO[nome_func_agregacao]
                
                if nome_func_agregacao in ['min', 'max']:
                    # as funções Min e Max não recebem o argumento 'distinct'
                    metricas[apelido] = func_agregacao(caminho_orm)
                else: 
                    metricas[apelido] = func_agregacao(caminho_orm, distinct=True)
                
                tipo = coluna['tipo_exibicao']
                chave_db = apelido

            elif nome_func_truncamento:
                func_truncamento = FUNCOES_DE_TRUNCAMENTO_DATA[nome_func_truncamento]
                campos_truncados[apelido] = func_truncamento(caminho_orm)
                tipo = coluna['tipo_exibicao']
                chave_db = apelido

            else:
                campos.append(caminho_orm)
                chave_db = caminho_orm
                
            self._mapa_saida.append({
                'chave_db': chave_db,
                'rotulo': rotulo,
                'tipo': tipo
            })
        
        return campos_truncados, campos, metricas


    def _construir_filtros(self):
        """Constrói a lista de objetos Q() para usar no .filter() do Django"""
        lista_q = []
        filtros = self.configuracao_consulta.get('filtros', [])

        for filtro in filtros:
            campo = filtro['campo']
            sufixo_operador = filtro['operador']
            valor = filtro['valor']

            func_agregacao = filtro.get('agregacao')
            
            if func_agregacao:
                apelido = filtro['apelido']
                consulta_orm = f"{apelido}__{sufixo_operador}"
            else:
                consulta_orm = f"{campo}__{sufixo_operador}"

            lista_q.append(Q(**{consulta_orm: valor}))
        
        return lista_q 


    def _construir_ordenacao(self):
        """Constrói a lista de campos para o order_by() do Django"""
        ordenacao_final = []
        ordenacoes = self.configuracao_consulta.get('ordenacoes', [])
        for ordenacao in ordenacoes:
            campo = ordenacao['campo']
            direcao = ordenacao.get('ordem', 'asc').lower()
            nome_funcao = ordenacao.get('agregacao') or ordenacao.get('truncamento')
            
            # se o campo for uma métrica, usa o apelido gerado
            if nome_funcao:
                campo_ordenacao = ordenacao.get('apelido')
            else:
                campo_ordenacao = campo 

            prefixo = "-" if direcao == "desc" else ""
            ordenacao_final.append(f"{prefixo}{campo_ordenacao}")
        
        return ordenacao_final


    def criar_queryset(self):
        """
        Gera o objeto QuerySet do Django sem executar a consulta no banco.
        Prepara também o self._mapa_saida.
        """
        queryset = self.modelo_classe.objects.all()
        # prepara as colunas
        campos_truncados, campos, metricas = self._processar_colunas()
        
        # constrói o QuerySet na ordem correta
        
        if campos_truncados:
            # aplica os truncamentos de data
            queryset = queryset.annotate(**campos_truncados)
        
        campos_agrupamento = campos + list(campos_truncados.keys())

        if campos_agrupamento:
            # define os campos para o GROUP BY (agrupamento)
            queryset = queryset.values(*campos_agrupamento)
        
        if metricas:
            # calcula as funções de agregação 
            queryset = queryset.annotate(**metricas)
        
        # constrói os filtros
        filtros = self._construir_filtros()

        if filtros:
            # combina todos os filtros com AND
            queryset = queryset.filter(reduce(operator.and_, filtros))

        # limpa o SELECT final para trazer apenas o solicitado
        chaves_selecao_final = list(campos_truncados.keys()) + campos + list(metricas.keys())

        if chaves_selecao_final:
            queryset = queryset.values(*chaves_selecao_final)

        # remove resultados duplicados
        queryset = queryset.distinct()
        # ordenação
        ordenacao_final = self._construir_ordenacao()
        
        if ordenacao_final:
            queryset = queryset.order_by(*ordenacao_final)

        # limite 
        limite = self.configuracao_consulta.get('limite')
        queryset = queryset[:limite]

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
                    valor = "Verdadeiro" if valor else "Falso"
                elif item_mapa['tipo'] == 'date' and valor:
                    valor = valor.strftime("%d/%m/%Y") if hasattr(valor, 'strftime') else valor
                elif item_mapa['tipo'] == 'datetime' and valor:
                    valor = valor.strftime("%d/%m/%Y %H:%M") if hasattr(valor, 'strftime') else valor
                elif item_mapa['tipo'] == 'month' and valor:
                    valor = valor.strftime("%m/%Y") if hasattr(valor, 'strftime') else valor
                elif item_mapa['tipo'] == 'year' and valor:
                    valor = valor.strftime("%Y") if hasattr(valor, 'strftime') else valor

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
        self._html_inicial = html_inicial
        self._caminho_template = caminho_template

    def gerar_html(self):
        template = render_to_string(self._caminho_template)
        estrutura_html = BeautifulSoup(template, 'html.parser')
        body = estrutura_html.find('body')
        html_preenchido = self._inserir_dados_no_html()
        body.append(html_preenchido)

        return str(estrutura_html)

    def _inserir_dados_no_html(self):
        conteudo_html = BeautifulSoup(self._html_inicial, 'html.parser')
        tabelas = conteudo_html.find_all(attrs={'data-config-consulta': True})
        validador_consulta = ValidadorConsulta(self._esquema_bd)

        for tab in tabelas:
            dados_consulta_str = tab['data-config-consulta']
            dados_consulta = json.loads(dados_consulta_str)
            # retorna lista de dicts: [{'Nome': 'João', 'Idade': 30}, ...]
            config_consulta_valida = validador_consulta.validar(dados_consulta)
            construtor_consulta = ConstrutorConsulta(config_consulta_valida)
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

