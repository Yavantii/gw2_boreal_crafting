import requests
import json
from datetime import datetime

API_KEY = "53E1B734-BE78-6D4B-BFC4-AB5A7BD0CE8E8CE228E8-69FC-4E92-9CAE-AD4C68D3AB44"
headers = {"Authorization": f"Bearer {API_KEY}"}

def format_time_since(created_time):
    created = datetime.fromisoformat(created_time.replace('Z', '+00:00'))
    now = datetime.now().astimezone()
    diff = now - created
    
    if diff.days > 0:
        return f"vor {diff.days} Tagen"
    hours = diff.seconds // 3600
    if hours > 0:
        return f"vor {hours} Stunden"
    minutes = (diff.seconds % 3600) // 60
    return f"vor {minutes} Minuten"

def get_listing_position(item_id, my_price):
    try:
        response = requests.get(f"https://api.guildwars2.com/v2/commerce/listings/{item_id}")
        if response.status_code == 200:
            listings = response.json()
            sells = listings.get('sells', [])
            position = 1
            total_quantity = 0
            
            for sell in sells:
                if sell['unit_price'] < my_price:
                    total_quantity += sell['quantity']
                elif sell['unit_price'] == my_price:
                    # Bei gleichem Preis: Position ist nach allen vorherigen plus 1
                    return total_quantity + 1
            
            # Wenn wir hier ankommen, sind wir teurer als alle anderen
            return total_quantity + 1
    except Exception as e:
        print(f"Fehler beim Abrufen der Position: {e}")
        return None
    return None

def get_market_info(item_id, my_price):
    try:
        response = requests.get(f"https://api.guildwars2.com/v2/commerce/listings/{item_id}")
        if response.status_code == 200:
            listings = response.json()
            sells = listings.get('sells', [])
            
            # Finde den nächstniedrigeren und nächsthöheren Preis
            lower_price = None
            higher_price = None
            position = 1
            total_quantity = 0
            
            for sell in sells:
                if sell['unit_price'] < my_price:
                    lower_price = sell['unit_price']
                    total_quantity += sell['quantity']
                elif sell['unit_price'] == my_price:
                    position = total_quantity + 1
                elif sell['unit_price'] > my_price and not higher_price:
                    higher_price = sell['unit_price']
                    break
            
            return {
                'position': position,
                'total_listings': len(sells),
                'lower_price': lower_price,
                'higher_price': higher_price
            }
    except Exception as e:
        print(f"Fehler beim Abrufen der Marktinfos: {e}")
    return None

def format_price(price):
    gold = price // 10000
    silver = (price % 10000) // 100
    copper = price % 100
    return f"{gold}G {silver}S {copper}C"

def get_current_sells():
    response = requests.get(
        "https://api.guildwars2.com/v2/commerce/transactions/current/sells",
        headers=headers
    )
    
    if response.status_code == 200:
        sells = response.json()
        
        # Hole Item-Details für jedes Angebot
        item_ids = [str(item['item_id']) for item in sells]
        if item_ids:
            items_response = requests.get(
                f"https://api.guildwars2.com/v2/items?ids={','.join(item_ids)}"
            )
            items = {item['id']: item for item in items_response.json()}
            
            # Sortiere nach Einstelldatum (neueste zuerst)
            sells.sort(key=lambda x: x['created'], reverse=True)
            
            print("\nAktuelle Verkaufsangebote:")
            print("-" * 70)
            for sell in sells:
                item = items[sell['item_id']]
                market_info = get_market_info(sell['item_id'], sell['price'])
                
                print(f"Item: {item['name']}")
                print(f"Preis: {format_price(sell['price'])}")
                print(f"Menge: {sell['quantity']}")
                print(f"Eingestellt: {format_time_since(sell['created'])}")
                
                if market_info:
                    print(f"Position: {market_info['position']}. von {market_info['total_listings']} Angeboten")
                    if market_info['lower_price']:
                        print(f"Günstigstes Angebot: {format_price(market_info['lower_price'])}")
                    if market_info['higher_price']:
                        print(f"Nächsthöheres Angebot: {format_price(market_info['higher_price'])}")
                
                print("-" * 70)
        else:
            print("Keine aktiven Verkaufsangebote gefunden.")
    else:
        print(f"Fehler beim Abrufen der Daten: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    get_current_sells() 