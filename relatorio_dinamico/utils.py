from django.apps import apps
from django.db.models import Q, Count, Sum, Avg, Min, Max
from django.core.exceptions import ValidationError
from functools import reduce
import operator

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
        :param esquema: Dicionário completo de configurações (SCHEMA_RELATORIOS)
        :param dados_entrada: JSON vindo do frontend com a definição do relatório
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
        
        # 1. Aplica Filtros
        filtros = self._construir_filtros()
        if filtros:
            # Combina todos os filtros com AND (intersecção)
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
        
        # 3. Constrói a QuerySet na ordem correta
        # ORDEM CRÍTICA: values() -> annotate() -> values()
        
        if dimensoes:
            # define os campos para o GROUP BY (agrupamento)
            queryset = queryset.values(*dimensoes)
            print("queryset 2:", queryset.query)
        
        if metricas:
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
                
                # Formatações cosméticas (opcional)
                if item_mapa['tipo'] == 'boolean':
                    valor = "Sim" if valor else "Não"
                elif item_mapa['tipo'] == 'datetime' and valor:
                    # Formata data se o objeto tiver método strftime
                    valor = valor.strftime("%d/%m/%Y %H:%M") if hasattr(valor, 'strftime') else valor
                    
                nova_linha[item_mapa['rotulo']] = valor
            dados_formatados.append(nova_linha)
            
        return dados_formatados