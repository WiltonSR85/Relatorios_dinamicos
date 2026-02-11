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
    margemSuperior: document.getElementById('prop-margem-superior'),
    margemInferior: document.getElementById('prop-margem-inferior'),
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
    el.style.marginTop = '16px';
    el.style.marginBottom = '16px';
    el.dataset.x = 0; 
    el.dataset.y = 0;

    if(container.id == "main"){
        el.style.width = window.getComputedStyle(container).width;
    }

    container.appendChild(el);
    tornarElementoInterativo(el);
    selecionarElemento(el);
}

export function tornarElementoInterativo(el){
    const objetoInteract = interact(el);
    const tipo = el.dataset.tipo;
    
    /* se o elemento for adicionado à região principal do relatório, ele não 
    será arrastável porque o PDF gerado não refletia corretamente suas posições, poderá apenas ser redimensionado */
    if(el.parentElement.id !== "main"){
        tornarElementoArrastavel(objetoInteract);
    }

    if(tipo === 'tabela'){
        tornarElementoRedimencionavel(objetoInteract, {
            right: true, left: true, top: false, bottom: false
        });
        tornarCabecalhosDaTabelaRedimensionaveis(el);
    } else if (tipo !== 'imagem'){
        tornarElementoRedimencionavel(objetoInteract);
    }
}
function criarTexto(){
    const el = document.createElement('p');
    el.innerText = 'Texto editável';
    el.style.height = '50px';
    el.style.padding = '0';
    el.style.textAlign = 'center';

    return el;
}

function criarH1(){
    const el = document.createElement('h1');
    el.innerText = 'Título 1';
    el.style.height = '50px';
    el.style.textAlign = 'center';

    return el;
}

function criarH2(){
    const el = document.createElement('h2');
    el.innerText = 'Título 2';
    el.style.height = '50px';
    el.style.textAlign = 'center';

    return el;
}

function criarTabela(){
    const el = document.createElement('table');
    el.classList.add('table', 'table-sm');
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

export function tornarCabecalhosDaTabelaRedimensionaveis(elementoTabela){
    /* Permite redimensionar os cabeçalhos da tabela */
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
        props.texto.value = elementoSelecionado.innerText;
    }

    const estilo = window.getComputedStyle(elementoSelecionado);
    props.tamanho.value = parseInt(estilo.fontSize);
    let alinhamento;
    alinhamento = elementoSelecionado.style.textAlign;

    props.alinhamento.forEach(btn => {
        if(btn.dataset.align == alinhamento){
            btn.classList.add('ativo');
        }
        else {
            btn.classList.remove('ativo');
        }
    });

    // estilos comuns
    props.fundo.value = estilo.backgroundColor === 'rgba(0, 0, 0, 0)' ? '#ffffff' : estilo.backgroundColor;
    props.fonte.value = elementoSelecionado.style.fontFamily ?  elementoSelecionado.style.fontFamily : fontes[0].valor;
    props.cor.value = estilo.color;
    props.borda.value = estilo.border;    
    props.margemInferior.value = parseInt(estilo.marginBottom);
    props.margemSuperior.value = parseInt(estilo.marginTop);
}

export function inicializarOuvintesPropriedades() {
    props.texto.addEventListener('input', (e) => { 
        if (elementoSelecionado) 
            elementoSelecionado.innerText = e.target.value;
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
            const border = e.target.value || "";
            elementoSelecionado.style.border = border;
        } 
    });

    props.alinhamento.forEach(btn => {
        btn.addEventListener('click', (e) => {
            if (!elementoSelecionado) 
                return;

            const botao = e.target.closest('.btn-align');
            const alinhamento = botao.dataset.align;
            elementoSelecionado.style.textAlign = alinhamento;
            props.alinhamento.forEach(b => b.classList.remove('ativo'));
            botao.classList.add('ativo');
        });
    });

    props.margemSuperior.addEventListener('input', (e) => { 
        if (elementoSelecionado) 
            elementoSelecionado.style.marginTop = e.target.value + 'px'; 
    });

    props.margemInferior.addEventListener('input', (e) => { 
        if (elementoSelecionado) 
            elementoSelecionado.style.marginBottom = e.target.value + 'px'; 
    });
}