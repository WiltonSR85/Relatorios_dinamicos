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
        html_final = ConstrutorHTML.inserir_dados_no_html(esquema_bd, html)
    except (FieldError, ValidationError) as e:
        return JsonResponse({'error': 'Erro na construção da consulta', 'detail': str(e)}, status=400)

    """ with open('html/relatorio.html', 'w', encoding='utf-8') as arquivo:
        arquivo.write(html_final)
        print("novo html salvo") """

    try:
        pdf = HTML(string=html_final, base_url=request.build_absolute_uri('/')).write_pdf()
    except Exception as e:
        return JsonResponse({'error': 'Erro ao gerar PDF', 'detail': str(e)}, status=500)

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="relatorio.pdf"'
    return response

def salvar_relatorio(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido'}, status=405)

    try:
        data = json.loads(force_str(request.body))

        nome = data.get('nome')
        html = data.get('html')

        if not nome or not html:
            return JsonResponse(
                {'error': 'Campos obrigatórios ausentes: nome e html'},
                status=400
            )

        modelo = Relatorio.objects.create(nome=nome, html=html)

        return JsonResponse({'success': True, 'id': modelo.id})

    except Exception as e:
        return JsonResponse(
            {'error': 'Erro interno ao salvar o modelo', 'detail': str(e)},
            status=500
        )