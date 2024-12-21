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

# IDs für die Komponenten
COMPONENT_IDS = {
    # Axe Components
    "orichalcum_axe_blade": 12852,
    "orichalcum_axe_haft": 12892,
    
    # Dagger Components
    "orichalcum_dagger_blade": 12858,
    "orichalcum_dagger_hilt": 12882,
    
    # Mace Components
    "orichalcum_mace_head": 12876,
    "orichalcum_mace_handle": 12892,
    
    # Pistol Components
    "orichalcum_pistol_barrel": 12924,
    "ancient_pistol_frame": 12959,
    
    # Scepter Components
    "ancient_scepter_core": 13255,
    "ancient_scepter_rod": 12976,
    
    # Sword Components
    "orichalcum_sword_blade": 12870,
    "orichalcum_sword_hilt": 12846,
    
    # Focus Components
    "ancient_focus_core": 13243,
    "ancient_focus_casing": 12982,
    
    # Shield Components
    "orichalcum_shield_boss": 12912,
    "orichalcum_shield_backing": 12906,
    
    # Torch Components
    "ancient_torch_handle": 13014,
    "orichalcum_torch_head": 13061,
    
    # Warhorn Components
    "orichalcum_horn": 12936,
    "orichalcum_warhorn_mouthpiece": 12930,
    
    # Greatsword Components
    "orichalcum_greatsword_blade": 12840,
    "orichalcum_greatsword_hilt": 12888,
    
    # Hammer Components
    "orichalcum_hammer_head": 12864,
    "large_ancient_haft": 12899,
    
    # Longbow Components
    "ancient_longbow_stave": 12941,
    "hardened_string": 12963,
    
    # Rifle Components
    "orichalcum_rifle_barrel": 12918,
    "ancient_rifle_stock": 12953,
    
    # Short Bow Components
    "ancient_short_bow_stave": 12947,
    # hardened_string already defined for longbow
    
    # Staff Components
    "ancient_staff_head": 13261,
    "ancient_staff_shaft": 12973
}

# Mapping von Komponentennamen zu API-IDs
COMPONENT_NAME_MAPPING = {
    "Orichalcum Axe Blade": "orichalcum_axe_blade",
    "Orichalcum Axe Haft": "orichalcum_axe_haft",
    "Orichalcum Dagger Blade": "orichalcum_dagger_blade",
    "Orichalcum Dagger Hilt": "orichalcum_dagger_hilt",
    "Orichalcum Mace Head": "orichalcum_mace_head",
    "Orichalcum Mace Handle": "orichalcum_mace_handle",
    "Orichalcum Pistol Barrel": "orichalcum_pistol_barrel",
    "Ancient Pistol Frame": "ancient_pistol_frame",
    "Ancient Scepter Core": "ancient_scepter_core",
    "Ancient Scepter Rod": "ancient_scepter_rod",
    "Orichalcum Sword Blade": "orichalcum_sword_blade",
    "Orichalcum Sword Hilt": "orichalcum_sword_hilt",
    "Ancient Focus Core": "ancient_focus_core",
    "Ancient Focus Casing": "ancient_focus_casing",
    "Orichalcum Shield Boss": "orichalcum_shield_boss",
    "Orichalcum Shield Backing": "orichalcum_shield_backing",
    "Ancient Torch Handle": "ancient_torch_handle",
    "Orichalcum Torch Head": "orichalcum_torch_head",
    "Orichalcum Horn": "orichalcum_horn",
    "Orichalcum Warhorn Mouthpiece": "orichalcum_warhorn_mouthpiece",
    "Orichalcum Greatsword Blade": "orichalcum_greatsword_blade",
    "Orichalcum Greatsword Hilt": "orichalcum_greatsword_hilt",
    "Orichalcum Hammer Head": "orichalcum_hammer_head",
    "Large Ancient Haft": "large_ancient_haft",
    "Ancient Longbow Stave": "ancient_longbow_stave",
    "Hardened String": "hardened_string",
    "Orichalcum Rifle Barrel": "orichalcum_rifle_barrel",
    "Ancient Rifle Stock": "ancient_rifle_stock",
    "Ancient Short-Bow Stave": "ancient_short_bow_stave",
    "Ancient Staff Head": "ancient_staff_head",
    "Ancient Staff Shaft": "ancient_staff_shaft"
}

# Dictionary für Waffen-IDs
WEAPON_IDS = {
    'Restored Boreal Axe': 92218,
    'Restored Boreal Dagger': 92331,
    'Restored Boreal Focus': 92367,
    'Restored Boreal Greatsword': 92363,
    'Restored Boreal Hammer': 92230,
    'Restored Boreal Longbow': 92354,
    'Restored Boreal Mace': 92395,
    'Restored Boreal Pistol': 92222,
    'Restored Boreal Rifle': 92248,
    'Restored Boreal Scepter': 92244,
    'Restored Boreal Shield': 92261,
    'Restored Boreal Short Bow': 92298,
    'Restored Boreal Staff': 92343,
    'Restored Boreal Sword': 92359,
    'Restored Boreal Torch': 92217,
    'Restored Boreal Warhorn': 92290
}

@app.route('/')
def index():
    prices = fetch_prices()
    component_prices = fetch_component_prices()
    return render_template('index.html', prices=prices, component_prices=component_prices)

def fetch_component_prices():
    item_ids = ",".join(str(id) for id in COMPONENT_IDS.values())
    url = API_URL.format(item_ids)
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        prices = response.json()
        return {
            comp_name: GW2Price(
                gold=price["sells"]["unit_price"] // 10000,
                silver=(price["sells"]["unit_price"] % 10000) // 100,
                copper=price["sells"]["unit_price"] % 100
            )
            for comp_name, comp_id in COMPONENT_IDS.items()
            for price in prices
            if price["id"] == comp_id
        }
    else:
        app.logger.error(f"Error fetching component prices from GW2 API: {response.status_code}")
        return None

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
        component_prices = fetch_component_prices()
        
        if prices is None or component_prices is None:
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
                    'materials': inscription_data.materials,
                    'buyFromTP': False  # Inscriptions immer craften
                }
            
            # Füge andere Komponenten hinzu
            for comp_name, comp_data in component_costs.items():
                if comp_name != "Berserker's Orichalcum Imbued Inscription":
                    # Berechne Craft-Kosten
                    craft_cost = (comp_data.cost.gold * 10000 + 
                                comp_data.cost.silver * 100 + 
                                comp_data.cost.copper)
                    
                    # Hole Trading Post Preis
                    comp_id = COMPONENT_NAME_MAPPING.get(comp_name)
                    tp_price = component_prices.get(comp_id) if comp_id else None
                    
                    if tp_price:
                        tp_cost = (tp_price.gold * 10000 + 
                                 tp_price.silver * 100 + 
                                 tp_price.copper)
                        
                        # Vergleiche die Preise
                        if tp_cost < craft_cost:
                            # Trading Post ist günstiger
                            components_json[comp_name] = {
                                'gold': tp_price.gold,
                                'silver': tp_price.silver,
                                'copper': tp_price.copper,
                                'materials': comp_data.materials,
                                'buyFromTP': True
                            }
                            continue
                    
                    # Craft ist günstiger oder kein TP-Preis verfügbar
                    components_json[comp_name] = {
                        'gold': comp_data.cost.gold,
                        'silver': comp_data.cost.silver,
                        'copper': comp_data.cost.copper,
                        'materials': comp_data.materials,
                        'buyFromTP': False
                    }

            # Berechne die Gesamtkosten neu basierend auf den günstigsten Optionen
            total_copper = sum(
                (comp['gold'] * 10000 + comp['silver'] * 100 + comp['copper'])
                for comp in components_json.values()
            )
            
            # Verwende weapon_type.value statt weapon_type als Schlüssel
            results[str(weapon_type.value)] = {
                'total': {
                    'gold': total_copper // 10000,
                    'silver': (total_copper % 10000) // 100,
                    'copper': total_copper % 100
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

@app.route('/fetch-weapon-price/<weapon_name>')
def fetch_weapon_price(weapon_name):
    try:
        if weapon_name not in WEAPON_IDS:
            return jsonify({'error': 'Weapon not found'}), 404
            
        weapon_id = WEAPON_IDS[weapon_name]
        url = f"https://api.guildwars2.com/v2/commerce/prices/{weapon_id}"
        headers = {"Authorization": f"Bearer {API_KEY}"}
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            return jsonify({'error': 'Failed to fetch price'}), response.status_code
            
        data = response.json()
        sells = data.get('sells', {}).get('unit_price', 0)
        
        # Konvertiere in Gold/Silber/Kupfer Format
        gold = sells // 10000
        silver = (sells % 10000) // 100
        copper = sells % 100
        
        return jsonify({
            'gold': gold,
            'silver': silver,
            'copper': copper
        })
        
    except Exception as e:
        print(f"Error fetching weapon price: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
