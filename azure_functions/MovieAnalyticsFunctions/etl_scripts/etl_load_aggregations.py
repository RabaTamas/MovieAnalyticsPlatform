import os
from dotenv import load_dotenv
import pyodbc
from datetime import datetime

load_dotenv()

print("=" * 70)
print("ETL Job 4: Load Aggregation Tables")
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

job_name = "Load_Aggregations"
start_time = datetime.now()
total_rows_processed = 0

print(f"\nJob started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

# =============================================================================
# 1. AGG_GENRE_PERFORMANCE
# =============================================================================
print("\n" + "=" * 70)
print("Loading Agg_Genre_Performance")
print("=" * 70)

try:
    # Clear existing data
    cursor.execute("DELETE FROM Agg_Genre_Performance")
    conn.commit()
    
    # Insert aggregated data
    agg_genre_query = """
    INSERT INTO Agg_Genre_Performance (
        genre_id, genre_name, total_films, total_revenue, total_budget,
        avg_revenue, avg_budget, avg_roi, avg_rating
    )
    SELECT 
        g.genre_id,
        g.genre_name,
        COUNT(DISTINCT f.movie_id) as total_films,
        SUM(f.revenue) as total_revenue,
        SUM(f.budget) as total_budget,
        AVG(f.revenue) as avg_revenue,
        AVG(f.budget) as avg_budget,
        AVG(f.roi) as avg_roi,
        AVG(f.vote_average) as avg_rating
    FROM Fact_Movies f
    INNER JOIN Dim_Genre g ON f.genre_id = g.genre_id
    GROUP BY g.genre_id, g.genre_name
    """
    
    cursor.execute(agg_genre_query)
    rows_affected = cursor.rowcount
    conn.commit()
    
    total_rows_processed += rows_affected
    
    print(f"Inserted {rows_affected} genre aggregations")
    
    # Show top genres by total revenue
    cursor.execute("""
        SELECT TOP 5 
            genre_name, 
            total_films, 
            total_revenue / 1000000000.0 as revenue_billions,
            avg_roi
        FROM Agg_Genre_Performance
        ORDER BY total_revenue DESC
    """)
    
    print(f"\nTop 5 genres by total revenue:")
    for row in cursor.fetchall():
        print(f"      {row.genre_name:<20} | {row.total_films:>5} films | ${row.revenue_billions:>6.2f}B | Avg ROI: {row.avg_roi:>6.2f}")
    
except Exception as e:
    print(f"Error loading Agg_Genre_Performance: {e}")

# =============================================================================
# 2. AGG_YEARLY_TRENDS
# =============================================================================
print("\n" + "=" * 70)
print("Loading Agg_Yearly_Trends")
print("=" * 70)

try:
    # Clear existing data
    cursor.execute("DELETE FROM Agg_Yearly_Trends")
    conn.commit()
    
    # Insert aggregated data
    agg_yearly_query = """
    INSERT INTO Agg_Yearly_Trends (
        year, total_films, total_revenue, total_budget,
        avg_revenue, avg_budget, avg_roi, avg_rating
    )
    SELECT 
        t.year,
        COUNT(DISTINCT f.movie_id) as total_films,
        SUM(f.revenue) as total_revenue,
        SUM(f.budget) as total_budget,
        AVG(f.revenue) as avg_revenue,
        AVG(f.budget) as avg_budget,
        AVG(f.roi) as avg_roi,
        AVG(f.vote_average) as avg_rating
    FROM Fact_Movies f
    INNER JOIN Dim_Time t ON f.time_id = t.time_id
    GROUP BY t.year
    """
    
    cursor.execute(agg_yearly_query)
    rows_affected = cursor.rowcount
    conn.commit()
    
    total_rows_processed += rows_affected
    
    print(f"Inserted {rows_affected} yearly aggregations")
    
    # Show recent years
    cursor.execute("""
        SELECT TOP 10 
            year, 
            total_films, 
            total_revenue / 1000000000.0 as revenue_billions,
            avg_budget / 1000000.0 as avg_budget_millions
        FROM Agg_Yearly_Trends
        ORDER BY year DESC
    """)
    
    print(f"\nRecent 10 years:")
    for row in cursor.fetchall():
        print(f"      {row.year} | {row.total_films:>4} films | ${row.revenue_billions:>6.2f}B total | Avg budget: ${row.avg_budget_millions:>5.1f}M")
    
except Exception as e:
    print(f"Error loading Agg_Yearly_Trends: {e}")

# =============================================================================
# VERIFICATION
# =============================================================================
print("\n" + "=" * 70)
print("Verification")
print("=" * 70)

cursor.execute("SELECT COUNT(*) FROM Agg_Genre_Performance")
genre_agg_count = cursor.fetchone()[0]
print(f"Agg_Genre_Performance: {genre_agg_count} records")

cursor.execute("SELECT COUNT(*) FROM Agg_Yearly_Trends")
yearly_agg_count = cursor.fetchone()[0]
print(f"Agg_Yearly_Trends: {yearly_agg_count} records")

# =============================================================================
# ETL JOB COMPLETION
# =============================================================================
end_time = datetime.now()
duration = (end_time - start_time).total_seconds()
status = "SUCCESS"

print(f"\nJob finished at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Duration: {duration:.2f} seconds")
print(f"Total aggregation records: {total_rows_processed}")

# Log to ETL_Log
log_etl_job(cursor, conn, job_name, start_time, end_time, total_rows_processed, 0, status, '')

cursor.close()
conn.close()

print("\n" + "=" * 70)
print("ETL Job 4 completed - Status: {status}")
print("=" * 70)