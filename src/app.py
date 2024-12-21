from flask import Flask, render_template, request, jsonify
from models.materials import GW2Price, BaseMaterials
from calculator.crafting_calculator import CraftingCalculator
import requests

app = Flask(__name__)
calculator = CraftingCalculator()

API_KEY = "53E1B734-BE78-6D4B-BFC4-AB5A7BD0CE8E8CE228E8-69FC-4E92-9CAE-AD4C68D3AB44"
API_URL = "https://api.guildwars2.com/v2/commerce/prices?ids={}"

MATERIAL_IDS = {
    "inscription": 19920,
    "ori_ore": 19701, 
    "leather": 19732,
    "ancient_wood": 19725
}

@app.route('/')
def index():
    prices = fetch_prices()
    return render_template('index.html', prices=prices)

def fetch_prices():
    item_ids = ",".join(str(id) for id in MATERIAL_IDS.values())
    url = API_URL.format(item_ids)
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        prices = response.json()
        return {
            item_name: GW2Price(
                gold=price["buys"]["unit_price"] // 10000,
                silver=(price["buys"]["unit_price"] % 10000) // 100,
                copper=price["buys"]["unit_price"] % 100
            )
            for item_name, item_id in MATERIAL_IDS.items()
            for price in prices
            if price["id"] == item_id
        }
    else:
        app.logger.error(f"Error fetching prices from GW2 API: {response.status_code}")
        return None

@app.route('/calculate', methods=['POST'])
def calculate():
    try:
        # Preise über die GW2 API abrufen
        prices = fetch_prices()
        
        if prices is None:
            return jsonify({'error': "Failed to fetch prices from GW2 API"}), 500
        
        # Materialdaten aus den abgerufenen Preisen erstellen
        materials = BaseMaterials(
            inscription_price=prices["inscription"],
            ori_ore_price=prices["ori_ore"],
            ancient_wood_price=prices["ancient_wood"],
            leather_price=prices["leather"]
        )

        results = {}
        for weapon_type, recipe in calculator.get_all_recipes().items():
            # Berechne Gesamtkosten
            total_cost = calculator.calculate_cost(recipe, materials)
            # Berechne detaillierte Komponentenkosten
            component_costs = calculator.calculate_detailed_cost(recipe, materials)
            
            # Formatiere die Komponenten für JSON
            components_json = {}
            
            # Füge Inscription hinzu
            inscription_data = component_costs.get("Berserker's Orichalcum Imbued Inscription")
            if inscription_data:
                components_json['inscription'] = {
                    'gold': inscription_data.cost.gold,
                    'silver': inscription_data.cost.silver,
                    'copper': inscription_data.cost.copper,
                    'materials': inscription_data.materials
                }
            
            # Füge andere Komponenten hinzu
            for comp_name, comp_data in component_costs.items():
                if comp_name != "Berserker's Orichalcum Imbued Inscription":
                    components_json[comp_name] = {
                        'gold': comp_data.cost.gold,
                        'silver': comp_data.cost.silver,
                        'copper': comp_data.cost.copper,
                        'materials': comp_data.materials
                    }

            # Verwende weapon_type.value statt weapon_type als Schlüssel
            results[str(weapon_type.value)] = {
                'total': {
                    'gold': total_cost.gold,
                    'silver': total_cost.silver,
                    'copper': total_cost.copper
                },
                'components': components_json,
                'profession': weapon_type.profession.value
            }

        return jsonify(results)
    
    except Exception as e:
        app.logger.error(f"Error in calculate: {str(e)}")
        return jsonify({'error': str(e)}), 400

@app.route('/refresh-prices', methods=['GET'])
def refresh_prices():
    prices = fetch_prices()
    if prices is None:
        return jsonify({'error': "Failed to fetch prices from GW2 API"}), 500
    return jsonify({
        item_name: {
            'gold': price.gold,
            'silver': price.silver,
            'copper': price.copper
        }
        for item_name, price in prices.items()
    })

if __name__ == '__main__':
    app.run(debug=True)
