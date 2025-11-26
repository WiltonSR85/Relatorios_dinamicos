import json
import logging
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import render
from .utils import ConstrutorHTML
from setup.esquema import esquema_bd
from weasyprint import HTML

logger = logging.getLogger(__name__)

def index(request):
    return render(request, 'index.html')

def retornar_esquema(request):
    return JsonResponse(esquema_bd)


def editor(request):
    return render(request, 'editor.html')


@require_POST
def gerar_pdf(request):
    try:
        dados_recebidos = json.loads(request.body.decode('utf-8'))
    except Exception as e:
        return JsonResponse({'error': 'JSON inválido', 'detail': str(e)}, status=400)

    html = dados_recebidos.get('html')
    html_final = ConstrutorHTML.inserir_dados_no_html(esquema_bd, html)

    try:
        pdf = HTML(string=html_final, base_url=request.build_absolute_uri('/')).write_pdf()
    except Exception as e:
        return JsonResponse({'error': 'Erro ao gerar PDF', 'detail': str(e)}, status=500)

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="relatorio.pdf"'
    return response
