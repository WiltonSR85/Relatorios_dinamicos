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
    def __init__(self, esquema, configuracao_consulta):
        """
        :param esquema: Dicionário representando o esquema do BD
        :param configuracao_consulta: Dicionário especificando os metadados da consulta
        """
        self.esquema = esquema
        
        if not isinstance(configuracao_consulta, dict):
            raise ValidationError("Configuração de consulta inválida.")
        
        self.configuracao_consulta = configuracao_consulta
        self.nome_entidade_raiz = configuracao_consulta.get('fonte_principal')
        
        if self.nome_entidade_raiz not in self.esquema:
            raise ValidationError(f"Entidade raiz '{self.nome_entidade_raiz}' inválida.")
        
        self.configuracao_consulta['app_model'] = self.esquema[self.nome_entidade_raiz]['app_model']
        self.campos_validados = {}  # para evitar validação repetida de campos

    
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
        Traduz o caminho da configuração (ex: "solicitante__usuario__email") 
        para o caminho do Django ORM, validando cada passo no esquema.
        
        Retorna: (caminho_orm, tipo_dado)
        """

        if caminho_str in self.campos_validados:
            return caminho_str, self.campos_validados[caminho_str]

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
        
        # retorna o caminho unido (ex: solicitante__usuario__email), o tipo (ex: string)
        caminho_final = "__".join(partes_caminho_orm)
        self.campos_validados[caminho_final] = config_campo['tipo']
        return caminho_final, config_campo['tipo']

    
    def validar(self):
        """Valida todos os campos usados na consulta"""
        colunas = self.configuracao_consulta.get('colunas', [])

        if len(colunas) == 0:
            raise ValidationError("Nenhuma coluna foi especificada para a consulta.")

        filtros = self.configuracao_consulta.get('filtros', [])
        ordenacoes = self.configuracao_consulta.get('ordenacoes', [])

        lista_elementos = colunas + filtros + ordenacoes

        for elemento in lista_elementos:
            campo = elemento['campo']
            _, tipo = self._resolver_caminho(campo)
            elemento['tipo'] = tipo

        return self.configuracao_consulta

class ConstrutorConsulta:
    def __init__(self, configuracao_consulta):
        """
        :param configuracao_consulta: JSON especificando os metadados da consulta
        """
        self.configuracao_consulta = configuracao_consulta
        self.nome_entidade_raiz = configuracao_consulta.get('fonte_principal')
        
        # carrega o modelo dinamicamente
        try:
            self.modelo_classe = apps.get_model(self.configuracao_consulta['app_model'])
        except LookupError:
            raise ValidationError(f"Modelo do Django não encontrado: {self.configuracao_consulta['app_model']}")


    def _processar_colunas(self):
        """Processa as colunas da configuração"""
        campos_truncados = {} # para campos com truncamento de data (.annotate)
        campos = []   # para o Group By (.values)
        metricas = {}    # para agregações (.annotate)
        colunas = self.configuracao_consulta.get('colunas', [])

        for coluna in colunas:
            caminho_orm = coluna['campo']
            tipo_campo = coluna['tipo']
            rotulo = coluna.get('rotulo', coluna['campo'])
            nome_func_agregacao = coluna.get('agregacao')
            nome_func_truncamento = coluna.get('truncamento')
            
            if nome_func_agregacao:
                self._processar_agregacao(caminho_orm, nome_func_agregacao, rotulo, metricas)
            elif nome_func_truncamento:
                self._processar_truncamento(caminho_orm, tipo_campo, nome_func_truncamento, rotulo, campos_truncados)
            else:
                campos.append(caminho_orm)
                self._mapa_saida.append({
                    'chave_db': caminho_orm,
                    'rotulo': rotulo,
                    'tipo': tipo_campo
                })
        
        return campos_truncados, campos, metricas

    def _processar_agregacao(self, caminho_orm, nome_funcao, rotulo, metricas):
        """Processa uma coluna com função de agregação"""
        if nome_funcao not in FUNCOES_DE_AGREGACAO:
            raise ValidationError(f"Função de agregação inválida: {nome_funcao}")
        
        chave_agregacao = f"{caminho_orm}__{nome_funcao}"
        apelido_agregacao = chave_agregacao.replace('__', '_')
        
        func_agregacao = FUNCOES_DE_AGREGACAO[nome_funcao]
        metricas[apelido_agregacao] = func_agregacao(caminho_orm, distinct=True)
        self._mapa_apelidos[chave_agregacao] = apelido_agregacao
        self._mapa_saida.append({
            'chave_db': apelido_agregacao,
            'rotulo': rotulo,
            'tipo': 'number'
        })


    def _processar_truncamento(self, caminho_orm, tipo_campo, nome_funcao, rotulo, campos_truncados):
        """Processa uma coluna com truncamento de data"""
        if nome_funcao not in FUNCOES_DE_TRUNCAMENTO_DATA:
            return
        
        if tipo_campo not in ['date', 'datetime']:
            raise ValidationError(
                f"Truncamento de data só pode ser aplicado a campos 'date' ou 'datetime'. "
                f"Campo é do tipo '{tipo_campo}'."
            )
        
        chave_truncamento = f"{caminho_orm}__{nome_funcao}"
        apelido_truncamento = chave_truncamento.replace('__', '_')
        func_truncamento = FUNCOES_DE_TRUNCAMENTO_DATA[nome_funcao]
        campos_truncados[apelido_truncamento] = func_truncamento(caminho_orm) 
        self._mapa_apelidos[chave_truncamento] = apelido_truncamento
        
        if nome_funcao.endswith("month"):
            tipo_exibicao = 'month'
        elif nome_funcao.endswith("year"):
            tipo_exibicao = 'year'
        else:
            tipo_exibicao = 'date'

        self._mapa_saida.append({
            'chave_db': apelido_truncamento,
            'rotulo': rotulo,
            'tipo': tipo_exibicao
        })


    def _construir_filtros(self):
        """Constrói a lista de objetos Q() para usar no .filter() do Django"""
        lista_q = []
        filtros = self.configuracao_consulta.get('filtros', [])

        for filtro in filtros:
            campo = filtro['campo']
            sufixo_operador = filtro['operador']
            valor = filtro['valor']
            tipo_campo = filtro['tipo']

            # tratamento de tipos específicos
            if tipo_campo == 'bool':
                valor = bool(valor)
        
            # monta o lookup do Django (ex: base__cidade__icontains)
            consulta_orm = f"{campo}__{sufixo_operador}"
            lista_q.append(Q(**{consulta_orm: valor}))

        return lista_q


    def _construir_ordenacao(self):
        """Constrói a lista de campos para o order_by() do Django"""
        ordenacao_final = []
        ordenacoes = self.configuracao_consulta.get('ordenacoes', [])
        for ord_item in ordenacoes:
            campo_input = ord_item['campo']
            direcao = ord_item.get('ordem', 'asc').lower()
            
            # se o campo for uma métrica, usa o alias gerado
            if campo_input in self._mapa_apelidos:
                campo_ordenar = self._mapa_apelidos[campo_input]
            else:
                campo_ordenar = campo_input

            prefixo = "-" if direcao == "desc" else ""
            ordenacao_final.append(f"{prefixo}{campo_ordenar}")
        
        return ordenacao_final


    def criar_queryset(self):
        """
        Gera o objeto QuerySet do Django sem executar a consulta no banco.
        Prepara também o self._mapa_saida.
        """
        queryset = self.modelo_classe.objects.all()
        # prepara as colunas
        self._mapa_apelidos = {}  # para mapear nomes de campos relacionados a agrupamentos e truncamentos
        self._mapa_saida = []  # para formatar o resultado final e manter a ordem
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
                """ elif item_mapa['tipo'] == 'month' and valor:
                    valor = valor = valor.strftime("%B/%Y") if hasattr(valor, 'strftime') else valor
                elif item_mapa['tipo'] == 'year' and valor:
                    valor = valor = valor.strftime("%Y") if hasattr(valor, 'strftime') else valor """

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

        for tab in tabelas:
            dados_consulta_str = tab['data-config-consulta']
            dados_consulta = json.loads(dados_consulta_str)
            # retorna lista de dicts: [{'Nome': 'João', 'Idade': 30}, ...]
            validador_consulta = ValidadorConsulta(self._esquema_bd, dados_consulta)
            config_consulta_valida = validador_consulta.validar()
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

