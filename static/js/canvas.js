import { rgbParaHex } from './uteis.js';
import { tornarElementoArrastavel, tornarElementoRedimencionavel } from './interact-config.js';
import { fontes } from './uteis.js';

let elementoSelecionado = null;

// Lógica de propriedades
const props = {
    texto: document.getElementById('prop-texto-conteudo'),
    fonte: document.getElementById('prop-fonte-familia'),
    fundo: document.getElementById('prop-cor-fundo'),
    cor: document.getElementById('prop-cor-texto'),
    tamanho: document.getElementById('prop-tamanho-fonte'),
    peso: document.getElementById('prop-peso-fonte'),
    borda: document.getElementById('prop-borda'),
    alinhamento: document.querySelectorAll('#prop-botoes-alinhamento > button'),
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

export function criarElementoRelatorio(tipo, x, y, container, dadosAdicionais = {}) {
    let el;
    
    if (tipo === 'texto') {
        el = criarTexto();
    } else if (tipo === 'h1') {
        el = criarH1();
    } else if (tipo === 'h2') {
        el = criarH2();
    } else if (tipo === 'tabela') {
        el = criarTabela();
    } else if (tipo === 'imagem'){
        el = criarImagem(dadosAdicionais['src']);
    }
    
    el.classList.add('elemento-relatorio');
    el.dataset.tipo = tipo;
    el.style.left = `${x}px`; 
    el.style.top = `${y}px`;
    el.dataset.x = 0; 
    el.dataset.y = 0;

    const objetoInteract = interact(el);
    tornarElementoArrastavel(objetoInteract);
    if(tipo == 'tabela'){
        tornarElementoRedimencionavel(objetoInteract, {
            right: true, left: true, top: false, bottom: false
        });
    } else if (tipo !== 'imagem'){
        tornarElementoRedimencionavel(objetoInteract);
    }
    
    container.appendChild(el);
    selecionarElemento(el);
}

function criarTexto(){
    const el = document.createElement('div');
    el.classList.add('el-texto'); 
    el.innerHTML = '<div style="margin:auto;">Texto editável</div>';
    el.style.fontSize = '14px'; el.style.color = '#000';
    el.style.width = '200px';
    el.style.height = '50px';
    el.style.display = "flex";
    el.style.padding = '0';

    return el;
}

function criarH1(){
    const el = document.createElement('h1');
    el.innerText = 'Título 1';
    el.style.width = '200px';
    el.style.height = '50px';
    el.style.textAlign = 'center';

    return el;
}

function criarH2(){
    const el = document.createElement('h2');
    el.innerText = 'Título 2';
    el.style.width = '200px';
    el.style.height = '50px';
    el.style.textAlign = 'center';

    return el;
}

function criarTabela(){
    const el = document.createElement('table');
    el.style.borderCollapse = 'collapse';
    el.innerHTML = `
        <thead>
            <tr>
                <th>Coluna 1</div></th>
                <th>Coluna 2</div></th>
                <th>Coluna 3</div></th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>{}</td>
                <td>{}</td>
                <td>{}</td>
            </tr>
        </tbody>
    `;
    el.dataset.configConsulta = "{}";

    return el;
}

export function criarImagem(src){
    const el = document.createElement('img');
    el.src = src;
    el.style.maxHeight = '65px';

    return el;
}

export function tornarComponentesDaTabelasRedimensionaveis(elementoTabela){
    const cabeçalhos = elementoTabela.querySelectorAll('thead tr > th');
    
    cabeçalhos.forEach((elemento) => {
        let objInt = interact(elemento);
        tornarElementoRedimencionavel(objInt, {
            left: false,
            right: true,
            bottom: true,
            top: false
        });
    });
}

export function atualizarPainelPropriedades() {
    const painel = document.getElementById('painel-propriedades'); 
    const vazio = document.getElementById('propriedades-vazio');
    
    if (!elementoSelecionado) { 
        painel.classList.add('d-none'); 
        vazio.classList.remove('d-none'); 
        return; 
    }

    painel.classList.remove('d-none'); 
    vazio.classList.add('d-none');

    const tipo = elementoSelecionado.dataset.tipo;

    let force = true;
    if (tipo === 'texto' || tipo === 'h1' || tipo === 'h2'){
        force = false;
    }

    document.getElementById('grupo-prop-conteudo-texto').classList.toggle('d-none', force);
    document.getElementById('grupo-prop-tabela').classList.toggle('d-none', tipo !== 'tabela');

    if (tipo === 'texto' || tipo === 'h1' || tipo === 'h2') {
        props.texto.value = elementoSelecionado.childNodes[0]?.nodeValue || elementoSelecionado.innerText;
    }
    props.tamanho.value = parseInt(window.getComputedStyle(elementoSelecionado).fontSize);

    let alinhamento;
    if(elementoSelecionado.dataset.tipo == 'texto'){
        alinhamento = elementoSelecionado.children[0].style.textAlign;
    } else {
        alinhamento = elementoSelecionado.style.textAlign;
    }

    props.alinhamento.forEach(btn => {
        if(btn.dataset.align == alinhamento){
            btn.classList.add('ativo');
        }
        else {
            btn.classList.remove('ativo');
        }
    });

    // estilos comuns
    const estilo = window.getComputedStyle(elementoSelecionado);
    props.fundo.value = estilo.backgroundColor === 'rgba(0, 0, 0, 0)' ? '#ffffff' : rgbParaHex(estilo.backgroundColor);
    props.fonte.value = elementoSelecionado.style.fontFamily ?  elementoSelecionado.style.fontFamily : fontes[0].valor;
    props.cor.value = rgbParaHex(estilo.color);
}

export function inicializarOuvintesPropriedades() {
    props.texto.addEventListener('input', (e) => { 
        let tipo = elementoSelecionado?.dataset.tipo;
        if (tipo === 'texto') { 
            const divTexto = elementoSelecionado.children[0];
            divTexto.innerText = e.target.value;
            divTexto.style.width = elementoSelecionado.style.width;
        } else if(tipo === 'h1' || tipo === 'h2'){
            elementoSelecionado.innerText = e.target.value;
        }
    });
    props.fundo.addEventListener('input', (e) => { 
        if (elementoSelecionado) 
        elementoSelecionado.style.backgroundColor = e.target.value; 
    });
    props.fonte.addEventListener('change', (e) => { 
        if (elementoSelecionado) 
        elementoSelecionado.style.fontFamily = e.target.value; 
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
        if (elementoSelecionado){
            const border = e.target.value;
            elementoSelecionado.style.border = border;
        } 
    });

    props.alinhamento.forEach(btn => {
        btn.addEventListener('click', (e) => {
            if (!elementoSelecionado) 
                return;

            const botao = e.target.closest('.btn-align');
            const alinhamento = botao.dataset.align;

            if(elementoSelecionado.dataset.tipo == 'texto'){                
                elementoSelecionado.children[0].style.textAlign = alinhamento;
            } else {
                elementoSelecionado.style.textAlign = alinhamento;
            }

            props.alinhamento.forEach(b => b.classList.remove('ativo'));
            botao.classList.add('ativo');
        });
    });
}