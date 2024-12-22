from flask import Blueprint, render_template, jsonify
import sqlite3
from datetime import datetime, timedelta
from market_research import TRACKED_ITEMS, format_price

market_bp = Blueprint('market', __name__)

def get_db():
    conn = sqlite3.connect('market_data.db')
    conn.row_factory = sqlite3.Row
    return conn

@market_bp.route('/market')
def market_analysis():
    return render_template('market_analysis.html', items=TRACKED_ITEMS)

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