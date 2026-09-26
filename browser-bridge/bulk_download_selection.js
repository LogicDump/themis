/*
 * Builds the exact native Pasta Digital bulk payload without touching the DOM.
 * The old Bridge protocol posts each provider-attested part as
 * `itensPdfSelecionados`; incremental sync merely narrows its input to NEW.
 */
(function (global) {
  "use strict";

  function selectedPartParameters(document) {
    const parts = Array.isArray(document.parts) ? document.parts : [];
    const partParameters = parts
      .map((part) => String(part && part.parametros || "").trim())
      .filter(Boolean);
    if (partParameters.length) return partParameters;

    const parameters = String(document.parametros || "").trim();
    if (!parameters) {
      throw new Error(`Peça NEW sem parâmetros nativos da Pasta Digital: ${document.cdDocumento || "(sem cdDocumento)"}.`);
    }
    return [parameters];
  }

  function prepareNativeBulkDownload(documents) {
    if (!Array.isArray(documents) || documents.length === 0) return null;

    const itemParameters = [];
    const seen = new Set();
    for (const document of documents) {
      for (const parameters of selectedPartParameters(document || {})) {
        if (!seen.has(parameters)) {
          seen.add(parameters);
          itemParameters.push(parameters);
        }
      }
    }
    if (!itemParameters.length) return null;

    const lastParameters = new URLSearchParams(itemParameters[itemParameters.length - 1]);
    return Object.freeze({
      documentCount: documents.length,
      itemParameters,
      lastCdDocumento: lastParameters.get("cdDocumento") || null,
    });
  }

  global.ThemisBulkDownloadSelection = Object.freeze({ prepareNativeBulkDownload });
})(globalThis);
