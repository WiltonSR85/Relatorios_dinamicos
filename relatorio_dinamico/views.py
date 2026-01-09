import json
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import render
from .construtores import ConstrutorHTML, ConstrutorConsulta
from .models import Relatorio
from django.utils.encoding import force_str
from setup.esquema import esquema_bd
from weasyprint import HTML
from django.core.exceptions import FieldError, ValidationError
import nh3

def index(request):
    return render(request, 'index.html')

def retornar_esquema(request):
    return JsonResponse(esquema_bd)

def editor(request):
    return render(request, 'editor.html')

@require_POST
def gerar_sql(request):
    try:
        configuracao_consulta = json.loads(request.body.decode('utf-8'))
    except Exception as e:
        return JsonResponse({'error': 'JSON inválido', 'detail': str(e)}, status=400)
    
    construtor_consulta = ConstrutorConsulta(esquema_bd, configuracao_consulta)
    try:
        queryset = construtor_consulta.criar_queryset()
        sql = str(queryset.query)
        return JsonResponse({'sql': sql})

    except (FieldError, ValidationError) as e:
        return JsonResponse({'error': 'Erro na construção da consulta', 'detail': str(e)}, status=400)

@require_POST
def gerar_pdf(request):
    try:
        dados_recebidos = json.loads(request.body.decode('utf-8'))
    except Exception as e:
        return JsonResponse({'error': 'JSON inválido', 'detail': str(e)}, status=400)

    html = dados_recebidos.get('html')
    try:
        html_final = ConstrutorHTML.gerar_html(esquema_bd, html, "_pdf_dinamico.html")
    except (FieldError, ValidationError) as e:
        return JsonResponse({'error': 'Erro na construção da consulta', 'detail': str(e)}, status=400)

    with open('templates/teste.html', 'w', encoding='utf-8') as arquivo:
        arquivo.write(html_final)


    try:
        pdf = HTML(string=html_final, base_url=request.build_absolute_uri('/')).write_pdf()
    except Exception as e:
        return JsonResponse({'error': 'Erro ao gerar PDF', 'detail': str(e)}, status=500)

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="relatorio.pdf"'
    return response

@require_POST
def salvar_relatorio(request):
    data = json.loads(force_str(request.body))

    nome = data.get('nome')
    html = data.get('html')

    if not nome or not html:
        return JsonResponse(
            {'error': 'Campos obrigatórios ausentes: nome e html'},
            status=400
        )

    tags = {"div", "h1", "h2", "img", "table", "thead", "tbody", "tr", "td", "header", "main", "footer"}
    atributos = {"class", "style", "data-x", "data-y", "data-tipo", "src"}
    tags_e_atributos = {}

    for tag in tags:
        tags_e_atributos[tag] = atributos

    html_limpo = nh3.clean(html, tags=tags, attributes=tags_e_atributos)

    modelo = Relatorio.objects.create(nome=nome, html=html_limpo)

    return JsonResponse({'success': True, 'id': modelo.id})
    
def testar(request):
    from django.template.loader import render_to_string
    html = render_to_string('teste.html')
    pdf = HTML(string=html, base_url=request.build_absolute_uri('/')).write_pdf()
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="teste.pdf"'
    return response