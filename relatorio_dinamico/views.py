import json
import logging
from io import BytesIO
from pathlib import Path
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from django.templatetags.static import static
from django.utils.html import escape
from weasyprint import HTML
from django.shortcuts import render

logger = logging.getLogger(__name__)

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

    header_html = (
        '<div id="reportHeader" aria-label="Cabeçalho">'
        '<div class="header-element" id="headerLogo">LOGO</div>'
        '<div class="header-element" id="headerTitle">Serviço de Atendimento - Relatório</div>'
        '</div>'
    )
    footer_html = (
        '<div id="reportFooter" aria-label="Rodapé">'
        '<div class="footer-element" id="footerText">Rodapé padrão - contato: (xx) xxxx-xxxx</div>'
        '<div class="footer-element" id="footerPage">Página 1</div>'
        '</div>'
    )

    content_items = []
    for el in elements:
        x = int(el.get('x', 0))
        y = int(el.get('y', 0))
        content = escape(el.get('content', ''))
        content_items.append(f'<div class="elemento" style="position:absolute; left:{x}px; top:{y}px">{content}</div>')

    content_html = (
        f'<div id="reportContent" aria-label="Conteúdo editável" style="position:relative; width:{page_w}px; height:{max(0, page_h - 1)}px;">'
        + ''.join(content_items) +
        '</div>'
    )

    # monta html para o PDF (com overrides para remover margens e toolbar)
    page_style = (
        '<style>'
        '@page { size: A4; margin: 0; }'
        'html, body { margin: 0 !important; padding: 0 !important; background: transparent !important; }'
        '#toolbar { display: none !important; }'
        '#reportCanvas { margin: 0 !important; padding: 0 !important; box-shadow: none !important; }'
        '#reportHeader, #reportFooter { box-shadow: none !important; }'
        '</style>'
    )

    html = (
        '<!doctype html><html><head>'
        '<meta charset="utf-8">'
        f'<link rel="stylesheet" href="{css_url}">'
        + page_style +
        '</head><body>'
        f'<div id="reportCanvas" style="width:{page_w}px; height:{page_h}px; position:relative;">'
        f'{header_html}{content_html}{footer_html}'
        '</div>'
        '</body></html>'
    )

    try:
        pdf = HTML(string=html, base_url=request.build_absolute_uri('/')).write_pdf()
    except Exception as e:
        return JsonResponse({'error': 'Erro ao gerar PDF', 'detail': str(e)}, status=500)

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="relatorio.pdf"'
    return response
