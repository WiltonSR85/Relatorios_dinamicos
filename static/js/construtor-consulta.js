import { getElementoSelecionado, atualizarPainelPropriedades, tornarComponentesDaTabelasRedimensionaveis } from './canvas.js';

const URL_ESQUEMA_DB = '/esquema';

let ESQUEMA_DB = {};

// Variáveis globais do estado da consulta
const estadoGlobal = {
    modeloRaiz: "",
    tabelas: [],
    colunas: [], 
    filtros: [],
    ordenacoes: [],
    limite: null
};

export async function iniciarAplicacao() {
    try {
        const resposta = await fetch(URL_ESQUEMA_DB);
        if (!resposta.ok) {
            throw new Error('Falha na rede');
        }

        ESQUEMA_DB = await resposta.json();

        const selectRaiz = document.getElementById('select-raiz');
        selectRaiz.innerHTML = '<option value="" selected disabled>Selecione...</option>';

        Object.keys(ESQUEMA_DB).forEach(key => {
            const opcao = document.createElement('option');
            opcao.value = key;
            opcao.text = key;
            selectRaiz.appendChild(opcao);
        });

    } catch (erro) {
        console.error(erro);
    }
}

export function abrirConstrutorConsulta() {
    const elementoSelecionado = getElementoSelecionado();

    if (!elementoSelecionado) 
        return;

    // Carrega lista de tabelas raiz no select
    const sel = document.getElementById('select-raiz');
    sel.innerHTML = '<option value="" disabled selected>Selecione...</option>';
    Object.keys(ESQUEMA_DB).forEach(k => 
        sel.innerHTML += `
        <option value="${k}">${k}</option>`
    );

    // Tenta carregar config existente
    const cfg = JSON.parse(elementoSelecionado.dataset.configConsulta || "{}");
    redefinirConstrutorConsulta();

    if (cfg.fonte_principal) {
        // Restaurar estado
        sel.value = cfg.fonte_principal;
        iniciarRaiz(cfg.fonte_principal);
        // TODO: Implementar re-hidratação completa (junções, colunas, filtros)
    }

    $('#modalConstrutorConsulta').modal('show');
}

export function salvarConfiguracaoTabela() {
    const elementoSelecionado = getElementoSelecionado();

    if (!elementoSelecionado) 
        return;

    const cargaUtil = gerarCargaUtil();
    elementoSelecionado.dataset.configConsulta = JSON.stringify(cargaUtil, null, 4);

    const cabecalhosColunas = cargaUtil['colunas'].map(c => c.rotulo);
    inserirCabecalhosNaTabela(elementoSelecionado, cabecalhosColunas);
    
    atualizarPainelPropriedades();
    $('#modalConstrutorConsulta').modal('hide');
}

function inserirCabecalhosNaTabela(elementoSelecionado, cabeçalhos){
    const linhaDoCabeçalho = elementoSelecionado.querySelector('thead tr');
    const linhaDoCorpo = elementoSelecionado.querySelector('tbody tr');
    linhaDoCabeçalho.innerHTML = '';   
    linhaDoCorpo.innerHTML = '';
    
    if(cabeçalhos.length === 0){
        const th = document.createElement('th');
        th.innerText = 'Nenhuma coluna selecionada';
        linhaDoCabeçalho.appendChild(th);
    } else {
        cabeçalhos.forEach(c => {
            const th = document.createElement('th');
            th.innerText = c;
            linhaDoCabeçalho.appendChild(th);
    
            const td = document.createElement('td');
            td.innerText = '{}';
            linhaDoCorpo.appendChild(td);
        });
    }

    tornarComponentesDaTabelasRedimensionaveis(elementoSelecionado);
}

export function redefinirConstrutorConsulta() {
    estadoGlobal.modeloRaiz = "";
    estadoGlobal.tabelas = [];
    estadoGlobal.colunas = [];
    estadoGlobal.filtros = [];
    estadoGlobal.ordenacoes = [];
    
    let limite = document.getElementById('input-limite-valor').value;
    estadoGlobal.limite = Number(limite) || null;
    
    document.getElementById('select-raiz').value = "";
    renderizarTudo();
}

export function iniciarRaiz(nomeModelo) {
    estadoGlobal.modeloRaiz = nomeModelo;
    estadoGlobal.tabelas = [];
    estadoGlobal.colunas = [];
    estadoGlobal.filtros = [];
    estadoGlobal.ordenacoes = [];
    
    let limite = document.getElementById('input-limite-valor').value;
    estadoGlobal.limite = Number(limite) || null;

    const rotulo = nomeModelo;
    carregarTabela(nomeModelo, rotulo, "", "Raiz");
    renderizarTudo();
}

export function carregarTabela(nomeModelo, nomeAmigavel, caminhoPrefixo, tipo) {
    const esquema = ESQUEMA_DB[nomeModelo];
    if (!esquema) return;

    estadoGlobal.tabelas.push({
        id: Math.random().toString(36).substr(2, 9),
        model: nomeModelo,
        nome_amigavel: nomeAmigavel,
        caminho: caminhoPrefixo,
        campos: esquema.campos || [],
        conexoes_disponiveis: esquema.conexoes || [],
        tipo: tipo
    });
}

export function adicionarJuncao(tabelaPaiId, conexaoIdx) {
    const tabelaPai = estadoGlobal.tabelas.find(t => t.id === tabelaPaiId);
    if (!tabelaPai) return;

    const conn = tabelaPai.conexoes_disponiveis[conexaoIdx];
    const prefixo = tabelaPai.caminho + conn.campo_relacao + "__";

    carregarTabela(conn.model_destino, conn.nome_amigavel, prefixo, "Junção");
    renderizarTudo();
}

export function adicionarColuna() {
    const tableIdx = document.getElementById('select-col-tabela').value;
    const fieldVal = document.getElementById('select-col-campo').value;
    const agg = document.getElementById('select-col-agregacao').value;
    const rotulo = document.getElementById('input-col-rotulo').value;

    if (tableIdx === "" || fieldVal === "") 
        return;

    const tab = estadoGlobal.tabelas[tableIdx];
    const campoObj = tab.campos.find(c => c.valor === fieldVal);
    const caminho = tab.caminho + fieldVal;
    let rotuloExibicao;

    if(agg){
        if(rotulo){
            rotuloExibicao = rotulo;
        } else {
            rotuloExibicao = `${agg} de ${campoObj.rotulo}`;
        }
    } else if(rotulo){
        rotuloExibicao = rotulo;
    } else {
        rotuloExibicao = campoObj.rotulo;
    }

    estadoGlobal.colunas.push({
        tabela_origem: tab.nome_amigavel,
        caminho_final: caminho,
        rotulo: campoObj.rotulo,
        rotulo_exibicao: rotuloExibicao,
        agregacao: agg || null
    });

    renderizarColunasSelecionadas();
    renderizarJson();

    document.getElementById('select-col-campo').value = "";
    document.getElementById('select-col-agregacao').value = "";
    document.getElementById('input-col-rotulo').value = "";
    document.getElementById('btn-add-coluna').disabled = true;
}

export function removerColuna(index) {
    estadoGlobal.colunas.splice(index, 1);
    renderizarColunasSelecionadas();
    renderizarJson();
}

export function adicionarFiltro() {
    const tableIdx = document.getElementById('select-filtro-tabela').value;
    const fieldVal = document.getElementById('select-filtro-campo').value;
    const operador = document.getElementById('select-filtro-operador').value;
    const valor = document.getElementById('input-filtro-valor').value;

    if (tableIdx === "" || fieldVal === "") return;

    const tab = estadoGlobal.tabelas[tableIdx];
    estadoGlobal.filtros.push({
        campo: tab.caminho + fieldVal,
        operador: operador,
        valor: valor
    });

    renderizarFiltros();
    renderizarJson();
    document.getElementById('input-filtro-valor').value = "";
}

export function removerFiltro(index) {
    estadoGlobal.filtros.splice(index, 1);
    renderizarFiltros();
    renderizarJson();
}

export function adicionarOrdenacao() {
    const tableIdx = document.getElementById('select-ordenacao-tabela').value;
    const fieldVal = document.getElementById('select-ordenacao-campo').value;
    const ordem = document.getElementById('select-ordenacao-ordem').value;

    if (tableIdx === "" || fieldVal === "") return;

    const tab = estadoGlobal.tabelas[tableIdx];
    estadoGlobal.ordenacoes.push({
        campo: tab.caminho + fieldVal,
        ordem: ordem
    });

    renderizarOrdenacoes();
    renderizarJson();
}

export function removerOrdenacao(index) {
    estadoGlobal.ordenacoes.splice(index, 1);
    renderizarOrdenacoes();
    renderizarJson();
}

export function adicionarLimite(valor) {
    estadoGlobal.limite = Number(valor) || null;
    renderizarJson();
}

export function isTabelaJaAdicionada(caminhoPai, campoRel) {
    const check = caminhoPai + campoRel + "__";
    return estadoGlobal.tabelas.some(t => t.caminho === check);
}

export function atualizarSelectCampos(tabelaIdx, idSelectAlvo, idBtn) {
    const selectAlvo = document.getElementById(idSelectAlvo);
    const btn = document.getElementById(idBtn);
    selectAlvo.innerHTML = '<option value="" disabled selected>Selecione...</option>';

    if (tabelaIdx === null || !estadoGlobal.tabelas[tabelaIdx]) {
        selectAlvo.disabled = true;
        if (btn) 
            btn.disabled = true;
        return;
    }

    const tab = estadoGlobal.tabelas[tabelaIdx];
    tab.campos.forEach(campo => {
        const opt = document.createElement('option');
        opt.value = campo.valor;
        opt.text = campo.rotulo;
        opt.dataset.tipo = campo.tipo;
        selectAlvo.appendChild(opt);
    });
    selectAlvo.disabled = false;
}

export function renderizarTudo() {
    renderizarEstruturaTabelas();

    const temTabelas = estadoGlobal.tabelas.length > 0;
    const containerSecoes = document.getElementById('wrapper-secoes');
    const containerTabelas = document.getElementById('container-tabelas');

    if (temTabelas) {
        containerSecoes.classList.remove('d-none');
        containerTabelas.classList.remove('d-none');
    } else {
        containerSecoes.classList.add('d-none');
        containerTabelas.classList.add('d-none');
    }

    atualizarOpcoesSelect('select-col-tabela');
    atualizarOpcoesSelect('select-filtro-tabela');
    atualizarOpcoesSelect('select-ordenacao-tabela');

    renderizarColunasSelecionadas();
    renderizarFiltros();
    renderizarJson();
}

export function renderizarEstruturaTabelas() {
    const container = document.getElementById('lista-tabelas');
    container.innerHTML = '';

    estadoGlobal.tabelas.forEach(tab => {
        const div = document.createElement('div');
        div.className = "mb-2 p-2 bg-white border rounded shadow-sm d-flex flex-wrap align-items-center justify-content-between";

        let btnsHtml = '';
        if (tab.conexoes_disponiveis.length > 0) {
            btnsHtml = `
                <div class="d-flex align-items-center flex-wrap mt-2 mt-md-0" style="gap: 0.5rem;">
                    <small class="text-muted mr-2">Conectar:</small>
            `;
            tab.conexoes_disponiveis.forEach((conn, idx) => {
                const disabled = isTabelaJaAdicionada(tab.caminho, conn.campo_relacao) ? 'disabled' : '';
                const btnClass = disabled ? 'btn-outline-secondary' : 'btn-outline-dark';
                btnsHtml += `<button class="btn ${btnClass} btn-sm mr-1 btn-add-join" ${disabled} data-tab-id="${tab.id}" data-conn-idx="${idx}">+ ${conn.nome_amigavel}</button>`;
            });
            btnsHtml += `</div>`;
        }

        div.innerHTML = `
            <div>
                <span class="badge badge-primary mr-2">${tab.tipo}</span>
                <span class="font-weight-bold">${tab.nome_amigavel}</span>
                    ${tab.caminho ? `<small class="text-muted ml-2">(via <code>${tab.caminho.slice(0, -2)}</code>)</small>` : ''}
                </div>${btnsHtml}`;
        container.appendChild(div);
    });
}

export function atualizarOpcoesSelect(idSelect) {
    const select = document.getElementById(idSelect);
    select.innerHTML = '';
    estadoGlobal.tabelas.forEach((tab, index) => {
        const opt = document.createElement('option');
        opt.value = index;
        opt.text = tab.nome_amigavel;
        select.appendChild(opt);
    });
    if (estadoGlobal.tabelas.length > 0) {
        select.value = 0;
        select.dispatchEvent(new Event('change'));
    }
}

export function renderizarColunasSelecionadas() {
    const container = document.getElementById('lista-colunas-selecionadas');
    const msg = document.getElementById('msg-sem-colunas');
    container.innerHTML = '';

    if (estadoGlobal.colunas.length === 0) {
        msg.classList.remove('d-none');
        container.classList.add('d-none');
    } else {
        msg.classList.add('d-none');
        container.classList.remove('d-none');

        estadoGlobal.colunas.forEach((col, idx) => {
            const bgClass = col.agregacao ? 'badge-warning text-dark' : 'badge-primary text-white';
            const iconClass = col.agregacao ? 'bi-calculator' : 'bi-check';

            const div = document.createElement('div');
            div.className = "border rounded p-2 d-flex align-items-center bg-light shadow-sm mr-2 mb-2";

            div.innerHTML = `
                <div class="badge-circle mr-2 ${bgClass}">
                    <i class="bi ${iconClass}"></i>
                </div>
                <div class="d-flex flex-column mr-3">
                    <span class="font-weight-bold small">${col.rotulo_exibicao}</span>
                    <span class="text-muted" style="font-size:0.7rem;">${col.tabela_origem}</span>
                </div>
                <button class="btn btn-link text-danger p-0 btn-remover-col" data-idx="${idx}">
                    <i class="bi bi-x-circle-fill"></i>
                </button>`;
            container.appendChild(div);
        });
    }
}

export function renderizarFiltros() {
    const tbody = document.getElementById('tbody-filtros');
    const containerTabela = document.getElementById('container-tabela-filtros');
    const msg = document.getElementById('msg-sem-filtros');
    tbody.innerHTML = '';

    if (estadoGlobal.filtros.length === 0) {
        containerTabela.classList.add('d-none');
        msg.classList.remove('d-none');
    } else {
        containerTabela.classList.remove('d-none');
        msg.classList.add('d-none');
        estadoGlobal.filtros.forEach((filtro, idx) => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td class="text-primary">
                    <code>${filtro.campo}</code>
                </td>
                <td>${filtro.operador}</td>
                <td>${filtro.valor}</td>
                <td class="text-right">
                    <button class="btn btn-link text-danger p-0 btn-remover-filtro" data-idx="${idx}">
                        <i class="bi bi-trash"></i>
                    </button>
                </td>`;
            tbody.appendChild(tr);
        });
    }
}

export function renderizarOrdenacoes(){
    const tbody = document.getElementById('tbody-ordenacao');
    const containerTabela = document.getElementById('container-tabela-ordenacao');
    const msg = document.getElementById('msg-sem-ordenacao');
    tbody.innerHTML = '';

    if (estadoGlobal.ordenacoes.length === 0) {
        containerTabela.classList.add('d-none');
        msg.classList.remove('d-none');
    } else {
        containerTabela.classList.remove('d-none');
        msg.classList.add('d-none');
        estadoGlobal.ordenacoes.forEach((ordenacao, idx) => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td class="text-primary">
                    <code>${ordenacao.campo}</code>
                </td>
                <td>${ordenacao.ordem == 'ASC' ? 'Crescente': 'Decrescente'}</td>
                <td class="text-right">
                    <button class="btn btn-link text-danger p-0 btn-remover-ordenacao" data-idx="${idx}">
                        <i class="bi bi-trash"></i>
                    </button>
                </td>`;
            tbody.appendChild(tr);
        });
    }
}

export function gerarCargaUtil()
{
    return {
        fonte_principal: estadoGlobal.modeloRaiz,
        colunas: estadoGlobal.colunas.map(c => {
            return { 
                campo: c.caminho_final, 
                rotulo: c.rotulo_exibicao, 
                agregacao: c.agregacao 
            };
        }),
        filtros: estadoGlobal.filtros,
        ordenacoes: estadoGlobal.ordenacoes,
        limite: estadoGlobal.limite
    };
}

export function renderizarJson() {
    const cargaUtil = gerarCargaUtil();
    document.getElementById('saida-json').textContent = JSON.stringify(cargaUtil, null, 4);
}