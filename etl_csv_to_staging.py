import os
from dotenv import load_dotenv
import pyodbc
import pandas as pd
from datetime import datetime

load_dotenv()

print("=" * 70)
print("📥 ETL Job 1: CSV → Staging Table")
print("=" * 70)

# =============================================================================
# ETL LOGGING
# =============================================================================
def log_etl_job(cursor, conn, job_name, start_time, end_time, rows_processed, rows_failed, status, error_message=''):
    """Log ETL job execution to ETL_Log table"""
    try:
        cursor.execute("""
            INSERT INTO ETL_Log (job_name, start_time, end_time, rows_processed, rows_failed, status, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (job_name, start_time, end_time, rows_processed, rows_failed, status, error_message))
        conn.commit()
    except Exception as e:
        print(f"   ⚠️  Warning: Could not log to ETL_Log: {e}")

# =============================================================================
# DATABASE CONNECTION
# =============================================================================
server = os.getenv('AZURE_SQL_SERVER')
database = os.getenv('AZURE_SQL_DATABASE')
username = os.getenv('AZURE_SQL_USERNAME')
password = os.getenv('AZURE_SQL_PASSWORD')

conn_string = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'

print(f"\n⏳ Connecting to: {server}/{database}")
conn = pyodbc.connect(conn_string, timeout=30)
cursor = conn.cursor()
print("✅ Connected!")

# Start ETL job
job_name = "CSV_to_Staging"
start_time = datetime.now()
rows_processed = 0
rows_failed = 0
status = "RUNNING"

print(f"\n🕐 Job started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

# =============================================================================
# LOAD CSV DATA
# =============================================================================
print("\n" + "=" * 70)
print("📂 Loading cleaned CSV")
print("=" * 70)

csv_path = 'data/processed/movies_cleaned.csv'

try:
    df = pd.read_csv(csv_path)
    print(f"✅ Loaded {len(df):,} rows from CSV")
    print(f"📋 Columns: {list(df.columns)}")
except Exception as e:
    print(f"❌ Error loading CSV: {e}")
    end_time = datetime.now()
    log_etl_job(cursor, conn, job_name, start_time, end_time, 0, 0, 'FAILED', str(e))
    cursor.close()
    conn.close()
    exit()

# =============================================================================
# DATA PREPARATION
# =============================================================================
print("\n" + "=" * 70)
print("🔧 Preparing data for insert")
print("=" * 70)

# Convert date to proper format
df['release_date'] = pd.to_datetime(df['release_date'])

# Fill NaN values
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

print(f"✅ Data prepared: {len(df)} rows ready")

# =============================================================================
# TRUNCATE STAGING TABLE
# =============================================================================
print("\n" + "=" * 70)
print("🗑️  Clearing Staging Table")
print("=" * 70)

try:
    cursor.execute("TRUNCATE TABLE Staging_Movies")
    conn.commit()
    print("✅ Staging_Movies truncated")
except Exception as e:
    print(f"❌ Error truncating: {e}")

# =============================================================================
# INSERT DATA INTO STAGING
# =============================================================================
print("\n" + "=" * 70)
print("📥 Inserting data into Staging_Movies")
print("=" * 70)

insert_query = """
INSERT INTO Staging_Movies (
    movie_id, title, genres, original_language, overview, popularity,
    production_companies, release_date, budget, revenue, runtime,
    vote_average, vote_count, profit, roi, release_year, release_month, source
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

batch_size = 1000
total_rows = len(df)
successful_inserts = 0
failed_inserts = 0

print(f"⏳ Inserting {total_rows:,} rows in batches of {batch_size}...")

for i in range(0, total_rows, batch_size):
    batch = df.iloc[i:i+batch_size]
    batch_num = (i // batch_size) + 1
    total_batches = (total_rows // batch_size) + 1
    
    try:
        for idx, row in batch.iterrows():
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
                'CSV'
            ))
        
        conn.commit()
        successful_inserts += len(batch)
        
        # Progress update
        progress = (i + len(batch)) / total_rows * 100
        print(f"   📊 Batch {batch_num}/{total_batches} - Progress: {progress:.1f}% ({successful_inserts:,}/{total_rows:,} rows)")
        
    except Exception as e:
        failed_inserts += len(batch)
        print(f"   ❌ Error in batch {batch_num}: {e}")
        conn.rollback()

rows_processed = successful_inserts
rows_failed = failed_inserts

print(f"\n✅ Insert completed!")
print(f"   Successful: {successful_inserts:,}")
print(f"   Failed: {failed_inserts:,}")

# =============================================================================
# VERIFY DATA
# =============================================================================
print("\n" + "=" * 70)
print("✅ Verification")
print("=" * 70)

cursor.execute("SELECT COUNT(*) FROM Staging_Movies")
staging_count = cursor.fetchone()[0]
print(f"   Rows in Staging_Movies: {staging_count:,}")

cursor.execute("""
    SELECT TOP 5 
        movie_id, title, release_date, budget, revenue, roi
    FROM Staging_Movies
    ORDER BY revenue DESC
""")

print(f"\n   📊 Top 5 movies by revenue:")
for row in cursor.fetchall():
    print(f"      {row.title[:40]:40s} | ${row.revenue/1e9:.2f}B | ROI: {row.roi:.2f}")

# =============================================================================
# ETL JOB COMPLETION
# =============================================================================
end_time = datetime.now()
duration = (end_time - start_time).total_seconds()
status = "SUCCESS" if failed_inserts == 0 else "PARTIAL_SUCCESS"

print(f"\n🕐 Job finished at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"⏱️  Duration: {duration:.2f} seconds")

# Log to ETL_Log
log_etl_job(cursor, conn, job_name, start_time, end_time, rows_processed, rows_failed, status, '')

cursor.close()
conn.close()

print("\n" + "=" * 70)
print(f"✅ ETL Job 1 completed - Status: {status}")
print("=" * 70)