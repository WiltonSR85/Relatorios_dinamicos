import { rgbParaHex } from './uteis.js';

let elementoSelecionado = null;

// Lógica de propriedades
const props = {
    texto: document.getElementById('prop-texto-conteudo'),
    fundo: document.getElementById('prop-cor-fundo'),
    cor: document.getElementById('prop-cor-texto'),
    tamanho: document.getElementById('prop-tamanho-fonte'),
    peso: document.getElementById('prop-peso-fonte'),
    borda: document.getElementById('prop-borda')
};

export function getElementoSelecionado() {
    return elementoSelecionado;
}

export function selecionarElemento(el) {
    desselecionarTudo();
    elementoSelecionado = el;
    el.classList.add('selecionado');
    atualizarPainelPropriedades();
}

export function desselecionarTudo() {
    document.querySelectorAll('.elemento-relatorio.selecionado').forEach(el => el.classList.remove('selecionado'));
    elementoSelecionado = null;
    atualizarPainelPropriedades();
}

export function deletarElementoSelecionado() { 
    if (elementoSelecionado) { 
        elementoSelecionado.remove(); 
        selecionarElemento(null); 
    } 
}

export function criarElementoRelatorio(tipo, x, y) {
    const el = document.createElement('div');
    el.classList.add('elemento-relatorio');
    el.id = `el-${Date.now()}`;
    el.dataset.tipo = tipo;
    el.style.left = `${x}px`; el.style.top = `${y}px`;
    el.style.width = tipo === 'tabela' ? '400px' : '200px';
    el.style.height = tipo === 'tabela' ? '150px' : '50px';
    el.dataset.x = 0; el.dataset.y = 0;

    if (tipo === 'texto') {
        el.classList.add('el-texto'); el.innerText = 'Texto editável';
        el.style.fontSize = '14px'; el.style.color = '#000';
    } else if (tipo === 'tabela') {
        el.innerHTML = `<div class="el-tabela-placeholder"><div class="el-tabela-cabecalho">Tabela de dados</div><div class="el-tabela-corpo">Dados dinâmicos</div></div>`;
        el.dataset.configConsulta = "{}";
    } 

    document.getElementById('canvas-pagina').appendChild(el);
    selecionarElemento(el);
}

export function atualizarPainelPropriedades() {
    const painel = document.getElementById('painel-propriedades'), vazio = document.getElementById('propriedades-vazio');
    
    if (!elementoSelecionado) { 
        painel.classList.add('oculto-custom'); 
        vazio.classList.remove('oculto-custom'); 
        return; 
    }

    painel.classList.remove('oculto-custom'); vazio.classList.add('oculto-custom');

    const tipo = elementoSelecionado.dataset.tipo;
    document.getElementById('grupo-prop-conteudo-texto').classList.toggle('oculto-custom', tipo !== 'texto');
    document.getElementById('grupo-prop-tabela').classList.toggle('oculto-custom', tipo !== 'tabela');

    if (tipo === 'texto') {
        props.texto.value = elementoSelecionado.childNodes[0]?.nodeValue || elementoSelecionado.innerText;
        props.tamanho.value = parseInt(window.getComputedStyle(elementoSelecionado).fontSize);
    }

    if (tipo === 'tabela') {
        const conf = JSON.parse(elementoSelecionado.dataset.configConsulta || "{}");
        document.getElementById('status-consulta').innerHTML = conf.fonte_principal ?
            `<span class="text-success font-weight-bold">Configurado: ${conf.fonte_principal}</span>` : `<span class="text-danger">Não configurado</span>`;
    }

    // estilos comuns
    const estilo = window.getComputedStyle(elementoSelecionado);
    props.fundo.value = estilo.backgroundColor === 'rgba(0, 0, 0, 0)' ? '#ffffff' : rgbParaHex(estilo.backgroundColor);
    props.cor.value = rgbParaHex(estilo.color);
}

export function inicializarOuvintesPropriedades() {
    props.texto.addEventListener('input', (e) => { 
        if (elementoSelecionado?.dataset.tipo === 'texto') { 
            elementoSelecionado.innerText = e.target.value; 
        } 
    });
    props.fundo.addEventListener('input', (e) => { 
        if (elementoSelecionado) 
        elementoSelecionado.style.backgroundColor = e.target.value; 
    });
    props.cor.addEventListener('input', (e) => { 
        if (elementoSelecionado)
        elementoSelecionado.style.color = e.target.value; 
    });
    props.tamanho.addEventListener('input', (e) => { 
        if (elementoSelecionado) 
            elementoSelecionado.style.fontSize = e.target.value + 'px'; 
    });
    props.peso.addEventListener('change', (e) => { 
        if (elementoSelecionado) 
            elementoSelecionado.style.fontWeight = e.target.value; 
    });
    props.borda.addEventListener('change', (e) => { 
        if (elementoSelecionado) 
            elementoSelecionado.style.border = e.target.value === 'none' ? '1px dashed transparent' : e.target.value; 
    });
}