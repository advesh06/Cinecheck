/**
 * CineCheck - Dataset Management Controller
 * Handles drag-and-drop file uploads (CSV/XLSX), schema validation, dataset previews, and deletions.
 */

document.addEventListener("DOMContentLoaded", () => {
  initDatasetPage();
});

function initDatasetPage() {
  setupDropzone();
  setupUploadForm();
  loadDatasetsTable();
}

function setupDropzone() {
  const dropzone = document.getElementById("dataset-dropzone");
  const fileInput = document.getElementById("dataset-file-input");
  if (!dropzone || !fileInput) return;

  dropzone.addEventListener("click", () => fileInput.click());

  dropzone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropzone.classList.add("dragover");
  });

  dropzone.addEventListener("dragleave", () => {
    dropzone.classList.remove("dragover");
  });

  dropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropzone.classList.remove("dragover");
    if (e.dataTransfer.files.length > 0) {
      fileInput.files = e.dataTransfer.files;
      handleFileSelected(fileInput.files[0]);
    }
  });

  fileInput.addEventListener("change", () => {
    if (fileInput.files.length > 0) {
      handleFileSelected(fileInput.files[0]);
    }
  });
}

function handleFileSelected(file) {
  const fileNameDisplay = document.getElementById("selected-file-name");
  if (fileNameDisplay) {
    fileNameDisplay.textContent = `Selected: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
    fileNameDisplay.classList.remove("d-none");
  }
}

function setupUploadForm() {
  const form = document.getElementById("dataset-upload-form");
  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const fileInput = document.getElementById("dataset-file-input");
    if (!fileInput.files || fileInput.files.length === 0) {
      showToast("Please select a CSV or XLSX file to upload.", "warning");
      return;
    }

    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append("file", file);

    const btnSubmit = document.getElementById("btn-upload-submit");
    const originalText = btnSubmit.innerHTML;
    btnSubmit.disabled = true;
    btnSubmit.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span>Validating & Ingesting Dataset...`;

    try {
      const res = await fetchAPI("/datasets/upload", {
        method: "POST",
        body: formData
      });

      renderValidationCard(res);
      showToast(res.message, "success");
      loadDatasetsTable();
      form.reset();
      document.getElementById("selected-file-name")?.classList.add("d-none");
    } catch (err) {
      showToast(`Upload failed: ${err.message}`, "danger");
    } finally {
      btnSubmit.disabled = false;
      btnSubmit.innerHTML = originalText;
    }
  });
}

function renderValidationCard(res) {
  const card = document.getElementById("upload-validation-card");
  if (!card) return;

  card.classList.remove("d-none");
  card.scrollIntoView({ behavior: "smooth" });

  document.getElementById("val-filename").textContent = res.filename;
  document.getElementById("val-total").textContent = formatNumber(res.total_rows);
  document.getElementById("val-valid").textContent = formatNumber(res.valid_rows);
  document.getElementById("val-invalid").textContent = formatNumber(res.invalid_rows);
  document.getElementById("val-duplicates").textContent = formatNumber(res.duplicate_rows);
  document.getElementById("val-movies").textContent = (res.movies_detected || []).join(", ") || "General";

  // Preview rows
  const previewTbody = document.getElementById("val-preview-tbody");
  if (previewTbody && res.preview) {
    previewTbody.innerHTML = "";
    res.preview.forEach(row => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td class="font-monospace small">${row.review_id || '—'}</td>
        <td class="fw-semibold">${row.movie_title || 'General'}</td>
        <td class="text-truncate" style="max-width: 320px;">${row.review_text || ''}</td>
        <td>★ ${row.rating !== null ? row.rating : '—'}</td>
        <td><span class="badge bg-secondary">${row.label || 'Unlabelled'}</span></td>
      `;
      previewTbody.appendChild(tr);
    });
  }
}

async function loadDatasetsTable() {
  const tbody = document.getElementById("datasets-table-tbody");
  if (!tbody) return;

  try {
    const data = await fetchAPI("/datasets");
    const datasets = data.datasets || [];
    tbody.innerHTML = "";

    if (datasets.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-muted">No datasets uploaded yet.</td></tr>`;
      return;
    }

    datasets.forEach(d => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td class="fw-bold text-info">#${d.id}</td>
        <td class="fw-semibold">${d.filename}</td>
        <td><span class="badge bg-dark border border-secondary text-uppercase">${d.file_type}</span></td>
        <td>${formatNumber(d.valid_rows)} <small class="text-muted">(${d.invalid_rows} invalid)</small></td>
        <td><span class="badge bg-primary bg-opacity-25 text-primary">${d.analysis_count} runs</span></td>
        <td class="small text-muted">${new Date(d.uploaded_at).toLocaleDateString()}</td>
        <td>
          <div class="d-flex gap-1">
            <a href="/batch" class="btn btn-sm btn-primary-cine py-1 px-2" title="Run Batch Analysis">
              <i class="bi bi-play-circle"></i>
            </a>
            <button class="btn btn-sm btn-danger bg-opacity-25 text-danger border-0 py-1 px-2" onclick="confirmDeleteDataset(${d.id}, '${d.filename}')" title="Delete Dataset">
              <i class="bi bi-trash"></i>
            </button>
          </div>
        </td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error("Failed to load datasets:", err);
  }
}

async function confirmDeleteDataset(datasetId, filename) {
  if (confirm(`Are you sure you want to delete dataset #${datasetId} ("${filename}")?\nThis will also remove all associated review records and batch analyses.`)) {
    try {
      await fetchAPI(`/datasets/${datasetId}`, { method: "DELETE" });
      showToast(`Dataset #${datasetId} deleted successfully.`, "success");
      loadDatasetsTable();
    } catch (err) {
      showToast(`Delete failed: ${err.message}`, "danger");
    }
  }
}
