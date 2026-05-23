const state = {
  view: "cancer",
  tables: [],
  overview: null,
  health: null
};

const copy = {
  cancer: {
    kicker: "Cancer Data",
    title: "Cancer cohort tables",
    empty: "No cancer-oriented tables detected yet.",
    hint: "Import TCGA/GDC, clinical, mutation, CNV, survival, or sample tables and they will appear here automatically."
  },
  chemical: {
    kicker: "Chemical Data",
    title: "Chemical and compound tables",
    empty: "No chemical-oriented tables detected yet.",
    hint: "Drug, compound, molecule, SMILES, PubChem, ChEMBL, ADMET, or toxicity tables will be grouped here."
  },
  analysis: {
    kicker: "Data Analysis",
    title: "Database analysis overview",
    empty: "No analysis metadata available.",
    hint: "The overview summarizes table counts, row counts, and widest schemas from PostgreSQL."
  }
};

const elements = {
  dbPill: document.querySelector("#db-pill"),
  metricTables: document.querySelector("#metric-tables"),
  metricRows: document.querySelector("#metric-rows"),
  metricLatency: document.querySelector("#metric-latency"),
  metricDb: document.querySelector("#metric-db"),
  tableGrid: document.querySelector("#table-grid"),
  analysisView: document.querySelector("#analysis-view"),
  statusMessage: document.querySelector("#status-message"),
  viewKicker: document.querySelector("#view-kicker"),
  viewTitle: document.querySelector("#view-title"),
  refreshButton: document.querySelector("#refresh-button")
};

function formatNumber(value) {
  return new Intl.NumberFormat().format(value || 0);
}

async function fetchJson(url) {
  const response = await fetch(url);
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.message || "Request failed");
  }
  return payload;
}

function setDbStatus(ok, text) {
  const pulse = elements.dbPill.querySelector(".pulse");
  pulse.classList.remove("pending", "ok", "error");
  pulse.classList.add(ok ? "ok" : "error");
  elements.dbPill.querySelector("span:last-child").textContent = text;
}

function tableCard(table) {
  const visibleColumns = table.columns.slice(0, 8);
  const hiddenCount = Math.max(table.columns.length - visibleColumns.length, 0);
  const chips = visibleColumns
    .map((column) => `<span class="chip">${column.name} · ${column.type}</span>`)
    .join("");

  return `
    <article class="table-card">
      <h3>${table.name}</h3>
      <code>${table.schema}.${table.name}</code>
      <div class="chip-row">
        <span class="chip">${formatNumber(table.rowCount)} estimated rows</span>
        <span class="chip">${formatNumber(table.columnCount)} columns</span>
        <span class="chip">${table.category}</span>
      </div>
      <p>${table.description || "No table comment is available in PostgreSQL."}</p>
      <div class="chip-row">
        ${chips}
        ${hiddenCount ? `<span class="chip">+${hiddenCount} more</span>` : ""}
      </div>
    </article>
  `;
}

function renderEmpty(view) {
  const info = copy[view];
  elements.tableGrid.innerHTML = `
    <div class="empty-state">
      <strong>${info.empty}</strong>
      <span>${info.hint}</span>
    </div>
  `;
}

function renderAnalysis() {
  const overview = state.overview;
  elements.tableGrid.innerHTML = "";
  elements.analysisView.hidden = false;

  if (!overview) {
    elements.analysisView.innerHTML = "";
    renderEmpty("analysis");
    return;
  }

  const categoryTiles = Object.entries(overview.categories)
    .map(
      ([name, value]) => `
        <article class="analysis-tile">
          <span class="metric-label">${name}</span>
          <strong>${formatNumber(value.tables)}</strong>
          <p>${formatNumber(value.rows)} estimated rows across detected ${name} data tables.</p>
        </article>
      `
    )
    .join("");

  const widest = overview.widestTables
    .map((table) => `<li>${table.schema}.${table.name} · ${table.columnCount} columns</li>`)
    .join("");

  elements.analysisView.innerHTML = `
    <article class="analysis-tile">
      <span class="metric-label">All rows</span>
      <strong>${formatNumber(overview.totalRows)}</strong>
      <p>Estimated from PostgreSQL planner statistics for responsive browsing.</p>
    </article>
    <article class="analysis-tile">
      <span class="metric-label">All tables</span>
      <strong>${formatNumber(overview.totalTables)}</strong>
      <p>Base tables found outside system schemas.</p>
    </article>
    ${categoryTiles}
    <article class="analysis-tile">
      <span class="metric-label">Widest schemas</span>
      <ul>${widest || "<li>No table schemas found yet.</li>"}</ul>
    </article>
  `;
}

function renderCurrentView() {
  const view = state.view;
  const info = copy[view];
  elements.viewKicker.textContent = info.kicker;
  elements.viewTitle.textContent = info.title;

  document.querySelectorAll("[data-view]").forEach((item) => {
    item.classList.toggle("active", item.dataset.view === view);
  });

  if (view === "analysis") {
    renderAnalysis();
    return;
  }

  elements.analysisView.hidden = true;
  elements.analysisView.innerHTML = "";
  const tables = state.tables.filter((table) => table.category === view);
  if (!tables.length) {
    renderEmpty(view);
    return;
  }
  elements.tableGrid.innerHTML = tables.map(tableCard).join("");
}

function updateMetrics() {
  const overview = state.overview;
  elements.metricTables.textContent = overview ? formatNumber(overview.totalTables) : "...";
  elements.metricRows.textContent = overview ? formatNumber(overview.totalRows) : "...";
  elements.metricLatency.textContent = state.health ? `${state.health.latencyMs}ms` : "...";
  elements.metricDb.textContent = state.health?.postgres?.database || "...";

  const counts = state.tables.reduce(
    (acc, table) => {
      acc[table.category] += 1;
      return acc;
    },
    { cancer: 0, chemical: 0, analysis: 0 }
  );

  document.querySelector("#rail-cancer").textContent = counts.cancer;
  document.querySelector("#rail-chemical").textContent = counts.chemical;
  document.querySelector("#rail-analysis").textContent = state.overview?.totalTables || 0;
}

async function loadData() {
  elements.statusMessage.textContent = "Loading PostgreSQL metadata...";
  elements.refreshButton.disabled = true;

  try {
    const [health, tablePayload, overview] = await Promise.all([
      fetchJson("/api/health"),
      fetchJson("/api/tables"),
      fetchJson("/api/analysis/overview")
    ]);

    state.health = health;
    state.tables = tablePayload.tables;
    state.overview = overview;
    setDbStatus(true, `Connected to ${health.postgres.database}`);
    elements.statusMessage.textContent = `Last refreshed ${new Date().toLocaleTimeString()}`;
  } catch (error) {
    setDbStatus(false, "PostgreSQL unavailable");
    elements.statusMessage.textContent = error.message;
  } finally {
    elements.refreshButton.disabled = false;
    updateMetrics();
    renderCurrentView();
  }
}

function setView(view) {
  state.view = view;
  history.replaceState(null, "", `#${view}`);
  renderCurrentView();
}

document.querySelectorAll("[data-view]").forEach((item) => {
  item.addEventListener("click", (event) => {
    event.preventDefault();
    setView(item.dataset.view);
  });
});

elements.refreshButton.addEventListener("click", loadData);

const initialView = location.hash.replace("#", "");
if (["cancer", "chemical", "analysis"].includes(initialView)) {
  state.view = initialView;
}

loadData();
