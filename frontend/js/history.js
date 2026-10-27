/**
 * CineCheck - Analysis History Controller
 * Loads past batch runs, handles exports, and manages deletion.
 */

document.addEventListener("DOMContentLoaded", () => {
  loadHistoryPage();
});

async function loadHistoryPage() {
  try {
    const data = await fetchAPI("/history");
    renderBatchRuns(data.batch_analyses || []);
    renderSingleRuns(data.recent_single_analyses || []);
  } catch (err) {
    showToast(`Failed to load history: ${err.message}`, "danger");
  }
}

function renderBatchRuns(runs) {
  const tbody = document.getElementById("history-batch-tbody");
  if (!tbody) return;

  tbody.innerHTML = "";
  if (runs.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" class="text-center py-4 text-muted">No batch analysis runs recorded yet.</td></tr>`;
    return;
  }

  runs.forEach(r => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td class="fw-bold text-info">#${r.id}</td>
      <td class="fw-semibold">${r.dataset_name}</td>
      <td><span class="badge bg-dark border border-secondary text-light">${r.model_used}</span></td>
      <td>${formatNumber(r.total_analyzed)}</td>
      <td><span class="text-danger fw-bold">${formatNumber(r.suspicious_count)}</span> <small class="text-muted">(${r.suspicious_percentage}%)</small></td>
      <td><code>${r.avg_suspicion_score.toFixed(3)}</code></td>
      <td class="small text-muted">${new Date(r.created_at).toLocaleString()}</td>
      <td>
        <div class="d-flex gap-1">
          <a href="/api/exports/${r.id}?format=csv" class="btn btn-sm btn-secondary-cine py-1 px-2" title="Download CSV">
            <i class="bi bi-filetype-csv text-primary"></i>
          </a>
          <a href="/api/exports/${r.id}?format=xlsx" class="btn btn-sm btn-secondary-cine py-1 px-2" title="Download Excel">
            <i class="bi bi-file-earmark-excel text-success"></i>
          </a>
          <button class="btn btn-sm btn-danger bg-opacity-25 text-danger border-0 py-1 px-2" onclick="deleteHistoryRun(${r.id})" title="Delete Run">
            <i class="bi bi-trash"></i>
          </button>
        </div>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

function renderSingleRuns(singles) {
  const tbody = document.getElementById("history-single-tbody");
  if (!tbody) return;

  tbody.innerHTML = "";
  if (singles.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" class="text-center py-3 text-muted">No individual audits logged yet.</td></tr>`;
    return;
  }

  singles.forEach(s => {
    const tr = document.createElement("tr");
    const badge = s.predicted_label === "Potentially Suspicious" ? "badge-suspicious" : "badge-genuine";
    tr.innerHTML = `
      <td class="fw-semibold">${s.movie_title}</td>
      <td class="text-truncate" style="max-width: 320px;" title="${s.review_text}">${s.review_text}</td>
      <td><span class="${badge}">${s.predicted_label}</span></td>
      <td><code>${s.suspicion_score.toFixed(3)}</code></td>
      <td>${s.model_used}</td>
      <td class="small text-muted">${new Date(s.created_at).toLocaleString()}</td>
    `;
    tbody.appendChild(tr);
  });
}

async function deleteHistoryRun(runId) {
  if (confirm(`Delete batch analysis record #${runId} and all associated per-review predictions?`)) {
    try {
      await fetchAPI(`/history/${runId}`, { method: "DELETE" });
      showToast(`Analysis run #${runId} deleted successfully.`, "success");
      loadHistoryPage();
    } catch (err) {
      showToast(`Failed to delete run: ${err.message}`, "danger");
    }
  }
}
