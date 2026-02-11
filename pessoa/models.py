from django.contrib.auth.models import User
from django.db import models
from base.models import Base


# Create your models here.
class Pessoa(models.Model):
    imagem_perfil = models.ImageField(upload_to='perfil/', blank=True, null=True)

    usuario = models.OneToOneField(User, on_delete=models.CASCADE, blank=True, null=True)

    nome = models.CharField(max_length=100)
    email = models.EmailField(null=True, blank=True, unique=True)
    rg = models.CharField(max_length=20, null=True, blank=True, unique=True)

    cpf = models.CharField(
        verbose_name='CPF',
        max_length=14, # 14 dígitos (com pontuação)
        null=True,
        blank=True, # Campo obrigatório em formulários
        unique=True, # Garante que não haverá CPFs duplicados
    )    

    dataNascimentoReal = models.DateField("Data nascimento", null=True, blank=True)
    dataNascimentoEstimada = models.DateField("Data nascimento estimada", null=True, blank=True)
    sexo = models.CharField(max_length=2, null=True, blank=True)
    estadoCivil = models.CharField("Estado civil", max_length=20, null=True, blank=True)
    nacionalidade = models.CharField(max_length=2, null=True, default="BR")
    naturalidade = models.CharField(max_length=200, null=True, blank=True)
    telefone = models.CharField(max_length=20, null=True, blank=True)
    telefoneCelular = models.CharField(max_length=20, null=True, blank=True)


    uf = models.CharField("Estado", max_length=2, null=True)
    cidade = models.CharField(max_length=100, null=True, blank=True)
    logradouro = models.CharField(max_length=200, null=True, blank=True)
    numero = models.CharField(max_length=20, null=True, blank=True)
    complemento = models.CharField(max_length=100, null=True, blank=True)
    bairro = models.CharField(max_length=100, null=True, blank=True)
    cep = models.CharField(max_length=10, null=True, blank=True)

    historicoClinico = models.TextField("Histórico clínico", null=True, blank=True)

    nomeMae = models.CharField("Nome da mãe", max_length=100, null=True, blank=True)
    nomePai = models.CharField("Nome do pai", max_length=100, null=True, blank=True)

    telefoneMae = models.CharField("Telefone da mãe", max_length=20, null=True, blank=True)
    telefonePai = models.CharField("Telefone do pai", max_length=20, null=True, blank=True)
    telefoneResponsavel = models.CharField("Telefone responsável", max_length=20, null=True, blank=True)

    telefoneContato = models.CharField("Telefone contato",max_length=20, null=True, blank=True)
    telefoneRecado = models.CharField("Telefone recado",max_length=20, null=True, blank=True)

    tipoSanguineo = models.CharField("Tipo sanguineo", max_length=5, null=True, blank=True)
    alergias = models.TextField(null=True, blank=True)
    doencasPreExistentes = models.TextField("Doenças pre-existentes",null=True, blank=True)
    medicamentosEmUso = models.TextField("Medicamentos em uso",null=True, blank=True)

    deficienciaVisual = models.BooleanField("Deficiência visual", default=False)
    deficienciaAuditiva = models.BooleanField("Deficiência auditiva",default=False)
    deficienciaMotora = models.BooleanField("Deficiência motora",default=False)
    deficienciaIntelectual = models.BooleanField("Deficiência intelectual",default=False)

    observacoes = models.TextField(null=True, blank=True)
    criado_por = models.ForeignKey(User, related_name='pessoas_criadas', on_delete=models.SET_NULL, null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    base_cadastro = models.ForeignKey(Base, verbose_name="Base", on_delete=models.SET_NULL, null=True, blank=True, related_name='base_pessoa')
    criado_em = models.DateTimeField(verbose_name="Criado em", auto_now_add=True, blank=True)

    def __str__(self):
        return f"{self.nome} - {self.dataNascimentoReal.strftime('%d-%m-%Y')}"

    class Meta:

        permissions = (
            ('detail_pessoa', 'Pode ver os detalhes da pessoa'),
        )