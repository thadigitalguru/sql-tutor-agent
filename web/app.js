import { EditorState } from "https://esm.sh/@codemirror/state@6";
import { EditorView, keymap, lineNumbers, highlightActiveLine } from "https://esm.sh/@codemirror/view@6";
import { defaultKeymap, history, historyKeymap } from "https://esm.sh/@codemirror/commands@6";
import { sql } from "https://esm.sh/@codemirror/lang-sql@6";
import { oneDark } from "https://esm.sh/@codemirror/theme-one-dark@6";

const STORAGE_LEARNER = "sql-tutor-learner-id";
const STORAGE_SESSION = "sql-tutor-session-id";

const els = {
  onboarding: document.querySelector("#onboarding"),
  form: document.querySelector("#onboarding-form"),
  skill: document.querySelector("#lesson-skill"),
  kicker: document.querySelector("#lesson-kicker"),
  title: document.querySelector("#task-title"),
  prompt: document.querySelector("#task-prompt"),
  concept: document.querySelector("#task-concept"),
  schema: document.querySelector("#schema-list"),
  orderNote: document.querySelector("#order-note"),
  feedback: document.querySelector("#tutor-feedback"),
  result: document.querySelector("#result-table"),
  status: document.querySelector("#status-chip"),
  engine: document.querySelector("#engine-error"),
  engineText: document.querySelector("#engine-error-text"),
  next: document.querySelector("#btn-next"),
  progressDlg: document.querySelector("#progress-panel"),
  skillList: document.querySelector("#skill-list"),
  progressPattern: document.querySelector("#progress-pattern"),
};

let sessionId = localStorage.getItem(STORAGE_SESSION);
let learnerId = localStorage.getItem(STORAGE_LEARNER);
let exercise = null;
let schema = null;
let editorView = null;

function editor() {
  if (editorView) return editorView;
  editorView = new EditorView({
    parent: document.querySelector("#editor"),
    state: EditorState.create({
      doc: "SELECT\n  \nFROM ",
      extensions: [
        lineNumbers(),
        history(),
        highlightActiveLine(),
        sql(),
        oneDark,
        keymap.of([...defaultKeymap, ...historyKeymap]),
        EditorView.theme({
          "&": { fontSize: "0.92rem" },
          ".cm-content": { fontFamily: "IBM Plex Mono, ui-monospace, monospace" },
        }),
      ],
    }),
  });
  return editorView;
}

async function api(path, options = {}) {
  const response = await fetch(`/api${path}`, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || response.statusText);
  }
  return data;
}

function setQuery(sqlText) {
  const view = editor();
  view.dispatch({
    changes: { from: 0, to: view.state.doc.length, insert: sqlText },
  });
}

function renderSchema(payload) {
  schema = payload;
  els.schema.replaceChildren();
  if (!payload?.tables) return;
  for (const [table, columns] of Object.entries(payload.tables)) {
    const card = document.createElement("article");
    card.className = "table-card";
    const head = document.createElement("h3");
    head.textContent = table;
    const previewBtn = document.createElement("button");
    previewBtn.type = "button";
    previewBtn.className = "text-btn";
    previewBtn.textContent = "Preview";
    previewBtn.addEventListener("click", () => previewTable(table));
    head.append(previewBtn);
    const list = document.createElement("ul");
    list.className = "cols";
    for (const col of columns) {
      const item = document.createElement("li");
      const name = document.createElement("span");
      name.textContent = col.name;
      const type = document.createElement("span");
      type.textContent = col.type;
      item.append(name, type);
      list.append(item);
    }
    card.append(head, list);
    els.schema.append(card);
  }
}

function renderExercise(ex) {
  exercise = ex;
  if (!ex) {
    els.title.textContent = "Session complete";
    els.prompt.textContent = "Open Progress to see what to review next.";
    els.concept.textContent = "";
    els.next.hidden = true;
    return;
  }
  els.kicker.textContent = `Lesson: ${ex.primary_skill.replaceAll("_", " ")}`;
  els.skill.textContent = `Difficulty ${ex.difficulty}`;
  els.title.textContent = ex.title;
  els.prompt.textContent = ex.prompt;
  els.concept.textContent = ex.teach || ex.concept || "";
  els.orderNote.textContent = ex.evaluation?.order_matters
    ? "Row order matters"
    : "Row order does not matter";
  els.next.hidden = true;
}

function renderFeedback(payload) {
  els.feedback.textContent = payload.feedback || "";
  const status = payload.evaluation?.status;
  els.status.textContent = status || (payload.result?.ok === false ? payload.result.error_type : "");
  els.status.className = "muted " + (status === "CORRECT" || status === "CORRECT_WITH_IMPROVEMENT" ? "status-ok" : "status-bad");
  const engineMessage = payload.evaluation?.engine_message || payload.result?.message;
  if (engineMessage && payload.evaluation && payload.evaluation.status !== "CORRECT") {
    els.engine.hidden = false;
    els.engineText.textContent = engineMessage;
  } else {
    els.engine.hidden = true;
    els.engineText.textContent = "";
  }
  renderTable(payload.result);
  if (status === "CORRECT" || status === "CORRECT_WITH_IMPROVEMENT") {
    els.next.hidden = false;
    els.feedback.focus();
  }
}

function renderTable(result) {
  els.result.replaceChildren();
  if (!result?.ok) return;
  const table = document.createElement("table");
  table.className = "data";
  const thead = document.createElement("thead");
  const headRow = document.createElement("tr");
  for (const col of result.columns || []) {
    const th = document.createElement("th");
    th.textContent = col;
    headRow.append(th);
  }
  thead.append(headRow);
  const tbody = document.createElement("tbody");
  for (const row of result.rows || []) {
    const tr = document.createElement("tr");
    for (const value of row) {
      const td = document.createElement("td");
      if (value === null) {
        td.className = "null";
        td.textContent = "NULL";
      } else {
        td.textContent = String(value);
      }
      tr.append(td);
    }
    tbody.append(tr);
  }
  table.append(thead, tbody);
  const note = document.createElement("p");
  note.className = "muted";
  note.textContent = `${result.row_count} row(s)${result.truncated ? " — truncated" : ""} · ${result.elapsed_ms} ms`;
  els.result.append(note, table);
}

function renderProgress(progress) {
  if (!progress) return;
  els.progressPattern.textContent = [progress.pattern, progress.suggested_next && `Suggested next: ${progress.suggested_next}`]
    .filter(Boolean)
    .join(" ");
  els.skillList.replaceChildren();
  for (const skill of progress.skills || []) {
    if (skill.attempts === 0 && skill.mastery === 0) continue;
    const li = document.createElement("li");
    const name = document.createElement("span");
    name.textContent = skill.name;
    const band = document.createElement("span");
    band.className = "muted";
    band.textContent = skill.band;
    const pct = document.createElement("span");
    pct.textContent = `${Math.round(skill.mastery * 100)}%`;
    const bar = document.createElement("div");
    bar.className = "bar";
    const fill = document.createElement("span");
    fill.style.inlineSize = `${Math.round(skill.mastery * 100)}%`;
    bar.append(fill);
    li.append(name, band, pct, bar);
    els.skillList.append(li);
  }
}

function applyPayload(payload) {
  if (payload.session?.id) {
    sessionId = payload.session.id;
    localStorage.setItem(STORAGE_SESSION, sessionId);
  }
  if (payload.session?.learner_id) {
    learnerId = payload.session.learner_id;
    localStorage.setItem(STORAGE_LEARNER, learnerId);
  }
  renderExercise(payload.exercise);
  renderSchema(payload.schema);
  renderFeedback(payload);
  renderProgress(payload.progress);
}

async function startSession(overrides = {}) {
  const body = {
    learner_id: learnerId,
    resume: true,
    ...overrides,
  };
  const payload = await api("/sessions", { method: "POST", body: JSON.stringify(body) });
  applyPayload(payload);
  if (payload.onboarding && !overrides.sql_level) {
    els.onboarding.hidden = false;
  } else {
    els.onboarding.hidden = true;
  }
}

async function previewTable(table) {
  if (!exercise) return;
  const data = await api(
    `/tables/${encodeURIComponent(table)}/preview?dataset_id=${encodeURIComponent(exercise.dataset)}&limit=8`
  );
  renderTable(data);
  els.feedback.textContent = `Preview of ${table}. This is exploration — it does not affect mastery.`;
  els.status.textContent = "preview";
}

async function runQuery(kind) {
  if (!exercise || !sessionId) return;
  const query = editor().state.doc.toString();
  const path = kind === "submit" ? `/exercises/${exercise.id}/submit` : "/sql/run";
  const payload = await api(path, {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId, query }),
  });
  applyPayload(payload);
}

async function requestHint(wantSolution = false) {
  if (!exercise || !sessionId) return;
  const payload = await api(`/exercises/${exercise.id}/hint`, {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId, want_solution: wantSolution }),
  });
  applyPayload(payload);
}

els.form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const data = new FormData(els.form);
  await startSession({
    sql_level: data.get("sql_level"),
    dialect: data.get("dialect"),
    goal: data.get("goal"),
    resume: false,
  });
});

document.querySelector("#btn-run").addEventListener("click", () => runQuery("run"));
document.querySelector("#btn-submit").addEventListener("click", () => runQuery("submit"));
document.querySelector("#btn-hint").addEventListener("click", () => requestHint(false));
document.querySelector("#btn-solution").addEventListener("click", () => requestHint(true));
document.querySelector("#btn-next").addEventListener("click", async () => {
  const payload = await api("/lessons/next", {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId }),
  });
  applyPayload(payload);
  setQuery("SELECT\n  \nFROM ");
});
document.querySelector("#btn-progress").addEventListener("click", async () => {
  if (learnerId) {
    const progress = await api(`/progress?learner_id=${encodeURIComponent(learnerId)}`);
    renderProgress(progress);
  }
  const btn = document.querySelector("#btn-progress");
  btn.setAttribute("aria-expanded", "true");
  els.progressDlg.showModal();
});
els.progressDlg.addEventListener("close", () => {
  document.querySelector("#btn-progress").setAttribute("aria-expanded", "false");
});
document.querySelector("#btn-schema-data").addEventListener("click", async () => {
  const first = schema && Object.keys(schema.tables)[0];
  if (first) await previewTable(first);
});
document.querySelector("#btn-easier").addEventListener("click", async () => {
  els.feedback.textContent = "Asking for a simpler task…";
  const payload = await api("/lessons/next", {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId }),
  });
  applyPayload(payload);
});

editor();
startSession().catch((err) => {
  els.onboarding.hidden = false;
  els.feedback.textContent = err.message;
});
