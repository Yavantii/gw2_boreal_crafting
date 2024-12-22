from flask import Blueprint, render_template, jsonify, request
import sqlite3
from datetime import datetime, timedelta
from market_research import TRACKED_ITEMS, format_price, init_db
import json
import os

# Absoluter Pfad zur Datenbank
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'market_data.db')

# Initialisiere die Datenbank beim Start
init_db()

market_bp = Blueprint('market', __name__)

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@market_bp.route('/market')
def market_analysis():
    # Sortiere die Items nach Namen
    sorted_items = dict(sorted(TRACKED_ITEMS.items(), key=lambda x: x[1]))
    return render_template('market_analysis.html', items=sorted_items)

@market_bp.route('/api/market/current')
def current_market_data():
    conn = get_db()
    try:
        c = conn.cursor()
        
        # Hole die neuesten Daten für jedes Item
        c.execute('''
            WITH LatestSnapshots AS (
                SELECT item_id, MAX(timestamp) as max_timestamp
                FROM market_snapshots
                GROUP BY item_id
            )
            SELECT m.*
            FROM market_snapshots m
            JOIN LatestSnapshots l
                ON m.item_id = l.item_id
                AND m.timestamp = l.max_timestamp
        ''')
        
        current_data = {}
        for row in c.fetchall():
            current_data[row['item_id']] = {
                'lowest_sell': row['lowest_sell'],
                'total_listings': row['total_sell_listings'],
                'positions': row['sell_listing_positions']
            }
        
        return jsonify(current_data)
    finally:
        conn.close()

@market_bp.route('/api/market/history/<int:item_id>')
def item_history(item_id):
    conn = get_db()
    try:
        c = conn.cursor()
        
        # Hole 7-Tage-Historie
        seven_days_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        c.execute('''
            SELECT date(timestamp) as date,
                   MIN(lowest_sell) as min_price,
                   MAX(lowest_sell) as max_price,
                   AVG(lowest_sell) as avg_price,
                   AVG(total_sell_listings) as avg_listings
            FROM market_snapshots
            WHERE item_id = ? AND date(timestamp) >= ?
            GROUP BY date(timestamp)
            ORDER BY date(timestamp)
        ''', (item_id, seven_days_ago))
        
        history_data = []
        for row in c.fetchall():
            history_data.append({
                'date': row['date'],
                'min_price': row['min_price'],
                'max_price': row['max_price'],
                'avg_price': row['avg_price'],
                'avg_listings': row['avg_listings']
            })
        
        return jsonify(history_data)
    finally:
        conn.close()

@market_bp.route('/api/market/recommendations')
def get_recommendations():
    conn = get_db()
    try:
        c = conn.cursor()
        
        # Hole die neuesten Daten
        recommendations = {
            'sell': [],  # Beste Verkaufschancen
            'relist': [] # Neueinstellen empfohlen
        }
        
        # Finde Items mit wenigen Angeboten und gutem Preis
        c.execute('''
            WITH LatestSnapshots AS (
                SELECT item_id, MAX(timestamp) as max_timestamp
                FROM market_snapshots
                GROUP BY item_id
            )
            SELECT m.*, 
                   (SELECT AVG(lowest_sell) 
                    FROM market_snapshots 
                    WHERE item_id = m.item_id 
                    AND timestamp >= datetime('now', '-7 days')
                   ) as avg_price_7d
            FROM market_snapshots m
            JOIN LatestSnapshots l
                ON m.item_id = l.item_id
                AND m.timestamp = l.max_timestamp
            WHERE m.total_sell_listings < 50  -- Wenige Angebote
            ORDER BY (m.lowest_sell / avg_price_7d) DESC  -- Guter Preis im Vergleich zum 7-Tage-Durchschnitt
            LIMIT 5
        ''')
        
        for row in c.fetchall():
            recommendations['sell'].append({
                'item_id': row['item_id'],
                'name': TRACKED_ITEMS[row['item_id']],
                'current_price': format_price(row['lowest_sell']),
                'listings': row['total_sell_listings']
            })
        
        # Finde Items, die neu eingestellt werden sollten
        c.execute('''
            WITH LatestSnapshots AS (
                SELECT item_id, MAX(timestamp) as max_timestamp
                FROM market_snapshots
                GROUP BY item_id
            )
            SELECT m.*, json_extract(m.sell_listing_positions, '$[0].quantity') as top_quantity
            FROM market_snapshots m
            JOIN LatestSnapshots l
                ON m.item_id = l.item_id
                AND m.timestamp = l.max_timestamp
            WHERE json_extract(m.sell_listing_positions, '$[0].quantity') > 10  -- Viele Angebote vor uns
            ORDER BY json_extract(m.sell_listing_positions, '$[0].quantity') DESC
            LIMIT 5
        ''')
        
        for row in c.fetchall():
            recommendations['relist'].append({
                'item_id': row['item_id'],
                'name': TRACKED_ITEMS[row['item_id']],
                'items_ahead': row['top_quantity'],
                'current_price': format_price(row['lowest_sell'])
            })
        
        return jsonify(recommendations)
    finally:
        conn.close() 

@market_bp.route('/api/market/details/<int:item_id>')
def get_item_details(item_id):
    conn = get_db()
    try:
        c = conn.cursor()
        
        # Hole die letzten 24 Stunden an Snapshots
        c.execute('''
            SELECT 
                strftime('%Y-%m-%d %H:00:00', timestamp) as hour,
                AVG(lowest_sell) as avg_price,
                MIN(lowest_sell) as min_price,
                MAX(lowest_sell) as max_price,
                AVG(total_sell_listings) as avg_listings,
                MAX(sell_listing_positions) as latest_positions
            FROM market_snapshots
            WHERE item_id = ? 
            AND timestamp >= datetime('now', '-24 hours')
            GROUP BY strftime('%Y-%m-%d %H:00:00', timestamp)
            ORDER BY hour ASC
        ''', (item_id,))
        
        hourly_data = []
        for row in c.fetchall():
            hourly_data.append({
                'timestamp': row[0],
                'avg_price': int(row[1]),
                'min_price': row[2],
                'max_price': row[3],
                'avg_listings': int(row[4]),
                'positions': json.loads(row[5]) if row[5] else []
            })
        
        # Hole die letzten 7 Tage an Tagesstatistiken
        c.execute('''
            SELECT 
                date,
                avg_price,
                min_price,
                max_price,
                avg_listings,
                sales_estimate
            FROM daily_stats
            WHERE item_id = ?
            AND date >= date('now', '-7 days')
            ORDER BY date ASC
        ''', (item_id,))
        
        daily_stats = []
        for row in c.fetchall():
            daily_stats.append({
                'date': row[0],
                'avg_price': row[1],
                'min_price': row[2],
                'max_price': row[3],
                'avg_listings': int(row[4]),
                'sales_estimate': row[5]
            })
        
        # Aktuelle Position im Handelsposten
        current_position = None
        if hourly_data and hourly_data[-1]['positions']:
            positions = hourly_data[-1]['positions']
            total_items = sum(p['quantity'] for p in positions)
            current_position = {
                'total_listings': total_items,
                'price_points': positions[:5]  # Top 5 Preispunkte
            }
        
        return jsonify({
            'hourly_data': hourly_data,
            'daily_stats': daily_stats,
            'current_position': current_position,
            'name': TRACKED_ITEMS.get(item_id, 'Unbekanntes Item')
        })
        
    finally:
        conn.close() 

# Neue Route für den Service-Status
@market_bp.route('/api/market/service-status')
def service_status():
    try:
        conn = get_db()
        c = conn.cursor()
        
        # Prüfe den letzten Snapshot
        c.execute('''
            SELECT MAX(timestamp) as last_update
            FROM market_snapshots
        ''')
        
        result = c.fetchone()
        last_update = result['last_update'] if result and result['last_update'] else None
        
        if not last_update:
            return jsonify({
                'status': 'inactive',
                'message': 'Keine Daten vorhanden',
                'last_update': None
            })
            
        last_update_time = datetime.strptime(last_update, '%Y-%m-%d %H:%M:%S')
        time_diff = datetime.now() - last_update_time
        
        if time_diff.total_seconds() > 600:  # 10 Minuten
            status = 'inactive'
            message = 'Service läuft nicht (Letzte Aktualisierung vor mehr als 10 Minuten)'
        else:
            status = 'active'
            message = 'Service läuft'
            
        return jsonify({
            'status': status,
            'message': message,
            'last_update': last_update
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Fehler beim Prüfen des Service-Status: {str(e)}',
            'last_update': None
        })
    finally:
        conn.close() 

@market_bp.route('/api/market/chat', methods=['POST'])
def market_chat():
    try:
        user_message = request.json.get('message')
        
        # Hole relevante Marktdaten aus der Datenbank
        conn = get_db()
        c = conn.cursor()
        
        # Hole die neuesten Snapshots
        c.execute('''
            WITH LatestSnapshots AS (
                SELECT item_id, MAX(timestamp) as max_timestamp
                FROM market_snapshots
                GROUP BY item_id
            )
            SELECT m.*, i.date, i.avg_price, i.min_price, i.max_price, i.sales_estimate
            FROM market_snapshots m
            JOIN LatestSnapshots l ON m.item_id = l.item_id AND m.timestamp = l.max_timestamp
            LEFT JOIN daily_stats i ON m.item_id = i.item_id AND date(m.timestamp) = i.date
        ''')
        
        market_data = {}
        for row in c.fetchall():
            item_id = row['item_id']
            item_name = TRACKED_ITEMS.get(item_id, 'Unbekannt')
            market_data[item_name] = {
                'current_price': row['lowest_sell'],
                'total_listings': row['total_sell_listings'],
                'avg_price': row['avg_price'],
                'min_price': row['min_price'],
                'max_price': row['max_price'],
                'sales_estimate': row['sales_estimate'],
                'positions': json.loads(row['sell_listing_positions'])
            }
        
        # Analysiere die Daten und erstelle eine Antwort
        response = analyze_market_data(user_message, market_data)
        
        return jsonify({
            'response': response,
            'market_data': market_data
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Fehler bei der Verarbeitung: {str(e)}'
        }), 500
    finally:
        conn.close()

def analyze_market_data(user_message, market_data):
    """Analysiert die Marktdaten basierend auf der Benutzeranfrage."""
    
    if not market_data:
        return "Entschuldigung, aber ich habe noch keine Marktdaten zur Analyse. Der Market Research Service sammelt gerade die ersten Daten."
    
    response = "Basierend auf den aktuellen Marktdaten:\n\n"
    
    # Finde die profitabelsten Items
    profitable_items = []
    for item_name, data in market_data.items():
        if data['avg_price'] and data['current_price'] and data['avg_price'] > 0:
            profit_margin = (data['current_price'] - data['avg_price']) / data['avg_price'] * 100
            profitable_items.append((item_name, profit_margin, data))
    
    if not profitable_items:
        response = "Aktuelle Marktübersicht:\n\n"
        for item_name, data in market_data.items():
            response += f"- {item_name}:\n"
            response += f"  Aktueller Preis: {format_price(data['current_price'])}\n"
            response += f"  Aktive Angebote: {data['total_listings']} Stück\n"
            
            # Füge Positionsdaten hinzu, wenn verfügbar
            if data['positions'].get('price_points'):
                price_points = data['positions']['price_points']
                if price_points:
                    response += f"  Top 3 Preispunkte:\n"
                    for point in price_points[:3]:
                        response += f"    Position {point['position']}: {format_price(point['price'])} ({point['quantity']} Stück)\n"
            response += "\n"
        
        return response
    
    # Sortiere nach Gewinnmarge
    profitable_items.sort(key=lambda x: x[1], reverse=True)
    
    # Füge Empfehlungen hinzu
    response += "Top 3 profitable Items:\n"
    for item_name, margin, data in profitable_items[:3]:
        response += f"- {item_name}:\n"
        response += f"  Gewinnmarge: {margin:.1f}%\n"
        response += f"  Aktueller Preis: {format_price(data['current_price'])}\n"
        response += f"  Durchschnittspreis: {format_price(data['avg_price'])}\n"
        response += f"  Aktive Angebote: {data['total_listings']} Stück\n"
        if data['sales_estimate'] is not None:
            response += f"  Verkaufsschätzung: {data['sales_estimate']} pro Tag\n"
        response += "\n"
    
    # Füge allgemeine Marktanalyse hinzu
    total_listings = sum(data['total_listings'] for data in market_data.values())
    response += f"Allgemeine Marktanalyse:\n"
    response += f"- Gesamtangebote im Markt: {total_listings} Stück\n"
    
    if profitable_items:
        avg_margin = sum(margin for _, margin, _ in profitable_items) / len(profitable_items)
        response += f"- Durchschnittliche Gewinnmarge: {avg_margin:.1f}%\n"
    
    # Füge Handelsempfehlungen hinzu
    response += "\nHandelsempfehlungen:\n"
    
    # Finde Items mit wenigen Angeboten
    low_supply = sorted(market_data.items(), key=lambda x: x[1]['total_listings'])[:3]
    response += "Items mit geringem Angebot (Verkaufschance):\n"
    for item_name, data in low_supply:
        response += f"- {item_name}: {data['total_listings']} Angebote\n"
    
    return response 

@market_bp.route('/api/market/restart-service', methods=['POST'])
def restart_service():
    try:
        import subprocess
        import sys
        import os

        # Starte den Market Research Service als Hintergrundprozess
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'market_research.py')
        subprocess.Popen([sys.executable, script_path], 
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        creationflags=subprocess.CREATE_NO_WINDOW)
        
        return jsonify({
            'status': 'success',
            'message': 'Market Research Service wurde neu gestartet'
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Fehler beim Neustarten des Services: {str(e)}'
        }), 500