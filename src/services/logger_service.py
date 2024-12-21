"""
Logger-Service für strukturiertes Logging
"""

import logging
import json
import os
from datetime import datetime
from functools import wraps
from flask import request, has_request_context

class LoggerService:
    def __init__(self, app_name='gw2craft', log_dir='logs'):
        self.app_name = app_name
        self.log_dir = log_dir
        
        # Erstelle Log-Verzeichnis falls nicht vorhanden
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        # Konfiguriere Logger
        self.setup_loggers()
        
    def setup_loggers(self):
        """Konfiguriert die verschiedenen Logger"""
        # API Logger
        self.api_logger = self._create_logger('api', 'api.log')
        # Berechnungs-Logger
        self.calc_logger = self._create_logger('calculation', 'calculation.log')
        # Allgemeiner Logger
        self.app_logger = self._create_logger('app', 'app.log')
        
    def _create_logger(self, name, filename):
        """Erstellt einen konfigurierten Logger"""
        logger = logging.getLogger(f"{self.app_name}.{name}")
        logger.setLevel(logging.INFO)
        
        # Datei-Handler
        file_handler = logging.FileHandler(
            os.path.join(self.log_dir, filename),
            encoding='utf-8'
        )
        file_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        return logger
        
    def _format_log_message(self, message, extra=None):
        """Formatiert die Log-Nachricht als JSON"""
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'message': message
        }
        
        # Füge Request-Informationen hinzu wenn verfügbar
        if has_request_context():
            log_data.update({
                'method': request.method,
                'path': request.path,
                'ip': request.remote_addr
            })
            
        # Füge zusätzliche Informationen hinzu
        if extra:
            log_data.update(extra)
            
        return json.dumps(log_data)
        
    def log_api_call(self, endpoint, response_time, status_code, error=None):
        """Loggt API-Aufrufe"""
        extra = {
            'endpoint': endpoint,
            'response_time_ms': response_time,
            'status_code': status_code
        }
        if error:
            extra['error'] = str(error)
            
        self.api_logger.info(
            self._format_log_message('API call', extra)
        )
        
    def log_calculation(self, weapon_type, calculation_time, result=None, error=None):
        """Loggt Berechnungen"""
        extra = {
            'weapon_type': weapon_type,
            'calculation_time_ms': calculation_time
        }
        if result:
            extra['result'] = result
        if error:
            extra['error'] = str(error)
            
        self.calc_logger.info(
            self._format_log_message('Calculation', extra)
        )
        
    def log_error(self, error, context=None):
        """Loggt Fehler"""
        extra = {
            'error_type': error.__class__.__name__,
            'error_message': str(error)
        }
        if context:
            extra['context'] = context
            
        self.app_logger.error(
            self._format_log_message('Error occurred', extra)
        )

def log_execution_time(logger_func):
    """
    Decorator zum Loggen der Ausführungszeit
    
    Args:
        logger_func: Logging-Funktion die aufgerufen werden soll
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = datetime.now()
            try:
                result = func(*args, **kwargs)
                execution_time = (datetime.now() - start_time).total_seconds() * 1000
                logger_func(execution_time, result=result)
                return result
            except Exception as e:
                execution_time = (datetime.now() - start_time).total_seconds() * 1000
                logger_func(execution_time, error=e)
                raise
        return wrapper
    return decorator 