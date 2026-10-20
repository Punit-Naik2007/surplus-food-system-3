/**
 * Surplus Food Redistribution Analytics & Visualizations
 * Built for "Data, Statistics & ML for Real India" Presentation
 */

function initAnalyticsCharts() {
  const statusCanvas = document.getElementById('statusChart');
  const categoryCanvas = document.getElementById('categoryChart');
  const cityCanvas = document.getElementById('cityChart');
  const unitCanvas = document.getElementById('unitComparisonChart');

  if (!statusCanvas && !categoryCanvas) {
    return;
  }

  fetch('/api/analytics-data')
    .then(response => {
      if (!response.ok) throw new Error('Network error loading analytics data');
      return response.json();
    })
    .then(data => {
      // 1. Status Distribution Doughnut Chart
      if (statusCanvas) {
        const statuses = Object.keys(data.status_data);
        const counts = Object.values(data.status_data);
        const statusColors = {
          'AVAILABLE': '#2e7d32',
          'ACCEPTED': '#0288d1',
          'PICKED_UP': '#f57c00',
          'DELIVERED': '#00897b',
          'CANCELLED': '#78909c',
          'EXPIRED': '#37474f',
          'REJECTED': '#d32f2f'
        };

        const bgColors = statuses.map(s => statusColors[s] || '#9e9e9e');

        new Chart(statusCanvas, {
          type: 'doughnut',
          data: {
            labels: statuses,
            datasets: [{
              data: counts,
              backgroundColor: bgColors,
              borderWidth: 2,
              borderColor: '#ffffff'
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: { position: 'bottom' },
              title: { display: true, text: 'Donation Status Lifecycle Distribution' }
            }
          }
        });
      }

      // 2. Food Category Breakdown Chart
      if (categoryCanvas) {
        const categories = Object.keys(data.category_data);
        const catCounts = Object.values(data.category_data);

        new Chart(categoryCanvas, {
          type: 'bar',
          data: {
            labels: categories,
            datasets: [{
              label: 'Number of Listings',
              data: catCounts,
              backgroundColor: '#43a047',
              borderRadius: 6
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: { display: false },
              title: { display: true, text: 'Listings by Food Classification Category' }
            },
            scales: {
              y: { beginAtZero: true, ticks: { precision: 0 } }
            }
          }
        });
      }

      // 3. City Distribution Chart
      if (cityCanvas) {
        const cities = Object.keys(data.city_data);
        const cityCounts = Object.values(data.city_data);

        new Chart(cityCanvas, {
          type: 'bar',
          data: {
            labels: cities,
            datasets: [{
              label: 'Listings by Region',
              data: cityCounts,
              backgroundColor: '#00897b',
              borderRadius: 6
            }]
          },
          options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: { display: false },
              title: { display: true, text: 'Geographic Distribution (City / Service Area)' }
            },
            scales: {
              x: { beginAtZero: true, ticks: { precision: 0 } }
            }
          }
        });
      }

      // 4. Unit-wise quantities (kg vs servings vs packages)
      if (unitCanvas && data.unit_comparison) {
        const units = data.unit_comparison.map(u => u.unit.toUpperCase());
        const listedValues = data.unit_comparison.map(u => u.listed);
        const deliveredValues = data.unit_comparison.map(u => u.delivered);

        new Chart(unitCanvas, {
          type: 'bar',
          data: {
            labels: units,
            datasets: [
              {
                label: 'Total Listed',
                data: listedValues,
                backgroundColor: '#90caf9',
                borderRadius: 4
              },
              {
                label: 'Delivered to Beneficiaries',
                data: deliveredValues,
                backgroundColor: '#2e7d32',
                borderRadius: 4
              }
            ]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: { position: 'top' },
              title: { 
                display: true, 
                text: 'Volume Comparison by Distinct Unit (Kg, Servings, Packages)' 
              },
              tooltip: {
                callbacks: {
                  label: function(ctx) {
                    return `${ctx.dataset.label}: ${ctx.raw} ${units[ctx.dataIndex]}`;
                  }
                }
              }
            },
            scales: {
              y: { beginAtZero: true }
            }
          }
        });
      }
    })
    .catch(err => console.error('Error fetching analytics chart data:', err));
}

document.addEventListener('DOMContentLoaded', initAnalyticsCharts);
