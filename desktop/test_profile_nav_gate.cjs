// Profile-scoped Themis frontend smoke test against the packaged plugin registration.
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, 'plugin.js'), 'utf8');
const start = source.lastIndexOf('var plugin_default = {');
const end = source.indexOf('//#endregion', start);
assert(start > 0 && end > start);
const listeners = new Set();
let profile = 'default';
const state = { get: () => profile, subscribe(fn) { listeners.add(fn); fn(profile); return () => listeners.delete(fn); } };
const host = { state: { profile: { get: () => 'default', subscribe() { throw new Error('wrong socket profile atom'); } }, focusedSessionProfile: state } };
const active = new Set();
const calls = [];
const disposeCallbacks = [];
const ctx = {
  registerMany(items) {
    assert.equal(items.length, 3);
    for (const item of items) { assert(!active.has(item.id)); active.add(item.id); }
    calls.push(items.map(x => x.id));
    let gone = false;
    return () => { if (gone) return; gone = true; for (const item of items) active.delete(item.id); };
  },
  onDispose(fn) { disposeCallbacks.push(fn); }
};
const code = source.slice(start, end) + '\nplugin_default;';
const plugin = vm.runInNewContext(code, {
  host, installThemisBundledFonts: () => {}, ROUTES_AREA: 'routes',
  SIDEBAR_NAV_AREA: 'sidebar.nav', THEMES_AREA: 'themes',
  jsx: () => null, ThemisShell() {}, themisTheme: {}
});
plugin.register(ctx);
assert.deepEqual([...active], []);
function select(value, expected) {
  profile = value;
  for (const fn of listeners) fn(value);
  assert.deepEqual([...active].sort(), expected.slice().sort(), value);
}
const all = ['page', 'nav', 'theme'];
select('themis', all);
select('themis', all);
assert.equal(calls.length, 1, 'duplicated on unchanged profile');
select('daedalus', []);
select('default', []);
select('themis', all);
assert.equal(calls.length, 2);
for (const fn of disposeCallbacks) fn();
assert.equal(listeners.size, 0);
assert.deepEqual([...active], []);
console.log('PROFILE_NAV_GATE_PASS 7 assertions + no duplicate registration');
