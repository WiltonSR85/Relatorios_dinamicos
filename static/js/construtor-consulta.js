import { getElementoSelecionado, atualizarPainelPropriedades } from './canvas.js';

// Variáveis globais do estado da consulta
let ESQUEMA_DB = {};

const estadoGlobal = {
    modeloRaiz: "",
    tabelasAtivas: [],
    colunasEscolhidas: [], 
    filtrosAtivos: []
};

export async function iniciarAplicacao() {
    try {
        const resposta = await fetch('/esquema');
        if (!resposta.ok) throw new Error('Falha na rede');

        ESQUEMA_DB = await resposta.json();

        const selectRaiz = document.getElementById('select-raiz');
        selectRaiz.innerHTML = '<option value="" selected disabled>Selecione...</option>';

        Object.keys(ESQUEMA_DB).forEach(key => {
            const dadosModelo = ESQUEMA_DB[key];
            const opcao = document.createElement('option');
            opcao.value = key;
            opcao.text = dadosModelo.label_tabela || key;
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
        <option value="${k}">${ESQUEMA_DB[k].label_tabela}</option>`
    );

    // Tenta carregar config existente
    const cfg = JSON.parse(elementoSelecionado.dataset.configConsulta || "{}");
    redefinirConstrutorConsulta();

    if (cfg.fonte_principal) {
        // Restaurar estado
        sel.value = cfg.fonte_principal;
        iniciarRaiz(cfg.fonte_principal);
        // TODO: Implementar re-hidratação completa (joins, colunas, filtros)
    }

    $('#modalConstrutorConsulta').modal('show');
}

export function salvarConfiguracaoTabela() {
    const elementoSelecionado = getElementoSelecionado();

    if (!elementoSelecionado) 
        return;
    const textoJson = document.getElementById('saida-json').innerText;
    elementoSelecionado.dataset.configConsulta = textoJson;

    const payload = JSON.parse(textoJson);
    if (payload.fonte_principal) {
        elementoSelecionado.querySelector('.el-tabela-corpo').innerHTML = `
            <div class="text-success font-weight-bold">Consulta configurada</div>
            <div class="small">${payload.colunas.length} colunas</div>
            <div class="small text-muted">Raiz: ${payload.fonte_principal}</div>
        `;
    }
    atualizarPainelPropriedades();
    $('#modalConstrutorConsulta').modal('hide');
}

export function redefinirConstrutorConsulta() {
    estadoGlobal.modeloRaiz = "";
    estadoGlobal.tabelasAtivas = [];
    estadoGlobal.colunasEscolhidas = [];
    estadoGlobal.filtrosAtivos = [];
    document.getElementById('select-raiz').value = "";
    renderizarTudo();
}

export function iniciarRaiz(nomeModelo) {
    estadoGlobal.modeloRaiz = nomeModelo;
    estadoGlobal.tabelasAtivas = [];
    estadoGlobal.colunasEscolhidas = [];
    estadoGlobal.filtrosAtivos = [];

    const label = ESQUEMA_DB[nomeModelo]?.label_tabela || "Tabela Principal";
    carregarTabela(nomeModelo, label, "", "Raiz");
    renderizarTudo();
}

export function carregarTabela(nomeModelo, nomeAmigavel, caminhoPrefixo, tipo) {
    const esquema = ESQUEMA_DB[nomeModelo];
    if (!esquema) return;

    estadoGlobal.tabelasAtivas.push({
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
    const tabelaPai = estadoGlobal.tabelasAtivas.find(t => t.id === tabelaPaiId);
    if (!tabelaPai) return;

    const conn = tabelaPai.conexoes_disponiveis[conexaoIdx];
    const prefixo = tabelaPai.caminho + conn.campo_relacao + "__";

    carregarTabela(conn.model_destino, conn.nome_amigavel, prefixo, "Join");
    renderizarTudo();
}

export function adicionarColuna() {
    const tableIdx = document.getElementById('select-col-tabela').value;
    const fieldVal = document.getElementById('select-col-campo').value;
    const agg = document.getElementById('select-col-agregacao').value;

    if (tableIdx === "" || fieldVal === "") return;

    const tab = estadoGlobal.tabelasAtivas[tableIdx];
    const campoObj = tab.campos.find(c => c.valor === fieldVal);
    const caminho = tab.caminho + fieldVal;
    const labelDisplay = agg ? `${agg} de ${campoObj.label}` : campoObj.label;

    estadoGlobal.colunasEscolhidas.push({
        tabela_origem: tab.nome_amigavel,
        label: campoObj.label,
        label_display: labelDisplay,
        path_final: caminho,
        agregacao: agg || null
    });

    renderizarColunasSelecionadas();
    renderizarJson();

    document.getElementById('select-col-campo').value = "";
    document.getElementById('select-col-agregacao').value = "";
    document.getElementById('btn-add-coluna').disabled = true;
}

export function removerColuna(index) {
    estadoGlobal.colunasEscolhidas.splice(index, 1);
    renderizarColunasSelecionadas();
    renderizarJson();
}

export function adicionarFiltro() {
    const tableIdx = document.getElementById('select-filtro-tabela').value;
    const fieldVal = document.getElementById('select-filtro-campo').value;
    const operador = document.getElementById('select-filtro-operador').value;
    const valor = document.getElementById('input-filtro-valor').value;

    if (tableIdx === "" || fieldVal === "") return;

    const tab = estadoGlobal.tabelasAtivas[tableIdx];
    estadoGlobal.filtrosAtivos.push({
        campo: tab.caminho + fieldVal,
        operador: operador,
        valor: valor
    });

    renderizarFiltros();
    renderizarJson();
    document.getElementById('input-filtro-valor').value = "";
}

export function removerFiltro(index) {
    estadoGlobal.filtrosAtivos.splice(index, 1);
    renderizarFiltros();
    renderizarJson();
}

export function isTabelaJaAdicionada(caminhoPai, campoRel) {
    const check = caminhoPai + campoRel + "__";
    return estadoGlobal.tabelasAtivas.some(t => t.caminho === check);
}

export function atualizarSelectCampos(tabelaIdx, idSelectAlvo, idBtn) {
    const selectAlvo = document.getElementById(idSelectAlvo);
    const btn = document.getElementById(idBtn);
    selectAlvo.innerHTML = '<option value="" disabled selected>Selecione...</option>';

    if (tabelaIdx === null || !estadoGlobal.tabelasAtivas[tabelaIdx]) {
        selectAlvo.disabled = true;
        if (btn) btn.disabled = true;
        return;
    }

    const tab = estadoGlobal.tabelasAtivas[tabelaIdx];
    tab.campos.forEach(campo => {
        const opt = document.createElement('option');
        opt.value = campo.valor;
        opt.text = campo.label;
        selectAlvo.appendChild(opt);
    });
    selectAlvo.disabled = false;
}

export function renderizarTudo() {
    renderizarEstruturaTabelas();

    const hasTables = estadoGlobal.tabelasAtivas.length > 0;
    const wrapperSecoes = document.getElementById('wrapper-secoes');
    const containerTabelas = document.getElementById('container-tabelas');

    if (hasTables) {
        wrapperSecoes.classList.remove('oculto-custom');
        containerTabelas.classList.remove('oculto-custom');
    } else {
        wrapperSecoes.classList.add('oculto-custom');
        containerTabelas.classList.add('oculto-custom');
    }

    atualizarOpcoesSelect('select-col-tabela');
    atualizarOpcoesSelect('select-filtro-tabela');

    document.getElementById('select-col-campo').innerHTML = '<option value="" disabled selected>Selecione...</option>';
    document.getElementById('select-col-campo').disabled = true;
    document.getElementById('select-filtro-campo').innerHTML = '<option value="" disabled selected>Campo...</option>';
    document.getElementById('select-filtro-campo').disabled = true;

    renderizarColunasSelecionadas();
    renderizarFiltros();
    renderizarJson();
}

export function renderizarEstruturaTabelas() {
    const container = document.getElementById('lista-tabelas');
    container.innerHTML = '';

    estadoGlobal.tabelasAtivas.forEach(tab => {
        const div = document.createElement('div');
        div.className = "mb-2 p-2 bg-white border rounded shadow-sm d-flex flex-wrap align-items-center justify-content-between";

        let btnsHtml = '';
        if (tab.conexoes_disponiveis.length > 0) {
            btnsHtml = `<div class="d-flex align-items-center mt-2 mt-md-0"><small class="text-muted mr-2">Conectar:</small>`;
            tab.conexoes_disponiveis.forEach((conn, idx) => {
                const disabled = isTabelaJaAdicionada(tab.caminho, conn.campo_relacao) ? 'disabled' : '';
                const btnClass = disabled ? 'btn-outline-secondary' : 'btn-outline-dark';
                btnsHtml += `<button class="btn ${btnClass} btn-sm mr-1 btn-add-join" ${disabled} data-tab-id="${tab.id}" data-conn-idx="${idx}">+ ${conn.nome_amigavel}</button>`;
            });
            btnsHtml += `</div>`;
        }

        div.innerHTML = `<div><span class="badge badge-primary mr-2">${tab.tipo}</span><span class="font-weight-bold">${tab.nome_amigavel}</span>
                        ${tab.caminho ? `<small class="text-muted ml-2">(via <code>${tab.caminho.slice(0, -2)}</code>)</small>` : ''}</div>${btnsHtml}`;
        container.appendChild(div);
    });
}

export function atualizarOpcoesSelect(idSelect) {
    const select = document.getElementById(idSelect);
    select.innerHTML = '';
    estadoGlobal.tabelasAtivas.forEach((tab, index) => {
        const opt = document.createElement('option');
        opt.value = index;
        opt.text = tab.nome_amigavel;
        select.appendChild(opt);
    });
    if (estadoGlobal.tabelasAtivas.length > 0) {
        select.value = 0;
        select.dispatchEvent(new Event('change'));
    }
}

export function renderizarColunasSelecionadas() {
    const container = document.getElementById('lista-colunas-selecionadas');
    const msg = document.getElementById('msg-sem-colunas');
    container.innerHTML = '';

    if (estadoGlobal.colunasEscolhidas.length === 0) {
        msg.classList.remove('oculto-custom');
        container.classList.add('oculto-custom');
    } else {
        msg.classList.add('oculto-custom');
        container.classList.remove('oculto-custom');

        estadoGlobal.colunasEscolhidas.forEach((col, idx) => {
            const bgClass = col.agregacao ? 'badge-warning text-dark' : 'badge-primary text-white';
            const iconClass = col.agregacao ? 'bi-calculator' : 'bi-check';

            const div = document.createElement('div');
            div.className = "border rounded p-2 d-flex align-items-center bg-light shadow-sm mr-2 mb-2";

            div.innerHTML = `<div class="badge-circle mr-2 ${bgClass}"><i class="bi ${iconClass}"></i></div>
                            <div class="d-flex flex-column mr-3"><span class="font-weight-bold small">${col.label_display}</span><span class="text-muted" style="font-size:0.7rem;">${col.tabela_origem}</span></div>
                            <button class="btn btn-link text-danger p-0 btn-remover-col" data-idx="${idx}"><i class="bi bi-x-circle-fill"></i></button>`;
            container.appendChild(div);
        });
    }
}

export function renderizarFiltros() {
    const tbody = document.getElementById('tbody-filtros');
    const containerTabela = document.getElementById('container-tabela-filtros');
    const msg = document.getElementById('msg-sem-filtros');
    tbody.innerHTML = '';

    if (estadoGlobal.filtrosAtivos.length === 0) {
        containerTabela.classList.add('oculto-custom');
        msg.classList.remove('oculto-custom');
    } else {
        containerTabela.classList.remove('oculto-custom');
        msg.classList.add('oculto-custom');
        estadoGlobal.filtrosAtivos.forEach((filtro, idx) => {
            const tr = document.createElement('tr');
            tr.innerHTML = `<td class="text-primary"><code>${filtro.campo}</code></td><td>${filtro.operador}</td><td>${filtro.valor}</td><td class="text-right"><button class="btn btn-link text-danger p-0 btn-remover-filtro" data-idx="${idx}"><i class="bi bi-trash"></i></button></td>`;
            tbody.appendChild(tr);
        });
    }
}

export function renderizarJson() {
    const payload = {
        fonte_principal: estadoGlobal.modeloRaiz,
        colunas: estadoGlobal.colunasEscolhidas.map(c => ({ campo: c.path_final, label: c.label, agregacao: c.agregacao })),
        filtros: estadoGlobal.filtrosAtivos.map(f => ({ campo: f.campo, operador: f.operador, valor: f.valor })),
        agrupamentos: estadoGlobal.colunasEscolhidas.filter(c => !c.agregacao).map(c => c.path_final)
    };
    document.getElementById('saida-json').textContent = JSON.stringify(payload, null, 2);
}