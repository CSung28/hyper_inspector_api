from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from app.api.hyper_routes import router as hyper_router


app = FastAPI(
    title="Hyper Inspector API",
    version="0.1.0",
    description="Tableau .hyper 파일을 업로드하고 구조와 데이터를 확인하는 API입니다.",
)

app.include_router(hyper_router)


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
      color-scheme: light;
      --bg: #f6f7f9;
      --panel: #ffffff;
      --ink: #20242a;
      --muted: #687282;
      --line: #dfe4ea;
      --brand: #1473e6;
      --brand-dark: #0c58b6;
      --ok: #1d8f5f;
      --warn: #b65c00;
      --error: #c93535;
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
      padding: 28px 24px;
    }

    .wrap {
      width: min(1180px, calc(100% - 32px));
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
      font-size: clamp(28px, 4vw, 44px);
      letter-spacing: 0;
    }

    .subtitle {
      margin: 0;
      max-width: 760px;
      color: #d7dee8;
      font-size: 16px;
    }

    .docs-link {
      color: white;
      border: 1px solid rgba(255, 255, 255, 0.28);
      border-radius: 8px;
      padding: 9px 13px;
      text-decoration: none;
      white-space: nowrap;
    }

    main { padding: 24px 0 44px; }

    .steps {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 12px;
      margin-bottom: 18px;
    }

    .step {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px 16px;
      min-height: 82px;
    }

    .step strong {
      display: block;
      margin-bottom: 4px;
      font-size: 15px;
    }

    .step span {
      color: var(--muted);
      font-size: 14px;
    }

    .layout {
      display: grid;
      grid-template-columns: 360px 1fr;
      gap: 18px;
      align-items: start;
    }

    .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: var(--shadow);
    }

    .panel-head {
      padding: 18px 20px;
      border-bottom: 1px solid var(--line);
    }

    .panel-head h2 {
      margin: 0;
      font-size: 18px;
    }

    .panel-head p {
      margin: 4px 0 0;
      color: var(--muted);
      font-size: 14px;
    }

    .panel-body { padding: 20px; }

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

    input[type="file"] { padding: 10px; }

    .field { margin-bottom: 16px; }

    .field-note {
      margin-top: 6px;
      color: var(--muted);
      font-size: 13px;
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
      gap: 7px;
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
      opacity: 0.55;
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
      background: #f1f4f8;
      color: #354052;
      font-size: 14px;
      word-break: break-word;
    }

    .status.ok { background: #e9f8f0; color: #176846; }
    .status.warn { background: #fff4e5; color: var(--warn); }
    .status.error { background: #fdecec; color: var(--error); }

    .summary-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 12px;
      margin-bottom: 18px;
    }

    .metric {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
      background: #fbfcfe;
      min-height: 86px;
    }

    .metric span {
      display: block;
      color: var(--muted);
      font-size: 13px;
      margin-bottom: 5px;
    }

    .metric strong {
      display: block;
      font-size: 22px;
      word-break: break-word;
    }

    .table-tools {
      display: flex;
      flex-wrap: wrap;
      align-items: end;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 14px;
    }

    .limit-control { width: 150px; }

    .tabs {
      display: flex;
      gap: 8px;
      margin-bottom: 12px;
      border-bottom: 1px solid var(--line);
    }

    .tab {
      background: transparent;
      color: var(--muted);
      border-radius: 8px 8px 0 0;
      min-height: 38px;
    }

    .tab.active {
      background: var(--soft);
      color: #0f4f9f;
    }

    .data-box {
      border: 1px solid var(--line);
      border-radius: 8px;
      overflow: auto;
      max-height: 520px;
      background: white;
    }

    table {
      width: 100%;
      border-collapse: collapse;
      min-width: 620px;
      font-size: 14px;
    }

    th,
    td {
      border-bottom: 1px solid var(--line);
      padding: 10px 12px;
      text-align: left;
      vertical-align: top;
      white-space: nowrap;
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
      padding: 28px;
      text-align: center;
      color: var(--muted);
      background: #fbfcfe;
    }

    @media (max-width: 900px) {
      .topbar,
      .layout,
      .steps,
      .summary-grid {
        grid-template-columns: 1fr;
      }

      .topbar { display: grid; }
      .docs-link { width: fit-content; }
    }
  </style>
</head>
<body>
  <header>
    <div class="wrap topbar">
      <div>
        <h1>Hyper Inspector</h1>
        <p class="subtitle">Tableau .hyper 파일을 올리면 테이블 목록, 컬럼 구조, 행 수, 미리보기 데이터를 한 화면에서 확인할 수 있습니다.</p>
      </div>
      <a class="docs-link" href="/docs" target="_blank" rel="noreferrer">API 문서 열기</a>
    </div>
  </header>

  <main class="wrap">
    <section class="steps" aria-label="사용 순서">
      <div class="step"><strong>1. 파일 업로드</strong><span>분석할 .hyper 파일을 선택합니다.</span></div>
      <div class="step"><strong>2. 테이블 선택</strong><span>파일 안의 테이블을 목록에서 고릅니다.</span></div>
      <div class="step"><strong>3. 결과 확인</strong><span>컬럼, 행 수, 샘플 데이터를 확인합니다.</span></div>
    </section>

    <section class="layout">
      <aside class="panel">
        <div class="panel-head">
          <h2>파일과 테이블</h2>
          <p>처음 사용해도 순서대로 누르면 됩니다.</p>
        </div>
        <div class="panel-body">
          <form id="uploadForm">
            <div class="field">
              <label for="fileInput">.hyper 파일</label>
              <input id="fileInput" name="file" type="file" accept=".hyper" required />
              <div class="field-note">예: Sample - Superstore.hyper</div>
            </div>
            <button id="uploadButton" type="submit">파일 분석 시작</button>
          </form>

          <div id="status" class="status warn">아직 파일이 업로드되지 않았습니다.</div>

          <div class="field" style="margin-top: 18px;">
            <label for="tableSelect">테이블 선택</label>
            <select id="tableSelect" disabled>
              <option value="">먼저 파일을 업로드하세요</option>
            </select>
            <div id="tableNote" class="field-note">테이블이 여러 개면 원하는 항목을 선택하세요.</div>
          </div>

          <div class="button-row">
            <button id="refreshButton" class="secondary" type="button" disabled>다시 불러오기</button>
            <a id="downloadLink" class="button secondary disabled" href="#" aria-disabled="true">CSV 다운로드</a>
          </div>
        </div>
      </aside>

      <section class="panel">
        <div class="panel-head">
          <h2>분석 결과</h2>
          <p id="resultSubtitle">파일을 업로드하면 이곳에 결과가 표시됩니다.</p>
        </div>
        <div class="panel-body">
          <div class="summary-grid">
            <div class="metric"><span>파일 ID</span><strong id="fileIdMetric">-</strong></div>
            <div class="metric"><span>테이블 수</span><strong id="tableCountMetric">-</strong></div>
            <div class="metric"><span>선택 테이블 행 수</span><strong id="rowCountMetric">-</strong></div>
          </div>

          <div class="table-tools">
            <div class="limit-control">
              <label for="limitInput">미리보기 행 수</label>
              <input id="limitInput" type="number" min="1" max="1000" value="100" />
            </div>
            <div class="button-row">
              <button id="loadPreviewButton" type="button" disabled>미리보기 새로고침</button>
            </div>
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
      previewTab: document.querySelector("#previewTab"),
      schemaTab: document.querySelector("#schemaTab"),
      previewBox: document.querySelector("#previewBox"),
      schemaBox: document.querySelector("#schemaBox"),
    };

    function setStatus(message, type = "warn") {
      els.status.className = `status ${type}`;
      els.status.textContent = message;
    }

    function formatNumber(value) {
      return Number(value).toLocaleString("ko-KR");
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
      const rows = columns.map((column) => [column.column_name, column.data_type]);
      renderTable(els.schemaBox, ["컬럼명", "데이터 타입"], rows);
    }

    function updateDownloadLink() {
      if (!state.fileId || !state.selectedTable) {
        els.downloadLink.classList.add("disabled");
        els.downloadLink.setAttribute("aria-disabled", "true");
        els.downloadLink.href = "#";
        return;
      }

      const params = new URLSearchParams({
        table: state.selectedTable,
        limit: String(els.limitInput.value || 100),
      });
      els.downloadLink.classList.remove("disabled");
      els.downloadLink.removeAttribute("aria-disabled");
      els.downloadLink.href = `/hyper/${encodeURIComponent(state.fileId)}/preview.csv?${params}`;
    }

    function setActiveTab(tab) {
      const isPreview = tab === "preview";
      els.previewTab.classList.toggle("active", isPreview);
      els.schemaTab.classList.toggle("active", !isPreview);
      els.previewBox.hidden = !isPreview;
      els.schemaBox.hidden = isPreview;
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

    async function apiJson(url, options) {
      const response = await fetch(url, options);
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(data.detail || "요청을 처리하지 못했습니다.");
      }
      return data;
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
        setStatus("분석 결과를 불러왔습니다.", "ok");
      } catch (error) {
        setStatus(error.message, "error");
      } finally {
        els.loadPreviewButton.disabled = false;
      }
    }

    els.uploadForm.addEventListener("submit", async (event) => {
      event.preventDefault();

      const file = els.fileInput.files[0];
      if (!file) {
        setStatus("업로드할 .hyper 파일을 선택하세요.", "error");
        return;
      }

      if (!file.name.toLowerCase().endsWith(".hyper")) {
        setStatus(".hyper 파일만 업로드할 수 있습니다.", "error");
        return;
      }

      const formData = new FormData();
      formData.append("file", file);
      els.uploadButton.disabled = true;
      setStatus("파일을 업로드하고 테이블을 찾는 중입니다...", "warn");

      try {
        const data = await apiJson("/hyper/upload", {
          method: "POST",
          body: formData,
        });

        state.fileId = data.file_id;
        state.filename = data.original_filename;
        state.tables = data.tables || [];
        state.selectedTable = "";

        els.fileIdMetric.textContent = state.fileId.slice(0, 8) + "...";
        els.fileIdMetric.title = state.fileId;
        els.tableCountMetric.textContent = formatNumber(state.tables.length);
        els.refreshButton.disabled = false;
        els.loadPreviewButton.disabled = !state.tables.length;
        fillTables();
        setStatus(`${state.filename} 업로드 완료`, "ok");
        updateDownloadLink();

        if (state.tables.length) {
          await loadSelectedTable();
        }
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
    els.previewTab.addEventListener("click", () => setActiveTab("preview"));
    els.schemaTab.addEventListener("click", () => setActiveTab("schema"));

    els.downloadLink.addEventListener("click", (event) => {
      if (els.downloadLink.classList.contains("disabled")) {
        event.preventDefault();
      }
    });
  </script>
</body>
</html>
"""


@app.get("/health")
def health_check():
    return {"status": "ok"}
