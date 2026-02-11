from django.contrib import admin
from .models import Chamado, TramiteChamado, UnidadeChamado, AtendimentoPessoa

admin.site.register(Chamado)
admin.site.register(TramiteChamado)
admin.site.register(UnidadeChamado)
admin.site.register(AtendimentoPessoa)
