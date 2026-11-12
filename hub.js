// The hub's one script, written by hand. Without it, every page still lists
// everything; this file adds the "what's new" windows on the home page, and the filters and search on the library.
(() => {
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const daysSince = (d) => (d ? (Date.now() - new Date(d + 'T00:00:00').getTime()) / 864e5 : Infinity);
  const press = (buttons, on) => buttons.forEach((b) => b.setAttribute('aria-pressed', String(b === on)));

  // Home: what changed in the last 7 or 30 days, or the latest rows.
  const wn = $('#whatsnew');
  if (wn) {
    const rows = $$('.list li', wn), buttons = $$('.controls button', wn);
    const show = (btn) => {
      const days = Number(btn.dataset.days);
      let n = 0;
      rows.forEach((li, i) => { const on = days ? daysSince(li.dataset.updated) <= days : i < 15; li.hidden = !on; n += on; });
      $('.empty', wn).hidden = n > 0;
      press(buttons, btn);
    };
    $('.controls', wn).hidden = false;
    buttons.forEach((b) => b.addEventListener('click', () => show(b)));
    // Open on the narrowest window that has something in it.
    show(buttons.find((b) => { const d = Number(b.dataset.days); return !d || rows.some((li) => daysSince(li.dataset.updated) <= d); }));
  }

  // Library: type and age filters, a sort, and search. The state lives in the URL.
  const list = $('#library');
  if (!list) return;
  const rows = $$('li', list), q = $('#q'), age = $('#age'), sort = $('#sort'), chips = $$('#types button');
  const params = new URLSearchParams(location.search);
  const state = { q: params.get('q') || '', type: params.get('type') || '', age: params.get('age') || '', sort: params.get('sort') || 'updated' };
  if (!chips.some((b) => b.dataset.type === state.type)) state.type = '';
  if (![...age.options].some((o) => o.value === state.age)) state.age = '';
  if (![...sort.options].some((o) => o.value === state.sort)) state.sort = 'updated';
  const hay = new Map(rows.map((li) => [li, (li.textContent + ' ' + li.dataset.path).toLowerCase()]));
  let index = null, loading = null;
  const fullText = () => loading || (loading = fetch('search-index.json').then((r) => r.json())
    .then((a) => { index = new Map(a.map((e) => [e.p, e.t])); apply(); }).catch(() => { index = new Map(); }));

  function apply() {
    const words = state.q.toLowerCase().split(/\s+/).filter(Boolean);
    if (words.length && !index) fullText();
    let n = 0;
    for (const li of rows) {
      const hit = $('.hit', li);
      hit.hidden = true;
      let on = (!state.type || li.dataset.type === state.type) && (!state.age || daysSince(li.dataset.updated) <= Number(state.age));
      if (on && words.length) {
        const meta = hay.get(li), text = (index && index.get(li.dataset.path)) || '';
        on = words.every((w) => meta.includes(w) || text.includes(w));
        const deep = on && words.find((w) => !meta.includes(w));
        if (deep) {
          const at = text.indexOf(deep), from = Math.max(0, at - 70);
          hit.textContent = (from ? '… ' : '') + text.slice(from, at + deep.length + 90) + ' …';
          hit.hidden = false;
        }
      }
      li.hidden = !on;
      n += on;
    }
    const key = { updated: (li) => li.dataset.updated, added: (li) => li.dataset.added, title: (li) => $('.title', li).textContent.toLowerCase() }[state.sort];
    const dir = state.sort === 'title' ? 1 : -1;
    [...rows].sort((a, b) => (key(a) < key(b) ? -dir : key(a) > key(b) ? dir : 0)).forEach((li) => list.appendChild(li));
    $('#count').textContent = n + ' of ' + rows.length;
    $('.empty').hidden = n > 0;
    press(chips, chips.find((b) => b.dataset.type === state.type));
    const out = new URLSearchParams();
    for (const [k, v] of Object.entries(state)) if (v && !(k === 'sort' && v === 'updated')) out.set(k, v);
    history.replaceState(null, '', out.toString() ? '?' + out : location.pathname);
  }

  q.value = state.q; age.value = state.age; sort.value = state.sort;
  q.addEventListener('input', () => { state.q = q.value.trim(); apply(); });
  age.addEventListener('change', () => { state.age = age.value; apply(); });
  sort.addEventListener('change', () => { state.sort = sort.value; apply(); });
  chips.forEach((b) => b.addEventListener('click', () => { state.type = b.dataset.type; apply(); }));
  apply();
})();
