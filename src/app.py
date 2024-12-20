from flask import Flask, render_template, request, jsonify
from models.materials import GW2Price, BaseMaterials
from calculator.crafting_calculator import CraftingCalculator

app = Flask(__name__)
calculator = CraftingCalculator()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate():
    try:
        # Materialdaten aus dem Formular holen
        materials = BaseMaterials(
            inscription_price=GW2Price(
                gold=int(request.form.get('inscription_gold', 0)),
                silver=int(request.form.get('inscription_silver', 0)),
                copper=int(request.form.get('inscription_copper', 0))
            ),
            ori_ore_price=GW2Price(
                gold=int(request.form.get('ori_ore_gold', 0)),
                silver=int(request.form.get('ori_ore_silver', 0)),
                copper=int(request.form.get('ori_ore_copper', 0))
            ),
            ancient_wood_price=GW2Price(
                gold=int(request.form.get('ancient_wood_gold', 0)),
                silver=int(request.form.get('ancient_wood_silver', 0)),
                copper=int(request.form.get('ancient_wood_copper', 0))
            ),
            leather_price=GW2Price(
                gold=int(request.form.get('leather_gold', 0)),
                silver=int(request.form.get('leather_silver', 0)),
                copper=int(request.form.get('leather_copper', 0))
            )
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
                'profession': weapon_type.profession.value  # Stelle sicher, dass wir den String-Wert verwenden
            }

        return jsonify(results)
    
    except Exception as e:
        app.logger.error(f"Error in calculate: {str(e)}")
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)
