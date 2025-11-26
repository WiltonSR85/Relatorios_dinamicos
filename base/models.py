from django.db import models

class Base(models.Model):
    responsavel = models.ForeignKey("auth.User", null=True, blank=True, on_delete=models.CASCADE, related_name="resposavel_base")
    
    nome = models.CharField(verbose_name="Nome da base", max_length=255)
    
    cidade = models.CharField(verbose_name="Cidade", max_length=255)
    uf = models.CharField(verbose_name="Estado", max_length=2, null=True)
    logradouro = models.CharField(verbose_name="Logradouro:",  max_length=255, null=True, blank=True)
    bairro = models.CharField(verbose_name="Bairro:",  max_length=255, null=True, blank=True)
    numero = models.CharField(verbose_name="Número:",  max_length=20, null=True, blank=True)
    complemento = models.CharField(verbose_name="Complemento:",  max_length=255, null=True, blank=True)
    
    central = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Base Central",
        related_name='base_central'
    )  
    
    criado_em = models.DateTimeField(verbose_name="Criado em", auto_now_add=True, blank=True)
    criado_por = models.ForeignKey("auth.User", blank=True, verbose_name="Criado por", on_delete=models.CASCADE, related_name="base_criador")
    
    def __str__(self):
        return self.nome + "( " + self.cidade + " )"

    class Meta:

        permissions = (
            ('detail_base', 'Pode ver os detalhes da base'),
        )
