import { criarElementoRelatorio, selecionarElemento, desselecionarTudo, deletarElementoSelecionado, inicializarOuvintesPropriedades } from './canvas.js';
import * as CC from './construtor-consulta.js';
import { fontes, tiposDeDadosEntrada, formatarSQL } from './uteis.js';

// URLs para comunicação com o backend
const URL_SALVAR_RELATORIO = '/salvar_relatorio/';
const URL_GERAR_PDF = '/gerar_pdf/';
const URL_OBTER_SQL = '/obter_sql/';

window.addEventListener('DOMContentLoaded', () => {
    inicializarOuvintesPropriedades();
    CC.iniciarAplicacao();

    document.querySelector("#btn-abrir-editor").addEventListener("click", () => {
        const navPreview = document.getElementsByClassName('area-canvas')[0];
        navPreview.children[0].classList.remove('d-none');
        navPreview.children[1].classList.add('d-none');
    });

    document.getElementById("btn-confirmar-salvar-modelo").addEventListener("click", salvarModeloRelatorio);
    document.getElementById("btn-gerar-relatorio").addEventListener("click", gerarRelatorioFinal);
    document.getElementById("btn-deletar-elemento").addEventListener('click', deletarElementoSelecionado);


    document.getElementById("btn-configurar-consulta").addEventListener("click", CC.abrirConstrutorConsulta);
    document.getElementById("btn-salvar-config-tabela").addEventListener('click', CC.salvarConfiguracaoTabela);


    document.getElementById('select-raiz').addEventListener('change', (e) => {
        if (e.target.value) 
            CC.iniciarRaiz(e.target.value);
    });

    document.getElementById('lista-tabelas').addEventListener('click', (e) => {
        const btn = e.target.closest('.btn-add-join');
        if (btn) 
            CC.adicionarJuncao(btn.getAttribute('data-tab-id'), parseInt(btn.getAttribute('data-conn-idx')));
    });

    document.getElementById('lista-colunas-selecionadas').addEventListener('click', (e) => {
        const btn = e.target.closest('.btn-remover-col');
        if (btn) {
            CC.removerColuna(parseInt(btn.getAttribute('data-idx')));
        }
    });

    document.getElementById('tbody-filtros').addEventListener('click', (e) => {
        const btn = e.target.closest('.btn-remover-filtro');
        if (btn) 
            CC.removerFiltro(parseInt(btn.getAttribute('data-idx')));
    });

    document.getElementById('tbody-ordenacao').addEventListener('click', (e) => {
        const btn = e.target.closest('.btn-remover-ordenacao');
        if (btn) 
            CC.removerOrdenacao(parseInt(btn.getAttribute('data-idx')));
    });

    // Filtros e colunas 
    document.getElementById('select-col-tabela').addEventListener('change', (e) => {
        CC.atualizarSelectCampos(e.target.value, 'select-col-campo', 'btn-add-coluna');
    });

    document.getElementById('select-col-campo').addEventListener('change', (e) => {
        document.getElementById('btn-add-coluna').disabled = !e.target.value;
    });

    document.getElementById('btn-add-coluna').addEventListener('click', () => {
        CC.adicionarColuna();
        $("#collapseSQL").collapse('hide');
    });

    document.getElementById('select-filtro-tabela').addEventListener('change', (e) => {
        CC.atualizarSelectCampos(e.target.value, 'select-filtro-campo', 'btn-add-filtro')
    });
    
    document.getElementById('select-filtro-campo').addEventListener('change', (e) => {
        document.getElementById('btn-add-filtro').disabled = !e.target.value;
    });

    // ajusta o tipo de entrada conforme o tipo de dado do campo selecionado
    document.getElementById('select-filtro-campo').addEventListener('change', (e) => {
        const tipoCampo = e.target.options[e.target.selectedIndex].getAttribute('data-tipo');
        document.getElementById('input-filtro-valor').value = '';
        document.getElementById('input-filtro-valor').type = tiposDeDadosEntrada[tipoCampo] || 'text';
    });
    
    document.getElementById('btn-add-filtro').addEventListener('click', () => {
        CC.adicionarFiltro();
        $("#collapseSQL").collapse('hide');
    });

    document.getElementById('select-ordenacao-tabela').addEventListener('change', (e) => {
        CC.atualizarSelectCampos(e.target.value, 'select-ordenacao-campo', 'btn-add-ordenacao')
    });

    document.getElementById('select-ordenacao-campo').addEventListener('change', (e) => {
        document.getElementById('btn-add-ordenacao').disabled = !e.target.value;
    });

    document.getElementById('btn-add-ordenacao').addEventListener('click', () => {
        CC.adicionarOrdenacao();
        $("#collapseSQL").collapse('hide');
    });

    document.getElementById('input-limite-valor').addEventListener('input', (e) => {
        CC.adicionarLimite(e.target.value);
        $("#collapseSQL").collapse('hide');
    });

    document.getElementById('btn-obter-sql').addEventListener('click', obterSQL);

    Array.from(document.getElementsByClassName("item-arrastavel")).forEach(e => {
        e.addEventListener("dragstart", (e) => iniciarArrasto(e));
    });

    const paginaCanvas = document.getElementById("canvas-pagina");
    paginaCanvas.addEventListener("dragover", (e) => permitirSoltar(e));
    paginaCanvas.addEventListener("drop", (e) => soltar(e));

    paginaCanvas.addEventListener('mousedown', (e) => {
        const elementoPai = e.target.parentElement;
        if (elementoPai.id === 'canvas-pagina') 
            desselecionarTudo();
        else { 
            const el = e.target.closest('.elemento-relatorio'); 
            if (el) 
                selecionarElemento(el); 
        }
    });

    carregarFontes();
});

function carregarFontes(){
    const selectFontes = document.getElementById('prop-fonte-familia');
    for(let fonte of fontes){
        const opcao = document.createElement('option');
        opcao.value = fonte.valor;
        opcao.innerText = fonte.nome;
        selectFontes.appendChild(opcao);
    }
}

function iniciarArrasto(evento) { 
    const tipo = evento.target.getAttribute("data-tipo");
    evento.dataTransfer.setData("tipo", tipo);

    if(tipo === 'imagem'){
        const src = evento.target.getAttribute('src');
        evento.dataTransfer.setData("src", src);
    }
}

function permitirSoltar(evento) { 
    evento.preventDefault(); 
}

function soltar(evento) {
    evento.preventDefault();
    const tipo = evento.dataTransfer.getData("tipo");

    const objParam = {}
    if(tipo === 'imagem'){
        objParam['src'] = evento.dataTransfer.getData('src');
        console.log(objParam);
    }

    const alvo = evento.target;
    let conteinerElemento;

    if(alvo.closest("#header")){
        conteinerElemento = alvo.closest("#header");
    } else if(alvo.closest("#main")){
        conteinerElemento = alvo.closest("#main");
    } else if(alvo.closest("#footer")){
        conteinerElemento = alvo.closest("#footer");
    }
    
    const rect = conteinerElemento.getBoundingClientRect();

    criarElementoRelatorio(tipo, evento.clientX - rect.left, evento.clientY - rect.top, conteinerElemento, objParam);
}

function getCSRFToken() {
    const v = document.querySelector("input[name='csrfmiddlewaretoken']");
    return v.value;
}

async function gerarRelatorioFinal() {
    const csrftoken = getCSRFToken();

    const resp = await fetch(URL_GERAR_PDF, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken         // header exigido pelo Django CSRF
        },
        body: JSON.stringify({
            html: getHTML()
        })
    });

    if (!resp.ok) {
        const ct = resp.headers.get('content-type') || '';
        let msgErro = '';
        let detalheErro = '';

        if(ct.includes('application/json')){
            const data = await resp.json();
            msgErro = data.error;
            detalheErro = data.detail || '';
            alert(`${msgErro}: ${detalheErro}`);
        }
        return;
    }

    const ct = resp.headers.get('content-type') || '';
    if (ct.includes('application/pdf')) {
        const blob = await resp.blob();
        const preview = document.createElement('object');
        preview.data = window.URL.createObjectURL(blob);
        preview.type = "application/pdf";
        preview.innerText = "Pré-visualização do PDF gerado";

        preview.style.height = "240mm";
        preview.style.width = "210mm";
        preview.style.maxWidth = "100%";

        const navPreview = document.getElementsByClassName('area-canvas')[0];
        navPreview.children[0].classList.add('d-none');
        navPreview.children[1].classList.remove('d-none');
        navPreview.children[1].innerHTML = '';
        navPreview.children[1].append(preview);

    } else {
        const text = await resp.text();
        alert('Resposta inesperada: ' + text.slice(0, 500));
    }
}

function getHTML(){
    return `
        <!DOCTYPE html>
        <html lang="pt-br">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                @page { size: A4; }
                header, main, footer { position: relative; }
                header { height: 100px; }
                .elemento-relatorio { position: absolute; }
                table, th, td { border: 1px solid black; border-collapse: collapse; }
            </style>
        </head>
        <body>
            ${document.getElementById('canvas-pagina').innerHTML}
        </body>
        </html>
    `;    
}

function salvarModeloRelatorio() {
    const nome = document.getElementById('relatorio-nome').value || 'Relatório sem nome';
    const html = getHTML();

    fetch(URL_SALVAR_RELATORIO, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({
            nome: nome,
            html: html
        })
    })
    .then(resp => resp.json())
    .then(data => {
        if (data.success) {
            alert('Modelo salvo com sucesso!');
            $('#salvarModeloRelatorio').modal('hide'); 
        } else {
            alert('Erro ao salvar modelo: ' + (data.error || JSON.stringify(data)));
        }
    });
}

async function obterSQL(){
    const containerSQL = document.querySelector("#codigo-SQL");
    const cargaUtil = CC.gerarCargaUtil();

    if(cargaUtil.colunas.length === 0){
        containerSQL.innerHTML = `<p class="px-3 py-4 mb-0 text-center text-danger">Nenhuma coluna foi especificada para a consulta.</p>`;
        return;
    }

    containerSQL.innerHTML = `
        <div class="d-flex justify-content-center">
            <div class="spinner-border" role="status">
                <span class="sr-only">Carregando...</span>
            </div>
        </div>
    `;

    const res = await fetch(URL_OBTER_SQL, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify(cargaUtil)
    });

    if(!res.ok){
        const ct = res.headers.get('content-type') || '';
        console.log(res.headers);
        let msgErro = '';
        let detalheErro = '';

        if(ct.includes('application/json')){
            const data = await res.json();
            msgErro = data.error;
            detalheErro = data.detail || '';
        }
        containerSQL.innerHTML = `<p class="px-3 py-4 mb-0 text-center text-danger">Houve um erro ao obter SQL. ${msgErro}: ${detalheErro}</p>`;
        return;
    }

    const json = await res.json();
    const sql = json['sql'];
    containerSQL.innerHTML = `<code>${formatarSQL(sql)}</code>`;
}