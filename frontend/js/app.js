/**
 * CineCheck - Global JavaScript Utilities & API Helper
 */

const API_BASE = "/api";

async function fetchAPI(endpoint, options = {}) {
  try {
    const url = endpoint.startsWith("http") ? endpoint : `${API_BASE}${endpoint.startsWith('/') ? '' : '/'}${endpoint}`;
    const defaultHeaders = {};
    
    // Don't set Content-Type for FormData
    if (!(options.body instanceof FormData)) {
      defaultHeaders["Content-Type"] = "application/json";
    }

    const config = {
      ...options,
      headers: {
        ...defaultHeaders,
        ...(options.headers || {})
      }
    };

    const res = await fetch(url, config);
    const data = await res.json().catch(() => ({}));

    if (!res.ok) {
      const errorMsg = data.error || data.message || `API error (${res.status})`;
      throw new Error(errorMsg);
    }
    return data;
  } catch (err) {
    console.error("API Call Error:", err);
    throw err;
  }
}

function showToast(message, type = "info") {
  let toastContainer = document.getElementById("cinecheck-toast-container");
  if (!toastContainer) {
    toastContainer = document.createElement("div");
    toastContainer.id = "cinecheck-toast-container";
    toastContainer.style.position = "fixed";
    toastContainer.style.bottom = "20px";
    toastContainer.style.right = "20px";
    toastContainer.style.zIndex = "9999";
    document.body.appendChild(toastContainer);
  }

  const bgClass = {
    success: "bg-success text-white",
    danger: "bg-danger text-white",
    warning: "bg-warning text-dark",
    info: "bg-primary text-white"
  }[type] || "bg-secondary text-white";

  const toastEl = document.createElement("div");
  toastEl.className = `toast align-items-center ${bgClass} border-0 show shadow-lg mb-2`;
  toastEl.setAttribute("role", "alert");
  toastEl.setAttribute("aria-live", "assertive");
  toastEl.setAttribute("aria-atomic", "true");

  toastEl.innerHTML = `
    <div class="d-flex">
      <div class="toast-body py-2 px-3">
        <strong>${type.toUpperCase()}:</strong> ${message}
      </div>
      <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
    </div>
  `;

  toastContainer.appendChild(toastEl);
  setTimeout(() => {
    toastEl.classList.remove("show");
    setTimeout(() => toastEl.remove(), 300);
  }, 4500);
}

function formatNumber(num) {
  if (num === null || num === undefined) return "0";
  return new Intl.NumberFormat().format(num);
}

function formatPercentage(num) {
  if (num === null || num === undefined) return "0.0%";
  return `${Number(num).toFixed(1)}%`;
}

// Highlight active page link
document.addEventListener("DOMContentLoaded", () => {
  const currentPath = window.location.pathname.toLowerCase();
  const navLinks = document.querySelectorAll(".navbar-cinecheck .nav-link");
  
  navLinks.forEach(link => {
    const href = link.getAttribute("href");
    if (!href) return;
    const cleanHref = href.toLowerCase();
    if (
      currentPath === cleanHref ||
      (currentPath.includes("dashboard") && cleanHref.includes("dashboard")) ||
      (currentPath.includes("analyse") && cleanHref.includes("analyse")) ||
      (currentPath.includes("batch") && cleanHref.includes("batch")) ||
      (currentPath.includes("evaluation") && cleanHref.includes("evaluation")) ||
      (currentPath.includes("dataset") && cleanHref.includes("dataset")) ||
      (currentPath.includes("history") && cleanHref.includes("history")) ||
      (currentPath.includes("about") && cleanHref.includes("about")) ||
      (currentPath === "/" && cleanHref.includes("index"))
    ) {
      link.classList.add("active");
    } else {
      link.classList.remove("active");
    }
  });
});
