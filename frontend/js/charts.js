/**
 * CineCheck - Chart.js Helpers & Dark Theme Configurations
 */

const chartRegistry = {};

function initChartDefaults() {
  if (typeof Chart === "undefined") return;

  Chart.defaults.color = "#94a3b8";
  Chart.defaults.font.family = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif";
  Chart.defaults.plugins.legend.labels.color = "#94a3b8";
  Chart.defaults.plugins.tooltip.backgroundColor = "#1e293b";
  Chart.defaults.plugins.tooltip.titleColor = "#f8fafc";
  Chart.defaults.plugins.tooltip.bodyColor = "#cbd5e1";
  Chart.defaults.plugins.tooltip.borderColor = "#334155";
  Chart.defaults.plugins.tooltip.borderWidth = 1;
  Chart.defaults.plugins.tooltip.padding = 10;
  Chart.defaults.plugins.tooltip.cornerRadius = 6;
}

function destroyChartIfExists(canvasId) {
  if (chartRegistry[canvasId]) {
    chartRegistry[canvasId].destroy();
    delete chartRegistry[canvasId];
  }
}

function renderDoughnut(canvasId, labels, data, colors) {
  initChartDefaults();
  destroyChartIfExists(canvasId);

  const ctx = document.getElementById(canvasId)?.getContext("2d");
  if (!ctx) return;

  chartRegistry[canvasId] = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: labels,
      datasets: [{
        data: data,
        backgroundColor: colors || ["#ef4444", "#10b981", "#64748b"],
        borderWidth: 2,
        borderColor: "#151e32",
        hoverOffset: 4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "bottom",
          labels: { boxWidth: 14, padding: 16 }
        }
      },
      cutout: "70%"
    }
  });
}

function renderBarChart(canvasId, labels, data, labelName = "Count", barColor = "#6366f1") {
  initChartDefaults();
  destroyChartIfExists(canvasId);

  const ctx = document.getElementById(canvasId)?.getContext("2d");
  if (!ctx) return;

  chartRegistry[canvasId] = new Chart(ctx, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [{
        label: labelName,
        data: data,
        backgroundColor: barColor,
        borderRadius: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false }
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { color: "#94a3b8" }
        },
        y: {
          grid: { color: "rgba(255, 255, 255, 0.05)" },
          ticks: { color: "#94a3b8", precision: 0 },
          beginAtZero: true
        }
      }
    }
  });
}

function renderHorizontalBarChart(canvasId, labels, data, labelName = "Suspicious %", barColor = "#f43f5e") {
  initChartDefaults();
  destroyChartIfExists(canvasId);

  const ctx = document.getElementById(canvasId)?.getContext("2d");
  if (!ctx) return;

  chartRegistry[canvasId] = new Chart(ctx, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [{
        label: labelName,
        data: data,
        backgroundColor: barColor,
        borderRadius: 4
      }]
    },
    options: {
      indexAxis: "y",
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => ` ${ctx.parsed.x}% suspicious`
          }
        }
      },
      scales: {
        x: {
          grid: { color: "rgba(255, 255, 255, 0.05)" },
          ticks: {
            color: "#94a3b8",
            callback: (val) => `${val}%`
          },
          min: 0,
          max: 100
        },
        y: {
          grid: { display: false },
          ticks: { color: "#94a3b8" }
        }
      }
    }
  });
}

function renderLineChart(canvasId, labels, datasets) {
  initChartDefaults();
  destroyChartIfExists(canvasId);

  const ctx = document.getElementById(canvasId)?.getContext("2d");
  if (!ctx) return;

  chartRegistry[canvasId] = new Chart(ctx, {
    type: "line",
    data: {
      labels: labels,
      datasets: datasets
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: "index",
        intersect: false
      },
      plugins: {
        legend: {
          position: "top",
          labels: { boxWidth: 14, padding: 12 }
        }
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { color: "#94a3b8" }
        },
        y: {
          grid: { color: "rgba(255, 255, 255, 0.05)" },
          ticks: { color: "#94a3b8", precision: 0 },
          beginAtZero: true
        }
      }
    }
  });
}
