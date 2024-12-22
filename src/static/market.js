// Chart-Objekte
let priceChart, volumeChart, historyChart;

// Lade initiale Daten
async function loadInitialData() {
    const [currentData, recommendations] = await Promise.all([
        fetch('/api/market/current').then(r => r.json()),
        fetch('/api/market/recommendations').then(r => r.json())
    ]);

    updateCharts(currentData);
    updateRecommendations(recommendations);
}

// Aktualisiere Charts mit aktuellen Daten
function updateCharts(data) {
    const items = Object.entries(data);
    
    // Aktualisiere Preischart
    if (priceChart) priceChart.destroy();
    priceChart = new Chart(document.getElementById('currentPricesChart'), {
        type: 'bar',
        data: {
            labels: items.map(([_, item]) => item.name),
            datasets: [{
                label: 'Aktueller Preis',
                data: items.map(([_, item]) => item.lowest_sell / 10000), // Konvertiere zu Gold
                backgroundColor: 'rgba(74, 158, 255, 0.7)'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    title: {
                        display: true,
                        text: 'Preis in Gold'
                    }
                }
            }
        }
    });

    // Aktualisiere Volumen-Chart
    if (volumeChart) volumeChart.destroy();
    volumeChart = new Chart(document.getElementById('volumeChart'), {
        type: 'bar',
        data: {
            labels: items.map(([_, item]) => item.name),
            datasets: [{
                label: 'Aktive Angebote',
                data: items.map(([_, item]) => item.total_listings),
                backgroundColor: 'rgba(46, 204, 113, 0.7)'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    title: {
                        display: true,
                        text: 'Anzahl Angebote'
                    }
                }
            }
        }
    });
}

// Aktualisiere Detailansicht für ein Item
async function updateItemDetails(itemId) {
    const historyData = await fetch(`/api/market/history/${itemId}`).then(r => r.json());
    
    // Aktualisiere History-Chart
    if (historyChart) historyChart.destroy();
    historyChart = new Chart(document.getElementById('priceHistoryChart'), {
        type: 'line',
        data: {
            labels: historyData.map(d => d.date),
            datasets: [{
                label: 'Durchschnittspreis',
                data: historyData.map(d => d.avg_price / 10000),
                borderColor: 'rgb(74, 158, 255)',
                tension: 0.1
            }, {
                label: 'Min-Max Bereich',
                data: historyData.map(d => ({
                    x: d.date,
                    low: d.min_price / 10000,
                    high: d.max_price / 10000
                })),
                backgroundColor: 'rgba(74, 158, 255, 0.2)',
                borderWidth: 0,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ${context.parsed.y.toFixed(2)}G`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    title: {
                        display: true,
                        text: 'Preis in Gold'
                    }
                }
            }
        }
    });

    // Aktualisiere Statistiken
    document.getElementById('avgPrice').textContent = formatPrice(historyData[historyData.length - 1].avg_price);
    document.getElementById('activeListings').textContent = Math.round(historyData[historyData.length - 1].avg_listings);
}

// Aktualisiere Empfehlungen
function updateRecommendations(data) {
    // Verkaufsempfehlungen
    const sellList = document.getElementById('sellRecommendations');
    sellList.innerHTML = data.sell.map(item => `
        <li class="mb-2">
            <strong>${item.name}</strong><br>
            <small class="text-muted">
                Preis: ${item.current_price} | Angebote: ${item.listings}
            </small>
        </li>
    `).join('');

    // Neueinstellungsempfehlungen
    const relistList = document.getElementById('relistRecommendations');
    relistList.innerHTML = data.relist.map(item => `
        <li class="mb-2">
            <strong>${item.name}</strong><br>
            <small class="text-muted">
                ${item.items_ahead} Angebote vor dir | Aktuell: ${item.current_price}
            </small>
        </li>
    `).join('');
}

// Formatiere Preis in Gold, Silber, Kupfer
function formatPrice(price) {
    const gold = Math.floor(price / 10000);
    const silver = Math.floor((price % 10000) / 100);
    const copper = price % 100;
    return `${gold}G ${silver}S ${copper}C`;
}

// Event Listener
document.addEventListener('DOMContentLoaded', function() {
    loadInitialData();
    
    // Aktualisiere alle 5 Minuten
    setInterval(loadInitialData, 300000);
    
    // Event Listener für Item-Auswahl
    document.getElementById('itemSelect').addEventListener('change', function() {
        updateItemDetails(this.value);
    });
}); 