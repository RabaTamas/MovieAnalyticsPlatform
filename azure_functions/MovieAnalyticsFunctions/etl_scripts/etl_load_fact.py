import os
from dotenv import load_dotenv
import pyodbc
from datetime import datetime

load_dotenv()

print("=" * 70)
print("ETL Job 3: Load Fact Table")
print("=" * 70)

# =============================================================================
# ETL LOGGING
# =============================================================================
def log_etl_job(cursor, conn, job_name, start_time, end_time, rows_processed, rows_failed, status, error_message=''):
    try:
        cursor.execute("""
            INSERT INTO ETL_Log (job_name, start_time, end_time, rows_processed, rows_failed, status, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (job_name, start_time, end_time, rows_processed, rows_failed, status, error_message))
        conn.commit()
    except Exception as e:
        print(f"Warning: Could not log to ETL_Log: {e}")

# =============================================================================
# DATABASE CONNECTION
# =============================================================================
server = os.getenv('AZURE_SQL_SERVER')
database = os.getenv('AZURE_SQL_DATABASE')
username = os.getenv('AZURE_SQL_USERNAME')
password = os.getenv('AZURE_SQL_PASSWORD')

conn_string = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'

print(f"\nConnecting to: {server}/{database}")
conn = pyodbc.connect(conn_string, timeout=30)
cursor = conn.cursor()
print("Connected!")

job_name = "Load_Fact_Movies"
start_time = datetime.now()
rows_processed = 0
rows_failed = 0

print(f"\nJob started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

# =============================================================================
# CLEAR FACT TABLE
# =============================================================================
print("\n" + "=" * 70)
print("Clearing Fact_Movies table")
print("=" * 70)

try:
    cursor.execute("DELETE FROM Fact_Movies")
    conn.commit()
    print("Fact_Movies cleared")
except Exception as e:
    print(f"Error clearing Fact_Movies: {e}")

# =============================================================================
# LOAD FACT TABLE FROM STAGING
# =============================================================================
print("\n" + "=" * 70)
print("Loading Fact_Movies from Staging")
print("=" * 70)

# Complex INSERT with JOINs to get foreign keys from dimension tables
insert_query = """
INSERT INTO Fact_Movies (
    movie_id, title, genre_id, time_id, country_id, studio_id,
    budget, revenue, profit, roi, runtime, vote_average, vote_count,
    popularity, original_language
)
SELECT 
    s.movie_id,
    s.title,
    -- Get genre_id for FIRST genre (movies can have multiple genres)
    (SELECT TOP 1 g.genre_id 
     FROM Dim_Genre g 
     WHERE g.genre_name = TRIM(value)
     ORDER BY g.genre_id) as genre_id,
    -- Get time_id
    t.time_id,
    -- Get country_id based on language (simplified mapping)
    ISNULL(c.country_id, 1) as country_id,  -- 1 = Unknown
    -- Get studio_id for FIRST studio
    (SELECT TOP 1 st.studio_id 
     FROM Dim_Studio st 
     WHERE st.studio_name = TRIM(studio_value)
     ORDER BY st.studio_id) as studio_id,
    -- Financial and other metrics
    s.budget,
    s.revenue,
    s.profit,
    s.roi,
    s.runtime,
    s.vote_average,
    s.vote_count,
    s.popularity,
    s.original_language
FROM Staging_Movies s
LEFT JOIN Dim_Time t ON t.full_date = s.release_date
LEFT JOIN Dim_Country c ON c.country_code = UPPER(s.original_language)
-- Split genres to get first one
CROSS APPLY STRING_SPLIT(s.genres, '-') AS genre_split
-- Split studios to get first one
CROSS APPLY (
    SELECT TOP 1 TRIM(value) as studio_value
    FROM STRING_SPLIT(s.production_companies, '-')
    WHERE TRIM(value) != '' AND TRIM(value) != 'Unknown'
) AS studio_split
WHERE 
    s.release_date IS NOT NULL
    AND s.budget > 0
    AND s.revenue > 0
"""

print("Executing INSERT with JOINs...")
print("   This will:")
print("   - Join Staging with Dim_Genre (match first genre)")
print("   - Join Staging with Dim_Time (match release date)")
print("   - Join Staging with Dim_Country (match language)")
print("   - Join Staging with Dim_Studio (match first studio)")

try:
    cursor.execute(insert_query)
    rows_affected = cursor.rowcount
    conn.commit()
    
    rows_processed = rows_affected
    
    print(f"\nFact table loaded successfully!")
    print(f"   Rows inserted: {rows_affected:,}")
    
except Exception as e:
    print(f"Error loading Fact_Movies: {e}")
    rows_failed = rows_processed
    conn.rollback()

# =============================================================================
# VERIFICATION
# =============================================================================
print("\n" + "=" * 70)
print("Verification")
print("=" * 70)

# Count records
cursor.execute("SELECT COUNT(*) FROM Fact_Movies")
fact_count = cursor.fetchone()[0]
print(f"Total records in Fact_Movies: {fact_count:,}")

# Top 10 movies by revenue
cursor.execute("""
    SELECT TOP 10
        f.title,
        g.genre_name,
        t.year,
        f.budget,
        f.revenue,
        f.profit,
        f.roi
    FROM Fact_Movies f
    LEFT JOIN Dim_Genre g ON f.genre_id = g.genre_id
    LEFT JOIN Dim_Time t ON f.time_id = t.time_id
    ORDER BY f.revenue DESC
""")

print(f"\nTop 10 movies by revenue:")
print(f"   {'Title':<40} {'Genre':<15} {'Year':<6} {'Revenue':<12} {'ROI':<8}")
print(f"   {'-'*95}")

for row in cursor.fetchall():
    title = row.title[:40] if row.title else 'Unknown'
    genre = row.genre_name if row.genre_name else 'Unknown'
    year = row.year if row.year else 0
    revenue = row.revenue / 1e9 if row.revenue else 0
    roi = row.roi if row.roi else 0
    print(f"   {title:<40} {genre:<15} {year:<6} ${revenue:>10.2f}B {roi:>7.2f}")

# Check for orphaned records (missing foreign keys)
print(f"\nData quality checks:")

cursor.execute("SELECT COUNT(*) FROM Fact_Movies WHERE genre_id IS NULL")
null_genres = cursor.fetchone()[0]
print(f"   - Movies with NULL genre_id: {null_genres}")

cursor.execute("SELECT COUNT(*) FROM Fact_Movies WHERE time_id IS NULL")
null_times = cursor.fetchone()[0]
print(f"   - Movies with NULL time_id: {null_times}")

cursor.execute("SELECT COUNT(*) FROM Fact_Movies WHERE studio_id IS NULL")
null_studios = cursor.fetchone()[0]
print(f"   - Movies with NULL studio_id: {null_studios}")

# =============================================================================
# ETL JOB COMPLETION
# =============================================================================
end_time = datetime.now()
duration = (end_time - start_time).total_seconds()
status = "SUCCESS" if rows_failed == 0 else "FAILED"

print(f"\nJob finished at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Duration: {duration:.2f} seconds ({duration/60:.2f} minutes)")

# Log to ETL_Log
log_etl_job(cursor, conn, job_name, start_time, end_time, rows_processed, rows_failed, status, '')

cursor.close()
conn.close()

print("\n" + "=" * 70)
print(f"ETL Job 3 completed - Status: {status}")
print("=" * 70)