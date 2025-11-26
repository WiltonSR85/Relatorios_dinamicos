from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('editor/', views.editor, name='editor'),
    path('gerar_pdf/', views.gerar_pdf, name='gerar_pdf'),
    path('esquema', views.retornar_esquema)
]