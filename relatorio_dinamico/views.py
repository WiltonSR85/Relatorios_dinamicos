import json
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import render
from .construtores import ConstrutorHTML, ConstrutorConsulta, ValidadorConsulta
from .models import Relatorio
from django.utils.encoding import force_str
from setup.esquema import esquema_bd
from weasyprint import HTML
from django.core.exceptions import FieldError, ValidationError
import nh3

def index(request):
    return render(request, 'links.html')

def novo(request):
    return render(request, 'index.html')

def editar(request, id):
    relatorio = Relatorio.objects.get(id=id)
    return render(request, "index.html", {"relatorio": relatorio})

def listar(request):
    relatorios = Relatorio.objects.all()
    return render(request, 'listar.html', {'relatorios': relatorios})

def retornar_esquema(request):
    return JsonResponse(esquema_bd)

@require_POST
def gerar_sql(request):
    try:
        configuracao_consulta = json.loads(request.body.decode('utf-8'))
    except Exception as e:
        return JsonResponse({'error': 'JSON inválido', 'detail': str(e)}, status=400)
    
    try:
        validador_consulta = ValidadorConsulta(esquema_bd, configuracao_consulta)
        config_consulta_valida = validador_consulta.validar()
        construtor_consulta = ConstrutorConsulta(config_consulta_valida)
        queryset = construtor_consulta.criar_queryset()
        sql = str(queryset.query)
        return JsonResponse({'sql': sql})

    except (FieldError, ValidationError, ValueError) as e:
        #return JsonResponse({'error': 'Erro na construção da consulta', 'detail': str(e)}, status=400)
        raise e

@require_POST
def gerar_pdf(request):
    try:
        dados_recebidos = json.loads(request.body.decode('utf-8'))
    except Exception as e:
        return JsonResponse({'error': 'JSON inválido', 'detail': str(e)}, status=400)

    html = dados_recebidos.get('html')
    try:
        construtor_html = ConstrutorHTML(esquema_bd, html, "_pdf_dinamico.html")
        html_final = construtor_html.gerar_html()
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
    id =  data.get('id')

    if not nome or not html:
        return JsonResponse(
            {'error': 'Campos obrigatórios ausentes: nome e html'},
            status=400
        )

    tags = {"div", "h1", "h2", "img", "table", "thead", "tbody", "tr", "th", "td", "header", "main", "footer"}
    atributos = {"class", "id", "style", "data-config-consulta", "data-x", "data-y", "data-tipo", "src"}
    tags_e_atributos = {}

    for tag in tags:
        tags_e_atributos[tag] = atributos

    html_limpo = nh3.clean(html, tags=tags, attributes=tags_e_atributos)
    
    if id:
        try:
            modelo = Relatorio.objects.get(id=id)
            modelo.nome = nome
            modelo.html = html_limpo
            modelo.save()
        except Relatorio.DoesNotExist:
            return JsonResponse({'error': 'Relatório não encontrado'}, status=404)
    else:
        modelo = Relatorio.objects.create(nome=nome, html=html_limpo)

    return JsonResponse({'success': True, 'id': modelo.id})

def excluir(request, id):
    from django.shortcuts import get_object_or_404, redirect

    relatorio = get_object_or_404(Relatorio, id=id)
    relatorio.delete()
    return redirect("listar_relatorio")

def testar_html(request):
    from django.template.exceptions import TemplateDoesNotExist
    from django.http import HttpResponse
    
    try:
        return render(request, 'teste.html')
    except TemplateDoesNotExist as e:
        return HttpResponse("<h1 style='text-align:center;'>Você ainda não gerou nenhum relatório</h1>")


def testar_pdf(request):
    from django.template.loader import render_to_string
    html = render_to_string('teste.html')
    pdf = HTML(string=html, base_url=request.build_absolute_uri('/')).write_pdf()
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="teste.pdf"'
    return response