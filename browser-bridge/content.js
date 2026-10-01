/**
 * Content Script para Themis Bridge no e-SAJ/TJSP
 * Sincronização completa de processo e ingestão pontual de peças via Hermes Plugin API.
 */
(function() {
  'use strict';

  let requestScopePromiseMap = new Map();
  let bulkDownloadPromiseMap = new Map();
  let activeSyncCnj = null;

  console.log("[Themis Bridge] Inicializando content script na Pasta Digital do e-SAJ...");

  // 1. Injetar script no contexto MAIN
  function injectMainScript() {
    if (document.getElementById("themis-bridge-injected")) return;
    const injectBridgeMain = () => {
      const script = document.createElement("script");
      script.id = "themis-bridge-injected";
      script.src = chrome.runtime.getURL("injected.js");
      document.documentElement.appendChild(script);
    };
    const bulkScript = document.createElement("script");
    bulkScript.id = "themis-bulk-download-selection";
    bulkScript.src = chrome.runtime.getURL("bulk_download_selection.js");
    bulkScript.onload = injectBridgeMain;
    document.documentElement.appendChild(bulkScript);
  }

  // 2. Ouvir respostas do script injetado
  window.addEventListener("message", function(event) {
    if (event.source !== window || !event.data) return;

    if (event.data.type === "THEMIS_SCOPE_RESPONSE") {
      const { requestId, success, data, pageContext, error } = event.data;
      const resolver = requestScopePromiseMap.get(requestId);
      if (resolver) {
        if (success) resolver.resolve({ scope: data, pageContext: pageContext || {} });
        else resolver.reject(new Error(error));
        requestScopePromiseMap.delete(requestId);
      }
    }
    if (event.data.type === "THEMIS_BULK_DOWNLOAD_RESPONSE") {
      const resolver = bulkDownloadPromiseMap.get(event.data.requestId);
      if (resolver) {
        if (event.data.success) resolver.resolve(event.data.data || {});
        else resolver.reject(new Error(event.data.error));
        bulkDownloadPromiseMap.delete(event.data.requestId);
      }
    }
    if (event.data.type === "THEMIS_BULK_DOWNLOAD_PROGRESS") {
      const resolver = bulkDownloadPromiseMap.get(event.data.requestId);
      if (resolver && typeof resolver.onProgress === "function") resolver.onProgress(event.data);
    }
  });

  chrome.runtime.onMessage.addListener(message => {
    if (message?.type !== "THEMIS_ZIP_DOWNLOAD_PROGRESS" || message.cnj !== activeSyncCnj) return;
    const downloaded = Number(message.downloadedBytes || 0);
    const total = Number(message.totalBytes || 0);
    const itemCount = Number(message.itemCount || 0);
    const mb = value => `${(value / (1024 * 1024)).toFixed(1)} MB`;
    const progress = total > 0
      ? `${Math.min(100, Math.round((downloaded / total) * 100))}% · ${mb(downloaded)}/${mb(total)}`
      : `${mb(downloaded)} recebidos`;
    const itemLabel = itemCount > 0 ? `pacote de ${itemCount} itens · ` : "pacote · ";
    showToastCard(`Baixando ${itemLabel}${progress}`, "info", true);
  });

  function sanitizeUrl(rawUrl) {
    if (!rawUrl || typeof rawUrl !== "string") return "";
    try {
      const parsed = new URL(rawUrl);
      const safeParams = new URLSearchParams();
      for (const [key, value] of parsed.searchParams.entries()) {
        const lowerKey = key.toLowerCase();
        if (["ticket", "token", "senha", "password", "auth", "session", "jwt", "credential", "bearer"].some(s => lowerKey.includes(s))) {
          safeParams.set(key, "[REDACTED]");
        } else if (["processo.codigo", "cdprocesso", "nuprocesso", "cdforo", "grau"].includes(lowerKey)) {
          safeParams.set(key, value);
        }
      }
      const qs = safeParams.toString();
      return qs ? `${parsed.origin}${parsed.pathname}?${qs}` : `${parsed.origin}${parsed.pathname}`;
    } catch {
      return "";
    }
  }

  function uint8ToBase64(bytes) {
    let binary = "";
    const chunkSize = 32768;
    for (let j = 0; j < bytes.length; j += chunkSize) {
      binary += String.fromCharCode.apply(null, bytes.subarray(j, Math.min(j + chunkSize, bytes.length)));
    }
    return btoa(binary);
  }

  function getRequestScope() {
    return new Promise((resolve, reject) => {
      const requestId = "req_" + Date.now() + "_" + Math.random().toString(36).substring(2, 7);
      requestScopePromiseMap.set(requestId, { resolve, reject });
      window.postMessage({ type: "THEMIS_GET_SCOPE", requestId }, "*");
      setTimeout(() => {
        if (requestScopePromiseMap.has(requestId)) {
          requestScopePromiseMap.delete(requestId);
          reject(new Error("Timeout ao consultar requestScope da Pasta Digital."));
        }
      }, 5000);
    });
  }

  function executeNativeBulkDownload(cdProcesso, documents, onProgress = null) {
    return new Promise((resolve, reject) => {
      const requestId = "bulk_download_" + Date.now() + "_" + Math.random().toString(36).substring(2, 7);
      bulkDownloadPromiseMap.set(requestId, { resolve, reject, onProgress });
      window.postMessage({ type: "THEMIS_EXECUTE_BULK_DOWNLOAD", requestId, cdProcesso, documents }, "*");
      setTimeout(() => {
        if (bulkDownloadPromiseMap.has(requestId)) {
          bulkDownloadPromiseMap.delete(requestId);
          reject(new Error("Tempo limite ao preparar o download nativo da Pasta Digital."));
        }
      }, 16 * 60 * 1000);
    });
  }

  function sendBridgeMessage(message) {
    return new Promise((resolve, reject) => {
      chrome.runtime.sendMessage(message, response => {
        if (chrome.runtime.lastError) {
          reject(new Error(chrome.runtime.lastError.message));
          return;
        }
        resolve(response);
      });
    });
  }

  // 3. Detecção e Validação Estrita de CNJ e Metadados do Processo
  function cleanDigits(val) {
    return String(val || "").replace(/\D/g, "");
  }

  function getProcessCnj(pageContext = {}) {
    const urlParams = new URLSearchParams(window.location.search);
    const fromParam = urlParams.get("nuProcesso") || urlParams.get("processo.numero");
    const ctxParam = pageContext.nuProcesso;

    let rawCnj = null;
    if (ctxParam) rawCnj = ctxParam.trim();
    else if (fromParam) rawCnj = fromParam.trim();
    else {
      const cnjRegex = /\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}/;
      const fromUrl = window.location.href.match(cnjRegex);
      if (fromUrl) rawCnj = fromUrl[0];
      else {
        const fromBody = (document.body ? document.body.innerText : "").match(cnjRegex);
        if (fromBody) rawCnj = fromBody[0];
      }
    }

    if (!rawCnj) return null;

    const digits = cleanDigits(rawCnj);
    if (digits.length !== 20) {
      throw new Error(`INVARIANT_VIOLATION: CNJ detectado '${rawCnj}' possui ${digits.length} dígitos, esperados 20.`);
    }

    // Invariante: nuProcesso da URL deve coincidir com o CNJ extraído da página
    if (fromParam) {
      const urlDigits = cleanDigits(fromParam);
      if (urlDigits && urlDigits !== digits) {
        throw new Error(`INVARIANT_VIOLATION: nuProcesso da URL ('${fromParam}') diverge do CNJ do processo ('${rawCnj}').`);
      }
    }

    // Invariante: pageContext.nuProcesso deve coincidir com o CNJ
    if (ctxParam) {
      const ctxDigits = cleanDigits(ctxParam);
      if (ctxDigits && ctxDigits !== digits) {
        throw new Error(`INVARIANT_VIOLATION: pageContext.nuProcesso ('${ctxParam}') diverge do CNJ do processo ('${rawCnj}').`);
      }
    }

    return `${digits.slice(0, 7)}-${digits.slice(7, 9)}.${digits.slice(9, 13)}.${digits.slice(13, 14)}.${digits.slice(14, 16)}.${digits.slice(16, 20)}`;
  }

  function extractProcessMetadata(pageContext = {}) {
    const cnj = getProcessCnj(pageContext);
    const meta = {
      cnj: cnj,
      source: "pastadigital_esaj",
      url: window.location.href
    };

    // Extrai cdProcesso da URL e do contexto
    const urlParams = new URLSearchParams(window.location.search);
    const urlCdProc = urlParams.get("cdProcesso") || urlParams.get("processo.codigo");
    const ctxCdProc = pageContext.cdProcesso;

    if (urlCdProc && ctxCdProc && String(urlCdProc).trim() !== String(ctxCdProc).trim()) {
      throw new Error(`INVARIANT_VIOLATION: cdProcesso da URL ('${urlCdProc}') diverge do pageContext.cdProcesso ('${ctxCdProc}').`);
    }

    meta.cdProcesso = urlCdProc || ctxCdProc || null;
    if (urlParams.get("cdForo")) meta.cdForo = urlParams.get("cdForo");
    if (pageContext.cdForo && !meta.cdForo) meta.cdForo = pageContext.cdForo;

    // Título ou cabeçalho do DOM se presente
    const headerTitle = document.querySelector(".pastaDigitalTitulo, #divBotoesInterna, .tituloProcesso");
    if (headerTitle) {
      meta.headerText = headerTitle.innerText.trim();
    }

    return meta;
  }

  // 3. Extração Estruturada e Simultânea: DOM (#proc_principal, #arvore_principal) + requestScope
  function parsePageInterval(text) {
    if (!text || typeof text !== "string") return { folhaInicial: null, folhaFinal: null, raw: null };
    const clean = text.trim();
    // Padrões comuns no e-SAJ: "Páginas 1 - 10", "Página 1 - 10", "fls. 1/10", "fls. 1000 - 1039", "fl. 5"
    const regexMulti = /(?:p[áa]ginas?|fls?\.?|folhas?\.?)\s*(\d+)\s*(?:-|a|\/|at[ée])\s*(\d+)/i;
    const matchMulti = clean.match(regexMulti);
    if (matchMulti) {
      return {
        folhaInicial: parseInt(matchMulti[1], 10),
        folhaFinal: parseInt(matchMulti[2], 10),
        raw: matchMulti[0]
      };
    }
    const regexSingle = /(?:p[áa]ginas?|fls?\.?|folhas?\.?)\s*(\d+)/i;
    const matchSingle = clean.match(regexSingle);
    if (matchSingle) {
      const val = parseInt(matchSingle[1], 10);
      return {
        folhaInicial: val,
        folhaFinal: val,
        raw: matchSingle[0]
      };
    }
    return { folhaInicial: null, folhaFinal: null, raw: null };
  }

  function extractDomTree() {
    const domNodes = [];
    const arvoreElem = document.getElementById("arvore_principal") || document.querySelector(".jstree, #arvoreDocumentos, ul.treeview");
    if (!arvoreElem) {
      console.warn("[Themis Bridge] #arvore_principal não encontrado no DOM.");
      return domNodes;
    }

    const treeItems = arvoreElem.querySelectorAll("li[role='treeitem'], li.jstree-node");
    let globalIndex = 0;

    treeItems.forEach((li) => {
      globalIndex++;
      const domId = li.id || null;
      const ariaLevel = parseInt(li.getAttribute("aria-level") || "1", 10);
      const ariaExpanded = li.getAttribute("aria-expanded") === "true";
      const anchor = li.querySelector("a.jstree-anchor, a");
      const label = anchor ? anchor.innerText.trim() : li.innerText.trim();
      
      // Encontra parent DOM se existir
      const parentLi = li.parentElement ? li.parentElement.closest("li[role='treeitem'], li.jstree-node") : null;
      const parentDomId = parentLi ? parentLi.id : null;

      const interval = parsePageInterval(label);

      domNodes.push({
        dom_order: globalIndex,
        dom_id: domId,
        aria_level: ariaLevel,
        aria_expanded: ariaExpanded,
        parent_dom_id: parentDomId,
        label: label,
        folha_inicial: interval.folhaInicial,
        folha_final: interval.folhaFinal,
        interval_raw: interval.raw
      });
    });

    return domNodes;
  }

  // Flatten e normalização da árvore correlacionando DOM com requestScope (Source-First)
  function flattenDocumentTree(scope, domNodes = [], tabCdProcesso = null) {
    const documents = [];
    if (!Array.isArray(scope)) return documents;

    // Mapa de nós DOM por ID ou fragmento
    const domByDocId = new Map();
    const domByOrder = new Map();
    domNodes.forEach((dn) => {
      if (dn.dom_id) domByDocId.set(dn.dom_id, dn);
      domByOrder.set(dn.dom_order, dn);
    });

    let topLevelIndex = 0;
    for (const node of scope) {
      if (!node) continue;
      topLevelIndex++;
      const nodeData = node.data || {};
      const children = Array.isArray(node.children) ? node.children : [];

      let downloadParams = nodeData.parametros || null;
      let folhaIni = nodeData.folhaInicial || nodeData.flsInicial || nodeData.nuPaginaInicial || null;
      let folhaFim = nodeData.folhaFinal || nodeData.flsFinal || nodeData.nuPaginaFinal || null;
      let parts = [];

      for (let cIdx = 0; cIdx < children.length; cIdx++) {
        const child = children[cIdx];
        if (!child || !child.data) continue;
        const childData = child.data;
        if (childData.parametros && !downloadParams) {
          downloadParams = childData.parametros;
        }
        if (!folhaIni && (childData.nuPaginaInicial || childData.folhaInicial)) {
          folhaIni = childData.nuPaginaInicial || childData.folhaInicial;
        }
        if (!folhaFim && (childData.nuPaginaFinal || childData.folhaFinal)) {
          folhaFim = childData.nuPaginaFinal || childData.folhaFinal;
        }
        parts.push({
          index: cIdx,
          title: childData.title || `Parte ${cIdx + 1}`,
          nuPaginaInicial: childData.nuPaginaInicial ? parseInt(childData.nuPaginaInicial, 10) : null,
          nuPaginaFinal: childData.nuPaginaFinal ? parseInt(childData.nuPaginaFinal, 10) : null,
          nuPaginas: childData.nuPaginas ? parseInt(childData.nuPaginas, 10) : 1,
          parametros: childData.parametros || null,
          cdItemPastaDigital: childData.cdItemPastaDigital || null,
          flIndisponivel: childData.flIndisponivel || false
        });
      }

      // Validação invariante: cdProcesso usado em getPDF.do deve coincidir com a aba
      if (downloadParams && tabCdProcesso) {
        const docParams = new URLSearchParams(downloadParams);
        const docCdProc = docParams.get("cdProcesso");
        if (docCdProc && String(docCdProc).trim() !== String(tabCdProcesso).trim()) {
          console.error(`[Themis Bridge] INVARIANT_VIOLATION: Documento '${nodeData.title}' possui cdProcesso=${docCdProc}, divergente da aba (${tabCdProcesso}). Descartando.`);
          continue;
        }
      }

      const cdDoc = nodeData.cdDocumento || (downloadParams ? new URLSearchParams(downloadParams).get("cdDocumento") : null);
      const title = nodeData.title || nodeData.deTipoDocDigital || nodeData.deDadosDoc || "Peça Processual";

      // Correlaciona com o nó DOM
      let matchedDom = null;
      if (cdDoc && domByDocId.has(`pasta_${cdDoc}`)) {
        matchedDom = domByDocId.get(`pasta_${cdDoc}`);
      } else if (cdDoc && domByDocId.has(String(cdDoc))) {
        matchedDom = domByDocId.get(String(cdDoc));
      } else if (domByOrder.has(topLevelIndex)) {
        matchedDom = domByOrder.get(topLevelIndex);
      }

      if (matchedDom && matchedDom.folha_inicial && !folhaIni) {
        folhaIni = matchedDom.folha_inicial;
      }
      if (matchedDom && matchedDom.folha_final && !folhaFim) {
        folhaFim = matchedDom.folha_final;
      }

      if (cdDoc || downloadParams) {
        documents.push({
          order: topLevelIndex,
          cdDocumento: cdDoc ? String(cdDoc) : "",
          cdItemPastaDigital: nodeData.cdItemPastaDigital || null,
          nuSequencia: nodeData.nuSequencia || topLevelIndex,
          flIndisponivel: nodeData.flIndisponivel || false,
          title: title,
          deTipoDocDigital: nodeData.deTipoDocDigital || title,
          dtInclusao: nodeData.dtInclusao || null,
          folhaInicial: folhaIni ? parseInt(folhaIni, 10) : null,
          folhaFinal: folhaFim ? parseInt(folhaFim, 10) : null,
          parametros: downloadParams,
          parts: parts,
          total_parts: parts.length > 0 ? parts.length : 1,
          dom_metadata: matchedDom || null
        });
      }
    }

    return documents;
  }

  // 4. Injeção da Interface Themis Bridge na Pasta Digital
  function injectToolbar() {
    if (document.getElementById("themis-bridge-toolbar")) return;

    const toggleBtn = document.getElementById("toggleArvoreButton");
    let container = null;

    if (toggleBtn && toggleBtn.parentElement && toggleBtn.parentElement.tagName === "TD") {
      container = toggleBtn.parentElement;
    } else {
      container = document.getElementById("divBotoesInterna") || document.querySelector("table.pastaDigitalTitulo td");
    }

    if (!container) return;

    const toolbar = document.createElement("div");
    toolbar.id = "themis-bridge-toolbar";
    toolbar.className = "themis-toolbar-container";

    // Botão Principal: Sincronizar Processo
    const syncBtn = document.createElement("button");
    syncBtn.id = "themis-sync-btn";
    syncBtn.type = "button";
    syncBtn.className = "themis-bridge-btn themis-btn-primary";
    syncBtn.innerHTML = `<span class="themis-icon">🔄</span> Sincronizar este processo`;
    syncBtn.title = "Sincroniza todas as peças e movimentações deste processo no Themis local (somente novidades)";

    syncBtn.addEventListener("click", async () => {
      await handleSyncProcess(syncBtn);
    });

    // Botão Secundário: Enviar Peça Atual
    const singleBtn = document.createElement("button");
    singleBtn.id = "themis-send-single-btn";
    singleBtn.type = "button";
    singleBtn.className = "themis-bridge-btn themis-btn-secondary";
    singleBtn.innerHTML = `<span class="themis-icon">📄</span> Enviar Peça`;
    singleBtn.title = "Ingerir a peça atual individualmente nos Autos do Themis";

    singleBtn.addEventListener("click", async () => {
      await handleSendSinglePiece(singleBtn);
    });

    toolbar.appendChild(syncBtn);
    toolbar.appendChild(singleBtn);

    if (toggleBtn) {
      container.insertBefore(toolbar, toggleBtn);
    } else {
      container.appendChild(toolbar);
    }

    console.log("[Themis Bridge] Toolbar de sincronização injetada com sucesso.");
  }

  // 4.1. Extração Estruturada e Sanitização da Capa CPOPG
  function sanitizeDomFragment(element) {
    if (!element) return "";
    const clone = element.cloneNode(true);

    // Remove tags executáveis ou de formulário
    const sensitiveTags = clone.querySelectorAll("script, style, link, iframe, form, input, button, select, textarea");
    sensitiveTags.forEach(el => el.remove());

    // Remove atributos inline e campos com dados sensíveis de autenticação
    const allEls = clone.querySelectorAll("*");
    allEls.forEach(el => {
      for (const attr of Array.from(el.attributes)) {
        const name = attr.name.toLowerCase();
        const val = attr.value.toLowerCase();
        if (name.startsWith("on")) {
          el.removeAttribute(attr.name);
        } else if (["ticket", "token", "auth", "session", "jsessionid", "cookie", "secret", "csrf", "nonce"].some(s => name.includes(s) || val.includes(s))) {
          el.removeAttribute(attr.name);
        } else if (name === "href" || name === "src") {
          el.setAttribute(attr.name, sanitizeUrl(attr.value));
        }
      }
    });

    return clone.innerHTML.trim();
  }

  function extractCpopgFromHtml(htmlText, cpopgUrl, processCnj = "") {
    if (!htmlText || typeof htmlText !== "string") return null;

    const doc = new DOMParser().parseFromString(htmlText, "text/html");
    const getElementFormattedText = (el) => {
      if (!el) return "";
      const clone = el.cloneNode(true);
      clone.querySelectorAll("br").forEach(br => br.replaceWith("\n"));
      clone.querySelectorAll("p, div, tr").forEach(block => block.append("\n"));
      return (clone.textContent || "").replace(/\r/g, "");
    };

    const getText = (selector) => {
      const el = doc.querySelector(selector);
      return el ? (el.textContent || "").trim().replace(/\s+/g, " ") : "";
    };
    const cnjPattern = /\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}/g;
    const findCnjByLabel = (labelRegex, excludeCnj = "") => {
      // CPOPG mixes table and div layouts. Never search an entire section for
      // the first CNJ: the section also contains the current process number.
      // Resolve the value adjacent to the *label* instead.
      const labels = doc.querySelectorAll("td, th, label, span, strong, b");
      for (const labelEl of labels) {
        const labelText = (labelEl.textContent || "").replace(/\s+/g, " ").trim();
        if (!labelText || labelText.length > 120 || !labelRegex.test(labelText)) continue;

        const valueCandidates = [];
        if (labelEl.nextElementSibling) valueCandidates.push(labelEl.nextElementSibling);

        const cell = labelEl.closest("td, th");
        if (cell?.nextElementSibling) valueCandidates.push(cell.nextElementSibling);

        const row = labelEl.closest("tr");
        if (row) {
          const cells = Array.from(row.querySelectorAll(":scope > td, :scope > th"));
          const ownerIndex = cells.findIndex((candidate) => candidate === cell || candidate.contains(labelEl));
          if (ownerIndex >= 0) valueCandidates.push(...cells.slice(ownerIndex + 1));
        }

        if (labelEl.parentElement?.nextElementSibling) {
          valueCandidates.push(labelEl.parentElement.nextElementSibling);
        }

        for (const valueEl of valueCandidates) {
          const valueText = (valueEl?.textContent || "").replace(/\s+/g, " ").trim();
          const matches = valueText.match(cnjPattern) || [];
          const related = matches.find((candidate) => candidate !== excludeCnj);
          if (related) return related;
        }
      }
      return "";
    };

    // 1. Dados Principais
    const mainContainer = doc.querySelector("#containerDadosPrincipaisProcesso, .secaoFormGrid, #dadosProcesso");
    const segredoJustica = !!(
      doc.querySelector(".segredoJustica, .badge-segredo, #segredoJustica") ||
      (mainContainer && /segredo\s+de\s+justi[çc]a/i.test(mainContainer.textContent || ""))
    );

    const currentCnjText = processCnj || getText("#numeroProcesso") || getText("#numeroDigitoAnoUnificado") || getText(".numeroProcesso");
    const currentCnj = (String(currentCnjText).match(cnjPattern) || [String(currentCnjText).trim()])[0] || "";
    const basicData = {
      cnj: currentCnj,
      segredo_justica: segredoJustica,
      segredo_justica_label: getText("#labelSegredoDeJusticaProcesso"),
      classe: getText("#classeProcesso") || getText("span[title='Classe']") || getText("#classe"),
      assunto: getText("#assuntoProcesso") || getText("span[title='Assunto']") || getText("#assunto"),
      outros_assuntos: getText("#outrosAssuntosProcesso") || getText("#outrosAssuntos"),
      foro: getText("#foroProcesso") || getText("#localFisicoProcesso") || getText("#foro"),
      vara: getText("#varaProcesso") || getText("#vara"),
      juiz: getText("#juizProcesso") || getText("#juiz"),
      distribuicao: getText("#dataHoraDistribuicaoProcesso") || getText("#dataDistribuicaoProcesso") || getText("#distribuicaoProcesso"),
      controle: getText("#numeroControleProcesso") || getText("#controleProcesso"),
      area: getText("#areaProcesso") || getText("#area"),
      valor_acao: getText("#valorAcaoProcesso") || getText("#valorAcao"),
      outros_numeros: getText("#outrosNumerosProcesso") || getText("#outrosNumeros"),
      processo_principal: findCnjByLabel(/processo\s+principal/i, currentCnj),
      apensado_ao: findCnjByLabel(/apensad[oa]\s+ao/i, currentCnj)
    };

    // 2. Partes e Advogados. tableTodasPartes contém o quadro completo, mesmo
    // quando tablePartesPrincipais está recolhida e mostra só parte do cadastro.
    const allPartiesTable = doc.querySelector("#tableTodasPartes");
    const partyTable = allPartiesTable || doc.querySelector("#tablePartesPrincipais") || doc.querySelector(".tabelaTodasPartes, .tabelaPartes");
    const primaryRows = partyTable
      ? Array.from(partyTable.querySelectorAll("tbody > tr"))
      : Array.from(doc.querySelectorAll("#tablePartesPrincipais > tbody > tr"));
    const rawRows = allPartiesTable
      ? Array.from(allPartiesTable.querySelectorAll("tr"))
      : (primaryRows.length > 0 ? [] : (partyTable ? Array.from(partyTable.querySelectorAll("tr")) : Array.from(doc.querySelectorAll(".secaoFormGrid tr, .tabelaPartes tr"))));

    const parties = [];
    const lawyers = [];
    const seenPartyKeys = new Set();
    const seenLawyerKeys = new Set();

    let currentParty = null;

    const lawyerRegex = /^(?:advogad[ao]|defensor(?:a)?|procurador(?:a)?|representante\s+legal)/i;

    function parseOab(str) {
      if (!str) return null;
      const match = str.match(/OAB\s*[\/:]?\s*([A-Z]{2})?\s*(\d+)(?:\s*[\/-]\s*([A-Z]{2}))?/i) ||
                    str.match(/(\d{4,8}\s*[\/-]\s*[A-Z]{2})/i) ||
                    str.match(/([A-Z]{2}\s*[\/-]?\s*\d{4,8})/i);
      return match ? match[0].replace(/\s+/g, " ").trim() : null;
    }

    function addLawyer(lawyerName, rawText, partyRepresented, partyRole) {
      let cleanName = lawyerName.replace(/^(?:Advogad[ao]|Defensor(?:a)?|Procurador(?:a)?|Representante\s+Legal)\s*:\s*/i, "").trim();
      const oab = parseOab(rawText || cleanName);
      if (oab) {
        cleanName = cleanName.replace(new RegExp(`\\(?\\s*${oab.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\)?`, 'i'), '').trim();
        cleanName = cleanName.replace(/\(\s*OAB.*?\)/i, '').trim();
      }
      if (!cleanName && rawText) {
        cleanName = rawText.replace(/^(?:Advogad[ao]|Defensor(?:a)?|Procurador(?:a)?|Representante\s+Legal)\s*:\s*/i, "").replace(/\(\s*OAB.*?\)/i, '').trim();
      }
      if (!cleanName) return;

      const key = `${(oab || cleanName).toLowerCase()}_${(partyRepresented || "").toLowerCase()}`;
      if (seenLawyerKeys.has(key)) return;
      seenLawyerKeys.add(key);

      lawyers.push({
        party_represented: partyRepresented || null,
        party_role: partyRole || null,
        lawyer_name: cleanName,
        raw_text: rawText || cleanName,
        oab: oab
      });
    }

    function fragmentText(fragment) {
      const holder = doc.createElement("div");
      holder.appendChild(fragment);
      holder.querySelectorAll(".mensagemExibindo").forEach(el => el.remove());
      return (holder.textContent || "").replace(/\s+/g, " ").trim();
    }

    function rowTextBetween(cell, startNode, endNode) {
      const range = doc.createRange();
      if (startNode) range.setStartAfter(startNode); else range.setStart(cell, 0);
      if (endNode) range.setEndBefore(endNode); else range.setEnd(cell, cell.childNodes.length);
      return fragmentText(range.cloneContents());
    }

    for (const row of primaryRows) {
      const role = (row.querySelector(".tipoDeParticipacao")?.textContent || "").replace(/\s+/g, " ").trim();
      const cell = row.querySelector(".nomeParteEAdvogado");
      if (!cell) continue;

      const relationLabels = Array.from(cell.querySelectorAll(".mensagemExibindo"));
      const partyName = rowTextBetween(cell, null, relationLabels[0]).replace(/\s+/g, " ").trim();
      let partyEntry = null;
      if (partyName) {
        const partyKey = `${role.toLowerCase()}_${partyName.toLowerCase()}`;
        partyEntry = parties.find(item => `${String(item.role || "").toLowerCase()}_${String(item.name || "").toLowerCase()}` === partyKey) || null;
        if (!partyEntry && !seenPartyKeys.has(partyKey)) {
          seenPartyKeys.add(partyKey);
          partyEntry = { role: role || "PARTE", name: partyName, relations: [] };
          parties.push(partyEntry);
        }
      }
      for (let i = 0; i < relationLabels.length; i++) {
        const label = (relationLabels[i].textContent || "").replace(/\s+/g, " ").replace(/[:\s]+$/, "").trim();
        const raw = rowTextBetween(cell, relationLabels[i], relationLabels[i + 1]);
        if (!raw) continue;
        const relation = { label, name: raw, raw_text: `${label}: ${raw}` };
        if (partyEntry) partyEntry.relations.push(relation);
        if (/^(?:advogad[ao]|defensor(?:a)?|procurador(?:a)?|representante\s+legal)$/i.test(label)) {
          addLawyer(raw, relation.raw_text, partyName || null, role || null);
        }
      }
    }

    for (const r of rawRows) {
      const cells = Array.from(r.querySelectorAll("td"));
      if (cells.length === 0) continue;

      const labelCell = cells[0];
      const nameCell = cells.length > 1 ? cells[cells.length - 1] : cells[0];

      const labelRaw = (labelCell ? (labelCell.textContent || "") : "").replace(/[\r\n\t]+/g, " ").replace(/\s+/g, " ").trim().replace(/[:\s]+$/, "");
      const formattedName = getElementFormattedText(nameCell);
      const nameLines = formattedName
        .replace(/\r\n?/g, "\n")
        .split("\n")
        .map(line => line.replace(/[\t\f\v ]+/g, " ").trim())
        .filter(Boolean);
      if (nameLines.length === 0) continue;

      // Caso A: A própria linha é de advogado (ex: td.label = "Advogado:")
      if (lawyerRegex.test(labelRaw)) {
        for (const line of nameLines) {
          addLawyer(line, line, currentParty ? currentParty.name : null, currentParty ? currentParty.role : null);
        }
        continue;
      }

      // Caso B: Linha de Parte Processual (ex: "Reqte:", "Reqdo:", "Autor:", "Réu:", etc.)
      const firstLine = nameLines[0];
      if (lawyerRegex.test(firstLine)) {
        addLawyer(firstLine, firstLine, currentParty ? currentParty.name : null, currentParty ? currentParty.role : null);
      } else {
        const partyRole = labelRaw || "PARTE";
        const partyName = firstLine;
        const partyKey = `${partyRole.toLowerCase()}_${partyName.toLowerCase()}`;

        if (!seenPartyKeys.has(partyKey)) {
          seenPartyKeys.add(partyKey);
          currentParty = {
            role: partyRole,
            name: partyName
          };
          parties.push(currentParty);
        }
      }

      // Processar linhas adicionais na mesma célula (ex: advogados após <br>)
      if (nameLines.length > 1) {
        for (let k = 1; k < nameLines.length; k++) {
          const line = nameLines[k];
          if (lawyerRegex.test(line) || /oab/i.test(line)) {
            addLawyer(line, line, currentParty ? currentParty.name : null, currentParty ? currentParty.role : null);
          }
        }
      }
    }

    // 3. Audiências (Descoberta robusta no DOM da Capa CPOPG)
    const hearings = [];
    const seenHearingKeys = new Set();

    const hearingTableCandidates = [
      doc.querySelector("#tabelaTodasAudiencias"),
      doc.querySelector("#tabelaAudiencias"),
      doc.querySelector("#tableAudiencias"),
      doc.querySelector("#audiencias"),
      doc.querySelector("#secaoAudiencias"),
      doc.querySelector("#tabelaResultadoAudiencia"),
      doc.querySelector("#gridAudiencias"),
      ...Array.from(doc.querySelectorAll("table.secaoFormGrid, table.tabelaGrid, table")).filter(t => {
        const headerText = (t.textContent || "").slice(0, 300);
        return /audi[êe]ncia/i.test(headerText) && (/data/i.test(headerText) || /situa[çc][ãa]o/i.test(headerText));
      })
    ].filter(Boolean);

    const hearingTables = Array.from(new Set(hearingTableCandidates));

    for (const hTable of hearingTables) {
      const rows = hTable.querySelectorAll("tr");
      rows.forEach(r => {
        const cells = Array.from(r.querySelectorAll("td")).map(c => (c.textContent || "").trim().replace(/\s+/g, " "));
        if (cells.length >= 2) {
          const dateMatch = cells[0].match(/\d{2}\/\d{2}\/\d{4}/);
          if (dateMatch) {
            const dataHora = cells[0];
            const tipo = cells[1] || "Audiência";
            const situacao = cells[2] || "Designada";
            const location = cells[3] || (cells.length > 4 ? cells.slice(3).join(" - ") : null);
            const key = `${dataHora}_${tipo}_${situacao}_${location || ""}`;
            if (!seenHearingKeys.has(key)) {
              seenHearingKeys.add(key);
              hearings.push({
                data_hora: dataHora,
                tipo: tipo,
                situacao: situacao,
                location: location,
                raw_cells: cells
              });
            }
          }
        }
      });
    }

    // Fallback geral para audiências
    if (hearings.length === 0) {
      const allTrs = doc.querySelectorAll("tr");
      allTrs.forEach(r => {
        const cells = Array.from(r.querySelectorAll("td")).map(c => (c.textContent || "").trim().replace(/\s+/g, " "));
        if (cells.length >= 2) {
          const firstCell = cells[0];
          const dateMatch = firstCell.match(/\d{2}\/\d{2}\/\d{4}/);
          const rowText = cells.join(" ");
          if (dateMatch && /concilia[çc][ãa]o|instru[çc][ãa]o|julgamento|audi[êe]ncia|designada|realizada|cancelada/i.test(rowText)) {
            const key = `${firstCell}_${cells[1] || ''}_${cells[2] || ''}`;
            if (!seenHearingKeys.has(key)) {
              seenHearingKeys.add(key);
              hearings.push({
                data_hora: firstCell,
                tipo: cells[1] || "Audiência",
                situacao: cells[2] || "Designada",
                location: cells[3] || null,
                raw_cells: cells
              });
            }
          }
        }
      });
    }

    // 4. Incidentes, Ações Incidentais, Recursos e Execuções
    const incidents = [];
    const incidentRows = doc.querySelectorAll("#tabelaIncidentes tr, #tableIncidentes tr, #tabelaRecursos tr, #tabelaExecucoes tr");
    incidentRows.forEach(r => {
      const cells = Array.from(r.querySelectorAll("td")).map(c => c.innerText.trim());
      if (cells.length >= 2) {
        incidents.push({
          tipo: cells[0],
          numero: cells[1],
          descricao: cells[2] || cells[1]
        });
      }
    });

    // 5. Processos Apensos / Entranhados / Unificados
    const relatedProcesses = [];
    const apensosRows = doc.querySelectorAll("#tabelaApensos tr, #tabelaProcessosApensos tr, #tableApensos tr");
    apensosRows.forEach(r => {
      const cells = Array.from(r.querySelectorAll("td")).map(c => (c.textContent || "").trim());
      if (cells.length >= 2) {
        relatedProcesses.push({
          tipo: cells[0],
          numero: cells[1]
        });
      }
    });

    // 6. Petições Diversas
    const petitions = [];
    const petitionRows = doc.querySelectorAll("#tabelaTodasPeticoes tr, #tabelaPeticoes tr, #tablePeticoes tr");
    petitionRows.forEach(r => {
      const cells = Array.from(r.querySelectorAll("td")).map(c => (c.textContent || "").trim());
      if (cells.length >= 2) {
        petitions.push({
          data: cells[0],
          tipo: cells[1],
          protocolo: cells[2] || null
        });
      }
    });

    // 7. Fragmentos DOM-fonte Sanitizados
    const sanitizedFragments = {
      dados_principais_html: sanitizeDomFragment(doc.querySelector("#containerDadosPrincipaisProcesso, .secaoFormGrid, #dadosProcesso")),
      mais_detalhes_html: sanitizeDomFragment(doc.querySelector("#maisDetalhes, .maisDetalhes")),
      partes_html: sanitizeDomFragment(doc.querySelector("#tableTodasPartes, #tablePartesPrincipais, .tabelaPartes")),
      audiencias_html: sanitizeDomFragment(doc.querySelector("#tabelaTodasAudiencias, #tabelaAudiencias, #tableAudiencias, .tabelaAudiencias")),
      incidentes_html: sanitizeDomFragment(doc.querySelector("#tabelaIncidentes, #tableIncidentes, .tabelaIncidentes")),
      apensos_html: sanitizeDomFragment(doc.querySelector("#tabelaApensos, #tableApensos")),
      peticoes_html: sanitizeDomFragment(doc.querySelector("#tabelaTodasPeticoes, #tabelaPeticoes"))
    };

    return {
      captured_at: new Date().toISOString(),
      canonical_url: sanitizeUrl(cpopgUrl),
      source: "cpopg_esaj",
      basic_data: basicData,
      parties: parties,
      lawyers: lawyers,
      hearings: hearings,
      incidents: incidents,
      related_processes: relatedProcesses,
      petitions: petitions,
      sanitized_dom_fragments: sanitizedFragments
    };
  }

  // 5. Sincronização incremental: inventário provider → somente novas peças
  async function handleSyncProcess(btn) {
    const originalText = btn.innerHTML;
    btn.disabled = true;
    showToastCard("Consultando estrutura e metadados da Pasta Digital...", "info", true);

    let cnj = "";
    try {
      // Passo 1: Capturar snapshot DOM + requestScope antes do download
      const scopeData = await getRequestScope();
      const pageContext = scopeData.pageContext || {};

      cnj = getProcessCnj(pageContext);
      if (!cnj) {
        throw new Error("Não foi possível identificar o número CNJ do processo nesta página.");
      }
      activeSyncCnj = cnj;

      const meta = extractProcessMetadata(pageContext);
      const domNodes = extractDomTree();
      const allDocs = flattenDocumentTree(scopeData.scope, domNodes, meta.cdProcesso);

      if (!Array.isArray(scopeData.scope) || scopeData.scope.length === 0) {
        throw new Error("window.requestScope está vazio ou não possui documentos.");
      }

      // Passo 1.1: Fetch da Capa CPOPG da mesma sessão autenticada (sem alterar navegação)
      showToastCard("Consultando capa CPOPG do processo...", "info", true);
      let cpopgData = null;
      if (meta.cdProcesso) {
        const cpopgRelUrl = `/cpopg/show.do?processo.codigo=${encodeURIComponent(meta.cdProcesso)}&processo.foro=${encodeURIComponent(meta.cdForo || '')}&processo.numero=${encodeURIComponent(cnj)}`;
        const cpopgUrl = `${window.location.origin}${cpopgRelUrl}`;
        const cpopgStart = performance.now();
        console.info(`[Themis Bridge] [CPOPG_FETCH] INÍCIO: GET ${cpopgRelUrl}`);

        try {
          const cpopgResp = await fetch(cpopgUrl, { method: "GET", credentials: "include" });
          const cpopgDur = Math.round(performance.now() - cpopgStart);

          if (cpopgResp.ok) {
            const htmlText = await cpopgResp.text();
            cpopgData = extractCpopgFromHtml(htmlText, cpopgUrl, cnj);
            console.info(`[Themis Bridge] [CPOPG_FETCH] SUCESSO: HTTP ${cpopgResp.status} (${cpopgDur}ms)`, {
              classe: cpopgData?.basic_data?.classe,
              parties: cpopgData?.parties?.length,
              lawyers: cpopgData?.lawyers?.length,
              hearings: cpopgData?.hearings?.length
            });
          } else {
            console.error("[Themis Bridge] [CPOPG_FETCH] ERRO:", {
              stage: "CPOPG_FETCH",
              errorName: "HttpStatusError",
              message: `HTTP ${cpopgResp.status}`,
              cause: null,
              url: cpopgRelUrl,
              method: "GET"
            });
          }
        } catch (cpopgErr) {
          console.error("[Themis Bridge] [CPOPG_FETCH] ERRO:", {
            stage: "CPOPG_FETCH",
            errorName: cpopgErr.name || "Error",
            message: cpopgErr.message,
            cause: cpopgErr.cause || null,
            url: cpopgRelUrl,
            method: "GET"
          });
        }
      }

      // Passo 1.2: Registro de Plano e Snapshot no Themis
      showToastCard("Registrando snapshot canônico e Dossiê no Themis...", "info", true);
      const planStart = performance.now();
      console.info("[Themis Bridge] [THEMIS_SYNC_PLAN] INÍCIO: POST /api/plugins/themis/bridge/sync/plan");

      const planResponse = await sendBridgeMessage({
          action: "SYNC_PLAN",
          payload: {
            cnj: cnj,
            metadata: {
              cdProcesso: meta.cdProcesso,
              nuProcesso: cnj,
              url: sanitizeUrl(window.location.href),
              source: "pastadigital_esaj",
              total_scope_items: scopeData.scope.length
            },
            page_context: pageContext,
            documents: allDocs,
            participants: meta.participants || [],
            movements: meta.movements || [],
            cpopg: cpopgData
          }
      });

      const planDur = Math.round(performance.now() - planStart);
      if (!planResponse || !planResponse.success) {
        const errMsg = (planResponse && planResponse.error) ? planResponse.error : "Falha ao registrar snapshot do processo no Themis";
        console.error("[Themis Bridge] [THEMIS_SYNC_PLAN] ERRO:", {
          stage: "THEMIS_SYNC_PLAN",
          errorName: "SyncPlanError",
          message: errMsg,
          cause: null,
          url: "/api/plugins/themis/bridge/sync/plan",
          method: "POST"
        });
        throw new Error(errMsg);
      }
      console.info(`[Themis Bridge] [THEMIS_SYNC_PLAN] SUCESSO: (${planDur}ms)`);

      const plan = planResponse.data || {};
      const newDocuments = Array.isArray(plan.needed_documents) ? plan.needed_documents : [];
      if (newDocuments.length === 0) {
        showToastCard("✅ Processo já está atualizado: nenhuma peça nova para baixar.", "success", false, 6000);
        return;
      }

      // Fase B: o protocolo bulk nativo permanece transparente. NEW substitui
      // somente o antigo conjunto ALL; não há interação com a árvore ou modal.
      showToastCard(`e-SAJ preparando pacote para ${newDocuments.length} nova(s) peça(s)...`, "info", true);
      const nativeResult = await executeNativeBulkDownload(meta.cdProcesso, newDocuments, update => {
        const max = Number(update.maxAttempts || 300);
        showToastCard(`e-SAJ preparando ${update.itemCount || newDocuments.length} peças · verificação ${update.attempt}/${max}`, "info", true);
      });
      const uploadResult = await sendBridgeMessage({
          action: "DOWNLOAD_AND_UPLOAD_ZIP",
          cnj,
          downloadUrl: nativeResult.downloadUrl,
          itemCount: nativeResult.itemCount,
      });
      if (!uploadResult || !uploadResult.success) {
        throw new Error((uploadResult && uploadResult.error) || "Falha ao receber o pacote nativo da Pasta Digital.");
      }

      console.info("[Themis Bridge] [THEMIS_INCREMENTAL_BULK_DOWNLOAD] CONCLUÍDO", {
        existing: plan.already_ingested_count || 0,
        selectedDocuments: nativeResult.documentCount,
        selectedItems: nativeResult.itemCount,
      });
      showToastCard(
        `✅ Pacote recebido pelo Themis · ${nativeResult.itemCount || newDocuments.length} peças. O processamento continua no Themis; você já pode fechar esta etapa no navegador.`,
        "success",
        false,
        10000
      );
    } catch (err) {
      console.error(`[Themis Bridge] Erro na sincronização (Origem: pastadigital_esaj, CNJ: ${cnj || "desconhecido"}):`, err);
      showToastCard(`❌ Erro na sincronização incremental: ${err.message}`, "error", false, 12000);
    } finally {
      activeSyncCnj = null;
      btn.disabled = false;
      btn.innerHTML = originalText;
    }
  }

  // 6. Envio Individual de Peça
  async function handleSendSinglePiece(btn) {
    const originalText = btn.innerHTML;
    btn.disabled = true;
    showToastCard("Lendo peça atual...", "info", true);

    let cnj = "";
    try {
      const scopeData = await getRequestScope();
      const pageContext = scopeData.pageContext || {};

      cnj = getProcessCnj(pageContext);
      if (!cnj) {
        throw new Error("Não foi possível identificar o número CNJ do processo nesta página.");
      }

      const meta = extractProcessMetadata(pageContext);
      const domNodes = extractDomTree();
      const allDocs = flattenDocumentTree(scopeData.scope, domNodes, meta.cdProcesso);
      if (allDocs.length === 0) {
        throw new Error("Nenhum documento encontrado na Pasta Digital.");
      }

      const targetDoc = allDocs[0];

      // Passo A: Garantir criação do processo/snapshot no Themis antes do envio da peça
      showToastCard("Preparando registro do processo no Themis...", "info", true);
      const planResponse = await new Promise((resolve) => {
        chrome.runtime.sendMessage({
          action: "SYNC_PLAN",
          payload: {
            cnj: cnj,
            metadata: {
              cdProcesso: meta.cdProcesso,
              nuProcesso: cnj,
              url: sanitizeUrl(window.location.href),
              source: "pastadigital_esaj"
            },
            page_context: pageContext,
            documents: allDocs,
            participants: meta.participants || [],
            movements: meta.movements || []
          }
        }, resolve);
      });

      if (!planResponse || !planResponse.success) {
        throw new Error((planResponse && planResponse.error) ? planResponse.error : "Falha ao preparar processo no Themis");
      }

      // Passo B: Download da peça (e suas partes se multipartes)
      const hasMultiParts = Array.isArray(targetDoc.parts) && targetDoc.parts.length > 1;
      const totalParts = hasMultiParts ? targetDoc.parts.length : 1;
      let mainBase64 = null;
      let partsBase64 = [];

      if (hasMultiParts) {
        for (let pIdx = 0; pIdx < targetDoc.parts.length; pIdx++) {
          const part = targetDoc.parts[pIdx];
          const partParams = part.parametros || targetDoc.parametros;
          if (!partParams) continue;

          showToastCard(`Baixando ${targetDoc.title} (Parte ${pIdx + 1}/${totalParts})...`, "info", true);
          const pdfUrl = `${window.location.origin}/pastadigital/getPDF.do?${partParams}`;
          const resp = await fetch(pdfUrl, { method: "GET", credentials: "include" });
          if (!resp.ok) {
            throw new Error(`Falha no download da parte ${pIdx + 1}: HTTP ${resp.status}`);
          }
          const arrayBuffer = await resp.arrayBuffer();
          const bytes = new Uint8Array(arrayBuffer);
          if (bytes.length < 4 || !(bytes[0] === 0x25 && bytes[1] === 0x50 && bytes[2] === 0x44 && bytes[3] === 0x46)) {
            throw new Error(`Parte ${pIdx + 1} não é um PDF válido.`);
          }
          const b64 = uint8ToBase64(bytes);
          partsBase64.push(b64);
          if (pIdx === 0) mainBase64 = b64;
        }
      } else {
        const pdfUrl = `${window.location.origin}/pastadigital/getPDF.do?${targetDoc.parametros}`;
        const resp = await fetch(pdfUrl, { method: "GET", credentials: "include" });
        if (!resp.ok) {
          throw new Error(`Falha no download da peça: HTTP ${resp.status}`);
        }
        const arrayBuffer = await resp.arrayBuffer();
        const bytes = new Uint8Array(arrayBuffer);
        if (bytes.length < 4 || !(bytes[0] === 0x25 && bytes[1] === 0x50 && bytes[2] === 0x44 && bytes[3] === 0x46)) {
          throw new Error("O arquivo retornado não é um PDF válido.");
        }
        mainBase64 = uint8ToBase64(bytes);
      }

      if (!mainBase64) {
        throw new Error("Não foi possível obter o binário PDF da peça.");
      }

      // Passo C: Ingestão atômica da peça
      showToastCard(`Indexando peça '${targetDoc.title}'...`, "info", true);
      const ingestResponse = await new Promise((resolve) => {
        chrome.runtime.sendMessage({
          action: "INGEST_PDF",
          payload: {
            cnj: cnj,
            filename: `${targetDoc.cdDocumento ? targetDoc.cdDocumento + "_" : ""}${targetDoc.title.replace(/[^a-zA-Z0-9_-]/g, "_")}.pdf`,
            content_base64: mainBase64,
            parts_base64: partsBase64.length > 1 ? partsBase64 : undefined,
            page_context: pageContext,
            metadata: {
              docName: targetDoc.title,
              deTipoDocDigital: targetDoc.deTipoDocDigital,
              cdDocumento: targetDoc.cdDocumento,
              cdProcesso: meta.cdProcesso,
              dtInclusao: targetDoc.dtInclusao,
              folhaInicial: targetDoc.folhaInicial,
              folhaFinal: targetDoc.folhaFinal,
              url: sanitizeUrl(window.location.href),
              source: "pastadigital_esaj",
              parts_count: totalParts
            }
          }
        }, resolve);
      });

      if (!ingestResponse || !ingestResponse.success) {
        throw new Error((ingestResponse && ingestResponse.error) ? ingestResponse.error : "Falha na ingestão");
      }

      // Passo D: Reconciliação dos Autos
      await new Promise((resolve) => {
        chrome.runtime.sendMessage({
          action: "SYNC_FINISH",
          payload: { cnj: cnj, metadata: meta, page_context: pageContext }
        }, resolve);
      });

      showToastCard(`✅ Peça '${targetDoc.title}' enviada aos Autos do Themis (CNJ: ${cnj})!`, "success", false, 6000);
    } catch (err) {
      console.error(`[Themis Bridge] Erro no envio de peça (Origem: pastadigital_esaj, CNJ: ${cnj || "desconhecido"}):`, err.message);
      showToastCard(`❌ Erro: ${err.message}`, "error", false, 8000);
    } finally {
      btn.disabled = false;
      btn.innerHTML = originalText;
    }
  }

  // 7. Toast / Status Card Flutuante
  function showToastCard(msg, type, isSpinner = false, duration = 0) {
    let card = document.getElementById("themis-bridge-toast");
    if (!card) {
      card = document.createElement("div");
      card.id = "themis-bridge-toast";
      document.body.appendChild(card);
    }

    card.className = `themis-toast themis-toast-${type}`;
    const formattedMsg = msg.replace(/\n/g, "<br>");

    if (isSpinner) {
      card.innerHTML = `<span class="themis-spinner"></span> <span>${formattedMsg}</span>`;
    } else {
      card.innerHTML = `<span>${formattedMsg}</span>`;
    }

    if (duration > 0) {
      setTimeout(() => {
        if (card && card.parentNode) {
          card.classList.add("themis-toast-fadeout");
          setTimeout(() => card.remove(), 400);
        }
      }, duration);
    }
  }

  // Inicialização
  injectMainScript();

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", injectToolbar);
  } else {
    injectToolbar();
  }

  const observer = new MutationObserver(() => {
    if (!document.getElementById("themis-bridge-toolbar")) {
      injectToolbar();
    }
  });
  observer.observe(document.body, { childList: true, subtree: true });

})();
