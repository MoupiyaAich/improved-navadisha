import mysql.connector
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': os.getenv('DB_PASSWORD'),
    'database': 'navadisha'
}

def save_to_db(problem, response, citations, language, region, category):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        query = """
            INSERT INTO queries_navadisha (problem, response, source_citations, language, region, legal_category) 
            VALUES (%s, %s, %s, %s, %s, %s)
        """

        cursor.execute(query, (problem, response, citations, language, region, category))

        conn.commit()
        cursor.close()
        conn.close()
        print("Data saved successfully!")

    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        
    except mysql.connector.Error as err:
        print(f"Database error: {err}")