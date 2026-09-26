/**
 * Injected script no contexto MAIN da página e-SAJ
 * Permite ler com segurança objetos do DOM/JSF como window.requestScope e variáveis globais
 */
(function() {
  'use strict';

  function extractPageContext() {
    const ctx = {};
    try {
      if (typeof cdProcesso !== 'undefined') ctx.cdProcesso = cdProcesso;
      if (typeof nuProcesso !== 'undefined') ctx.nuProcesso = nuProcesso;
      if (typeof cdForo !== 'undefined') ctx.cdForo = cdForo;
      if (typeof flsInicial !== 'undefined') ctx.flsInicial = flsInicial;
      if (typeof flsFinal !== 'undefined') ctx.flsFinal = flsFinal;
    } catch (e) {}
    return ctx;
  }

  window.addEventListener('message', function(event) {
    if (event.source !== window || !event.data) return;

    if (event.data.type === 'THEMIS_GET_SCOPE') {
      const requestId = event.data.requestId;
      if (typeof requestScope !== 'undefined' && Array.isArray(requestScope)) {
        window.postMessage({
          type: 'THEMIS_SCOPE_RESPONSE',
          requestId: requestId,
          success: true,
          data: requestScope,
          pageContext: extractPageContext()
        }, '*');
      } else {
        window.postMessage({
          type: 'THEMIS_SCOPE_RESPONSE',
          requestId: requestId,
          success: false,
          error: 'window.requestScope não encontrado no contexto da página.',
          pageContext: extractPageContext()
        }, '*');
      }
    }

    if (event.data.type === 'THEMIS_EXECUTE_BULK_DOWNLOAD') {
      const { requestId, cdProcesso, documents } = event.data;

      (async () => {
        try {
          if (!window.ThemisBulkDownloadSelection) {
            throw new Error('Preparação transparente de download não foi carregada no contexto MAIN.');
          }
          const selection = window.ThemisBulkDownloadSelection.prepareNativeBulkDownload(
            Array.isArray(documents) ? documents : []
          );
          if (!selection) {
            throw new Error('Nenhuma peça NEW foi informada para o download nativo.');
          }
          const { itemParameters: itemsParams, lastCdDocumento } = selection;
          // 1. Estágio: BULK_PENDING
          const pendingStart = performance.now();
          console.info("[Themis Bridge] [BULK_PENDING] INÍCIO: POST /pastadigital/obterListaDocumentosPendentesRecebimento.do", { itemsCount: itemsParams.length });

          const obterBody = new URLSearchParams();
          for (const p of itemsParams) {
            obterBody.append("itensPdfSelecionados", p);
          }

          await new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();
            xhr.open("POST", "/pastadigital/obterListaDocumentosPendentesRecebimento.do", true);
            xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded; charset=UTF-8");
            xhr.setRequestHeader("X-Requested-With", "XMLHttpRequest");
            xhr.setRequestHeader("Accept", "*/*");
            xhr.onload = () => {
              const durationMs = Math.round(performance.now() - pendingStart);
              console.info(`[Themis Bridge] [BULK_PENDING] SUCESSO: HTTP ${xhr.status} (${durationMs}ms)`);
              resolve();
            };
            xhr.onerror = () => {
              const durationMs = Math.round(performance.now() - pendingStart);
              const errObj = {
                stage: "BULK_PENDING",
                errorName: "NetworkError",
                message: "Falha de rede em obterListaDocumentosPendentesRecebimento.do",
                cause: null,
                url: "/pastadigital/obterListaDocumentosPendentesRecebimento.do",
                method: "POST"
              };
              console.error("[Themis Bridge] [BULK_PENDING] ERRO:", errObj);
              // Não bloqueia preparação caso o endpoint de validação seja opcional
              resolve();
            };
            xhr.send(obterBody.toString());
          });

          // Resolve cdProcesso e cdDocumento de forma defensiva
          const urlParams = new URLSearchParams(window.location.search);
          let effectiveCdProc = cdProcesso || (typeof window.cdProcesso !== 'undefined' ? window.cdProcesso : null) || urlParams.get("cdProcesso") || urlParams.get("processo.codigo");
          let effectiveCdDoc = lastCdDocumento;

          if (itemsParams && itemsParams.length > 0) {
            const lastQs = new URLSearchParams(itemsParams[itemsParams.length - 1]);
            if (!effectiveCdProc) effectiveCdProc = lastQs.get("cdProcesso");
            if (!effectiveCdDoc) effectiveCdDoc = lastQs.get("cdDocumento");
          }

          // 2. Estágio: BULK_PREPARE
          const prepStart = performance.now();
          console.info("[Themis Bridge] [BULK_PREPARE] INÍCIO: POST /pastadigital/salvarDocumentoPreparado.do", {
            cdProcesso: effectiveCdProc,
            cdDocumento: effectiveCdDoc,
            itemsCount: itemsParams.length
          });

          const prepBody = new URLSearchParams();
          for (const p of itemsParams) {
            prepBody.append("itensPdfSelecionados", p);
          }
          prepBody.append("separarDocumentos", "true");
          if (effectiveCdProc) prepBody.append("cdProcesso", effectiveCdProc);
          if (effectiveCdDoc) prepBody.append("cdDocumento", String(effectiveCdDoc));

          const localizador = await new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();
            xhr.open("POST", "/pastadigital/salvarDocumentoPreparado.do", true);
            xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded; charset=UTF-8");
            xhr.setRequestHeader("X-Requested-With", "XMLHttpRequest");
            xhr.setRequestHeader("Accept", "*/*");
            xhr.onload = () => {
              const durationMs = Math.round(performance.now() - prepStart);
              if (xhr.status === 200) {
                const res = xhr.responseText.trim();
                if (res && !res.includes("<html")) {
                  console.info(`[Themis Bridge] [BULK_PREPARE] SUCESSO: HTTP ${xhr.status} (${durationMs}ms) Localizador: ${res}`);
                  resolve(res);
                } else {
                  const errMsg = "Resposta HTML inesperada ao salvar documento preparado: " + res.slice(0, 150);
                  console.error("[Themis Bridge] [BULK_PREPARE] ERRO:", {
                    stage: "BULK_PREPARE",
                    errorName: "InvalidPayload",
                    message: errMsg,
                    cause: null,
                    url: "/pastadigital/salvarDocumentoPreparado.do",
                    method: "POST"
                  });
                  reject(new Error(errMsg));
                }
              } else {
                const errMsg = `HTTP ${xhr.status} em salvarDocumentoPreparado.do: ` + xhr.responseText.slice(0, 150);
                console.error("[Themis Bridge] [BULK_PREPARE] ERRO:", {
                  stage: "BULK_PREPARE",
                  errorName: "HttpStatusError",
                  message: errMsg,
                  cause: null,
                  url: "/pastadigital/salvarDocumentoPreparado.do",
                  method: "POST"
                });
                reject(new Error(errMsg));
              }
            };
            xhr.onerror = () => {
              const errObj = {
                stage: "BULK_PREPARE",
                errorName: "NetworkError",
                message: "Erro de rede ao chamar salvarDocumentoPreparado.do",
                cause: null,
                url: "/pastadigital/salvarDocumentoPreparado.do",
                method: "POST"
              };
              console.error("[Themis Bridge] [BULK_PREPARE] ERRO:", errObj);
              reject(new Error(errObj.message));
            };
            xhr.send(prepBody.toString());
          });

          // 3. Estágio: BULK_POLL
          const pollBody = new URLSearchParams();
          pollBody.set("localizador", localizador);
          if (effectiveCdProc) pollBody.set("cdProcesso", effectiveCdProc);
          if (effectiveCdDoc) pollBody.set("cdDocumento", String(effectiveCdDoc));

          let rawDownloadUrl = null;
          const pollOverallStart = performance.now();

          const maxPollAttempts = 300;
          for (let attempt = 1; attempt <= maxPollAttempts; attempt++) {
            await new Promise((r) => setTimeout(r, 3000));
            const attemptStart = performance.now();

            const urlRes = await new Promise((resolve) => {
              const xhr = new XMLHttpRequest();
              xhr.open("POST", "/pastadigital/buscarDocumentoFinalizado.do", true);
              xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded; charset=UTF-8");
              xhr.setRequestHeader("X-Requested-With", "XMLHttpRequest");
              xhr.setRequestHeader("Accept", "*/*");
              xhr.onload = () => {
                if (xhr.status === 200) {
                  const text = xhr.responseText.trim();
                  // O e-SAJ pode retornar URL absoluta (https://...) ou relativa (/pastadigital/getPDFImpressao.do?...)
                  if (text && (text.startsWith("http") || text.includes("getPDFImpressao") || text.includes(".do") || text.includes("download"))) {
                    resolve(text);
                  } else {
                    resolve(null);
                  }
                } else {
                  resolve(null);
                }
              };
              xhr.onerror = () => resolve(null);
              xhr.send(pollBody.toString());
            });

            if (urlRes) {
              const totalPollMs = Math.round(performance.now() - pollOverallStart);
              console.info(`[Themis Bridge] [BULK_POLL] SUCESSO: Pacote pronto na tentativa ${attempt} (${totalPollMs}ms)`);
              rawDownloadUrl = urlRes;
              break;
            }
            window.postMessage({
              type: "THEMIS_BULK_DOWNLOAD_PROGRESS",
              requestId: requestId,
              attempt: attempt,
              maxAttempts: maxPollAttempts,
              itemCount: itemsParams.length,
              documentCount: selection.documentCount,
            }, "*");
          }

          if (!rawDownloadUrl) {
            const timeoutErr = {
              stage: "BULK_POLL",
              errorName: "TimeoutError",
              message: "Tempo limite de preparação do pacote excedido no TJSP (15 min).",
              cause: null,
              url: "/pastadigital/buscarDocumentoFinalizado.do",
              method: "POST"
            };
            console.error("[Themis Bridge] [BULK_POLL] ERRO:", timeoutErr);
            throw new Error(timeoutErr.message);
          }

          // Garante URL absoluta no mesmo origin do e-SAJ
          const absoluteDownloadUrl = new URL(rawDownloadUrl, window.location.origin).href;

          window.postMessage({
            type: "THEMIS_BULK_DOWNLOAD_RESPONSE",
            requestId: requestId,
            success: true,
            data: {
              downloadUrl: absoluteDownloadUrl,
              documentCount: selection.documentCount,
              itemCount: itemsParams.length,
            }
          }, "*");
        } catch (err) {
          console.error("[Themis Bridge MAIN] Erro no protocolo Bulk:", err);
          window.postMessage({
            type: "THEMIS_BULK_DOWNLOAD_RESPONSE",
            requestId: requestId,
            success: false,
            error: err.message
          }, "*");
        }
      })();
    }
  });

  // Trace de requisições de rede para mapeamento do fluxo oficial de Bulk Download
  window.__esaj_bulk_trace__ = window.__esaj_bulk_trace__ || [];

  function recordTrace(type, details) {
    const entry = {
      timestamp: new Date().toISOString(),
      type: type,
      ...details
    };
    window.__esaj_bulk_trace__.push(entry);
    console.log(`%c[e-SAJ Bulk Protocol] [${type}] ${details.method || ''} ${details.url || details.action || ''}`, 'color: #00bcd4; font-weight: bold;', details);
  }

  // Interceptar XMLHttpRequest
  const origXhrOpen = XMLHttpRequest.prototype.open;
  const origXhrSend = XMLHttpRequest.prototype.send;
  const origXhrSetRequestHeader = XMLHttpRequest.prototype.setRequestHeader;

  XMLHttpRequest.prototype.open = function(method, url, async, user, password) {
    this._bulk_method = method;
    this._bulk_url = url;
    this._bulk_headers = {};
    return origXhrOpen.apply(this, arguments);
  };

  XMLHttpRequest.prototype.setRequestHeader = function(header, value) {
    if (this._bulk_headers && header && header.toLowerCase() !== 'cookie') {
      this._bulk_headers[header] = value;
    }
    return origXhrSetRequestHeader.apply(this, arguments);
  };

  XMLHttpRequest.prototype.send = function(body) {
    const method = this._bulk_method;
    const url = this._bulk_url;
    const headers = this._bulk_headers;
    const startTime = performance.now();

    recordTrace('XHR_REQUEST', {
      method: method,
      url: url,
      headers: headers,
      body: typeof body === 'string' ? body : (body ? String(body) : null)
    });

    this.addEventListener('load', function() {
      const durationMs = Math.round(performance.now() - startTime);
      const ct = this.getResponseHeader('content-type') || '';
      const cd = this.getResponseHeader('content-disposition') || '';
      const cl = this.getResponseHeader('content-length') || '';
      
      let respBody = null;
      if (ct.includes('json') || ct.includes('text') || ct.includes('xml')) {
        respBody = (typeof this.responseText === 'string') ? this.responseText.slice(0, 1000) : null;
      }

      recordTrace('XHR_RESPONSE', {
        url: url,
        status: this.status,
        statusText: this.statusText,
        contentType: ct,
        contentDisposition: cd,
        contentLength: cl,
        durationMs: durationMs,
        responseSnippet: respBody
      });
    });

    return origXhrSend.apply(this, arguments);
  };

  // Interceptar Fetch
  const origFetch = window.fetch;
  window.fetch = async function(resource, init) {
    const url = (typeof resource === 'string') ? resource : (resource ? resource.url : '');
    const method = (init && init.method) ? init.method : 'GET';
    const startTime = performance.now();

    recordTrace('FETCH_REQUEST', {
      method: method,
      url: url,
      body: init && init.body ? (typeof init.body === 'string' ? init.body : String(init.body)) : null
    });

    try {
      const response = await origFetch.apply(this, arguments);
      const durationMs = Math.round(performance.now() - startTime);
      const ct = response.headers.get('content-type') || '';
      const cd = response.headers.get('content-disposition') || '';
      const cl = response.headers.get('content-length') || '';

      recordTrace('FETCH_RESPONSE', {
        url: url,
        status: response.status,
        statusText: response.statusText,
        contentType: ct,
        contentDisposition: cd,
        contentLength: cl,
        durationMs: durationMs
      });

      return response;
    } catch (err) {
      recordTrace('FETCH_ERROR', { url: url, error: err.message });
      throw err;
    }
  };

  // Interceptar Form Submits
  const origFormSubmit = HTMLFormElement.prototype.submit;
  HTMLFormElement.prototype.submit = function() {
    const formData = {};
    try {
      const inputs = this.querySelectorAll('input, select, textarea');
      inputs.forEach(inp => {
        if (inp.name) formData[inp.name] = inp.value;
      });
    } catch (e) {}

    recordTrace('FORM_SUBMIT', {
      action: this.action || window.location.href,
      method: (this.method || 'GET').toUpperCase(),
      fields: formData
    });

    return origFormSubmit.apply(this, arguments);
  };

  // Interceptar window.open
  const origWindowOpen = window.open;
  window.open = function(url, target, features) {
    recordTrace('WINDOW_OPEN', {
      url: url,
      target: target,
      features: features
    });
    return origWindowOpen.apply(this, arguments);
  };

  // Notifica que o script injetado está ativo com o trace habilitado
  console.log('%c[Themis Bridge] Tracer de Bulk Protocol ativo no contexto da página (observa tráfego e XHR/fetch nativos da página, não requisições isoladas de content scripts ou background workers). Registro em window.__esaj_bulk_trace__', 'color: #4caf50; font-weight: bold;');
  window.postMessage({ type: 'THEMIS_INJECTED_READY' }, '*');
})();
