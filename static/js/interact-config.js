// configuração do Interact.js (biblioteca de arrastar/redimensionar)
export function tornarElementoArrastavel(objetoInteract){
    objetoInteract.draggable({
        listeners: {
            move(evento) {
                if (!evento.target.classList.contains('selecionado')){
                    selecionarElemento(evento.target);
                } 
                const t = evento.target;
                const x = (parseFloat(t.dataset.x) || 0) + evento.dx;
                const y = (parseFloat(t.dataset.y) || 0) + evento.dy;
                t.style.transform = `translate(${x}px, ${y}px)`; 
                Object.assign(t.dataset, { x, y });
            }
        },
        modifiers: [interact.modifiers.restrictRect({ 
            restriction: 'parent', 
            endOnly: false 
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
        }
    });
}