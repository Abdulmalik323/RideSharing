import psycopg2

def get_db_connection():
    conn = psycopg2.connect(
        host="localhost",
        database="your_database_name",
        user="your_username",
        password="your_password"
    )
    return conn
