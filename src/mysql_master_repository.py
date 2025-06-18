import mysql.connector

class MySQLMasterRepository:
    def __init__(self, host: str, user: str, password: str, database: str, port: int):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database

    def get_master_data(self):
        connection = None
        cursor = None
        try:
            print(
                f"Connecting to MySQL at {self.host}:{self.port} with user {self.user} using database: {self.database} and password: {self.password}")
            connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                port=self.port
            )
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT name, code, id FROM variant_products")
            result = cursor.fetchall()
            result_dict = [(row['name'], row['code'], row['id']) for row in result]
            return result_dict
        except Exception as e:
            print(f"Error fetching all medicines: {e}")
            return None
        finally:
            if connection is not None and connection.is_connected():
                connection.close()
            if cursor is not None:
                cursor.close()
