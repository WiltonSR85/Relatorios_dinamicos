from django.db import models

class Relatorio(models.Model):
    nome = models.CharField(max_length=255)
    html = models.TextField()
    criado_em = models.DateTimeField(auto_now_add=True)