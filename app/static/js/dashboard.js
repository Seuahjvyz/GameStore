import { Chart } from "@/components/ui/chart"
// Dashboard Analytics - Chart.js Implementation

document.addEventListener("DOMContentLoaded", () => {
  // Wait for Chart.js to load from CDN
  if (typeof Chart !== "undefined") {
    initSalesChart()
    initTopProductsChart()
  } else {
    console.error("Chart.js no está cargado")
  }
})

function initSalesChart() {
  const ctx = document.getElementById("salesChart")
  if (!ctx) return

  new Chart(ctx, {
    type: "line",
    data: {
      labels: ["Sem 1", "Sem 2", "Sem 3", "Sem 4"],
      datasets: [
        {
          label: "Ventas",
          data: [12000, 19000, 15000, 25000],
          borderColor: "#a21caf",
          backgroundColor: "rgba(162, 28, 175, 0.1)",
          tension: 0.4,
          fill: true,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false,
        },
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            callback: (value) => "$" + value.toLocaleString(),
          },
        },
      },
    },
  })
}

function initTopProductsChart() {
  const ctx = document.getElementById("topProductsChart")
  if (!ctx) return

  new Chart(ctx, {
    type: "bar",
    data: {
      labels: ["PS5", "Xbox Series X", "Nintendo Switch", "DualSense", "FIFA 24"],
      datasets: [
        {
          label: "Unidades Vendidas",
          data: [45, 38, 52, 67, 89],
          backgroundColor: ["#a21caf", "#c026d3", "#d946ef", "#e879f9", "#f0abfc"],
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false,
        },
      },
      scales: {
        y: {
          beginAtZero: true,
        },
      },
    },
  })
}
