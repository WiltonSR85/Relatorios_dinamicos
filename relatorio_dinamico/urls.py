from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('novo/', views.novo, name='novo'),
    path('gerar_pdf/', views.gerar_pdf, name='gerar_pdf'),
    path('esquema', views.retornar_esquema),
    path('salvar_relatorio/', views.salvar_relatorio, name='salvar_relatorio'),
    path('obter_sql/', views.gerar_sql),
    path('listar/', views.listar, name="listar_relatorio"),
    path('editar/<int:id>', views.editar, name="editar_relatorio"),
    path('excluir/<int:id>', views.excluir, name="excluir_relatorio"),
    path('testar', views.testar),
]