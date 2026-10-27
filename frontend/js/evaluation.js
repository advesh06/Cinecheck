/**
 * CineCheck - Model Evaluation Controller
 * Fetches held-out test evaluation metrics and renders comparison matrices.
 */

document.addEventListener("DOMContentLoaded", () => {
  loadModelEvaluation();
});

async function loadModelEvaluation() {
  try {
    const data = await fetchAPI("/model/evaluation");
    renderEvaluationData(data);
  } catch (err) {
    showToast(`Failed to load evaluation metrics: ${err.message}`, "danger");
  }
}

function renderEvaluationData(data) {
  // 1. Model Header Overview
  document.getElementById("eval-best-model").textContent = data.selected_best_model || "Logistic Regression";
  document.getElementById("eval-test-samples").textContent = data.test_sample_size || "0";
  document.getElementById("eval-train-samples").textContent = data.train_sample_size || "0";
  document.getElementById("eval-vocab-size").textContent = formatNumber(data.vocabulary_size) + " features";

  // 2. Metric Highlight Cards (Best model)
  const lr = data.logistic_regression || {};
  const nb = data.naive_bayes || {};
  const isLR = data.selected_best_model === "Logistic Regression";
  const activeModel = isLR ? lr : nb;

  document.getElementById("eval-acc-val").textContent = (activeModel.accuracy * 100).toFixed(1) + "%";
  document.getElementById("eval-f1-val").textContent = (activeModel.f1_score * 100).toFixed(1) + "%";
  document.getElementById("eval-prec-val").textContent = (activeModel.precision * 100).toFixed(1) + "%";
  document.getElementById("eval-rec-val").textContent = (activeModel.recall * 100).toFixed(1) + "%";

  // 3. Comparison Table (Logistic Regression vs Naive Bayes)
  const compTbody = document.getElementById("eval-comparison-tbody");
  compTbody.innerHTML = "";
  (data.comparison || []).forEach(row => {
    const tr = document.createElement("tr");
    const lrVal = (row.logistic_regression * 100).toFixed(2) + "%";
    const nbVal = (row.naive_bayes * 100).toFixed(2) + "%";
    const lrIsHigher = row.logistic_regression >= row.naive_bayes;
    tr.innerHTML = `
      <td class="fw-semibold">${row.metric}</td>
      <td class="${lrIsHigher ? 'text-success fw-bold' : ''}">${lrVal}</td>
      <td class="${!lrIsHigher ? 'text-success fw-bold' : ''}">${nbVal}</td>
    `;
    compTbody.appendChild(tr);
  });

  // 4. Confusion Matrix (Logistic Regression)
  const lrCm = lr.confusion_matrix_breakdown || { true_genuine: 0, false_suspicious: 0, false_genuine: 0, true_suspicious: 0 };
  document.getElementById("cm-lr-tn").textContent = lrCm.true_genuine;
  document.getElementById("cm-lr-fp").textContent = lrCm.false_suspicious;
  document.getElementById("cm-lr-fn").textContent = lrCm.false_genuine;
  document.getElementById("cm-lr-tp").textContent = lrCm.true_suspicious;

  // Confusion Matrix (Naive Bayes)
  const nbCm = nb.confusion_matrix_breakdown || { true_genuine: 0, false_suspicious: 0, false_genuine: 0, true_suspicious: 0 };
  document.getElementById("cm-nb-tn").textContent = nbCm.true_genuine;
  document.getElementById("cm-nb-fp").textContent = nbCm.false_suspicious;
  document.getElementById("cm-nb-fn").textContent = nbCm.false_genuine;
  document.getElementById("cm-nb-tp").textContent = nbCm.true_suspicious;

  // 5. Bias & Subgroup Disparity Analysis
  const biasTbody = document.getElementById("eval-bias-tbody");
  biasTbody.innerHTML = "";
  const subgroups = data.bias_analysis?.rating_subgroups || {};
  Object.keys(subgroups).forEach(k => {
    const s = subgroups[k];
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td class="fw-semibold">${k}</td>
      <td>${s.sample_count}</td>
      <td class="text-info">${(s.accuracy * 100).toFixed(1)}%</td>
      <td class="text-success">${(s.f1_score * 100).toFixed(1)}%</td>
    `;
    biasTbody.appendChild(tr);
  });
}
