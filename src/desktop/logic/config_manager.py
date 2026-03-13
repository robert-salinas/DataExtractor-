import yaml
import os
import sys

class ConfigManager:
    """
    Singleton class to manage application configuration from config.yaml.
    """
    _instance = None
    _config = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self):
        # Handle path when running as a PyInstaller executable
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        config_path = os.path.join(base_path, 'config.yaml')
        
        # Fallback if not found in root (e.g. current working directory)
        if not os.path.exists(config_path):
            config_path = 'config.yaml'

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f)
        except Exception as e:
            print(f"[ERROR] No se pudo cargar config.yaml: {e}")
            # Configuración por defecto mínima
            self._config = {
                'scraping': {'rate_limit': 2, 'max_retries': 3, 'timeout': 30, 'max_threads': 3, 'headless': False},
                'proxies': {'archivo': 'proxies.txt', 'rotar': True},
                'osint': {'breach_check': True, 'max_subdominios': 100, 'dns_tipos': ['A', 'MX', 'TXT', 'NS', 'SOA', 'AAAA']},
                'sqli': {'umbral_multiplicador': 2.5, 'baseline_requests': 3, 'probar_headers': True, 'probar_post': True},
                'export': {'carpeta': './resultados', 'formato': 'json'}
            }

    def get(self, section, key=None, default=None):
        if section in self._config:
            if key is None:
                return self._config[section]
            return self._config[section].get(key, default)
        return default

    def set(self, section, key, value):
        if section not in self._config:
            self._config[section] = {}
        self._config[section][key] = value
        self.save()

    def save(self):
        # Handle path when running as a PyInstaller executable
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        config_path = os.path.join(base_path, 'config.yaml')
        
        # Fallback if not found in root (e.g. current working directory)
        if not os.path.exists(config_path):
            config_path = 'config.yaml'

        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self._config, f, default_flow_style=False)
        except Exception as e:
            print(f"[ERROR] No se pudo guardar config.yaml: {e}")
