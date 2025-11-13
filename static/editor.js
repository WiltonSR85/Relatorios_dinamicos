function getCookie(name) {
  const v = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
  return v ? v.pop() : '';
}

let elementos = [];

function addText() {
  const parent = document.getElementById('reportContent'); // agora adiciona no content
  const el = document.createElement('div');
  el.className = 'elemento';
  el.contentEditable = true;
  el.innerText = 'Novo texto';

  // posição inicial (clamp para dentro da área de conteúdo)
  const left = 10;
  const top = 10;
  el.style.left = left + 'px';
  el.style.top = top + 'px';

  parent.appendChild(el);
  makeDraggable(el);
}

function addTable() {
  const parent = document.getElementById('reportContent'); // agora adiciona no content
  const el = document.createElement('div');
  el.className = 'elemento';
  el.innerText = 'Tabela (fixa)';

  // posição inicial (clamp para dentro da área de conteúdo)
  const left = 20;
  const top = 50;
  el.style.left = left + 'px';
  el.style.top = top + 'px';

  parent.appendChild(el);
  makeDraggable(el);
}

function makeDraggable(el) {
  // garante posicionamento absoluto inicial e atributos
  el.style.position = 'absolute';
  el.style.touchAction = 'none';
  if (!el.hasAttribute('data-x')) el.setAttribute('data-x', '0');
  if (!el.hasAttribute('data-y')) el.setAttribute('data-y', '0');
  if (!el.style.transform) el.style.transform = 'translate(0px, 0px)';

  // limita ao conteúdo editável, não ao canvas inteiro
  const parent = document.getElementById('reportContent');
  if (!parent) {
    // fallback: comportamento padrão
    interact(el).draggable({
      listeners: {
        move (event) {
          const target = event.target;
          const x = (parseFloat(target.getAttribute('data-x')) || 0) + event.dx;
          const y = (parseFloat(target.getAttribute('data-y')) || 0) + event.dy;
          target.style.transform = `translate(${x}px, ${y}px)`;
          target.setAttribute('data-x', x);
          target.setAttribute('data-y', y);
        },
        end () {}
      }
    });
    return;
  }

  // comportamento principal: clamp dentro do #reportContent
  interact(el).draggable({
    modifiers: [
      interact.modifiers.restrictRect({
        restriction: parent,
        endOnly: false,
        elementRect: { top: 0, left: 0, bottom: 1, right: 1 }
      })
    ],
    listeners: {
      move (event) {
        const target = event.target;

        const baseLeft = Math.round(parseFloat(target.style.left) || 0);
        const baseTop = Math.round(parseFloat(target.style.top) || 0);

        const parentWidth = parent.clientWidth;
        const parentHeight = parent.clientHeight;

        const elWidth = target.offsetWidth;
        const elHeight = target.offsetHeight;

        // acumulado atual
        let curTx = (parseFloat(target.getAttribute('data-x')) || 0) + event.dx;
        let curTy = (parseFloat(target.getAttribute('data-y')) || 0) + event.dy;

        // posição absoluta proposta (relativa ao parent)
        let absLeft = baseLeft + curTx;
        let absTop = baseTop + curTy;

        // limites rígidos (não permite sair do content)
        const minLeft = 0;
        const maxLeft = Math.max(0, parentWidth - elWidth);
        const minTop = 0;
        const maxTop = Math.max(0, parentHeight - elHeight);

        absLeft = Math.round(Math.max(minLeft, Math.min(absLeft, maxLeft)));
        absTop = Math.round(Math.max(minTop, Math.min(absTop, maxTop)));

        // translate relativo ao base
        const tx = absLeft - baseLeft;
        const ty = absTop - baseTop;

        target.style.transform = `translate(${tx}px, ${ty}px)`;
        target.setAttribute('data-x', tx);
        target.setAttribute('data-y', ty);
      },

      end (event) {
        const target = event.target;
        const baseLeft = Math.round(parseFloat(target.style.left) || 0);
        const baseTop = Math.round(parseFloat(target.style.top) || 0);
        const dx = Math.round(parseFloat(target.getAttribute('data-x')) || 0);
        const dy = Math.round(parseFloat(target.getAttribute('data-y')) || 0);

        // consolida posição final em left/top
        const finalLeft = baseLeft + dx;
        const finalTop = baseTop + dy;

        target.style.left = finalLeft + 'px';
        target.style.top = finalTop + 'px';
        target.style.transform = 'translate(0px, 0px)';
        target.setAttribute('data-x', '0');
        target.setAttribute('data-y', '0');
      }
    }
  });

  el.addEventListener('dragstart', e => e.preventDefault());
}

// aplica makeDraggable em elementos já existentes ao carregar (apenas no content)
document.addEventListener('DOMContentLoaded', () => {
  const parent = document.getElementById('reportContent');
  if (!parent) return;

  // NÃO criar headerTitle nem headerLogo — o header já está no template com as imagens/título.

  // Garante texto do rodapé se faltar
  const footer = document.getElementById('reportFooter');
  if (footer && !document.getElementById('footerText')) {
    const f = document.createElement('div');
    f.className = 'footer-element';
    f.id = 'footerText';
    f.innerText = '© ' + new Date().getFullYear() + ' - IF Baiano - Campus Guanambi | SAMU 192';
    footer.insertBefore(f, footer.firstChild);
  }

  // aplica makeDraggable em elementos já existentes no content
  Array.from(parent.querySelectorAll('.elemento')).forEach(el => {
    el.style.position = 'absolute';
    const pw = parent.clientWidth;
    const ph = parent.clientHeight;
    const ew = el.offsetWidth;
    const eh = el.offsetHeight;
    let left = Math.round(parseFloat(el.style.left) || 0);
    let top = Math.round(parseFloat(el.style.top) || 0);
    left = Math.max(0, Math.min(left, Math.max(0, pw - ew)));
    top = Math.max(0, Math.min(top, Math.max(0, ph - eh)));
    el.style.left = left + 'px';
    el.style.top = top + 'px';
    makeDraggable(el);
  });
});

const navPreview = document.querySelector("#nav-preview");

async function gerarPDF() {
  const canvasRect = document.getElementById('reportCanvas').getBoundingClientRect();
  const contentRect = document.getElementById('reportContent').getBoundingClientRect();

  // envia posições relativas ao topo/esquerda da FOLHA (reportCanvas)
  const items = Array.from(document.querySelectorAll('#reportContent .elemento')).map(el => {
    const rect = el.getBoundingClientRect();
    return {
      type: el.innerText.includes('Tabela') ? 'table' : 'text',
      x: Math.round(rect.left - canvasRect.left),   // <<--- mudou para canvasRect
      y: Math.round(rect.top - canvasRect.top),     // <<--- mudou para canvasRect
      content: el.innerText
    };
  });

  const csrftoken = getCookie('csrftoken'); // garante que getCookie() exista

  const resp = await fetch('/gerar_pdf/', {
    method: 'POST',
    credentials: 'same-origin',        // garante envio de cookies
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrftoken         // header exigido pelo Django CSRF
    },
    body: JSON.stringify({
      elements: items,
      page: { width: Math.round(canvasRect.width), height: Math.round(canvasRect.height) }
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
    
    navPreview.innerHTML = "";
    navPreview.appendChild(preview);

  } else {
    const text = await resp.text();
    alert('Resposta inesperada: ' + text.slice(0, 500));
  }
}
