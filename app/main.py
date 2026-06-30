from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from app.api.hyper_routes import router as hyper_router
from app.api.insight_routes import router as insight_router


app = FastAPI(
    title="Hyper Inspector API",
    version="0.2.0",
    description="Tableau .hyper 파일을 업로드하고 구조, 데이터, insight를 확인하는 API입니다.",
)

app.include_router(hyper_router)
app.include_router(insight_router)


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
      --bg: #f6f7f9;
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

    body {
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: "Segoe UI", system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
      line-height: 1.5;
    }

    header {
      background: #0f1720;
      color: white;
      padding: 26px 24px;
    }

    .wrap {
      width: min(1200px, calc(100% - 32px));
      margin: 0 auto;
    }

    .topbar {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 20px;
    }

    h1 {
      margin: 0 0 6px;
      font-size: clamp(28px, 4vw, 42px);
      letter-spacing: 0;
    }

    h2 { margin: 0; font-size: 18px; }
    h3 { margin: 0 0 10px; font-size: 15px; }

    .subtitle {
      margin: 0;
      max-width: 820px;
      color: #d7dee8;
      font-size: 16px;
    }

    .docs-link {
      color: white;
      border: 1px solid rgba(255,255,255,.28);
      border-radius: 8px;
      padding: 9px 13px;
      text-decoration: none;
      white-space: nowrap;
    }

    main { padding: 22px 0 44px; }

    .layout {
      display: grid;
      grid-template-columns: 340px minmax(0, 1fr);
      gap: 18px;
      align-items: start;
    }

    .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: var(--shadow);
      margin-bottom: 18px;
      min-width: 0;
    }

    .panel-head {
      padding: 17px 20px;
      border-bottom: 1px solid var(--line);
    }

    .panel-head p {
      margin: 4px 0 0;
      color: var(--muted);
      font-size: 14px;
    }

    .panel-body { padding: 20px; min-width: 0; }
    .field { margin-bottom: 16px; }
    .muted { color: var(--muted); font-size: 13px; }

    label {
      display: block;
      margin-bottom: 7px;
      font-weight: 650;
      font-size: 14px;
    }

    input[type="file"],
    select,
    input[type="number"] {
      width: 100%;
      min-height: 42px;
      border: 1px solid #cbd3dd;
      border-radius: 8px;
      background: #fff;
      padding: 9px 11px;
      color: var(--ink);
      font: inherit;
    }

    .button-row {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }

    button,
    .button {
      border: 0;
      border-radius: 8px;
      background: var(--brand);
      color: white;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 40px;
      padding: 9px 13px;
      font: inherit;
      font-weight: 650;
      text-decoration: none;
    }

    button.secondary,
    .button.secondary {
      background: #e8edf3;
      color: #1f2933;
    }

    button:disabled,
    .button.disabled {
      cursor: not-allowed;
      opacity: .55;
    }

    button:not(:disabled):hover,
    .button:not(.disabled):hover {
      background: var(--brand-dark);
    }

    button.secondary:not(:disabled):hover,
    .button.secondary:not(.disabled):hover {
      background: #d7dee7;
    }

    .status {
      margin-top: 16px;
      border-radius: 8px;
      padding: 12px 13px;
      background: #fff4e5;
      color: var(--warn);
      font-size: 14px;
      word-break: break-word;
    }

    .status.ok { background: #e9f8f0; color: var(--ok); }
    .status.error { background: #fdecec; color: var(--error); }

    .summary-grid,
    .insight-grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
      margin-bottom: 16px;
    }

    .metric,
    .mini-card,
    .question-card {
      background: #fbfcfe;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
      min-width: 0;
    }

    .metric span {
      display: block;
      color: var(--muted);
      font-size: 13px;
      margin-bottom: 5px;
    }

    .metric strong {
      display: block;
      font-size: 20px;
      word-break: break-word;
    }

    .workspace-tabs,
    .tabs {
      display: flex;
      gap: 8px;
      border-bottom: 1px solid var(--line);
      margin-bottom: 14px;
    }

    .workspace-tab,
    .tab {
      background: transparent;
      color: var(--muted);
      border-radius: 8px 8px 0 0;
      min-height: 38px;
    }

    .workspace-tab.active,
    .tab.active {
      background: var(--soft);
      color: #0f4f9f;
    }

    .workspace-view[hidden] { display: none; }

    .table-tools {
      display: flex;
      flex-wrap: wrap;
      align-items: end;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 14px;
    }

    .limit-control { width: 150px; }

    .data-box {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 8px;
      overflow-x: auto;
      overflow-y: auto;
      max-height: 480px;
      background: white;
    }

    table {
      width: max-content;
      min-width: 100%;
      border-collapse: collapse;
      table-layout: auto;
      font-size: 13px;
    }

    th,
    td {
      border-bottom: 1px solid var(--line);
      padding: 9px 10px;
      text-align: left;
      vertical-align: top;
      white-space: normal;
      overflow-wrap: anywhere;
      word-break: break-word;
      min-width: 120px;
      max-width: 240px;
    }

    th {
      position: sticky;
      top: 0;
      background: #f4f7fb;
      z-index: 1;
      font-weight: 700;
    }

    tr:hover td { background: #fafcff; }

    .empty {
      border: 1px dashed #bcc7d4;
      border-radius: 8px;
      padding: 26px;
      text-align: center;
      color: var(--muted);
      background: #fbfcfe;
    }

    .chip-list {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }

    .chip {
      display: inline-flex;
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 5px 9px;
      background: white;
      font-size: 13px;
      max-width: 100%;
      overflow-wrap: anywhere;
    }

    .question-card {
      display: grid;
      gap: 8px;
    }

    .sql-box {
      background: #111827;
      color: #f9fafb;
      border-radius: 8px;
      padding: 12px;
      overflow: auto;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
      font-family: Consolas, "Courier New", monospace;
      font-size: 12px;
    }

    details { margin-top: 12px; }
    summary { cursor: pointer; color: #1f5ea8; font-weight: 650; }

    @media (max-width: 900px) {
      .topbar,
      .layout,
      .summary-grid,
      .insight-grid {
        display: grid;
        grid-template-columns: 1fr;
      }

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
        <p class="subtitle">Tableau .hyper 파일을 업로드하고 데이터 구조와 추천 insight를 확인합니다.</p>
      </div>
      <a class="docs-link" href="/docs" target="_blank" rel="noreferrer">API 문서 열기</a>
    </div>
  </header>

  <main class="wrap">
    <section class="layout">
      <aside class="panel">
        <div class="panel-head">
          <h2>파일과 테이블</h2>
          <p>파일을 올린 뒤 테이블을 선택하세요.</p>
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
            <select id="tableSelect" disabled>
              <option value="">먼저 파일을 업로드하세요</option>
            </select>
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

            <div id="previewBox" class="data-box">
              <div class="empty">업로드 후 테이블을 선택하면 샘플 데이터가 표시됩니다.</div>
            </div>
            <div id="schemaBox" class="data-box" hidden>
              <div class="empty">컬럼 구조가 여기에 표시됩니다.</div>
            </div>
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

            <h3>추천 분석 질문</h3>
            <div id="suggestionCards" class="insight-grid"></div>

            <div class="table-tools" style="margin-top:18px;">
              <button id="recentSalesButton" type="button" disabled>최근 3개월 매출 보기</button>
              <button id="trendButton" class="secondary" type="button" disabled>월별 추이 실행</button>
              <button id="topNButton" class="secondary" type="button" disabled>TOP N 실행</button>
            </div>

            <div class="summary-grid">
              <div class="metric"><span>Insight</span><strong id="insightTitle">-</strong></div>
              <div class="metric"><span>값</span><strong id="insightValue">-</strong></div>
              <div class="metric"><span>신뢰도</span><strong id="insightConfidence">-</strong></div>
            </div>

            <h3>월별 추이</h3>
            <div id="trendBox" class="data-box">
              <div class="empty">월별 추이 결과가 여기에 표시됩니다.</div>
            </div>

            <h3 style="margin-top:16px;">TOP N 결과</h3>
            <div id="topNBox" class="data-box">
              <div class="empty">TOP N 결과가 여기에 표시됩니다.</div>
            </div>

            <details>
              <summary>실제 실행 SQL 보기</summary>
              <pre id="sqlBox" class="sql-box">아직 실행된 insight SQL이 없습니다.</pre>
            </details>
          </section>
        </div>
      </section>
    </section>
  </main>

  <script>
    const state = {
      fileId: "",
      filename: "",
      tables: [],
      selectedTable: "",
      suggestions: [],
      semantics: null,
    };

    const els = {
      uploadForm: document.querySelector("#uploadForm"),
      fileInput: document.querySelector("#fileInput"),
      uploadButton: document.querySelector("#uploadButton"),
      status: document.querySelector("#status"),
      tableSelect: document.querySelector("#tableSelect"),
      tableNote: document.querySelector("#tableNote"),
      refreshButton: document.querySelector("#refreshButton"),
      downloadLink: document.querySelector("#downloadLink"),
      fileIdMetric: document.querySelector("#fileIdMetric"),
      tableCountMetric: document.querySelector("#tableCountMetric"),
      rowCountMetric: document.querySelector("#rowCountMetric"),
      resultSubtitle: document.querySelector("#resultSubtitle"),
      limitInput: document.querySelector("#limitInput"),
      loadPreviewButton: document.querySelector("#loadPreviewButton"),
      dataWorkspaceTab: document.querySelector("#dataWorkspaceTab"),
      insightWorkspaceTab: document.querySelector("#insightWorkspaceTab"),
      dataWorkspace: document.querySelector("#dataWorkspace"),
      insightWorkspace: document.querySelector("#insightWorkspace"),
      previewTab: document.querySelector("#previewTab"),
      schemaTab: document.querySelector("#schemaTab"),
      previewBox: document.querySelector("#previewBox"),
      schemaBox: document.querySelector("#schemaBox"),
      profileSummary: document.querySelector("#profileSummary"),
      dateCandidates: document.querySelector("#dateCandidates"),
      measureCandidates: document.querySelector("#measureCandidates"),
      suggestionCards: document.querySelector("#suggestionCards"),
      recentSalesButton: document.querySelector("#recentSalesButton"),
      trendButton: document.querySelector("#trendButton"),
      topNButton: document.querySelector("#topNButton"),
      insightTitle: document.querySelector("#insightTitle"),
      insightValue: document.querySelector("#insightValue"),
      insightConfidence: document.querySelector("#insightConfidence"),
      trendBox: document.querySelector("#trendBox"),
      topNBox: document.querySelector("#topNBox"),
      sqlBox: document.querySelector("#sqlBox"),
    };

    function setStatus(message, type = "warn") {
      els.status.className = `status ${type}`;
      els.status.textContent = message;
    }

    function formatNumber(value) {
      const number = Number(value);
      return Number.isFinite(number)
        ? number.toLocaleString("ko-KR", { maximumFractionDigits: 2 })
        : String(value ?? "-");
    }

    function escapeHtml(value) {
      return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
    }

    function renderTable(container, columns, rows) {
      if (!rows.length) {
        container.innerHTML = '<div class="empty">표시할 데이터가 없습니다.</div>';
        return;
      }
      const header = columns.map((column) => `<th>${escapeHtml(column)}</th>`).join("");
      const body = rows
        .map((row) => `<tr>${row.map((cell) => `<td>${escapeHtml(cell)}</td>`).join("")}</tr>`)
        .join("");
      container.innerHTML = `<table><thead><tr>${header}</tr></thead><tbody>${body}</tbody></table>`;
    }

    function renderSchema(columns) {
      renderTable(
        els.schemaBox,
        ["컬럼명", "데이터 타입"],
        columns.map((column) => [column.column_name, column.data_type])
      );
    }

    async function apiJson(url, options) {
      const response = await fetch(url, options);
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(data.detail || "요청을 처리하지 못했습니다.");
      }
      return data;
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
      if (!state.fileId || !state.selectedTable) {
        els.downloadLink.classList.add("disabled");
        els.downloadLink.href = "#";
        return;
      }
      const params = new URLSearchParams({
        table: state.selectedTable,
        limit: String(els.limitInput.value || 100),
      });
      els.downloadLink.classList.remove("disabled");
      els.downloadLink.href = `/hyper/${encodeURIComponent(state.fileId)}/preview.csv?${params}`;
    }

    function fillTables() {
      els.tableSelect.innerHTML = "";
      if (!state.tables.length) {
        els.tableSelect.disabled = true;
        els.tableSelect.innerHTML = '<option value="">테이블이 없습니다</option>';
        return;
      }
      for (const table of state.tables) {
        const option = document.createElement("option");
        option.value = table;
        option.textContent = table;
        els.tableSelect.appendChild(option);
      }
      els.tableSelect.disabled = false;
      state.selectedTable = state.tables[0];
      els.tableSelect.value = state.selectedTable;
      els.tableNote.textContent = `${state.tables.length}개 테이블을 찾았습니다.`;
    }

    function candidateChips(container, candidates) {
      container.innerHTML = "";
      for (const item of candidates.slice(0, 5)) {
        const chip = document.createElement("span");
        chip.className = "chip";
        chip.textContent = `${item.column_name} (${Math.round(item.confidence * 100)}%)`;
        container.appendChild(chip);
      }
      if (!container.children.length) {
        container.innerHTML = '<span class="muted">후보 없음</span>';
      }
    }

    function bestDate() {
      return state.semantics?.date_candidates?.[0]?.column_name;
    }

    function bestMeasure() {
      return (state.semantics?.sales_candidates?.[0] || state.semantics?.measure_candidates?.[0])?.column_name;
    }

    function bestDimension() {
      const dims = state.semantics?.dimension_candidates || [];
      return (dims.find((item) => ["Region", "Category"].includes(item.column_name)) || dims[0])?.column_name;
    }

    function renderSuggestions(suggestions) {
      els.suggestionCards.innerHTML = "";
      for (const suggestion of suggestions) {
        const card = document.createElement("div");
        card.className = "question-card";
        card.innerHTML = `
          <strong>${escapeHtml(suggestion.title)}</strong>
          <span class="muted">${escapeHtml(suggestion.kind)} · ${Math.round((suggestion.confidence || 0) * 100)}%</span>
        `;
        els.suggestionCards.appendChild(card);
      }
      if (!suggestions.length) {
        els.suggestionCards.innerHTML = '<div class="empty">추천 분석을 만들 수 있는 컬럼 후보가 부족합니다.</div>';
      }
    }

    function renderInsightSummary(result) {
      els.insightTitle.textContent = result.insight_title || "-";
      els.insightValue.textContent = formatNumber(result.value);
      els.insightConfidence.textContent = result.confidence ? `${Math.round(result.confidence * 100)}%` : "-";
      els.sqlBox.textContent = result.executed_sql || "실행 SQL이 없습니다.";
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

        renderSchema(schema.columns);
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

    async function loadInsightSuggestions() {
      const params = new URLSearchParams({ table: state.selectedTable });
      els.profileSummary.textContent = "컬럼 프로파일을 계산하는 중입니다...";
      const data = await apiJson(`/hyper/${encodeURIComponent(state.fileId)}/insights/suggestions?${params}`);
      state.suggestions = data.suggestions || [];
      state.semantics = data.semantics;

      els.profileSummary.textContent =
        `${formatNumber(data.profile_summary.row_count)}행 · ${formatNumber(data.profile_summary.column_count)}개 컬럼`;
      candidateChips(els.dateCandidates, state.semantics.date_candidates || []);
      candidateChips(
        els.measureCandidates,
        [...(state.semantics.sales_candidates || []), ...(state.semantics.measure_candidates || [])]
      );
      renderSuggestions(state.suggestions);

      const canTrend = !!bestDate() && !!bestMeasure();
      els.recentSalesButton.disabled = !canTrend;
      els.trendButton.disabled = !canTrend;
      els.topNButton.disabled = !(bestDimension() && bestMeasure());
    }

    async function runInsight(kind) {
      const body = {
        kind,
        table: state.selectedTable,
        date_column: bestDate(),
        measure_column: bestMeasure(),
        dimension_column: bestDimension(),
        months: 3,
        limit: kind === "monthly_trend" ? 24 : 10,
      };
      const result = await apiJson(`/hyper/${encodeURIComponent(state.fileId)}/insights/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      renderInsightSummary(result);
      if (result.rows && kind === "monthly_trend") {
        renderTable(
          els.trendBox,
          ["월", "합계", "행 수"],
          result.rows.map((row) => [row.month, formatNumber(row.value), formatNumber(row.rows_used)])
        );
      }
      if (result.rows && kind === "top_n") {
        renderTable(
          els.topNBox,
          ["차원 값", "합계", "행 수"],
          result.rows.map((row) => [row.dimension_value, formatNumber(row.value), formatNumber(row.rows_used)])
        );
      }
    }

    els.uploadForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const file = els.fileInput.files[0];
      if (!file || !file.name.toLowerCase().endsWith(".hyper")) {
        setStatus(".hyper 파일을 선택하세요.", "error");
        return;
      }

      const formData = new FormData();
      formData.append("file", file);
      els.uploadButton.disabled = true;
      setStatus("파일을 업로드하고 테이블을 찾는 중입니다...", "warn");

      try {
        const data = await apiJson("/hyper/upload", { method: "POST", body: formData });
        state.fileId = data.file_id;
        state.filename = data.original_filename;
        state.tables = data.tables || [];
        els.fileIdMetric.textContent = state.fileId.slice(0, 8) + "...";
        els.fileIdMetric.title = state.fileId;
        els.tableCountMetric.textContent = formatNumber(state.tables.length);
        els.refreshButton.disabled = false;
        els.loadPreviewButton.disabled = !state.tables.length;
        fillTables();
        updateDownloadLink();
        setWorkspace("data");
        if (state.tables.length) await loadSelectedTable();
      } catch (error) {
        setStatus(error.message, "error");
      } finally {
        els.uploadButton.disabled = false;
      }
    });

    els.tableSelect.addEventListener("change", async () => {
      state.selectedTable = els.tableSelect.value;
      updateDownloadLink();
      await loadSelectedTable();
    });

    els.limitInput.addEventListener("change", updateDownloadLink);
    els.loadPreviewButton.addEventListener("click", loadSelectedTable);
    els.refreshButton.addEventListener("click", loadSelectedTable);
    els.dataWorkspaceTab.addEventListener("click", () => setWorkspace("data"));
    els.insightWorkspaceTab.addEventListener("click", () => setWorkspace("insight"));
    els.previewTab.addEventListener("click", () => setDataTab("preview"));
    els.schemaTab.addEventListener("click", () => setDataTab("schema"));
    els.recentSalesButton.addEventListener("click", () => runInsight("recent_period_sum"));
    els.trendButton.addEventListener("click", () => runInsight("monthly_trend"));
    els.topNButton.addEventListener("click", () => runInsight("top_n"));
  </script>
</body>
</html>
"""


@app.get("/health")
def health_check():
    return {"status": "ok"}
