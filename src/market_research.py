import requests
from datetime import datetime, timedelta
import json
import sqlite3
import time
from pathlib import Path
import logging
import os

# Logging konfigurieren
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Absoluter Pfad zur Datenbank
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'market_data.db')

# API-Konfiguration
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

def init_db():
    """Initialisiert die Datenbank mit den notwendigen Tabellen."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Tabelle für Markt-Snapshots
    c.execute('''CREATE TABLE IF NOT EXISTS market_snapshots (
        item_id INTEGER,
        timestamp DATETIME,
        lowest_sell INTEGER,
        highest_sell INTEGER,
        total_sell_listings INTEGER,
        sell_listing_positions TEXT,
        PRIMARY KEY (item_id, timestamp)
    )''')
    
    # Tabelle für tägliche Statistiken
    c.execute('''CREATE TABLE IF NOT EXISTS daily_stats (
        item_id INTEGER,
        date DATE,
        avg_price INTEGER,
        min_price INTEGER,
        max_price INTEGER,
        avg_listings INTEGER,
        sales_estimate INTEGER,
        snapshot_count INTEGER,
        PRIMARY KEY (item_id, date)
    )''')
    
    conn.commit()
    conn.close()
    logger.info("Datenbank initialisiert")

def format_price(price):
    gold = price // 10000
    silver = (price % 10000) // 100
    copper = price % 100
    return f"{gold}G {silver}S {copper}C"

def collect_market_data():
    """Sammelt aktuelle Marktdaten für alle überwachten Items."""
    conn = sqlite3.connect(DB_PATH)
    try:
        logger.info("Starte Datensammlung...")
        current_time = datetime.now().replace(microsecond=0)
        
        for item_id in TRACKED_ITEMS.keys():
            try:
                # API-Anfrage für Handelspostergebnisse
                response = requests.get(f'https://api.guildwars2.com/v2/commerce/listings/{item_id}')
                if response.status_code != 200:
                    logger.warning(f"Fehler beim Abrufen der Daten für Item {item_id}: {response.status_code}")
                    continue
                
                data = response.json()
                if not data.get('sells'):
                    logger.warning(f"Keine Verkaufsdaten für Item {item_id}")
                    continue
                
                # Extrahiere relevante Daten
                sells = data['sells']
                if not sells:
                    continue
                
                lowest_sell = sells[0]['unit_price']
                highest_sell = sells[-1]['unit_price']
                total_listings = sum(offer['quantity'] for offer in sells)
                
                # Speichere die ersten 5 Preispunkte mit Mengen
                price_points = []
                quantity_before = 0
                for i, offer in enumerate(sells[:5]):
                    price_points.append({
                        'position': i + 1,
                        'price': offer['unit_price'],
                        'quantity': offer['quantity']
                    })
                    if i < 5:  # Zähle Angebote vor Position 5
                        quantity_before += offer['quantity']
                
                # Speichere Snapshot in der Datenbank
                c = conn.cursor()
                c.execute('''
                    INSERT INTO market_snapshots 
                    (item_id, timestamp, lowest_sell, highest_sell, total_sell_listings, sell_listing_positions)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    item_id,
                    current_time,
                    lowest_sell,
                    highest_sell,
                    total_listings,
                    json.dumps({
                        'price_points': price_points,
                        'quantity_before_5': quantity_before
                    })
                ))
                
                # Logge Informationen
                logger.info(f"Waffe: {TRACKED_ITEMS[item_id]}")
                logger.info(f"Niedrigster Verkaufspreis: {format_price(lowest_sell)}")
                logger.info(f"Aktive Verkaufsangebote: {total_listings} Stück")
                
                for point in price_points:
                    logger.info(f"Position {point['position']}: {format_price(point['price'])} ({point['quantity']} Stück)")
                logger.info(f"Angebote vor Position 5: {quantity_before} Stück")
                logger.info("-" * 70)
                
            except Exception as e:
                logger.error(f"Fehler bei der Verarbeitung von Item {item_id}: {str(e)}")
                continue
        
        conn.commit()
        logger.info("Datensammlung abgeschlossen")
        
    except Exception as e:
        logger.error(f"Allgemeiner Fehler bei der Datensammlung: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

def analyze_daily_data():
    """Analysiert die gesammelten Daten des Tages."""
    conn = sqlite3.connect(DB_PATH)
    try:
        logger.info(f"Tagesanalyse für {datetime.now().date()}:")
        logger.info("-" * 70)
        
        c = conn.cursor()
        current_date = datetime.now().date()
        
        for item_id in TRACKED_ITEMS.keys():
            try:
                # Hole Snapshots für heute
                c.execute('''SELECT 
                    AVG(lowest_sell) as avg_price,
                    MIN(lowest_sell) as min_price,
                    MAX(lowest_sell) as max_price,
                    AVG(total_sell_listings) as avg_listings,
                    COUNT(*) as snapshot_count
                FROM market_snapshots 
                WHERE item_id = ? 
                AND date(timestamp) = date('now')
                ''', (item_id,))
                
                daily_stats = c.fetchone()
                
                if not daily_stats or not daily_stats[0]:
                    continue
                
                # Schätze Verkäufe basierend auf Änderungen in den Angeboten
                c.execute('''SELECT total_sell_listings
                    FROM market_snapshots
                    WHERE item_id = ?
                    AND date(timestamp) = date('now')
                    ORDER BY timestamp''', (item_id,))
                
                listings = [row[0] for row in c.fetchall()]
                sales_estimate = 0
                if len(listings) > 1:
                    for i in range(1, len(listings)):
                        if listings[i] < listings[i-1]:
                            sales_estimate += listings[i-1] - listings[i]
                
                # Speichere Tagesstatistik
                c.execute('''INSERT OR REPLACE INTO daily_stats
                    (item_id, date, avg_price, min_price, max_price, avg_listings, sales_estimate, snapshot_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    item_id,
                    current_date,
                    round(daily_stats[0]),
                    daily_stats[1],
                    daily_stats[2],
                    round(daily_stats[3]),
                    sales_estimate,
                    daily_stats[4]
                ))
                
                # Logge Statistiken
                logger.info(f"Item: {TRACKED_ITEMS[item_id]}")
                logger.info(f"Durchschnittspreis: {format_price(round(daily_stats[0]))}")
                logger.info(f"Preisbereich: {format_price(daily_stats[1])} - {format_price(daily_stats[2])}")
                logger.info(f"Durchschnittliche Angebote: {round(daily_stats[3])}")
                logger.info(f"Geschätzte Verkäufe: {sales_estimate}")
                logger.info(f"Anzahl Snapshots: {daily_stats[4]}")
                logger.info("-" * 70)
                
            except Exception as e:
                logger.error(f"Fehler bei der Analyse von Item {item_id}: {str(e)}")
                continue
        
        conn.commit()
        logger.info("Tagesanalyse abgeschlossen")
        
    except Exception as e:
        logger.error(f"Allgemeiner Fehler bei der Tagesanalyse: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

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
    # Initialisiere die Datenbank beim Start
    init_db()
    
    while True:
        try:
            collect_market_data()
            analyze_daily_data()
            time.sleep(300)  # 5 Minuten warten
        except Exception as e:
            logger.error(f"Fehler im Market Research Service: {str(e)}")
            time.sleep(60)  # Bei Fehler 1 Minute warten 