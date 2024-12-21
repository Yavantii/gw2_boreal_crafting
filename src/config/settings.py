"""
Konfigurationseinstellungen für die Anwendung
"""

import os
from datetime import timedelta

# API-Konfiguration
API_KEY = os.getenv('GW2_API_KEY', "53E1B734-BE78-6D4B-BFC4-AB5A7BD0CE8E8CE228E8-69FC-4E92-9CAE-AD4C68D3AB44")
API_BASE_URL = "https://api.guildwars2.com/v2"
API_COMMERCE_PRICES_URL = f"{API_BASE_URL}/commerce/prices"

# Cache-Konfiguration
CACHE_DURATION = timedelta(minutes=5)

# Trading Post Gebühren
LISTING_FEE_PERCENT = 5
EXCHANGE_FEE_PERCENT = 10

# Flask-Konfiguration
class Config:
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
    
class DevelopmentConfig(Config):
    DEBUG = True
    
class ProductionConfig(Config):
    # Produktionseinstellungen hier
    pass
    
class TestingConfig(Config):
    TESTING = True
    
# Konfigurationsauswahl basierend auf Umgebungsvariable
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Gibt die aktuelle Konfiguration basierend auf der Umgebung zurück"""
    env = os.getenv('FLASK_ENV', 'default')
    return config[env] 