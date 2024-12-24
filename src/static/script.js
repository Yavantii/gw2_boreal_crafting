// Definiere die Sortierreihenfolge am Anfang der Datei
const weaponOrder = [
    "Restored Boreal Longbow",     // Huntsman - 1
    "Restored Boreal Pistol",      // Huntsman - 2
    "Restored Boreal Rifle",       // Huntsman - 3
    "Restored Boreal Short Bow",   // Huntsman - 4
    "Restored Boreal Torch",       // Huntsman - 5
    "Restored Boreal Warhorn",     // Huntsman - 6
    "Restored Boreal Axe",         // Weaponsmith - 7
    "Restored Boreal Dagger",      // Weaponsmith - 8
    "Restored Boreal Greatsword",  // Weaponsmith - 9
    "Restored Boreal Hammer",      // Weaponsmith - 10
    "Restored Boreal Mace",        // Weaponsmith - 11
    "Restored Boreal Shield",      // Weaponsmith - 12
    "Restored Boreal Sword",       // Weaponsmith - 13
    "Restored Boreal Focus",       // Artificer - 14
    "Restored Boreal Scepter",     // Artificer - 15
    "Restored Boreal Staff"        // Artificer - 16
];

// Mapping von englischen zu deutschen Namen
const nameMapping = {
    'Restored Boreal Rifle': 'Wiederhergestelltes Boreal-Gewehr',
    'Restored Boreal Pistol': 'Wiederhergestellte Boreal-Pistole',
    'Restored Boreal Short Bow': 'Wiederhergestellter Boreal-Kurzbogen',
    'Restored Boreal Longbow': 'Wiederhergestellter Boreal-Langbogen',
    'Restored Boreal Focus': 'Wiederhergestellter Boreal-Fokus',
    'Restored Boreal Staff': 'Wiederhergestellter Boreal-Stab',
    'Restored Boreal Warhorn': 'Wiederhergestelltes Boreal-Kriegshorn',
    'Restored Boreal Axe': 'Wiederhergestellte Boreal-Axt',
    'Restored Boreal Dagger': 'Wiederhergestellter Boreal-Dolch',
    'Restored Boreal Greatsword': 'Wiederhergestelltes Boreal-Großschwert',
    'Restored Boreal Hammer': 'Wiederhergestellter Boreal-Hammer',
    'Restored Boreal Mace': 'Wiederhergestellter Boreal-Streitkolben',
    'Restored Boreal Shield': 'Wiederhergestelltes Boreal-Schild',
    'Restored Boreal Sword': 'Wiederhergestelltes Boreal-Schwert',
    'Restored Boreal Scepter': 'Wiederhergestelltes Boreal-Zepter',
    'Restored Boreal Torch': 'Wiederhergestellte Boreal-Fackel'
};

// Globale Variablen
let currentResults = null;

// Funktion zum Formatieren der Währung
function formatCurrency(gold, silver, copper) {
    // Wenn nur ein Parameter übergeben wurde, behandele ihn als Copper-Wert
    if (silver === undefined && copper === undefined) {
        const totalCopper = Math.round(gold);  // gold ist hier eigentlich der copper-Wert
        gold = Math.floor(totalCopper / 10000);
        silver = Math.floor((totalCopper % 10000) / 100);
        copper = totalCopper % 100;
    }
    
    let result = '<span class="price">';
    
    // Wenn Gold vorhanden ist, zeige es und alle nachfolgenden Währungen
    if (gold > 0) {
        result += `${gold}<img src="https://render.guildwars2.com/file/090A980A96D39FD36FBB004903644C6DBEFB1FFB/156904.png" alt="Gold" class="currency-icon">`;
        result += `${silver}<img src="https://render.guildwars2.com/file/E5A2197D78ECE4AE0349C8B3710D033D22DB0DA6/156907.png" alt="Silver" class="currency-icon">`;
        result += `${copper}<img src="https://render.guildwars2.com/file/6CF8F96A3299CFC75D5CC90617C3C70331A1EF0E/156902.png" alt="Copper" class="currency-icon">`;
    }
    // Wenn kein Gold aber Silber vorhanden ist
    else if (silver > 0) {
        result += `${silver}<img src="https://render.guildwars2.com/file/E5A2197D78ECE4AE0349C8B3710D033D22DB0DA6/156907.png" alt="Silver" class="currency-icon">`;
        result += `${copper}<img src="https://render.guildwars2.com/file/6CF8F96A3299CFC75D5CC90617C3C70331A1EF0E/156902.png" alt="Copper" class="currency-icon">`;
    }
    // Wenn weder Gold noch Silber
    else {
        result += `${copper}<img src="https://render.guildwars2.com/file/6CF8F96A3299CFC75D5CC90617C3C70331A1EF0E/156902.png" alt="Copper" class="currency-icon">`;
    }
    
    result += '</span>';
    return result;
}

// Funktion zum Anzeigen der Ergebnisse
function displayResults(results) {
    if (!results) return;
    
    // Speichere die Ergebnisse global
    currentResults = results;
    
    const resultsDiv = document.getElementById('resultsList');
    if (!resultsDiv) {
        console.error('resultsList Element nicht gefunden');
        return;
    }
    
    // Sammle aktive Filter
    const activeProfessions = Array.from(document.querySelectorAll('.profession-filter:checked')).map(cb => cb.value);
    const hideActiveListings = document.getElementById('hideActiveListingsFilter').checked;
    
    // Hole aktive Verkäufe aus dem localStorage
    const activeSales = JSON.parse(localStorage.getItem('activeBorealSales') || '[]');
    const activeWeaponNames = activeSales.map(sale => {
        // Konvertiere deutsche Namen zurück zu englischen
        const englishName = Object.entries(nameMapping).find(([eng, ger]) => ger === sale.name)?.[0];
        return englishName;
    });

    // Berechne Gesamtkosten und Materialien
    let materials = {
        totalOrichalcum: 0,
        totalAncientWood: 0,
        totalLeather: 0,
        totalInscriptions: 0,
        buyComponents: []
    };

    // Filtere und zeige Ergebnisse
    const resultsContainer = document.createElement('div');
    resultsContainer.className = 'row g-3';
    resultsDiv.innerHTML = '';
    resultsDiv.appendChild(resultsContainer);

    // Sortiere die Ergebnisse nach der weaponOrder
    const sortedResults = weaponOrder
        .filter(weaponName => {
            const data = results[weaponName];
            if (!data) return false;
            
            // Prüfe Berufsfilter
            if (!activeProfessions.includes(data.profession)) return false;
            
            // Prüfe aktive Verkäufe Filter
            if (hideActiveListings && activeWeaponNames.includes(weaponName)) return false;
            
            return true;
        })
        .map(weaponName => [weaponName, results[weaponName]]);

    // Zeige die gefilterten Ergebnisse an
    sortedResults.forEach(([weaponName, data]) => {
        // Zähle eine Inscription pro Waffe
        materials.totalInscriptions += 1;
        
        // Verarbeite die Komponenten und zähle Materialien
        Object.entries(data.components).forEach(([compName, compData]) => {
            // Zähle Materialien nur, wenn die Komponente NICHT im TP gekauft wird
            if (!compData.buyFromTP && compData.materials) {
                Object.entries(compData.materials).forEach(([matName, amount]) => {
                    switch(matName) {
                        case 'ori_ore':
                            materials.totalOrichalcum += amount;
                            break;
                        case 'ancient_wood':
                            materials.totalAncientWood += amount;
                            break;
                        case 'leather':
                            materials.totalLeather += amount;
                            break;
                    }
                });
            }
            
            // Wenn es eine Inscription ist und nicht im TP gekauft wird
            if (compName === "Berserker's Orichalcum Imbued Inscription" && !compData.buyFromTP) {
                materials.totalInscriptions += 1;
            }
            
            // Wenn die Komponente im TP gekauft werden soll
            if (compData.buyFromTP) {
                const displayName = compName === 'inscription' ? "Berserker's Orichalcum Imbued Inscription" : compName;
                const existingComp = materials.buyComponents.find(c => c.name === displayName);
                if (existingComp) {
                    existingComp.amount += 1;
                } else {
                    materials.buyComponents.push({
                        name: displayName,
                        amount: 1
                    });
                }
            }
        });
        
        // Erstelle Ergebniskarte im Raster
        const cardContainer = document.createElement('div');
        cardContainer.className = 'col-md-6 col-lg-4';
        
        const card = document.createElement('div');
        card.className = 'card h-100 result-card';
        
        const cardBody = document.createElement('div');
        cardBody.className = 'card-body p-3';

        // Waffentitel und Gesamtkosten
        cardBody.innerHTML = `
            <div class="d-flex justify-content-between align-items-start mb-2">
                <h6 class="card-title mb-0 weapon-name">${weaponName}</h6>
                <button type="button" class="btn btn-sm btn-outline-primary calculate-profit" data-weapon="${weaponName}">
                    Profit
                </button>
            </div>
            <div class="d-flex justify-content-between align-items-center small mb-2">
                <div><strong>Cost:</strong> ${formatCurrency(data.total.gold, data.total.silver, data.total.copper)}</div>
                <div class="net-profit text-end" style="white-space: nowrap;"></div>
            </div>
        `;

        // Wenn ein Profit bereits berechnet wurde, stelle den Button-Status wieder her
        if (currentResults[weaponName].profit) {
            const profitButton = cardBody.querySelector('.calculate-profit');
            profitButton.classList.remove('btn-outline-primary');
            profitButton.classList.add('btn-outline-success');
            const netProfitSpan = cardBody.querySelector('.net-profit');
            const profitData = currentResults[weaponName].profit;
            netProfitSpan.className = `net-profit text-end ${profitData.netProfit.gold < 0 ? 'text-danger' : 'text-success'} small`;
            netProfitSpan.innerHTML = `${formatCurrency(Math.abs(profitData.netProfit.gold), profitData.netProfit.silver, profitData.netProfit.copper)}`;
        }

        // Komponenten Details
        const componentsList = document.createElement('div');
        componentsList.className = 'components-list small';
        
        Object.entries(data.components).forEach(([compName, compData]) => {
            const compDiv = document.createElement('div');
            compDiv.className = 'component-item mb-1';
            
            // Formatiere den Komponentennamen
            let displayName = compName;
            if (compName === 'inscription') {
                displayName = "Berserker's Orichalcum Imbued Inscription";
            }
            
            // HTML für die Komponente mit kleinerer Schrift und ohne Zeilenumbrüche
            let componentHtml = `
                <div class="d-flex justify-content-between align-items-center" style="font-size: 0.8rem; white-space: nowrap;">
                    <div class="text-truncate pe-2" style="max-width: 70%;" title="${displayName}">
                        <span class="${compData.buyFromTP ? 'text-warning' : ''}">${displayName}</span>
                    </div>
                    <div class="text-end" style="min-width: 30%;">
                        <span class="${compData.buyFromTP ? 'text-warning' : ''}">${formatCurrency(compData.gold, compData.silver, compData.copper)}</span>
                    </div>
                </div>`;
            
            compDiv.innerHTML = componentHtml;
            
            // Verarbeite Materialien und zu kaufende Komponenten
            if (compData.buyFromTP && compName !== 'inscription') {
                // Zeige Trading Post Hinweis mit Copy Button
                const materialsList = document.createElement('div');
                materialsList.className = 'component-materials ms-3';
                materialsList.style.fontSize = '0.75rem';
                materialsList.innerHTML = `
                    <div class="d-flex align-items-center">
                        <span class="text-warning">Trading Post</span>
                        <button class="btn btn-sm btn-outline-secondary ms-2 copy-btn" data-name="${displayName}" style="padding: 0px 4px; font-size: 0.7rem;">
                            <i class="bi bi-clipboard"></i>
                        </button>
                    </div>
                `;
                compDiv.appendChild(materialsList);
            } else {
                // Verarbeite Materialien für zu craftende Komponenten
                if (compData.materials) {
                    const materialsList = document.createElement('div');
                    materialsList.className = 'component-materials ms-3 text-muted';
                    materialsList.style.fontSize = '0.75rem';
                    materialsList.style.whiteSpace = 'nowrap';
                    materialsList.style.overflow = 'hidden';
                    materialsList.style.textOverflow = 'ellipsis';
                    
                    const formattedMaterials = Object.entries(compData.materials).map(([matName, amount]) => {
                        // Entferne die Materialzählung hier, da sie bereits vorher gemacht wurde
                        switch(matName) {
                            case 'ori_ore':
                                return `Orichalcum Ore: ${amount}`;
                            case 'ancient_wood':
                                return `Ancient Wood Log: ${amount}`;
                            case 'leather':
                                return `Hardened Leather Section: ${amount}`;
                            case 'inscription':
                                return `Berserker's Orichalcum Imbued Inscription: ${amount}`;
                            default:
                                return `${matName}: ${amount}`;
                        }
                    }).join(', ');
                    
                    materialsList.textContent = formattedMaterials;
                    materialsList.title = formattedMaterials; // Zeige vollständigen Text beim Hover
                    compDiv.appendChild(materialsList);
                }
            }

            componentsList.appendChild(compDiv);
        });
        
        cardBody.appendChild(componentsList);
        card.appendChild(cardBody);
        cardContainer.appendChild(card);
        resultsContainer.appendChild(cardContainer);
    });

    // Aktualisiere die Materialmengen in den Anzeigen NACHDEM alle Berechnungen abgeschlossen sind
    document.getElementById('totalInscriptions').textContent = materials.totalInscriptions;
    document.getElementById('totalOrichalcum').textContent = materials.totalOrichalcum;
    document.getElementById('totalAncientWood').textContent = materials.totalAncientWood;
    document.getElementById('totalLeather').textContent = materials.totalLeather;

    // Aktualisiere die Shopping-Liste mit den gesammelten Materialien
    updateShoppingList(materials);

    // Aktualisiere die Markierungen für aktive Verkäufe
    updateActiveListings();
}

// Event-Handler für Profit-Buttons
document.addEventListener('click', async function(event) {
    if (!event.target.matches('.calculate-profit')) return;
    
    const button = event.target;
    const weaponName = button.dataset.weapon;
    const netProfitSpan = button.closest('.card-body').querySelector('.net-profit');
    
    // Wenn der Profit bereits angezeigt wird, entferne ihn
    if (button.classList.contains('btn-outline-success')) {
        button.classList.remove('btn-outline-success');
        button.classList.add('btn-outline-primary');
        netProfitSpan.textContent = '';
        if (currentResults[weaponName]) {
            delete currentResults[weaponName].profit;
        }
        return;
    }
    
    try {
        // Hole die Craft-Kosten aus den aktuellen Ergebnissen
        const craftCost = currentResults[weaponName].total;
        if (!craftCost) {
            throw new Error('Could not find craft cost for ' + weaponName);
        }
        
        // Konvertiere Craft-Kosten in Kupfer
        const craftCostCopper = (craftCost.gold * 10000) + (craftCost.silver * 100) + craftCost.copper;
        
        // Hole den aktuellen Verkaufspreis
        const response = await fetch(`/fetch-weapon-price/${encodeURIComponent(weaponName)}`);
        if (!response.ok) {
            throw new Error('Failed to fetch weapon price');
        }
        
        const sellPrice = await response.json();
        if (!sellPrice || typeof sellPrice.gold === 'undefined') {
            throw new Error('Invalid price data received');
        }
        
        // Konvertiere Verkaufspreis in Kupfer
        const sellPriceCopper = (sellPrice.gold * 10000) + (sellPrice.silver * 100) + sellPrice.copper;
        
        // Berechne Trading Post Gebühren (15%)
        const tpFeeCopper = Math.ceil(sellPriceCopper * 0.15);
        
        // Berechne Nettogewinn in Kupfer
        const netProfitInCopper = sellPriceCopper - tpFeeCopper - craftCostCopper;
        
        // Konvertiere Nettogewinn zurück in Gold/Silber/Kupfer
        const profitGold = Math.floor(Math.abs(netProfitInCopper) / 10000);
        const profitSilver = Math.floor((Math.abs(netProfitInCopper) % 10000) / 100);
        const profitCopper = Math.abs(netProfitInCopper) % 100;
        
        // Speichere die Profitdaten
        currentResults[weaponName].profit = {
            sellPrice: sellPrice,
            tpFee: {
                gold: Math.floor(tpFeeCopper / 10000),
                silver: Math.floor((tpFeeCopper % 10000) / 100),
                copper: tpFeeCopper % 100
            },
            netProfit: {
                gold: netProfitInCopper < 0 ? -profitGold : profitGold,
                silver: profitSilver,
                copper: profitCopper
            }
        };
        
        // Aktualisiere die Anzeige
        button.classList.remove('btn-outline-primary');
        button.classList.add('btn-outline-success');
        netProfitSpan.className = `net-profit text-end ${netProfitInCopper < 0 ? 'text-danger' : 'text-success'} small`;
        netProfitSpan.innerHTML = formatCurrency(
            Math.abs(currentResults[weaponName].profit.netProfit.gold),
            currentResults[weaponName].profit.netProfit.silver,
            currentResults[weaponName].profit.netProfit.copper
        );
        
    } catch (error) {
        console.error('Error calculating profit:', error);
        button.classList.remove('btn-outline-primary', 'btn-outline-success');
        button.classList.add('btn-outline-danger');
        netProfitSpan.className = 'net-profit text-end text-danger small';
        netProfitSpan.textContent = 'Error: ' + error.message;
        
        // Setze den Button nach 3 Sekunden zurück
        setTimeout(() => {
            button.classList.remove('btn-outline-danger');
            button.classList.add('btn-outline-primary');
            netProfitSpan.textContent = '';
            if (currentResults[weaponName]) {
                delete currentResults[weaponName].profit;
            }
        }, 3000);
    }
});

// Event Listener für den Calculate Button
document.getElementById('calculateButton').addEventListener('click', async () => {
    try {
        const response = await fetch('/calculate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        
        const results = await response.json();
        console.log('Server response:', results);  // Debug-Ausgabe
        
        if (results.error) {
            console.error('Server Error:', results.error);
            alert('Server Fehler: ' + results.error);
            return;
        }
        
        currentResults = results;
        displayResults(results);
        
    } catch (error) {
        console.error('Fetch Error:', error);
        alert('Netzwerk Fehler: ' + error.message);
    }
});

// Event-Listener für Filter
function setupFilterListeners() {
    // Berufsfilter
    document.querySelectorAll('.profession-filter').forEach(checkbox => {
        checkbox.addEventListener('change', () => {
            if (currentResults) {
                displayResults(currentResults);
            }
        });
    });

    // Aktive Verkäufe Filter
    document.getElementById('hideActiveListingsFilter').addEventListener('change', () => {
        if (currentResults) {
            displayResults(currentResults);
        }
    });
}

// Initialisiere die Filter-Listener beim Laden der Seite
document.addEventListener('DOMContentLoaded', () => {
    setupFilterListeners();

    // Event Listener für Collapse-Funktionalität
    const sections = [
        document.querySelector('.shopping-list-section'),
        document.querySelector('.total-profits-section')
    ];

    sections.forEach(section => {
        if (section) {
            const header = section.querySelector('.card-header');
            if (header) {
                header.addEventListener('click', () => {
                    section.classList.toggle('collapsed');
                });
            }
            section.classList.add('collapsed');
        }
    });

    // Automatisch Ergebnisse berechnen beim Laden der Seite
    document.getElementById('calculateButton').click();
});

// Funktion zum Berechnen des Profits
function calculateProfit(sellPrice, craftCost) {
    const sellCopper = (sellPrice.gold * 10000) + (sellPrice.silver * 100) + sellPrice.copper;
    const costCopper = (craftCost.gold * 10000) + (craftCost.silver * 100) + craftCost.copper;
    
    // Berechne Gebühren
    const listingFee = Math.ceil(sellCopper * 0.05); // 5% Listing Fee
    const exchangeFee = Math.ceil(sellCopper * 0.10); // 10% Exchange Fee
    const totalFees = listingFee + exchangeFee;
    
    // Berechne Nettogewinn
    const profitCopper = sellCopper - costCopper - totalFees;
    
    return {
        gold: Math.floor(profitCopper / 10000),
        silver: Math.floor((profitCopper % 10000) / 100),
        copper: profitCopper % 100,
        fees: {
            listingFee: {
                gold: Math.floor(listingFee / 10000),
                silver: Math.floor((listingFee % 10000) / 100),
                copper: listingFee % 100
            },
            exchangeFee: {
                gold: Math.floor(exchangeFee / 10000),
                silver: Math.floor((exchangeFee % 10000) / 100),
                copper: exchangeFee % 100
            }
        }
    };
}

// Funktion zum Aktualisieren des Gesamtgewinns
function updateTotalProfit() {
    let totalProfitCopper = 0;
    
    // Sammle alle Profit-Beträge
    document.querySelectorAll('#profitsList li span').forEach(element => {
        const goldMatch = element.querySelector('.gold');
        const silverMatch = element.querySelector('.silver');
        const copperMatch = element.querySelector('.copper');
        
        if (goldMatch && silverMatch && copperMatch) {
            const gold = parseInt(goldMatch.textContent) || 0;
            const silver = parseInt(silverMatch.textContent) || 0;
            const copper = parseInt(copperMatch.textContent) || 0;
            const isNegative = element.classList.contains('text-danger');
            const profitCopper = (gold * 10000) + (silver * 100) + copper;
            totalProfitCopper += isNegative ? -profitCopper : profitCopper;
        }
    });
    
    // Aktualisiere die Gesamtgewinn-Anzeige
    const gold = Math.floor(Math.abs(totalProfitCopper) / 10000);
    const silver = Math.floor((Math.abs(totalProfitCopper) % 10000) / 100);
    const copper = Math.abs(totalProfitCopper) % 100;
    const totalProfitElement = document.getElementById('totalProfit');
    if (totalProfitElement) {
        totalProfitElement.innerHTML = formatCurrency(
            totalProfitCopper < 0 ? -gold : gold,
            silver,
            copper
        );
        totalProfitElement.className = totalProfitCopper < 0 ? 'h4 text-danger' : 'h4 text-success';
    }
}

// Funktion zum Aktualisieren der Shopping-Liste
function updateShoppingList(materials) {
    const rawMaterialsList = document.getElementById('rawMaterialsList');
    const inscriptionsList = document.getElementById('inscriptionsList');
    const componentsList = document.getElementById('componentsList');
    
    if (!rawMaterialsList || !inscriptionsList || !componentsList) {
        console.error('Required elements not found');
        return;
    }
    
    // Aktualisiere Rohmaterialien
    rawMaterialsList.innerHTML = `
        <li class="mb-2 d-flex justify-content-between align-items-center">
            <div>
                <strong>Orichalcum Ore:</strong> ${materials.totalOrichalcum}
                <button class="btn btn-sm btn-outline-secondary ms-2 copy-btn" data-name="Orichalcum Ore">
                    <i class="bi bi-clipboard"></i>
                                </button>
                            </div>
        </li>
        <li class="mb-2 d-flex justify-content-between align-items-center">
            <div>
                <strong>Ancient Wood Log:</strong> ${materials.totalAncientWood}
                <button class="btn btn-sm btn-outline-secondary ms-2 copy-btn" data-name="Ancient Wood Log">
                    <i class="bi bi-clipboard"></i>
                                        </button>
                                    </div>
        </li>
        <li class="mb-2 d-flex justify-content-between align-items-center">
            <div>
                <strong>Hardened Leather Section:</strong> ${materials.totalLeather}
                <button class="btn btn-sm btn-outline-secondary ms-2 copy-btn" data-name="Hardened Leather Section">
                    <i class="bi bi-clipboard"></i>
                </button>
            </div>
        </li>
    `;
    
    // Aktualisiere Inscriptions
    inscriptionsList.innerHTML = `
        <li class="mb-2 d-flex justify-content-between align-items-center">
            <div>
                <strong>Berserker's Orichalcum Imbued Inscription:</strong> ${materials.totalInscriptions}
                <button class="btn btn-sm btn-outline-secondary ms-2 copy-btn" data-name="Berserker's Orichalcum Imbued Inscription">
                    <i class="bi bi-clipboard"></i>
                </button>
                </div>
        </li>
    `;
    
    // Aktualisiere zu kaufende Komponenten
    componentsList.innerHTML = materials.buyComponents.map(comp => `
        <li class="mb-2 d-flex justify-content-between align-items-center">
            <div>
                <strong>${comp.name}:</strong> ${comp.amount}
                <button class="btn btn-sm btn-outline-secondary ms-2 copy-btn" data-name="${comp.name}">
                    <i class="bi bi-clipboard"></i>
                </button>
            </div>
        </li>
    `).join('');

// Event Listener für Copy Buttons
    document.querySelectorAll('.copy-btn').forEach(button => {
        button.addEventListener('click', function() {
            const textToCopy = this.dataset.name;
        navigator.clipboard.writeText(textToCopy).then(() => {
                // Optional: Visuelles Feedback
                const originalText = this.innerHTML;
                this.innerHTML = '<i class="bi bi-check"></i>';
            setTimeout(() => {
                    this.innerHTML = originalText;
            }, 1000);
            });
        });
    });
}

// Funktion zum Kopieren der Shopping-Liste
async function copyShoppingList() {
    const shoppingList = document.getElementById('shoppingList');
    if (!shoppingList) {
        console.error('Shopping list element not found');
        return;
    }

    // Formatiere die Shopping-Liste für das Kopieren
    const rawMaterials = Array.from(document.querySelectorAll('#rawMaterialsList li')).map(li => li.textContent.trim());
    const inscriptions = Array.from(document.querySelectorAll('#inscriptionsList li')).map(li => li.textContent.trim());
    const components = Array.from(document.querySelectorAll('#componentsList li')).map(li => li.textContent.trim());

    const formattedList = [
        'Rohmaterialien:',
        ...rawMaterials,
        '',
        'Inschriften:',
        ...inscriptions,
        '',
        'Komponenten:',
        ...components
    ].join('\n');

    try {
        await navigator.clipboard.writeText(formattedList);
        // Zeige Feedback an
        const copyButton = document.querySelector('.copy-shopping-list');
        if (copyButton) {
            const originalText = copyButton.innerHTML;
            copyButton.innerHTML = '<i class="bi bi-check"></i> Kopiert!';
            setTimeout(() => {
                copyButton.innerHTML = originalText;
            }, 2000);
        }
    } catch (err) {
        console.error('Failed to copy text: ', err);
    }
}

// Event-Listener für den Copy-Button
document.addEventListener('DOMContentLoaded', () => {
    const copyButton = document.querySelector('.copy-shopping-list');
    if (copyButton) {
        copyButton.addEventListener('click', copyShoppingList);
    }
});
