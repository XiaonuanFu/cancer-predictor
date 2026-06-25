const state = {
  data: null,
  selectedDataKey: "clinical",
  selectedStep: 1,
  selectedGene: "KRAS",
  compoundQuery: "",
  compoundEvidence: "all",
  compoundSort: "name",
  glossaryQuery: "",
  glossaryCategory: "all",
  sourceType: "all",
  contactEmail: "cookiekat987@gmail.com"
};

const els = {
  menuButton: document.querySelector(".menu-button"),
  nav: document.querySelector("#primary-nav"),
  heroStats: document.querySelector("#hero-stats"),
  dataFilters: document.querySelector("#data-filters"),
  dataReport: document.querySelector("#data-report"),
  dataDefinition: document.querySelector("#data-definition"),
  sampleSummary: document.querySelector("#sample-summary"),
  sampleBars: document.querySelector("#sample-bars"),
  workflowLine: document.querySelector("#workflow-line"),
  workflowDetail: document.querySelector("#workflow-detail"),
  modelSampleGrid: document.querySelector("#model-sample-grid"),
  modelComparison: document.querySelector("#model-comparison"),
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

const chartInstances = new Map();

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

function chartColor(name, fallback) {
  const value = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  return value || fallback;
}

function chartPalette() {
  return [
    chartColor("--green", "#0f473d"),
    chartColor("--blue", "#2b6fb3"),
    chartColor("--coral", "#ec635c"),
    "#7b8f8a",
    "#b8a25b",
    "#6b7fa8"
  ];
}

function disposeDataCharts() {
  chartInstances.forEach((chart, id) => {
    if (id.startsWith("coad-data-")) {
      chart.dispose();
      chartInstances.delete(id);
    }
  });
}

function resizeCharts() {
  chartInstances.forEach((chart) => chart.resize());
  if (document.body.classList.contains("page-data") && state.data?.coadDataPage) {
    window.clearTimeout(resizeCharts.timer);
    resizeCharts.timer = window.setTimeout(renderDataSection, 140);
  }
}

async function fetchJson(url) {
  const response = await fetch(url);
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.message || "Request failed");
  return payload;
}

function setActiveNav() {
  if (!els.nav) return;
  const path = window.location.pathname.replace(/\/+$/, "") || "/";
  const pageMap = {
    "/": "home",
    "/index.html": "home",
    "/data.html": "data",
    "/model.html": "model",
    "/mutation-analysis.html": "mutation",
    "/glossary.html": "glossary",
    "/sources.html": "sources",
    "/about.html": "about"
  };
  const page = pageMap[path] || "home";
  els.nav.querySelectorAll("a").forEach((link) => {
    link.classList.toggle("active", link.dataset.nav === page);
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

function chartCardHtml(chart) {
  const chartId = `coad-data-${chart.id}`;
  const media =
    chart.type === "image"
      ? `<figure class="notebook-figure"><img src="${escapeHtml(chart.imageSrc)}" alt="${escapeHtml(chart.imageAlt)}" /></figure>`
      : chart.type === "boxSummary"
        ? `<div class="tmb-summary">${chart.data
            .map((item) => `<article><span>${escapeHtml(item.label)}</span><strong>${formatNumber(item.value)}</strong></article>`)
            .join("")}</div>`
        : `<div class="echart-canvas" id="${escapeHtml(chartId)}" role="img" aria-label="${escapeHtml(chart.title)}"></div>`;

  return `
    <section class="data-chart-card ${chart.type === "image" ? "notebook-card" : ""}">
      <div class="data-chart-head">
        <h3>${escapeHtml(chart.title)}</h3>
        <span>${chart.type === "image" ? "Notebook figure" : chart.type === "boxSummary" ? "Summary" : "ECharts"}</span>
      </div>
      ${media}
      <p>${escapeHtml(chart.takeaway)}</p>
    </section>
  `;
}

function baseChartOption(chart) {
  return {
    color: chartPalette(),
    animationDuration: 700,
    grid: { left: 58, right: 24, top: 34, bottom: 54, containLabel: true },
    tooltip: { trigger: "item", confine: true },
    textStyle: { color: "#243935", fontFamily: "Avenir Next, Helvetica Neue, sans-serif" }
  };
}

function chartOption(chart) {
  const option = baseChartOption(chart);
  const labels = chart.data?.map((item) => item.label) || [];
  const values = chart.data?.map((item) => item.value) || [];

  if (chart.type === "donut") {
    return {
      ...option,
      legend: { bottom: 0, itemWidth: 10, itemHeight: 10 },
      series: [
        {
          name: chart.title,
          type: "pie",
          radius: ["48%", "72%"],
          center: ["50%", "44%"],
          avoidLabelOverlap: true,
          label: { formatter: "{b}: {c}" },
          data: chart.data.map((item) => ({ name: item.label, value: item.value }))
        }
      ]
    };
  }

  if (chart.type === "horizontalBar" || chart.type === "horizontalBarPercent") {
    return {
      ...option,
      grid: { left: 118, right: 36, top: 28, bottom: 38, containLabel: true },
      tooltip: {
        trigger: "axis",
        axisPointer: { type: "shadow" },
        formatter: (params) => {
          const item = chart.data[params[0].dataIndex];
          const extra = item.percent == null ? "" : ` (${item.percent}%)`;
          return `${escapeHtml(item.label)}<br />${formatNumber(item.value)}${extra}`;
        }
      },
      xAxis: { type: "value", name: chart.xLabel || "", nameLocation: "middle", nameGap: 28, axisLine: { lineStyle: { color: "#9eb7b2" } } },
      yAxis: { type: "category", inverse: true, data: labels, axisTick: { show: false }, axisLine: { lineStyle: { color: "#9eb7b2" } } },
      series: [
        {
          type: "bar",
          data: values,
          barMaxWidth: 18,
          itemStyle: {
            borderRadius: [0, 5, 5, 0],
            color: (params) => (values[params.dataIndex] < 0 ? chartColor("--blue", "#2b6fb3") : chartColor("--coral", "#ec635c"))
          },
          label: {
            show: true,
            position: "right",
            formatter: (params) => {
              const item = chart.data[params.dataIndex];
              return item.percent == null ? formatNumber(item.value) : `${formatNumber(item.value)} / ${item.percent}%`;
            }
          }
        }
      ]
    };
  }

  if (chart.type === "groupedBar") {
    return {
      ...option,
      legend: { top: 0 },
      tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
      xAxis: { type: "category", data: chart.categories, axisTick: { show: false }, axisLine: { lineStyle: { color: "#9eb7b2" } } },
      yAxis: { type: "value", name: chart.yLabel || "", max: 100, axisLine: { lineStyle: { color: "#9eb7b2" } }, splitLine: { lineStyle: { color: "rgba(158, 183, 178, 0.28)" } } },
      series: chart.series.map((entry) => ({ name: entry.name, type: "bar", data: entry.values, barMaxWidth: 22, label: { show: true, position: "top", formatter: "{c}%" } }))
    };
  }

  if (chart.type === "forest") {
    const narrow = window.matchMedia("(max-width: 620px)").matches;
    if (narrow) {
      const shortLabels = ["Age/10y", "Male/Female", "Stage level"];
      return {
        ...option,
        grid: { left: 46, right: 18, top: 22, bottom: 70, containLabel: true },
        tooltip: {
          trigger: "axis",
          axisPointer: { type: "shadow" },
          formatter: (params) => {
            const item = chart.data[params[0].dataIndex];
            return `${escapeHtml(item.label)}<br />HR ${item.value} (${item.low}-${item.high})<br />p = ${escapeHtml(item.p)}`;
          }
        },
        xAxis: {
          type: "category",
          data: shortLabels,
          axisLabel: { interval: 0, rotate: 18 },
          axisTick: { show: false },
          axisLine: { lineStyle: { color: "#9eb7b2" } }
        },
        yAxis: {
          type: "value",
          name: "HR",
          axisLine: { lineStyle: { color: "#9eb7b2" } },
          splitLine: { lineStyle: { color: "rgba(158, 183, 178, 0.28)" } }
        },
        series: [
          {
            type: "bar",
            data: values,
            barMaxWidth: 34,
            itemStyle: { borderRadius: [5, 5, 0, 0], color: chartColor("--green", "#0f473d") },
            label: { show: true, position: "top", formatter: (params) => `HR ${params.value}` }
          }
        ]
      };
    }

    return {
      ...option,
      grid: { left: 170, right: 40, top: 30, bottom: 42, containLabel: true },
      tooltip: {
        trigger: "axis",
        axisPointer: { type: "shadow" },
        formatter: (params) => {
          const item = chart.data[params[0].dataIndex];
          return `${escapeHtml(item.label)}<br />HR ${item.value} (${item.low}-${item.high})<br />p = ${escapeHtml(item.p)}`;
        }
      },
      xAxis: { type: "value", name: chart.xLabel, nameLocation: "middle", nameGap: 30, axisLine: { lineStyle: { color: "#9eb7b2" } }, splitLine: { lineStyle: { color: "rgba(158, 183, 178, 0.28)" } } },
      yAxis: { type: "category", inverse: true, data: labels, axisTick: { show: false }, axisLine: { lineStyle: { color: "#9eb7b2" } } },
      series: [
        {
          type: "bar",
          data: values,
          barMaxWidth: 18,
          itemStyle: { borderRadius: [0, 5, 5, 0], color: chartColor("--green", "#0f473d") },
          label: { show: true, position: "right", formatter: (params) => `HR ${params.value}` }
        }
      ]
    };
  }

  return {
    ...option,
    tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
    xAxis: { type: "category", data: labels, axisLabel: { interval: 0, rotate: labels.length > 4 ? 28 : 0 }, axisTick: { show: false }, axisLine: { lineStyle: { color: "#9eb7b2" } } },
    yAxis: { type: "value", name: chart.yLabel || "", axisLine: { lineStyle: { color: "#9eb7b2" } }, splitLine: { lineStyle: { color: "rgba(158, 183, 178, 0.28)" } } },
    series: [
      {
        type: "bar",
        data: values,
        barMaxWidth: 34,
        itemStyle: { borderRadius: [5, 5, 0, 0], color: chartColor("--green", "#0f473d") },
        label: { show: true, position: "top", formatter: (params) => formatNumber(params.value) }
      }
    ]
  };
}

function renderDataCharts(section) {
  disposeDataCharts();
  if (!window.echarts) {
    els.dataReport?.querySelectorAll(".echart-canvas").forEach((node) => {
      node.innerHTML = `<p class="chart-fallback">Chart library unavailable. Use the matching notebook figure if this remains blank.</p>`;
    });
    return;
  }

  section.charts
    .filter((chart) => !["image", "boxSummary"].includes(chart.type))
    .forEach((chart) => {
      const id = `coad-data-${chart.id}`;
      const node = document.getElementById(id);
      if (!node) return;
      const instance = window.echarts.init(node, null, { renderer: "canvas" });
      instance.setOption(chartOption(chart));
      chartInstances.set(id, instance);
    });
}

function renderDataSection() {
  if (!els.dataFilters || !els.dataReport || !state.data?.coadDataPage) return;
  const sections = state.data.coadDataPage.sections;
  const section = sections.find((entry) => entry.key === state.selectedDataKey) || sections[0];
  state.selectedDataKey = section.key;

  els.dataFilters.innerHTML = sections
    .map(
      (entry) => `
        <button type="button" role="tab" aria-selected="${entry.key === section.key}" data-key="${escapeHtml(entry.key)}" class="${entry.key === section.key ? "active" : ""}">
          <span>${escapeHtml(entry.label)}</span>
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

  els.dataReport.innerHTML = `
    <header class="data-report-head">
      <a class="data-source-link" href="${escapeHtml(section.notebookUrl)}" target="_blank" rel="noopener noreferrer">
        View notebook on GitHub
      </a>
      <h1>${escapeHtml(section.title)}</h1>
      <p><strong>${escapeHtml(section.sourceReport)}</strong> ${escapeHtml(section.summary)}</p>
    </header>
    <div class="data-definition-note">
      <strong>Plain meaning</strong>
      <p>${escapeHtml(section.plainDefinition)}</p>
    </div>
    <div class="data-metric-grid">
      ${section.metrics
        .map(
          (metric) => `
            <article>
              <span>${escapeHtml(metric.label)}</span>
              <strong>${typeof metric.value === "number" ? formatNumber(metric.value) : escapeHtml(metric.value)}</strong>
              <p>${escapeHtml(metric.note)}</p>
            </article>
          `
        )
        .join("")}
    </div>
    <div class="data-chart-grid">
      ${section.charts.map(chartCardHtml).join("")}
    </div>
  `;

  renderDataCharts(section);
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

function modelMetrics(model) {
  return [
    { label: "Accuracy", value: model.accuracy, meaning: "Proportion of all predictions that are correct." },
    { label: "Balanced accuracy", value: model.balancedAccuracy, meaning: "Average performance across tumor and normal classes." },
    { label: "Precision", value: model.precision, meaning: "Among predicted tumor samples, the proportion that are true tumor." },
    { label: "Recall", value: model.recall, meaning: "Among actual tumor samples, the proportion correctly identified." },
    { label: "F1 score", value: model.f1, meaning: "A combined score using precision and recall." },
    { label: "ROC-AUC", value: model.rocAuc, meaning: "How well the model separates tumor and normal across thresholds." }
  ];
}

function featureDirectionLabel(direction) {
  if (direction === "tree_importance") return "tree importance";
  return direction.replace(/_/g, " ");
}

function modelFeatureNote(modelKey) {
  if (modelKey === "random_forest") {
    return "Feature importance shows how much the gene helped tree splits. It is relative within this model.";
  }
  return "Positive or negative weights show which direction the feature pushed the prediction.";
}

function renderModelSamples(modelData) {
  if (!els.modelSampleGrid) return;
  const samples = modelData.samples;
  const items = [
    { label: "Tumor samples", value: samples.tumor, note: "Primary tumor samples." },
    { label: "Normal samples", value: samples.normal, note: "Solid tissue normal samples." },
    { label: "Shared genes", value: samples.sharedGenes, note: "Before filtering." },
    { label: "Model genes", value: samples.modelGenes, note: "After low-variance filtering." }
  ];

  els.modelSampleGrid.innerHTML = items
    .map(
      (item) => `
        <article>
          <span>${escapeHtml(item.label)}</span>
          <strong>${typeof item.value === "number" ? formatNumber(item.value) : escapeHtml(item.value)}</strong>
          <p>${escapeHtml(item.note)}</p>
        </article>
      `
    )
    .join("");
}

function renderModelCard(model, importantFeatures) {
  const matrix = model.confusionMatrix;
  const total = matrix.flat().reduce((sum, value) => sum + value, 0);
  const features = importantFeatures.filter((feature) => feature.modelKey === model.modelKey).slice(0, 10);
  const maxFeature = Math.max(...features.map((feature) => Math.abs(feature.importanceValue)), 0.001);
  const featureItems =
    features
      .map(
        (feature) => `
          <article>
            <div>
              <strong>${escapeHtml(feature.featureName)}</strong>
              <span>${escapeHtml(featureDirectionLabel(feature.direction))}</span>
            </div>
            <div class="feature-bar"><i style="width: ${(Math.abs(feature.importanceValue) / maxFeature) * 100}%"></i></div>
            <small>${formatScore(Math.abs(feature.importanceValue))}</small>
          </article>
        `
      )
      .join("") || `<p class="empty">No important features are available for this model yet.</p>`;

  return `
    <article class="model-card-full">
      <div class="model-card-head">
        <span>Baseline model</span>
        <h3>${escapeHtml(model.modelName)}</h3>
        <p>${escapeHtml(model.plainEnglish)}</p>
      </div>
      <div class="model-metrics-list">
        ${modelMetrics(model)
          .map(
            (metric) => `
              <div title="${escapeHtml(metric.meaning)}">
                <span>${escapeHtml(metric.label)}</span>
                <strong>${formatScore(metric.value)}</strong>
              </div>
            `
          )
          .join("")}
      </div>
      <div class="model-card-section">
        <h4>Confusion Matrix</h4>
        <div class="matrix-grid model-matrix" aria-label="Confusion matrix for ${escapeHtml(model.modelName)}">
          <span></span><b>Predicted normal</b><b>Predicted tumor</b>
          <b>Actual normal</b><strong>${matrix[0][0]}</strong><strong>${matrix[0][1]}</strong>
          <b>Actual tumor</b><strong>${matrix[1][0]}</strong><strong>${matrix[1][1]}</strong>
        </div>
        <p>Total test samples: ${formatNumber(total)}. Diagonal cells are correct predictions.</p>
      </div>
      <div class="model-card-section">
        <h4>Important Features</h4>
        <p>${escapeHtml(modelFeatureNote(model.modelKey))}</p>
        <div class="feature-list model-feature-list">${featureItems}</div>
      </div>
    </article>
  `;
}

function renderModel() {
  if (!state.data?.model) return;
  const modelData = state.data.model;
  renderModelSamples(modelData);

  if (els.modelComparison) {
    els.modelComparison.innerHTML = modelData.metrics
      .map((model) => renderModelCard(model, modelData.importantFeatures))
      .join("");
  }

  if (els.modelLimitation) {
    const extraLimitations = [
      "The classes are imbalanced: 471 tumor samples vs 41 normal samples.",
      "The earlier TCGA + UCSC Xena 100% accuracy suggested possible overfitting or batch-effect learning.",
      "Important genes are predictive signals, not proof that a gene causes cancer."
    ];
    els.modelLimitation.innerHTML = [...modelData.limitations, ...extraLimitations]
      .map((item) => `<li>${escapeHtml(item)}</li>`)
      .join("");
  }
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
  window.addEventListener("resize", resizeCharts);
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
    const subject = encodeURIComponent("COAD Project feedback");
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
