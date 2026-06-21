const state = {
  data: null,
  selectedDataKey: "rna",
  selectedStep: 1,
  selectedModelKey: "random_forest",
  selectedModelView: "metrics",
  selectedGene: "KRAS",
  compoundQuery: "",
  compoundEvidence: "all",
  compoundSort: "name",
  glossaryQuery: "",
  glossaryCategory: "all",
  sourceType: "all",
  contactEmail: "contact@example.com"
};

const els = {
  menuButton: document.querySelector(".menu-button"),
  nav: document.querySelector("#primary-nav"),
  heroStats: document.querySelector("#hero-stats"),
  dataFilters: document.querySelector("#data-filters"),
  dataDefinition: document.querySelector("#data-definition"),
  sampleSummary: document.querySelector("#sample-summary"),
  sampleBars: document.querySelector("#sample-bars"),
  workflowLine: document.querySelector("#workflow-line"),
  workflowDetail: document.querySelector("#workflow-detail"),
  modelTabs: document.querySelector("#model-tabs"),
  modelViews: document.querySelector("#model-views"),
  metricsGrid: document.querySelector("#metrics-grid"),
  confusionPanel: document.querySelector("#confusion-panel"),
  featureSearch: document.querySelector("#feature-search"),
  featureList: document.querySelector("#feature-list"),
  modelLimitation: document.querySelector("#model-limitation"),
  geneTabs: document.querySelector("#gene-tabs"),
  proteinFacts: document.querySelector("#protein-facts"),
  proteinActions: document.querySelector("#protein-actions"),
  structureCard: document.querySelector("#structure-card"),
  mutationCard: document.querySelector("#mutation-card"),
  compoundSearch: document.querySelector("#compound-search"),
  compoundFilter: document.querySelector("#compound-filter"),
  compoundSort: document.querySelector("#compound-sort"),
  compoundTable: document.querySelector("#compound-table"),
  glossarySearch: document.querySelector("#glossary-search"),
  glossaryCategories: document.querySelector("#glossary-categories"),
  glossaryList: document.querySelector("#glossary-list"),
  sourceFilters: document.querySelector("#source-filters"),
  sourceTable: document.querySelector("#source-table"),
  contactForm: document.querySelector("#contact-form"),
  contactNote: document.querySelector("#contact-note")
};

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function formatNumber(value) {
  return new Intl.NumberFormat("en-US").format(value);
}

function formatScore(value) {
  return Number(value).toFixed(3).replace(/0+$/, "").replace(/\.$/, "");
}

function formulaHtml(formula) {
  return escapeHtml(formula).replace(/(\d+)/g, "<sub>$1</sub>");
}

function externalLink(url, label) {
  return `<a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(label)}</a>`;
}

async function fetchJson(url) {
  const response = await fetch(url);
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.message || "Request failed");
  return payload;
}

function setActiveNav() {
  if (!els.nav) return;
  const path = window.location.pathname;
  const page =
    path.endsWith("/data.html") ? "data" :
    path.endsWith("/biology.html") ? "biology" :
    path.endsWith("/resources.html") ? "resources" :
    "home";
  const defaultHash = {
    home: "",
    data: "#coad-data",
    biology: "#proteins",
    resources: "#glossary"
  }[page];
  const currentHash = window.location.hash || defaultHash;
  els.nav.querySelectorAll("a").forEach((link) => {
    const url = new URL(link.href, window.location.origin);
    const active = url.pathname === path && (url.hash || "") === currentHash;
    link.classList.toggle("active", active);
  });
}

function renderHeroStats() {
  if (!els.heroStats) return;
  const samples = state.data.model.samples;
  const stats = [
    {
      key: "samples",
      label: "Samples",
      value: samples.tumor + samples.normal,
      noteHtml: `<span class="tumor-count">${formatNumber(samples.tumor)}</span> Tumor<br /><span class="normal-count">${formatNumber(samples.normal)}</span> Normal`
    },
    {
      key: "data",
      label: "Data Type",
      value: "RNA-seq",
      subvalue: "(TPM)",
      noteHtml: "Gene expression<br />quantification"
    },
    {
      key: "genes",
      label: "Genes",
      value: samples.modelGenes,
      noteHtml: "After filtering<br />&amp; variance selection"
    },
    {
      key: "platforms",
      label: "Platforms",
      value: "Illumina",
      noteHtml: "HiSeq RNA-seq<br />(PanCanAtlas)"
    }
  ];

  els.heroStats.innerHTML = stats
    .map(
      (stat) => `
        <article>
          <div class="stat-top">
            <span class="stat-icon ${escapeHtml(stat.key)}" aria-hidden="true"></span>
            <span>${escapeHtml(stat.label)}</span>
          </div>
          <strong>${typeof stat.value === "number" ? formatNumber(stat.value) : escapeHtml(stat.value)}</strong>
          ${stat.subvalue ? `<em>${escapeHtml(stat.subvalue)}</em>` : ""}
          <small>${stat.noteHtml}</small>
        </article>
      `
    )
    .join("");
}

function renderDataSection() {
  if (!els.dataFilters || !els.dataDefinition || !els.sampleBars) return;
  const item = state.data.datasetSummary.find((entry) => entry.key === state.selectedDataKey);
  const rna = state.data.datasetSummary.find((entry) => entry.key === "rna");

  els.dataFilters.innerHTML = state.data.datasetSummary
    .map(
      (entry) => `
        <button type="button" data-key="${escapeHtml(entry.key)}" class="${entry.key === state.selectedDataKey ? "active" : ""}">
          <span>${escapeHtml(entry.label)}</span>
          <small>${escapeHtml(entry.description)}</small>
        </button>
      `
    )
    .join("");
  els.dataFilters.querySelectorAll("button").forEach((button) => {
    button.addEventListener("click", () => {
      state.selectedDataKey = button.dataset.key;
      renderDataSection();
    });
  });

  els.dataDefinition.innerHTML = `
    <h3>${escapeHtml(item.title)}</h3>
    <p><strong>${escapeHtml(item.label)}:</strong> ${escapeHtml(item.plainDefinition)}</p>
    <p><strong>Feature matrix:</strong> rows are samples, columns are measurable features.</p>
    <dl>
      <div><dt>Sample count</dt><dd>${item.sampleCount ? formatNumber(item.sampleCount) : "Project summary"}</dd></div>
      <div><dt>Feature count</dt><dd>${item.featureCount ? formatNumber(item.featureCount) : "Not displayed as a raw table"}</dd></div>
      <div><dt>Note</dt><dd>${escapeHtml(item.note)}</dd></div>
    </dl>
  `;

  if (els.sampleSummary) {
    els.sampleSummary.innerHTML = `
      <article><i class="dot tumor"></i><strong>${formatNumber(rna.tumorSamples)}</strong><span>Tumor samples</span></article>
      <article><i class="dot normal"></i><strong>${formatNumber(rna.normalSamples)}</strong><span>Normal samples</span></article>
      <article><i class="dot total"></i><strong>${formatNumber(rna.tumorSamples + rna.normalSamples)}</strong><span>Total samples</span></article>
    `;
  }

  if (document.body.classList.contains("page-data")) {
    els.sampleBars.classList.add("trend-chart");
    els.sampleBars.innerHTML = `
      <svg viewBox="0 0 620 250" role="img" aria-label="Tumor and normal sample trend chart">
        <defs>
          <linearGradient id="tumorFill" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0" stop-color="#ec635c" stop-opacity="0.38" />
            <stop offset="1" stop-color="#ec635c" stop-opacity="0.08" />
          </linearGradient>
          <linearGradient id="normalFill" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0" stop-color="#2b6fb3" stop-opacity="0.28" />
            <stop offset="1" stop-color="#2b6fb3" stop-opacity="0.05" />
          </linearGradient>
        </defs>
        <g class="grid-lines">
          <path d="M48 30H590M48 70H590M48 110H590M48 150H590M48 190H590" />
        </g>
        <path class="area tumor-area" d="M48 196 L88 176 L128 166 L168 146 L208 130 L248 106 L288 84 L328 66 L368 54 L408 44 L448 38 L488 32 L528 28 L590 22 L590 216 L48 216Z" />
        <path class="line tumor-line" d="M48 196 L88 176 L128 166 L168 146 L208 130 L248 106 L288 84 L328 66 L368 54 L408 44 L448 38 L488 32 L528 28 L590 22" />
        <path class="area normal-area" d="M48 208 L88 205 L128 202 L168 199 L208 196 L248 190 L288 188 L328 184 L368 182 L408 181 L448 180 L488 178 L528 176 L590 174 L590 216 L48 216Z" />
        <path class="line normal-line" d="M48 208 L88 205 L128 202 L168 199 L208 196 L248 190 L288 188 L328 184 L368 182 L408 181 L448 180 L488 178 L528 176 L590 174" />
        <g class="axis-labels">
          <text x="42" y="28">300</text><text x="42" y="108">150</text><text x="42" y="214">0</text>
          <text x="48" y="238">Tumor</text><text x="540" y="238">Normal</text>
        </g>
      </svg>
    `;
  } else {
    const max = Math.max(rna.tumorSamples, rna.normalSamples);
    els.sampleBars.innerHTML = [
      { label: "Tumor", value: rna.tumorSamples, className: "tumor" },
      { label: "Normal", value: rna.normalSamples, className: "normal" }
    ]
      .map(
        (bar) => `
          <div class="sample-row">
            <span>${escapeHtml(bar.label)}</span>
            <div><i class="${bar.className}" style="width: ${(bar.value / max) * 100}%"></i></div>
            <strong>${formatNumber(bar.value)}</strong>
          </div>
        `
      )
      .join("");
  }
}

function renderWorkflow() {
  if (!els.workflowLine || !els.workflowDetail) return;
  els.workflowLine.innerHTML = state.data.workflowSteps
    .map(
      (step) => `
        <button type="button" data-step="${step.step}" class="${step.step === state.selectedStep ? "active" : ""}">
          <span>${step.step}</span>
          <strong>${escapeHtml(step.name)}</strong>
          <small>${escapeHtml(step.short)}</small>
        </button>
      `
    )
    .join("");
  els.workflowLine.querySelectorAll("button").forEach((button) => {
    button.addEventListener("click", () => {
      state.selectedStep = Number(button.dataset.step);
      renderWorkflow();
    });
  });

  const selected = state.data.workflowSteps.find((step) => step.step === state.selectedStep);
  els.workflowDetail.innerHTML = `
    <span>Step ${selected.step}</span>
    <h3>${escapeHtml(selected.name)}</h3>
    <p>${escapeHtml(selected.details)}</p>
  `;
}

function selectedModel() {
  return state.data.model.metrics.find((item) => item.modelKey === state.selectedModelKey);
}

function renderModel() {
  if (!els.modelTabs || !els.metricsGrid || !els.confusionPanel || !els.featureList) return;
  const model = selectedModel();
  els.modelTabs.innerHTML = state.data.model.metrics
    .map(
      (entry) => `
        <button type="button" data-model="${escapeHtml(entry.modelKey)}" class="${entry.modelKey === state.selectedModelKey ? "active" : ""}">
          <span>${escapeHtml(entry.modelName)}</span>
          <small>${escapeHtml(entry.plainEnglish)}</small>
        </button>
      `
    )
    .join("");
  els.modelTabs.querySelectorAll("button").forEach((button) => {
    button.addEventListener("click", () => {
      state.selectedModelKey = button.dataset.model;
      renderModel();
    });
  });

  const metrics = [
    { label: "Accuracy", value: model.accuracy, meaning: "Proportion of all predictions that are correct." },
    { label: "Precision", value: model.precision, meaning: "Among predicted tumor samples, the proportion that are true tumor." },
    { label: "Recall", value: model.recall, meaning: "Among actual tumor samples, the proportion correctly identified." },
    { label: "F1 score", value: model.f1, meaning: "Harmonic mean of precision and recall." },
    { label: "ROC-AUC", value: model.rocAuc, meaning: "Ability to separate tumor from normal across thresholds." }
  ];
  els.metricsGrid.innerHTML = metrics
    .map(
      (metric) => `
        <article>
          <span>${escapeHtml(metric.label)}</span>
          <strong>${formatScore(metric.value)}</strong>
          <p>${escapeHtml(metric.meaning)}</p>
        </article>
      `
    )
    .join("");

  const matrix = model.confusionMatrix;
  const total = matrix.flat().reduce((sum, value) => sum + value, 0);
  els.confusionPanel.innerHTML = `
    <div class="panel-head"><h3>Confusion Matrix</h3><span>${escapeHtml(model.modelName)}</span></div>
    <div class="matrix-grid" aria-label="Confusion matrix for ${escapeHtml(model.modelName)}">
      <span></span><b>Predicted normal</b><b>Predicted tumor</b>
      <b>Actual normal</b><strong>${matrix[0][0]}</strong><strong>${matrix[0][1]}</strong>
      <b>Actual tumor</b><strong>${matrix[1][0]}</strong><strong>${matrix[1][1]}</strong>
    </div>
    <p>Total test samples: ${formatNumber(total)}. Green cells represent correct predictions.</p>
  `;

  renderFeatures();
  if (els.modelLimitation) els.modelLimitation.textContent = state.data.model.limitations.join(" ");
  if (els.modelViews) {
    els.modelViews.querySelectorAll("button").forEach((button) => {
      button.classList.toggle("active", button.dataset.view === state.selectedModelView);
    });
  }
}

function renderFeatures() {
  if (!els.featureList) return;
  const query = (els.featureSearch?.value || "").trim().toLowerCase();
  const features = state.data.model.importantFeatures
    .filter((feature) => feature.modelKey === state.selectedModelKey)
    .filter((feature) => !query || `${feature.featureName} ${feature.direction}`.toLowerCase().includes(query))
    .slice(0, 10);
  const max = Math.max(...features.map((feature) => Math.abs(feature.importanceValue)), 0.001);

  els.featureList.innerHTML =
    features
      .map(
        (feature) => `
          <article>
            <div>
              <strong>${escapeHtml(feature.featureName)}</strong>
              <span>${escapeHtml(feature.direction.replace(/_/g, " "))}</span>
            </div>
            <div class="feature-bar"><i style="width: ${(Math.abs(feature.importanceValue) / max) * 100}%"></i></div>
            <small>${formatScore(Math.abs(feature.importanceValue))}</small>
          </article>
        `
      )
      .join("") || `<p class="empty">No matching features.</p>`;
}

function renderProteins() {
  if (!els.geneTabs || !els.proteinFacts || !els.structureCard || !els.mutationCard) return;
  els.geneTabs.innerHTML = state.data.proteins
    .map(
      (protein) => `
        <button type="button" data-gene="${escapeHtml(protein.geneSymbol)}" class="${protein.geneSymbol === state.selectedGene ? "active" : ""}">
          ${escapeHtml(protein.geneSymbol)}
        </button>
      `
    )
    .join("");
  els.geneTabs.querySelectorAll("button").forEach((button) => {
    button.addEventListener("click", () => {
      state.selectedGene = button.dataset.gene;
      renderProteins();
    });
  });

  const protein = state.data.proteins.find((item) => item.geneSymbol === state.selectedGene);
  const mutations = state.data.mutationTargets.filter((item) => item.geneSymbol === state.selectedGene);
  els.proteinFacts.innerHTML = `
    <div><dt>Gene symbol</dt><dd>${escapeHtml(protein.geneSymbol)}</dd></div>
    <div><dt>Protein name</dt><dd>${escapeHtml(protein.proteinName)}</dd></div>
    <div><dt>UniProt ID</dt><dd>${escapeHtml(protein.uniprotId)}</dd></div>
    <div><dt>AlphaFold DB</dt><dd>${escapeHtml(protein.uniprotId)}</dd></div>
    <div><dt>MutationMapper</dt><dd>${escapeHtml(protein.geneSymbol)}</dd></div>
    <div><dt>Mutation or hotspot</dt><dd><span class="hotspot-pill">${escapeHtml(protein.hotspotLabel.split(" / ")[0])}</span></dd></div>
    <div><dt>Why this protein is shown</dt><dd>${escapeHtml(protein.projectReason)}</dd></div>
  `;
  if (els.proteinActions) {
    els.proteinActions.innerHTML = `
      ${externalLink(protein.alphafoldUrl, "Open AlphaFold DB")}
      ${externalLink(protein.mutationMapperUrl, "Open cBioPortal MutationMapper")}
    `;
  }

  els.structureCard.innerHTML = `
    <div class="structure-tabs"><button class="active" type="button">Structure (AlphaFold)</button><button type="button">Mutation Map</button></div>
    <div class="panel-head">
      <h3>${escapeHtml(protein.geneSymbol)} (AlphaFold model)</h3>
      <span>AF model / ${escapeHtml(protein.uniprotId)}</span>
    </div>
    <div class="protein-visual" aria-hidden="true">
      <span class="ribbon r1"></span>
      <span class="ribbon r2"></span>
      <span class="ribbon r3"></span>
      <b>${escapeHtml(protein.hotspotLabel.split(" / ")[0])}</b>
    </div>
    <p>${escapeHtml(protein.structureNote)}</p>
  `;

  const maxPosition = Math.max(...mutations.map((mutation) => mutation.position), 200);
  els.mutationCard.innerHTML = `
    <div class="panel-head">
      <h3>${escapeHtml(protein.geneSymbol)} mutation locations</h3>
      <span>MutationMapper context</span>
    </div>
    <div class="domain-track"><span>1</span><span>50</span><span>100</span><span>${maxPosition}</span></div>
    <div class="mutation-track" aria-label="Mutation locations for ${escapeHtml(protein.geneSymbol)}">
      ${mutations
        .map(
          (mutation) => `
            <span style="left: ${Math.min((mutation.position / maxPosition) * 92 + 4, 96)}%">
              <i></i><b>${escapeHtml(mutation.proteinChange)}</b>
            </span>
          `
        )
        .join("")}
    </div>
    <ul>
      ${mutations
        .map(
          (mutation) => `<li>${escapeHtml(mutation.proteinChange)} - ${formatNumber(mutation.sampleCount)} mutated samples - ${escapeHtml(mutation.mutationLabel)}</li>`
        )
        .join("")}
    </ul>
    <p>Each marker shows a mutation position on the protein.</p>
  `;
}

function renderCompounds() {
  if (!els.compoundTable) return;
  if (els.compoundFilter && !els.compoundFilter.dataset.ready) {
    const labels = ["all", ...new Set(state.data.compounds.map((item) => item.evidenceLabel))];
    els.compoundFilter.innerHTML = labels
      .map((label) => `<option value="${escapeHtml(label)}">${label === "all" ? "Evidence label" : escapeHtml(label)}</option>`)
      .join("");
    els.compoundFilter.dataset.ready = "true";
  }
  const query = state.compoundQuery.toLowerCase();
  const compounds = [...state.data.compounds]
    .filter((item) => state.compoundEvidence === "all" || item.evidenceLabel === state.compoundEvidence)
    .filter((item) => !query || `${item.compoundName} ${item.chemblId} ${item.molecularFormula}`.toLowerCase().includes(query))
    .sort((a, b) => {
      const key = state.compoundSort === "formula" ? "molecularFormula" : "compoundName";
      return a[key].localeCompare(b[key]);
    });

  els.compoundTable.innerHTML =
    compounds
      .map(
        (item) => `
          <tr>
            <td>${escapeHtml(item.compoundName)}</td>
            <td>${externalLink(`https://www.ebi.ac.uk/chembl/compound_report_card/${item.chemblId}/`, item.chemblId)}</td>
            <td><code>${formulaHtml(item.molecularFormula)}</code></td>
            <td><span class="tag">${escapeHtml(item.evidenceLabel)}</span></td>
            <td>${escapeHtml(item.sourceNote)}</td>
          </tr>
        `
      )
      .join("") || `<tr><td colspan="5">No matching compounds.</td></tr>`;
}

function renderGlossary() {
  if (!els.glossaryList || !els.glossaryCategories) return;
  const counts = state.data.glossary.reduce((acc, term) => {
    acc[term.category] = (acc[term.category] || 0) + 1;
    return acc;
  }, {});
  const categories = [{ key: "all", label: "All terms", count: state.data.glossary.length }].concat(
    Object.entries(counts).map(([key, count]) => ({ key, label: key.replace(/\b\w/g, (letter) => letter.toUpperCase()), count }))
  );

  els.glossaryCategories.innerHTML = categories
    .map(
      (category) => `
        <button type="button" data-category="${escapeHtml(category.key)}" class="${category.key === state.glossaryCategory ? "active" : ""}">
          <span>${escapeHtml(category.label)}</span><strong>${category.count}</strong>
        </button>
      `
    )
    .join("");
  els.glossaryCategories.querySelectorAll("button").forEach((button) => {
    button.addEventListener("click", () => {
      state.glossaryCategory = button.dataset.category;
      renderGlossary();
    });
  });

  const query = state.glossaryQuery.toLowerCase();
  const terms = state.data.glossary
    .filter((term) => state.glossaryCategory === "all" || term.category === state.glossaryCategory)
    .filter((term) => !query || `${term.term} ${term.definition} ${term.projectContext}`.toLowerCase().includes(query));

  els.glossaryList.innerHTML =
    terms
      .map(
        (term, index) => `
          <details>
            <summary>
              <strong>${escapeHtml(term.term)}</strong>
              <span><b>Plain-language definition</b>${escapeHtml(term.definition)}</span>
              <span><b>Where it appears</b>${escapeHtml(term.projectContext)}</span>
            </summary>
            <div>
              <p><b>Category:</b> ${escapeHtml(term.category)}</p>
              <p>${escapeHtml(term.definition)}</p>
              <p>${escapeHtml(term.projectContext)}</p>
            </div>
          </details>
        `
      )
      .join("") || `<p class="empty">No matching glossary terms.</p>`;
}

function renderSources() {
  if (!els.sourceFilters || !els.sourceTable) return;
  const types = ["all", ...new Set(state.data.references.map((item) => item.type))];
  els.sourceFilters.innerHTML = types
    .map(
      (type) => `
        <button type="button" data-type="${escapeHtml(type)}" class="${type === state.sourceType ? "active" : ""}">
          ${type === "all" ? "All" : escapeHtml(type)}
        </button>
      `
    )
    .join("");
  els.sourceFilters.querySelectorAll("button").forEach((button) => {
    button.addEventListener("click", () => {
      state.sourceType = button.dataset.type;
      renderSources();
    });
  });

  const references = state.data.references.filter((item) => state.sourceType === "all" || item.type === state.sourceType);
  els.sourceTable.innerHTML = references
    .map(
      (item) => `
        <tr>
          <td>${escapeHtml(item.name)}</td>
          <td><span class="tag cool">${escapeHtml(item.type)}</span></td>
          <td>${escapeHtml(item.usedFor)}</td>
          <td>${externalLink(item.url, item.url.replace(/^https?:\/\//, ""))}</td>
          <td>${escapeHtml(item.accessDate)}</td>
          <td>${escapeHtml(item.citationNote)}</td>
        </tr>
      `
    )
    .join("");
}

async function loadContact() {
  if (!els.contactNote && !els.contactForm) return;
  try {
    const payload = await fetchJson("/api/contact");
    state.contactEmail = payload.email;
    if (els.contactNote) els.contactNote.textContent = `${payload.message} If nothing opens, email ${payload.email}.`;
  } catch (_error) {
    if (els.contactNote) els.contactNote.textContent = `This form uses your email app. If nothing opens, email ${state.contactEmail}.`;
  }
}

function bindEvents() {
  setActiveNav();
  window.addEventListener("hashchange", setActiveNav);
  if (els.menuButton && els.nav) {
    els.menuButton.addEventListener("click", () => {
      const expanded = els.menuButton.getAttribute("aria-expanded") === "true";
      els.menuButton.setAttribute("aria-expanded", String(!expanded));
      els.nav.classList.toggle("open", !expanded);
    });
    els.nav.querySelectorAll("a").forEach((link) => {
      link.addEventListener("click", () => {
        els.nav.classList.remove("open");
        els.menuButton.setAttribute("aria-expanded", "false");
      });
    });
  }
  els.modelViews?.querySelectorAll("button").forEach((button) => {
    button.addEventListener("click", () => {
      state.selectedModelView = button.dataset.view;
      renderModel();
    });
  });
  els.featureSearch?.addEventListener("input", renderFeatures);
  els.compoundSearch?.addEventListener("input", () => {
    state.compoundQuery = els.compoundSearch.value;
    renderCompounds();
  });
  els.compoundFilter?.addEventListener("change", () => {
    state.compoundEvidence = els.compoundFilter.value;
    renderCompounds();
  });
  els.compoundSort?.addEventListener("change", () => {
    state.compoundSort = els.compoundSort.value;
    renderCompounds();
  });
  els.glossarySearch?.addEventListener("input", () => {
    state.glossaryQuery = els.glossarySearch.value;
    renderGlossary();
  });
  els.contactForm?.addEventListener("submit", (event) => {
    event.preventDefault();
    const form = new FormData(els.contactForm);
    const name = form.get("name") || "Website visitor";
    const from = form.get("email") || "";
    const message = form.get("message") || "";
    const subject = encodeURIComponent("COAD Cancer Predictor feedback");
    const body = encodeURIComponent(`Name: ${name}\nEmail: ${from}\n\n${message}`);
    window.location.href = `mailto:${state.contactEmail}?subject=${subject}&body=${body}`;
  });
}

async function init() {
  bindEvents();
  try {
    state.data = await fetchJson("/api/site-data");
    renderHeroStats();
    renderDataSection();
    renderWorkflow();
    renderModel();
    renderProteins();
    renderCompounds();
    renderGlossary();
    renderSources();
    await loadContact();
  } catch (error) {
    document.body.insertAdjacentHTML("afterbegin", `<div class="load-error">Unable to load COAD project data: ${escapeHtml(error.message)}</div>`);
  }
}

init();
