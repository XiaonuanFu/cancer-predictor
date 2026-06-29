const state = {
  data: null,
  selectedDataKey: "clinical",
  selectedStep: 1,
  selectedGene: "KRAS",
  compoundQuery: "",
  compoundEvidence: "all",
  compoundSort: "name",
  mutationGenes: [],
  mutationTypes: [],
  mutationDetails: [],
  mutationGeneFilter: "all",
  mutationTypeFilter: "all",
  mutationPage: 1,
  mutationPageSize: 50,
  mutationTotalRows: 0,
  mutationTotalPages: 1,
  selectedMutationDetail: null,
  mutationHotspots: [],
  mutationLocationMutations: [],
  mutationMapperZoom: 1,
  mutationMapperYMax: null,
  mutationMapperAnnotation: "domains",
  mutationMapperShowLegend: true,
  mutationDrugs: [],
  mutationDrugQuery: "",
  mutationDrugEvidence: "all",
  mutationDrugSort: "drug",
  drawerLastFocus: null,
  glossaryQuery: "",
  glossaryCategory: "all",
  sourceType: "all",
  contactEmail: "nancy.fu.2027@this.edu.cn"
};

const MUTATION_TYPE_STYLES = {
  Missense_Mutation: { color: "#13883b", label: "Missense" },
  Nonsense_Mutation: { color: "#202628", label: "Nonsense" },
  Frame_Shift_Del: { color: "#d16a20", label: "Frameshift deletion" },
  Frame_Shift_Ins: { color: "#e0872e", label: "Frameshift insertion" },
  In_Frame_Del: { color: "#2f71b7", label: "In-frame deletion" },
  In_Frame_Ins: { color: "#178a91", label: "In-frame insertion" },
  Splice_Site: { color: "#7c4ca5", label: "Splice site" },
  Translation_Start_Site: { color: "#bf4f79", label: "Translation start" },
  Nonstop_Mutation: { color: "#8b5738", label: "Nonstop" },
  default: { color: "#697477", label: "Other" }
};

const PROTEIN_DOMAIN_TRACKS = {
  APC: [
    { startCodon: 1, endCodon: 55, label: "Oligomerization", color: "#31b8a4" },
    { startCodon: 453, endCodon: 767, label: "Armadillo repeats", color: "#5a7be7" },
    { startCodon: 1020, endCodon: 1169, label: "15-aa repeats", color: "#ef795e" },
    { startCodon: 1265, endCodon: 2035, label: "20-aa repeats", color: "#d9a72f" },
    { startCodon: 2200, endCodon: 2400, label: "Basic region", color: "#72a74c" }
  ],
  TP53: [
    { startCodon: 1, endCodon: 61, label: "Transactivation", color: "#31b8a4" },
    { startCodon: 64, endCodon: 92, label: "Proline-rich", color: "#ef795e" },
    { startCodon: 94, endCodon: 292, label: "DNA-binding", color: "#5a7be7" },
    { startCodon: 325, endCodon: 356, label: "Tetramerization", color: "#d9a72f" },
    { startCodon: 363, endCodon: 393, label: "Regulatory", color: "#72a74c" }
  ],
  KRAS: [
    { startCodon: 1, endCodon: 166, label: "Small GTPase", color: "#5a7be7" },
    { startCodon: 167, endCodon: 189, label: "Hypervariable", color: "#ef795e" }
  ],
  BRAF: [
    { startCodon: 151, endCodon: 232, label: "RAS-binding", color: "#31b8a4" },
    { startCodon: 234, endCodon: 280, label: "Cysteine-rich", color: "#ef795e" },
    { startCodon: 457, endCodon: 717, label: "Protein kinase", color: "#d9a72f" }
  ],
  PIK3CA: [
    { startCodon: 1, endCodon: 108, label: "Adaptor-binding", color: "#31b8a4" },
    { startCodon: 190, endCodon: 291, label: "RAS-binding", color: "#72a74c" },
    { startCodon: 330, endCodon: 480, label: "C2", color: "#ef795e" },
    { startCodon: 517, endCodon: 694, label: "Helical", color: "#5a7be7" },
    { startCodon: 696, endCodon: 1068, label: "PI3/4-kinase", color: "#d9a72f" }
  ],
  SMAD4: [
    { startCodon: 19, endCodon: 135, label: "MH1", color: "#31b8a4" },
    { startCodon: 136, endCodon: 318, label: "Linker", color: "#ef795e" },
    { startCodon: 319, endCodon: 543, label: "MH2", color: "#5a7be7" }
  ],
  TTN: [
    { startCodon: 1, endCodon: 15300, label: "I-band repeats", color: "#31b8a4" },
    { startCodon: 15301, endCodon: 27000, label: "A-band repeats", color: "#5a7be7" },
    { startCodon: 27001, endCodon: 34350, label: "M-line region", color: "#d9a72f" }
  ]
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
  mutationGeneChart: document.querySelector("#mutation-gene-chart"),
  mutationTypeChart: document.querySelector("#mutation-type-chart"),
  mutationGeneFilter: document.querySelector("#mutation-gene-filter"),
  mutationTypeFilter: document.querySelector("#mutation-type-filter"),
  mutationDetailTable: document.querySelector("#mutation-detail-table"),
  mutationTableCount: document.querySelector("#mutation-table-count"),
  mutationPagePrev: document.querySelector("#mutation-page-prev"),
  mutationPageNext: document.querySelector("#mutation-page-next"),
  mutationPageSummary: document.querySelector("#mutation-page-summary"),
  mutationPageSize: document.querySelector("#mutation-page-size"),
  mutationStructureCard: document.querySelector("#mutation-structure-card"),
  mutationMapperCard: document.querySelector("#mutation-mapper-card"),
  mutationDrugSearch: document.querySelector("#mutation-drug-search"),
  mutationDrugFilter: document.querySelector("#mutation-drug-filter"),
  mutationDrugSort: document.querySelector("#mutation-drug-sort"),
  mutationDrugTable: document.querySelector("#mutation-drug-table"),
  drugDrawer: document.querySelector("#drug-drawer"),
  drugDrawerBackdrop: document.querySelector("#drug-drawer-backdrop"),
  drugDrawerClose: document.querySelector("#drug-drawer-close"),
  drugDrawerContent: document.querySelector("#drug-drawer-content"),
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
let mutationStructureStage = null;
let mutationStructureComponent = null;
let mutationStructureResizeObserver = null;
let mutationStructureLoadToken = 0;
let mutationPlddtColorScheme = null;
let mutationFullscreenHandler = null;

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
    textStyle: { color: "#243935", fontFamily: "Times New Roman, Times, serif" }
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

function modelParameterList(model) {
  const parameters = model.parameters || [];
  if (!parameters.length) return "";
  return `
    <dl class="model-parameter-list" aria-label="Training parameters for ${escapeHtml(model.modelName)}">
      ${parameters
        .map(
          (parameter) => `
            <div>
              <dt>${escapeHtml(parameter.name)}</dt>
              <dd>${escapeHtml(parameter.value)}</dd>
            </div>
          `
        )
        .join("")}
    </dl>
  `;
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
        ${modelParameterList(model)}
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

function formatPercent(value) {
  return `${Number(value || 0).toFixed(1).replace(/\.0$/, "")}%`;
}

function mutationPageActive() {
  return Boolean(els.mutationGeneChart || els.mutationDrugTable);
}

function mutationExternalLink(url, label) {
  if (!url) return `<span class="empty-inline">Not available</span>`;
  return externalLink(url, label);
}

function renderMutationGeneChart() {
  if (!els.mutationGeneChart) return;
  if (!window.echarts) {
    els.mutationGeneChart.innerHTML = `<p class="chart-fallback">Chart library unavailable. Mutation genes are still listed in the summary panel.</p>`;
    return;
  }

  const genes = state.mutationGenes.slice(0, 12);
  const chartGenes = [...genes].reverse();
  const existing = chartInstances.get("mutation-genes");
  if (existing) {
    existing.dispose();
    chartInstances.delete("mutation-genes");
  }

  const chart = window.echarts.init(els.mutationGeneChart, null, { renderer: "canvas" });
  chart.setOption({
    color: [chartColor("--green", "#005b49")],
    tooltip: {
      trigger: "axis",
      axisPointer: { type: "shadow" },
      formatter: (params) => {
        const item = chartGenes[params[0].dataIndex];
        return `<strong>${escapeHtml(item.geneSymbol)}</strong><br/>Mutated samples: ${formatNumber(item.mutatedSampleCount)}<br/>Frequency: ${formatPercent(item.mutatedSamplePercent)}<br/>Records: ${formatNumber(item.mutationRecords)}`;
      }
    },
    grid: { left: 92, right: 94, top: 16, bottom: 42 },
    xAxis: {
      type: "value",
      name: "Mutated samples",
      nameLocation: "middle",
      nameGap: 30,
      axisLine: { lineStyle: { color: "#9eb7b2" } },
      splitLine: { lineStyle: { color: "rgba(158, 183, 178, 0.28)" } }
    },
    yAxis: {
      type: "category",
      data: chartGenes.map((item) => item.geneSymbol),
      axisTick: { show: false },
      axisLine: { lineStyle: { color: "#9eb7b2" } }
    },
    series: [
      {
        type: "bar",
        data: chartGenes.map((item) => item.mutatedSampleCount),
        barMaxWidth: 22,
        itemStyle: {
          borderRadius: [0, 6, 6, 0],
          color: (params) => {
            const gene = chartGenes[params.dataIndex];
            return gene.geneSymbol === state.mutationGeneFilter ? chartColor("--coral", "#ec635c") : chartColor("--green", "#005b49");
          }
        },
        label: {
          show: true,
          position: "right",
          formatter: (params) => {
            const item = chartGenes[params.dataIndex];
            return `${item.mutatedSampleCount} (${formatPercent(item.mutatedSamplePercent)})`;
          }
        }
      }
    ]
  });
  chart.on("click", (params) => {
    const gene = chartGenes[params.dataIndex];
    if (!gene) return;
    state.mutationGeneFilter = gene.geneSymbol;
    if (els.mutationGeneFilter) els.mutationGeneFilter.value = gene.geneSymbol;
    state.mutationPage = 1;
    state.selectedMutationDetail = null;
    state.mutationLocationMutations = [];
    renderMutationStructure();
    renderMutationMapper();
    renderMutationGeneChart();
    loadMutationTable();
  });
  chartInstances.set("mutation-genes", chart);
}

function renderMutationTypeChart() {
  if (!els.mutationTypeChart) return;
  if (!window.echarts) {
    els.mutationTypeChart.innerHTML = `<p class="chart-fallback">Chart library unavailable.</p>`;
    return;
  }

  const mutationTypes = state.mutationTypes.slice(0, 12);
  const chartTypes = [...mutationTypes].reverse();
  const existing = chartInstances.get("mutation-types");
  if (existing) {
    existing.dispose();
    chartInstances.delete("mutation-types");
  }

  const chart = window.echarts.init(els.mutationTypeChart, null, { renderer: "canvas" });
  chart.setOption({
    tooltip: {
      trigger: "axis",
      axisPointer: { type: "shadow" },
      formatter: (params) => {
        const item = chartTypes[params[0].dataIndex];
        return `<strong>${escapeHtml(item.variantClassification)}</strong><br/>Mutation records: ${formatNumber(item.mutationRecords)}<br/>Mutated samples: ${formatNumber(item.mutatedSampleCount)}<br/>Affected genes: ${formatNumber(item.affectedGeneCount)}`;
      }
    },
    grid: { left: 138, right: 32, top: 16, bottom: 42 },
    xAxis: {
      type: "value",
      name: "Mutation records",
      nameLocation: "middle",
      nameGap: 30,
      axisLine: { lineStyle: { color: "#9eb7b2" } },
      splitLine: { lineStyle: { color: "rgba(158, 183, 178, 0.28)" } }
    },
    yAxis: {
      type: "category",
      data: chartTypes.map((item) => item.variantClassification),
      axisTick: { show: false },
      axisLabel: { width: 126, overflow: "truncate" },
      axisLine: { lineStyle: { color: "#9eb7b2" } }
    },
    series: [
      {
        type: "bar",
        data: chartTypes.map((item) => item.mutationRecords),
        barMaxWidth: 22,
        itemStyle: {
          borderRadius: [0, 6, 6, 0],
          color: (params) => {
            const item = chartTypes[params.dataIndex];
            return item.variantClassification === state.mutationTypeFilter
              ? chartColor("--coral", "#ec635c")
              : chartColor("--blue", "#2b6fb3");
          }
        },
        label: {
          show: true,
          position: "right",
          formatter: (params) => formatNumber(chartTypes[params.dataIndex].mutationRecords)
        }
      }
    ]
  });
  chart.on("click", (params) => {
    const mutationType = chartTypes[params.dataIndex];
    if (!mutationType) return;
    state.mutationTypeFilter = mutationType.variantClassification;
    if (els.mutationTypeFilter) els.mutationTypeFilter.value = mutationType.variantClassification;
    state.mutationPage = 1;
    state.selectedMutationDetail = null;
    state.mutationLocationMutations = [];
    renderMutationStructure();
    renderMutationMapper();
    renderMutationTypeChart();
    loadMutationTable();
  });
  chartInstances.set("mutation-types", chart);
}

function disposeMutationStructureViewer() {
  mutationStructureLoadToken += 1;
  mutationStructureResizeObserver?.disconnect();
  mutationStructureResizeObserver = null;
  mutationStructureComponent = null;
  if (mutationFullscreenHandler) {
    document.removeEventListener("fullscreenchange", mutationFullscreenHandler);
    mutationFullscreenHandler = null;
  }
  if (mutationStructureStage) {
    mutationStructureStage.dispose();
    mutationStructureStage = null;
  }
}

function plddtColorScheme() {
  if (mutationPlddtColorScheme || !window.NGL) return mutationPlddtColorScheme;
  mutationPlddtColorScheme = window.NGL.ColormakerRegistry.addScheme(function () {
    this.atomColor = (atom) => {
      const confidence = Number(atom.bfactor || 0);
      if (confidence > 90) return 0x0053d6;
      if (confidence > 70) return 0x65cbf3;
      if (confidence > 50) return 0xffdb13;
      return 0xff7d45;
    };
  }, "AlphaFold pLDDT confidence");
  return mutationPlddtColorScheme;
}

async function loadMutationStructureViewer(detail) {
  const viewer = document.querySelector("#alphafold-structure-viewer");
  const status = document.querySelector("#alphafold-viewer-status");
  const resetButton = document.querySelector("#alphafold-reset-view");
  const spinToggle = document.querySelector("#alphafold-spin");
  const fullscreenButton = document.querySelector("#alphafold-fullscreen");
  const viewerShell = document.querySelector(".alphafold-viewer-shell");
  if (!viewer || !status || !detail?.protein) return;

  if (!window.NGL) {
    status.textContent = "The 3D viewer library could not be loaded.";
    status.dataset.state = "error";
    viewer.setAttribute("aria-busy", "false");
    return;
  }

  const loadToken = ++mutationStructureLoadToken;
  const protein = detail.protein;
  const stage = new window.NGL.Stage(viewer, {
    backgroundColor: "#f7faf9",
    quality: protein.proteinLength && protein.proteinLength > 1200 ? "medium" : "high",
    tooltip: true
  });
  mutationStructureStage = stage;

  resetButton?.addEventListener("click", () => {
    mutationStructureComponent?.autoView(450);
  });
  spinToggle?.addEventListener("change", () => {
    stage.setSpin(Boolean(spinToggle.checked));
  });
  fullscreenButton?.addEventListener("click", async () => {
    try {
      if (document.fullscreenElement) {
        await document.exitFullscreen();
      } else if (viewerShell?.requestFullscreen) {
        await viewerShell.requestFullscreen();
      }
      window.setTimeout(() => stage.handleResize(), 120);
    } catch (_error) {
      viewerShell?.classList.toggle("fullscreen-fallback");
      document.body.classList.toggle("structure-fullscreen-open", viewerShell?.classList.contains("fullscreen-fallback"));
      window.setTimeout(() => stage.handleResize(), 120);
    }
  });
  mutationFullscreenHandler = () => {
    if (fullscreenButton) fullscreenButton.textContent = document.fullscreenElement ? "Exit full screen" : "Full screen";
    window.setTimeout(() => stage.handleResize(), 120);
  };
  document.addEventListener("fullscreenchange", mutationFullscreenHandler);

  mutationStructureResizeObserver = new ResizeObserver(() => {
    stage.handleResize();
  });
  mutationStructureResizeObserver.observe(viewer);

  try {
    const structureParams = new URLSearchParams();
    if (detail.aminoAcidPosition) structureParams.set("position", String(detail.aminoAcidPosition));
    const structureUrl = `/api/mutation-analysis/proteins/${encodeURIComponent(protein.uniprotId)}/structure${structureParams.toString() ? `?${structureParams.toString()}` : ""}`;
    const structureResponse = await fetch(structureUrl);
    if (!structureResponse.ok) {
      const payload = await structureResponse.json().catch(() => null);
      throw new Error(payload?.message || "A structure fragment is not available for this protein position.");
    }
    const structureFormat = structureResponse.headers.get("X-Structure-Format") || "pdb";
    const structureEntry = structureResponse.headers.get("X-Structure-Entry") || protein.uniprotId;
    const fragmentStart = Number(structureResponse.headers.get("X-Fragment-Start") || 0);
    const fragmentEnd = Number(structureResponse.headers.get("X-Fragment-End") || 0);
    const selectedResidueLocal = Number(structureResponse.headers.get("X-Selected-Residue-Local") || detail.aminoAcidPosition || 0);
    const structureBlob = await structureResponse.blob();
    const component = await stage.loadFile(structureBlob, { ext: structureFormat });
    if (loadToken !== mutationStructureLoadToken) {
      stage.dispose();
      return;
    }

    mutationStructureComponent = component;
    component.addRepresentation("cartoon", {
      color: plddtColorScheme(),
      quality: protein.proteinLength && protein.proteinLength > 1200 ? "medium" : "high",
      smoothSheet: true
    });

    const hotspotSelection = [state.selectedMutationDetail, ...state.mutationHotspots]
      .map((item) => {
        const position = Number(item?.aminoAcidPosition || 0);
        if (fragmentStart && fragmentEnd) {
          return position >= fragmentStart && position <= fragmentEnd ? position - fragmentStart + 1 : 0;
        }
        return position;
      })
      .filter((position) => position > 0)
      .filter((position, index, positions) => positions.indexOf(position) === index)
      .slice(0, 5)
      .join(" or ");
    const selectedPosition = selectedResidueLocal > 0 ? selectedResidueLocal : 0;
    if (hotspotSelection) {
      component.addRepresentation("ball+stick", {
        sele: hotspotSelection,
        color: "#ec635c",
        scale: 1.25
      });
    }

    component.autoView(650);
    if (selectedPosition) component.autoView(String(selectedPosition), 450);
    stage.handleResize();
    viewer.dataset.rendered = "true";
    viewer.setAttribute("aria-busy", "false");
    status.textContent = fragmentStart && fragmentEnd
      ? `${detail.geneSymbol} fragment ${formatNumber(fragmentStart)}-${formatNumber(fragmentEnd)} loaded (${structureEntry})`
      : `${detail.geneSymbol} AlphaFold structure loaded`;
    status.dataset.state = "ready";
  } catch (error) {
    if (loadToken !== mutationStructureLoadToken) return;
    stage.dispose();
    mutationStructureStage = null;
    mutationStructureComponent = null;
    viewer.setAttribute("aria-busy", "false");
    status.textContent = error instanceof Error ? `Unable to load 3D structure: ${error.message}` : "Unable to load the 3D structure.";
    status.dataset.state = "error";
  }
}

function renderMutationStructure() {
  if (!els.mutationStructureCard) return;
  disposeMutationStructureViewer();
  const detail = state.selectedMutationDetail;
  const protein = detail?.protein;
  if (!detail) {
    els.mutationStructureCard.innerHTML = `
      <div class="panel-head">
        <h2>Protein Structure</h2>
        <span>Selection required</span>
      </div>
      <p class="empty">Select a mutation row to load its corresponding protein structure.</p>
    `;
    return;
  }
  if (!protein) {
    els.mutationStructureCard.innerHTML = `
      <div class="panel-head">
        <h3>${escapeHtml(detail.geneSymbol)} protein structure</h3>
        <span>${escapeHtml(detail.proteinChange)}</span>
      </div>
      <p class="empty">A curated AlphaFold target is not available for this gene in coad_web.</p>
    `;
    return;
  }

  els.mutationStructureCard.innerHTML = `
    <div class="panel-head">
      <h3>${escapeHtml(detail.geneSymbol)} protein fragment 3D structure</h3>
      <span>${escapeHtml(protein.uniprotId)}${protein.proteinLength ? ` / ${formatNumber(protein.proteinLength)} aa` : ""}</span>
    </div>
    <p class="selected-mutation-label"><strong>${escapeHtml(detail.proteinChange)}</strong> / ${escapeHtml(detail.variantClassification)}</p>
    <div class="alphafold-viewer-shell">
      <div
        class="alphafold-structure-viewer"
        id="alphafold-structure-viewer"
        role="img"
        aria-label="Interactive AlphaFold 3D structure for ${escapeHtml(detail.geneSymbol)}"
        aria-busy="true"
      ></div>
      <div class="alphafold-viewer-toolbar">
        <button id="alphafold-reset-view" type="button" title="Reset the 3D structure orientation">Reset view</button>
        <button id="alphafold-fullscreen" type="button" title="Show the protein structure in full screen">Full screen</button>
        <label class="viewer-spin-control">
          <input id="alphafold-spin" type="checkbox" />
          <span>Spin</span>
        </label>
      </div>
      <div class="alphafold-viewer-status" id="alphafold-viewer-status" role="status" data-state="loading">
        Loading ${escapeHtml(detail.geneSymbol)} structure fragment...
      </div>
    </div>
    <div class="plddt-legend" aria-label="AlphaFold pLDDT confidence legend">
      <span><i class="plddt-very-high"></i>Very high (&gt;90)</span>
      <span><i class="plddt-confident"></i>Confident (70-90)</span>
      <span><i class="plddt-low"></i>Low (50-70)</span>
      <span><i class="plddt-very-low"></i>Very low (&lt;50)</span>
      <span><i class="plddt-hotspot"></i>COAD hotspot</span>
    </div>
    <p>${escapeHtml(protein.structureNote)}</p>
    <p>Colors show AlphaFold pLDDT confidence (how certain AlphaFold is about each amino acid position). For large proteins, the viewer loads the overlapping fragment around the selected mutation.</p>
    <div class="external-actions">
      ${mutationExternalLink(protein.alphafoldUrl, "Open AlphaFold DB")}
      ${mutationExternalLink(`https://www.cbioportal.org/mutation_mapper?standaloneMutationMapperGeneTab=${encodeURIComponent(detail.geneSymbol)}`, "Open cBioPortal Mutation Mapper")}
    </div>
  `;

  requestAnimationFrame(() => {
    loadMutationStructureViewer(detail);
  });
}

function buildCbioportalLollipopData(detail, mutations, proteinLength) {
  const sortedForLabels = [...mutations].sort((a, b) => (b.sampleCount || 0) - (a.sampleCount || 0));
  const selectedKey = `${detail.aminoAcidPosition}:${detail.proteinChange}`;
  const selectedPosition = Number(detail.aminoAcidPosition || 0);
  const labelledPositions = selectedPosition > 0 ? [selectedPosition] : [];
  const labelSet = new Set(selectedPosition > 0 ? [selectedKey] : []);
  const minimumLabelGap = Math.max(1, proteinLength / 18);
  sortedForLabels.forEach((mutation) => {
    if (labelSet.size >= 7) return;
    const position = Number(mutation.aminoAcidPosition || 0);
    const key = `${mutation.aminoAcidPosition}:${mutation.proteinChange}`;
    if (!position || labelSet.has(key)) return;
    if (labelledPositions.some((labelledPosition) => Math.abs(position - labelledPosition) < minimumLabelGap)) return;
    labelledPositions.push(position);
    labelSet.add(key);
  });
  const lollipops = mutations
    .filter((mutation) => Number(mutation.aminoAcidPosition || 0) > 0)
    .map((mutation) => {
      const mutationType = mutation.variantClassification || mutation.mutationLabel || "Other";
      const typeStyle = MUTATION_TYPE_STYLES[mutationType] || MUTATION_TYPE_STYLES.default;
      const selected = mutation.aminoAcidPosition === detail.aminoAcidPosition
        && mutation.proteinChange === detail.proteinChange;
      return {
        codon: Number(mutation.aminoAcidPosition),
        count: Number(mutation.sampleCount || mutation.mutationRecords || 1),
        color: typeStyle.color,
        typeLabel: typeStyle.label,
        selected,
        label: {
          text: mutation.proteinChange.replace(/^p\./, ""),
          show: labelSet.has(`${mutation.aminoAcidPosition}:${mutation.proteinChange}`) || selected
        },
        proteinChange: mutation.proteinChange,
        mutationType
      };
    });

  const domains = (PROTEIN_DOMAIN_TRACKS[detail.geneSymbol] || [])
    .map((domain) => ({
      ...domain,
      startCodon: Math.max(1, Math.min(domain.startCodon, proteinLength)),
      endCodon: Math.max(1, Math.min(domain.endCodon, proteinLength))
    }))
    .filter((domain) => domain.endCodon > domain.startCodon);

  return {
    hugoGeneSymbol: detail.geneSymbol,
    geneWidth: proteinLength,
    xMax: proteinLength,
    yMax: Math.max(...lollipops.map((item) => item.count), 1),
    lollipops,
    zoom: state.mutationMapperZoom,
    domains,
    sourceComponent: "react-mutation-mapper/LollipopPlot"
  };
}

function mutationMapperTickValues(maximum, divisions = 4) {
  const values = [];
  for (let index = 0; index <= divisions; index += 1) {
    values.push(Math.round((maximum * index) / divisions));
  }
  return [...new Set(values)];
}

function renderCbioportalLollipopPlot(plotData) {
  const width = Math.max(1040, Math.min(22000, Math.round(plotData.xMax * 0.22 * plotData.zoom)));
  const height = 390;
  const lollipopBaseY = 246;
  const domainY = 252;
  const xAxisY = 320;
  const leftPad = 76;
  const rightPad = 38;
  const topPad = 54;
  const usableWidth = width - leftPad - rightPad;
  const selectedYMax = Number(state.mutationMapperYMax);
  const yMax = Math.max(selectedYMax || plotData.yMax, 1);
  const capped = plotData.yMax > yMax;

  const xForCodon = (codon) => leftPad + Math.min(Math.max(codon / plotData.xMax, 0), 1) * usableWidth;
  const yForCount = (count) => count > 0
    ? lollipopBaseY - Math.max((Math.min(count, yMax) / yMax) * 172, 12)
    : lollipopBaseY;
  const ticks = [0, Math.round(plotData.xMax / 5), Math.round((plotData.xMax * 2) / 5), Math.round((plotData.xMax * 3) / 5), Math.round((plotData.xMax * 4) / 5), plotData.xMax];
  const yTicks = mutationMapperTickValues(yMax);
  const labelSlots = [];

  const labelFor = (lollipop) => {
    const x = xForCodon(lollipop.codon);
    let slot = 0;
    while (labelSlots[slot] !== undefined && Math.abs(x - labelSlots[slot]) < 82) slot += 1;
    labelSlots[slot] = x;
    return {
      x,
      y: Math.max(topPad - 8, yForCount(lollipop.count) - 14 - slot * 21)
    };
  };

  const presentTypes = [...new Map(
    plotData.lollipops.map((item) => [item.mutationType, { color: item.color, label: item.typeLabel }])
  ).values()];
  const domainsVisible = state.mutationMapperAnnotation === "domains" && plotData.domains.length;

  return `
    <div class="cbioportal-mutation-mapper" data-component-source="${escapeHtml(plotData.sourceComponent)}">
      <div class="mutation-mapper-canvas" style="width: ${width}px">
        ${state.mutationMapperShowLegend ? `
          <div class="mutation-mapper-legend" aria-label="Mutation type legend">
            <strong>Mutation type</strong>
            ${presentTypes.map((item) => `<span><i style="--legend-color: ${escapeHtml(item.color)}"></i>${escapeHtml(item.label)}</span>`).join("")}
            <span><i class="selected-ring"></i>Selected row</span>
          </div>
        ` : ""}
        <svg id="mutation-mapper-svg" viewBox="0 0 ${width} ${height}" style="width: ${width}px" role="img" aria-label="Mutation Mapper lollipop plot for ${escapeHtml(plotData.hugoGeneSymbol)}">
          <g class="cbio-y-axis">
            <line x1="${leftPad}" y1="${topPad}" x2="${leftPad}" y2="${lollipopBaseY}"></line>
            ${yTicks.map((tick) => {
              const y = yForCount(tick);
              return `<g><line x1="${leftPad - 7}" y1="${y}" x2="${leftPad}" y2="${y}"></line><text x="${leftPad - 12}" y="${y + 5}">${tick === yMax && capped ? `≥ ${formatNumber(tick)}` : formatNumber(tick)}</text></g>`;
            }).join("")}
            <text class="cbio-y-title" transform="translate(22 ${(topPad + lollipopBaseY) / 2}) rotate(-90)">Mutated samples</text>
          </g>
          <g class="cbio-axis">
            <line x1="${leftPad}" y1="${xAxisY}" x2="${width - rightPad}" y2="${xAxisY}"></line>
          ${ticks
            .map((tick) => {
              const x = xForCodon(tick);
              return `<g><line x1="${x}" y1="${xAxisY}" x2="${x}" y2="${xAxisY + 7}"></line><text x="${x}" y="${xAxisY + 29}">${formatNumber(tick)}</text></g>`;
            })
            .join("")}
            <text class="cbio-x-title" x="${width - rightPad}" y="${xAxisY + 54}">Amino acid position (aa)</text>
          </g>
          <g class="cbio-domains">
            <rect class="protein-backbone" x="${leftPad}" y="${domainY}" width="${usableWidth}" height="28" rx="2"></rect>
            ${domainsVisible ? plotData.domains
            .map((domain) => {
              const start = xForCodon(domain.startCodon);
              const end = xForCodon(domain.endCodon);
              const domainWidth = Math.max(end - start, 2);
              return `
                <g class="cbio-domain">
                  <g
                    class="mutation-mapper-tooltip-target"
                    tabindex="0"
                    aria-label="${escapeHtml(domain.label)}, amino acids ${formatNumber(domain.startCodon)} to ${formatNumber(domain.endCodon)}"
                    aria-describedby="mutation-mapper-tooltip"
                    data-tooltip-title="${escapeHtml(domain.label)}"
                    data-tooltip-position="Amino acids ${formatNumber(domain.startCodon)}–${formatNumber(domain.endCodon)}"
                  >
                  <rect x="${start}" y="${domainY - 7}" width="${domainWidth}" height="42" rx="2" fill="${escapeHtml(domain.color)}"></rect>
                  ${domainWidth > 68 ? `<text x="${start + domainWidth / 2}" y="${domainY + 19}">${escapeHtml(domain.label)}</text>` : ""}
                  </g>
                </g>
              `;
            })
            .join("") : ""}
          </g>
          <g class="cbio-lollipops">
            ${plotData.lollipops
            .sort((a, b) => a.codon - b.codon)
            .map((lollipop) => {
              const x = xForCodon(lollipop.codon);
              const y = yForCount(lollipop.count);
              const radius = Math.min(10, Math.max(5, 4 + Math.sqrt(lollipop.count) * 0.8));
              const label = lollipop.label.show ? labelFor(lollipop) : null;
              return `
                <g
                  class="cbio-lollipop mutation-mapper-tooltip-target${lollipop.selected ? " is-selected" : ""}"
                  tabindex="0"
                  aria-label="${escapeHtml(lollipop.proteinChange)}, position ${formatNumber(lollipop.codon)}, ${formatNumber(lollipop.count)} mutated samples, ${escapeHtml(lollipop.typeLabel)}"
                  aria-describedby="mutation-mapper-tooltip"
                  data-tooltip-title="${escapeHtml(lollipop.proteinChange)}"
                  data-tooltip-position="Position ${formatNumber(lollipop.codon)}"
                  data-tooltip-samples="${formatNumber(lollipop.count)} mutated samples"
                  data-tooltip-type="${escapeHtml(lollipop.typeLabel)}"
                >
                  <line x1="${x}" y1="${domainY}" x2="${x}" y2="${y}"></line>
                  <circle cx="${x}" cy="${y}" r="${radius}" fill="${escapeHtml(lollipop.color)}"></circle>
                  ${label ? `<text x="${label.x}" y="${label.y}">${escapeHtml(lollipop.label.text)}</text>` : ""}
                </g>
              `;
            })
            .join("")}
          </g>
        </svg>
        <div id="mutation-mapper-tooltip" class="mutation-mapper-tooltip" role="tooltip" hidden>
          <strong class="mutation-mapper-tooltip-title"></strong>
          <dl class="mutation-mapper-tooltip-details"></dl>
        </div>
      </div>
    </div>
  `;
}

function initializeMutationMapperTooltips() {
  const canvas = document.querySelector(".mutation-mapper-canvas");
  const tooltip = document.querySelector("#mutation-mapper-tooltip");
  if (!canvas || !tooltip) return;

  const title = tooltip.querySelector(".mutation-mapper-tooltip-title");
  const details = tooltip.querySelector(".mutation-mapper-tooltip-details");
  const targets = canvas.querySelectorAll(".mutation-mapper-tooltip-target");

  const positionTooltip = (event, target) => {
    const canvasRect = canvas.getBoundingClientRect();
    const scroller = canvas.closest(".cbioportal-mutation-mapper");
    const targetRect = target.getBoundingClientRect();
    const clientX = Number.isFinite(event?.clientX) && event.clientX > 0
      ? event.clientX
      : targetRect.left + targetRect.width / 2;
    const clientY = Number.isFinite(event?.clientY) && event.clientY > 0
      ? event.clientY
      : targetRect.top;
    const visibleLeft = scroller ? scroller.scrollLeft + 12 : 12;
    const visibleRight = scroller
      ? scroller.scrollLeft + scroller.clientWidth - tooltip.offsetWidth - 12
      : canvas.clientWidth - tooltip.offsetWidth - 12;
    let left = clientX - canvasRect.left + 16;
    let top = clientY - canvasRect.top - tooltip.offsetHeight - 14;

    left = Math.min(Math.max(left, visibleLeft), Math.max(visibleLeft, visibleRight));
    if (top < 8) top = clientY - canvasRect.top + 18;
    top = Math.min(Math.max(top, 8), Math.max(8, canvas.clientHeight - tooltip.offsetHeight - 8));
    tooltip.style.left = `${left}px`;
    tooltip.style.top = `${top}px`;
  };

  const showTooltip = (event) => {
    const target = event.currentTarget;
    title.textContent = target.dataset.tooltipTitle || "Mutation detail";
    details.replaceChildren();
    [
      ["Location", target.dataset.tooltipPosition],
      ["Samples", target.dataset.tooltipSamples],
      ["Type", target.dataset.tooltipType]
    ].forEach(([label, value]) => {
      if (!value) return;
      const term = document.createElement("dt");
      const description = document.createElement("dd");
      term.textContent = label;
      description.textContent = value;
      details.append(term, description);
    });
    tooltip.hidden = false;
    positionTooltip(event, target);
  };

  const hideTooltip = (event) => {
    if (event.currentTarget.matches(":focus")) return;
    tooltip.hidden = true;
  };

  targets.forEach((target) => {
    target.addEventListener("mouseenter", showTooltip);
    target.addEventListener("mousemove", (event) => positionTooltip(event, target));
    target.addEventListener("mouseleave", hideTooltip);
    target.addEventListener("focus", showTooltip);
    target.addEventListener("blur", () => {
      tooltip.hidden = true;
    });
  });
}

function downloadMutationMapperSvg(geneSymbol) {
  const svg = document.querySelector("#mutation-mapper-svg");
  if (!svg) return;
  const clone = svg.cloneNode(true);
  clone.setAttribute("xmlns", "http://www.w3.org/2000/svg");
  const style = document.createElement("style");
  style.textContent = `
    text { font-family: "Times New Roman", Times, serif; }
    .cbio-axis line, .cbio-y-axis line { stroke: #84918f; stroke-width: 1.2; }
    .cbio-axis text, .cbio-y-axis text { fill: #4d5b59; font-size: 14px; }
    .cbio-lollipop line { stroke: #9da8a5; stroke-width: 1.3; }
    .cbio-lollipop circle { stroke: #fff; stroke-width: 2; }
    .cbio-lollipop text { fill: #21302d; font-size: 13px; text-anchor: middle; }
    .protein-backbone { fill: #b9bfbc; }
    .cbio-domain text { fill: #fff; font-size: 13px; font-weight: 700; text-anchor: middle; }
  `;
  clone.prepend(style);
  const blob = new Blob([new XMLSerializer().serializeToString(clone)], { type: "image/svg+xml;charset=utf-8" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = `${geneSymbol}-mutation-mapper.svg`;
  link.click();
  URL.revokeObjectURL(link.href);
}

function renderMutationMapper() {
  if (!els.mutationMapperCard) return;
  const detail = state.selectedMutationDetail;
  if (!detail) {
    els.mutationMapperCard.innerHTML = `
      <div class="panel-head">
        <h2>Mutation Locations</h2>
        <span>Selection required</span>
      </div>
      <p class="empty">Select a mutation row to display protein positions.</p>
    `;
    return;
  }

  const mutations = [...state.mutationLocationMutations];
  if (
    detail.aminoAcidPosition
    && !mutations.some((item) => item.aminoAcidPosition === detail.aminoAcidPosition && item.proteinChange === detail.proteinChange)
  ) {
    mutations.unshift({
      mutationDetailId: detail.mutationDetailId,
      proteinChange: detail.proteinChange,
      aminoAcidPosition: detail.aminoAcidPosition,
      sampleCount: detail.mutatedSampleCount,
      mutationRecords: detail.mutationRecords,
      variantClassification: detail.variantClassification,
      mutationLabel: detail.variantClassification,
      cbioportalMutationMapperUrl: `https://www.cbioportal.org/mutation_mapper?standaloneMutationMapperGeneTab=${encodeURIComponent(detail.geneSymbol)}`
    });
  }
  if (!mutations.length) {
    els.mutationMapperCard.innerHTML = `
      <div class="panel-head">
        <h3>${escapeHtml(detail.geneSymbol)} mutation locations</h3>
        <span>MutationMapper context</span>
      </div>
      <p class="empty">No protein mutation positions are available in coad_web for this selected gene.</p>
      <div class="external-actions">
        ${mutationExternalLink(`https://www.cbioportal.org/mutation_mapper?standaloneMutationMapperGeneTab=${encodeURIComponent(detail.geneSymbol)}`, "Open cBioPortal Mutation Mapper")}
      </div>
    `;
    return;
  }

  const proteinLength = detail.protein?.proteinLength || Math.max(...mutations.map((item) => item.aminoAcidPosition || 0), 200);
  const plotData = buildCbioportalLollipopData(detail, mutations, proteinLength);
  const yControlMax = Math.max(6, Math.ceil(plotData.yMax * 1.5));
  if (!state.mutationMapperYMax) state.mutationMapperYMax = plotData.yMax;
  state.mutationMapperYMax = Math.min(Math.max(1, state.mutationMapperYMax), yControlMax);
  const listedMutations = [...mutations]
    .sort((a, b) => (b.sampleCount || 0) - (a.sampleCount || 0))
    .slice(0, 18);

  els.mutationMapperCard.innerHTML = `
    <div class="panel-head">
      <h3>${escapeHtml(detail.geneSymbol)} mutation locations</h3>
      <span>${formatNumber(plotData.lollipops.length)} positioned / ${formatNumber(mutations.length)} records</span>
    </div>
    <div class="mutation-mapper-tools">
      <label class="mutation-annotation-control">
        <span>Annotation track</span>
        <select id="mutation-mapper-annotation">
          <option value="domains" ${state.mutationMapperAnnotation === "domains" ? "selected" : ""}>Protein domains</option>
          <option value="sequence" ${state.mutationMapperAnnotation === "sequence" ? "selected" : ""}>Protein sequence only</option>
        </select>
      </label>
      <label class="mutation-y-control">
        <span>Y-axis max</span>
        <input id="mutation-mapper-y-max" type="range" min="1" max="${yControlMax}" step="1" value="${state.mutationMapperYMax}" />
        <output id="mutation-mapper-y-output">${formatNumber(state.mutationMapperYMax)}</output>
      </label>
      <label class="mutation-zoom-control">
        <span>Zoom</span>
        <input id="mutation-mapper-zoom" type="range" min="1" max="4" step="0.5" value="${state.mutationMapperZoom}" />
      </label>
      <div class="mutation-mapper-actions">
        <button id="mutation-mapper-legend-toggle" type="button" aria-pressed="${state.mutationMapperShowLegend}">
          ${state.mutationMapperShowLegend ? "Hide" : "Show"} legend
        </button>
        <button id="mutation-mapper-download" type="button">Download SVG</button>
      </div>
    </div>
    ${renderCbioportalLollipopPlot(plotData)}
    <p class="mutation-mapper-help">Each circle marks a protein change; its height is the number of COAD tumor samples. Hover over or focus a circle for details. Drag the horizontal scrollbar when the protein is zoomed.</p>
    <details class="mutation-mapper-list">
      <summary>View the ${formatNumber(listedMutations.length)} most frequent mutation locations</summary>
      <ul>
        ${listedMutations
          .map(
            (mutation) => `<li><code>${escapeHtml(mutation.proteinChange)}</code> · position ${mutation.aminoAcidPosition ? formatNumber(mutation.aminoAcidPosition) : "not available"} · ${formatNumber(mutation.sampleCount)} samples · ${escapeHtml(mutation.variantClassification || mutation.mutationLabel)}</li>`
          )
          .join("")}
      </ul>
    </details>
    <div class="external-actions">
      ${mutationExternalLink(mutations[0].cbioportalMutationMapperUrl, "Open cBioPortal Mutation Mapper")}
    </div>
  `;

  document.querySelector("#mutation-mapper-annotation")?.addEventListener("change", (event) => {
    state.mutationMapperAnnotation = event.target.value;
    renderMutationMapper();
  });
  document.querySelector("#mutation-mapper-y-max")?.addEventListener("input", (event) => {
    state.mutationMapperYMax = Number(event.target.value) || plotData.yMax;
    renderMutationMapper();
  });
  document.querySelector("#mutation-mapper-zoom")?.addEventListener("input", (event) => {
    state.mutationMapperZoom = Number(event.target.value) || 1;
    renderMutationMapper();
  });
  document.querySelector("#mutation-mapper-legend-toggle")?.addEventListener("click", () => {
    state.mutationMapperShowLegend = !state.mutationMapperShowLegend;
    renderMutationMapper();
  });
  document.querySelector("#mutation-mapper-download")?.addEventListener("click", () => {
    downloadMutationMapperSvg(detail.geneSymbol);
  });
  initializeMutationMapperTooltips();
}

function populateMutationFilters() {
  if (els.mutationGeneFilter) {
    els.mutationGeneFilter.innerHTML = [
      `<option value="all">All genes</option>`,
      ...state.mutationGenes.map((item) => `<option value="${escapeHtml(item.geneSymbol)}">${escapeHtml(item.geneSymbol)}</option>`)
    ].join("");
    els.mutationGeneFilter.value = state.mutationGeneFilter;
  }

  if (els.mutationTypeFilter) {
    els.mutationTypeFilter.innerHTML = [
      `<option value="all">All mutation types</option>`,
      ...state.mutationTypes.map((item) => `<option value="${escapeHtml(item.variantClassification)}">${escapeHtml(item.variantClassification)}</option>`)
    ].join("");
    els.mutationTypeFilter.value = state.mutationTypeFilter;
  }
}

function renderMutationTable() {
  if (!els.mutationDetailTable) return;
  const totalRows = state.mutationTotalRows || 0;
  const startRow = totalRows ? (state.mutationPage - 1) * state.mutationPageSize + 1 : 0;
  const endRow = totalRows ? Math.min(startRow + state.mutationDetails.length - 1, totalRows) : 0;
  if (els.mutationTableCount) {
    els.mutationTableCount.textContent = totalRows
      ? `Showing ${formatNumber(startRow)}-${formatNumber(endRow)} of ${formatNumber(totalRows)}`
      : "0 rows";
  }
  if (els.mutationPageSummary) {
    els.mutationPageSummary.textContent = `Page ${formatNumber(state.mutationPage)} of ${formatNumber(state.mutationTotalPages)}`;
  }
  if (els.mutationPagePrev) {
    els.mutationPagePrev.disabled = state.mutationPage <= 1;
  }
  if (els.mutationPageNext) {
    els.mutationPageNext.disabled = state.mutationPage >= state.mutationTotalPages;
  }
  if (els.mutationPageSize) {
    els.mutationPageSize.value = String(state.mutationPageSize);
  }

  els.mutationDetailTable.innerHTML = state.mutationDetails
    .map((item) => {
      const selected = item.mutationDetailId === state.selectedMutationDetail?.mutationDetailId;
      return `
        <tr
          class="${selected ? "selected" : ""}"
          data-mutation-detail-id="${item.mutationDetailId}"
          tabindex="0"
          aria-selected="${selected}"
        >
          <td>
            <input
              type="radio"
              name="mutation-detail-selection"
              value="${item.mutationDetailId}"
              aria-label="Select ${escapeHtml(item.geneSymbol)} ${escapeHtml(item.proteinChange)}"
              ${selected ? "checked" : ""}
            />
          </td>
          <td><strong>${escapeHtml(item.geneSymbol)}</strong></td>
          <td>${item.protein ? escapeHtml(item.protein.proteinName) : `<span class="empty-inline">No curated structure</span>`}</td>
          <td><code>${escapeHtml(item.proteinChange)}</code></td>
          <td>${item.aminoAcidPosition ? formatNumber(item.aminoAcidPosition) : `<span class="empty-inline">Not available</span>`}</td>
          <td>${escapeHtml(item.variantClassification)}</td>
          <td>${formatNumber(item.mutatedSampleCount)}</td>
          <td>${formatNumber(item.mutationRecords)}</td>
        </tr>
      `;
    })
    .join("") || `<tr><td colspan="8">No mutations match the selected filters.</td></tr>`;

  els.mutationDetailTable.querySelectorAll("tr[data-mutation-detail-id]").forEach((row) => {
    const selectRow = () => {
      selectMutationDetail(Number(row.dataset.mutationDetailId));
    };
    row.addEventListener("click", selectRow);
    row.addEventListener("keydown", (event) => {
      if (event.key !== "Enter" && event.key !== " ") return;
      event.preventDefault();
      selectRow();
    });
  });
}

async function loadMutationTable() {
  if (!els.mutationDetailTable) return;
  els.mutationDetailTable.innerHTML = `<tr><td colspan="8">Loading mutations from coad_web...</td></tr>`;
  if (els.mutationTableCount) els.mutationTableCount.textContent = "Loading";
  if (els.mutationPageSummary) els.mutationPageSummary.textContent = "Loading";

  const params = new URLSearchParams({
    page: String(state.mutationPage),
    pageSize: String(state.mutationPageSize)
  });
  if (state.mutationGeneFilter !== "all") params.set("geneSymbol", state.mutationGeneFilter);
  if (state.mutationTypeFilter !== "all") params.set("variantClassification", state.mutationTypeFilter);

  try {
    const payload = await fetchJson(`/api/mutation-analysis/mutations?${params.toString()}`);
    state.mutationDetails = payload.items || [];
    state.mutationTotalRows = payload.totalRows || 0;
    state.mutationPage = payload.page || state.mutationPage;
    state.mutationPageSize = payload.pageSize || state.mutationPageSize;
    state.mutationTotalPages = payload.totalPages || 1;
    if (
      state.selectedMutationDetail
      && !state.mutationDetails.some((item) => item.mutationDetailId === state.selectedMutationDetail.mutationDetailId)
    ) {
      state.selectedMutationDetail = null;
      state.mutationHotspots = [];
      state.mutationLocationMutations = [];
      renderMutationStructure();
      renderMutationMapper();
    }
    renderMutationTable();
  } catch (error) {
    state.mutationDetails = [];
    state.mutationTotalRows = 0;
    state.mutationTotalPages = 1;
    els.mutationDetailTable.innerHTML = `<tr><td colspan="8">Unable to load mutation table: ${escapeHtml(error.message)}</td></tr>`;
    if (els.mutationTableCount) els.mutationTableCount.textContent = "Unavailable";
    if (els.mutationPageSummary) els.mutationPageSummary.textContent = "Unavailable";
  }
}

async function selectMutationDetail(mutationDetailId) {
  const detail = state.mutationDetails.find((item) => item.mutationDetailId === mutationDetailId);
  if (!detail) return;

  state.selectedMutationDetail = detail;
  state.selectedGene = detail.geneSymbol;
  state.mutationHotspots = [];
  state.mutationLocationMutations = [];
  state.mutationMapperYMax = null;
  renderMutationTable();
  renderMutationStructure();
  if (els.mutationMapperCard) {
    els.mutationMapperCard.innerHTML = `<p class="empty">Loading ${escapeHtml(detail.geneSymbol)} mutation locations...</p>`;
  }

  try {
    const [hotspots, allMutations] = await Promise.all([
      fetchJson(`/api/mutation-analysis/genes/${encodeURIComponent(detail.geneSymbol)}/hotspots`),
      fetchJson(`/api/mutation-analysis/genes/${encodeURIComponent(detail.geneSymbol)}/mutations`)
    ]);
    state.mutationHotspots = hotspots;
    state.mutationLocationMutations = allMutations;
  } catch (_error) {
    state.mutationHotspots = [];
    state.mutationLocationMutations = [];
  }
  renderMutationMapper();
}

function filteredMutationDrugs() {
  const query = state.mutationDrugQuery.toLowerCase();
  return [...state.mutationDrugs]
    .filter((item) => state.mutationDrugEvidence === "all" || item.evidenceLabel === state.mutationDrugEvidence)
    .filter((item) => {
      const haystack = `${item.drugName} ${item.compoundName || ""} ${item.chemblId || ""} ${item.molecularFormula || ""}`.toLowerCase();
      return !query || haystack.includes(query);
    })
    .sort((a, b) => {
      if (state.mutationDrugSort === "compound") return (a.compoundName || a.drugName).localeCompare(b.compoundName || b.drugName);
      if (state.mutationDrugSort === "formula") return (a.molecularFormula || "").localeCompare(b.molecularFormula || "");
      return a.drugName.localeCompare(b.drugName);
    });
}

function renderMutationDrugs() {
  if (!els.mutationDrugTable) return;
  if (els.mutationDrugFilter && !els.mutationDrugFilter.dataset.ready) {
    const labels = ["all", ...new Set(state.mutationDrugs.map((item) => item.evidenceLabel))];
    els.mutationDrugFilter.innerHTML = labels
      .map((label) => `<option value="${escapeHtml(label)}">${label === "all" ? "Evidence label" : escapeHtml(label)}</option>`)
      .join("");
    els.mutationDrugFilter.dataset.ready = "true";
  }

  const drugs = filteredMutationDrugs();
  els.mutationDrugTable.innerHTML =
    drugs
      .map(
        (item) => `
          <tr>
            <td>
              <button class="drug-row-button" type="button" data-chembl-id="${escapeHtml(item.chemblId || "")}" data-drug-slug="${escapeHtml(item.drugSlug)}">
                ${escapeHtml(item.drugName)}
              </button>
            </td>
            <td>${escapeHtml(item.compoundName || "No local ChEMBL match yet")}</td>
            <td>${item.chemblId ? externalLink(`https://www.ebi.ac.uk/chembl/compound_report_card/${item.chemblId}/`, item.chemblId) : `<span class="empty-inline">Not matched</span>`}</td>
            <td>${item.molecularFormula ? `<code>${formulaHtml(item.molecularFormula)}</code>` : `<span class="empty-inline">Not available</span>`}</td>
            <td><span class="tag">${escapeHtml(item.evidenceLabel)}</span></td>
            <td>${externalLink(item.nciDrugUrl, "NCI")}</td>
          </tr>
        `
      )
      .join("") || `<tr><td colspan="6">No matching drugs.</td></tr>`;

  els.mutationDrugTable.querySelectorAll(".drug-row-button").forEach((button) => {
    button.addEventListener("click", () => {
      const drug = state.mutationDrugs.find((item) => item.drugSlug === button.dataset.drugSlug && (item.chemblId || "") === (button.dataset.chemblId || ""));
      openDrugDrawer(drug, button);
    });
  });
}

function drawerFocusable() {
  if (!els.drugDrawer) return [];
  return Array.from(els.drugDrawer.querySelectorAll("a, button, input, select, textarea, [tabindex]:not([tabindex='-1'])")).filter((node) => !node.disabled);
}

function closeDrugDrawer() {
  if (!els.drugDrawer || !els.drugDrawerBackdrop) return;
  els.drugDrawer.hidden = true;
  els.drugDrawerBackdrop.hidden = true;
  document.body.classList.remove("drawer-open");
  if (state.drawerLastFocus) state.drawerLastFocus.focus();
}

function renderNoMatchDrawer(drug) {
  if (!els.drugDrawerContent) return;
  els.drugDrawerContent.innerHTML = `
    <div class="drawer-head">
      <span class="section-kicker">Drug detail</span>
      <h2 id="drug-drawer-title">${escapeHtml(drug.drugName)}</h2>
      <p>No local ChEMBL compound match is available yet for this NCI-listed drug.</p>
    </div>
    <dl class="drawer-facts">
      <div><dt>NCI source</dt><dd>${externalLink(drug.nciDrugUrl, "Open NCI drug page")}</dd></div>
      <div><dt>Evidence</dt><dd>${escapeHtml(drug.evidenceLabel)}</dd></div>
      <div><dt>Context</dt><dd>${escapeHtml(drug.nciCancerType)}</dd></div>
    </dl>
  `;
}

function renderDrugDetailDrawer(detail) {
  if (!els.drugDrawerContent) return;
  const showChemicalStructure = Boolean(detail.molecularFormula && detail.structureImageUrlOrSvg);
  els.drugDrawerContent.innerHTML = `
    <div class="drawer-head">
      <span class="section-kicker">Compound detail</span>
      <h2 id="drug-drawer-title">${escapeHtml(detail.drugName)}</h2>
      <p>${escapeHtml(detail.compoundName || "Local ChEMBL compound")} from the compact COAD web schema.</p>
    </div>
    ${showChemicalStructure ? `<figure class="compound-structure"><img src="${escapeHtml(detail.structureImageUrlOrSvg)}" alt="Chemical structure for ${escapeHtml(detail.compoundName)}" /></figure>` : ""}
    <dl class="drawer-facts">
      <div><dt>Compound</dt><dd>${escapeHtml(detail.compoundName || "Not available")}</dd></div>
      <div><dt>ChEMBL ID</dt><dd>${detail.chemblId ? externalLink(`https://www.ebi.ac.uk/chembl/compound_report_card/${detail.chemblId}/`, detail.chemblId) : "Not available"}</dd></div>
      <div><dt>Molecular formula</dt><dd>${detail.molecularFormula ? `<code>${formulaHtml(detail.molecularFormula)}</code>` : "Not available"}</dd></div>
      <div><dt>Molecule type</dt><dd>${escapeHtml(detail.moleculeType || "Not available")}</dd></div>
      <div><dt>Max phase</dt><dd>${detail.maxPhase ?? "Not available"}</dd></div>
      <div><dt>InChIKey</dt><dd>${escapeHtml(detail.standardInchiKey || "Not available")}</dd></div>
      <div><dt>SMILES</dt><dd><code>${escapeHtml(detail.canonicalSmiles || "Not available")}</code></dd></div>
      <div><dt>NCI source</dt><dd>${externalLink(detail.nciDrugUrl, "Open NCI drug page")}</dd></div>
    </dl>
    <section class="drawer-section">
      <h3>Indications</h3>
      ${
        detail.indications?.length
          ? `<ul>${detail.indications
              .map((item) => `<li>${escapeHtml(item.indicationText || item.meshHeading || item.efoTerm || "ChEMBL indication record")}</li>`)
              .join("")}</ul>`
          : `<p class="empty">No local ChEMBL indication record is available yet.</p>`
      }
    </section>
    <p class="drawer-note">Molecular formula shows which atoms are in a molecule. SMILES is a text format for describing chemical structure.</p>
  `;
}

async function openDrugDrawer(drug, trigger) {
  if (!drug || !els.drugDrawer || !els.drugDrawerBackdrop || !els.drugDrawerContent) return;
  state.drawerLastFocus = trigger || document.activeElement;
  els.drugDrawer.hidden = false;
  els.drugDrawerBackdrop.hidden = false;
  document.body.classList.add("drawer-open");
  els.drugDrawerContent.innerHTML = `<p class="empty">Loading drug details from coad_web...</p>`;

  if (!drug.chemblId) {
    renderNoMatchDrawer(drug);
    els.drugDrawerClose?.focus();
    return;
  }

  try {
    const detail = await fetchJson(`/api/mutation-analysis/drugs/${encodeURIComponent(drug.chemblId)}`);
    renderDrugDetailDrawer(detail);
  } catch (error) {
    els.drugDrawerContent.innerHTML = `<p class="empty">Unable to load ${escapeHtml(drug.chemblId)}: ${escapeHtml(error.message)}</p>`;
  }
  els.drugDrawerClose?.focus();
}

async function loadMutationAnalysis() {
  if (!mutationPageActive()) return;
  try {
    const [genes, mutationTypes, drugs] = await Promise.all([
      fetchJson("/api/mutation-analysis/genes"),
      fetchJson("/api/mutation-analysis/mutation-types"),
      fetchJson("/api/mutation-analysis/drugs")
    ]);
    state.mutationGenes = genes;
    state.mutationTypes = mutationTypes;
    state.mutationDrugs = drugs;
    renderMutationGeneChart();
    renderMutationTypeChart();
    populateMutationFilters();
    renderMutationStructure();
    renderMutationMapper();
    renderMutationDrugs();
    await loadMutationTable();
  } catch (error) {
    const message = `Unable to load Mutation Analysis data from coad_web: ${escapeHtml(error.message)}`;
    if (els.mutationDetailTable) els.mutationDetailTable.innerHTML = `<tr><td colspan="8">${message}</td></tr>`;
    if (els.mutationDrugTable) els.mutationDrugTable.innerHTML = `<tr><td colspan="6">${message}</td></tr>`;
  }
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
  els.mutationGeneFilter?.addEventListener("change", () => {
    state.mutationGeneFilter = els.mutationGeneFilter.value;
    state.mutationPage = 1;
    state.selectedMutationDetail = null;
    state.mutationHotspots = [];
    state.mutationLocationMutations = [];
    renderMutationGeneChart();
    renderMutationStructure();
    renderMutationMapper();
    loadMutationTable();
  });
  els.mutationTypeFilter?.addEventListener("change", () => {
    state.mutationTypeFilter = els.mutationTypeFilter.value;
    state.mutationPage = 1;
    state.selectedMutationDetail = null;
    state.mutationHotspots = [];
    state.mutationLocationMutations = [];
    renderMutationTypeChart();
    renderMutationStructure();
    renderMutationMapper();
    loadMutationTable();
  });
  els.mutationPagePrev?.addEventListener("click", () => {
    if (state.mutationPage <= 1) return;
    state.mutationPage -= 1;
    loadMutationTable();
  });
  els.mutationPageNext?.addEventListener("click", () => {
    if (state.mutationPage >= state.mutationTotalPages) return;
    state.mutationPage += 1;
    loadMutationTable();
  });
  els.mutationPageSize?.addEventListener("change", () => {
    state.mutationPageSize = Number(els.mutationPageSize.value) || 50;
    state.mutationPage = 1;
    loadMutationTable();
  });
  els.mutationDrugSearch?.addEventListener("input", () => {
    state.mutationDrugQuery = els.mutationDrugSearch.value;
    renderMutationDrugs();
  });
  els.mutationDrugFilter?.addEventListener("change", () => {
    state.mutationDrugEvidence = els.mutationDrugFilter.value;
    renderMutationDrugs();
  });
  els.mutationDrugSort?.addEventListener("change", () => {
    state.mutationDrugSort = els.mutationDrugSort.value;
    renderMutationDrugs();
  });
  els.drugDrawerClose?.addEventListener("click", closeDrugDrawer);
  els.drugDrawerBackdrop?.addEventListener("click", closeDrugDrawer);
  document.addEventListener("keydown", (event) => {
    if (!els.drugDrawer || els.drugDrawer.hidden) return;
    if (event.key === "Escape") {
      event.preventDefault();
      closeDrugDrawer();
      return;
    }
    if (event.key !== "Tab") return;
    const focusable = drawerFocusable();
    if (!focusable.length) return;
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
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
    await loadMutationAnalysis();
    renderGlossary();
    renderSources();
    await loadContact();
  } catch (error) {
    document.body.insertAdjacentHTML("afterbegin", `<div class="load-error">Unable to load COAD project data: ${escapeHtml(error.message)}</div>`);
  }
}

init();
