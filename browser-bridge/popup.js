document.addEventListener("DOMContentLoaded", async () => {
  const statusContainer = document.getElementById("status-container");
  const statusText = document.getElementById("status-text");
  const endpointDisplay = document.getElementById("endpoint-display");
  const tokenInput = document.getElementById("pairing-token");
  const saveBtn = document.getElementById("save-token-btn");
  const rediscoverBtn = document.getElementById("rediscover-btn");

  // Carregar token salvo
  chrome.storage.local.get(["themis_pairing_token", "themis_api_base", "themis_port", "themis_host"], (res) => {
    const currentToken = res ? res.themis_pairing_token || "" : "";
    if (currentToken) {
      tokenInput.value = currentToken;
    }
    if (res && res.themis_api_base) {
      endpointDisplay.textContent = `Endpoint: ${res.themis_api_base}`;
    }
    checkStatus(currentToken);
  });

  saveBtn.addEventListener("click", async () => {
    const val = tokenInput.value.trim();
    await chrome.storage.local.set({ "themis_pairing_token": val });
    checkStatus(val);
  });

  rediscoverBtn.addEventListener("click", () => {
    statusContainer.className = "status-box status-offline";
    statusText.textContent = "Descobrindo endpoint do Hermes...";
    endpointDisplay.textContent = "Endpoint: Consultando Ledger...";
    chrome.runtime.sendMessage({ action: "DISCOVER_ENDPOINT" }, (resp) => {
      if (resp && resp.success && resp.endpoint) {
        if (resp.endpoint.token && !tokenInput.value) {
          tokenInput.value = resp.endpoint.token;
        }
        endpointDisplay.textContent = `Endpoint: ${resp.endpoint.apiBase}`;
        checkStatus(tokenInput.value || resp.endpoint.token);
      } else {
        statusContainer.className = "status-box status-offline";
        statusText.textContent = `🔴 ${resp ? resp.error : "Falha no discovery"}`;
      }
    });
  });

  function checkStatus(token) {
    chrome.runtime.sendMessage({ action: "CHECK_STATUS", token: token }, (response) => {
      if (!response) {
        statusContainer.className = "status-box status-offline";
        statusText.textContent = "🔴 Service Worker Offline";
        return;
      }

      if (response.endpoint && response.endpoint.apiBase) {
        endpointDisplay.textContent = `Endpoint: ${response.endpoint.apiBase}`;
        if (response.endpoint.token && !tokenInput.value) {
          tokenInput.value = response.endpoint.token;
        }
      }

      if (response.success && response.authenticated) {
        statusContainer.className = "status-box status-online";
        const epInfo = response.endpoint ? `${response.endpoint.host}:${response.endpoint.port}` : "Ativo";
        statusText.textContent = `🟢 Conectado ao Themis (${epInfo})`;
      } else if (response.authenticated === false) {
        statusContainer.className = "status-box status-offline";
        statusText.textContent = "🟡 Token Inválido / Ausente";
      } else {
        statusContainer.className = "status-box status-offline";
        statusText.textContent = `🔴 Hermes Offline (${response.error || "Desconectado"})`;
      }
    });
  }
});
