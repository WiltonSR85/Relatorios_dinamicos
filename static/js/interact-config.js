// configuração do Interact.js (biblioteca de arrastar/redimensionar)
export function tornarElementoArrastavel(objetoInteract){
    objetoInteract.draggable({
        listeners: {
            move(evento) {
                const t = evento.target;
                const x = (parseFloat(t.dataset.x) || 0) + evento.dx;
                const y = (parseFloat(t.dataset.y) || 0) + evento.dy;
                t.style.transform = `translate(${x}px, ${y}px)`; 
                Object.assign(t.dataset, { x, y });
            }
        },
        modifiers: [interact.modifiers.restrictRect({ 
            restriction: 'parent', 
        })]
    });
}

export function tornarElementoRedimencionavel(objetoInteract, edges = { 
    left: true, right: true, bottom: true, top: true 
}){
    objetoInteract.resizable({
        edges: edges,
        listeners: {
            move(evento) {
                let { x, y } = evento.target.dataset;
                x = (parseFloat(x) || 0) + evento.deltaRect.left; 
                y = (parseFloat(y) || 0) + evento.deltaRect.top;
                Object.assign(evento.target.style, { 
                    width: `${evento.rect.width}px`, 
                    height: `${evento.rect.height}px`, 
                    transform: `translate(${x}px, ${y}px)` 
                });
                Object.assign(evento.target.dataset, { x, y });
            }
        },
        modifiers: [
            interact.modifiers.restrictEdges({
                outer: 'parent',
            }),
        ]
    });
}

// função para tornar o elemento redimensionável por gestos de pinça em dispositivos de toque
export function tornarElementoManipulavel(objetoInteract, elementoDeEscala){
    let escala = 1;
    
    objetoInteract.gesturable({
        listeners: {
            move (event) {
                let escalaAtual = event.scale * escala;
                elementoDeEscala.style.transform = `scale(${escalaAtual})`;
            },
            end (event) {
                escala = escala * event.scale;
            }
        }
    });
}