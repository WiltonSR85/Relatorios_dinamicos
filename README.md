# Relatórios Dinâmicos — README

Este projeto é um editor de relatórios com uma área A4 (template), onde é possível adicionar e mover elementos (texto/tabelas) no conteúdo e gerar PDF mantendo o CSS via WeasyPrint.

---

## Tecnologias e ferramentas usadas

- Python 3.11+ (ou 3.13 conforme ambiente local)
- Django (projeto e app `relatorio_dinamico`)
- WeasyPrint (biblioteca Python para gerar PDF a partir de HTML/CSS)
- MSYS2 (no Windows) para instalar dependências nativas do WeasyPrint (cairo, pango, glib, gdk-pixbuf, etc.)
- Alternativa: WSL/Ubuntu (pacotes via apt)
- Interact.js (arraste/solte) — carregado via CDN no template (`editor.html`)
- Nenhum bundler JS ou package.json obrigatório (assets estáticos em `static/`)

Arquivos principais no projeto:

- `templates/editor.html` — template do editor (carrega `editor.css` e `editor.js` via `{% static %}`).
- `static/editor.css` — estilos do editor (header, content, footer, A4 etc.).
- `static/editor.js` — lógica do editor (adicionar elementos, arrastar, gerar JSON e enviar para `/gerar_pdf/`).
- `relatorio_dinamico/views.py` — view que gera o PDF (usa WeasyPrint).
- `relatorio_dinamico/urls.py` — rota para `gerar_pdf/`.
- `setup/urls.py` — inclui as rotas do app (verifique se contém `path('', include('relatorio_dinamico.urls'))`).

---

## 1) Preparar ambiente Python (venv) e dependências Python

No diretório do projeto (ex.: `c:\Users\usercomum\Documents\relatorios`):

PowerShell (Windows):

```powershell
# criar virtualenv (se ainda não existir)
python -m venv venv
# ativar
venv\Scripts\Activate.ps1
# atualizar pip
python -m pip install --upgrade pip
# instalar dependências mínimas (exemplo)
python -m pip install Django WeasyPrint pycairo
```
Terminal (Linux):

```bash
# criar virtualenv (se ainda não existir)
python3 -m venv venv

# ativar o ambiente virtual
source venv/bin/activate

# atualizar o pip
python3 -m pip install --upgrade pip

# instalar dependências do sistema para o WeasyPrint (renderização CSS/HTML → PDF)
sudo apt install -y python3-dev libpango-1.0-0 libcairo2 libpangoft2-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info

# instalar pacotes Python necessários
pip install Django WeasyPrint pycairo
```


Observação: `WeasyPrint` foi instalado com `pip`, mas depende de bibliotecas nativas (passos abaixo). Também garantimos `pycairo` no venv.

Se você tiver um `requirements.txt` próprio, use `python -m pip install -r requirements.txt`.

---

## 2) Dependências nativas do WeasyPrint (Windows — recomendação: MSYS2)

WeasyPrint requer bibliotecas nativas (C libs) — cairo, pango, glib, gdk-pixbuf, fontconfig etc. No Windows a forma mais confiável é usar MSYS2 para instalar esses pacotes e adicionar o caminho `mingw64\bin` ao PATH.

Resumo (passos):

1) Instale MSYS2: https://www.msys2.org/ (baixe e instale).
2) Abra a shell "MSYS2 MinGW 64-bit" (procure por "MSYS2 MinGW 64-bit" no menu Iniciar — NÃO use UCRT64 ou MSYS shell).
3) Atualize o sistema e pacotes:

```bash
pacman -Syu
# se pedir, feche e reabra a shell MinGW64 e depois rode:
pacman -Su
```

4) Instale os pacotes necessários (execute na shell MinGW64):

```bash
pacman -S --noconfirm mingw-w64-x86_64-gtk3 mingw-w64-x86_64-cairo mingw-w64-x86_64-pango mingw-w64-x86_64-gdk-pixbuf2 mingw-w64-x86_64-freetype mingw-w64-x86_64-fontconfig mingw-w64-x86_64-glib2 mingw-w64-x86_64-libxml2 mingw-w64-x86_64-libpng mingw-w64-x86_64-libjpeg-turbo
```

Observações:
- Se algum pacote não for encontrado, certifique-se de usar a shell *MinGW 64-bit* (prompt geralmente `MINGW64 ~`).
- Em algumas versões o nome do pacote pode variar; use `pacman -Ss nome` para procurar.

5) Adicione ao PATH do Windows o diretório `C:\msys64\mingw64\bin` (temporário para sessão atual ou permanente):

PowerShell (temporário):

```powershell
$env:Path = "C:\msys64\mingw64\bin;" + $env:Path
```

Ou para permanente (setx) — feche/abra terminal/IDE após usar setx:

```powershell
setx PATH "C:\msys64\mingw64\bin;%PATH%"
```

6) Garanta `pycairo` no venv (já mencionado):

```powershell
python -m pip install pycairo
```

7) Teste rápido (no venv, no PowerShell):

```powershell
python -c "import weasyprint; print(weasyprint.__version__)"
```

Se retornar a versão do WeasyPrint, o runtime nativo está ok.

---

## 2b) Alternativa: WSL / Ubuntu (muito mais simples)

Se você usa WSL (Windows Subsystem for Linux) com uma distro como Ubuntu, instale as libs via apt:

```bash
sudo apt update
sudo apt install libcairo2 libpango-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info libxml2 libfontconfig1 libjpeg-dev libpng-dev
```

Em seguida ative seu ambiente Python no WSL e `pip install WeasyPrint pycairo`.

---

## 3) Servir arquivos estáticos (editor.css / editor.js)

Em desenvolvimento (DEBUG=True), o Django serve estáticos automaticamente quando o template usa `{% load static %}` e você está usando `runserver`.

Passos para garantir que os arquivos estáticos carreguem:

```powershell
# venv ativo
python manage.py runserver
# abra no navegador e verifique no DevTools -> Network se /static/editor.css e /static/editor.js retornam 200
```

Em produção (DEBUG=False) configure `STATIC_ROOT` e rode `collectstatic`, ou use WhiteNoise para servir arquivos estáticos diretamente:

```powershell
python manage.py collectstatic
```

Se editar `templates/editor.html`, verifique que `{% load static %}` esteja na primeira linha e que os caminhos usados sejam `{% static 'editor.css' %}` / `{% static 'editor.js' %}`.

---

## 4) Como rodar o projeto e testar o editor

1) Ative o venv:

Windows:
```powershell
venv\Scripts\Activate.ps1
```

Linux:
```bash
# ativar o ambiente virtual
source venv/bin/activate
```

2) Instale dependências Python (se ainda não instalou):

```powershell
python -m pip install -r requirements.txt
# ou, manualmente:
python -m pip install Django WeasyPrint pycairo
```

3) Rode o servidor Django:

```powershell
python manage.py runserver
```

4) Abra o editor no navegador. Dependendo da rota configurada, geralmente:

- http://127.0.0.1:8000/  (se o `relatorio_dinamico.urls` estiver ligado à raiz do projeto)

No editor:
- Use os botões para adicionar texto/tabela;
- Arraste os elementos — agora o arrasto é limitado à área `#reportContent` (folha A4);
- Clique em "💾 Gerar PDF" para enviar os elementos ao endpoint `/gerar_pdf/` e baixar o PDF.

---

## 5) Como a geração de PDF funciona (visão rápida)

- O `static/editor.js` coleta a posição (x,y) dos `.elemento` dentro da área do `#reportContent` e envia JSON para `/gerar_pdf/`.
- A view `relatorio_dinamico.views.gerar_pdf` monta um HTML com header/content/footer e inclui o CSS estático (`editor.css`) usando uma URL absoluta (via `request.build_absolute_uri(static('editor.css'))`) e chama WeasyPrint para renderizar o PDF.
- Para manter o CSS e evitar margens extras, a view injeta regras `@page { margin: 0 }` e zera margin/padding do `body` no HTML que é passado ao WeasyPrint.

---

## 6) Comandos úteis (PowerShell)

```powershell
# ativar venv
venv\Scripts\Activate.ps1

# atualizar pip
python -m pip install --upgrade pip

# instalar dependências
python -m pip install Django WeasyPrint pycairo

# executar servidor de desenvolvimento
python manage.py runserver

# testar import weasyprint (deve imprimir versão)
python -c "import weasyprint; print(weasyprint.__version__)"

# temporariamente adicionar mingw64 ao PATH (se usou MSYS2)
$env:Path = "C:\msys64\mingw64\bin;" + $env:Path
```

