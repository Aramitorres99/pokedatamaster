import psycopg2
from psycopg2 import OperationalError

#realizar la conexion a la base de datos
def get_conexion():
    try:
        conn = psycopg2.connect(
            dbname = 'pokemon',
            user = "postgres",
            password = "123456",
            host= "localhost",
            port = "5432"
        )
        print("La conexion fue exitosa")
        return conn
    except OperationalError as e:
        print(f"Error de conexion: {e}")
        return None
    
 
