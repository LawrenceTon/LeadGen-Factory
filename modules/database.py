import sqlite3
import pandas as pd
import os
import json
from datetime import datetime

class LeadDB:
    def __init__(self, db_path="leads.db"):
        self.db_path = db_path
        self.conn = None
        self._init_db()

    def _init_db(self):
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE,
                status TEXT,
                ai_result TEXT,
                timestamp DATETIME
            )
        ''')
        self.conn.commit()

    def record_exists(self, url):
        """Checks if a URL has already been processed."""
        if not url: return False
        cursor = self.conn.cursor()
        cursor.execute("SELECT 1 FROM audit_logs WHERE url = ?", (url,))
        return cursor.fetchone() is not None

    def save_audit(self, url, status, ai_result):
        """Saves or updates the audit result."""
        cursor = self.conn.cursor()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # upsert or ignore? Phoenix Protocol says persist data. 
        # We'll use REPLACE into to just update if it exists or insert new.
        cursor.execute('''
            INSERT OR REPLACE INTO audit_logs (url, status, ai_result, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (url, status, ai_result, timestamp))
        self.conn.commit()

    def export_to_csv(self, filepath):
        """Exports the entire DB to a CSV file."""
        try:
            query = "SELECT url, status, ai_result, timestamp FROM audit_logs"
            df = pd.read_sql_query(query, self.conn)
            
            # The ai_result is JSON string, maybe we want to expand it?
            # For now, export raw or simple expansion if possible. 
            # Prompt didn't specify expansion, but 'Export History' usually implies readable.
            # Let's try to expand if valid json
            expanded_data = []
            for index, row in df.iterrows():
                base = {
                    "URL": row['url'],
                    "Status": row['status'],
                    "Timestamp": row['timestamp']
                }
                try:
                    meta = json.loads(row['ai_result'])
                    if isinstance(meta, dict):
                        base.update(meta)
                    else:
                        base["Result_Data"] = str(meta)
                except:
                    base["Result_Data"] = str(row['ai_result'])
                
                expanded_data.append(base)
            
            final_df = pd.DataFrame(expanded_data)
            final_df.to_csv(filepath, index=False)
            return True, f"Exported {len(final_df)} records."
        except Exception as e:
            return False, str(e)
