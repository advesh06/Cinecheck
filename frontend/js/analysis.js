/**
 * CineCheck - Individual Review Analysis Controller
 * Manages form interactions, sample review presets, and explainability visualizations.
 */

document.addEventListener("DOMContentLoaded", () => {
  initAnalysisPage();
});

const SAMPLE_PRESETS = {
  genuine: {
    movie: "Chhaava",
    rating: "4.0",
    text: "Watched the first show at PVR today. The lead actor carries the film with an intense and grounded screen presence. The cinematography captures stunning color tones, while the sound design truly immerses you in the battlefield. The screenplay is tightly woven in the first half, though the pacing stumbles slightly before reaching the climax. Definitely worth catching in a good theater with friends."
  },
  suspicious: {
    movie: "War 2",
    rating: "5.0",
    text: "ALL TIME HISTORIC BLOCKBUSTER RECORD BREAKER!!! GO BOOK TICKETS RIGHT NOW WITH ENTIRE FAMILY!! 🔥🔥🔥 BEST MOVIE EVER IN INDIAN CINEMA HISTORY! MIND BLOWING MASTERPIECE 10/10 RATING!! FULL PAISA VASOOL ENTERTAINMENT!!"
  },
  mismatch: {
    movie: "Game Changer",
    rating: "1.0",
    text: "ALL TIME BLOCKBUSTER MASTERPIECE MUST WATCH GO BOOK TICKETS RIGHT NOW WITH FAMILY! MIND BLOWING RECORD BREAKING FILM!"
  }
};

function initAnalysisPage() {
  setupSamplePresetButtons();
  setupAnalysisForm();
  loadRecentAudits();
}

function setupSamplePresetButtons() {
  document.getElementById("btn-preset-genuine")?.addEventListener("click", () => {
    applyPreset(SAMPLE_PRESETS.genuine);
  });
  document.getElementById("btn-preset-suspicious")?.addEventListener("click", () => {
    applyPreset(SAMPLE_PRESETS.suspicious);
  });
  document.getElementById("btn-preset-mismatch")?.addEventListener("click", () => {
    applyPreset(SAMPLE_PRESETS.mismatch);
  });
}

function applyPreset(preset) {
  document.getElementById("input-movie").value = preset.movie;
  document.getElementById("input-rating").value = preset.rating;
  document.getElementById("input-review-text").value = preset.text;
  showToast(`Loaded ${preset.movie} preset review.`, "info");
}

function setupAnalysisForm() {
  const form = document.getElementById("single-analysis-form");
  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const reviewText = document.getElementById("input-review-text").value.trim();
    const movieTitle = document.getElementById("input-movie").value.trim() || "Unspecified Movie";
    const ratingVal = document.getElementById("input-rating").value;
    const modelChoice = document.getElementById("input-model-choice").value;

    if (!reviewText) {
      showToast("Please enter a review text to analyse.", "warning");
      return;
    }

    const btnSubmit = document.getElementById("btn-analyse-submit");
    const originalBtnHtml = btnSubmit.innerHTML;
    btnSubmit.disabled = true;
    btnSubmit.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span>Analysing NLP & Features...`;

    try {
      const payload = {
        review_text: reviewText,
        movie_title: movieTitle,
        rating: ratingVal ? parseFloat(ratingVal) : null,
        model_choice: modelChoice
      };

      const result = await fetchAPI("/reviews/analyse", {
        method: "POST",
        body: JSON.stringify(payload)
      });

      renderAnalysisResult(result, reviewText);
      loadRecentAudits();
      showToast("Review analysis complete!", "success");
    } catch (err) {
      showToast(`Analysis failed: ${err.message}`, "danger");
    } finally {
      btnSubmit.disabled = false;
      btnSubmit.innerHTML = originalBtnHtml;
    }
  });
}

function renderAnalysisResult(res, originalText) {
  const resultCard = document.getElementById("analysis-result-container");
  if (!resultCard) return;

  resultCard.classList.remove("d-none");
  resultCard.scrollIntoView({ behavior: "smooth", block: "start" });

  // 1. Badge & Header
  const badgeContainer = document.getElementById("result-category-badge");
  const cat = res.predicted_category;
  if (cat === "Potentially Suspicious") {
    badgeContainer.className = "badge-suspicious fs-6";
    badgeContainer.innerHTML = `<i class="bi bi-exclamation-triangle-fill"></i> Potentially Suspicious`;
  } else if (cat === "More Likely Genuine") {
    badgeContainer.className = "badge-genuine fs-6";
    badgeContainer.innerHTML = `<i class="bi bi-shield-check"></i> More Likely Genuine`;
  } else {
    badgeContainer.className = "badge-insufficient fs-6";
    badgeContainer.innerHTML = `<i class="bi bi-info-circle"></i> Insufficient Evidence`;
  }

  // 2. Metrics
  document.getElementById("result-score-val").textContent = res.suspicion_score.toFixed(3);
  document.getElementById("result-confidence-val").textContent = `${res.confidence_percentage}%`;
  document.getElementById("result-model-used").textContent = res.model_used;

  // Score Bar
  const scoreBar = document.getElementById("result-score-bar");
  const scorePct = Math.round(res.suspicion_score * 100);
  scoreBar.style.width = `${scorePct}%`;
  if (res.suspicion_score >= 0.5) {
    scoreBar.className = "progress-bar bg-danger";
  } else {
    scoreBar.className = "progress-bar bg-success";
  }

  // 3. Raw vs Preprocessed Text comparison
  document.getElementById("result-raw-text").textContent = originalText;
  document.getElementById("result-cleaned-text").textContent = res.processed_text || "[No tokens remaining]";

  // 4. Warning Indicators
  const warningsList = document.getElementById("result-warning-indicators");
  warningsList.innerHTML = "";
  if (res.warning_indicators && res.warning_indicators.length > 0) {
    res.warning_indicators.forEach(w => {
      const chip = document.createElement("span");
      chip.className = "chip-warning me-2 mb-2";
      chip.innerHTML = `<i class="bi bi-exclamation-circle me-1"></i> ${w}`;
      warningsList.appendChild(chip);
    });
  } else {
    warningsList.innerHTML = `<span class="text-success small"><i class="bi bi-check-circle me-1"></i> No suspicious stylistic heuristics triggered</span>`;
  }

  // 5. TF-IDF Influential Features (Explainability Chips)
  const featContainer = document.getElementById("result-features-cloud");
  featContainer.innerHTML = "";
  const exp = res.explanation || {};
  const suspFeats = exp.top_suspicious_features || [];
  const genFeats = exp.top_genuine_features || [];

  if (suspFeats.length === 0 && genFeats.length === 0) {
    featContainer.innerHTML = `<span class="text-muted small">No significant TF-IDF keyword weights extracted.</span>`;
  } else {
    suspFeats.forEach(f => {
      const chip = document.createElement("span");
      chip.className = "chip-suspicious";
      chip.title = `Suspicion Weight: +${f.weight}`;
      chip.innerHTML = `<i class="bi bi-arrow-up-circle me-1"></i> ${f.feature} <small class="opacity-75 ms-1">+${f.weight}</small>`;
      featContainer.appendChild(chip);
    });
    genFeats.forEach(f => {
      const chip = document.createElement("span");
      chip.className = "chip-genuine";
      chip.title = `Genuine Weight: -${f.weight}`;
      chip.innerHTML = `<i class="bi bi-arrow-down-circle me-1"></i> ${f.feature} <small class="opacity-75 ms-1">-${f.weight}</small>`;
      featContainer.appendChild(chip);
    });
  }

  // 6. Explanation Summary
  document.getElementById("result-explanation-summary").textContent = exp.explanation_summary || "Automated linguistic inference completed.";
}

async function loadRecentAudits() {
  const tbody = document.getElementById("recent-audits-tbody");
  if (!tbody) return;

  try {
    const data = await fetchAPI("/history");
    const singles = data.recent_single_analyses || [];
    tbody.innerHTML = "";

    if (singles.length === 0) {
      tbody.innerHTML = `<tr><td colspan="5" class="text-center text-muted py-3">No recent individual reviews analysed.</td></tr>`;
      return;
    }

    singles.forEach(s => {
      const tr = document.createElement("tr");
      const badge = s.predicted_label === "Potentially Suspicious" ? "badge-suspicious" : "badge-genuine";
      tr.innerHTML = `
        <td class="fw-semibold">${s.movie_title}</td>
        <td class="text-truncate" style="max-width: 280px;" title="${s.review_text}">${s.review_text}</td>
        <td><span class="${badge}">${s.predicted_label}</span></td>
        <td><code>${s.suspicion_score.toFixed(3)}</code></td>
        <td class="text-muted small">${new Date(s.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error("Failed to load audit history:", err);
  }
}
