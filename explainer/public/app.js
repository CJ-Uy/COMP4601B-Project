import {
  CONDITIONS,
  RESULT_CONDITIONS,
  splitPlan,
  batchPlan,
  validateResearch,
} from "./research-model.js";

const $ = (selector) => document.querySelector(selector);
const number = (value) => value.toLocaleString("en");
const date = (value) =>
  new Intl.DateTimeFormat("en", {
    day: "numeric",
    month: "short",
    year: "numeric",
    timeZone: "UTC",
  }).format(new Date(value));
const formats = {
  original: [
    "Three notebooks at five dollars each cost 3 × 5 = 15 dollars.",
    "Subtract the cost from the amount paid: 20 − 15 = 5 dollars.",
  ],
  english: ["Cost: 3 × 5 = 15.", "Change: 20 − 15 = 5."],
  mixed: ["成本: 3 × 5 = 15.", "Change: 20 − 15 = 5."],
};
let stage = "data",
  depth = "plain",
  research,
  updateFailed = false;
const stages = ["data", "rewrite", "select", "train", "test"];
const stageNames = [
  "Get the data",
  "Rewrite the work",
  "Choose examples",
  "Train with LoRA",
  "Test fairly",
];
function animate(element) {
  element.classList.remove("content-enter");
  void element.offsetWidth;
  element.classList.add("content-enter");
}
function selectGroup(selector, attribute, value) {
  document
    .querySelectorAll(selector)
    .forEach((button) =>
      button.setAttribute(
        "aria-pressed",
        String(button.dataset[attribute] === value),
      ),
    );
}
function renderStage() {
  const index = stages.indexOf(stage);
  $("#selected-stage-name").textContent = `${index + 1} · ${stageNames[index]}`;
  $("#previous-step").disabled = index === 0;
  $("#next-step").disabled = index === stages.length - 1;
  $("#stage-content").replaceChildren(
    $(`#stage-${stage}`).content.cloneNode(true),
  );
  $("#stage-content")
    .querySelectorAll("[data-panel]")
    .forEach((panel) => {
      panel.hidden = panel.dataset.panel !== depth;
    });
  if ($("#training-size")) updateSplit();
  if ($("#batch-size")) updateBatch();
  $("#detail-dialog").scrollTop = 0;
  animate($("#stage-content"));
}
function openDetails(nextStage, nextDepth = "plain") {
  stage = nextStage;
  depth = nextDepth;
  selectGroup("[data-stage]", "stage", stage);
  selectGroup("[data-depth]", "depth", depth);
  renderStage();
  $("#detail-dialog").showModal();
}
function updateSplit() {
  const plan = splitPlan(Number($("#training-size").value));
  $("#training-value").textContent = number(plan.training);
  $("#split-training").textContent = `${number(plan.training)} training`;
  $("#split-total").textContent =
    `${number(plan.training + plan.calibration + plan.development)} selected from the training pool; ${number(plan.unused)} left for possible expansion.`;
}
function updateBatch() {
  const size = Number($("#batch-size").value),
    plan = batchPlan(1000, size);
  $("#batch-tiles").replaceChildren(
    ...Array.from({ length: size }, (_, index) => {
      const tile = document.createElement("span");
      tile.textContent = index + 1;
      return tile;
    }),
  );
  $("#batch-summary").textContent =
    `1,000 examples ÷ ${size} at a time = ${number(plan.batches)} batches per epoch.`;
}
function textElement(tag, text, className) {
  const element = document.createElement(tag);
  element.textContent = text;
  if (className) element.className = className;
  return element;
}
function renderProgress() {
  $("#study-status").textContent = research.results.length
    ? "Measured results available below"
    : "Proposed study · no measured results yet";
  $("#results-title").textContent = research.results.length
    ? "Measured results"
    : "Results will live here.";
  $("#current-phase").textContent = research.phase;
  $("#progress-summary").textContent = research.summary;
  $("#last-updated").textContent = `Updated ${date(research.updated)}`;
  $("#milestone-list").replaceChildren(
    ...research.milestones.map((item) => {
      const row = document.createElement("li"),
        content = document.createElement("div");
      const status = {
        done: "Complete",
        "in-progress": "In progress",
        planned: "Planned",
      }[item.status];
      content.append(
        textElement("h3", item.title),
        textElement("p", item.note),
      );
      const when = textElement(
        item.date ? "time" : "span",
        item.date ? date(item.date) : "After the pilot",
      );
      if (item.date) when.dateTime = item.date;
      row.append(
        textElement("span", status, `status-label ${item.status}`),
        content,
        when,
      );
      return row;
    }),
  );
  $("#decision-list").replaceChildren(
    ...research.decisions.map((item) => {
      const article = document.createElement("article");
      article.append(
        textElement("h3", item.title),
        textElement("p", item.reason),
        textElement("small", date(item.date)),
      );
      return article;
    }),
  );
}
function renderResults() {
  if (!research) {
    $("#result-count").textContent = updateFailed
      ? "Results unavailable"
      : "Loading results";
    $("#results-empty h3").textContent = updateFailed
      ? "Measured results are unavailable."
      : "Loading the latest research update.";
    return;
  }
  const filtered = (research?.results ?? []).filter(
    (result) =>
      result.budget === Number($("#result-budget").value) &&
      result.split === $("#result-split").value,
  );
  $("#result-count").textContent =
    `${filtered.length} measured ${filtered.length === 1 ? "run" : "runs"}`;
  $("#results-empty").hidden = filtered.length > 0;
  $("#results-table-wrap").hidden = filtered.length === 0;
  const noRuns = !research?.results.length;
  $("#results-empty h3").textContent = noRuns
    ? "The experiment has not run yet."
    : "No measured runs for this selection yet.";
  $("#results-body").replaceChildren(
    ...filtered.map((result) => {
      const row = document.createElement("tr");
      const condition = RESULT_CONDITIONS.find(
        (item) => item.id === result.condition,
      );
      for (const value of [
        condition.name,
        `${result.correct}/${result.sampleSize} (${((100 * result.correct) / result.sampleSize).toFixed(1)}%)`,
        number(result.meanTokens),
        number(result.meanSeconds),
      ])
        row.append(textElement("td", value));
      const evidence = document.createElement("td"),
        link = document.createElement("a");
      link.href = result.source;
      link.textContent = "Run evidence";
      evidence.append(
        textElement(
          "p",
          `${result.model} · seed ${result.seed} · ${date(result.date)}`,
        ),
        textElement("p", result.notes),
        link,
      );
      row.append(evidence);
      return row;
    }),
  );
}
document.addEventListener("click", (event) => {
  const button = event.target.closest("button");
  if (!button) return;
  if (button.dataset.format) {
    const values = formats[button.dataset.format];
    selectGroup("[data-format]", "format", button.dataset.format);
    $("#demo-cost").textContent = values[0];
    $("#demo-change").textContent = values[1];
    animate($("#demo-work"));
  }
  if (button.dataset.stage) {
    openDetails(button.dataset.stage);
  }
  if (button.dataset.open)
    openDetails(button.dataset.open, button.dataset.level);
  if (button.id === "close-detail") $("#detail-dialog").close();
  if (["previous-step", "next-step"].includes(button.id)) {
    stage =
      stages[stages.indexOf(stage) + (button.id === "next-step" ? 1 : -1)];
    selectGroup("[data-stage]", "stage", stage);
    renderStage();
  }
  if (button.dataset.depth) {
    depth = button.dataset.depth;
    selectGroup("[data-depth]", "depth", depth);
    renderStage();
  }
});
$("#detail-dialog").addEventListener("close", () =>
  selectGroup("[data-stage]", "stage", ""),
);
$("#detail-dialog").addEventListener("click", (event) => {
  if (event.target !== event.currentTarget) return;
  const box = event.currentTarget.getBoundingClientRect();
  if (
    event.clientX < box.left ||
    event.clientX > box.right ||
    event.clientY < box.top ||
    event.clientY > box.bottom
  )
    event.currentTarget.close();
});
document.addEventListener("input", (event) => {
  if (event.target.id === "training-size") updateSplit();
});
document.addEventListener("change", (event) => {
  if (event.target.id === "batch-size") updateBatch();
  if (["result-budget", "result-split"].includes(event.target.id))
    renderResults();
});
$("#conditions-body").replaceChildren(
  ...CONDITIONS.map((condition, index) => {
    const row = document.createElement("tr"),
      name = textElement("td", condition.name);
    if (index === 0)
      name.append(textElement("span", "Required baseline", "baseline-label"));
    row.append(
      name,
      textElement("td", condition.language),
      textElement("td", condition.selection),
    );
    return row;
  }),
);
renderStage();
document.querySelectorAll("[data-stage]").forEach((button) => {
  button.setAttribute("aria-haspopup", "dialog");
  button.setAttribute("aria-controls", "detail-dialog");
});
renderResults();
try {
  const response = await fetch("research.json", { cache: "no-cache" });
  if (!response.ok) throw new Error("Research update could not be fetched.");
  research = validateResearch(await response.json());
  renderProgress();
  renderResults();
} catch (error) {
  updateFailed = true;
  $("#study-status").textContent = "Latest research update unavailable";
  $("#last-updated").textContent = "Latest update unavailable";
  $("#update-error").textContent =
    "The latest progress and results could not be loaded. Reload the page to try again. The explainer is still available.";
  $("#update-error").hidden = false;
  renderResults();
  console.error(error.message);
}
