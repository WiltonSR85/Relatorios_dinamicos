# Relatórios Dinâmicos — README

Este projeto é um editor de relatórios com uma área A4 (template), onde é possível adicionar e mover elementos (texto/tabelas) no conteúdo e gerar PDF  via WeasyPrint.

---

## Tecnologias e ferramentas usadas

- Python 3.10+
- Django (projeto e app `relatorio_dinamico`)
- WeasyPrint (biblioteca Python para gerar PDF a partir de HTML/CSS)
- Docker & Docker Compose (para execução containerizada)
- Interact.js (arraste/solte) — carregado via CDN no template (`editor.html`)

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
4. Clique em "Visualizar relatório"

---