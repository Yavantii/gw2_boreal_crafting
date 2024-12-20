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

// Globale Variable für die Ergebnisse
let currentResults = {};

// Am Anfang der Datei nach den Konstanten
let sellPriceModal;

// Initialisiere das Modal beim Laden der Seite
document.addEventListener('DOMContentLoaded', () => {
    // Initialisiere das Modal
    sellPriceModal = new bootstrap.Modal(document.getElementById('sellPriceModal'));
    
    // Event Listener für Profession Filter
    document.querySelectorAll('.profession-filter').forEach(checkbox => {
        checkbox.addEventListener('change', (e) => {
            const profession = e.target.value;
            const isChecked = e.target.checked;
            
            // Alle Waffen der entsprechenden Profession selektieren/deselektieren
            document.querySelectorAll(`.${profession.toLowerCase()}-weapon`).forEach(weaponCheckbox => {
                weaponCheckbox.checked = isChecked;
            });
            
            applyFilters();
        });
    });

    // Event Listener für Waffen Filter
    document.querySelectorAll('.weapon-filter').forEach(checkbox => {
        checkbox.addEventListener('change', applyFilters);
    });

    // Eingabefeld-Handler
    const inputs = document.querySelectorAll('input[type="number"]');
    inputs.forEach(input => {
        input.addEventListener('blur', () => {
            if (input.value === '') {
                input.value = '0';
            }
        });
    });

    updateShoppingList();
});

document.getElementById('calculatorForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    // Alle Eingabefelder durchgehen und leere Werte mit 0 ersetzen
    const inputs = e.target.querySelectorAll('input[type="number"]');
    inputs.forEach(input => {
        if (input.value === '') {
            input.value = '0';
        }
    });
    
    const formData = new FormData(e.target);
    
    try {
        const response = await fetch('/calculate', {
            method: 'POST',
            body: formData
        });
        
        const results = await response.json();
        
        if (response.ok) {
            currentResults = results;
            // Wende Filter direkt nach dem Laden der Ergebnisse an
            applyFilters();
        } else {
            console.error('Server Error:', results);
            alert('Server Fehler: ' + (results.error || 'Unbekannter Fehler'));
        }
    } catch (error) {
        console.error('Fetch Error:', error);
        alert('Netzwerk Fehler: ' + error.message);
    }
});

function applyFilters() {
    if (!currentResults) {
        console.error('Keine Ergebnisse zum Filtern vorhanden');
        return;
    }

    // Hole alle ausgewählten Waffen
    const selectedWeapons = Array.from(document.querySelectorAll('.weapon-filter:checked'))
        .map(cb => cb.value);
    
    console.log('Selected Weapons:', selectedWeapons);
    
    if (selectedWeapons.length === 0) {
        displayNoFilterWarning();
        return;
    }
    
    const filteredResults = {};
    Object.entries(currentResults).forEach(([weaponName, data]) => {
        if (selectedWeapons.includes(weaponName)) {
            filteredResults[weaponName] = data;
        }
    });
    
    displayResults(filteredResults);
    updateShoppingList();
}

function displayNoFilterWarning() {
    const resultsDiv = document.getElementById('resultsList');
    if (!resultsDiv) {
        console.error('resultsList Element nicht gefunden');
        return;
    }
    
    resultsDiv.innerHTML = `
        <div class="alert alert-warning" role="alert">
            <h4 class="alert-heading">Keine Filter ausgewählt!</h4>
            <p>Bitte wählen Sie mindestens einen Beruf aus, um die Ergebnisse anzuzeigen.</p>
        </div>
    `;
}

function calculateProfit(sellPrice, craftingCost) {
    const listingFee = Math.floor(sellPrice * 0.05);
    const exchangeFee = Math.floor(sellPrice * 0.10);
    const totalFees = listingFee + exchangeFee;
    const profit = sellPrice - totalFees - craftingCost;
    
    return {
        profit: profit,
        listingFee: listingFee,
        exchangeFee: exchangeFee,
        totalFees: totalFees,
        effectiveCost: craftingCost
    };
}

function displayResults(results) {
    console.log('Displaying results:', results);
    
    const resultsDiv = document.getElementById('resultsList');
    if (!resultsDiv) {
        console.error('resultsList Element nicht gefunden');
        return;
    }
    
    // Prüfe ob es Ergebnisse gibt
    if (Object.keys(results).length === 0) {
        resultsDiv.innerHTML = `
            <div class="alert alert-info" role="alert">
                <h4 class="alert-heading">Keine Ergebnisse gefunden</h4>
                <p>Für die ausgewählten Filter wurden keine Ergebnisse gefunden.</p>
            </div>
        `;
        return;
    }
    
    resultsDiv.innerHTML = '';
    
    // Sortiere die Ergebnisse nach der definierten Reihenfolge
    const sortedResults = Object.entries(results)
        .sort((a, b) => {
            const indexA = weaponOrder.indexOf(a[0]);
            const indexB = weaponOrder.indexOf(b[0]);
            return indexA - indexB;
        });
    
    sortedResults.forEach(([weaponName, data]) => {
        const resultItem = document.createElement('div');
        resultItem.className = 'result-item mb-4 p-3 border rounded';
        
        let componentsHtml = '<div class="components-list">';
        componentsHtml += '<h5>Komponenten:</h5><ul>';
        
        // Inscription (ohne Edit-Button)
        if (data.components && data.components.inscription) {
            componentsHtml += `
                <li>
                    Berserker's Orichalcum Imbued Inscription
                    <span class="component-cost">${data.components.inscription.gold}g ${data.components.inscription.silver}s ${data.components.inscription.copper}c</span>
                </li>`;
        }
        
        // Andere Komponenten mit Edit-Button
        if (data.components) {
            Object.entries(data.components).forEach(([componentName, componentData]) => {
                if (componentName !== 'inscription') {
                    const componentId = `${weaponName}-${componentName}`.replace(/\s+/g, '-').toLowerCase();
                    const craftingPrice = `${componentData.gold}g ${componentData.silver}s ${componentData.copper}c`;
                    const totalCopper = componentData.gold * 10000 + componentData.silver * 100 + componentData.copper;
                    
                    componentsHtml += `
                        <li class="component-item">
                            <div class="d-flex align-items-center mb-2">
                                <span>${componentName}</span>
                                <button type="button" class="btn btn-sm btn-link edit-price-btn ms-2"
                                        data-component="${componentId}"
                                        data-bs-toggle="collapse" 
                                        data-bs-target="#editor-${componentId}">
                                    <i class="fas fa-edit"></i>
                                    Edit
                                </button>
                            </div>
                            <div class="component-prices">
                                <span class="crafting-price" id="craft-${componentId}">
                                    ${craftingPrice}
                                </span>
                                <span class="custom-price ms-2" id="custom-price-${componentId}"></span>
                            </div>
                            <div class="collapse" id="editor-${componentId}">
                                <div class="custom-price-editor card card-body mt-2 mb-2">
                                    <div class="input-group input-group-sm">
                                        <button class="btn btn-danger btn-sm reset-price-btn" 
                                                data-component="${componentId}"
                                                title="Zurück zum Craftingpreis">
                                            <i class="fas fa-undo"></i>
                                        </button>
                                        <input type="number" class="form-control currency-input" placeholder="Gold" 
                                               id="${componentId}-gold" min="0">
                                        <span class="input-group-text">G</span>
                                        <input type="number" class="form-control currency-input" placeholder="Silber" 
                                               id="${componentId}-silver" min="0" max="99">
                                        <span class="input-group-text">S</span>
                                        <input type="number" class="form-control currency-input" placeholder="Kupfer" 
                                               id="${componentId}-copper" min="0" max="99">
                                        <span class="input-group-text">C</span>
                                        <button class="btn btn-success btn-sm confirm-price-btn" 
                                                data-component="${componentId}"
                                                data-original-price="${totalCopper}"
                                                title="Custom-Preis bestätigen">
                                            <i class="fas fa-check"></i>
                                        </button>
                                    </div>
                                </div>
                            </div>
                            <div class="component-materials">
                                ${componentData.materials.ori_ore ? `${componentData.materials.ori_ore}x Orichalcum Ore` : ''}
                                ${componentData.materials.ancient_wood ? `${componentData.materials.ancient_wood}x Ancient Wood` : ''}
                                ${componentData.materials.leather ? `${componentData.materials.leather}x Hardened Leather` : ''}
                            </div>
                        </li>`;
                }
            });
        }
        
        componentsHtml += '</ul></div>';
        
        resultItem.innerHTML = `
            <h4>${weaponName}</h4>
            <p class="profession-info">Beruf: ${data.profession}</p>
            <p class="total-cost">Materialkosten: ${data.total.gold}g ${data.total.silver}s ${data.total.copper}c</p>
            ${componentsHtml}
            <div class="profit-section mt-3">
                <button class="btn btn-outline-primary btn-sm calculate-profit-btn" 
                        data-weapon="${weaponName}"
                        data-cost="${data.total.gold * 10000 + data.total.silver * 100 + data.total.copper}">
                    Gewinn berechnen
                </button>
                <div class="profit-results" id="profit-${weaponName.replace(/\s+/g, '-')}"></div>
            </div>
        `;
        
        resultsDiv.appendChild(resultItem);
        
        // Event Listener für die Reset-Buttons
        document.querySelectorAll('.reset-price-btn').forEach(button => {
            button.addEventListener('click', handlePriceReset);
        });
        
        // Event Listener für die Bestätigungsbuttons
        document.querySelectorAll('.confirm-price-btn').forEach(button => {
            button.addEventListener('click', handleCustomPriceConfirm);
        });
    });
}

// Funktion für das Handling der Custom Price Bestätigung
function handleCustomPriceConfirm(e) {
    const componentId = e.target.closest('.confirm-price-btn').dataset.component;
    const gold = parseInt(document.getElementById(`${componentId}-gold`).value || 0);
    const silver = parseInt(document.getElementById(`${componentId}-silver`).value || 0);
    const copper = parseInt(document.getElementById(`${componentId}-copper`).value || 0);
    
    const customPrice = `${gold}g ${silver}s ${copper}c`;
    const customPriceSpan = document.getElementById(`custom-price-${componentId}`);
    const craftingPrice = document.getElementById(`craft-${componentId}`);
    
    // Setze Custom Price und Style
    customPriceSpan.textContent = customPrice;
    customPriceSpan.classList.add('custom-price-active');
    craftingPrice.classList.add('price-strikethrough');
    
    // Schließe den Editor
    const editor = document.getElementById(`editor-${componentId}`);
    bootstrap.Collapse.getInstance(editor).hide();
    
    // Speichere den Custom Price für spätere Berechnungen
    e.target.closest('.confirm-price-btn').dataset.customPrice = 
        (gold * 10000 + silver * 100 + copper).toString();

    // Aktualisiere die Gesamtkosten
    updateTotalCost(componentId);
    updateShoppingList();
}

// Neue Funktion für das Aktualisieren der Gesamtkosten
function updateTotalCost(changedComponentId) {
    // Finde die Waffe anhand der Komponenten-ID
    const weaponElement = document.querySelector(`.result-item:has([data-component="${changedComponentId}"])`);
    if (!weaponElement) return;

    const totalCostElement = weaponElement.querySelector('.total-cost');
    if (!totalCostElement) return;

    // Sammle alle Komponenten dieser Waffe
    let totalCopperCost = 0;
    
    // Finde die Inscription
    const inscriptionElement = weaponElement.querySelector('.component-cost');
    if (inscriptionElement) {
        const match = inscriptionElement.textContent.match(/(\d+)g\s+(\d+)s\s+(\d+)c/);
        if (match) {
            totalCopperCost += parseInt(match[1]) * 10000 + parseInt(match[2]) * 100 + parseInt(match[3]);
        }
    }

    // Finde alle anderen Komponenten dieser spezifischen Waffe
    const components = weaponElement.querySelectorAll('.component-item');
    components.forEach(component => {
        const customPriceSpan = component.querySelector('.custom-price');
        const craftingPriceSpan = component.querySelector('.crafting-price');
        const confirmBtn = component.querySelector('.confirm-price-btn');
        
        if (customPriceSpan?.classList.contains('custom-price-active') && confirmBtn?.dataset.customPrice) {
            // Verwende Custom-Preis wenn aktiv
            totalCopperCost += parseInt(confirmBtn.dataset.customPrice);
        } else if (craftingPriceSpan) {
            // Verwende Original-Preis
            const match = craftingPriceSpan.textContent.match(/(\d+)g\s+(\d+)s\s+(\d+)c/);
            if (match) {
                totalCopperCost += parseInt(match[1]) * 10000 + parseInt(match[2]) * 100 + parseInt(match[3]);
            }
        }
    });

    // Konvertiere in Gold/Silber/Copper Format
    const gold = Math.floor(totalCopperCost / 10000);
    const silver = Math.floor((totalCopperCost % 10000) / 100);
    const copper = totalCopperCost % 100;

    // Aktualisiere die Anzeige der Materialkosten
    totalCostElement.textContent = `Materialkosten: ${gold}g ${silver}s ${copper}c`;
    
    // Aktualisiere auch den data-cost Wert des Gewinn-Berechnen-Buttons
    const profitBtn = weaponElement.querySelector('.calculate-profit-btn');
    if (profitBtn) {
        profitBtn.dataset.cost = totalCopperCost.toString();
        
        // Prüfe ob bereits eine Gewinnberechnung angezeigt wird
        const profitDetails = weaponElement.querySelector('.profit-details');
        if (profitDetails) {
            // Extrahiere den aktuellen Verkaufspreis
            const sellPriceText = profitDetails.querySelector('p:first-child').textContent;
            const sellPriceMatch = sellPriceText.match(/(\d+)g\s+(\d+)s\s+(\d+)c/);
            
            if (sellPriceMatch) {
                const sellPrice = parseInt(sellPriceMatch[1]) * 10000 + 
                                parseInt(sellPriceMatch[2]) * 100 + 
                                parseInt(sellPriceMatch[3]);
                
                // Berechne den Gewinn neu
                const profitData = calculateProfit(sellPrice, totalCopperCost);
                
                // Formatiere die Preise
                const formatPrice = (copperValue) => {
                    const g = Math.floor(copperValue / 10000);
                    const s = Math.floor((copperValue % 10000) / 100);
                    const c = copperValue % 100;
                    return `${g}g ${s}s ${c}c`;
                };
                
                // Aktualisiere die einzelnen Werte in der bestehenden Gewinnberechnung
                const allElements = profitDetails.children;
                
                // Aktualisiere nur die relevanten Werte und behalte die Formatierung bei
                for (let i = 0; i < allElements.length; i++) {
                    const element = allElements[i];
                    if (element.textContent.includes('Listing Fee')) {
                        element.innerHTML = `<strong>Listing Fee (5%):</strong> ${formatPrice(profitData.listingFee)}`;
                    } else if (element.textContent.includes('Exchange Fee')) {
                        element.innerHTML = `<strong>Exchange Fee (10%):</strong> ${formatPrice(profitData.exchangeFee)}`;
                    } else if (element.textContent.includes('Materialkosten')) {
                        element.innerHTML = `<strong>Materialkosten:</strong> ${formatPrice(profitData.effectiveCost)}`;
                    } else if (element.textContent.includes('Gewinn')) {
                        // Behalte die Profit-Formatierung bei
                        element.className = `profit-amount ${profitData.profit >= 0 ? 'text-success' : 'text-danger'}`;
                        element.innerHTML = `<strong>Gewinn:</strong> ${formatPrice(profitData.profit)}`;
                    }
                }
            }
        }
    }
}

// Aktualisiere auch die handlePriceReset Funktion
function handlePriceReset(e) {
    const componentId = e.target.closest('.reset-price-btn').dataset.component;
    const customPriceSpan = document.getElementById(`custom-price-${componentId}`);
    const craftingPrice = document.getElementById(`craft-${componentId}`);
    
    // Entferne Custom Price und Styles
    customPriceSpan.textContent = '';
    customPriceSpan.classList.remove('custom-price-active');
    craftingPrice.classList.remove('price-strikethrough');
    
    // Setze Eingabefelder zurück
    document.getElementById(`${componentId}-gold`).value = '';
    document.getElementById(`${componentId}-silver`).value = '';
    document.getElementById(`${componentId}-copper`).value = '';
    
    // Entferne gespeicherten Custom Price
    const confirmBtn = document.querySelector(`.confirm-price-btn[data-component="${componentId}"]`);
    if (confirmBtn) {
        confirmBtn.dataset.customPrice = '';
    }
    
    // Schließe den Editor
    const editor = document.getElementById(`editor-${componentId}`);
    bootstrap.Collapse.getInstance(editor).hide();
    
    // Aktualisiere die Gesamtkosten
    updateTotalCost(componentId);
    updateShoppingList();
}

// Event-Listener für die Profit-Buttons
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('calculate-profit-btn')) {
        const weaponName = e.target.dataset.weapon;
        const craftingCost = parseInt(e.target.dataset.cost);
        
        // Setze den Weapon-Namen im Modal
        document.getElementById('currentWeaponName').value = weaponName;
        document.getElementById('sellPriceModalLabel').textContent = `Verkaufspreis für ${weaponName}`;
        
        // Reset previous values
        document.getElementById('sell_price_gold').value = '';
        document.getElementById('sell_price_silver').value = '';
        document.getElementById('sell_price_copper').value = '';
        
        // Zeige das Modal
        sellPriceModal.show();
        
        // Event-Listener für den Berechnen-Button im Modal
        const calculateProfitBtn = document.getElementById('calculateProfitBtn');
        calculateProfitBtn.onclick = () => {
            const gold = parseInt(document.getElementById('sell_price_gold').value || 0);
            const silver = parseInt(document.getElementById('sell_price_silver').value || 0);
            const copper = parseInt(document.getElementById('sell_price_copper').value || 0);
            
            const sellPrice = gold * 10000 + silver * 100 + copper;
            const profitData = calculateProfit(sellPrice, craftingCost);
            
            // Konvertiere die Copper-Werte in Gold/Silber/Copper
            const formatPrice = (copperValue) => {
                const gold = Math.floor(copperValue / 10000);
                const silver = Math.floor((copperValue % 10000) / 100);
                const copper = copperValue % 100;
                return `${gold}g ${silver}s ${copper}c`;
            };
            
            // Zeige die Gewinnberechnung an
            const profitResultsDiv = document.getElementById(`profit-${weaponName.replace(/\s+/g, '-')}`);
            profitResultsDiv.innerHTML = `
                <div class="profit-details mt-2">
                    <p><strong>Verkaufspreis:</strong> ${formatPrice(sellPrice)}</p>
                    <p><strong>Listing Fee (5%):</strong> ${formatPrice(profitData.listingFee)}</p>
                    <p><strong>Exchange Fee (10%):</strong> ${formatPrice(profitData.exchangeFee)}</p>
                    <p><strong>Materialkosten:</strong> ${formatPrice(profitData.effectiveCost)}</p>
                    <p class="profit-amount ${profitData.profit >= 0 ? 'text-success' : 'text-danger'}">
                        <strong>Gewinn:</strong> ${formatPrice(profitData.profit)}
                    </p>
                </div>
            `;
            
            sellPriceModal.hide();
        };
    }
});

function updateShoppingList() {
    // Prüfe ob die erforderlichen Elemente existieren
    const componentsList = document.getElementById('componentsList');
    const totalCostElement = document.getElementById('totalCost');
    
    if (!componentsList || !totalCostElement) {
        console.warn('Shopping List elements not found');
        return;
    }

    let totalOrichalcum = 0;
    let totalAncientWood = 0;
    let totalLeather = 0;
    let totalInscriptions = 0;
    let totalCostInCopper = 0;
    let componentsToBy = new Map();

    // Finde alle sichtbaren Waffen-Ergebnisse
    const visibleWeapons = document.querySelectorAll('.result-item:not(.d-none)');
    
    visibleWeapons.forEach(weapon => {
        // Sammle Materialien aus allen Komponenten
        const components = weapon.querySelectorAll('.component-item');
        components.forEach(component => {
            const componentName = component.querySelector('span').textContent.trim();
            const customPriceSpan = component.querySelector('.custom-price.custom-price-active');
            
            if (customPriceSpan) {
                // Diese Komponente wird gekauft
                const priceMatch = customPriceSpan.textContent.match(/(\d+)g\s+(\d+)s\s+(\d+)c/);
                if (priceMatch) {
                    const componentPrice = parseInt(priceMatch[1]) * 10000 + 
                                        parseInt(priceMatch[2]) * 100 + 
                                        parseInt(priceMatch[3]);
                    totalCostInCopper += componentPrice;
                    
                    // Füge zur Liste der zu kaufenden Komponenten hinzu
                    if (componentsToBy.has(componentName)) {
                        componentsToBy.set(componentName, {
                            count: componentsToBy.get(componentName).count + 1,
                            pricePerUnit: componentPrice
                        });
                    } else {
                        componentsToBy.set(componentName, {
                            count: 1,
                            pricePerUnit: componentPrice
                        });
                    }
                }
            } else {
                // Diese Komponente wird gecraftet, zähle Rohmaterialien
                const materialsText = component.querySelector('.component-materials').textContent;
                
                const oriMatch = materialsText.match(/(\d+)x Orichalcum Ore/);
                if (oriMatch) totalOrichalcum += parseInt(oriMatch[1]);
                
                const woodMatch = materialsText.match(/(\d+)x Ancient Wood/);
                if (woodMatch) totalAncientWood += parseInt(woodMatch[1]);
                
                const leatherMatch = materialsText.match(/(\d+)x Hardened Leather/);
                if (leatherMatch) totalLeather += parseInt(leatherMatch[1]);
                
                // Addiere Craftingkosten
                const craftingPriceSpan = component.querySelector('.crafting-price');
                if (craftingPriceSpan) {
                    const priceMatch = craftingPriceSpan.textContent.match(/(\d+)g\s+(\d+)s\s+(\d+)c/);
                    if (priceMatch) {
                        totalCostInCopper += parseInt(priceMatch[1]) * 10000 + 
                                           parseInt(priceMatch[2]) * 100 + 
                                           parseInt(priceMatch[3]);
                    }
                }
            }
        });
        
        // Zähle Inscriptions
        const inscription = weapon.querySelector('.component-cost');
        if (inscription) {
            totalInscriptions++;
            const priceMatch = inscription.textContent.match(/(\d+)g\s+(\d+)s\s+(\d+)c/);
            if (priceMatch) {
                totalCostInCopper += parseInt(priceMatch[1]) * 10000 + 
                                   parseInt(priceMatch[2]) * 100 + 
                                   parseInt(priceMatch[3]);
            }
        }
    });

    // Aktualisiere die Anzeige der Rohmaterialien
    document.getElementById('totalOrichalcum').textContent = totalOrichalcum;
    document.getElementById('totalAncientWood').textContent = totalAncientWood;
    document.getElementById('totalLeather').textContent = totalLeather;
    document.getElementById('totalInscriptions').textContent = totalInscriptions;
    
    // Aktualisiere die Liste der zu kaufenden Komponenten
    componentsList.innerHTML = ''; // Liste leeren
    
    componentsToBy.forEach((data, componentName) => {
        const li = document.createElement('li');
        li.className = 'mb-2';
        const gold = Math.floor(data.pricePerUnit / 10000);
        const silver = Math.floor((data.pricePerUnit % 10000) / 100);
        const copper = data.pricePerUnit % 100;
        li.innerHTML = `
            <strong>${componentName}:</strong> ${data.count}x 
            <span class="text-muted">(${gold}g ${silver}s ${copper}c pro Stück)</span>
        `;
        componentsList.appendChild(li);
    });
    
    // Formatiere und zeige Gesamtkosten
    const gold = Math.floor(totalCostInCopper / 10000);
    const silver = Math.floor((totalCostInCopper % 10000) / 100);
    const copper = totalCostInCopper % 100;
    totalCostElement.textContent = `${gold}g ${silver}s ${copper}c`;
}

// Stelle sicher, dass updateShoppingList erst nach dem DOM-Load ausgeführt wird
document.addEventListener('DOMContentLoaded', () => {
    updateShoppingList();
});