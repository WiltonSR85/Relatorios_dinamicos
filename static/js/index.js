document.getElementById('adicionarTexto').addEventListener('click', (e) => {
    criarElemento(e.target.dataset.type, 10, 10);
});

document.getElementById('adicionarTabela').addEventListener('click', (e) => {
    criarElemento(e.target.dataset.type, 10, 10);
});

const canvas = document.getElementById('page-canvas');
let contadorDeElementos = 0;
let elementoSelecionado;

const painel = document.getElementById('properties');

function tornarElementoArrastavel(objetoInteract, restricao) {
    objetoInteract.draggable({
        inertia: true,
        modifiers: [
            interact.modifiers.restrictRect({
                restriction: restricao,
            })
        ],
        listeners: {
            move: function(event) {
                var target = event.target;
                var x = (parseFloat(target.getAttribute('data-x')) || 0) + event.dx;
                var y = (parseFloat(target.getAttribute('data-y')) || 0) + event.dy;

                target.style.transform = 'translate(' + x + 'px, ' + y + 'px)';
                target.setAttribute('data-x', x);
                target.setAttribute('data-y', y);
            }
        }
    });
}

function tornarElementoRedimensionavel(objetoInteract, restricao) {
    objetoInteract.resizable({
        edges: { top: true, left: true, bottom: true, right: true },

        modifiers: [
            interact.modifiers.restrictSize({
                min: { width: 50, height: 50 },
                max: (element) => {
                    const containerRect = restricao.getBoundingClientRect();
                    return {
                        width: containerRect.width,
                        height: containerRect.height
                    };
                }
            })
        ],

        listeners: {
            move: function(event) {
                let { x, y } = event.target.dataset;

                x = (parseFloat(x) || 0) + event.deltaRect.left;
                y = (parseFloat(y) || 0) + event.deltaRect.top;

                Object.assign(event.target.style, {
                    width: `${event.rect.width}px`,
                    height: `${event.rect.height}px`,
                    transform: `translate(${x}px, ${y}px)`
                });

                Object.assign(event.target.dataset, { x, y });
            },
            /* end: function(event) {
                Object.assign(event.target.style, {
                    height: `auto',
                });
            } */
        }
    });
}

function criarElemento(type, x, y) {
    let element;
    
    switch(type) {
        case 'text':
            element = document.createElement('div');
            element.className = `canvas-element ${type}-element element-content`;
            element.id = `element-${++contadorDeElementos}`;
            element.style.left = x + 'px';
            element.style.top = y + 'px';
            element.style.textAlign = 'center';
            element.style.padding = '.5rem';
            element.style.width = '10rem';
            element.style.minHeight = '3rem';
            element.contentEditable = true;
            element.innerText = 'Digite seu texto aqui';
            break;
        case 'table':
            element = document.createElement('table');
            element.className = `canvas-element ${type}-element element-content data-table`;
            element.id = `element-${++contadorDeElementos}`;
            element.style.left = x + 'px';
            element.style.top = y + 'px';
            element.innerHTML = `
                    <tr contenteditable="true">
                        <th>Coluna 1</th>
                        <th>Coluna 2</th>
                        <th>Coluna 3</th>
                    </tr>
                    <tr>
                        <td>Dado 1</td>
                        <td>Dado 2</td>
                        <td>Dado 3</td>
                    </tr>
            `;
            break;
    }

    canvas.appendChild(element);
    
    const objetoInteract = interact(element);
    tornarElementoArrastavel(objetoInteract, canvas);
    tornarElementoRedimensionavel(objetoInteract, canvas);
    tornarElementoSelecionavel(objetoInteract);
}


function tornarElementoSelecionavel(objetoInteract) {
    objetoInteract.on('click', (e) => {
        if (elementoSelecionado) {
            elementoSelecionado.classList.remove('selected');
        }
    
        elementoSelecionado = e.target;
        elementoSelecionado.classList.add('selected');
        atualizarPainelDePropriedades();
    });
}

 
function atualizarPainelDePropriedades() {
    if (!elementoSelecionado) {
        painel.innerHTML = '<div class="no-selection">Selecione um elemento para editar suas propriedades</div>';
        return;
    }
    
    const estiloAtual = window.getComputedStyle(elementoSelecionado);

    painel.innerHTML = `
        <div class="mb-2">
            <h3 class="h6 text-danger">Formatação de texto</h3>
            <div class="style-buttons d-flex " style="gap:.25rem;">
                <button class="style-btn flex-grow-1 ${estiloAtual.fontWeight === '700' ? 'active-style-btn' : ''}" title="Negrito" value="bold">
                    <strong>B</strong>
                </button>
                <button class="style-btn flex-grow-1 ${estiloAtual.fontStyle === 'italic' ? 'active-style-btn' : ''}" title="Itálico" value="italic">
                    <em>I</em>
                </button>
                <button class="style-btn flex-grow-1 ${estiloAtual.textDecoration === 'underline' ? 'active-style-btn' : ''}" title="Sublinhado" value="underline">
                    <u>U</u>
                </button>
                <button class="style-btn flex-grow-1 ${estiloAtual.textDecoration === 'line-through' ? 'active-style-btn' : ''}" title="Tachado" value="line-through">
                    <s>S</s>
                </button>
            </div>
        </div>

        <div class="mb-2">
            <h3 class="h6 text-danger">Alinhamento</h3>
            <div class="align-buttons d-flex" style="gap:.25rem;">
                <button class="style-btn flex-grow-1 mdi mdi-format-align-left ${estiloAtual.textAlign === 'left' ? 'active-style-btn' : ''}" value="left" title="Esquerda" aria-label="Esquerda"></button>

                <button class="style-btn flex-grow-1 mdi mdi-format-align-center ${estiloAtual.textAlign === 'center' ? 'active-style-btn' : ''}" value="center" title="Centro" aria-label="Centro"></button>

                <button class="style-btn flex-grow-1 mdi mdi-format-align-right ${estiloAtual.textAlign === 'right' ? 'active-style-btn' : ''}" value="right" title="Direita" aria-label="Direita"></button>

                <button class="style-btn flex-grow-1 mdi mdi-format-align-justify ${estiloAtual.textAlign === 'justify' ? 'active-style-btn' : ''}" value="justify" title="Justificar" aria-label="Justificar"></button>
            </div>
        </div>

        <div class="mb-2">
            <label class="h6 text-danger">Tamanho da fonte</label>
            <input type="number" class="property-input" value="${parseInt(estiloAtual.fontSize)}" min="8" max="72" id="botaoTamanhoFonte">
        </div>

        <div class="mb-2">
            <h3 class="h6 text-danger">Cores</h3>
            <div class="color-picker-group">
                <div class="color-picker-wrapper">
                    <label class="property-label">Cor do texto</label>
                    <input type="color" class="color-picker" value="${rgbToHex(estiloAtual.color)}" id="selecionadorCorDeTexto">
                </div>
                <div class="color-picker-wrapper">
                    <label class="property-label">Cor de fundo</label>
                    <input type="color" class="color-picker" value="${rgbToHex(estiloAtual.backgroundColor)}" id="selecionadorCorDeFundo">
                </div>
                <div class="color-picker-wrapper">
                    <label class="property-label">Cor da borda</label>
                    <input type="color" class="color-picker" value="${rgbToHex(estiloAtual.borderColor)}" id="selecionadorCorDaBorda">
                </div>
            </div>
        </div>

        <div class="mb-2">
            <h3 class="h6 text-danger">Borda</h3>
            <div class="d-flex gap-2">
                <input type="number" class="property-input" value="${parseInt(estiloAtual.borderWidth)}" min="0" max="20" id="bordaEspessura" placeholder="Espessura (px)" aria-label="Espessura da borda em pixels">
                <select class="property-input" id="bordaEstilo" aria-label="Estilo da borda">
                    <option value="solid" ${estiloAtual.borderStyle === 'solid' ? 'selected' : ''}>Sólida</option>
                    <option value="dashed" ${estiloAtual.borderStyle === 'dashed' ? 'selected' : ''}>Tracejada</option>
                    <option value="dotted" ${estiloAtual.borderStyle === 'dotted' ? 'selected' : ''}>Pontilhada</option>
                    <option value="double" ${estiloAtual.borderStyle === 'double' ? 'selected' : ''}>Dupla</option>
                    <option value="none" ${estiloAtual.borderStyle === 'none' ? 'selected' : ''}>Nenhuma</option>
                </select>
            </div>
        </div>

        <div class="mb-2">
            <label class="h6 text-danger">Fonte</label>
            <select class="property-input" id="selecaoDeFonte">                            
                <option value="Arial" ${estiloAtual.fontFamily.includes('Arial') ? 'selected' : ''}>Arial</option>
                <option value="Times New Roman" ${estiloAtual.fontFamily.includes('Times New Roman') ? 'selected' : ''}>Times New Roman</option>
                <option value="Courier New" ${estiloAtual.fontFamily.includes('Courier New') ? 'selected' : ''}>Courier New</option>
                <option value="Georgia" ${estiloAtual.fontFamily.includes('Georgia') ? 'selected' : ''}>Georgia</option>
                <option value="Verdana" ${estiloAtual.fontFamily.includes('Verdana') ? 'selected' : ''}>Verdana</option>
            </select>
        </div>
    `;
    atualizarEventosDoPainel();
}

function atualizarEventosDoPainel() {   
    const botoesDeEstilo = document.querySelectorAll('.style-buttons .style-btn');
    botoesDeEstilo.forEach((botao) => {
        botao.addEventListener('click', () => {
            const estilo = botao.value;
            aplicarEstilo(estilo);
            if (botao.classList.contains('active-style-btn')) {
                botao.classList.remove('active-style-btn');
            } else {
                botao.classList.add('active-style-btn');
            }
        });
    });

    const botoesDeAlinhamento = document.querySelectorAll('.align-buttons .style-btn');
    botoesDeAlinhamento.forEach((botao) => {
        botao.addEventListener('click', () => {
            const alinhamento = botao.value;
            aplicarAlinhamento(alinhamento);
            for (const b of botoesDeAlinhamento) {
                b.classList.remove('active-style-btn');
            }
            botao.classList.add('active-style-btn');
        });
    });

    const botaoTamanhoFonte = document.getElementById('botaoTamanhoFonte');
    botaoTamanhoFonte.addEventListener('change', () => {
        const tamanho = botaoTamanhoFonte.value;
        mudarTamanhoDaFonte(tamanho);
    });

    const selecionarCorDeTexto = document.getElementById('selecionadorCorDeTexto');
    selecionarCorDeTexto.addEventListener('input', () => {
        const cor = selecionarCorDeTexto.value;
        mudarCorDoTexto(cor);
    });

    const selecionadorCorDeFundo = document.getElementById('selecionadorCorDeFundo');
    selecionadorCorDeFundo.addEventListener('input', () => {
        const cor = selecionadorCorDeFundo.value;
        mudarCorDeFundo(cor);
    });

    const selecionadorCorDaBorda = document.getElementById('selecionadorCorDaBorda');
    selecionadorCorDaBorda.addEventListener('input', () => {
        const cor = selecionadorCorDaBorda.value;
        mudarCorDaBorda(cor);
    });

    const selecionarDeFonte = document.getElementById('selecaoDeFonte');
    selecionarDeFonte.addEventListener('change', () => {
        const fonte = selecionarDeFonte.value;
        mudarFonte(fonte);
    });

    const bordaEstilo = document.getElementById('bordaEstilo');
    bordaEstilo.addEventListener('change', () => {
        const estilo = bordaEstilo.value;
        mudarEstiloDaBorda(estilo);
    });

    const bordaEspessura = document.getElementById('bordaEspessura');
    bordaEspessura.addEventListener('change', () => {
        const espessura = bordaEspessura.value;
        mudarEspessuraDaBorda(espessura);
    });
}

function aplicarEstilo(style) {
    if (!elementoSelecionado) return;
    
    switch(style) {
        case 'bold':
            const isBold = elementoSelecionado.style.fontWeight === 'bold';
            elementoSelecionado.style.fontWeight = isBold ? 'normal' : 'bold';
            break;
        case 'italic':
            const isItalic = elementoSelecionado.style.fontStyle === 'italic';
            elementoSelecionado.style.fontStyle = isItalic ? 'normal' : 'italic';
            break;
        case 'underline':
            const isUnderline = elementoSelecionado.style.textDecoration.includes('underline');
            elementoSelecionado.style.textDecoration = isUnderline ? 'none' : 'underline';
            break;
        case 'line-through':
            const isStrike = elementoSelecionado.style.textDecoration.includes('line-through');
            elementoSelecionado.style.textDecoration = isStrike ? 'none' : 'line-through';
            break;
    }
}

function aplicarAlinhamento(align) {
    if (!elementoSelecionado) return;
    elementoSelecionado.style.textAlign = align;
}

function mudarTamanhoDaFonte(size) {
    if (!elementoSelecionado) return;
    elementoSelecionado.style.fontSize = size + 'px';
}

function mudarCorDoTexto(color) {
    if (!elementoSelecionado) return;
    elementoSelecionado.style.color = color;
}

function mudarCorDeFundo(color) {
    if (!elementoSelecionado) return;
    elementoSelecionado.style.backgroundColor = color;
}

function mudarFonte(font) {
    if (!elementoSelecionado) return;
    elementoSelecionado.style.fontFamily = font;
}

function mudarCorDaBorda(color) {
    if (!elementoSelecionado) return;
    elementoSelecionado.style.borderColor = color;
}

function mudarEstiloDaBorda(style) {
    if (!elementoSelecionado) return;
    elementoSelecionado.style.borderStyle = style;
}

function mudarEspessuraDaBorda(width) {
    if (!elementoSelecionado) return;
    elementoSelecionado.style.borderWidth = width + 'px';
}

function rgbToHex(rgb) {
    if (rgb.startsWith('#')) return rgb;
    const matches = rgb.match(/\d+/g);
    if (!matches) return '#000000';
    const [r, g, b] = matches;
    return '#' + [r, g, b].map(x => {
        const hex = parseInt(x).toString(16);
        return hex.length === 1 ? '0' + hex : hex;
    }).join('');
}

function deleteElement(btn) {
    const element = btn.parentElement;
    element.remove();
    if (elementoSelecionado === element) {
        elementoSelecionado = null;
        atualizarPainelDePropriedades();
    }
}

// Perde o foco ao clicar fora de um elemento
canvas.addEventListener('click', (e) => {
    if (e.target === canvas || e.target.classList.contains('canvas-grid')) {
        if (elementoSelecionado) {
            elementoSelecionado.classList.remove('selected');
            elementoSelecionado = null;
            atualizarPainelDePropriedades();
        }
    }
});