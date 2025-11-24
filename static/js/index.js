import { tornarElementoArrastavel } from './interact-config.js';
import { criarElementoRelatorio, selecionarElemento, desselecionarTudo, deletarElementoSelecionado, inicializarOuvintesPropriedades } from './canvas.js';
import * as CC from './construtor-consulta.js';

window.addEventListener('DOMContentLoaded', () => {
    inicializarOuvintesPropriedades();
    CC.iniciarAplicacao();
    //CC.renderizarTudo();

    document.getElementById("btn-salvar-modelo").addEventListener("click", salvarTemplateJson);
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
        if (btn) 
            CC.removerColuna(parseInt(btn.getAttribute('data-idx')));
    });

    document.getElementById('tbody-filtros').addEventListener('click', (e) => {
        const btn = e.target.closest('.btn-remover-filtro');
        if (btn) 
            CC.removerFiltro(parseInt(btn.getAttribute('data-idx')));
    });

    // Filtros e colunas 
    document.getElementById('select-col-tabela').addEventListener('change', (e) => CC.atualizarSelectCampos(e.target.value, 'select-col-campo', 'btn-add-coluna'));
    document.getElementById('select-col-campo').addEventListener('change', (e) => document.getElementById('btn-add-coluna').disabled = !e.target.value);
    document.getElementById('btn-add-coluna').addEventListener('click', CC.adicionarColuna);

    document.getElementById('select-filtro-tabela').addEventListener('change', (e) => CC.atualizarSelectCampos(e.target.value, 'select-filtro-campo', 'btn-add-filtro'));
    document.getElementById('select-filtro-campo').addEventListener('change', (e) => document.getElementById('btn-add-filtro').disabled = !e.target.value);
    document.getElementById('btn-add-filtro').addEventListener('click', CC.adicionarFiltro);


    Array.from(document.getElementsByClassName("item-arrastavel")).forEach(e => {
        e.addEventListener("dragstart", (e) => iniciarArrasto(e));
    });

    const paginaCanvas = document.getElementById("canvas-pagina");
    paginaCanvas.addEventListener("dragover", (e) => permitirSoltar(e));
    paginaCanvas.addEventListener("drop", (e) => soltar(e));

    paginaCanvas.addEventListener('mousedown', (e) => {
        if (e.target.id === 'canvas-pagina') 
            desselecionarTudo();
        else { 
            const el = e.target.closest('.elemento-relatorio'); 
            if (el) 
                selecionarElemento(el); 
        }
    });

    tornarElementoArrastavel();
});

function iniciarArrasto(evento) { 
    evento.dataTransfer.setData("tipo", evento.target.getAttribute("data-tipo")); 
}

function permitirSoltar(evento) { 
    evento.preventDefault(); 
}

function soltar(evento) {
    evento.preventDefault();
    const tipo = evento.dataTransfer.getData("tipo");
    const rect = document.getElementById('canvas-pagina').getBoundingClientRect();
    criarElementoRelatorio(tipo, evento.clientX - rect.left, evento.clientY - rect.top);
}

function obterEsquemaRelatorio() {
    return Array.from(document.querySelectorAll('.elemento-relatorio')).map(el => {
        const style = window.getComputedStyle(el);
        const x = parseFloat(el.dataset.x) || 0;
        const y = parseFloat(el.dataset.y) || 0;
        return {
            id: el.id, 
            type: el.dataset.type,
            style: {
                left: (parseFloat(el.style.left) + x) + 'px', 
                top: (parseFloat(el.style.top) + y) + 'px',
                width: el.style.width, height: el.style.height,
                fontSize: style.fontSize, fontWeight: style.fontWeight,
                color: style.color, backgroundColor: style.backgroundColor, 
                border: style.border
            },
            content: el.dataset.type === 'text' ? el.innerText : null,
            query: el.dataset.type === 'table' ? JSON.parse(el.dataset.queryConfig || "{}") : null
        };
    });
}


function getCookie(name) {
    const v = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
    return v ? v.pop() : '';
}

async function gerarRelatorioFinal() {
    // envia posições relativas ao topo/esquerda da FOLHA (reportCanvas)
    const items = obterEsquemaRelatorio();
    const csrftoken = getCookie('csrftoken');

    const resp = await fetch('/gerar_pdf/', {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken         // header exigido pelo Django CSRF
        },
        body: JSON.stringify({
            elementos: items,
            html: getHTML()
        })
    });

    if (!resp.ok) {
        const ct = resp.headers.get('content-type') || '';
        if (ct.includes('application/json')) {
            const data = await resp.json();
            alert('Erro ao gerar PDF: ' + (data.error || JSON.stringify(data)));
        } else {
            const text = await resp.text();
            alert('Erro ao gerar PDF: HTTP ' + resp.status + '\n' + text.slice(0, 1000));
        }
        return;
    }

    const ct = resp.headers.get('content-type') || '';
    if (ct.includes('application/pdf')) {
        const blob = await resp.blob();
        const preview = document.createElement('object');
        preview.data = window.URL.createObjectURL(blob);
        preview.type = "application/pdf";


        preview.style.height = "297mm";
        preview.style.width = "210mm";
        preview.style.maxWidth = "100%";

        const navPreview = document.getElementsByClassName('area-canvas')[0];
        navPreview.innerHTML = "";
        navPreview.appendChild(preview);

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
        </head>
        <body>
            ${document.getElementById('canvas-pagina').outerHTML}
        </body>
        </html>
    `;    
}


function salvarTemplateJson() {
    console.log(obterEsquemaRelatorio());
}