//import { tornarElementoArrastavel } from './interact-config.js';
import { criarElementoRelatorio, selecionarElemento, desselecionarTudo, deletarElementoSelecionado, inicializarOuvintesPropriedades } from './canvas.js';
import * as CC from './construtor-consulta.js';
import { fontes } from './canvas.js';

console.log("index.js carregado");

window.addEventListener('DOMContentLoaded', () => {
    inicializarOuvintesPropriedades();
    CC.iniciarAplicacao();
    //CC.renderizarTudo();

    document.querySelector("#btn-abrir-editor").addEventListener("click", () => {
        const navPreview = document.getElementsByClassName('area-canvas')[0];
        navPreview.children[0].classList.remove('oculto-custom');
        navPreview.children[1].classList.add('oculto-custom');
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
        const elementoPai = e.target.parentElement;
        console.log(elementoPai);
        if (elementoPai.id === 'canvas-pagina') 
            desselecionarTudo();
        else { 
            const el = e.target.closest('.elemento-relatorio'); 
            if (el) 
                selecionarElemento(el); 
        }
    });

    //tornarElementoArrastavel('.elemento-relatorio');
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
    evento.dataTransfer.setData("tipo", evento.target.getAttribute("data-tipo")); 
}

function permitirSoltar(evento) { 
    evento.preventDefault(); 
}

function soltar(evento) {
    evento.preventDefault();
    const tipo = evento.dataTransfer.getData("tipo");
    const rect = document.getElementById('canvas-pagina').getBoundingClientRect();

    const alvo = evento.target;
    let conteinerElemento;

    if(alvo.closest("#header")){
        conteinerElemento = alvo.closest("#header");
    } else if(alvo.closest("#main")){
        conteinerElemento = alvo.closest("#main");
    } else if(alvo.closest("#footer")){
        conteinerElemento = alvo.closest("#footer");
    }
    
    criarElementoRelatorio(tipo, evento.clientX - rect.left, evento.clientY - rect.top, conteinerElemento);
}

function getCookie(name) {
    const v = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
    return v ? v.pop() : '';
}

async function gerarRelatorioFinal() {
    const csrftoken = getCookie('csrftoken');

    const resp = await fetch('/gerar_pdf/', {
        method: 'POST',
        credentials: 'same-origin',
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
        navPreview.children[0].classList.add('oculto-custom');
        navPreview.children[1].classList.remove('oculto-custom');
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
                .elemento-relatorio { position: absolute; }
            </style>
        </head>
        <body>
            ${document.getElementById('canvas-pagina').innerHTML}
        </body>
        </html>
    `;    
}

function salvarModeloRelatorio() {
    console.log("Função salvarTemplateJson chamada");
    const nome = document.getElementById('relatorio-nome').value || 'Relatório sem nome';
    const html = getHTML();

    fetch('/salvar_relatorio/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
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
            $('#salvarModeloRelatorio').modal('hide'); // Fecha o modal (usando jQuery/Bootstrap)
        } else {
            alert('Erro ao salvar modelo: ' + (data.error || JSON.stringify(data)));
        }
    });
}