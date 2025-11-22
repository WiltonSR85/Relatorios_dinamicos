import json
import logging
from io import BytesIO
from pathlib import Path
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from django.templatetags.static import static
from django.utils.html import escape
from django.shortcuts import render
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)

def index(request):
    return render(request, 'index.html')

def editor(request):
    return render(request, 'editor.html')


@require_POST
def gerar_pdf(request):
    try:
        from weasyprint import HTML
    except Exception as e:
        return JsonResponse({'error': 'WeasyPrint não disponível', 'detail': str(e)}, status=500)

    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception as e:
        return JsonResponse({'error': 'JSON inválido', 'detail': str(e)}, status=400)

    elements = payload.get('elements', [])
    page = payload.get('page') or {}
    page_w = int(page.get('width') or  (210*96/25.4))
    page_h = int(page.get('height') or (297*96/25.4))

    css_url = request.build_absolute_uri(static('editor.css'))

    # dados simples para header/footer (sem HTML na view)
    header_logo = 'LOGO'
    header_title = 'Serviço de Atendimento - Relatório'
    footer_text = 'Rodapé padrão - contato: (xx) xxxx-xxxx'
    footer_page = 'Página 1'

    # passa apenas os elementos como dados (x, y, content) — sem gerar HTML na view
    content_items = []
    for el in elements:
        x = int(el.get('x', 0))
        y = int(el.get('y', 0))
        content = escape(el.get('content', ''))
        content_items.append({'x': x, 'y': y, 'content': content})

    context = {
        'css_url': css_url,
        'header_logo': header_logo,
        'header_title': header_title,
        'footer_text': footer_text,
        'footer_page': footer_page,
        'content_items': content_items,
        'page_w': page_w,
        'page_h': page_h,
    }

    # renderiza o HTML a partir do template (todo o markup fica no template)
    html = render_to_string('pdf_template.html', context)

    try:
        pdf = HTML(string=html, base_url=request.build_absolute_uri('/')).write_pdf()
    except Exception as e:
        return JsonResponse({'error': 'Erro ao gerar PDF', 'detail': str(e)}, status=500)

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="relatorio.pdf"'
    return response
