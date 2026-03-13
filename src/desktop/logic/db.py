import sqlite3
import hashlib
from typing import List
from src.desktop.logic.validator import es_dato_valido

class DatabaseManager:
    """
    Manages SQLite persistence with global deduplication using value hashes.
    """
    def __init__(self, db_path="rs_omni_extractor.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize local SQLite database with robust schema"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Targets table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS targets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    input_raw TEXT,
                    tipo TEXT,
                    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
                    estado TEXT
                )
            ''')
            # Results table with global uniqueness based on hash
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    target_id INTEGER REFERENCES targets(id),
                    campo TEXT,
                    valor TEXT,
                    valor_hash TEXT,
                    fuente TEXT,
                    confianza REAL,
                    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(valor_hash, campo)
                )
            ''')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_results_target ON results(target_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_results_campo ON results(campo)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_results_hash ON results(valor_hash)')
            conn.commit()

    def save_results(self, data_type: str, results: List[str], target_input: str = ""):
        """Save extraction results with global deduplication using MD5 hashes."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 1. Create target record
            cursor.execute('INSERT INTO targets (input_raw, tipo, estado) VALUES (?, ?, ?)', 
                          (target_input, data_type, 'SUCCESS'))
            target_id = cursor.lastrowid
            
            # 2. Insert results with global UNIQUE check on hash
            for val in results:
                if not es_dato_valido(val, data_type):
                    continue
                
                # Generate 16-char MD5 hash for global deduplication
                val_hash = hashlib.md5(val.encode('utf-8', errors='ignore')).hexdigest()[:16]
                
                try:
                    cursor.execute('''
                        INSERT OR IGNORE INTO results (target_id, campo, valor, valor_hash, fuente, confianza) 
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (target_id, data_type, val, val_hash, 'Scraper', 1.0))
                except sqlite3.Error as e:
                    print(f"[DB ERROR] Error guardando {val}: {e}")
            
            conn.commit()
            return target_id
