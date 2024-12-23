"""
Guild Wars 2 Boreal Crafting Calculator
Main application file that handles the web interface and API interactions for
calculating crafting costs of Boreal weapons in Guild Wars 2.
"""

# Standard library imports
from datetime import datetime, timedelta
from functools import wraps
import logging
from typing import Dict, Any, Optional

# Third-party imports
from flask import Flask, render_template, request, jsonify
import requests

# Local application imports
from models.materials import GW2Price, BaseMaterials
from calculator.crafting_calculator import CraftingCalculator
from market_routes import market_bp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GW2APIError(Exception):
    """Base exception class for GW2 API related errors"""
    def __init__(self, message: str, error_code: Optional[int] = None, details: Optional[Dict] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

class ValidationError(GW2APIError):
    """Raised when API response validation fails"""
    pass

class NetworkError(GW2APIError):
    """Raised when network communication fails"""
    pass

class PriceCalculationError(GW2APIError):
    """Raised when price calculation fails"""
    pass

# Initialize Flask application
app = Flask(__name__)
app.register_blueprint(market_bp)

# Initialize crafting calculator
calculator = CraftingCalculator()

# API Configuration
API_KEY = "53E1B734-BE78-6D4B-BFC4-AB5A7BD0CE8E8CE228E8-69FC-4E92-9CAE-AD4C68D3AB44"
API_URL = "https://api.guildwars2.com/v2/commerce/prices?ids={}"

# Cache configuration
price_cache = {}
CACHE_DURATION = timedelta(minutes=5)

# Material IDs for basic crafting materials
MATERIAL_IDS = {
    "inscription": 19920,  # Berserker's Orichalcum Imbued Inscription
    "ori_ore": 19701,     # Orichalcum Ore
    "leather": 19732,     # Thick Leather Section
    "ancient_wood": 19725 # Ancient Wood Log
}

# Component IDs for weapon parts
COMPONENT_IDS = {
    "orichalcum_axe_blade": 12852,
    "orichalcum_axe_haft": 12892,
    "orichalcum_dagger_blade": 12858,
    "orichalcum_dagger_hilt": 12882,
    "orichalcum_mace_head": 12876,
    "orichalcum_mace_handle": 12892,
    "orichalcum_pistol_barrel": 12924,
    "ancient_pistol_frame": 12959,
    "ancient_scepter_core": 13255,
    "ancient_scepter_rod": 12976,
    "orichalcum_sword_blade": 12870,
    "orichalcum_sword_hilt": 12846,
    "ancient_focus_core": 13243,
    "ancient_focus_casing": 12982,
    "orichalcum_shield_boss": 12912,
    "orichalcum_shield_backing": 12906,
    "ancient_torch_handle": 13014,
    "orichalcum_torch_head": 13061,
    "orichalcum_horn": 12936,
    "orichalcum_warhorn_mouthpiece": 12930,
    "orichalcum_greatsword_blade": 12840,
    "orichalcum_greatsword_hilt": 12888,
    "orichalcum_hammer_head": 12864,
    "large_ancient_haft": 12899,
    "ancient_longbow_stave": 12941,
    "hardened_string": 12963,
    "orichalcum_rifle_barrel": 12918,
    "ancient_rifle_stock": 12953,
    "ancient_short_bow_stave": 12947,
    "ancient_staff_head": 13261,
    "ancient_staff_shaft": 12973
}

# Mapping of component names
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

# Dictionary for weapon IDs
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

@app.errorhandler(GW2APIError)
def handle_gw2_error(error):
    """Global error handler for GW2API related errors"""
    response = {
        'error': error.message,
        'error_type': error.__class__.__name__,
        'details': error.details
    }
    status_code = error.error_code if error.error_code else 500
    logger.error(f"GW2API Error: {error.message}", extra={'details': error.details})
    return jsonify(response), status_code

def validate_api_response(response_data):
    """Validates the GW2 API response for required fields and structure."""
    if not isinstance(response_data, list):
        raise ValidationError(
            "Invalid API response format",
            details={'expected': 'list', 'received': type(response_data).__name__}
        )

    for idx, item in enumerate(response_data):
        missing_fields = []
        for field in ['id', 'sells', 'buys']:
            if field not in item:
                missing_fields.append(field)
        
        if missing_fields:
            raise ValidationError(
                "Missing required fields in API response",
                details={
                    'item_index': idx,
                    'missing_fields': missing_fields,
                    'item_data': item
                }
            )
        
        for price_type in ['sells', 'buys']:
            if 'unit_price' not in item[price_type]:
                raise ValidationError(
                    f"Missing unit_price in {price_type} data",
                    details={
                        'item_id': item['id'],
                        'price_type': price_type,
                        'available_fields': list(item[price_type].keys())
                    }
                )

def cache_api_call(duration=CACHE_DURATION):
    """Decorator that caches API call results for a specified duration."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}_{args}_{kwargs}"
            now = datetime.now()
            
            if cache_key in price_cache:
                result, timestamp = price_cache[cache_key]
                if now - timestamp < duration:
                    logger.debug(f"Cache hit for {func.__name__}")
                    return result
                logger.debug(f"Cache expired for {func.__name__}")
            else:
                logger.debug(f"Cache miss for {func.__name__}")
            
            result = func(*args, **kwargs)
            price_cache[cache_key] = (result, now)
            return result
        return wrapper
    return decorator

@app.route('/')
def index():
    """Main route that displays the crafting calculator interface."""
    try:
        prices = fetch_prices()
        component_prices = fetch_component_prices()
        
        if prices is None or component_prices is None:
            raise GW2APIError(
                "Failed to fetch required price data",
                error_code=503,
                details={
                    'materials_fetched': prices is not None,
                    'components_fetched': component_prices is not None
                }
            )
        
        return render_template('index.html', prices=prices, component_prices=component_prices)
    except Exception as e:
        logger.exception("Unexpected error in index route")
        raise GW2APIError(
            "Failed to render calculator interface",
            error_code=500,
            details={'original_error': str(e)}
        )

@cache_api_call()
def fetch_prices():
    """Fetches current prices for basic crafting materials from the GW2 API."""
    item_ids = ",".join(str(id) for id in MATERIAL_IDS.values())
    url = API_URL.format(item_ids)
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        prices = response.json()
        
        validate_api_response(prices)
        
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
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error while fetching prices: {str(e)}")
        raise NetworkError(
            "Failed to communicate with GW2 API",
            error_code=503,
            details={
                'url': url,
                'error': str(e),
                'error_type': type(e).__name__
            }
        )
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error while fetching prices: {str(e)}")
        raise GW2APIError(
            "Failed to process material prices",
            error_code=500,
            details={
                'error': str(e),
                'error_type': type(e).__name__
            }
        )

@cache_api_call()
def fetch_component_prices():
    """Fetches current prices for weapon components from the GW2 API."""
    item_ids = ",".join(str(id) for id in COMPONENT_IDS.values())
    url = API_URL.format(item_ids)
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        prices = response.json()
        
        validate_api_response(prices)
        
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
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error while fetching component prices: {str(e)}")
        raise NetworkError(
            "Failed to fetch component prices from GW2 API",
            error_code=503,
            details={
                'url': url,
                'error': str(e),
                'error_type': type(e).__name__
            }
        )
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error while fetching component prices: {str(e)}")
        raise GW2APIError(
            "Failed to process component prices",
            error_code=500,
            details={
                'error': str(e),
                'error_type': type(e).__name__
            }
        )

def _format_component_costs(component_costs, component_prices):
    """Helper function to format component costs and determine buy vs. craft recommendations."""
    components_json = {}
    
    # Handle inscription separately as it should always be crafted
    inscription_data = component_costs.get("Berserker's Orichalcum Imbued Inscription")
    if inscription_data:
        components_json['inscription'] = {
            'gold': inscription_data.cost.gold,
            'silver': inscription_data.cost.silver,
            'copper': inscription_data.cost.copper,
            'materials': inscription_data.materials,
            'buyFromTP': False
        }
    
    # Process other components
    for comp_name, comp_data in component_costs.items():
        if comp_name != "Berserker's Orichalcum Imbued Inscription":
            # Calculate crafting cost
            craft_cost = (comp_data.cost.gold * 10000 + 
                        comp_data.cost.silver * 100 + 
                        comp_data.cost.copper)
            
            # Get Trading Post price if available
            comp_id = COMPONENT_NAME_MAPPING.get(comp_name)
            tp_price = component_prices.get(comp_id) if comp_id else None
            
            if tp_price:
                tp_cost = (tp_price.gold * 10000 + 
                         tp_price.silver * 100 + 
                         tp_price.copper)
                
                # Compare prices and use the cheaper option
                if tp_cost < craft_cost:
                    components_json[comp_name] = {
                        'gold': tp_price.gold,
                        'silver': tp_price.silver,
                        'copper': tp_price.copper,
                        'materials': comp_data.materials,
                        'buyFromTP': True
                    }
                    continue
            
            # Default to crafting if TP is more expensive or price unavailable
            components_json[comp_name] = {
                'gold': comp_data.cost.gold,
                'silver': comp_data.cost.silver,
                'copper': comp_data.cost.copper,
                'materials': comp_data.materials,
                'buyFromTP': False
            }
    
    return components_json

@app.route('/calculate', methods=['POST'])
def calculate():
    """Main calculation endpoint that computes crafting costs for all weapons."""
    try:
        # Fetch current market prices
        prices = fetch_prices()
        component_prices = fetch_component_prices()
        
        # Initialize materials with current prices
        materials = BaseMaterials(
            inscription_price=prices["inscription"],
            ori_ore_price=prices["ori_ore"],
            ancient_wood_price=prices["ancient_wood"],
            leather_price=prices["leather"]
        )

        results = {}
        for weapon_type, recipe in calculator.get_all_recipes().items():
            try:
                # Calculate total crafting costs
                total_cost = calculator.calculate_cost(recipe, materials)
                # Get detailed component costs
                component_costs = calculator.calculate_detailed_cost(recipe, materials)
                
                # Format component data for response
                components_json = _format_component_costs(component_costs, component_prices)
                
                # Calculate final total based on optimal component choices
                total_copper = sum(
                    (comp['gold'] * 10000 + comp['silver'] * 100 + comp['copper'])
                    for comp in components_json.values()
                )
                
                # Add results for this weapon
                results[str(weapon_type.value)] = {
                    'total': {
                        'gold': total_copper // 10000,
                        'silver': (total_copper % 10000) // 100,
                        'copper': total_copper % 100
                    },
                    'components': components_json,
                    'profession': weapon_type.profession.value
                }
            except Exception as e:
                logger.error(f"Error calculating costs for weapon {weapon_type}: {str(e)}")
                raise PriceCalculationError(
                    f"Failed to calculate costs for {weapon_type}",
                    details={
                        'weapon_type': str(weapon_type),
                        'error': str(e),
                        'error_type': type(e).__name__
                    }
                )

        return jsonify(results)
    
    except (NetworkError, ValidationError) as e:
        raise
    except PriceCalculationError as e:
        logger.error(f"Calculation error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in calculate endpoint: {str(e)}")
        raise GW2APIError(
            "Failed to process crafting calculations",
            error_code=500,
            details={
                'error': str(e),
                'error_type': type(e).__name__
            }
        )

@app.route('/refresh-prices', methods=['GET'])
def refresh_prices():
    """Endpoint to manually refresh material prices from the GW2 API."""
    try:
        # Force a fresh fetch by clearing cache for this request
        cache_key = f"fetch_prices_()_{{}}"
        if cache_key in price_cache:
            del price_cache[cache_key]
            logger.info("Cleared price cache for refresh")
        
        prices = fetch_prices()
        return jsonify({
            item_name: {
                'gold': price.gold,
                'silver': price.silver,
                'copper': price.copper
            }
            for item_name, price in prices.items()
        })
    except (NetworkError, ValidationError) as e:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in refresh-prices endpoint: {str(e)}")
        raise GW2APIError(
            "Failed to refresh prices",
            error_code=500,
            details={
                'error': str(e),
                'error_type': type(e).__name__
            }
        )

@app.route('/fetch-weapon-price/<weapon_name>')
@cache_api_call()
def fetch_weapon_price(weapon_name):
    """Fetches the current Trading Post price for a specific weapon."""
    try:
        if weapon_name not in WEAPON_IDS:
            raise ValidationError(
                "Weapon not found",
                error_code=404,
                details={
                    'weapon_name': weapon_name,
                    'available_weapons': list(WEAPON_IDS.keys())
                }
            )
            
        weapon_id = WEAPON_IDS[weapon_name]
        url = f"https://api.guildwars2.com/v2/commerce/prices/{weapon_id}"
        headers = {"Authorization": f"Bearer {API_KEY}"}
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise NetworkError(
                "Failed to fetch weapon price from GW2 API",
                error_code=503,
                details={
                    'weapon_name': weapon_name,
                    'weapon_id': weapon_id,
                    'url': url,
                    'error': str(e)
                }
            )
        
        data = response.json()
        if not all(key in data for key in ['sells']):
            raise ValidationError(
                "Invalid weapon price response",
                error_code=500,
                details={
                    'weapon_name': weapon_name,
                    'weapon_id': weapon_id,
                    'available_fields': list(data.keys())
                }
            )
            
        sells = data['sells']['unit_price']
        return jsonify({
            'gold': sells // 10000,
            'silver': (sells % 10000) // 100,
            'copper': sells % 100
        })
        
    except (NetworkError, ValidationError) as e:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in fetch-weapon-price endpoint: {str(e)}")
        raise GW2APIError(
            "Failed to process weapon price",
            error_code=500,
            details={
                'weapon_name': weapon_name,
                'error': str(e),
                'error_type': type(e).__name__
            }
        )

if __name__ == '__main__':
    app.run(debug=True)
