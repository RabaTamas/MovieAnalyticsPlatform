import os
import sys
from dotenv import load_dotenv
import pyodbc
import pandas as pd
from datetime import datetime

load_dotenv()

if len(sys.argv) < 2:
    print("❌ Használat: py etl_csv_chunk_to_staging.py <chunk_id>")
    print("   chunk_id: 1, 2, 3 vagy 4")
    sys.exit(1)

chunk_id = int(sys.argv[1])
if chunk_id not in [1, 2, 3, 4]:
    print(f"❌ Érvénytelen chunk_id: {chunk_id}. Csak 1-4 lehet.")
    sys.exit(1)

csv_path = f'data/chunks/movies_chunk_{chunk_id}.csv'

print("=" * 70)
print(f"📥 ETL: CSV Chunk {chunk_id}/4 → Staging Table")
print("=" * 70)

# ── ETL LOGGING ──────────────────────────────────────────────────────────────
def log_etl_job(cursor, conn, job_name, start_time, end_time, rows_processed, rows_failed, status, error_message=''):
    try:
        cursor.execute("""
            INSERT INTO ETL_Log (job_name, start_time, end_time, rows_processed, rows_failed, status, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (job_name, start_time, end_time, rows_processed, rows_failed, status, error_message))
        conn.commit()
    except Exception as e:
        print(f"⚠️ Warning: Could not log to ETL_Log: {e}")

# ── DATABASE CONNECTION ───────────────────────────────────────────────────────
server   = os.getenv('AZURE_SQL_SERVER')
database = os.getenv('AZURE_SQL_DATABASE')
username = os.getenv('AZURE_SQL_USERNAME')
password = os.getenv('AZURE_SQL_PASSWORD')

conn_string = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'
print(f"\n⏳ Connecting to: {server}/{database}")
conn   = pyodbc.connect(conn_string, timeout=30)
cursor = conn.cursor()
print("✅ Connected!")

job_name   = f"CSV_Chunk_{chunk_id}_to_Staging"
start_time = datetime.now()
print(f"🕐 Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

# ── LOAD CSV CHUNK ────────────────────────────────────────────────────────────
print(f"\n📂 Loading: {csv_path}")
try:
    df = pd.read_csv(csv_path)
    print(f"✅ Loaded {len(df):,} rows from chunk_{chunk_id}")
except Exception as e:
    print(f"❌ Error loading CSV: {e}")
    log_etl_job(cursor, conn, job_name, start_time, datetime.now(), 0, 0, 'FAILED', str(e))
    cursor.close(); conn.close(); sys.exit(1)

# ── CHECK: már be lett-e töltve ez a chunk? ───────────────────────────────────
cursor.execute("SELECT COUNT(*) FROM Staging_Movies WHERE source = ?", (f'CSV_chunk_{chunk_id}',))
already_loaded = cursor.fetchone()[0]
if already_loaded > 0:
    print(f"\n⚠️ Chunk {chunk_id} már be van töltve ({already_loaded:,} sor). Kihagyva (idempotens).")
    log_etl_job(cursor, conn, job_name, start_time, datetime.now(), 0, 0, 'SKIPPED', f'Chunk {chunk_id} already loaded')
    cursor.close(); conn.close()
    sys.exit(0)

# ── DATA PREPARATION ──────────────────────────────────────────────────────────
df['release_date'] = pd.to_datetime(df['release_date'], errors='coerce')
df = df.fillna({
    'genres': 'Unknown',
    'original_language': 'en',
    'overview': '',
    'production_companies': 'Unknown',
    'popularity': 0,
    'runtime': 0,
    'vote_average': 0,
    'vote_count': 0
})
print(f"✅ Data prepared: {len(df):,} rows")

# ── INSERT INTO STAGING ───────────────────────────────────────────────────────
print(f"\n📥 Inserting chunk_{chunk_id} into Staging_Movies...")

insert_query = """
    INSERT INTO Staging_Movies (
        movie_id, title, genres, original_language, overview, popularity,
        production_companies, release_date, budget, revenue, runtime,
        vote_average, vote_count, profit, roi, release_year, release_month, source
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

batch_size = 500
successful_inserts = 0
failed_inserts = 0
total_rows = len(df)

for i in range(0, total_rows, batch_size):
    batch = df.iloc[i:i+batch_size]
    batch_num = (i // batch_size) + 1
    total_batches = (total_rows // batch_size) + 1
    try:
        for _, row in batch.iterrows():
            cursor.execute(insert_query, (
                int(row['id']),
                row['title'],
                row['genres'],
                row['original_language'],
                row['overview'],
                float(row['popularity']) if pd.notna(row['popularity']) else 0,
                row['production_companies'],
                row['release_date'],
                float(row['budget']),
                float(row['revenue']),
                float(row['runtime']) if pd.notna(row['runtime']) else 0,
                float(row['vote_average']),
                float(row['vote_count']),
                float(row['profit']),
                float(row['roi']),
                int(row['release_year']),
                int(row['release_month']),
                f'CSV_chunk_{chunk_id}'   # ← source mezőbe kerül a chunk azonosító
            ))
        conn.commit()
        successful_inserts += len(batch)
        progress = (i + len(batch)) / total_rows * 100
        print(f"  📊 Batch {batch_num}/{total_batches} – {progress:.0f}% ({successful_inserts:,}/{total_rows:,})")
    except Exception as e:
        failed_inserts += len(batch)
        print(f"  ❌ Batch {batch_num} error: {e}")
        conn.rollback()

# ── VERIFY ────────────────────────────────────────────────────────────────────
cursor.execute("SELECT COUNT(*) FROM Staging_Movies")
total_staging = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM Staging_Movies WHERE source = ?", (f'CSV_chunk_{chunk_id}',))
this_chunk = cursor.fetchone()[0]

print(f"\n✅ Staging_Movies összesen: {total_staging:,} sor")
print(f"✅ Ebből chunk_{chunk_id}: {this_chunk:,} sor")

# ── LOG & CLOSE ───────────────────────────────────────────────────────────────
end_time = datetime.now()
duration = (end_time - start_time).total_seconds()
status   = "SUCCESS" if failed_inserts == 0 else "PARTIAL_SUCCESS"

log_etl_job(cursor, conn, job_name, start_time, end_time, successful_inserts, failed_inserts, status)
cursor.close()
conn.close()

print(f"\n⏱️ Duration: {duration:.1f}s – Status: {status}")
print("=" * 70)
print(f"✅ ETL Chunk {chunk_id}/4 completed!")
print("=" * 70)