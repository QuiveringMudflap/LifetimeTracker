/* ============================================================
   ProspectDialer — cold-call CRM (vanilla JS, localStorage)
   ============================================================ */
(function () {
  "use strict";

  const LS_KEY = "prospectdialer.v1";
  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => Array.from(document.querySelectorAll(sel));

  /* ---------- Default state ---------- */
  const DEFAULT_CATEGORIES = [
    { id: "voicemail", name: "Voicemail", color: "#f5a623" },
    { id: "accepted", name: "Accepted", color: "#23b26d" },
    { id: "pickedup", name: "Picked Up", color: "#4f8cff" },
    { id: "callback", name: "Callback", color: "#9b6bff" },
    { id: "notinterested", name: "Not Interested", color: "#e5484d" },
    { id: "noanswer", name: "No Answer", color: "#94a3b8" },
    { id: "wrongnumber", name: "Wrong Number", color: "#64748b" },
  ];

  let state = load();
  let selectedId = null;
  let timer = { t0: 0, handle: null };
  let callActive = false;

  /* ---------- Persistence ---------- */
  function load() {
    try {
      const raw = localStorage.getItem(LS_KEY);
      if (raw) {
        const s = JSON.parse(raw);
        if (!s.categories || !s.categories.length) s.categories = clone(DEFAULT_CATEGORIES);
        if (!s.leads) s.leads = [];
        if (!s.batches) s.batches = [];
        if (!s.settings) s.settings = defaultSettings();
        if (typeof s.totalTalkSeconds !== "number") s.totalTalkSeconds = 0;
        // migrate: give any pre-batch leads a legacy batch
        const orphan = s.leads.filter(l => !l.batchId);
        if (orphan.length) {
          const b = { id: "legacy", name: "Legacy Leads", createdAt: Date.now(), count: orphan.length };
          s.batches.unshift(b);
          orphan.forEach(l => l.batchId = "legacy");
        }
        // UI prefs
        if (!s.ui) s.ui = { activeBatch: "", hideWithWebsite: true };
        if (typeof s.ui.hideWithWebsite !== "boolean") s.ui.hideWithWebsite = true;
        return s;
      }
    } catch (e) { console.warn("load failed", e); }
    return { leads: [], batches: [], categories: clone(DEFAULT_CATEGORIES), settings: defaultSettings(), totalTalkSeconds: 0, ui: { activeBatch: "", hideWithWebsite: true } };
  }
  function defaultSettings() {
    return { callMode: "click", twilioTokenUrl: "", twilioCallerId: "" };
  }
  function save() {
    try { localStorage.setItem(LS_KEY, JSON.stringify(state)); }
    catch (e) { toast("⚠ Could not save (storage full?)"); }
  }
  function clone(x) { return JSON.parse(JSON.stringify(x)); }
  function uid() { return Date.now().toString(36) + Math.random().toString(36).slice(2, 7); }

  /* ---------- Phone helpers ---------- */
  function cleanPhone(raw) {
    if (!raw) return "";
    let p = String(raw).trim();
    const hasPlus = p.startsWith("+");
    p = p.replace(/[^\d]/g, "");
    return (hasPlus ? "+" : "") + p;
  }
  function prettyPhone(raw) {
    const p = cleanPhone(raw);
    const d = p.replace(/^\+/, "");
    if (d.length === 10) return `+1 ${d.slice(0,3)} ${d.slice(3,6)} ${d.slice(6)}`;
    if (d.length === 11 && d[0] === "1") return `+1 ${d.slice(1,4)} ${d.slice(4,7)} ${d.slice(7)}`;
    if (p.startsWith("+")) return p.replace(/(\+\d{1,3})(\d{3})(\d{3})(\d+)/, "$1 $2 $3 $4");
    return p || "—";
  }

  /* ============================================================
     RENDERING
     ============================================================ */
  function catById(id) { return state.categories.find(c => c.id === id); }

  function renderCategoryPicker() {
    const box = $("#categoryPicker");
    const lead = getSelected();
    box.innerHTML = "";
    state.categories.forEach(c => {
      const chip = document.createElement("button");
      chip.className = "cat-chip" + (lead && lead.category === c.id ? " selected" : "");
      chip.innerHTML = `<span class="dot" style="background:${c.color}"></span>${escapeHtml(c.name)}`;
      if (lead && lead.category === c.id) { chip.style.background = c.color; chip.style.borderColor = c.color; }
      chip.onclick = () => {
        if (!lead) { toast("Select a lead first"); return; }
        lead.category = (lead.category === c.id) ? null : c.id;
        lead.updatedAt = Date.now();
        save(); renderCategoryPicker(); renderList(); renderStats();
      };
      box.appendChild(chip);
    });
  }

  function renderFilterOptions() {
    const sel = $("#filterCategory");
    const cur = sel.value;
    sel.innerHTML = '<option value="">All categories</option><option value="__none">Uncategorized</option>';
    state.categories.forEach(c => {
      const o = document.createElement("option");
      o.value = c.id; o.textContent = c.name;
      sel.appendChild(o);
    });
    sel.value = cur;
  }

  function filteredLeads() {
    const q = $("#search").value.trim().toLowerCase();
    const f = $("#filterCategory").value;
    const activeBatch = state.ui.activeBatch;
    const hideWithWebsite = state.ui.hideWithWebsite;
    return state.leads.filter(l => {
      if (activeBatch && l.batchId !== activeBatch) return false;
      if (hideWithWebsite && l.website) return false;
      if (f === "__none" && l.category) return false;
      if (f && f !== "__none" && l.category !== f) return false;
      if (q) {
        const hay = `${l.name} ${l.company} ${l.phone} ${l.title} ${l.email}`.toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    });
  }

  function renderList() {
    const list = $("#leadList");
    const leads = filteredLeads();
    $("#listEmpty").hidden = state.leads.length !== 0;
    list.innerHTML = "";
    leads.forEach(l => {
      const cat = l.category ? catById(l.category) : null;
      const row = document.createElement("div");
      row.className = "lead-row" + (l.id === selectedId ? " active" : "");
      row.onclick = () => selectLead(l.id);
      const badge = cat
        ? `<span class="lead-badge" style="background:${cat.color}">${escapeHtml(cat.name)}</span>`
        : `<span class="lead-badge none">New</span>`;
      row.innerHTML = `
        <div class="lead-main">
          <div class="lead-name">${escapeHtml(l.name || l.company || prettyPhone(l.phone))}</div>
          <div class="lead-meta">${escapeHtml(l.company ? l.company + " · " : "")}${prettyPhone(l.phone)}</div>
        </div>
        ${badge}
        <button class="lead-call-mini" title="Call">📞</button>`;
      row.querySelector(".lead-call-mini").onclick = (e) => { e.stopPropagation(); selectLead(l.id); startCall(); };
      list.appendChild(row);
    });
    renderCounts();
  }

  function renderCounts() {
    const box = $("#listCounts");
    box.innerHTML = "";
    const counts = {};
    state.leads.forEach(l => { const k = l.category || "__none"; counts[k] = (counts[k] || 0) + 1; });
    state.categories.forEach(c => {
      if (counts[c.id]) {
        const pill = document.createElement("span");
        pill.className = "count-pill"; pill.style.background = c.color;
        pill.textContent = `${c.name} ${counts[c.id]}`;
        box.appendChild(pill);
      }
    });
    if (counts.__none) {
      const pill = document.createElement("span");
      pill.className = "count-pill"; pill.style.background = "#94a3b8";
      pill.textContent = `New ${counts.__none}`;
      box.appendChild(pill);
    }
  }

  function renderStats() {
    const dialed = state.leads.filter(l => l.dialed).length;
    const connected = state.leads.filter(l => l.category && ["accepted","pickedup"].includes(l.category)).length;
    const accepted = state.leads.filter(l => l.category === "accepted").length;
    $("#statQueued").textContent = state.leads.filter(l => !l.dialed).length;
    $("#statDialed").textContent = dialed;
    $("#statConnected").textContent = connected;
    $("#statAccepted").textContent = accepted;
    $("#statTalk").textContent = fmtShort(state.totalTalkSeconds);
  }

  function renderPhone() {
    const lead = getSelected();
    $("#phoneLeadName").textContent = lead ? (lead.name || lead.company || "—") : "No lead selected";
    $("#phoneLeadCompany").textContent = lead ? (lead.company || lead.title || "") : "—";
    $("#phoneNumber").textContent = lead ? prettyPhone(lead.phone) : "+1 000 000 0000";
    $("#outcomeLead").textContent = lead ? (lead.name || lead.company || prettyPhone(lead.phone)) : "Select a lead to begin";
    $("#leadNotes").value = lead ? (lead.notes || "") : "";
    $("#phoneMode").textContent = state.settings.callMode === "twilio" ? "Twilio Web Dialer" : "Click-to-Call";
  }

  function renderBatches() {
    const bar = $("#batchBar");
    if (!bar) return;
    bar.innerHTML = "";
    // "All" chip
    const all = document.createElement("button");
    all.className = "batch-chip" + (!state.ui.activeBatch ? " selected" : "");
    all.innerHTML = `<span>All batches</span><small>${state.leads.length}</small>`;
    all.onclick = () => { state.ui.activeBatch = ""; save(); renderBatches(); renderList(); };
    bar.appendChild(all);
    // Each batch
    state.batches.forEach(b => {
      const count = state.leads.filter(l => l.batchId === b.id).length;
      const chip = document.createElement("button");
      chip.className = "batch-chip" + (state.ui.activeBatch === b.id ? " selected" : "");
      chip.innerHTML = `<span>${escapeHtml(b.name)}</span><small>${count}</small><span class="batch-x" title="Batch options">⋯</span>`;
      chip.querySelector("span:first-child").onclick = () => {
        state.ui.activeBatch = b.id; save(); renderBatches(); renderList();
      };
      chip.onclick = (e) => {
        if (e.target.classList.contains("batch-x")) { openBatchMenu(b, e); return; }
        state.ui.activeBatch = b.id; save(); renderBatches(); renderList();
      };
      bar.appendChild(chip);
    });
    // "Hide has-website" toggle
    const cb = $("#hideWithWebsite");
    if (cb) cb.checked = state.ui.hideWithWebsite;
  }

  function openBatchMenu(batch, ev) {
    ev.stopPropagation();
    const choice = prompt(
      `Batch: ${batch.name}\n\n` +
      `Type a number:\n` +
      `  1 — Rename\n` +
      `  2 — Reset call progress (keep leads, clear dialed/category)\n` +
      `  3 — Delete this batch (removes its leads permanently)\n` +
      `  4 — Cancel`, "4");
    if (!choice || choice === "4") return;
    if (choice === "1") {
      const name = prompt("New name for this batch:", batch.name);
      if (name && name.trim()) { batch.name = name.trim(); save(); renderAll(); }
    } else if (choice === "2") {
      if (!confirm(`Reset call progress for "${batch.name}"? Leads stay, but dialed/category tags are cleared.`)) return;
      resetCallProgress(l => l.batchId === batch.id);
      toast(`Reset "${batch.name}"`);
    } else if (choice === "3") {
      if (!confirm(`DELETE batch "${batch.name}" and all ${state.leads.filter(l=>l.batchId===batch.id).length} of its leads? This cannot be undone.`)) return;
      state.leads = state.leads.filter(l => l.batchId !== batch.id);
      state.batches = state.batches.filter(b => b.id !== batch.id);
      if (state.ui.activeBatch === batch.id) state.ui.activeBatch = "";
      save(); renderAll();
      toast(`Deleted "${batch.name}"`);
    }
  }

  function resetCallProgress(matchFn) {
    state.leads.forEach(l => {
      if (matchFn(l)) {
        l.dialed = false;
        l.dialedAt = null;
        l.dialCount = 0;
        l.category = null;
        l.lastCallSeconds = 0;
      }
    });
    save(); renderAll();
  }

  function renderAll() {
    renderFilterOptions();
    renderBatches();
    renderList();
    renderStats();
    renderPhone();
    renderCategoryPicker();
  }

  /* ============================================================
     SELECTION & CALLING
     ============================================================ */
  function getSelected() { return state.leads.find(l => l.id === selectedId) || null; }

  function selectLead(id) {
    // save notes of previous selection
    persistNotes();
    selectedId = id;
    renderPhone(); renderCategoryPicker(); renderList();
  }

  function persistNotes() {
    const lead = getSelected();
    if (lead) { lead.notes = $("#leadNotes").value; }
  }

  function startCall() {
    const lead = getSelected();
    if (!lead) { toast("Select a lead first"); return; }
    lead.dialed = true;
    lead.dialedAt = Date.now();
    lead.dialCount = (lead.dialCount || 0) + 1;
    callActive = true;
    $("#btnCall").disabled = true;
    $("#btnHangup").disabled = false;
    $("#callStatus").textContent = "On Call";
    $("#callStatus").classList.add("live");
    startTimer();

    if (state.settings.callMode === "twilio" && state.settings.twilioTokenUrl) {
      startTwilioCall(lead);
    } else {
      // Click-to-call: open the system dialer.
      window.location.href = "tel:" + cleanPhone(lead.phone);
    }
    save(); renderStats(); renderList();
  }

  function endCall() {
    if (!callActive) return;
    callActive = false;
    const secs = stopTimer();
    state.totalTalkSeconds += secs;
    const lead = getSelected();
    if (lead) lead.lastCallSeconds = secs;
    if (twilioConn) { try { twilioConn.disconnect(); } catch (e) {} twilioConn = null; }
    $("#btnCall").disabled = false;
    $("#btnHangup").disabled = true;
    $("#callStatus").textContent = "Ready";
    $("#callStatus").classList.remove("live");
    save(); renderStats();
  }

  /* ---------- Timer ---------- */
  function startTimer() {
    timer.t0 = Date.now();
    $("#callTimer").classList.add("live");
    timer.handle = setInterval(() => {
      $("#callTimer").textContent = fmtLong(Math.floor((Date.now() - timer.t0) / 1000));
    }, 500);
  }
  function stopTimer() {
    if (timer.handle) clearInterval(timer.handle);
    timer.handle = null;
    $("#callTimer").classList.remove("live");
    const secs = Math.floor((Date.now() - timer.t0) / 1000);
    $("#callTimer").textContent = "00:00:00";
    return secs;
  }
  function fmtLong(s) {
    const h = String(Math.floor(s / 3600)).padStart(2, "0");
    const m = String(Math.floor((s % 3600) / 60)).padStart(2, "0");
    const ss = String(s % 60).padStart(2, "0");
    return `${h}:${m}:${ss}`;
  }
  function fmtShort(s) {
    const m = String(Math.floor(s / 60)).padStart(2, "0");
    const ss = String(s % 60).padStart(2, "0");
    return `${m}:${ss}`;
  }

  /* ---------- Save & Dial Next ---------- */
  function saveOutcome(advance) {
    persistNotes();
    const lead = getSelected();
    if (lead) { lead.updatedAt = Date.now(); if (!lead.category) toast("Saved (no category set)"); }
    save();
    if (callActive) endCall();
    if (advance) {
      const next = nextUndialedAfter(selectedId);
      if (next) { selectLead(next.id); toast("Next lead ready"); }
      else toast("🎉 No more un-dialed leads");
    }
    renderAll();
  }
  function nextUndialedAfter(id) {
    const list = filteredLeads();
    const idx = list.findIndex(l => l.id === id);
    for (let i = idx + 1; i < list.length; i++) if (!list[i].dialed) return list[i];
    return list.find(l => !l.dialed) || null;
  }

  function prevLead() {
    const list = filteredLeads();
    const idx = list.findIndex(l => l.id === selectedId);
    if (idx > 0) selectLead(list[idx - 1].id);
  }
  function skipLead() {
    const list = filteredLeads();
    const idx = list.findIndex(l => l.id === selectedId);
    if (idx > -1 && idx < list.length - 1) selectLead(list[idx + 1].id);
  }

  /* ============================================================
     IMPORT / PARSING

     Scraper CSVs are messy: they include ratings ("4.6"), review counts
     ("26"), zip codes ("84101"), lat/long ("-111.891"), prices ("$85"),
     hours ("9:00-17:00"), years ("2019"), Google Place IDs, image URLs,
     etc. We score every cell for what it looks like and only keep the
     real phone number + real name/company/email/website.
     ============================================================ */
  const HEADER_ALIASES = {
    name: ["name","full name","contact","lead","contact name","owner","first name"],
    phone: ["phone","number","phone number","phone_number","tel","telephone","mobile","cell","phone1","primary phone"],
    company: ["company","business","org","organization","account","business name","company name","title"],
    email: ["email","e-mail","mail","email1","contact email"],
    website: ["website","site","url","web","domain","homepage"],
    notes: ["notes","note","comment","comments"],
    // headers we recognise but IGNORE (never use their value for anything)
    ignore: [
      "rating","reviews","review count","reviews count","review_count","reviews_count","review",
      "latitude","longitude","lat","lng","lon","place id","place_id","cid",
      "price","price level","hours","hours of operation","status","open",
      "category","categories","type","types","subtype",
      "zip","zip code","postal","postal code","postcode",
      "state","city","country","county","region","address","street","address1","address2",
      "image","photo","thumbnail","photo url","image url","photos",
      "year","founded","established","reviews_link","google_url","maps_url","google url"
    ],
  };
  function matchHeader(cell) {
    const c = cell.trim().toLowerCase().replace(/[_\-]+/g, " ").replace(/\s+/g, " ");
    for (const key in HEADER_ALIASES) if (HEADER_ALIASES[key].includes(c)) return key;
    // fuzzy: "primary_phone_1" -> phone, "business_name_en" -> company
    if (/(^|\W)(phone|tel|mobile|cell)(\W|$)/.test(c)) return "phone";
    if (/(^|\W)(email|mail)(\W|$)/.test(c)) return "email";
    if (/(^|\W)(website|url|domain|site)(\W|$)/.test(c)) return "website";
    if (/(^|\W)(company|business|org)(\W|$)/.test(c)) return "company";
    if (/(^|\W)(name|contact|owner)(\W|$)/.test(c)) return "name";
    // known-junk fuzzy → ignore
    if (/(rating|review|latitude|longitude|zip|postal|address|photo|image|hours|price|place.?id|cid)/.test(c)) return "ignore";
    return null;
  }
  function parseCSVLine(line) {
    const out = []; let cur = ""; let inQ = false;
    for (let i = 0; i < line.length; i++) {
      const ch = line[i];
      if (inQ) {
        if (ch === '"' && line[i+1] === '"') { cur += '"'; i++; }
        else if (ch === '"') inQ = false;
        else cur += ch;
      } else {
        if (ch === '"') inQ = true;
        else if (ch === "," || ch === "\t" || ch === ";") { out.push(cur); cur = ""; }
        else cur += ch;
      }
    }
    out.push(cur);
    return out.map(s => s.trim());
  }

  /* ---------- Field detectors ---------- */

  // Real phone-number detector. Rejects zip codes, ratings, review counts,
  // years, lat/long, prices, times, IDs. Accepts formatted or bare 10/11-digit
  // North American numbers and E.164 international.
  function extractPhone(val) {
    if (!val) return "";
    const s = String(val).trim();
    if (!s) return "";
    // Kill obvious non-phones early
    if (/^https?:\/\//i.test(s)) return "";      // URL
    if (s.includes("@")) return "";                // email
    if (/^\d+\.\d+$/.test(s)) return "";           // decimal (rating, price, lat/long)
    if (/^-?\d{1,3}\.\d{2,}$/.test(s)) return ""; // lat/lng
    if (/^\$?\d+(\.\d{2})?$/.test(s)) return "";   // price like $85 or 85.00
    if (/\d{1,2}:\d{2}/.test(s)) return "";       // time / hours
    // Strip common phone formatting; keep leading +
    const hasPlus = s.trim().startsWith("+");
    // Grab the first phone-shaped chunk in the string
    // (handles cells like "Phone: (435) 239-7850 ext 12")
    const m = s.match(/(\+?\d[\d\s().\-]{7,}\d)/);
    if (!m) return "";
    let raw = m[1];
    const digits = raw.replace(/\D/g, "");
    // Length gate: 10, 11 (US with 1), or 8-15 (international with +)
    if (hasPlus || raw.startsWith("+")) {
      if (digits.length < 8 || digits.length > 15) return "";
    } else {
      if (digits.length !== 10 && digits.length !== 11) return "";
      if (digits.length === 11 && digits[0] !== "1") return ""; // 11-digit must start with 1
    }
    // Reject obvious junk numbers
    if (/^0{5,}/.test(digits) || /^(\d)\1{6,}$/.test(digits)) return "";
    // Reject years / zip codes / IDs (already caught by length, but belt-and-braces)
    if (digits.length < 10) return "";
    // Normalize to E.164-ish
    if (digits.length === 10) return "+1" + digits;
    if (digits.length === 11 && digits[0] === "1") return "+" + digits;
    return (hasPlus || raw.startsWith("+") ? "+" : "+") + digits;
  }

  function extractEmail(val) {
    if (!val) return "";
    const m = String(val).match(/[\w.+\-]+@[\w\-]+\.[\w.\-]+/);
    return m ? m[0] : "";
  }
  function extractWebsite(val) {
    if (!val) return "";
    const s = String(val).trim();
    if (!s) return "";
    // Real URL or bare domain like "acme.com" / "www.acme.com"
    if (/^https?:\/\/\S+\.\S+/i.test(s)) return s.split(/\s+/)[0];
    if (/^www\.[\w\-]+\.[\w.\-]+/i.test(s)) return "https://" + s.split(/\s+/)[0];
    if (/^[\w\-]+\.(com|net|org|io|co|us|biz|info|shop|store|app|dev|xyz)(\/\S*)?$/i.test(s)) return "https://" + s;
    return "";
  }
  // Company-name-ish: mostly letters, no digits-only, not a phone/URL/email
  function looksLikeCompany(val) {
    if (!val) return false;
    const s = String(val).trim();
    if (s.length < 2 || s.length > 120) return false;
    if (extractPhone(s) || extractEmail(s) || extractWebsite(s)) return false;
    if (/^\d/.test(s)) return false;                    // starts with a digit → address
    if (/^\d+(\.\d+)?$/.test(s)) return false;          // pure number
    const letters = (s.match(/[A-Za-z]/g) || []).length;
    if (letters < 2) return false;
    if (letters / s.length < 0.5) return false;         // too many symbols
    // reject street-address-ish: "123 Main St"
    if (/\b(st|street|ave|avenue|rd|road|blvd|dr|drive|ln|lane|way|hwy|suite|ste|apt|unit)\b/i.test(s) && /\d/.test(s)) return false;
    return true;
  }
  // Person-name-ish: 2-4 capitalised words, no digits
  function looksLikePersonName(val) {
    if (!val) return false;
    const s = String(val).trim();
    if (/\d/.test(s) || s.length > 60 || s.length < 3) return false;
    if (s.includes("@") || /https?:/i.test(s)) return false;
    const parts = s.split(/\s+/);
    if (parts.length < 2 || parts.length > 4) return false;
    return parts.every(p => /^[A-Z][a-zA-Z'.\-]+$/.test(p) || /^[A-Z]\.?$/.test(p));
  }

  function parseImport(text) {
    const lines = text.split(/\r?\n/).map(l => l.trim()).filter(Boolean);
    if (!lines.length) return { rows: [], stats: { total:0, kept:0, noPhone:0, dup:0 } };
    let cols = parseCSVLine(lines[0]);
    let mapping = cols.map(matchHeader);
    let hasHeader = mapping.filter(Boolean).length >= 2;
    let dataLines = hasHeader ? lines.slice(1) : lines;

    const rows = [];
    const stats = { total: 0, kept: 0, noPhone: 0, dup: 0 };
    const seenPhones = new Set();

    dataLines.forEach(line => {
      const cells = parseCSVLine(line);
      if (!cells.length || cells.every(c => !c)) return;
      stats.total++;
      const rec = { name:"", phone:"", company:"", title:"", email:"", website:"", notes:"" };

      // Which cell indices are ignore-listed by the header (rating, reviews,
      // lat/long, zip, category, reviews_link, etc.). These cells are OFF
      // LIMITS for the whole row — they never contribute to any field.
      const isIgnored = (i) => hasHeader && mapping[i] === "ignore";

      // 1) Header-guided extraction (only for whitelisted keys)
      if (hasHeader) {
        cells.forEach((val, i) => {
          const key = mapping[i];
          if (!key || key === "ignore") return;
          if (key === "phone") { const p = extractPhone(val); if (p && !rec.phone) rec.phone = p; }
          else if (key === "email") { const e = extractEmail(val); if (e && !rec.email) rec.email = e; }
          else if (key === "website") { const w = extractWebsite(val); if (w && !rec.website) rec.website = w; }
          else if (key === "company" && !rec.company && looksLikeCompany(val)) rec.company = val.trim();
          else if (key === "name" && !rec.name) rec.name = val.trim();
          else if (key === "notes" && !rec.notes) rec.notes = val.trim();
        });
      }

      // 2) Sweep non-ignored cells to fill blanks — this is what saves us on
      //    scraper dumps where the header lies or is missing.
      cells.forEach((val, i) => {
        if (!val || isIgnored(i)) return;
        if (!rec.phone) { const p = extractPhone(val); if (p) rec.phone = p; }
        if (!rec.email) { const e = extractEmail(val); if (e) rec.email = e; }
        if (!rec.website) { const w = extractWebsite(val); if (w) rec.website = w; }
      });

      // 3) Name/company fallback — pick best-looking non-ignored cell that
      //    isn't already used as phone/email/website.
      if (!rec.name || !rec.company) {
        const nameCands = [], compCands = [];
        cells.forEach((val, i) => {
          if (!val || isIgnored(i)) return;
          const s = val.trim();
          if (s === rec.phone || s === rec.email || s === rec.website) return;
          if (looksLikePersonName(s)) nameCands.push(s);
          else if (looksLikeCompany(s)) compCands.push(s);
        });
        if (!rec.name && nameCands.length) rec.name = nameCands[0];
        if (!rec.company && compCands.length) {
          rec.company = compCands.find(c => c !== rec.name) || compCands[0];
        }
      }

      // 4) Gate: must have a real phone number
      if (!rec.phone) { stats.noPhone++; return; }
      if (seenPhones.has(rec.phone)) { stats.dup++; return; }
      seenPhones.add(rec.phone);
      rows.push(rec);
      stats.kept++;
    });

    return { rows, stats };
  }

  function previewImport() {
    const active = $(".import-tabs .tab.active").dataset.tab;
    if (active === "sample") { renderPreviewRows(sampleData(), null); return; }
    const { rows, stats } = parseImport($("#pasteArea").value);
    renderPreviewRows(rows, stats);
  }
  function renderPreviewRows(rows, stats) {
    const box = $("#importPreview");
    if (!rows.length) {
      const msg = stats && stats.total
        ? `<span class="hint">Sifted <strong>${stats.total}</strong> rows — no real phone numbers found. Ratings, zip codes, prices and IDs are ignored on purpose.</span>`
        : '<span class="hint">Paste rows above. Each lead needs a real phone number (10+ digits, formatted or bare).</span>';
      box.innerHTML = msg; box._rows = []; return;
    }
    box._rows = rows;
    const head = ["name","phone","company","email","website"].map(h => `<th>${h}</th>`).join("");
    const body = rows.slice(0, 8).map(r =>
      `<tr><td>${escapeHtml(r.name)}</td><td>${escapeHtml(prettyPhone(r.phone))}</td><td>${escapeHtml(r.company)}</td><td>${escapeHtml(r.email)}</td><td>${escapeHtml(r.website)}</td></tr>`
    ).join("");
    const dropped = stats ? (stats.total - stats.kept) : 0;
    const siftLine = stats
      ? `Sifted <strong>${stats.total}</strong> row${stats.total!==1?"s":""} → kept <strong>${stats.kept}</strong> · dropped ${dropped} (${stats.noPhone} without a real phone${stats.dup?`, ${stats.dup} duplicates`:""}).`
      : `<strong>${rows.length}</strong> lead${rows.length!==1?"s":""} ready.`;
    box.innerHTML = `${siftLine}<table><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table>${rows.length>8?`<span class="hint">…and ${rows.length-8} more</span>`:""}`;
  }

  function doImport() {
    const active = $(".import-tabs .tab.active").dataset.tab;
    let rows;
    if (active === "sample") rows = sampleData();
    else if ($("#importPreview")._rows && $("#importPreview")._rows.length) rows = $("#importPreview")._rows;
    else rows = parseImport($("#pasteArea").value).rows;
    if (!rows.length) { toast("Nothing to import — no real phone numbers found"); return; }
    // Create a batch for this import
    const rawName = ($("#batchNameInput").value || "").trim();
    const batch = {
      id: uid(),
      name: rawName || `Batch ${state.batches.length + 1} — ${new Date().toLocaleDateString(undefined, { month: "short", day: "numeric" })}`,
      createdAt: Date.now(),
    };
    // De-dupe against existing phones
    const existing = new Set(state.leads.map(l => l.phone));
    let added = 0;
    rows.forEach(r => {
      if (existing.has(r.phone)) return;
      existing.add(r.phone);
      state.leads.push(makeLead(r, batch.id));
      added++;
    });
    if (added > 0) {
      state.batches.push(batch);
      state.ui.activeBatch = batch.id;   // jump to the new batch
    }
    $("#batchNameInput").value = "";
    save(); closeModals(); renderAll();
    const withSite = rows.filter(r => r.website).length;
    const msg = state.ui.hideWithWebsite && withSite > 0
      ? `Imported ${added} into "${batch.name}" (${withSite} hidden — already have websites)`
      : `Imported ${added} into "${batch.name}"`;
    toast(msg);
    if (!selectedId && state.leads.length) {
      const first = filteredLeads()[0];
      if (first) selectLead(first.id);
    }
  }
  function makeLead(r, batchId) {
    return {
      id: uid(), batchId: batchId || "legacy",
      name: r.name || "", phone: cleanPhone(r.phone), company: r.company || "",
      title: r.title || "", email: r.email || "", website: r.website || "", notes: r.notes || "",
      category: null, dialed: false, dialCount: 0, createdAt: Date.now(), updatedAt: Date.now(),
    };
  }

  function sampleData() {
    return [
      { name:"Mary J Laub", phone:"+14352397850", company:"Precision Landscape", title:"Owner", email:"" },
      { name:"Tom Reyes", phone:"+13105550142", company:"Reyes Auto Repair", title:"Manager", email:"tom@reyesauto.com" },
      { name:"Sandra Kim", phone:"+16505550198", company:"Kim Family Dentistry", title:"Office Mgr", email:"" },
      { name:"Derek Owens", phone:"+12145550171", company:"Owens Roofing", title:"Owner", email:"" },
      { name:"Priya Patel", phone:"+19735550188", company:"Patel Legal Group", title:"Partner", email:"priya@patellaw.com" },
      { name:"Luis Gómez", phone:"+13055550110", company:"Gómez Plumbing", title:"Owner", email:"" },
      { name:"Hannah Brooks", phone:"+16175550133", company:"Brooks Bakery", title:"Owner", email:"" },
      { name:"Ray Nolan", phone:"+17025550166", company:"Nolan HVAC", title:"Owner", email:"" },
      { name:"Aisha Khan", phone:"+14045550120", company:"Khan Tutoring", title:"Founder", email:"" },
      { name:"Greg Stanton", phone:"+12065550155", company:"Stanton Electric", title:"Owner", email:"" },
      { name:"Nina Petrova", phone:"+13125550177", company:"Petrova Salon", title:"Owner", email:"" },
      { name:"Carlos Vega", phone:"+16195550144", company:"Vega Landscaping", title:"Owner", email:"" },
    ].map(r => ({ ...r, phone: cleanPhone(r.phone) }));
  }

  /* ---------- Export ---------- */
  function exportCSV() {
    if (!state.leads.length) { toast("No leads to export"); return; }
    const headers = ["name","phone","company","title","email","website","category","dialed","dialCount","notes"];
    const lines = [headers.join(",")];
    state.leads.forEach(l => {
      const cat = l.category ? (catById(l.category)?.name || "") : "";
      const row = [l.name, l.phone, l.company, l.title, l.email, l.website, cat, l.dialed ? "yes":"no", l.dialCount||0, l.notes];
      lines.push(row.map(csvCell).join(","));
    });
    const blob = new Blob([lines.join("\n")], { type: "text/csv" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `prospectdialer-${new Date().toISOString().slice(0,10)}.csv`;
    a.click();
    URL.revokeObjectURL(a.href);
  }
  function csvCell(v) {
    v = v == null ? "" : String(v);
    return /[",\n]/.test(v) ? `"${v.replace(/"/g,'""')}"` : v;
  }

  /* ============================================================
     CATEGORY EDITOR (settings)
     ============================================================ */
  function renderCategoryEditor() {
    const box = $("#categoryEditor");
    box.innerHTML = "";
    state.categories.forEach((c, i) => {
      const row = document.createElement("div");
      row.className = "cat-edit-row";
      row.innerHTML = `
        <input type="color" value="${c.color}" />
        <input type="text" value="${escapeHtml(c.name)}" />
        <button class="cat-del" title="Delete">🗑</button>`;
      const [colorEl, nameEl, delBtn] = [row.querySelector('input[type=color]'), row.querySelector('input[type=text]'), row.querySelector('.cat-del')];
      colorEl.onchange = () => { c.color = colorEl.value; save(); renderList(); renderCounts(); renderCategoryPicker(); };
      nameEl.onchange = () => { c.name = nameEl.value.trim() || c.name; nameEl.value = c.name; save(); renderAll(); renderCategoryEditor(); };
      delBtn.onclick = () => {
        if (!confirm(`Delete category "${c.name}"? Leads keep their data but lose this tag.`)) return;
        state.leads.forEach(l => { if (l.category === c.id) l.category = null; });
        state.categories.splice(i, 1);
        save(); renderAll(); renderCategoryEditor();
      };
      box.appendChild(row);
    });
  }
  function addCategory() {
    const name = $("#newCatName").value.trim();
    if (!name) { toast("Enter a category name"); return; }
    state.categories.push({ id: uid(), name, color: $("#newCatColor").value });
    $("#newCatName").value = "";
    save(); renderAll(); renderCategoryEditor();
  }

  /* ============================================================
     TWILIO (optional real in-browser calling)
     ============================================================ */
  let twilioDevice = null, twilioConn = null, twilioLoading = false;
  function loadTwilioSDK() {
    return new Promise((resolve, reject) => {
      if (window.Twilio && window.Twilio.Device) return resolve();
      const s = document.createElement("script");
      s.src = "https://sdk.twilio.com/js/voice/releases/2.11.1/twilio.min.js";
      s.onload = resolve; s.onerror = reject;
      document.head.appendChild(s);
    });
  }
  async function startTwilioCall(lead) {
    try {
      if (twilioLoading) return;
      twilioLoading = true;
      await loadTwilioSDK();
      if (!twilioDevice) {
        const res = await fetch(state.settings.twilioTokenUrl);
        const data = await res.json();
        twilioDevice = new window.Twilio.Device(data.token, { codecPreferences: ["opus", "pcmu"] });
        await twilioDevice.register();
      }
      twilioConn = await twilioDevice.connect({ params: { To: cleanPhone(lead.phone) } });
      twilioConn.on("disconnect", () => { if (callActive) endCall(); });
      $("#phoneMode").textContent = "Twilio · connected";
    } catch (e) {
      console.error(e);
      toast("Twilio failed — falling back to click-to-call");
      window.location.href = "tel:" + cleanPhone(lead.phone);
    } finally { twilioLoading = false; }
  }

  /* ============================================================
     MODALS + UI WIRING
     ============================================================ */
  function openModal(id) {
    $("#modalBackdrop").hidden = false;
    $("#" + id).hidden = false;
  }
  function closeModals() {
    $("#modalBackdrop").hidden = true;
    $$(".modal").forEach(m => m.hidden = true);
  }

  function toast(msg) {
    const t = $("#toast");
    t.textContent = msg; t.hidden = false;
    clearTimeout(t._h);
    t._h = setTimeout(() => { t.hidden = true; }, 2600);
  }
  function escapeHtml(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, ch => ({ "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;" }[ch]));
  }

  function wire() {
    // top bar
    $("#btnImport").onclick = () => { openModal("importModal"); previewImport(); };
    $("#btnAddOne").onclick = () => openModal("addModal");
    $("#btnExport").onclick = exportCSV;
    $("#btnSettings").onclick = () => { renderCategoryEditor(); syncSettingsUI(); openModal("settingsModal"); };

    // modal close
    $("#modalBackdrop").onclick = closeModals;
    $$("[data-close]").forEach(b => b.onclick = closeModals);
    document.addEventListener("keydown", e => { if (e.key === "Escape") closeModals(); });

    // dialpad
    $("#dialpad").addEventListener("click", e => {
      const btn = e.target.closest("button"); if (!btn) return;
      // visual feedback only; DTMF sent to Twilio if connected
      if (twilioConn) { try { twilioConn.sendDigits(btn.dataset.key); } catch (_) {} }
    });

    // call controls
    $("#btnCall").onclick = startCall;
    $("#btnHangup").onclick = endCall;
    $("#btnSkip").onclick = skipLead;
    $("#btnPrev").onclick = prevLead;

    // outcome
    $("#btnSaveNext").onclick = () => saveOutcome(true);
    $("#btnSave").onclick = () => saveOutcome(false);
    $("#leadNotes").addEventListener("blur", () => { persistNotes(); save(); });

    // list controls
    $("#search").addEventListener("input", renderList);
    $("#filterCategory").addEventListener("change", renderList);

    // import tabs
    $$(".import-tabs .tab").forEach(tab => {
      tab.onclick = () => {
        $$(".import-tabs .tab").forEach(t => t.classList.remove("active"));
        tab.classList.add("active");
        $$(".tab-body").forEach(b => b.hidden = b.dataset.panel !== tab.dataset.tab);
        previewImport();
      };
    });
    $("#pasteArea").addEventListener("input", previewImport);
    $("#fileInput").addEventListener("change", e => {
      const file = e.target.files[0]; if (!file) return;
      const reader = new FileReader();
      reader.onload = () => {
        $("#pasteArea").value = reader.result;
        $$(".import-tabs .tab").forEach(t => t.classList.toggle("active", t.dataset.tab === "paste"));
        $$(".tab-body").forEach(b => b.hidden = b.dataset.panel !== "paste");
        previewImport();
      };
      reader.readAsText(file);
    });
    // drag & drop onto paste area
    const pa = $("#pasteArea");
    pa.addEventListener("dragover", e => e.preventDefault());
    pa.addEventListener("drop", e => {
      e.preventDefault();
      const file = e.dataTransfer.files[0]; if (!file) return;
      const reader = new FileReader();
      reader.onload = () => { pa.value = reader.result; previewImport(); };
      reader.readAsText(file);
    });
    $("#btnDoImport").onclick = doImport;

    // add one
    $("#btnDoAdd").onclick = () => {
      const phone = cleanPhone($("#f_phone").value);
      if (!phone) { toast("Phone is required"); return; }
      // Ensure a "Manual" batch exists
      let manual = state.batches.find(b => b.id === "manual");
      if (!manual) {
        manual = { id: "manual", name: "Manual Adds", createdAt: Date.now() };
        state.batches.push(manual);
      }
      const rec = {
        name: $("#f_name").value, phone, company: $("#f_company").value,
        title: $("#f_title").value, email: $("#f_email").value,
        website: $("#f_website").value, notes: $("#f_notes").value,
      };
      state.leads.unshift(makeLead(rec, "manual"));
      ["f_phone","f_name","f_company","f_title","f_email","f_website","f_notes"].forEach(id => $("#"+id).value = "");
      save(); closeModals(); renderAll();
      selectLead(state.leads[0].id);
      toast("Lead added");
    };

    // hide-has-website toggle
    const hideCb = $("#hideWithWebsite");
    if (hideCb) hideCb.addEventListener("change", () => {
      state.ui.hideWithWebsite = hideCb.checked;
      save(); renderList();
    });

    // reset dropdown
    const resetBtn = $("#btnResetCalls");
    if (resetBtn) resetBtn.addEventListener("click", () => {
      const scope = state.ui.activeBatch
        ? state.batches.find(b => b.id === state.ui.activeBatch)?.name
        : "ALL leads";
      if (!confirm(`Reset call progress for ${scope}?\n\nThis clears dialed status, category tags, and per-call timers. Leads themselves are kept.`)) return;
      const target = state.ui.activeBatch;
      resetCallProgress(l => !target || l.batchId === target);
      toast(`Reset ${scope}`);
    });

    // settings — categories
    $("#btnAddCat").onclick = addCategory;
    $("#newCatName").addEventListener("keydown", e => { if (e.key === "Enter") addCategory(); });

    // settings — call mode
    $$('input[name=callmode]').forEach(r => r.onchange = () => {
      state.settings.callMode = document.querySelector('input[name=callmode]:checked').value;
      $("#twilioConfig").hidden = state.settings.callMode !== "twilio";
      save(); renderPhone();
    });
    $("#twilioTokenUrl").addEventListener("change", e => { state.settings.twilioTokenUrl = e.target.value.trim(); save(); });
    $("#twilioCallerId").addEventListener("change", e => { state.settings.twilioCallerId = e.target.value.trim(); save(); });

    // danger
    $("#btnClearAll").onclick = () => {
      if (!confirm("Delete ALL leads, batches, and reset everything? This cannot be undone.")) return;
      state = { leads: [], batches: [], categories: clone(DEFAULT_CATEGORIES), settings: defaultSettings(), totalTalkSeconds: 0, ui: { activeBatch: "", hideWithWebsite: true } };
      selectedId = null; save(); closeModals(); renderAll(); renderCategoryEditor();
      toast("All data cleared");
    };
  }

  function syncSettingsUI() {
    $$('input[name=callmode]').forEach(r => r.checked = r.value === state.settings.callMode);
    $("#twilioConfig").hidden = state.settings.callMode !== "twilio";
    $("#twilioTokenUrl").value = state.settings.twilioTokenUrl || "";
    $("#twilioCallerId").value = state.settings.twilioCallerId || "";
  }

  /* ---------- init ---------- */
  wire();
  renderAll();
  if (state.leads.length) selectLead(state.leads[0].id);
})();
