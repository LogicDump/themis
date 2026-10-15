"use strict";
const { readFileSync } = require("node:fs");
const { join } = require("node:path");
const vm = require("node:vm");
const assert = require("node:assert/strict");
const { test } = require("node:test");

// Testa exatamente a funcao pura embarcada na UI, sem importar o SDK desktop.
const bundle = readFileSync(join(__dirname, "plugin.js"), "utf8");
const start = bundle.indexOf("function projectArchiveProcessTree(");
const end = bundle.indexOf("\nfunction ProcessosView(", start);
assert.ok(start > 0 && end > start, "projecao da arvore deve existir na UI");
const project = vm.runInNewContext(bundle.slice(start, end) + "\nprojectArchiveProcessTree", {}, { timeout: 1000 });
const ids = (rows) => Array.from(rows, (row) => row.process_id);
const row = (id, parent = null, materialized = true, depth = 0) => ({
  process_id: id, parent_process_id: parent, materialized, depth, label: id
});

test("arquivar unico descendente tira pai informativo dos ativos e leva contexto aos arquivados", () => {
  const tree = [row("0709", null, false), row("0833", "0709", true, 1), row("1000")];
  assert.deepEqual(ids(project(tree, ["0833"], false, "")), ["1000"]);
  const archived = project(tree, ["0833"], true, "");
  assert.deepEqual(ids(archived), ["0709", "0833"]);
  assert.equal(archived[0].contextOnly, true);
  assert.equal(archived[1].contextOnly, false);
});
test("pai informativo aparece em ambas visoes com filhos em estados distintos", () => {
  const tree = [row("pai", null, false), row("ativo", "pai", true, 1), row("arquivo", "pai", true, 1)];
  assert.deepEqual(ids(project(tree, ["arquivo"], false, "")), ["pai", "ativo"]);
  assert.deepEqual(ids(project(tree, ["arquivo"], true, "")), ["pai", "arquivo"]);
});

test("cadeia multinivel inclui somente ancestrais necessarios", () => {
  const tree = [row("avo", null, false), row("pai", "avo", false, 1),
    row("filho", "pai", true, 2), row("vazio", null, false)];
  assert.deepEqual(ids(project(tree, ["filho"], true, "")), ["avo", "pai", "filho"]);
  assert.deepEqual(ids(project(tree, ["filho"], false, "")), []);
});

test("busca por filho ou pai conserva hierarquia na visao correta", () => {
  const tree = [row("0709", null, false), row("0833", "0709", true, 1), row("outro")];
  assert.deepEqual(ids(project(tree, ["0833"], true, "0833")), ["0709", "0833"]);
  assert.deepEqual(ids(project(tree, ["0833"], true, "0709")), ["0709", "0833"]);
  assert.deepEqual(ids(project(tree, ["0833"], false, "0709")), []);
  assert.deepEqual(ids(project(tree, ["0833"], true, "inexistente")), []);
});

test("ancestral materializado de outro estado nao ganha acoes nessa visao", () => {
  const tree = [row("pai"), row("filho", "pai", true, 1)];
  const archived = project(tree, ["filho"], true, "");
  assert.deepEqual(ids(archived), ["pai", "filho"]);
  assert.equal(archived[0].contextOnly, true);
  assert.equal(archived[1].contextOnly, false);
});

test("ciclo anomalos nao travam a projecao", () => {
  const tree = [row("a", "b"), row("b", "a", false, 1)];
  assert.deepEqual(ids(project(tree, [], false, "")), ["a", "b"]);
});
