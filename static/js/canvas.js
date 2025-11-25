import { rgbParaHex } from './uteis.js';
import { tornarElementoArrastavel, tornarElementoRedimencionavel } from './interact-config.js';

export const fontes = [
    { valor: "'Segoe UI', Roboto, Helvetica, Arial, sans-serif", nome: "Padrão (Sans-serif)" },
    { valor: "'Times New Roman', Times, serif", nome: "Times New Roman" },
    { valor: "'Courier New', Courier, monospace", nome: "Courier New" },
];


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

export function criarElementoRelatorio(tipo, x, y) {
    let el;
    
    if (tipo === 'texto') {
        el = document.createElement('div');
        el.classList.add('el-texto'); 
        el.innerHTML = '<div style="margin:auto;">Texto editável</div>';
        el.style.fontSize = '14px'; el.style.color = '#000';
        el.style.width = '200px';
        el.style.height = '50px';
        el.style.display = "flex";
        el.style.padding = '0';
    } else if (tipo === 'tabela') {
        el = document.createElement('table')
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
    } 
    
    el.classList.add('elemento-relatorio');
    el.id = `el-${Date.now()}`;
    el.dataset.tipo = tipo;
    el.style.left = `${x}px`; 
    el.style.top = `${y}px`;
    el.dataset.x = 0; 
    el.dataset.y = 0;

    const objetoInteract = interact(el);
    tornarElementoArrastavel(objetoInteract);
    if(tipo == 'tabela')
        tornarElementoRedimencionavel(objetoInteract, {
            right: true, left: true, top: false, bottom: false
        });
    else 
        tornarElementoRedimencionavel(objetoInteract);
    
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
        if (elementoSelecionado?.dataset.tipo === 'texto') { 
            const divTexto = elementoSelecionado.children[0];
            divTexto.innerText = e.target.value;
            divTexto.style.width = elementoSelecionado.style.width;
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

            if (elementoSelecionado.dataset.tipo == 'tabela'){
                const filhos = elementoSelecionado.querySelectorAll('th, td');                
                for(let f of filhos){
                    f.style.border = border;
                }
            }

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