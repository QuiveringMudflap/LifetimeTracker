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
        if (!s.settings) s.settings = defaultSettings();
        if (typeof s.totalTalkSeconds !== "number") s.totalTalkSeconds = 0;
        return s;
      }
    } catch (e) { console.warn("load failed", e); }
    return { leads: [], categories: clone(DEFAULT_CATEGORIES), settings: defaultSettings(), totalTalkSeconds: 0 };
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
    return state.leads.filter(l => {
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

  function renderAll() {
    renderFilterOptions();
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
     ============================================================ */
  const HEADER_ALIASES = {
    name: ["name","full name","contact","lead","contact name"],
    phone: ["phone","number","phone number","tel","telephone","mobile","cell"],
    company: ["company","business","org","organization","account"],
    title: ["title","role","position"],
    email: ["email","e-mail","mail"],
    website: ["website","site","url","web"],
    notes: ["notes","note","comment","comments"],
  };
  function matchHeader(cell) {
    const c = cell.trim().toLowerCase();
    for (const key in HEADER_ALIASES) if (HEADER_ALIASES[key].includes(c)) return key;
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
  function parseImport(text) {
    const lines = text.split(/\r?\n/).map(l => l.trim()).filter(Boolean);
    if (!lines.length) return [];
    let cols = parseCSVLine(lines[0]);
    let mapping = cols.map(matchHeader);
    let hasHeader = mapping.filter(Boolean).length >= 2;
    let dataLines = hasHeader ? lines.slice(1) : lines;
    if (!hasHeader) {
      // Guess: find the column that looks like a phone; treat first as name.
      mapping = cols.map(() => null);
    }
    const rows = [];
    dataLines.forEach(line => {
      const cells = parseCSVLine(line);
      const rec = { name:"", phone:"", company:"", title:"", email:"", website:"", notes:"" };
      if (hasHeader) {
        cells.forEach((val, i) => { const key = mapping[i]; if (key) rec[key] = val; });
      } else {
        // Heuristic positional parse
        cells.forEach((val) => {
          const digits = val.replace(/[^\d]/g, "");
          if (!rec.phone && digits.length >= 7 && /[\d()+\-\s]/.test(val)) rec.phone = val;
          else if (!rec.name) rec.name = val;
          else if (!rec.company) rec.company = val;
          else if (!rec.title) rec.title = val;
          else if (val.includes("@") && !rec.email) rec.email = val;
        });
      }
      rec.phone = cleanPhone(rec.phone);
      if (rec.phone) rows.push(rec);
    });
    return rows;
  }

  function previewImport() {
    const active = $(".import-tabs .tab.active").dataset.tab;
    let text = "";
    if (active === "sample") { renderPreviewRows(sampleData()); return; }
    text = $("#pasteArea").value;
    const rows = parseImport(text);
    renderPreviewRows(rows);
  }
  function renderPreviewRows(rows) {
    const box = $("#importPreview");
    if (!rows.length) { box.innerHTML = '<span class="hint">No valid rows detected yet (each row needs a phone number).</span>'; box._rows = []; return; }
    box._rows = rows;
    const head = ["name","phone","company","title","email"].map(h => `<th>${h}</th>`).join("");
    const body = rows.slice(0, 8).map(r =>
      `<tr><td>${escapeHtml(r.name)}</td><td>${escapeHtml(prettyPhone(r.phone))}</td><td>${escapeHtml(r.company)}</td><td>${escapeHtml(r.title)}</td><td>${escapeHtml(r.email)}</td></tr>`
    ).join("");
    box.innerHTML = `<strong>${rows.length}</strong> lead${rows.length>1?"s":""} ready.<table><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table>${rows.length>8?`<span class="hint">…and ${rows.length-8} more</span>`:""}`;
  }

  function doImport() {
    const active = $(".import-tabs .tab.active").dataset.tab;
    let rows = active === "sample" ? sampleData() : ($("#importPreview")._rows || parseImport($("#pasteArea").value));
    if (!rows.length) { toast("Nothing to import"); return; }
    // De-dupe against existing phones
    const existing = new Set(state.leads.map(l => l.phone));
    let added = 0;
    rows.forEach(r => {
      if (existing.has(r.phone)) return;
      existing.add(r.phone);
      state.leads.push(makeLead(r));
      added++;
    });
    save(); closeModals(); renderAll();
    toast(`Imported ${added} lead${added!==1?"s":""}${added<rows.length?` (${rows.length-added} duplicates skipped)`:""}`);
    if (!selectedId && state.leads.length) selectLead(state.leads[0].id);
  }
  function makeLead(r) {
    return {
      id: uid(), name: r.name || "", phone: cleanPhone(r.phone), company: r.company || "",
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
      const rec = {
        name: $("#f_name").value, phone, company: $("#f_company").value,
        title: $("#f_title").value, email: $("#f_email").value,
        website: $("#f_website").value, notes: $("#f_notes").value,
      };
      state.leads.unshift(makeLead(rec));
      ["f_phone","f_name","f_company","f_title","f_email","f_website","f_notes"].forEach(id => $("#"+id).value = "");
      save(); closeModals(); renderAll();
      selectLead(state.leads[0].id);
      toast("Lead added");
    };

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
      if (!confirm("Delete ALL leads and reset everything? This cannot be undone.")) return;
      state = { leads: [], categories: clone(DEFAULT_CATEGORIES), settings: defaultSettings(), totalTalkSeconds: 0 };
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
