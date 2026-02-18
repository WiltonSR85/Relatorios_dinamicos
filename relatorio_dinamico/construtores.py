from django.apps import apps
from django.db.models import Q, Count, Sum, Avg, Min, Max
from django.db.models.functions import TruncDay, TruncMonth, TruncYear
from django.core.exceptions import ValidationError
from functools import reduce
import operator
import json
from bs4 import BeautifulSoup
from django.template.loader import render_to_string
import re

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
    def __init__(self, configuracao_consulta: dict=None):
        """
        :param configuracao_consulta: Dicionário especificando os metadados da consulta
        """
        self._configuracao_consulta = configuracao_consulta
        self._mapa_saida = [] # para formatar o resultado final e manter a ordem

        if configuracao_consulta:
            self._carregar_modelo()

    @property
    def configuracao_consulta(self):
        return self._configuracao_consulta
    
    @configuracao_consulta.setter
    def configuracao_consulta(self, configuracao_consulta: dict):
        self._configuracao_consulta = configuracao_consulta
        self._carregar_modelo()
        self._mapa_saida.clear()

    def _carregar_modelo(self):
        try:
            self._modelo_classe = apps.get_model(self._configuracao_consulta['app_model'])
        except LookupError:
            raise ValidationError(f"Modelo do Django não encontrado: {self._configuracao_consulta['app_model']}")

    def _processar_colunas(self):
        """Processa as colunas da configuração"""
        campos_truncados = {} # para campos com truncamento de data (.annotate)
        campos = []   # para o Group By (.values)
        metricas = {}    # para agregações (.annotate)
        colunas = self._configuracao_consulta.get('colunas', [])

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

    def _construir_filtro(self):
        """Constrói o objeto Q para os filtros da consulta, combinando-os com AND"""
        lista_q = []
        filtros = self._configuracao_consulta.get('filtros', [])

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
        
        if lista_q:
            return reduce(operator.and_, lista_q)
        else:
            return None

    def _construir_ordenacao(self):
        """Constrói a lista de campos para o order_by() do Django"""
        ordenacao_final = []
        ordenacoes = self._configuracao_consulta.get('ordenacoes', [])
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

    def _criar_queryset(self):
        """
        Gera o objeto QuerySet do Django sem executar a consulta no banco.
        """
        queryset = self._modelo_classe.objects.all()
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
        filtro = self._construir_filtro()

        if filtro:
            queryset = queryset.filter(filtro)

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
        limite = self._configuracao_consulta.get('limite')
        queryset = queryset[:limite]

        return queryset
    
    def _verificar_somente_agregacao(self):
        """Verifica se a consulta contém apenas colunas com funções de agregação. 
        Se a consulta tiver apenas funções de agregação, será necessário usar o método .aggregate() no lugar de .annotate()
        """
        colunas = self._configuracao_consulta.get('colunas', [])
        
        for coluna in colunas:
            if not coluna.get('agregacao'):
                return False

        return True

    def get_sql(self):
        """Retorna a string SQL da consulta construída"""
        tem_somente_agregacao = self._verificar_somente_agregacao()
        queryset = self._criar_queryset()

        if tem_somente_agregacao:
            # o método .aggregate() que será usado neste caso não retorna um QuerySet; 
            # uma alternativa é utilizar um queryset com annotate() e pegar o código SQL, 
            # removendo o GROUP BY desnecessário e tudo o que vier a partir dele usando regex
            sql = str(queryset.query)
            sql_limpa = re.sub(r'GROUP BY.*', '', sql, flags=re.IGNORECASE | re.DOTALL).strip()
            
            return sql_limpa
        else:
            return str(queryset.query)

    def executar(self):
        """
        Executa a consulta no banco de dados e formata o resultado.
        """
        tem_somente_agregacao = self._verificar_somente_agregacao()

        if tem_somente_agregacao:
            queryset = self._modelo_classe.objects.all()
            _, _, metricas = self._processar_colunas()
            filtro = self._construir_filtro()

            if filtro:
                queryset = queryset.filter(filtro)
            
            dados = [queryset.aggregate(**metricas)]
        else: 
            dados = self._criar_queryset()
        
        dados_formatados = []

        for dado in dados:
            nova_linha = {}
            for item_mapa in self._mapa_saida:
                valor = dado.get(item_mapa['chave_db'])
                
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
    def __init__(self, html_inicial: str, caminho_template: str, validador_consulta: ValidadorConsulta, construtor_consulta: ConstrutorConsulta):
        """ Classe para construir o HTML final do relatório dinâmico.
        :param html_inicial: HTML parcial contendo os componentes do documento, incluindo as tabelas a serem preenchidas
        :param caminho_template: Caminho do template base do relatório, dentro do qual o HTML parcial será inserido
        :param validador_consulta: Instância de ValidadorConsulta para validar as configurações de consulta encontradas no HTML
        :param construtor_consulta: Instância de ConstrutorConsulta para executar as consultas encontradas no HTML e obter os dados para preenchimento
        """
        template = render_to_string(caminho_template)
        self._html = BeautifulSoup(template, 'html.parser')
        html_inicial = BeautifulSoup(html_inicial, 'html.parser')
        self._html.body.append(html_inicial) # insere o HTML parcial dentro do corpo do template base
        self._validador_consulta = validador_consulta
        self._construtor_consulta = construtor_consulta

    def gerar_html(self):
        self._inserir_dados_no_html()

        return str(self._html)

    def _inserir_dados_no_html(self):
        # encontra todas as tabelas que possuem o atributo data-config-consulta, que indica que devem ser preenchidas dinamicamente
        tabelas = self._html.find_all(attrs={'data-config-consulta': True})

        for tab in tabelas:
            # extrai a configuração de consulta do atributo data-config-consulta, que é uma string JSON
            dados_consulta_str = tab['data-config-consulta']
            dados_consulta = json.loads(dados_consulta_str)
            # valida a consulta e obtém a configuração pronta para execução
            config_consulta_valida = self._validador_consulta.validar(dados_consulta)
            self._construtor_consulta.configuracao_consulta = config_consulta_valida
            # retorna uma lista de dicionários: [{'Nome': 'João', 'Idade': 30}, ...]
            dados = self._construtor_consulta.executar()
            
            if dados:
                self._preencher_tabela(tab, dados)

            # remove o atributo de dados para limpar o HTML final
            del tab['data-config-consulta']

    def _preencher_tabela(self, tabela, lista_dados):
        cabecalhos = lista_dados[0].keys()
        ths = tabela.find_all('th')
        
        for th, cabecalho in zip(ths, cabecalhos):
            th.string = cabecalho

        tbody = tabela.tbody
        tbody.clear()

        for linha in lista_dados:
            linha_tabela = self._html.new_tag('tr')
            
            for valor in linha.values():
                td = self._html.new_tag('td')
                td.string = str(valor) if valor is not None else "-"
                linha_tabela.append(td)

            tbody.append(linha_tabela)

