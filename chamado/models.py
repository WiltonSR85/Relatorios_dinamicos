from collections import Counter

from django.contrib.auth.models import User
from django.db import models
from django.db.models import PositiveIntegerField, BooleanField, SET_NULL

from base.models import Base
#from fluxo.models import Fluxo
from pessoa.models import Pessoa
from setor.models import Setor
from unidade.models import Unidade

# Create your models here.
class Chamado(models.Model):
    pessoa = models.ForeignKey(Pessoa, on_delete=models.CASCADE, null=True, blank=True)
    base = models.ForeignKey(Base, on_delete=models.CASCADE, related_name="base_chamado", null=True)

    solicitante_nome = models.CharField("nome solicitante", max_length=100, null=True, blank=True)

    relacao_vitima = models.CharField("Relação vítima", max_length=100, null=True, blank=True)    

    achados_clinicos = models.TextField("Achados clínicos / Queixa", null=True, blank=True)
    conduta_medica = models.TextField("Conduta médica", null=True, blank=True)
    queixa_principal = models.TextField("Queixa principal", null=True, blank=True)
    tipo_ocorrencia = models.CharField("Tipo de Ocorrência", max_length=100, null=True, blank=True)
    gravidade = models.CharField("Tipo de Gravidade", max_length=20, null=True, blank=True)

    uf = models.CharField("Estado", max_length=2, null=False)
    cidade = models.CharField(max_length=100, null=False, blank=False)
    logradouro = models.CharField("Endereço", max_length=200, null=True, blank=True)
    numero = models.CharField("Número", max_length=20, null=True, blank=True)
    bairro = models.CharField(max_length=100, null=True, blank=True)
    cep = models.CharField(max_length=10, null=True, blank=True)
    complemento = models.CharField("Complemento", null=True, blank=True)
    ponto_referencia = models.TextField("Ponto de referência", null=True, blank=True)
    apoio_solicitado = models.CharField("Apoio Solicitado", max_length=100,  null=True, blank=True)

    descricao_unidades_desejadas = models.TextField("Observações", null=True, blank=True)

    numero_vitimas = models.IntegerField("Nº de vítimas", null=True, blank=True, validators=[PositiveIntegerField])

    observacoes = models.TextField("Observações", null=True, blank=True)
    origem = models.CharField("Origem", max_length=20, null=True, blank=True)
    motivo = models.CharField("Motivo", max_length=100, null=True, blank=True)
    
    status = models.CharField(max_length=20, default='PENDENTE')

    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    localizacao_validada = BooleanField("Localização validada no mapa", default=False)

    desfecho = models.CharField("desfecho", null=True, blank=True)
    orientacao = models.CharField("Orientação", null=True, blank=True)
    incidente = models.CharField("Incidente", max_length=100, null=True, blank=True)

    unidade_solicitadas = models.JSONField("Unidades solicitadas", null=True, blank=True, default=dict)
    nome_vitimas = models.JSONField("Nome provisório das vitimas", null=True, blank=True, default=list)

    criado_em = models.DateTimeField("Data e hora do chamado", auto_now_add=True)
    criado_por = models.ForeignKey(User, related_name='chamado_criador', on_delete=models.CASCADE, null=True, blank=True)
    
    finalizado_em = models.DateTimeField("Data e hora de finalização do chamado", null=True, blank=True)
    finalizado_por = models.ForeignKey(User, related_name='chamado_finalizador', on_delete=models.CASCADE, null=True, blank=True)

    @property
    # retorna o último trâmite
    def ultimo_tramite(self):
        return self.tramite_chamado.order_by('criado_em').last()

    def __str__(self):
        return f"Chamado {self.id} em {self.criado_em.strftime('%d/%m/%Y às %H:%M:%S')}"


class TramiteChamado(models.Model):
    chamado = models.ForeignKey(Chamado, on_delete=models.CASCADE, null=False, blank=False, related_name="tramite_chamado")
    criado_por = models.ForeignKey(User, related_name='tramite_criador', on_delete=models.CASCADE, null=True, blank=True)
    aceito_por = models.ForeignKey(User, related_name='tramite_receptor', on_delete=models.CASCADE, null=True, blank=True)
    setor_origem = models.ForeignKey(Setor, on_delete=models.CASCADE, null=False, blank=False, related_name="tramite_origem")
    setor_destino = models.ForeignKey(Setor, on_delete=models.CASCADE, null=False, blank=False, related_name="tramite_destino")
    criado_em = models.DateTimeField(auto_now_add=True)
    aceito_em = models.DateTimeField(auto_now_add=False, blank=True, null=True)

    def __str__(self):
        if self.aceito_por is not None:
            return f"{self.chamado.id} | {self.criado_por} ({self.setor_origem}) >> {self.setor_destino}({self.aceito_por}) às {self.aceito_em.strftime('%d/%m/%Y às %H:%M:%S')} {self.id}"

        return f"{self.chamado.id} | {self.setor_origem} --> {self.setor_destino} às {self.criado_em.strftime('%d/%m/%Y às %H:%M:%S')} {self.id}"

    class Meta:
        ordering = ['criado_em']

class UnidadeChamado(models.Model):
    chamado = models.ForeignKey(Chamado, on_delete=models.CASCADE, null=False, blank=False, related_name="unidade_chamado")
    unidade = models.ForeignKey(Unidade, on_delete=models.CASCADE, null=False, blank=False, related_name="chamado_unidade")
    alocado_por = models.ForeignKey(User, related_name='unidade_alocado_por', on_delete=models.CASCADE, null=True, blank=True)
    alocado_em = models.DateTimeField("unidade_alocado_em", auto_now=True)
    status = models.CharField(max_length=20, blank=False, default="EM_ANDAMENTO")


class AtendimentoPessoa(models.Model):
    chamado = models.ForeignKey(Chamado, on_delete=models.CASCADE, null=True, blank=False, related_name="atendimento_chamado")
    pessoa = models.ForeignKey(Pessoa, null=True, blank=True, related_name="pessoa_atendimento", on_delete=SET_NULL)
    acompanhante = models.ForeignKey(Pessoa, on_delete=models.CASCADE, null=True, blank=True, related_name="acompanhante")

    finalizado = models.BooleanField("Atendimento foi finalizado", blank=True, null=False, default=False)

    nome_provisorio = models.CharField("Nome provisório", null=True, blank=True, max_length=60)

    tipo = models.CharField("Tipo de atendimento", max_length=50, null=True, blank=True)
    risco = models.CharField("Risco", max_length=50, null=True, blank=True)
    queixa = models.TextField("Queixa", null=True, blank=True)

    pulso = models.CharField("Pulso", max_length=50, null=True, blank=True)
    pa = models.CharField("Pressão arterial", max_length=50, null=True, blank=True)
    fr = models.CharField("Frequência respiratória", max_length=50, null=True, blank=True)
    so2 = models.CharField("Saturação de oxigênio", max_length=50, null=True, blank=True)
    temperatura = models.CharField("Temperatura", max_length=50, null=True, blank=True)
    glicemia = models.CharField("Glicemia", max_length=50, null=True, blank=True)

    situacaoDoLocal = models.CharField("Situação do local", max_length=100, null=True, blank=True)
    situacaoVitima = models.CharField("Situação da vítima", max_length=100, null=True, blank=True)

    usoCinto = models.CharField("Uso de cinto de segurança", max_length=50, null=True, blank=True)
    usoCapacete = models.CharField("Uso de capacete", max_length=50, null=True, blank=True)
    acidenteTrabalho = models.BooleanField("Acidente de trabalho", default=False)

    dataHoraChegada = models.DateTimeField("Data e hora de chegada", null=True, blank=True)
    dataHoraSaida = models.DateTimeField("Data e hora de saída", null=True, blank=True)
    dataHoraChegadaDestino = models.DateTimeField("Data e hora de chegada ao destino", null=True, blank=True)
    dataHoraLiberacaoUnidade = models.DateTimeField("Data e hora de liberação da unidade", null=True, blank=True)

    observacoes = models.TextField("Observações", null=True, blank=True)
    lesaoTraumatica = BooleanField(default=False)
    descLesaoTraumatica = models.CharField("Descrição da lesão traumática", max_length=255, null=True, blank=True)
    choqueHipovolemico = BooleanField(default=False)

    pele = models.CharField("Pele", max_length=50, null=True, blank=True)
    queimadura = BooleanField(default=False)
    percQueimadura = models.FloatField("Percentual de queimadura", null=True, blank=True)
    tipoQueimadura = models.CharField("Tipo de queimadura", max_length=50, null=True, blank=True)
    grauQueimadura = models.CharField("Grau da queimadura", max_length=50, null=True, blank=True)
    glasgow = models.CharField("Escala de Glasgow", max_length=10, null=True, blank=True)
    dilacaoPupilar = models.CharField("Dilatação pupilar", max_length=50, null=True, blank=True)

    intercorreciaTransporte = BooleanField(default=False)
    descrIntercorreciaTransporte = models.CharField("Descrição da intercorrência no transporte", max_length=255, null=True, blank=True)
    destinoPaciente = models.CharField("Destino do paciente", max_length=100, null=True, blank=True)
    tipoReceptor = models.CharField("Tipo de receptor", max_length=50, null=True, blank=True)
    
    nomeReceptor = models.CharField("Nome do receptor", max_length=100, null=True, blank=True)
    numRegistroConselho = models.CharField("Número de registro no conselho", max_length=50, null=True, blank=True)
    tipoEvolucao = models.CharField("Tipo de evolução", max_length=50, null=True, blank=True)

    evolucao = models.TextField("Evolução", null=True, blank=True)
    conduta = models.CharField("Conduta", max_length=255, null=True, blank=True)
    condicaoPaciente = models.CharField("Condição do paciente", max_length=50, null=True, blank=True)
    diagnosticoMedico = models.TextField("Diagnóstico médico", null=True, blank=True)
    ginecoObstetrico = models.BooleanField("Gineco-obstétrico", default=True)

    def __str__(self):
        return f"Atendimento: chamado = {self.chamado.id}, vitima=({self.nome_provisorio})"

    @property
    def nome_provisorio_asterisco(self):
        return self.nome_provisorio + '***'

    class Meta:

        permissions = (
            ('detail_chamado', 'Pode ver os detalhes do atendimento do chamado'),
        )