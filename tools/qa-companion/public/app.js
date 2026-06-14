"use strict";

// Client state. ITEMS is the flat list mirrored from the server; each item
// carries its owning file + group so edits can be POSTed straight back.
let ITEMS = [];
let STATUSES = [];
let REVIEWS = [];
let FEEDBACK_KINDS = [];
// Panel-level feedback, keyed by `file||group` (the area), not by test.
let AREA_FEEDBACK = {};
let activeId = null;
// "tests" (tree + card) or "feedback" (isolated panel-notes view).
let view = "tests";
const collapsed = {};
const fileFilter = new Set();
let saveTimer = null;

const FILE_LABEL = { "blender.md": "Blender", "photoshop.md": "Photoshop", "godot.md": "Godot", "flows.md": "Flows" };
const statusClass = (s) => (s === "n/a" ? "na" : s);
const byId = (id) => ITEMS.find((it) => it.id === id);
const esc = (s) => (s || "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);

// ---------- API ----------
async function api(path, body) {
  const opt = body ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) } : {};
  const r = await fetch(path, opt);
  if (!r.ok) throw new Error("HTTP " + r.status);
  return r.json();
}
function setMode(ok) {
  const c = document.getElementById("modeChip");
  c.className = ok ? "chip live" : "chip err";
  c.textContent = ok ? "writing to .md" : "save failed - retry";
}
function saveActive(immediate) {
  const it = byId(activeId);
  if (!it) return;
  const send = async () => {
    try {
      await api("/api/item", { file: it.file, group: it.group, item: it });
      setMode(true);
      renderProgress();
      renderTreeStatus(it.id);
    } catch (e) {
      setMode(false);
    }
  };
  clearTimeout(saveTimer);
  if (immediate) void send();
  else saveTimer = setTimeout(send, 400);
}

// ---------- panel feedback (area-scoped, keyed by file||group) ----------
// Feedback is deliberately isolated from the test cards: it is product feedback
// about a panel, not a test result, and lives in its own Feedback view + file.
const areaKeyOf = (a) => a.file + "||" + a.group;
const areaList = (a) => (AREA_FEEDBACK[areaKeyOf(a)] ??= []);
async function saveFeedback(a) {
  try {
    await api("/api/feedback", { file: a.file, group: a.group, feedback: areaList(a) });
    setMode(true);
  } catch (e) {
    setMode(false);
  }
}

// The distinct panels (areas), in checklist order, derived from the test list.
function areas() {
  const seen = new Map();
  ITEMS.forEach((it) => {
    const k = areaKeyOf(it);
    if (!seen.has(k)) seen.set(k, { key: k, file: it.file, group: it.group });
  });
  return [...seen.values()];
}

// ---------- view switching (Tests <-> Feedback) ----------
function setView(v, focusKey) {
  view = v;
  const tests = v === "tests";
  document.querySelector("aside").hidden = !tests;
  document.getElementById("card").hidden = !tests;
  document.getElementById("feedbackView").hidden = tests;
  document.getElementById("tabTests").classList.toggle("on", tests);
  document.getElementById("tabFeedback").classList.toggle("on", !tests);
  if (tests) {
    renderCard();
  } else {
    renderFeedbackView();
    if (focusKey) {
      const el = document.querySelector('.fb-panel[data-key="' + cssEsc(focusKey) + '"]');
      if (el) { el.scrollIntoView({ block: "start" }); el.querySelector("input")?.focus(); }
    }
  }
}

// ---------- render: isolated feedback view ----------
function renderFeedbackView() {
  const root = document.getElementById("feedbackView");
  const kindOpts = FEEDBACK_KINDS.map((k) => '<option value="' + esc(k) + '">' + esc(k) + "</option>").join("");
  let curFile = null;
  let h = '<div class="fb-intro">Panel feedback - product notes about a panel, not test results. Saved to <code>checklist/feedback.md</code> and normalized to the backlog later.</div>';
  areas().forEach((a) => {
    if (a.file !== curFile) { curFile = a.file; h += '<div class="fb-app-h">' + esc(FILE_LABEL[a.file] || a.file) + "</div>"; }
    const list = AREA_FEEDBACK[a.key] || [];
    h += '<div class="fb-panel" data-key="' + esc(a.key) + '">' +
      '<div class="fb-panel-h">' + esc(a.group) + (list.length ? ' <span class="fb-badge">&#9873; ' + list.length + "</span>" : "") + "</div>" +
      '<div class="feedback">' +
      list.map((f, i) => '<div class="fb-row"><span class="k ' + esc(f.kind) + '">' + esc(f.kind) + '</span><span class="txt" title="' + esc(f.text) + '">' + esc(f.text) + '</span><button class="fb-del" data-key="' + esc(a.key) + '" data-i="' + i + '" title="remove">&times;</button></div>').join("") +
      "</div>" +
      '<div class="fb-add"><select class="fb-kind">' + kindOpts + "</select>" +
      '<input type="text" class="fb-text" placeholder="observation about this panel (e.g. remove the redundant second search)" />' +
      '<button class="fb-submit" data-key="' + esc(a.key) + '">Add</button></div>' +
      "</div>";
  });
  root.innerHTML = h || '<div class="empty">No panels loaded.</div>';
}
function areaByKey(key) {
  const [file, group] = key.split("||");
  return { file, group };
}
function addAreaFeedback(panelEl, key) {
  const text = panelEl.querySelector(".fb-text").value.trim();
  if (!text) return;
  const kind = panelEl.querySelector(".fb-kind").value;
  const a = areaByKey(key);
  areaList(a).push({ kind, text });
  saveFeedback(a);
  renderFeedbackView();
  document.querySelector('.fb-panel[data-key="' + cssEsc(key) + '"] .fb-text')?.focus();
}
function delAreaFeedback(key, i) {
  const a = areaByKey(key);
  areaList(a).splice(i, 1);
  saveFeedback(a);
  renderFeedbackView();
}

// ---------- modal (window.prompt/confirm are blocked in the VS Code webview) ----------
let modalOk = null;
let modalCancel = null;
function openModal(title, bodyHtml) {
  return new Promise((resolve) => {
    const m = document.getElementById("modal");
    document.getElementById("modalTitle").textContent = title;
    document.getElementById("modalBody").innerHTML = bodyHtml;
    m.hidden = false;
    const first = document.getElementById("modalBody").querySelector("input,textarea,select");
    if (first) first.focus();
    modalOk = () => { m.hidden = true; resolve(true); };
    modalCancel = () => { m.hidden = true; resolve(false); };
  });
}
async function askText(title, label, value) {
  const ok = await openModal(title, '<label>' + esc(label) + '</label><input id="modalInput" type="text" value="' + esc(value || "") + '" />');
  return ok ? document.getElementById("modalInput").value : null;
}

// ---------- filtering ----------
function visible() {
  const q = document.getElementById("search").value.trim().toLowerCase();
  const sf = document.getElementById("statusFilter").value;
  const rf = document.getElementById("reviewFilter").value;
  return ITEMS.filter((it) => {
    if (!fileFilter.has(it.file)) return false;
    if (sf === "__done" && it.status === "pending") return false;
    if (sf === "__not-done" && it.status !== "pending") return false;
    if (sf && !sf.startsWith("__") && it.status !== sf) return false;
    if (rf && it.review !== rf) return false;
    const fb = (AREA_FEEDBACK[areaKeyOf(it)] || []).map((f) => f.kind + " " + f.text).join(" ");
    if (q && !(it.id + " " + it.title + " " + it.observe + " " + it.note + " " + fb).toLowerCase().includes(q)) return false;
    return true;
  });
}

// ---------- render: progress + tree ----------
function renderProgress() {
  const total = ITEMS.length;
  const counts = { pass: 0, fail: 0, blocked: 0, "n/a": 0, regressed: 0, pending: 0 };
  ITEMS.forEach((it) => counts[it.status]++);
  document.getElementById("progText").textContent = (total - counts.pending) + "/" + total;
  const order = ["pass", "fail", "blocked", "regressed", "n/a", "pending"];
  document.getElementById("bar").innerHTML = order
    .map((s) => {
      const w = total ? (counts[s] / total) * 100 : 0;
      return w ? '<i style="width:' + w.toFixed(2) + "%;background:var(--" + statusClass(s) + ')" title="' + s + ": " + counts[s] + '"></i>' : "";
    })
    .join("");
}

function renderTree() {
  const vis = visible();
  document.getElementById("countChip").textContent = vis.length + " shown";
  const tree = document.getElementById("tree");
  if (!vis.length) { tree.innerHTML = '<div class="empty">No items match.</div>'; return; }
  let html = "";
  let curFile = null;
  let curGroup = null;
  vis.forEach((it) => {
    if (it.file !== curFile) { curFile = it.file; curGroup = null; html += '<div class="app-h">' + esc(FILE_LABEL[it.file] || it.file) + "</div>"; }
    const groupKey = it.file + "||" + it.group;
    if (it.group !== curGroup) {
      curGroup = it.group;
      const fbCount = (AREA_FEEDBACK[groupKey] || []).length;
      html += '<div class="grp-h"><span class="group-name" data-grp="' + esc(groupKey) + '">' +
        (collapsed[groupKey] ? "&#9656;" : "&#9662;") + " " + esc(it.group || "(ungrouped)") + "</span>" +
        '<button class="fb-go" title="panel feedback (separate from tests)" data-fb-go="' + esc(groupKey) + '">&#9873;' + (fbCount ? " " + fbCount : "") + "</button>" +
        '<button class="add" title="add a test to this group" data-add="' + esc(groupKey) + '">+</button></div>';
    }
    if (collapsed[groupKey]) return;
    html += itemRow(it);
  });
  tree.innerHTML = html;
}
function itemRow(it) {
  return '<div class="it ' + (it.review === "drop" ? "drop " : "") + (it.id === activeId ? "active" : "") + '" data-id="' + esc(it.id) + '">' +
    '<span class="dot ' + statusClass(it.status) + '"></span>' +
    '<span class="rv ' + it.review + '"></span>' +
    '<span class="id">' + esc(it.id) + '</span><span class="t">' + esc(it.title) + "</span></div>";
}
// Cheap targeted refresh of one row's status dot without rebuilding the tree.
function renderTreeStatus(id) {
  const row = document.querySelector('.it[data-id="' + cssEsc(id) + '"]');
  const it = byId(id);
  if (!row || !it) { renderTree(); return; }
  row.className = "it " + (it.review === "drop" ? "drop " : "") + (id === activeId ? "active" : "");
  const dot = row.querySelector(".dot");
  if (dot) dot.className = "dot " + statusClass(it.status);
  const rv = row.querySelector(".rv");
  if (rv) rv.className = "rv " + it.review;
}
function cssEsc(s) { return s.replace(/["\\]/g, "\\$&"); }

// ---------- render: card ----------
function fieldInput(id, label, value, multiline) {
  const ctrl = multiline
    ? '<textarea id="' + id + '" data-f="' + id + '">' + esc(value) + "</textarea>"
    : '<input type="text" id="' + id + '" data-f="' + id + '" value="' + esc(value) + '" />';
  return '<div class="field' + (id === "observe" ? " observe" : "") + '"><div class="lab">' + label + "</div>" + ctrl + "</div>";
}

function renderCard() {
  const card = document.getElementById("card");
  const it = byId(activeId);
  if (!it) { card.innerHTML = '<div class="empty">Pick a test on the left.</div>'; return; }

  let h = '<div class="crumb"><span>' + esc(FILE_LABEL[it.file] || it.file) + " &rsaquo; " + esc(it.group) + '</span><span class="cid">' + esc(it.id) + "</span></div>";
  h += '<input type="text" id="title" data-f="title" value="' + esc(it.title) + '" />';

  h += '<div class="field"><div class="lab">status (o feature presta?)</div><div class="btns" id="statusBtns">' +
    STATUSES.map((s, i) => '<button class="sb ' + statusClass(s) + '" data-st="' + esc(s) + '" data-on="' + (it.status === s) + '">' + (i > 0 ? "<kbd>" + i + "</kbd> " : "") + esc(s) + "</button>").join("") + "</div></div>";
  h += '<div class="field"><div class="lab">review (o teste presta?)</div><div class="btns" id="reviewBtns">' +
    REVIEWS.map((r) => '<button class="sb ' + r + '" data-rv="' + esc(r) + '" data-on="' + (it.review === r) + '">' + esc(r) + "</button>").join("") + "</div></div>";

  h += fieldInput("pre", "pre", it.pre, false);
  h += fieldInput("steps", "steps (one per line)", it.steps.join("\n"), true);
  h += fieldInput("observe", "observe (what to see)", it.observe, true);
  h += fieldInput("intent", "intent (documented)", it.intent, true);
  h += fieldInput("code", "code", it.code, false);
  h += fieldInput("note", "note / observation", it.note, true);

  h += '<div class="field"><div class="lab">screenshots</div><div class="drop-zone" id="drop-zone">Paste (Ctrl/Cmd+V), drop an image, or click to pick</div><div class="shots" id="shots"></div></div>';

  h += '<div class="fb-hint">Feedback about this <b>panel</b> (not this test) lives in the <button class="text-link" id="toFeedback">Feedback tab</button>.</div>';

  h += '<div class="nav"><button id="prev">&larr; Prev</button><button id="nextPending">Next pending</button><button id="next">Next &rarr;</button>' +
    '<button class="danger" id="remove">Remove test</button></div>';
  h += '<div class="hint">Keys: <kbd>1</kbd>-<kbd>5</kbd> status, <kbd>0</kbd> pending, <kbd>n</kbd>/<kbd>p</kbd> next/prev. Edits autosave to the .md.</div>';
  card.innerHTML = h;

  card.querySelectorAll("[data-f]").forEach((el) => {
    el.addEventListener("input", () => {
      const f = el.dataset.f;
      if (f === "steps") it.steps = el.value.split("\n").map((s) => s.trim()).filter(Boolean);
      else it[f] = el.value;
      if (f === "title") renderTreeStatus(it.id), patchTitle(it);
      saveActive(false);
    });
  });
  card.querySelectorAll("#statusBtns .sb").forEach((b) => (b.onclick = () => { it.status = b.dataset.st; saveActive(true); refreshButtons("statusBtns", "st", it.status); }));
  card.querySelectorAll("#reviewBtns .sb").forEach((b) => (b.onclick = () => { it.review = b.dataset.rv; saveActive(true); refreshButtons("reviewBtns", "rv", it.review); renderTreeStatus(it.id); }));
  document.getElementById("prev").onclick = () => move(-1);
  document.getElementById("next").onclick = () => move(1);
  document.getElementById("nextPending").onclick = nextPending;
  document.getElementById("remove").onclick = () => removeActive();
  wireDrop(it);
  renderShots(it);
  document.getElementById("toFeedback").onclick = () => setView("feedback", areaKeyOf(it));
}
function patchTitle(it) {
  const row = document.querySelector('.it[data-id="' + cssEsc(it.id) + '"] .t');
  if (row) row.textContent = it.title;
}
function refreshButtons(containerId, attr, value) {
  document.querySelectorAll("#" + containerId + " .sb").forEach((b) => (b.dataset.on = String(b.dataset[attr === "st" ? "st" : "rv"] === value)));
}

function renderShots(it) {
  const wrap = document.getElementById("shots");
  if (!wrap) return;
  wrap.innerHTML = it.shots
    .map((p, i) => '<div class="shot"><a href="/' + esc(p) + '" target="_blank"><img src="/' + esc(p) + '" /></a><button data-shot="' + i + '" title="remove reference">&times;</button></div>')
    .join("");
  wrap.querySelectorAll("[data-shot]").forEach((b) => (b.onclick = () => { it.shots.splice(Number(b.dataset.shot), 1); saveActive(true); renderShots(it); }));
}
function wireDrop(it) {
  const dz = document.getElementById("drop-zone");
  const input = document.createElement("input");
  input.type = "file"; input.accept = "image/*"; input.style.display = "none";
  dz.appendChild(input);
  dz.onclick = () => input.click();
  input.onchange = () => { if (input.files[0]) addShot(it, input.files[0]); input.value = ""; };
  dz.ondragover = (e) => { e.preventDefault(); dz.classList.add("hot"); };
  dz.ondragleave = () => dz.classList.remove("hot");
  dz.ondrop = (e) => { e.preventDefault(); dz.classList.remove("hot"); const f = [...e.dataTransfer.files].find((x) => x.type.startsWith("image/")); if (f) addShot(it, f); };
}
async function addShot(it, file) {
  try {
    const dataUrl = await new Promise((res) => { const fr = new FileReader(); fr.onload = () => res(fr.result); fr.readAsDataURL(file); });
    const r = await api("/api/screenshot", { id: it.id, dataUrl });
    if (r.ok) { it.shots.push(r.path); saveActive(true); renderShots(it); }
  } catch (e) { setMode(false); }
}

// ---------- actions ----------
function selectItem(id) { activeId = id; renderTree(); renderCard(); document.getElementById("card").scrollTop = 0; }
function move(d) {
  const vis = visible(); if (!vis.length) return;
  let i = vis.findIndex((it) => it.id === activeId);
  i = Math.min(vis.length - 1, Math.max(0, (i < 0 ? 0 : i) + d));
  selectItem(vis[i].id);
}
function nextPending() {
  const vis = visible(); const start = vis.findIndex((it) => it.id === activeId);
  for (let k = 1; k <= vis.length; k++) { const it = vis[(start + k + vis.length) % vis.length]; if (it.status === "pending") { selectItem(it.id); return; } }
}
async function addTest(groupKey) {
  const [file, group] = groupKey.split("||");
  const title = await askText("Add test to " + group, "New test title", "");
  if (title === null || !title.trim()) return;
  try {
    const r = await api("/api/item", { file, group, item: { id: "", title } });
    if (r.ok && r.item) { ITEMS.push({ ...r.item, file, group }); renderTree(); selectItem(r.item.id); }
  } catch (e) { setMode(false); }
}
async function removeActive() {
  const it = byId(activeId); if (!it) return;
  const reason = await askText("Remove " + it.id, "Reason (archived to removed.md)", it.reason || "");
  if (reason === null) return;
  try {
    const r = await api("/api/remove", { id: it.id, reason });
    if (r.ok) {
      const vis = visible(); const idx = vis.findIndex((x) => x.id === it.id);
      ITEMS = ITEMS.filter((x) => x.id !== it.id);
      const nextId = vis[idx + 1]?.id || vis[idx - 1]?.id || (ITEMS[0] && ITEMS[0].id) || null;
      renderProgress(); activeId = nextId; renderTree(); renderCard();
    }
  } catch (e) { setMode(false); }
}

// ---------- wiring ----------
function buildFileFilters() {
  const wrap = document.getElementById("appFilters");
  const files = [...new Set(ITEMS.map((it) => it.file))];
  files.forEach((f) => fileFilter.add(f));
  wrap.innerHTML = files
    .map((f) => '<label style="display:flex;gap:3px;align-items:center;font-size:11px"><input type="checkbox" data-file="' + esc(f) + '" checked/> ' + esc(FILE_LABEL[f] || f) + "</label>")
    .join("");
  wrap.querySelectorAll("input").forEach((cb) => (cb.onchange = () => { cb.checked ? fileFilter.add(cb.dataset.file) : fileFilter.delete(cb.dataset.file); renderTree(); }));
}
function buildReviewFilter() {
  const sel = document.getElementById("reviewFilter");
  REVIEWS.forEach((r) => { const o = document.createElement("option"); o.value = r; o.textContent = "review: " + r; sel.appendChild(o); });
}
document.getElementById("tree").addEventListener("click", (e) => {
  const go = e.target.closest("[data-fb-go]"); if (go) { setView("feedback", go.dataset.fbGo); return; }
  const add = e.target.closest("[data-add]"); if (add) { addTest(add.dataset.add); return; }
  const g = e.target.closest("[data-grp]"); if (g) { collapsed[g.dataset.grp] = !collapsed[g.dataset.grp]; renderTree(); return; }
  const it = e.target.closest(".it"); if (it) selectItem(it.dataset.id);
});
document.getElementById("tabTests").onclick = () => setView("tests");
document.getElementById("tabFeedback").onclick = () => setView("feedback");
document.getElementById("feedbackView").addEventListener("click", (e) => {
  const del = e.target.closest(".fb-del"); if (del) { delAreaFeedback(del.dataset.key, Number(del.dataset.i)); return; }
  const add = e.target.closest(".fb-submit"); if (add) { addAreaFeedback(add.closest(".fb-panel"), add.dataset.key); }
});
document.getElementById("feedbackView").addEventListener("keydown", (e) => {
  if (e.key !== "Enter" || !e.target.classList.contains("fb-text")) return;
  e.preventDefault();
  const panel = e.target.closest(".fb-panel");
  addAreaFeedback(panel, panel.dataset.key);
});
document.getElementById("search").oninput = renderTree;
document.getElementById("statusFilter").onchange = renderTree;
document.getElementById("reviewFilter").onchange = renderTree;
document.getElementById("modalOk").onclick = () => modalOk && modalOk();
document.getElementById("modalCancel").onclick = () => modalCancel && modalCancel();
document.getElementById("modal").addEventListener("keydown", (e) => {
  if (e.key === "Enter") { e.preventDefault(); if (modalOk) modalOk(); }
  else if (e.key === "Escape") { e.preventDefault(); if (modalCancel) modalCancel(); }
});
document.addEventListener("keydown", (e) => {
  if (view !== "tests") return;
  if (["INPUT", "TEXTAREA"].includes(document.activeElement.tagName)) return;
  const it = byId(activeId); if (!it) return;
  if (e.key >= "1" && e.key <= "5") { it.status = STATUSES[+e.key]; saveActive(true); renderCard(); }
  else if (e.key === "0") { it.status = "pending"; saveActive(true); renderCard(); }
  else if (e.key === "n") move(1);
  else if (e.key === "p") move(-1);
});
document.addEventListener("paste", (e) => {
  if (view !== "tests") return;
  const it = byId(activeId); if (!it) return;
  const img = [...(e.clipboardData?.items || [])].find((i) => i.type.startsWith("image/"));
  if (img) { const f = img.getAsFile(); if (f) { e.preventDefault(); addShot(it, f); } }
});

async function init() {
  try {
    const state = await api("/api/state");
    ITEMS = state.items; STATUSES = state.statuses; REVIEWS = state.reviews; FEEDBACK_KINDS = state.feedbackKinds || [];
    AREA_FEEDBACK = state.feedback || {};
    buildFileFilters(); buildReviewFilter();
    renderProgress(); renderTree();
    const vis = visible(); if (vis.length) activeId = vis[0].id;
    renderCard();
  } catch (e) {
    document.getElementById("card").innerHTML = '<div class="empty">Failed to load. Is the server running? (pnpm walk)</div>';
  }
}
init();
