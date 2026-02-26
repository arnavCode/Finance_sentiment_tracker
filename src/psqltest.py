import os
import psycopg
from dotenv import load_dotenv

load_dotenv()

conn = psycopg.connect(os.environ["DATABASE_URL"])
with conn.cursor() as cur:
    cur.execute("select current_database(), current_user;")
    print(cur.fetchone())
conn.close()