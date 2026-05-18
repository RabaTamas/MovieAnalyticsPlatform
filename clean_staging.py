import os
from dotenv import load_dotenv
import pyodbc

load_dotenv()

server   = os.getenv('AZURE_SQL_SERVER')
database = os.getenv('AZURE_SQL_DATABASE')
username = os.getenv('AZURE_SQL_USERNAME')
password = os.getenv('AZURE_SQL_PASSWORD')

conn_string = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'
conn   = pyodbc.connect(conn_string, timeout=30)
cursor = conn.cursor()

# Delete old records (non-chunk sources)
cursor.execute("DELETE FROM Staging_Movies WHERE source NOT LIKE 'CSV_chunk_%'")
deleted = cursor.rowcount
conn.commit()

# Verify
cursor.execute("SELECT COUNT(*) FROM Staging_Movies")
total = cursor.fetchone()[0]
cursor.execute("SELECT source, COUNT(*) FROM Staging_Movies GROUP BY source")
rows = cursor.fetchall()

print(f"Deleted: {deleted} rows")
print(f"Remaining total: {total} rows")
for row in rows:
    print(f"  {row[0]}: {row[1]} rows")

cursor.close()
conn.close()