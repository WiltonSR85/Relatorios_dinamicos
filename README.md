# Relatórios Dinâmicos — README

Este projeto é um editor de relatórios com uma área A4 (template), onde é possível adicionar e mover elementos (texto/tabelas) no conteúdo e gerar PDF mantendo o CSS via WeasyPrint.

---

## Tecnologias e ferramentas usadas

- Python 3.10+
- Django (projeto e app `relatorio_dinamico`)
- WeasyPrint (biblioteca Python para gerar PDF a partir de HTML/CSS)
- Docker & Docker Compose (para execução containerizada)
- Interact.js (arraste/solte) — carregado via CDN no template (`editor.html`)
- Nenhum bundler JS ou package.json obrigatório (assets estáticos em `static/`)

---

## Arquivos principais no projeto

- `templates/editor.html` — template do editor (carrega `editor.css` e `editor.js` via `{% static %}`).
- `static/editor.css` — estilos do editor (header, content, footer, A4 etc.).
- `static/editor.js` — lógica do editor (adicionar elementos, arrastar, gerar JSON e enviar para `/gerar_pdf/`).
- `relatorio_dinamico/views.py` — view que gera o PDF (usa WeasyPrint).
- `relatorio_dinamico/urls.py` — rota para `gerar_pdf/`.
- `setup/urls.py` — inclui as rotas do app.
- `Dockerfile` — configuração da imagem Docker.
- `docker-compose.yml` — orquestração dos serviços Docker.
- `requirements.txt` — dependências Python.

---

## 🚀 Execução com Docker Compose

### Pré-requisitos
- Docker instalado
- Docker Compose instalado

### Iniciar a aplicação

```bash
# Clone o repositório
git clone git@github.com:WiltonSR85/Relatorios_dinamicos.git
cd Relatorios_dinamicos

# Inicie os containers
# a opção --build só é necessária na primeira vez que você o executar ou se mudar algo no Dockerfile
docker compose up --build
```

A aplicação estará disponível em: **http://localhost:8000**

---

## Como usar o editor

1. Abra a aplicação em **http://localhost:8000**
2. Use os botões para adicionar texto/tabela na área A4
3. Arraste os elementos para posicionar
4. Clique em "💾 Gerar PDF" para fazer download do PDF com o layout mantido

---

## Como a geração de PDF funciona (visão rápida)

- O `static/editor.js` coleta a posição (x,y) dos `.elemento` dentro da área do `#reportContent` e envia JSON para `/gerar_pdf/`.
- A view `relatorio_dinamico.views.gerar_pdf` monta um HTML com header/content/footer e inclui o CSS estático (`editor.css`) usando uma URL absoluta (via `request.build_absolute_uri(static('editor.css'))`) e chama WeasyPrint para renderizar o PDF.
- Para manter o CSS e evitar margens extras, a view injeta regras `@page { margin: 0 }` e zera margin/padding do `body` no HTML que é passado ao WeasyPrint.

---