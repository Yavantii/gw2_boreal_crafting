"""
Service für die Berechnung von Kosten und Profiten
"""

from models.materials import BaseMaterials, GW2Price
from calculator.crafting_calculator import CraftingCalculator
from api.gw2_api import fetch_prices, fetch_component_prices, fetch_weapon_price
from config.ids import COMPONENT_NAME_MAPPING
from utils.currency import convert_to_coins, convert_from_coins
from config.settings import LISTING_FEE_PERCENT, EXCHANGE_FEE_PERCENT
from utils.exceptions import CalculationError

class CalculationService:
    def __init__(self):
        self.calculator = CraftingCalculator()

    def prepare_materials(self, prices):
        """Erstellt ein BaseMaterials-Objekt aus den API-Preisen"""
        if not all(key in prices for key in ["inscription", "ori_ore", "ancient_wood", "leather"]):
            raise CalculationError("Missing required material prices")
            
        return BaseMaterials(
            inscription_price=prices["inscription"],
            ori_ore_price=prices["ori_ore"],
            ancient_wood_price=prices["ancient_wood"],
            leather_price=prices["leather"]
        )

    def calculate_component_costs(self, component_name, comp_data, component_prices):
        """
        Berechnet die Kosten für eine Komponente und entscheidet ob Crafting oder Kauf günstiger ist
        
        Args:
            component_name: Name der Komponente
            comp_data: Komponenten-Daten mit Craft-Kosten
            component_prices: Trading Post Preise der Komponenten
            
        Returns:
            dict: Komponenten-Informationen mit Kosten und Kaufempfehlung
        """
        # Berechne Craft-Kosten
        craft_cost = convert_to_coins(
            gold=comp_data.cost.gold,
            silver=comp_data.cost.silver,
            copper=comp_data.cost.copper
        )
        
        # Für Inscriptions immer Craft-Kosten verwenden
        if component_name == "Berserker's Orichalcum Imbued Inscription":
            return {
                'gold': comp_data.cost.gold,
                'silver': comp_data.cost.silver,
                'copper': comp_data.cost.copper,
                'materials': comp_data.materials,
                'buyFromTP': False,
                'craftCost': craft_cost
            }
        
        # Hole Trading Post Preis
        comp_id = COMPONENT_NAME_MAPPING.get(component_name)
        tp_price = component_prices.get(comp_id) if comp_id else None
        
        result = {
            'materials': comp_data.materials,
            'craftCost': craft_cost
        }
        
        if tp_price:
            tp_cost = convert_to_coins(
                gold=tp_price.gold,
                silver=tp_price.silver,
                copper=tp_price.copper
            )
            result['tpCost'] = tp_cost
            
            # Vergleiche die Preise
            if tp_cost < craft_cost:
                # Trading Post ist günstiger
                result.update({
                    'gold': tp_price.gold,
                    'silver': tp_price.silver,
                    'copper': tp_price.copper,
                    'buyFromTP': True,
                    'savings': craft_cost - tp_cost
                })
                return result
        
        # Craft ist günstiger oder kein TP-Preis verfügbar
        result.update({
            'gold': comp_data.cost.gold,
            'silver': comp_data.cost.silver,
            'copper': comp_data.cost.copper,
            'buyFromTP': False,
            'savings': tp_cost - craft_cost if tp_price else 0
        })
        return result

    def calculate_profit(self, total_cost, weapon_name):
        """
        Berechnet den Profit für eine Waffe unter Berücksichtigung der Trading Post Gebühren
        
        Args:
            total_cost: Gesamtkosten in Kupfer
            weapon_name: Name der Waffe
            
        Returns:
            dict: Profit-Informationen mit Verkaufspreis und Gebühren
        """
        result, status_code = fetch_weapon_price(weapon_name)
        if status_code != 200:
            return None
            
        sell_price = convert_to_coins(
            gold=result['gold'],
            silver=result['silver'],
            copper=result['copper']
        )
        
        # Berechne Gebühren
        listing_fee = int(sell_price * (LISTING_FEE_PERCENT / 100))
        exchange_fee = int(sell_price * (EXCHANGE_FEE_PERCENT / 100))
        total_fees = listing_fee + exchange_fee
        
        # Berechne Nettogewinn
        net_profit = sell_price - total_fees - total_cost
        
        return {
            'sellPrice': convert_from_coins(sell_price),
            'listingFee': convert_from_coins(listing_fee),
            'exchangeFee': convert_from_coins(exchange_fee),
            'totalFees': convert_from_coins(total_fees),
            'netProfit': convert_from_coins(net_profit),
            'profitPercent': round((net_profit / total_cost) * 100, 2) if total_cost > 0 else 0
        }

    def calculate_results(self):
        """
        Berechnet die Ergebnisse für alle Waffen
        
        Returns:
            dict: Ergebnisse mit Kosten, Komponenten und Profit für jede Waffe
        """
        # Preise abrufen
        prices = fetch_prices()
        component_prices = fetch_component_prices()
        
        if prices is None or component_prices is None:
            raise CalculationError("Failed to fetch prices from GW2 API")
        
        # Materialdaten erstellen
        materials = self.prepare_materials(prices)
        
        results = {}
        total_materials = {
            'totalOrichalcum': 0,
            'totalAncientWood': 0,
            'totalLeather': 0,
            'totalInscriptions': 0
        }
        
        for weapon_type, recipe in self.calculator.get_all_recipes().items():
            # Berechne detaillierte Komponentenkosten
            component_costs = self.calculator.calculate_detailed_cost(recipe, materials)
            
            # Formatiere die Komponenten für JSON
            components_json = {}
            
            # Verarbeite alle Komponenten
            for comp_name, comp_data in component_costs.items():
                components_json[comp_name] = self.calculate_component_costs(
                    comp_name, comp_data, component_prices
                )
                # Summiere die Materialien
                if 'materials' in comp_data:
                    for material, amount in comp_data.materials.items():
                        if material == 'ori_ore':
                            total_materials['totalOrichalcum'] += amount
                        elif material == 'ancient_wood':
                            total_materials['totalAncientWood'] += amount
                        elif material == 'leather':
                            total_materials['totalLeather'] += amount
            
            # Zähle Inscriptions
            total_materials['totalInscriptions'] += 1

            # Berechne die Gesamtkosten neu basierend auf den günstigsten Optionen
            total_copper = sum(
                convert_to_coins(
                    gold=comp['gold'],
                    silver=comp['silver'],
                    copper=comp['copper']
                )
                for comp in components_json.values()
            )
            
            # Berechne Profit
            profit_info = self.calculate_profit(total_copper, str(weapon_type.value))
            
            # Konvertiere Gesamtkosten zurück in Gold/Silber/Kupfer
            total_coins = convert_from_coins(total_copper)
            
            # Verwende weapon_type.value als Schlüssel
            results[str(weapon_type.value)] = {
                'total': total_coins,
                'components': components_json,
                'profession': weapon_type.profession.value,
                'profit': profit_info if profit_info else None
            }
        
        # Füge die Gesamtmaterialien zu den Ergebnissen hinzu
        results['materials'] = total_materials
        
        return results 