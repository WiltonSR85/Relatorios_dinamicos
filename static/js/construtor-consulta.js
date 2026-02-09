import { getElementoSelecionado, atualizarPainelPropriedades, tornarComponentesDaTabelaRedimensionaveis } from './canvas.js';

/** Várias das funções seguintes possuem comportamentos comuns.
 * Algumas delas adicionam ou removem elementos do estadoGlobal e
 * depois chamam funções de renderização específicas para atualizar
 * as partes da interface do usuário relacionadas a esses elementos.
 * Outras funções atualizam os elementos de seleção (select) com base
 * nas tabelas atualmente presentes no estadoGlobal.
 * Essas funções trabalham juntas para garantir que a interface do usuário
 * esteja sempre sincronizada com o estado atual da consulta sendo construída.
 * Assim, sempre que uma alteração é feita no estadoGlobal, como, por exemplo,
 * adição ou remoção de tabelas, colunas, filtros ou ordenações, as funções 
 * de renderização e atualização de seleção são chamadas para refletir 
 * essas mudanças na interface do usuário.
 */

const URL_ESQUEMA_DB = '/esquema';

let ESQUEMA_DB = {};

// variável global que representa a consulta
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
        const sel = document.getElementById('select-raiz');
        sel.innerHTML = '<option value="" selected disabled>Selecione...</option>';
        Object.keys(ESQUEMA_DB).forEach(key => {
            const opcao = document.createElement('option');
            opcao.value = key;
            opcao.text = key;
            sel.appendChild(opcao);
        });

    } catch (erro) {
        console.error(erro);
    }
}

export function abrirConstrutorConsulta() {
    const elementoSelecionado = getElementoSelecionado();

    if (!elementoSelecionado) 
        return;

    const sel = document.getElementById('select-raiz');
    const cfg = JSON.parse(elementoSelecionado.dataset.configConsulta || "{}");
    
    if (cfg.fonte_principal) {
        sel.value = cfg.fonte_principal;
        estadoGlobal.modeloRaiz = cfg.fonte_principal;
        estadoGlobal.tabelas = cfg.tabelas;
        estadoGlobal.colunas = cfg.colunas;
        estadoGlobal.filtros = cfg.filtros;
        estadoGlobal.ordenacoes = cfg.ordenacoes;
        
        if(cfg.limite){
            estadoGlobal.limite = cfg.limite;
        }
        renderizarTudo();

    } else {
        redefinirConstrutorConsulta();
    }

    $('#modalConstrutorConsulta').modal('show');
}

export function salvarConfiguracaoTabela() {
    /* Salva a configuração da consulta no elemento selecionado */
    
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
    /* Insere os cabeçalhos na tabela selecionada */

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

    tornarComponentesDaTabelaRedimensionaveis(elementoSelecionado);
}

export function redefinirConstrutorConsulta() {
    /* Redefine o estado do construtor de consultas */

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
    /* Inicia a construção da consulta a partir do modelo raiz selecionado */

    estadoGlobal.modeloRaiz = nomeModelo;
    estadoGlobal.tabelas = [];
    estadoGlobal.colunas = [];
    estadoGlobal.filtros = [];
    estadoGlobal.ordenacoes = [];
    
    let limite = document.getElementById('input-limite-valor').value;
    estadoGlobal.limite = Number(limite) || null;

    const nomeAmigavel = nomeModelo;
    carregarTabela(nomeModelo, nomeAmigavel, "", "", "", "Raiz");
    renderizarTudo();
}

export function carregarTabela(modeloDestino, nomeAmigavel, caminhoPrefixo, campoRelacao, modeloAnterior, tipo) {
    /* Adiciona uma tabela ao estado global */

    estadoGlobal.tabelas.push({
        id: Math.random().toString(36).substring(2, 9),
        model: modeloDestino,
        modelo_anterior: modeloAnterior || "",
        nome_amigavel: nomeAmigavel,
        caminho: caminhoPrefixo,
        campo_relacao: campoRelacao,
        tipo: tipo
    });
}

export function adicionarJuncao(tabelaPaiId, conexaoIdx) {
    const tabelaPai = estadoGlobal.tabelas.find(t => t.id === tabelaPaiId);
    if (!tabelaPai) 
        return;

    const conexoes = ESQUEMA_DB[tabelaPai.model].conexoes;
    const conn = conexoes[conexaoIdx];
    const prefixo = tabelaPai.caminho + conn.campo_relacao + "__";
    
    carregarTabela(conn.model_destino, conn.nome_amigavel, prefixo, conn.campo_relacao, tabelaPai.model, "Junção");
    renderizarTudo();
}

export function adicionarColuna() {
    const indiceTabela = document.getElementById('select-col-tabela').value;
    const campoEntradaNomeCampo = document.getElementById('select-col-campo');
    const agg = document.getElementById('select-col-agregacao').value;
    const rotuloPersonalizado = document.getElementById('input-col-rotulo').value;
    let nomeCampo = campoEntradaNomeCampo.value;
    const trunc = document.getElementById('select-col-truncamento').value;
    
    if (indiceTabela === "" || nomeCampo === "") 
        return;

    const tab = estadoGlobal.tabelas[indiceTabela];
    const campos = ESQUEMA_DB[tab.model].campos;
    const campoObj = campos.find(c => c.valor === nomeCampo);
    const caminho = tab.caminho + nomeCampo;
    let rotuloExibicao;

    if(agg){
        if(rotuloPersonalizado){
            rotuloExibicao = rotuloPersonalizado;
        } else {
            rotuloExibicao = `${agg} de ${campoObj.rotulo}`;
        }
    } else if(rotuloPersonalizado){
        rotuloExibicao = rotuloPersonalizado;
    } else {
        rotuloExibicao = campoObj.rotulo;
    }

    estadoGlobal.colunas.push({
        tabela_origem: tab.nome_amigavel,
        campo: caminho,
        rotulo: rotuloExibicao,
        agregacao: agg || null,
        truncamento: trunc || null
    });

    /* se houver agregação ou truncamento, o método renderizarTudo() é chamado 
    para garantir que os novos campos sejam adicionados às opções dos campos 
    de seleção de filtros e ordenações */

    if(agg || trunc){
        renderizarTudo();
    } else {
        renderizarColunas();
        renderizarJson();
    }

    campoEntradaNomeCampo.value = "";
    document.getElementById('select-col-agregacao').value = "";
    document.getElementById('input-col-rotulo').value = "";
    document.getElementById('select-col-truncamento').value = "";
    document.getElementById('btn-add-coluna').disabled = true;
}

export function removerColuna(index) {
    const colunasRemovidas = estadoGlobal.colunas.splice(index, 1);
    
    // se a coluna tiver agregacao ou truncamento, 
    // serão removidos os possíveis filtros e ordenações relacionados a ela
    
    let colunaRemovida;

    if(colunasRemovidas.length > 0){
        colunaRemovida = colunasRemovidas[0];
    } else {
        return;
    }

    const sufixo = colunaRemovida.agregacao || colunaRemovida.truncamento;
    
    if(!sufixo){
        renderizarColunas();
        renderizarJson();
        return;
    }

    const nomeCampo = colunaRemovida.campo;

    estadoGlobal.filtros = estadoGlobal.filtros.filter(filtro => {
        if ((filtro.agregacao || filtro.truncamento)) {
            return !(filtro.campo == nomeCampo);
        } else {
            return true;
        }
    });
    estadoGlobal.ordenacoes = estadoGlobal.ordenacoes.filter(ordenacao => {
        return !(ordenacao.campo == nomeCampo);
    });
    renderizarTudo();
}

export function adicionarFiltro() {
    const indiceTabela = document.getElementById('select-filtro-tabela').value;
    const campoEntradaNomeCampo = document.getElementById('select-filtro-campo');
    const operador = document.getElementById('select-filtro-operador').value;
    const campoEntradaValorFiltro = document.getElementById('input-filtro-valor');
    const valorFiltro = campoEntradaValorFiltro.value;
    let nomeCampo = campoEntradaNomeCampo.value;
    
    if (indiceTabela === "" || nomeCampo === "") 
        return;
    
    const agregacao = campoEntradaNomeCampo.selectedOptions[0].dataset.agregacao;
    const truncamento = campoEntradaNomeCampo.selectedOptions[0].dataset.truncamento;

    const tab = estadoGlobal.tabelas[indiceTabela];
    estadoGlobal.filtros.push({
        campo: tab.caminho + nomeCampo,
        operador: operador,
        valor: valorFiltro,
        agregacao: agregacao || null,
        truncamento: truncamento || null
    });

    renderizarFiltros();
    renderizarJson();
    campoEntradaValorFiltro.value = "";
}

export function removerFiltro(index) {
    estadoGlobal.filtros.splice(index, 1);
    renderizarFiltros();
    renderizarJson();
}

export function adicionarOrdenacao() {
    const indiceTabela = document.getElementById('select-ordenacao-tabela').value;
    const campoEntradaNomeCampo = document.getElementById('select-ordenacao-campo');
    const ordem = document.getElementById('select-ordenacao-ordem').value;
    let nomeCampo = campoEntradaNomeCampo.value;

    if (indiceTabela === "" || nomeCampo === "") 
        return;

    const agregacao = campoEntradaNomeCampo.selectedOptions[0].dataset.agregacao;
    const truncamento = campoEntradaNomeCampo.selectedOptions[0].dataset.truncamento;

    const tab = estadoGlobal.tabelas[indiceTabela];
    estadoGlobal.ordenacoes.push({
        campo: tab.caminho + nomeCampo,
        ordem: ordem,
        agregacao: agregacao || null,
        truncamento: truncamento || null
    });

    renderizarOrdenacoes();
    renderizarJson();
    campoEntradaNomeCampo.value = "";
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

export function isTabelaJaAdicionada(modelo, modeloDestino) {
    /* Verifica se uma tabela já foi adicionada */

    /** se houver uma tabela com os mesmos modelo anterior e modelo de destino, retorna true; 
     * por exemplo, se já existe uma tabela que tem "Base" como modelo_anterior e "Unidade" como modelo, 
     * então não deve ser possível adicionar outra tabela que também tenha "Base" como modelo_anterior e "Unidade" como modelo */
    return estadoGlobal.tabelas.some(t => {
        return (t.modelo_anterior == modelo && t.model == modeloDestino);
    });
}

export function atualizarSelectCampos(tabelaIdx, idSelectAlvo, idBtn) {
    /* Atualiza as opções seleção de campos (colunas, filtros ou ordenações) com base na tabela selecionada */

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
    const campos = ESQUEMA_DB[tab.model].campos;
    campos.forEach(campo => {
        const opt = document.createElement('option');
        opt.value = campo.valor;
        opt.text = campo.rotulo;
        opt.dataset.tipo = campo.tipo;
        opt.dataset.agregacao = "";
        selectAlvo.appendChild(opt);
    });
    selectAlvo.disabled = false;

    if(idSelectAlvo == "select-col-campo")
        return;

    /* a partir daqui, são adicionadas ao campo de seleção as opções relacionadas a agregação ou truncamento*/

    let tab_caminho = tab.caminho.replace(/__$/, ""); // remove o '__' final; 'base__' torna-se 'base'

    const colunasAgregacao = estadoGlobal.colunas.filter(c => {
        if(!(c.agregacao))
            return false;

        let campo = extrairCaminhoTabelaDoCampo(c.campo);
        return campo == tab_caminho; // verifica se o campo pertence à tabela selecionada
    });

    colunasAgregacao.forEach(c => {
        criarElementoOpcao(selectAlvo, c.campo, c.rotulo, "number", "agregacao", c.agregacao);
    });

    // não permite adicionar filtros usando campos com truncamento de data (por enquanto)
    if(idSelectAlvo == "select-filtro-campo")
        return;

    function extrairCaminhoTabelaDoCampo(campoCompleto) {
        let partes = campoCompleto.split("__"); // separa a string em partes
        partes.pop(); // remove a última parte
        return partes.join("__"); // retorna as partes restantes de volta numa string
    }

    const colunasTruncamento = estadoGlobal.colunas.filter(c => {
        if(!(c.truncamento))
            return false;
        
        let campo = extrairCaminhoTabelaDoCampo(c.campo);
        return campo == tab_caminho;
    });

    colunasTruncamento.forEach(c => {
        criarElementoOpcao(selectAlvo, c.campo, c.rotulo, "date", "truncamento", c.truncamento);
    });

    function criarElementoOpcao(container, campo, rotulo, tipo, nomePropriedade, valorPropriedade){
        const opt = document.createElement('option');
        let nomeCampo = campo.split("__").at(-1); // pega apenas o nome do campo
        opt.value = nomeCampo;
        opt.text = rotulo;
        opt.dataset.tipo = tipo;
        opt.dataset[nomePropriedade] = valorPropriedade || "";
        container.appendChild(opt);
    }
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

    renderizarColunas();
    renderizarFiltros();
    renderizarOrdenacoes();
    renderizarLimite();
    renderizarJson();
}

export function renderizarEstruturaTabelas() {
    const container = document.getElementById('lista-tabelas');
    container.innerHTML = '';

    estadoGlobal.tabelas.forEach((tab, indice) => {
        const containerTabela = document.createElement('div'); // envolve o nome da tabela e suas conexões
        containerTabela.className = "mb-2 p-2 bg-white border rounded shadow-sm";
        const conexoes = ESQUEMA_DB[tab.model].conexoes;
        let btnsHtml = '';

        if (conexoes.length > 0) {
            btnsHtml = `
                <div class="d-flex align-items-center flex-wrap mt-2 mt-md-0" style="gap: 0.5rem;">
                    <small class="text-muted mr-2">Conectar:</small>
            `;
            conexoes.forEach((conn, idx) => {
                let desabilitado = '';
                
                if(isTabelaJaAdicionada(tab.model, conn.model_destino)){
                    desabilitado = 'disabled';
                }

                const btnClass = desabilitado ? 'btn-outline-secondary' : 'btn-outline-dark';
                btnsHtml += `<button type="button" class="btn ${btnClass} btn-sm mr-1 btn-add-join" ${desabilitado} data-tab-id="${tab.id}" data-conn-idx="${idx}">+ ${conn.nome_amigavel}</button>`;
            });
            btnsHtml += `</div>`;
        }

        const div = document.createElement('div'); // envolve o nome da tabela e o botão de remover
        div.classList.add("d-flex", "justify-content-between", "flex-wrap");

        div.innerHTML = `
            <div>
                <span class="badge badge-primary mr-2">${tab.tipo}</span>
                <span class="font-weight-bold">${tab.nome_amigavel}</span>
                    ${tab.caminho ? `<small class="text-muted ml-2">(via <code style="word-break: break-all;">${tab.caminho.slice(0, -2)}</code>)</small>` : ''}
                </div>
        `;

        if(indice > 0){    
            // botão de remover tabela
            let btnRmvTab = document.createElement('button');
            btnRmvTab.classList.add("btn", "btn-sm", "text-danger", "btn-remover-tabela");
            btnRmvTab.type = "button";
            btnRmvTab.ariaLabel = "Remover tabela";
            btnRmvTab.dataset.tabCaminho = tab.caminho;
            btnRmvTab.innerHTML = `
                <i class="bi bi-x-square-fill" aria-hidden="true"></i>
            `;
            div.appendChild(btnRmvTab);
        }

        containerTabela.appendChild(div);
        containerTabela.innerHTML += btnsHtml;
        container.appendChild(containerTabela);
    });
    
    Array.from(document.querySelectorAll(".btn-remover-tabela")).forEach(btn => {
        btn.addEventListener('click', evento => {
            const caminhoTabelaRemovida = evento.currentTarget.dataset.tabCaminho;
            atualizarEstadoGlobalRemocaoTabela(caminhoTabelaRemovida);
            renderizarTudo();
        });
    });
}

function atualizarEstadoGlobalRemocaoTabela(caminhoTabelaRemovida) {
    /* Remove a tabela e todos os elementos relacionados a ela (colunas, filtros, ordenações) do estado global */

    estadoGlobal.tabelas = estadoGlobal.tabelas.filter(t => {
        return !t.caminho.startsWith(caminhoTabelaRemovida);
    });

    estadoGlobal.colunas = estadoGlobal.colunas.filter(c => {
        return !c.campo.startsWith(caminhoTabelaRemovida);
    });

    estadoGlobal.filtros = estadoGlobal.filtros.filter(f => {
        return !f.campo.startsWith(caminhoTabelaRemovida);
    });

    estadoGlobal.ordenacoes = estadoGlobal.ordenacoes.filter(o => {
        return !o.campo.startsWith(caminhoTabelaRemovida);
    });
}

export function atualizarOpcoesSelect(idSelect) {
    /* Atualiza as opções de um select com base na lista de tabelas do estado global */

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
        // dispara o evento change para mudar o campo desabilitado do select
        select.dispatchEvent(new Event('change'));
    }
}

export function renderizarColunas() {
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
                    <span class="font-weight-bold small">${col.rotulo}</span>
                    <span class="text-muted" style="font-size:0.7rem;">${col.tabela_origem}</span>
                </div>
                <button class="btn btn-link text-danger p-0 btn-remover-col" data-idx="${idx}" aria-label="Apagar">
                    <i class="bi bi-x-circle-fill" aria-hidden="true"></i>
                </button>`;
            container.appendChild(div);
        });
        
        permitirReordenamentoColunas(container);
    }
}

function permitirReordenamentoColunas(containerColunas){
    new Sortable(containerColunas, {
        animation: 150,
        ghostClass: 'blue-background-class',
        onEnd: function(evento){
            /* reflete a alteração da ordem das colunas na configuração da consulta */
            const posicaoAnterior = evento.oldIndex;
            const novaPosicao = evento.newIndex;
            const coluna = estadoGlobal.colunas.splice(posicaoAnterior, 1)[0];
            estadoGlobal.colunas.splice(novaPosicao, 0, coluna);
        }
    });
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
            let sufixo = filtro.agregacao || filtro.truncamento;
            sufixo = sufixo ? `__${sufixo}` : "";
            tr.innerHTML = `
                <td class="text-primary">
                    <code style="word-break: break-all;">${filtro.campo}${sufixo}</code>
                </td>
                <td>${filtro.operador}</td>
                <td>${filtro.valor}</td>
                <td class="text-right">
                    <button class="btn btn-link text-danger p-0 btn-remover-filtro" data-idx="${idx}" aria-label="Apagar">
                        <i class="bi bi-trash" aria-hidden="true"></i>
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
            let sufixo = ordenacao.agregacao || ordenacao.truncamento;
            sufixo = sufixo ? `__${sufixo}` : "";
            tr.innerHTML = `
                <td class="text-primary">
                    <code style="word-break: break-all;">${ordenacao.campo}${sufixo}</code>
                </td>
                <td>${ordenacao.ordem == 'ASC' ? 'Crescente': 'Decrescente'}</td>
                <td class="text-right">
                    <button type="button" class="btn btn-link text-danger p-0 btn-remover-ordenacao" data-idx="${idx}" aria-label="Apagar">
                        <i class="bi bi-trash" aria-hidden="true"></i>
                    </button>
                </td>`;
            tbody.appendChild(tr);
        });
    }
}

export function renderizarLimite(){
    if(estadoGlobal.limite){
        document.getElementById('input-limite-valor').value = estadoGlobal.limite;
    }
}

export function gerarCargaUtil()
{
    return {
        fonte_principal: estadoGlobal.modeloRaiz,
        tabelas: estadoGlobal.tabelas,
        colunas: estadoGlobal.colunas,
        filtros: estadoGlobal.filtros,
        ordenacoes: estadoGlobal.ordenacoes,
        limite: estadoGlobal.limite
    };
}

export function renderizarJson() {
    /* Exibe o objeto que representa a configuração da consulta */
    const cargaUtil = gerarCargaUtil();
    const saidaJSON = document.getElementById('saida-json');
    
    if(saidaJSON){
        saidaJSON.textContent = JSON.stringify(cargaUtil, null, 4);
    }
}