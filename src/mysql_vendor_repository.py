import mysql.connector

class MySQLVendorRepository:
    def __init__(self, host: str, user: str, password: str, database: str, port: int):
        self.connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            port=port
        )
    
    def _ensure_connection(self):
        try:
            if not self.connection.is_connected():
                self.connection.reconnect(attempts=3, delay=2)
        except Exception as e:
            print(f"Error reconnecting to MySQL: {e}")
            self.connection = mysql.connector.connect(
                host=self.connection.server_host,
                user=self.connection.user,
                password=self.connection.password,
                database=self.connection.database,
                port=self.connection._port
            )

    def get_all_medicines(self):
        self._ensure_connection()
        cursor = None
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM medicine_name_mapping")
            result = cursor.fetchall()
            result_dict = {row['vendor_medicine_name']: row['master_medicine_code'] for row in result}
            return result_dict
        except Exception as e:
            print(f"Error fetching all medicines: {e}")
            return None
        finally:
            if cursor is not None:
                cursor.close()
    
    def save_medicines(self, medicine_dict):    
        self._ensure_connection()
        cursor = None
        try:
            cursor = self.connection.cursor()
            data = [
                (vendor, master)
                for vendor, master in medicine_dict.items()
            ]
            sql = """
            INSERT INTO medicine_name_mapping (vendor_medicine_name, master_medicine_code)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE master_medicine_code=VALUES(master_medicine_code)
            """
            cursor.executemany(sql, data)
            self.connection.commit()
            print(f"Saved {len(data)} entries to medicine_name_mapping.")
        except Exception as e:
            print(f"Error saving data {medicine_dict} : {e}")
            self.connection.rollback()
        finally:
            if cursor is not None:
                cursor.close()

    def delete_medicines(self, vendor_medicine_names):
        self._ensure_connection()
        cursor = None
        try:
            cursor = self.connection.cursor()
            sql = "DELETE FROM medicine_name_mapping WHERE vendor_medicine_name = %s"
            data = [(name,) for name in vendor_medicine_names]
            cursor.executemany(sql, data)
            self.connection.commit()
            print(f"Deleted {len(vendor_medicine_names)} medicines.")
        except Exception as e:
            print(f"Error deleting medicines {vendor_medicine_names}: {e}")
            self.connection.rollback()
        finally:
            if cursor is not None:
                cursor.close()

    def close(self):
        if self.connection.is_connected():
            self.connection.close()