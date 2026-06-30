from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from app.api.ask_routes import router as ask_router
from app.api.hyper_routes import router as hyper_router
from app.api.insight_routes import router as insight_router


app = FastAPI(
    title="Hyper Inspector API",
    version="0.3.0",
    description="Tableau .hyper 파일을 업로드하고 구조, 미리보기, 자연어 기반 Insight 분석을 확인하는 API입니다.",
)

app.include_router(hyper_router)
app.include_router(insight_router)
app.include_router(ask_router)


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def web_ui():
    return """
<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Hyper Inspector</title>
  <style>
    :root {
      --bg: #f5f7fa;
      --panel: #fff;
      --ink: #20242a;
      --muted: #687282;
      --line: #dfe4ea;
      --brand: #1473e6;
      --brand-dark: #0c58b6;
      --ok: #176846;
      --warn: #9a5a00;
      --error: #b4232a;
      --soft: #edf4ff;
      --shadow: 0 12px 30px rgba(22, 34, 51, 0.08);
    }
    * { box-sizing: border-box; }
    body { margin: 0; background: var(--bg); color: var(--ink); font-family: "Segoe UI", system-ui, sans-serif; line-height: 1.5; }
    header { background: #0f1720; color: white; padding: 24px; }
    .wrap { width: min(1200px, calc(100% - 32px)); margin: 0 auto; }
    .topbar { display: flex; justify-content: space-between; gap: 20px; align-items: flex-start; }
    h1 { margin: 0 0 6px; font-size: clamp(28px, 4vw, 42px); letter-spacing: 0; }
    h2 { margin: 0; font-size: 18px; }
    h3 { margin: 0 0 10px; font-size: 15px; }
    .subtitle { margin: 0; max-width: 820px; color: #d7dee8; }
    .docs-link { color: white; border: 1px solid rgba(255,255,255,.28); border-radius: 8px; padding: 9px 13px; text-decoration: none; white-space: nowrap; }
    main { padding: 22px 0 44px; }
    .layout { display: grid; grid-template-columns: 340px minmax(0, 1fr); gap: 18px; align-items: start; }
    .panel { background: var(--panel); border: 1px solid var(--line); border-radius: 8px; box-shadow: var(--shadow); margin-bottom: 18px; min-width: 0; }
    .panel-head { padding: 17px 20px; border-bottom: 1px solid var(--line); }
    .panel-head p { margin: 4px 0 0; color: var(--muted); font-size: 14px; }
    .panel-body { padding: 20px; min-width: 0; }
    .field { margin-bottom: 16px; }
    .muted { color: var(--muted); font-size: 13px; }
    label { display: block; margin-bottom: 7px; font-weight: 650; font-size: 14px; }
    input[type="file"], select, input[type="number"], textarea {
      width: 100%; min-height: 42px; border: 1px solid #cbd3dd; border-radius: 8px; background: #fff; padding: 9px 11px; color: var(--ink); font: inherit;
    }
    textarea { min-height: 92px; resize: vertical; }
    .button-row, .ask-actions { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
    button, .button {
      border: 0; border-radius: 8px; background: var(--brand); color: white; cursor: pointer; display: inline-flex; align-items: center; justify-content: center;
      min-height: 40px; padding: 9px 13px; font: inherit; font-weight: 650; text-decoration: none;
    }
    button.secondary, .button.secondary { background: #e8edf3; color: #1f2933; }
    button:disabled, .button.disabled { cursor: not-allowed; opacity: .55; }
    button:not(:disabled):hover, .button:not(.disabled):hover { background: var(--brand-dark); }
    button.secondary:not(:disabled):hover, .button.secondary:not(.disabled):hover { background: #d7dee7; }
    .status { margin-top: 16px; border-radius: 8px; padding: 12px 13px; background: #fff4e5; color: var(--warn); font-size: 14px; word-break: break-word; }
    .status.ok { background: #e9f8f0; color: var(--ok); }
    .status.error { background: #fdecec; color: var(--error); }
    .summary-grid, .insight-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; margin-bottom: 16px; }
    .metric, .mini-card, .answer-card { background: #fbfcfe; border: 1px solid var(--line); border-radius: 8px; padding: 14px; min-width: 0; }
    .metric span { display: block; color: var(--muted); font-size: 13px; margin-bottom: 5px; }
    .metric strong { display: block; font-size: 20px; word-break: break-word; }
    .workspace-tabs, .tabs { display: flex; gap: 8px; border-bottom: 1px solid var(--line); margin-bottom: 14px; }
    .workspace-tab, .tab { background: transparent; color: var(--muted); border-radius: 8px 8px 0 0; min-height: 38px; }
    .workspace-tab.active, .tab.active { background: var(--soft); color: #0f4f9f; }
    .workspace-view[hidden], .hidden { display: none; }
    .table-tools { display: flex; flex-wrap: wrap; align-items: end; justify-content: space-between; gap: 12px; margin-bottom: 14px; }
    .limit-control { width: 150px; }
    .data-box { width: 100%; border: 1px solid var(--line); border-radius: 8px; overflow-x: auto; overflow-y: auto; max-height: 480px; background: white; }
    table { width: max-content; min-width: 100%; border-collapse: collapse; table-layout: auto; font-size: 13px; }
    th, td { border-bottom: 1px solid var(--line); padding: 9px 10px; text-align: left; vertical-align: top; white-space: normal; overflow-wrap: anywhere; word-break: break-word; min-width: 120px; max-width: 260px; }
    th { position: sticky; top: 0; background: #f4f7fb; z-index: 1; font-weight: 700; }
    tr:hover td { background: #fafcff; }
    .empty { border: 1px dashed #bcc7d4; border-radius: 8px; padding: 26px; text-align: center; color: var(--muted); background: #fbfcfe; }
    .chip-list { display: flex; flex-wrap: wrap; gap: 8px; }
    .chip { display: inline-flex; border: 1px solid var(--line); border-radius: 999px; padding: 5px 9px; background: white; font-size: 13px; max-width: 100%; overflow-wrap: anywhere; }
    .answer-card { margin-top: 16px; display: grid; gap: 12px; }
    .answer-text { font-size: 18px; font-weight: 700; }
    .meta-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; }
    .meta-grid div { border: 1px solid var(--line); border-radius: 8px; padding: 10px; background: white; }
    .sql-box { background: #111827; color: #f9fafb; border-radius: 8px; padding: 12px; overflow: auto; white-space: pre-wrap; overflow-wrap: anywhere; font-family: Consolas, "Courier New", monospace; font-size: 12px; }
    details { margin-top: 4px; }
    summary { cursor: pointer; color: #1f5ea8; font-weight: 650; }
    @media (max-width: 900px) {
      .topbar, .layout, .summary-grid, .insight-grid, .meta-grid { display: grid; grid-template-columns: 1fr; }
      .docs-link { width: fit-content; }
      table { min-width: 720px; }
    }
  </style>
</head>
<body>
  <header>
    <div class="wrap topbar">
      <div>
        <h1>Hyper Inspector</h1>
        <p class="subtitle">Tableau .hyper 파일을 업로드하고 데이터 구조, 미리보기, 자연어 Insight 분석을 확인합니다.</p>
      </div>
      <a class="docs-link" href="/docs" target="_blank" rel="noreferrer">API 문서 열기</a>
    </div>
  </header>
  <main class="wrap">
    <section class="layout">
      <aside class="panel">
        <div class="panel-head">
          <h2>파일과 테이블</h2>
          <p>파일을 올린 뒤 분석할 테이블을 선택하세요.</p>
        </div>
        <div class="panel-body">
          <form id="uploadForm">
            <div class="field">
              <label for="fileInput">.hyper 파일</label>
              <input id="fileInput" name="file" type="file" accept=".hyper" required />
              <div class="muted">예: Sample - Superstore.hyper</div>
            </div>
            <button id="uploadButton" type="submit">파일 분석 시작</button>
          </form>
          <div id="status" class="status">아직 파일이 업로드되지 않았습니다.</div>
          <div class="field" style="margin-top:18px;">
            <label for="tableSelect">테이블 선택</label>
            <select id="tableSelect" disabled><option value="">먼저 파일을 업로드하세요</option></select>
            <div id="tableNote" class="muted">테이블이 여러 개면 원하는 항목을 선택하세요.</div>
          </div>
          <div class="button-row">
            <button id="refreshButton" class="secondary" type="button" disabled>다시 불러오기</button>
            <a id="downloadLink" class="button secondary disabled" href="#" aria-disabled="true">CSV 다운로드</a>
          </div>
        </div>
      </aside>
      <section class="panel">
        <div class="panel-head">
          <h2>작업 영역</h2>
          <p id="resultSubtitle">파일을 업로드하면 데이터 확인과 Insight 분석을 사용할 수 있습니다.</p>
        </div>
        <div class="panel-body">
          <div class="summary-grid">
            <div class="metric"><span>파일 ID</span><strong id="fileIdMetric">-</strong></div>
            <div class="metric"><span>테이블 수</span><strong id="tableCountMetric">-</strong></div>
            <div class="metric"><span>선택 테이블 행 수</span><strong id="rowCountMetric">-</strong></div>
          </div>
          <div class="workspace-tabs" role="tablist">
            <button id="dataWorkspaceTab" class="workspace-tab active" type="button">데이터 확인</button>
            <button id="insightWorkspaceTab" class="workspace-tab" type="button">Insight 분석</button>
          </div>
          <section id="dataWorkspace" class="workspace-view">
            <div class="table-tools">
              <div class="limit-control">
                <label for="limitInput">미리보기 행 수</label>
                <input id="limitInput" type="number" min="1" max="1000" value="100" />
              </div>
              <button id="loadPreviewButton" type="button" disabled>미리보기 새로고침</button>
            </div>
            <div class="tabs" role="tablist">
              <button id="previewTab" class="tab active" type="button">데이터 미리보기</button>
              <button id="schemaTab" class="tab" type="button">컬럼 구조</button>
            </div>
            <div id="previewBox" class="data-box"><div class="empty">업로드 후 테이블을 선택하면 샘플 데이터가 표시됩니다.</div></div>
            <div id="schemaBox" class="data-box" hidden><div class="empty">컬럼 구조가 여기에 표시됩니다.</div></div>
          </section>
          <section id="insightWorkspace" class="workspace-view" hidden>
            <div class="insight-grid">
              <div class="mini-card">
                <h3>파일 요약</h3>
                <div id="profileSummary" class="muted">프로파일을 기다리는 중입니다.</div>
              </div>
              <div class="mini-card">
                <h3>날짜 컬럼 후보</h3>
                <div id="dateCandidates" class="chip-list"></div>
              </div>
              <div class="mini-card">
                <h3>측정값 후보</h3>
                <div id="measureCandidates" class="chip-list"></div>
              </div>
            </div>
            <div class="field">
              <label for="questionInput">질문 입력</label>
              <textarea id="questionInput" placeholder="예: 최근 3개월 Sales 매출은 얼마야?"></textarea>
            </div>
            <div class="ask-actions">
              <button id="askButton" type="button" disabled>질문 실행</button>
              <button id="planButton" class="secondary" type="button" disabled>계획만 보기</button>
              <label class="muted" style="display:inline-flex; gap:6px; align-items:center; margin:0;">
                <input id="includeSqlInput" type="checkbox" checked /> SQL 포함
              </label>
            </div>
            <div id="clarificationBox" class="status hidden"></div>
            <div id="answerBox" class="answer-card">
              <div class="empty">자연어로 질문하면 검증된 분석 계획을 만든 뒤 Hyper SQL 집계 결과를 보여줍니다.</div>
            </div>
          </section>
        </div>
      </section>
    </section>
  </main>
  <script>
    const state = { fileId: "", filename: "", tables: [], selectedTable: "", semantics: null };
    const els = {};
    for (const id of [
      "uploadForm","fileInput","uploadButton","status","tableSelect","tableNote","refreshButton","downloadLink",
      "fileIdMetric","tableCountMetric","rowCountMetric","resultSubtitle","limitInput","loadPreviewButton",
      "dataWorkspaceTab","insightWorkspaceTab","dataWorkspace","insightWorkspace","previewTab","schemaTab",
      "previewBox","schemaBox","profileSummary","dateCandidates","measureCandidates","questionInput","askButton",
      "planButton","includeSqlInput","answerBox","clarificationBox"
    ]) els[id] = document.querySelector("#" + id);

    function setStatus(message, type = "warn") { els.status.className = `status ${type}`; els.status.textContent = message; }
    function formatNumber(value) { const n = Number(value); return Number.isFinite(n) ? n.toLocaleString("ko-KR", { maximumFractionDigits: 2 }) : String(value ?? "-"); }
    function escapeHtml(value) { return String(value ?? "").replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&#039;"); }
    async function apiJson(url, options) {
      const response = await fetch(url, options);
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.detail || "요청을 처리하지 못했습니다.");
      return data;
    }
    function renderTable(container, columns, rows) {
      if (!rows || !rows.length) { container.innerHTML = '<div class="empty">표시할 데이터가 없습니다.</div>'; return; }
      const header = columns.map((column) => `<th>${escapeHtml(column)}</th>`).join("");
      const body = rows.map((row) => `<tr>${row.map((cell) => `<td>${escapeHtml(cell)}</td>`).join("")}</tr>`).join("");
      container.innerHTML = `<table><thead><tr>${header}</tr></thead><tbody>${body}</tbody></table>`;
    }
    function setWorkspace(tab) {
      const showData = tab === "data";
      els.dataWorkspaceTab.classList.toggle("active", showData);
      els.insightWorkspaceTab.classList.toggle("active", !showData);
      els.dataWorkspace.hidden = !showData;
      els.insightWorkspace.hidden = showData;
    }
    function setDataTab(tab) {
      const isPreview = tab === "preview";
      els.previewTab.classList.toggle("active", isPreview);
      els.schemaTab.classList.toggle("active", !isPreview);
      els.previewBox.hidden = !isPreview;
      els.schemaBox.hidden = isPreview;
    }
    function updateDownloadLink() {
      if (!state.fileId || !state.selectedTable) { els.downloadLink.classList.add("disabled"); els.downloadLink.href = "#"; return; }
      const params = new URLSearchParams({ table: state.selectedTable, limit: String(els.limitInput.value || 100) });
      els.downloadLink.classList.remove("disabled");
      els.downloadLink.href = `/hyper/${encodeURIComponent(state.fileId)}/preview.csv?${params}`;
    }
    function fillTables() {
      els.tableSelect.innerHTML = "";
      if (!state.tables.length) { els.tableSelect.disabled = true; els.tableSelect.innerHTML = '<option value="">테이블이 없습니다</option>'; return; }
      for (const table of state.tables) {
        const option = document.createElement("option");
        option.value = table; option.textContent = table; els.tableSelect.appendChild(option);
      }
      els.tableSelect.disabled = false;
      state.selectedTable = state.tables[0];
      els.tableSelect.value = state.selectedTable;
      els.tableNote.textContent = `${state.tables.length}개 테이블을 찾았습니다.`;
    }
    function candidateChips(container, candidates) {
      container.innerHTML = "";
      for (const item of (candidates || []).slice(0, 6)) {
        const chip = document.createElement("span");
        chip.className = "chip";
        chip.textContent = `${item.column_name} (${Math.round((item.confidence || 0) * 100)}%)`;
        container.appendChild(chip);
      }
      if (!container.children.length) container.innerHTML = '<span class="muted">후보 없음</span>';
    }
    async function loadInsightSuggestions() {
      const params = new URLSearchParams({ table: state.selectedTable });
      els.profileSummary.textContent = "컬럼 프로파일을 계산하는 중입니다...";
      const data = await apiJson(`/hyper/${encodeURIComponent(state.fileId)}/insights/suggestions?${params}`);
      state.semantics = data.semantics;
      els.profileSummary.textContent = `${formatNumber(data.profile_summary.row_count)}행 · ${formatNumber(data.profile_summary.column_count)}개 컬럼`;
      candidateChips(els.dateCandidates, state.semantics.date_candidates || []);
      candidateChips(els.measureCandidates, [...(state.semantics.sales_candidates || []), ...(state.semantics.measure_candidates || [])]);
      els.askButton.disabled = false;
      els.planButton.disabled = false;
    }
    async function loadSelectedTable() {
      if (!state.fileId || !state.selectedTable) return;
      const limit = Math.max(1, Math.min(1000, Number(els.limitInput.value || 100)));
      els.limitInput.value = limit;
      els.loadPreviewButton.disabled = true;
      setStatus("선택한 테이블을 읽는 중입니다...", "warn");
      updateDownloadLink();
      try {
        const params = new URLSearchParams({ table: state.selectedTable });
        const previewParams = new URLSearchParams({ table: state.selectedTable, limit: String(limit) });
        const schema = await apiJson(`/hyper/${encodeURIComponent(state.fileId)}/schema?${params}`);
        const count = await apiJson(`/hyper/${encodeURIComponent(state.fileId)}/row-count?${params}`);
        const preview = await apiJson(`/hyper/${encodeURIComponent(state.fileId)}/preview?${previewParams}`);
        renderTable(els.schemaBox, ["컬럼명", "데이터 타입"], schema.columns.map((column) => [column.column_name, column.data_type]));
        renderTable(els.previewBox, preview.columns, preview.rows);
        els.rowCountMetric.textContent = formatNumber(count.row_count);
        els.resultSubtitle.textContent = `${state.filename} / ${state.selectedTable}`;
        await loadInsightSuggestions();
        setStatus("분석 결과를 불러왔습니다.", "ok");
      } catch (error) {
        setStatus(error.message, "error");
      } finally {
        els.loadPreviewButton.disabled = false;
      }
    }
    function renderAskResult(result) {
      if (result.clarification_required) {
        const candidates = result.candidate_columns ? JSON.stringify(result.candidate_columns, null, 2) : "";
        els.clarificationBox.className = "status";
        els.clarificationBox.textContent = `${result.clarification_message || "추가 확인이 필요합니다."}${candidates ? "\\n후보: " + candidates : ""}`;
        els.answerBox.innerHTML = '<div class="empty">컬럼 후보를 확인한 뒤 더 구체적으로 다시 질문해주세요.</div>';
        return;
      }
      els.clarificationBox.className = "status hidden";
      const rows = result.data || [];
      const tableHtml = rows.length
        ? `<div class="data-box"><table><thead><tr>${Object.keys(rows[0]).map((c) => `<th>${escapeHtml(c)}</th>`).join("")}</tr></thead><tbody>${rows.map((row) => `<tr>${Object.values(row).map((v) => `<td>${escapeHtml(v)}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`
        : "";
      els.answerBox.innerHTML = `
        <div class="answer-text">${escapeHtml(result.answer)}</div>
        <div class="meta-grid">
          <div><span class="muted">테이블</span><br>${escapeHtml(result.table || "-")}</div>
          <div><span class="muted">컬럼</span><br>${escapeHtml([result.date_column, result.measure_column, result.dimension_column].filter(Boolean).join(" / ") || "-")}</div>
          <div><span class="muted">기간</span><br>${escapeHtml([result.period_start, result.period_end].filter(Boolean).join(" ~ ") || "-")}</div>
          <div><span class="muted">confidence</span><br>${result.confidence ? Math.round(result.confidence * 100) + "%" : "-"}</div>
        </div>
        ${result.assumptions?.length ? `<div class="muted">가정: ${escapeHtml(result.assumptions.join(" "))}</div>` : ""}
        ${tableHtml}
        <details><summary>SQL 보기</summary><pre class="sql-box">${escapeHtml(result.executed_sql || "SQL이 포함되지 않았습니다.")}</pre></details>
      `;
    }
    async function ask(mode) {
      const question = els.questionInput.value.trim();
      if (!question) { setStatus("질문을 입력해주세요.", "error"); return; }
      els.askButton.disabled = true; els.planButton.disabled = true;
      try {
        const result = await apiJson(`/hyper/${encodeURIComponent(state.fileId)}/ask${mode === "plan" ? "/plan" : ""}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ question, language: "ko", include_sql: els.includeSqlInput.checked }),
        });
        if (mode === "plan") {
          els.answerBox.innerHTML = `<pre class="sql-box">${escapeHtml(JSON.stringify(result.query_plan, null, 2))}</pre>`;
          els.clarificationBox.className = result.clarification_required ? "status" : "status hidden";
          els.clarificationBox.textContent = result.clarification_message || "";
        } else {
          renderAskResult(result);
        }
      } catch (error) {
        els.answerBox.innerHTML = '<div class="empty">질문을 처리하지 못했습니다. 컬럼명을 포함해 다시 질문해보세요.</div>';
        setStatus(error.message, "error");
      } finally {
        els.askButton.disabled = false; els.planButton.disabled = false;
      }
    }
    els.uploadForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const file = els.fileInput.files[0];
      if (!file || !file.name.toLowerCase().endsWith(".hyper")) { setStatus(".hyper 파일을 선택하세요.", "error"); return; }
      const formData = new FormData(); formData.append("file", file);
      els.uploadButton.disabled = true; setStatus("파일을 업로드하고 테이블을 찾는 중입니다...", "warn");
      try {
        const data = await apiJson("/hyper/upload", { method: "POST", body: formData });
        state.fileId = data.file_id; state.filename = data.original_filename; state.tables = data.tables || [];
        els.fileIdMetric.textContent = state.fileId.slice(0, 8) + "..."; els.fileIdMetric.title = state.fileId;
        els.tableCountMetric.textContent = formatNumber(state.tables.length);
        els.refreshButton.disabled = false; els.loadPreviewButton.disabled = !state.tables.length;
        fillTables(); updateDownloadLink(); setWorkspace("data");
        if (state.tables.length) await loadSelectedTable();
      } catch (error) {
        setStatus(error.message, "error");
      } finally {
        els.uploadButton.disabled = false;
      }
    });
    els.tableSelect.addEventListener("change", async () => { state.selectedTable = els.tableSelect.value; updateDownloadLink(); await loadSelectedTable(); });
    els.limitInput.addEventListener("change", updateDownloadLink);
    els.loadPreviewButton.addEventListener("click", loadSelectedTable);
    els.refreshButton.addEventListener("click", loadSelectedTable);
    els.dataWorkspaceTab.addEventListener("click", () => setWorkspace("data"));
    els.insightWorkspaceTab.addEventListener("click", () => setWorkspace("insight"));
    els.previewTab.addEventListener("click", () => setDataTab("preview"));
    els.schemaTab.addEventListener("click", () => setDataTab("schema"));
    els.askButton.addEventListener("click", () => ask("ask"));
    els.planButton.addEventListener("click", () => ask("plan"));
  </script>
</body>
</html>
"""


@app.get("/health")
def health_check():
    return {"status": "ok"}
