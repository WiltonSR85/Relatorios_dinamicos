import json
import logging
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import render
from .utils import ConstrutorHTML
from .models import Relatorio
from django.utils.encoding import force_str
from django.views.decorators.csrf import csrf_exempt
from setup.esquema import esquema_bd
from weasyprint import HTML
#import bleach # ainda não instalado; será usado para limpar o HTML recebido e evitar XSS

logger = logging.getLogger(__name__)

def index(request):
    return render(request, 'index.html')

def retornar_esquema(request):
    return JsonResponse(esquema_bd)


def editor(request):
    return render(request, 'editor.html')


@require_POST
@csrf_exempt
def gerar_pdf(request):
    try:
        dados_recebidos = json.loads(request.body.decode('utf-8'))
    except Exception as e:
        return JsonResponse({'error': 'JSON inválido', 'detail': str(e)}, status=400)

    html = dados_recebidos.get('html')
    html_final = ConstrutorHTML.inserir_dados_no_html(esquema_bd, html)

    with open('html/relatorio.html', 'w', encoding='utf-8') as arquivo:
        arquivo.write(html_final)
        print("novo html salvo")

    try:
        pdf = HTML(string=html_final, base_url=request.build_absolute_uri('/')).write_pdf()
    except Exception as e:
        return JsonResponse({'error': 'Erro ao gerar PDF', 'detail': str(e)}, status=500)

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="relatorio.pdf"'
    return response

@csrf_exempt
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
        logger.error(f"Erro ao salvar modelo de relatório: {e}")
        return JsonResponse(
            {'error': 'Erro interno ao salvar o modelo', 'detail': str(e)},
            status=500
        )