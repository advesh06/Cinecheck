/**
 * CineCheck - Dashboard Controller
 * Fetches real computed analytics from the backend SQLite database and renders charts.
 */

document.addEventListener("DOMContentLoaded", () => {
  initDashboard();
});

async function initDashboard() {
  await loadMovieDropdown();
  await refreshDashboardData();
  setupFilterHandlers();
}

async function loadMovieDropdown() {
  try {
    const data = await fetchAPI("/analytics/movies");
    const movieSelect = document.getElementById("filter-movie");
    if (!movieSelect) return;

    movieSelect.innerHTML = '<option value="all">All Movies</option>';
    if (data.movies && data.movies.length > 0) {
      data.movies.forEach(m => {
        const opt = document.createElement("option");
        opt.value = m;
        opt.textContent = m;
        movieSelect.appendChild(opt);
      });
    }
  } catch (err) {
    console.error("Failed to load movies dropdown:", err);
  }
}

async function refreshDashboardData() {
  const movie = document.getElementById("filter-movie")?.value || "all";
  const dateFrom = document.getElementById("filter-date-from")?.value || "";
  const dateTo = document.getElementById("filter-date-to")?.value || "";

  const queryParams = new URLSearchParams();
  if (movie !== "all") queryParams.append("movie", movie);
  if (dateFrom) queryParams.append("date_from", dateFrom);
  if (dateTo) queryParams.append("date_to", dateTo);

  try {
    const summary = await fetchAPI(`/analytics/summary?${queryParams.toString()}`);
    updateStatCards(summary);
    renderDashboardCharts(summary);
    renderMovieTable(summary.movie_breakdown || []);
  } catch (err) {
    showToast(`Failed to load dashboard data: ${err.message}`, "danger");
  }
}

function updateStatCards(data) {
  document.getElementById("stat-total-reviews").textContent = formatNumber(data.total_reviews);
  document.getElementById("stat-suspicious-count").textContent = formatNumber(data.suspicious_count);
  document.getElementById("stat-genuine-count").textContent = formatNumber(data.genuine_count);
  document.getElementById("stat-suspicious-pct").textContent = formatPercentage(data.suspicious_percentage);
  document.getElementById("stat-avg-rating").textContent = (data.average_rating || 0).toFixed(1) + " / 5.0";
  document.getElementById("stat-avg-score").textContent = (data.average_suspicion_score || 0).toFixed(3);
}

function renderDashboardCharts(data) {
  // 1. Classification Distribution Doughnut
  renderDoughnut(
    "chart-classification",
    ["Potentially Suspicious", "More Likely Genuine", "Insufficient Evidence"],
    [data.suspicious_count || 0, data.genuine_count || 0, data.insufficient_count || 0],
    ["#ef4444", "#10b981", "#64748b"]
  );

  // 2. Rating Distribution Bar Chart
  const rDist = data.rating_distribution || { labels: [], counts: [] };
  renderBarChart(
    "chart-rating-dist",
    rDist.labels,
    rDist.counts,
    "Number of Reviews",
    "#6366f1"
  );

  // 3. Movie-wise Suspicious % (Top 8 movies)
  const movies = (data.movie_breakdown || []).slice(0, 10);
  const movieLabels = movies.map(m => m.movie_title.length > 18 ? m.movie_title.slice(0, 18) + "..." : m.movie_title);
  const moviePcts = movies.map(m => m.suspicious_percentage);
  renderHorizontalBarChart(
    "chart-movie-pct",
    movieLabels,
    moviePcts,
    "Suspicious %",
    "#f43f5e"
  );

  // 4. Timeline Trend Line Chart
  const timeline = data.timeline || { labels: [], total_series: [], suspicious_series: [] };
  renderLineChart(
    "chart-timeline",
    timeline.labels.length > 0 ? timeline.labels : ["No Date Data"],
    [
      {
        label: "Total Reviews",
        data: timeline.total_series.length > 0 ? timeline.total_series : [0],
        borderColor: "#6366f1",
        backgroundColor: "rgba(99, 102, 241, 0.1)",
        tension: 0.3,
        fill: true
      },
      {
        label: "Potentially Suspicious",
        data: timeline.suspicious_series.length > 0 ? timeline.suspicious_series : [0],
        borderColor: "#ef4444",
        backgroundColor: "rgba(239, 68, 68, 0.1)",
        tension: 0.3,
        fill: true
      }
    ]
  );
}

function renderMovieTable(movieList) {
  const tbody = document.getElementById("movie-breakdown-tbody");
  if (!tbody) return;

  tbody.innerHTML = "";
  if (movieList.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" class="text-center text-muted py-4">No movie analytics found for current filter.</td></tr>`;
    return;
  }

  movieList.forEach(m => {
    const tr = document.createElement("tr");
    const pctBadgeClass = m.suspicious_percentage > 40 ? "text-danger fw-bold" : (m.suspicious_percentage > 20 ? "text-warning" : "text-success");
    tr.innerHTML = `
      <td class="fw-semibold">${m.movie_title}</td>
      <td>${formatNumber(m.total_reviews)}</td>
      <td><span class="text-danger fw-semibold">${formatNumber(m.suspicious_count)}</span></td>
      <td class="${pctBadgeClass}">${formatPercentage(m.suspicious_percentage)}</td>
      <td><span class="text-warning">★</span> ${m.avg_rating.toFixed(1)}</td>
      <td><span class="badge bg-dark border border-secondary">${m.avg_suspicion_score.toFixed(3)}</span></td>
    `;
    tbody.appendChild(tr);
  });
}

function setupFilterHandlers() {
  const form = document.getElementById("dashboard-filter-form");
  if (form) {
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      refreshDashboardData();
    });
  }

  const resetBtn = document.getElementById("btn-reset-filters");
  if (resetBtn) {
    resetBtn.addEventListener("click", () => {
      document.getElementById("filter-movie").value = "all";
      document.getElementById("filter-date-from").value = "";
      document.getElementById("filter-date-to").value = "";
      refreshDashboardData();
    });
  }
}
