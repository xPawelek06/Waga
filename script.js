// Prosta blokada hasłem po stronie klienta (wzorzec identyczny jak PlanTreningowy).
// To NIE jest prawdziwe zabezpieczenie (kod i hash są jawne w źródle strony) —
// to tylko odstraszacz przed przypadkowym trafieniem na stronę.
//
// To samo hasło jest też sekretem wysyłanym do backendu przy zapisie
// (nagłówek X-Auth-Secret) — patrz saveEntry()/runWeeklySummary niżej.
const CORRECT_HASH =
  "d38c9ea4eb4e9e9837b51c4155cb246a82ce89b58261eebe9ea497ed4b49f4ce";
const SESSION_KEY = "waga-unlocked";
const SECRET_SESSION_KEY = "waga-secret";

const API_BASE = "https://waga-api-vorc.onrender.com";

let authSecret = "";

async function sha256Hex(text) {
  const data = new TextEncoder().encode(text);
  const digest = await crypto.subtle.digest("SHA-256", data);
  return Array.from(new Uint8Array(digest))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

function showContent() {
  document.getElementById("lock-screen").classList.add("hidden");
  document.getElementById("content").classList.remove("hidden");
  loadWeek();
  loadSummaries();
}

async function tryUnlock() {
  const input = document.getElementById("password-input");
  const error = document.getElementById("lock-error");
  const value = input.value;
  const hash = await sha256Hex(value);

  if (hash === CORRECT_HASH) {
    authSecret = value;
    sessionStorage.setItem(SESSION_KEY, "1");
    sessionStorage.setItem(SECRET_SESSION_KEY, value);
    showContent();
  } else {
    error.textContent = "Złe hasło, spróbuj ponownie.";
    input.value = "";
    input.focus();
  }
}

document.getElementById("unlock-btn").addEventListener("click", tryUnlock);
document.getElementById("password-input").addEventListener("keydown", (e) => {
  if (e.key === "Enter") tryUnlock();
});

if (sessionStorage.getItem(SESSION_KEY) === "1") {
  authSecret = sessionStorage.getItem(SECRET_SESSION_KEY) || "";
  showContent();
}

// --- Zakładki ---

document.querySelectorAll(".tab-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach((p) => p.classList.add("hidden"));
    btn.classList.add("active");
    document.getElementById(`tab-${btn.dataset.tab}`).classList.remove("hidden");
  });
});

// --- Tydzień: pobranie z API i render tabeli ---

function setLoadStatus(text, isError) {
  const statusEl = document.getElementById("load-status");
  if (!text) {
    statusEl.classList.add("hidden");
    return;
  }
  statusEl.textContent = text;
  statusEl.classList.remove("hidden");
  statusEl.classList.toggle("load-error", Boolean(isError));
}

function makeEl(tag, opts) {
  const node = document.createElement(tag);
  opts = opts || {};
  if (opts.text !== undefined) node.textContent = opts.text;
  if (opts.className) node.className = opts.className;
  if (opts.attrs) {
    for (const [k, v] of Object.entries(opts.attrs)) node.setAttribute(k, v);
  }
  return node;
}

function buildRow(day, avgWeight7d) {
  const tr = document.createElement("tr");

  tr.appendChild(makeEl("td", { text: day.day, attrs: { "data-label": "Dzień" } }));

  const dateCell = makeEl("td", { attrs: { "data-label": "Data" } });
  const dateInput = makeEl("input", { attrs: { type: "date" } });
  dateInput.value = day.entry_date || "";
  dateCell.appendChild(dateInput);
  tr.appendChild(dateCell);

  const weightCell = makeEl("td", { attrs: { "data-label": "Waga (kg)" } });
  const weightInput = makeEl("input", { attrs: { type: "number", step: "0.1", inputmode: "decimal" } });
  weightInput.value = day.weight_kg ?? "";
  weightCell.appendChild(weightInput);
  tr.appendChild(weightCell);

  const kcalCell = makeEl("td", { attrs: { "data-label": "Kcal" } });
  const kcalInput = makeEl("input", { attrs: { type: "number", step: "1", inputmode: "numeric" } });
  kcalInput.value = day.kcal ?? "";
  kcalCell.appendChild(kcalInput);
  tr.appendChild(kcalCell);

  const avgCell = makeEl("td", {
    text: avgWeight7d !== null && avgWeight7d !== undefined ? avgWeight7d.toFixed(2) : "—",
    className: "avg-cell",
    attrs: { "data-label": "Średnia 7-dniowa" },
  });
  tr.appendChild(avgCell);

  const actionCell = makeEl("td", { attrs: { "data-label": "" }, className: "action-cell" });
  const saveBtn = makeEl("button", { text: "Zapisz", className: "save-btn" });
  const status = makeEl("span", { className: "save-status" });
  saveBtn.addEventListener("click", () =>
    saveEntry(day.id, dateInput.value, weightInput.value, kcalInput.value, saveBtn, status)
  );
  actionCell.appendChild(saveBtn);
  actionCell.appendChild(status);
  tr.appendChild(actionCell);

  return tr;
}

async function loadWeek() {
  setLoadStatus("Ładowanie… (jeśli backend spał, może to potrwać do 30 sek)", false);
  try {
    const resp = await fetchWithRetry(`${API_BASE}/api/week`);
    const week = await resp.json();

    const tbody = document.getElementById("week-body");
    tbody.innerHTML = "";
    for (const day of week.days) {
      tbody.appendChild(buildRow(day, week.avg_weight_7d));
    }

    setLoadStatus(null);
  } catch (err) {
    setLoadStatus(
      "Nie udało się połączyć z serwerem. Sprawdź internet i spróbuj odświeżyć stronę.",
      true
    );
    console.error("Błąd ładowania tygodnia:", err);
  }
}

async function saveEntry(weekDayId, entryDate, weight, kcal, button, statusEl) {
  button.disabled = true;
  statusEl.textContent = "Zapisywanie…";
  statusEl.classList.remove("save-error");
  try {
    const resp = await fetch(`${API_BASE}/api/entries`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Auth-Secret": authSecret,
      },
      body: JSON.stringify({
        week_day_id: weekDayId,
        entry_date: entryDate || null,
        weight_kg: weight === "" ? null : Number(weight),
        kcal: kcal === "" ? null : Number(kcal),
      }),
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    statusEl.textContent = "Zapisano ✓";
    setTimeout(() => {
      statusEl.textContent = "";
    }, 2500);
    // Srednia 7-dniowa mogla sie zmienic po zapisie - odswiez cala tabele.
    loadWeek();
  } catch (err) {
    statusEl.textContent = "Błąd zapisu";
    statusEl.classList.add("save-error");
    console.error("Błąd zapisu wpisu:", err);
  } finally {
    button.disabled = false;
  }
}

// --- Fetch z ponawianiem: darmowy plan Render usypia backend/baze po ~15 min
// bezczynnosci - pierwszy request po uspieniu regularnie konczy sie 500/timeoutem
// (baza jeszcze sie "budzi"), kolejny juz przechodzi. Z komputera appka bywa
// testowana zaraz po innej interakcji (backend juz rozgrzany), z telefonu
// zwykle po dluzszej przerwie - stad wrazenie "na telefonie nic sie nie
// pokazuje", choc to nie jest bug specyficzny dla urzadzenia, tylko wyscig ze
// stanem backendu. Ponawiamy kilka razy zanim pokazemy blad.
async function fetchWithRetry(url, options, attempts, delayMs) {
  attempts = attempts || 3;
  delayMs = delayMs || 1500;
  let lastErr;
  for (let i = 0; i < attempts; i++) {
    try {
      const resp = await fetch(url, options);
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      return resp;
    } catch (err) {
      lastErr = err;
      if (i < attempts - 1) {
        await new Promise((r) => setTimeout(r, delayMs * (i + 1)));
      }
    }
  }
  throw lastErr;
}

// --- Trend: historia podsumowań tygodniowych ---

function renderVerdict(summaries) {
  const box = document.getElementById("latest-verdict");
  box.innerHTML = "";
  if (!summaries.length) {
    box.appendChild(makeEl("p", { text: "Brak podsumowań jeszcze — pojawi się po pierwszej niedzieli." }));
    return;
  }
  const latest = summaries[0];
  const title = makeEl("p", {
    className: "verdict-title",
    text: `Tydzień ${latest.week_start} – ${latest.week_end}`,
  });
  const weight = makeEl("p", {
    text: `Średnia waga: ${latest.avg_weight_kg !== null ? latest.avg_weight_kg + " kg" : "brak danych"}`,
  });
  const trend = makeEl("p", {
    className: "verdict-trend",
    text: latest.trend ? `Trend: ${latest.trend}` : "Trend: —",
  });
  const rec = makeEl("p", {
    className: "verdict-rec",
    text: latest.kcal_recommendation || "—",
  });
  box.appendChild(title);
  box.appendChild(weight);
  box.appendChild(trend);
  box.appendChild(rec);
}

function renderSummaryHistory(summaries) {
  const tbody = document.getElementById("summary-body");
  tbody.innerHTML = "";
  if (!summaries.length) {
    const tr = document.createElement("tr");
    tr.appendChild(
      makeEl("td", { text: "Brak podsumowań jeszcze.", attrs: { "data-label": "" } })
    );
    tbody.appendChild(tr);
    return;
  }
  for (const s of summaries) {
    const tr = document.createElement("tr");
    tr.appendChild(
      makeEl("td", { text: `${s.week_start} – ${s.week_end}`, attrs: { "data-label": "Tydzień" } })
    );
    tr.appendChild(
      makeEl("td", {
        text: s.avg_weight_kg !== null ? String(s.avg_weight_kg) : "—",
        attrs: { "data-label": "Śr. waga (kg)" },
      })
    );
    tr.appendChild(
      makeEl("td", {
        text: s.avg_kcal !== null ? String(s.avg_kcal) : "—",
        attrs: { "data-label": "Śr. kcal" },
      })
    );
    tr.appendChild(makeEl("td", { text: s.trend || "—", attrs: { "data-label": "Trend" } }));
    tr.appendChild(
      makeEl("td", { text: s.kcal_recommendation || "—", attrs: { "data-label": "Rekomendacja" } })
    );
    tbody.appendChild(tr);
  }
}

async function loadSummaries() {
  const verdictBox = document.getElementById("latest-verdict");
  verdictBox.innerHTML = '<p class="load-status">Ładowanie… (jeśli backend spał, może to potrwać do 30 sek)</p>';
  try {
    const resp = await fetchWithRetry(`${API_BASE}/api/weekly-summary`);
    const summaries = await resp.json();
    renderVerdict(summaries);
    renderSummaryHistory(summaries);
  } catch (err) {
    console.error("Błąd ładowania podsumowań:", err);
    verdictBox.innerHTML =
      '<p class="load-status load-error">Nie udało się pobrać historii trendu. Sprawdź internet i spróbuj odświeżyć stronę.</p>';
    const tbody = document.getElementById("summary-body");
    tbody.innerHTML = "";
    const tr = document.createElement("tr");
    tr.appendChild(
      makeEl("td", {
        text: "Nie udało się pobrać historii.",
        className: "load-error",
        attrs: { "data-label": "" },
      })
    );
    tbody.appendChild(tr);
  }
}
