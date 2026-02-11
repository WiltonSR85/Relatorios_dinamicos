from django.db import models
from base.models import Base
from django.core.validators import MinValueValidator

class Unidade(models.Model):

    nome = models.CharField(verbose_name="Nome da Unidade", max_length=255)
    base = models.ForeignKey(Base, on_delete=models.CASCADE, related_name='unidades_operacionais', verbose_name="Base Operacional", null=True, blank=True)
    tipo = models.CharField(verbose_name="Tipo", max_length=255, null=True, blank=True)
    fabricante = models.CharField(verbose_name="Fabricante", max_length=255, null=True, blank=True)
    modelo = models.CharField(verbose_name="Modelo", max_length=255, null=True, blank=True)
    cor = models.CharField(verbose_name="Cor", max_length=255, null=True, blank=True)
    chassi = models.CharField(verbose_name="Chassi", max_length=255, unique=True, null=True, blank=True)
    renavam = models.CharField(verbose_name="Renavam", max_length=255, unique=True, null=True, blank=True)
    placa = models.CharField(verbose_name="Placa", max_length=255, unique=True, help_text="Ex: XXX-9X99", null=True, blank=True)
    status = models.CharField(verbose_name="Status", max_length=20, null=True, blank=True, default="DISPONIVEL")
    lotacao = models.IntegerField(verbose_name="Lotação", validators=[MinValueValidator(1)], null=True, blank=True)
    ano = models.IntegerField(verbose_name="Ano de fabricação",null=True, blank=True)
    criado_em = models.DateTimeField(verbose_name="Criado em", auto_now_add=True, blank=True)
    criado_por = models.ForeignKey("auth.User", blank=True, null=True, verbose_name="Criado por", on_delete=models.SET_NULL, related_name="unidades_criadas")

    def __str__(self):
        return self.nome

    class Meta:

        permissions = (
            ('detail_unidade', 'Pode ver os detalhes da unidade'),
        )