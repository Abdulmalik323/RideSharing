import psycopg2

def get_db_connection():
    conn = psycopg2.connect(
        host="localhost",
        database="ride_connect",
        user="user1",
        password="123"
    )
    return conn
