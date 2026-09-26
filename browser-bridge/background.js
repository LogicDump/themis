/**
 * Themis Browser Bridge - Background Service Worker (Manifest V3)
 * Descoberta dinâmica de endpoint do Hermes Desktop via Native Messaging / Ledger.
 */

let cachedEndpoint = null;

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === "CHECK_STATUS") {
    handleCheckStatus(message.token)
      .then(sendResponse)
      .catch(err => sendResponse({ success: false, authenticated: false, error: err.message }));
    return true;
  }

  if (message.action === "DISCOVER_ENDPOINT") {
    getThemisEndpoint(true)
      .then(ep => sendResponse({ success: true, endpoint: ep }))
      .catch(err => sendResponse({ success: false, error: err.message }));
    return true;
  }

  if (message.action === "SYNC_PLAN") {
    handleSyncPlan(message.payload)
      .then(sendResponse)
      .catch(err => sendResponse({ success: false, error: err.message }));
    return true;
  }

  if (message.action === "SYNC_STATUS") {
    handleSyncStatus(message.cnj)
      .then(sendResponse)
      .catch(err => sendResponse({ success: false, error: err.message }));
    return true;
  }

  if (message.action === "INGEST_PDF") {
    handleIngestPdf(message.payload)
      .then(sendResponse)
      .catch(err => sendResponse({ success: false, error: err.message }));
    return true;
  }

  if (message.action === "GET_AUTH_TOKEN") {
    getThemisEndpoint()
      .then(ep => sendResponse({ success: true, token: ep.token }))
      .catch(err => sendResponse({ success: false, error: err.message }));
    return true;
  }

  if (message.action === "DOWNLOAD_AND_UPLOAD_ZIP") {
    handleDownloadAndUploadZip(message.cnj, message.downloadUrl, message.itemCount, sender.tab?.id)
      .then(sendResponse)
      .catch(err => sendResponse({ success: false, error: err.message }));
    return true;
  }

  if (message.action === "UPLOAD_ZIP") {
    handleUploadZip(message.cnj, message.arrayBuffer)
      .then(sendResponse)
      .catch(err => sendResponse({ success: false, error: err.message }));
    return true;
  }

  if (message.action === "SYNC_FINISH") {
    handleSyncFinish(message.payload)
      .then(sendResponse)
      .catch(err => sendResponse({ success: false, error: err.message }));
    return true;
  }
});

function sanitizeUrl(rawUrl) {
  if (!rawUrl || typeof rawUrl !== "string") return "";
  try {
    const parsed = new URL(rawUrl);
    const safeParams = new URLSearchParams();
    for (const [key, value] of parsed.searchParams.entries()) {
      const lowerKey = key.toLowerCase();
      if (["ticket", "token", "senha", "password", "auth", "session", "jwt", "credential", "bearer", "cookie"].some(s => lowerKey.includes(s))) {
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

/**
 * Descoberta do endpoint dinâmico do Hermes Desktop.
 * 1. Consulta Native Messaging Host (themis_browser_bridge -> spawn-ledger.json).
 * 2. Fallback para chrome.storage.local (cache ou configurado manualmente no popup).
 */
async function getThemisEndpoint(forceRefresh = false) {
  if (!forceRefresh && cachedEndpoint && cachedEndpoint.apiBase) {
    return cachedEndpoint;
  }

  // 1. Tentar Native Messaging Host
  try {
    const nativeResp = await new Promise((resolve) => {
      if (typeof chrome !== "undefined" && chrome.runtime && chrome.runtime.sendNativeMessage) {
        chrome.runtime.sendNativeMessage("themis_browser_bridge", { action: "GET_ENDPOINT" }, (resp) => {
          if (chrome.runtime.lastError) {
            console.warn("[Themis Bridge] Native Messaging discovery aviso:", chrome.runtime.lastError.message);
            return resolve(null);
          }
          resolve(resp);
        });
      } else {
        resolve(null);
      }
    });

    if (nativeResp && nativeResp.success && nativeResp.api_base) {
      cachedEndpoint = {
        apiBase: nativeResp.api_base,
        token: nativeResp.token || "",
        host: nativeResp.host || "127.0.0.1",
        port: nativeResp.port || null,
        pid: nativeResp.pid || null
      };
      if (nativeResp.token) {
        await chrome.storage.local.set({ "themis_pairing_token": nativeResp.token });
      }
      await chrome.storage.local.set({
        "themis_api_base": nativeResp.api_base,
        "themis_host": nativeResp.host,
        "themis_port": nativeResp.port
      });
      console.info(`[Themis Bridge] Endpoint dinâmico descoberto via Hermes Ledger: ${nativeResp.api_base} (PID ${nativeResp.pid})`);
      return cachedEndpoint;
    }
  } catch (err) {
    console.warn("[Themis Bridge] Erro ao consultar Native Messaging Host:", err.message);
  }

  // 2. Fallback: ler do storage local
  const stored = await new Promise((resolve) => {
    chrome.storage.local.get(["themis_api_base", "themis_pairing_token", "themis_port", "themis_host"], resolve);
  });

  if (stored && stored.themis_api_base) {
    cachedEndpoint = {
      apiBase: stored.themis_api_base,
      token: stored.themis_pairing_token || "",
      host: stored.themis_host || "127.0.0.1",
      port: stored.themis_port || null
    };
    return cachedEndpoint;
  }

  if (stored && stored.themis_port) {
    const host = stored.themis_host || "127.0.0.1";
    const apiBase = `http://${host}:${stored.themis_port}/api/plugins/themis/bridge`;
    cachedEndpoint = {
      apiBase: apiBase,
      token: stored.themis_pairing_token || "",
      host: host,
      port: stored.themis_port
    };
    return cachedEndpoint;
  }

  throw new Error("[THEMIS_DISCOVERY] Endpoint dinâmico do Hermes Desktop não encontrado. Verifique se o Hermes Desktop está em execução e o Themis Plugin ativo.");
}

/**
 * Utilitário fetch com retry automático em caso de porta alterada / reinício do Hermes.
 */
async function fetchThemis(subPath, options = {}) {
  let ep = await getThemisEndpoint(false);
  let url = `${ep.apiBase}${subPath}`;
  const authToken = options.tokenOverride || ep.token || (await chrome.storage.local.get(["themis_pairing_token"])).themis_pairing_token || "";

  const headers = Object.assign({}, options.headers || {});
  if (authToken && !headers["Authorization"] && !headers["authorization"]) {
    headers["Authorization"] = `Bearer ${authToken}`;
  }
  options.headers = headers;

  try {
    return await fetch(url, options);
  } catch (err) {
    console.warn(`[Themis Bridge] Falha de conexão em ${url}. Tentando redescobrir endpoint do Hermes...`);
    cachedEndpoint = null;
    ep = await getThemisEndpoint(true);
    url = `${ep.apiBase}${subPath}`;
    const freshToken = options.tokenOverride || ep.token || (await chrome.storage.local.get(["themis_pairing_token"])).themis_pairing_token || "";
    if (freshToken) {
      options.headers["Authorization"] = `Bearer ${freshToken}`;
    }
    return await fetch(url, options);
  }
}

async function handleCheckStatus(overrideToken) {
  try {
    const ep = await getThemisEndpoint(true);
    const token = overrideToken || ep.token;
    const headers = {};
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const resp = await fetchThemis("/status", {
      method: "GET",
      headers: headers,
      tokenOverride: token
    });

    if (resp.status === 200) {
      const data = await resp.json();
      return { success: true, authenticated: true, data: data, endpoint: ep };
    } else if (resp.status === 401) {
      return { success: true, authenticated: false, error: "Token não autorizado ou ausente", endpoint: ep };
    } else {
      return { success: false, authenticated: false, error: `HTTP ${resp.status}`, endpoint: ep };
    }
  } catch (err) {
    return { success: false, authenticated: false, error: `Servidor Themis/Hermes Offline (${err.message})` };
  }
}

function notifyZipDownloadProgress(tabId, cnj, downloadedBytes, totalBytes, itemCount) {
  if (!Number.isInteger(tabId)) return;
  chrome.tabs.sendMessage(tabId, {
    type: "THEMIS_ZIP_DOWNLOAD_PROGRESS",
    cnj,
    itemCount: Number(itemCount || 0),
    downloadedBytes,
    totalBytes: totalBytes || null,
  }, () => {
    // Read lastError to avoid an unchecked runtime.lastError when the e-SAJ tab closes.
    void chrome.runtime.lastError;
  });
}

async function handleDownloadAndUploadZip(cnj, downloadUrl, itemCount = 0, tabId = null) {
  const ep = await getThemisEndpoint(false);
  const authToken = ep.token || (await chrome.storage.local.get(["themis_pairing_token"])).themis_pairing_token;
  if (!authToken) {
    throw new Error("Token de emparelhamento do Themis não configurado na extensão.");
  }

  // 1. Estágio: BULK_DOWNLOAD (do e-SAJ)
  let targetUrl = downloadUrl;
  if (targetUrl && targetUrl.startsWith("/")) {
    targetUrl = `https://esaj.tjsp.jus.br${targetUrl}`;
  }
  const cleanUrl = sanitizeUrl(targetUrl);
  const dlStart = performance.now();
  console.info(`[Themis Background] [BULK_DOWNLOAD] INÍCIO: GET ${cleanUrl}`);

  let zipResp;
  try {
    zipResp = await fetch(targetUrl, {
      method: "GET",
      credentials: "include"
    });
  } catch (err) {
    const dlMs = Math.round(performance.now() - dlStart);
    console.error("[Themis Background] [BULK_DOWNLOAD] ERRO:", {
      stage: "BULK_DOWNLOAD",
      errorName: err.name || "Error",
      message: err.message,
      cause: err.cause || null,
      url: cleanUrl,
      method: "GET"
    });
    throw new Error(`[BULK_DOWNLOAD] Falha de rede no download do pacote ZIP pelo e-SAJ (${dlMs}ms): ${err.message}`);
  }

  if (!zipResp.ok) {
    console.error("[Themis Background] [BULK_DOWNLOAD] ERRO:", {
      stage: "BULK_DOWNLOAD",
      errorName: "HttpStatusError",
      message: `HTTP ${zipResp.status}`,
      cause: null,
      url: cleanUrl,
      method: "GET"
    });
    throw new Error(`[BULK_DOWNLOAD] Falha no download do pacote ZIP pelo e-SAJ: HTTP ${zipResp.status}`);
  }

  const contentType = zipResp.headers.get("content-type") || "";
  if (contentType.includes("html") || contentType.includes("text")) {
    console.error("[Themis Background] [BULK_DOWNLOAD] ERRO: Retornou página HTML em vez de ZIP", { contentType });
    throw new Error(`[BULK_DOWNLOAD] TJSP retornou página HTML de erro em vez do pacote ZIP: ${contentType}`);
  }

  const totalBytes = Number(zipResp.headers.get("content-length") || 0) || null;
  let downloadedBytes = 0;
  let lastProgressBytes = 0;
  let lastProgressAt = 0;
  const chunks = [];
  if (zipResp.body) {
    const reader = zipResp.body.getReader();
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      chunks.push(value);
      downloadedBytes += value.byteLength;
      const now = Date.now();
      if (downloadedBytes - lastProgressBytes >= 512 * 1024 || now - lastProgressAt >= 250) {
        notifyZipDownloadProgress(tabId, cnj, downloadedBytes, totalBytes, itemCount);
        lastProgressBytes = downloadedBytes;
        lastProgressAt = now;
      }
    }
  } else {
    const buffer = await zipResp.arrayBuffer();
    const bytes = new Uint8Array(buffer);
    chunks.push(bytes);
    downloadedBytes = bytes.byteLength;
  }
  if (downloadedBytes !== lastProgressBytes) {
    notifyZipDownloadProgress(tabId, cnj, downloadedBytes, totalBytes, itemCount);
  }
  const dlMs = Math.round(performance.now() - dlStart);
  const zipBlob = new Blob(chunks, { type: "application/zip" });
  const signature = new Uint8Array(await zipBlob.slice(0, 4).arrayBuffer());
  if (zipBlob.size < 4 || !(signature[0] === 0x50 && signature[1] === 0x4B)) {
    console.error("[Themis Background] [BULK_DOWNLOAD] ERRO: Assinatura PK ausente", { size: zipBlob.size });
    throw new Error(`[BULK_DOWNLOAD] Arquivo baixado do TJSP não é um ZIP válido (assinatura PK ausente, tamanho=${zipBlob.size} bytes).`);
  }

  console.info(`[Themis Background] [BULK_DOWNLOAD] SUCESSO: HTTP ${zipResp.status} (${dlMs}ms, ${zipBlob.size} bytes)`);

  // 2. Estágio: THEMIS_UPLOAD (ao backend dinâmico do Themis)
  const uploadStart = performance.now();
  console.info(`[Themis Background] [THEMIS_UPLOAD] INÍCIO: POST /sync/zip?cnj=${encodeURIComponent(cnj)} (${(zipBlob.size / (1024 * 1024)).toFixed(2)} MB)`);

  let resp;
  try {
    resp = await fetchThemis(`/sync/zip?cnj=${encodeURIComponent(cnj)}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/zip"
      },
      body: zipBlob
    });
  } catch (err) {
    const upMs = Math.round(performance.now() - uploadStart);
    console.error("[Themis Background] [THEMIS_UPLOAD] ERRO:", {
      stage: "THEMIS_UPLOAD",
      errorName: err.name || "Error",
      message: err.message,
      cause: err.cause || null,
      url: "/sync/zip",
      method: "POST"
    });
    throw new Error(`[THEMIS_UPLOAD] Falha de conexão ao enviar ZIP ao Themis (${upMs}ms): ${err.message}`);
  }

  const upMs = Math.round(performance.now() - uploadStart);
  const data = await resp.json().catch(() => ({}));
  if (resp.ok && (data.status === "success" || data.status === "ok")) {
    console.info(`[Themis Background] [THEMIS_UPLOAD] SUCESSO: HTTP ${resp.status} (${upMs}ms)`);
    return { success: true, data: data, size_bytes: zipBlob.size };
  } else {
    const errMsg = data.detail || data.message || `HTTP ${resp.status}`;
    console.error("[Themis Background] [THEMIS_UPLOAD] ERRO:", {
      stage: "THEMIS_UPLOAD",
      errorName: "ThemisError",
      message: errMsg,
      cause: null,
      url: "/sync/zip",
      method: "POST"
    });
    throw new Error(`[THEMIS_UPLOAD] Falha no processamento do ZIP pelo Themis: ${errMsg}`);
  }
}

async function handleUploadZip(cnj, arrayBuffer) {
  let body = arrayBuffer;
  if (arrayBuffer instanceof ArrayBuffer) {
    body = arrayBuffer;
  } else if (ArrayBuffer.isView(arrayBuffer)) {
    body = arrayBuffer.buffer;
  } else if (typeof arrayBuffer === "object" && arrayBuffer !== null) {
    if (arrayBuffer.buffer instanceof ArrayBuffer) {
      body = arrayBuffer.buffer;
    } else {
      const values = Object.values(arrayBuffer);
      body = new Uint8Array(values).buffer;
    }
  }

  const resp = await fetchThemis(`/sync/zip?cnj=${encodeURIComponent(cnj)}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/zip"
    },
    body: body
  });

  const data = await resp.json().catch(() => ({}));
  if (resp.ok && (data.status === "success" || data.status === "ok")) {
    return { success: true, data: data };
  } else {
    throw new Error(data.detail || data.message || `Falha no upload do ZIP: HTTP ${resp.status}`);
  }
}

async function handleSyncPlan(payload) {
  const startMs = performance.now();
  console.info("[Themis Background] [THEMIS_SYNC_PLAN] INÍCIO: POST /sync/plan");

  let resp;
  try {
    resp = await fetchThemis("/sync/plan", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    });
  } catch (err) {
    const durMs = Math.round(performance.now() - startMs);
    console.error("[Themis Background] [THEMIS_SYNC_PLAN] ERRO:", {
      stage: "THEMIS_SYNC_PLAN",
      errorName: err.name || "Error",
      message: err.message,
      cause: err.cause || null,
      url: "/sync/plan",
      method: "POST"
    });
    throw new Error(`[THEMIS_SYNC_PLAN] Falha de conexão ao Themis (${durMs}ms): ${err.message}`);
  }

  const durMs = Math.round(performance.now() - startMs);
  const data = await resp.json().catch(() => ({}));

  if (resp.ok && data.status === "ok") {
    console.info(`[Themis Background] [THEMIS_SYNC_PLAN] SUCESSO: HTTP ${resp.status} (${durMs}ms)`);
    return { success: true, data: data };
  } else {
    const errMsg = data.detail || data.message || `HTTP ${resp.status}`;
    console.error("[Themis Background] [THEMIS_SYNC_PLAN] ERRO:", {
      stage: "THEMIS_SYNC_PLAN",
      errorName: "ThemisError",
      message: errMsg,
      cause: null,
      url: "/sync/plan",
      method: "POST"
    });
    throw new Error(`[THEMIS_SYNC_PLAN] Falha no plano de sincronização: ${errMsg}`);
  }
}

async function handleSyncStatus(cnj) {
  const resp = await fetchThemis(`/sync/status?cnj=${encodeURIComponent(cnj)}`, { method: "GET" });
  const data = await resp.json().catch(() => ({}));
  if (resp.ok && data.status === "ok") return { success: true, data };
  throw new Error(data.detail || data.message || `Falha ao consultar progresso do sync: HTTP ${resp.status}`);
}

async function handleIngestPdf(payload) {
  const resp = await fetchThemis("/ingest", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  const data = await resp.json().catch(() => ({}));

  if (resp.ok && (data.status === "success" || data.ingested)) {
    return { success: true, data: data };
  } else {
    throw new Error(data.detail || data.message || `Falha na ingestão: HTTP ${resp.status}`);
  }
}

async function handleSyncFinish(payload) {
  const resp = await fetchThemis("/sync/finish", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  const data = await resp.json().catch(() => ({}));

  if (resp.ok && data.status === "ok") {
    return { success: true, data: data };
  } else {
    throw new Error(data.detail || data.message || `Falha na finalização dos Autos: HTTP ${resp.status}`);
  }
}
