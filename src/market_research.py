import requests
from datetime import datetime, timedelta
import json
import sqlite3
import time
from pathlib import Path

API_KEY = "53E1B734-BE78-6D4B-BFC4-AB5A7BD0CE8E8CE228E8-69FC-4E92-9CAE-AD4C68D3AB44"
headers = {"Authorization": f"Bearer {API_KEY}"}

# Erweitere die IDs um die Inscription
TRACKED_ITEMS = {
    92218: "Restored Boreal Axe",
    92331: "Restored Boreal Dagger",
    92367: "Restored Boreal Focus",
    92363: "Restored Boreal Greatsword",
    92230: "Restored Boreal Hammer",
    92354: "Restored Boreal Longbow",
    92395: "Restored Boreal Mace",
    92222: "Restored Boreal Pistol",
    92248: "Restored Boreal Rifle",
    92244: "Restored Boreal Scepter",
    92261: "Restored Boreal Shield",
    92298: "Restored Boreal Short Bow",
    92343: "Restored Boreal Staff",
    92359: "Restored Boreal Sword",
    92217: "Restored Boreal Torch",
    92290: "Restored Boreal Warhorn",
    19920: "Berserker's Orichalcum Imbued Inscription"
}

def setup_database():
    db_path = Path("market_data.db")
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Tabelle für Marktdaten
    c.execute('''CREATE TABLE IF NOT EXISTS market_snapshots (
        timestamp DATETIME,
        item_id INTEGER,
        lowest_sell INTEGER,
        total_sell_listings INTEGER,
        sell_listing_positions TEXT,
        PRIMARY KEY (timestamp, item_id)
    )''')
    
    # Tabelle für tägliche Zusammenfassungen
    c.execute('''CREATE TABLE IF NOT EXISTS daily_stats (
        date DATE,
        item_id INTEGER,
        avg_price INTEGER,
        min_price INTEGER,
        max_price INTEGER,
        avg_listings INTEGER,
        sales_estimate INTEGER,
        PRIMARY KEY (date, item_id)
    )''')
    
    conn.commit()
    return conn

def format_price(price):
    gold = price // 10000
    silver = (price % 10000) // 100
    copper = price % 100
    return f"{gold}G {silver}S {copper}C"

def collect_market_data(conn):
    c = conn.cursor()
    timestamp = datetime.now()
    
    print(f"\nMarktdaten-Sammlung ({timestamp.strftime('%Y-%m-%d %H:%M:%S')}):")
    print("-" * 70)
    
    for item_id, name in TRACKED_ITEMS.items():
        try:
            response = requests.get(f"https://api.guildwars2.com/v2/commerce/listings/{item_id}")
            if response.status_code == 200:
                data = response.json()
                
                # Verkaufsangebote analysieren
                sells = data.get('sells', [])
                if sells:
                    lowest_sell = sells[0]['unit_price']
                    total_listings = sum(listing['quantity'] for listing in sells)
                    
                    # Speichere die ersten 50 Verkaufspreise mit Mengen
                    listing_positions = json.dumps([
                        {'price': s['unit_price'], 'quantity': s['quantity']}
                        for s in sells[:50]
                    ])
                    
                    # Speichere Snapshot
                    c.execute('''INSERT INTO market_snapshots 
                        (timestamp, item_id, lowest_sell, total_sell_listings, sell_listing_positions)
                        VALUES (?, ?, ?, ?, ?)''',
                        (timestamp, item_id, lowest_sell, total_listings, listing_positions))
                    
                    print(f"Waffe: {name}")
                    print(f"Niedrigster Verkaufspreis: {format_price(lowest_sell)}")
                    print(f"Aktive Verkaufsangebote: {total_listings} Stück")
                    
                    # Analysiere Verkaufspositionen
                    total_before = 0
                    for i, listing in enumerate(sells[:5], 1):
                        print(f"Position {i}: {format_price(listing['unit_price'])} ({listing['quantity']} Stück)")
                        total_before += listing['quantity']
                    
                    print(f"Angebote vor Position 5: {total_before} Stück")
                    print("-" * 70)
            
            time.sleep(1)  # API-Rate-Limit beachten
            
        except Exception as e:
            print(f"Fehler bei {name}: {str(e)}")
            continue
    
    conn.commit()

def analyze_daily_stats(conn):
    c = conn.cursor()
    yesterday = (datetime.now() - timedelta(days=1)).date()
    
    print(f"\nTagesanalyse für {yesterday}:")
    print("-" * 70)
    
    for item_id, name in TRACKED_ITEMS.items():
        # Hole Daten des Vortags
        c.execute('''SELECT 
            MIN(lowest_sell) as min_price,
            MAX(lowest_sell) as max_price,
            AVG(lowest_sell) as avg_price,
            AVG(total_sell_listings) as avg_listings,
            COUNT(*) as snapshots
            FROM market_snapshots 
            WHERE date(timestamp) = ? AND item_id = ?''',
            (yesterday, item_id))
        
        stats = c.fetchone()
        if stats and stats[0]:
            min_price, max_price, avg_price, avg_listings, snapshots = stats
            
            # Schätze Verkäufe durch Änderungen in den Listings
            c.execute('''SELECT total_sell_listings 
                FROM market_snapshots 
                WHERE date(timestamp) = ? AND item_id = ?
                ORDER BY timestamp''',
                (yesterday, item_id))
            
            listings = [r[0] for r in c.fetchall()]
            sales_estimate = 0
            for i in range(1, len(listings)):
                if listings[i] < listings[i-1]:
                    sales_estimate += listings[i-1] - listings[i]
            
            # Speichere Tagesstatistik
            c.execute('''INSERT OR REPLACE INTO daily_stats 
                (date, item_id, avg_price, min_price, max_price, avg_listings, sales_estimate)
                VALUES (?, ?, ?, ?, ?, ?, ?)''',
                (yesterday, item_id, int(avg_price), min_price, max_price, 
                 int(avg_listings), sales_estimate))
            
            print(f"Item: {name}")
            print(f"Durchschnittspreis: {format_price(int(avg_price))}")
            print(f"Preisbereich: {format_price(min_price)} - {format_price(max_price)}")
            print(f"Durchschnittliche Angebote: {int(avg_listings)}")
            print(f"Geschätzte Verkäufe: {sales_estimate}")
            print(f"Anzahl Snapshots: {snapshots}")
            print("-" * 70)
    
    conn.commit()

def main():
    conn = setup_database()
    try:
        # Sammle aktuelle Daten
        collect_market_data(conn)
        
        # Analysiere den Vortag
        analyze_daily_stats(conn)
        
    finally:
        conn.close()

if __name__ == "__main__":
    main() 