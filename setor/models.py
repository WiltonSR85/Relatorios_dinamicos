from django.db import models
from django.contrib.auth.models import User, Group
from base.models import Base

class Setor(Group):
    base = models.ForeignKey(Base, on_delete=models.CASCADE, related_name='base_setor', verbose_name="Base")
    membro = models.ManyToManyField(User, blank=True, related_name='membro_setor', verbose_name="Membros")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")

    criado_em = models.DateTimeField(verbose_name="Criado em", auto_now_add=True, blank=True)
    criado_por = models.ForeignKey("auth.User", blank=True, verbose_name="Criado por", on_delete=models.CASCADE, related_name="setor_criador")

    def __str__(self):  
        return f"{self.name} ({self.base.nome})"

    class Meta:

        permissions = (
            ('detail_setor', 'Pode ver os detalhes do setor'),
        )
