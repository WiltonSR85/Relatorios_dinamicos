# Relatórios dinâmicos

Este projeto é um editor de relatórios que permite adicionar e mover elementos (texto/tabelas) no conteúdo e gerar PDF  via WeasyPrint.

Além do código da aplicação, este repositório possui alguns apps e models de exemplo para permitir demonstrar a funcionalidade do editor. Esta aplicação pode ser usada em qualquer projeto Django, sendo necessário apenas adaptar o código do arquivo `setup/esquema.py` para refletir o esquema do banco de dados.

Observação: Por causa de algumas discrepâncias entre as posições dos elementos no editor e a renderização do PDF, a manipulação dos elementos na área principal do relatório é um pouco limitada.

---

## Tecnologias e ferramentas usadas

- Python 3.10+
- Django 
- WeasyPrint (biblioteca Python para gerar PDF a partir de HTML/CSS)
- Docker & Docker Compose (para execução containerizada)
- Bootstrap 4.6
- [Interact.js](https://github.com/taye/interact.js) (para arrastar e soltar elementos dentro da área do relátorio)
- [SortableJS](https://github.com/SortableJS/Sortable) (também fornece funcionalidades de arrastar e soltar; foi usado para permitir reordenar a ordem dos cabeçalhos das tabelas no formulário)
- BeautifulSoup (manipulação de HTML no backend)
- [nh3](https://github.com/messense/nh3) (para sanitização de HTML no backend)

---

## Execução com Docker Compose

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

A aplicação estará disponível em: **http://localhost:8001**

---

## Como usar o editor

1. Abra a aplicação em **http://localhost:8001**
2. Use os botões para adicionar texto/tabela na área A4
3. Arraste os elementos para posicionar
4. Clique em "Visualizar relatório"

---

## Imagens
<img width="1366" height="768" alt="image" src="https://github.com/user-attachments/assets/d53d89c1-528a-4dbd-9e3b-a45da3480886" />
<img width="1366" height="768" alt="image" src="https://github.com/user-attachments/assets/0d293912-24f2-4af8-859b-5fe04b2747fa" />
<img width="1366" height="768" alt="image" src="https://github.com/user-attachments/assets/1ce9c655-8440-4ff7-9fd6-dd5615b6d576" />


