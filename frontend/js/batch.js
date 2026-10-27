/**
 * CineCheck - Batch Analysis Controller
 * Handles batch dataset selection, progress execution, search, pagination, and file exports.
 */

let currentAnalysisId = null;
let currentPage = 1;
const perPage = 20;

document.addEventListener("DOMContentLoaded", () => {
  initBatchPage();
});

async function initBatchPage() {
  await loadDatasetsDropdown();
  await loadMovieFilters();
  setupBatchForm();
  setupTableFilters();
  setupExportButtons();
}

async function loadDatasetsDropdown() {
  try {
    const data = await fetchAPI("/datasets");
    const select = document.getElementById("batch-dataset-select");
    if (!select) return;

    select.innerHTML = "";
    if (data.datasets && data.datasets.length > 0) {
      data.datasets.forEach(d => {
        const opt = document.createElement("option");
        opt.value = d.id;
        opt.textContent = `#${d.id} - ${d.filename} (${d.valid_rows} rows)`;
        select.appendChild(opt);
      });
    } else {
      select.innerHTML = '<option value="">No datasets uploaded yet (Go to Datasets tab)</option>';
    }
  } catch (err) {
    console.error("Failed to load datasets:", err);
  }
}

async function loadMovieFilters() {
  try {
    const data = await fetchAPI("/analytics/movies");
    const movieFilter = document.getElementById("table-filter-movie");
    if (!movieFilter) return;

    movieFilter.innerHTML = '<option value="all">All Movies</option>';
    if (data.movies) {
      data.movies.forEach(m => {
        const opt = document.createElement("option");
        opt.value = m;
        opt.textContent = m;
        movieFilter.appendChild(opt);
      });
    }
  } catch (err) {
    console.error("Failed to load movies:", err);
  }
}

function setupBatchForm() {
  const form = document.getElementById("batch-run-form");
  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const datasetId = document.getElementById("batch-dataset-select").value;
    const modelChoice = document.getElementById("batch-model-select").value;

    if (!datasetId) {
      showToast("Please select a dataset to analyse.", "warning");
      return;
    }

    const btnRun = document.getElementById("btn-run-batch");
    const progressBar = document.getElementById("batch-progress-bar");
    const progressContainer = document.getElementById("batch-progress-container");

    btnRun.disabled = true;
    progressContainer.classList.remove("d-none");
    progressBar.style.width = "40%";

    try {
      progressBar.style.width = "75%";
      const payload = {
        dataset_id: parseInt(datasetId),
        model_choice: modelChoice
      };

      const res = await fetchAPI("/reviews/batch-analyse", {
        method: "POST",
        body: JSON.stringify(payload)
      });

      progressBar.style.width = "100%";
      currentAnalysisId = res.summary.analysis_id;

      renderSummaryCard(res.summary);
      currentPage = 1;
      await fetchAndRenderTable();

      showToast(`Batch analysis completed on ${res.summary.total_analyzed} records!`, "success");
    } catch (err) {
      showToast(`Batch analysis failed: ${err.message}`, "danger");
    } finally {
      btnRun.disabled = false;
      setTimeout(() => {
        progressContainer.classList.add("d-none");
        progressBar.style.width = "0%";
      }, 1000);
    }
  });
}

function renderSummaryCard(summary) {
  const card = document.getElementById("batch-summary-card");
  if (!card) return;

  card.classList.remove("d-none");
  card.scrollIntoView({ behavior: "smooth", block: "start" });

  document.getElementById("sum-total").textContent = formatNumber(summary.total_analyzed);
  document.getElementById("sum-suspicious").textContent = `${formatNumber(summary.suspicious_count)} (${summary.suspicious_percentage}%)`;
  document.getElementById("sum-genuine").textContent = formatNumber(summary.genuine_count);
  document.getElementById("sum-insufficient").textContent = formatNumber(summary.insufficient_count);
  document.getElementById("sum-avg-score").textContent = summary.average_suspicion_score.toFixed(3);
  document.getElementById("sum-model").textContent = summary.model_used;

  // Show table container and exports
  document.getElementById("batch-results-section")?.classList.remove("d-none");
}

async function fetchAndRenderTable() {
  if (!currentAnalysisId) return;

  const movie = document.getElementById("table-filter-movie")?.value || "all";
  const category = document.getElementById("table-filter-category")?.value || "all";
  const search = document.getElementById("table-search-input")?.value.trim() || "";

  const query = new URLSearchParams({
    page: currentPage,
    per_page: perPage
  });
  if (movie !== "all") query.append("movie", movie);
  if (category !== "all") query.append("category", category);
  if (search) query.append("search", search);

  const tbody = document.getElementById("batch-results-tbody");
  tbody.innerHTML = `<tr><td colspan="8" class="text-center py-4 text-muted"><span class="spinner-border spinner-border-sm me-2"></span>Loading records...</td></tr>`;

  try {
    const data = await fetchAPI(`/analysis-results/${currentAnalysisId}?${query.toString()}`);
    renderTableRows(data.records || []);
    renderPagination(data.page, data.total_pages, data.total);
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="8" class="text-center py-4 text-danger">Error: ${err.message}</td></tr>`;
  }
}

function renderTableRows(records) {
  const tbody = document.getElementById("batch-results-tbody");
  tbody.innerHTML = "";

  if (records.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" class="text-center py-4 text-muted">No records match current filter criteria.</td></tr>`;
    return;
  }

  records.forEach(r => {
    const tr = document.createElement("tr");

    let badgeClass = "badge-genuine";
    let badgeIcon = "bi-shield-check";
    if (r.predicted_label === "Potentially Suspicious") {
      badgeClass = "badge-suspicious";
      badgeIcon = "bi-exclamation-triangle";
    } else if (r.predicted_label === "Insufficient Evidence") {
      badgeClass = "badge-insufficient";
      badgeIcon = "bi-info-circle";
    }

    const simBadge = r.similarity_flag
      ? `<span class="badge bg-danger bg-opacity-25 text-danger border border-danger border-opacity-25" title="Max Cosine Similarity: ${r.similarity_score}"><i class="bi bi-copy me-1"></i>Duplicate Cluster</span>`
      : `<span class="text-muted small">—</span>`;

    const warnings = r.warning_indicators && r.warning_indicators !== "None"
      ? `<span class="text-warning small" title="${r.warning_indicators}"><i class="bi bi-exclamation-circle me-1"></i>${r.warning_indicators.split(';')[0]}</span>`
      : `<span class="text-muted small">None</span>`;

    tr.innerHTML = `
      <td class="small font-monospace">${r.review_id}</td>
      <td class="fw-semibold">${r.movie_title}</td>
      <td class="small text-muted">${r.review_date || '—'}</td>
      <td class="text-truncate" style="max-width: 320px;" title="${r.review_text}">${r.review_text}</td>
      <td><span class="text-warning">★</span> ${r.rating !== null ? r.rating : '—'}</td>
      <td><span class="${badgeClass}"><i class="bi ${badgeIcon}"></i> ${r.predicted_label}</span></td>
      <td><code class="fw-bold">${r.suspicion_score.toFixed(3)}</code></td>
      <td>${warnings}</td>
    `;
    tbody.appendChild(tr);
  });
}

function renderPagination(page, totalPages, totalCount) {
  const container = document.getElementById("table-pagination");
  const info = document.getElementById("table-records-info");
  if (!container) return;

  if (info) {
    info.textContent = `Showing page ${page} of ${totalPages} (${formatNumber(totalCount)} total results)`;
  }

  container.innerHTML = "";
  if (totalPages <= 1) return;

  // Previous
  const prevLi = document.createElement("li");
  prevLi.className = `page-item ${page <= 1 ? 'disabled' : ''}`;
  prevLi.innerHTML = `<button class="page-link bg-dark border-secondary text-white">&laquo; Prev</button>`;
  prevLi.onclick = () => { if (page > 1) { currentPage--; fetchAndRenderTable(); } };
  container.appendChild(prevLi);

  // Current indicator
  const curLi = document.createElement("li");
  curLi.className = `page-item active`;
  curLi.innerHTML = `<span class="page-link bg-primary border-primary">${page} / ${totalPages}</span>`;
  container.appendChild(curLi);

  // Next
  const nextLi = document.createElement("li");
  nextLi.className = `page-item ${page >= totalPages ? 'disabled' : ''}`;
  nextLi.innerHTML = `<button class="page-link bg-dark border-secondary text-white">Next &raquo;</button>`;
  nextLi.onclick = () => { if (page < totalPages) { currentPage++; fetchAndRenderTable(); } };
  container.appendChild(nextLi);
}

function setupTableFilters() {
  document.getElementById("table-filter-movie")?.addEventListener("change", () => {
    currentPage = 1;
    fetchAndRenderTable();
  });
  document.getElementById("table-filter-category")?.addEventListener("change", () => {
    currentPage = 1;
    fetchAndRenderTable();
  });
  document.getElementById("table-search-btn")?.addEventListener("click", () => {
    currentPage = 1;
    fetchAndRenderTable();
  });
  document.getElementById("table-search-input")?.addEventListener("keyup", (e) => {
    if (e.key === "Enter") {
      currentPage = 1;
      fetchAndRenderTable();
    }
  });
}

function setupExportButtons() {
  document.getElementById("btn-export-csv")?.addEventListener("click", () => {
    if (!currentAnalysisId) return;
    window.location.href = `/api/exports/${currentAnalysisId}?format=csv`;
    showToast("Downloading analysed dataset as CSV...", "info");
  });

  document.getElementById("btn-export-excel")?.addEventListener("click", () => {
    if (!currentAnalysisId) return;
    window.location.href = `/api/exports/${currentAnalysisId}?format=xlsx`;
    showToast("Downloading analysed dataset as Excel (XLSX)...", "info");
  });
}
