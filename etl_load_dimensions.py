import os
from dotenv import load_dotenv
import pyodbc
from datetime import datetime, timedelta

load_dotenv()

print("=" * 70)
print("⭐ ETL Job 2: Load Dimension Tables")
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

job_name = "Load_Dimensions"
start_time = datetime.now()
total_rows_processed = 0

print(f"\n🕐 Job started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

# =============================================================================
# 1. DIM_GENRE
# =============================================================================
print("\n" + "=" * 70)
print("🎭 Loading Dim_Genre")
print("=" * 70)

try:
    # Extract distinct genres from Staging (genres are separated by '-')
    cursor.execute("""
        SELECT DISTINCT TRIM(value) as genre_name
        FROM Staging_Movies
        CROSS APPLY STRING_SPLIT(genres, '-')
        WHERE TRIM(value) != ''
        ORDER BY genre_name
    """)
    
    genres = [row.genre_name for row in cursor.fetchall()]
    print(f"   Found {len(genres)} unique genres")
    
    # Clear existing data
    cursor.execute("DELETE FROM Dim_Genre")
    conn.commit()
    
    # Insert genres
    for genre in genres:
        cursor.execute("""
            INSERT INTO Dim_Genre (genre_name)
            VALUES (?)
        """, (genre,))
    
    conn.commit()
    total_rows_processed += len(genres)
    
    print(f"   ✅ Inserted {len(genres)} genres")
    print(f"   📋 Sample genres: {', '.join(genres[:10])}")
    
except Exception as e:
    print(f"   ❌ Error loading Dim_Genre: {e}")

# =============================================================================
# 2. DIM_TIME
# =============================================================================
print("\n" + "=" * 70)
print("📅 Loading Dim_Time")
print("=" * 70)

try:
    # Get min and max dates from Staging
    cursor.execute("""
        SELECT MIN(release_date) as min_date, MAX(release_date) as max_date
        FROM Staging_Movies
        WHERE release_date IS NOT NULL
    """)
    
    result = cursor.fetchone()
    min_date = result.min_date
    max_date = result.max_date
    
    print(f"   Date range: {min_date} to {max_date}")
    
    # Clear existing data
    cursor.execute("DELETE FROM Dim_Time")
    conn.commit()
    
    # Generate dates
    current_date = min_date
    dates_inserted = 0
    
    while current_date <= max_date:
        # Calculate date attributes
        year = current_date.year
        quarter = (current_date.month - 1) // 3 + 1
        month = current_date.month
        month_names = ['', 'January', 'February', 'March', 'April', 'May', 'June',
                      'July', 'August', 'September', 'October', 'November', 'December']
        month_name = month_names[month]
        day_of_month = current_date.day
        day_of_week = current_date.weekday() + 1  # Monday = 1
        day_names = ['', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_name = day_names[day_of_week] if day_of_week <= 7 else day_names[current_date.weekday() + 1]
        is_weekend = 1 if day_of_week in [6, 7] else 0
        
        cursor.execute("""
            INSERT INTO Dim_Time (full_date, year, quarter, month, month_name, day_of_month, day_of_week, day_name, is_weekend)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (current_date, year, quarter, month, month_name, day_of_month, day_of_week, day_name, is_weekend))
        
        dates_inserted += 1
        current_date += timedelta(days=1)
        
        # Commit in batches
        if dates_inserted % 1000 == 0:
            conn.commit()
            print(f"   📊 Processed {dates_inserted} dates...")
    
    conn.commit()
    total_rows_processed += dates_inserted
    
    print(f"   ✅ Inserted {dates_inserted} date records")
    
except Exception as e:
    print(f"   ❌ Error loading Dim_Time: {e}")

# =============================================================================
# 3. DIM_COUNTRY
# =============================================================================
print("\n" + "=" * 70)
print("🌍 Loading Dim_Country")
print("=" * 70)

try:
    # Extract distinct countries from Staging (production_companies often contain country info)
    # For simplicity, we'll use language as a proxy and add "Unknown"
    cursor.execute("""
        SELECT DISTINCT original_language
        FROM Staging_Movies
        WHERE original_language IS NOT NULL
        ORDER BY original_language
    """)
    
    languages = [row.original_language for row in cursor.fetchall()]
    
    # Create country mappings (simplified - language code to country)
    country_mappings = {
        'en': ('US', 'United States', 'North America'),
        'fr': ('FR', 'France', 'Europe'),
        'es': ('ES', 'Spain', 'Europe'),
        'de': ('DE', 'Germany', 'Europe'),
        'it': ('IT', 'Italy', 'Europe'),
        'ja': ('JP', 'Japan', 'Asia'),
        'ko': ('KR', 'South Korea', 'Asia'),
        'zh': ('CN', 'China', 'Asia'),
        'hi': ('IN', 'India', 'Asia'),
        'pt': ('PT', 'Portugal', 'Europe'),
        'ru': ('RU', 'Russia', 'Europe'),
        'ar': ('SA', 'Saudi Arabia', 'Middle East'),
    }
    
    # Clear existing data
    cursor.execute("DELETE FROM Dim_Country")
    conn.commit()
    
    # Insert Unknown first
    cursor.execute("""
        INSERT INTO Dim_Country (country_code, country_name, region)
        VALUES (?, ?, ?)
    """, ('UNK', 'Unknown', 'Unknown'))
    
    countries_inserted = 1
    
    # Insert countries based on language codes
    for lang in languages:
        if lang in country_mappings:
            code, name, region = country_mappings[lang]
            cursor.execute("""
                IF NOT EXISTS (SELECT 1 FROM Dim_Country WHERE country_code = ?)
                INSERT INTO Dim_Country (country_code, country_name, region)
                VALUES (?, ?, ?)
            """, (code, code, name, region))
            countries_inserted += 1
        else:
            # Unknown language - use language code as country
            cursor.execute("""
                IF NOT EXISTS (SELECT 1 FROM Dim_Country WHERE country_code = ?)
                INSERT INTO Dim_Country (country_code, country_name, region)
                VALUES (?, ?, ?)
            """, (lang.upper(), lang.upper(), f'Language: {lang}', 'Other'))
            countries_inserted += 1
    
    conn.commit()
    total_rows_processed += countries_inserted
    
    print(f"   ✅ Inserted {countries_inserted} countries")
    
except Exception as e:
    print(f"   ❌ Error loading Dim_Country: {e}")

# =============================================================================
# 4. DIM_STUDIO
# =============================================================================
print("\n" + "=" * 70)
print("🎬 Loading Dim_Studio")
print("=" * 70)

try:
    # Extract distinct studios from Staging (studios are separated by '-')
    cursor.execute("""
        SELECT DISTINCT TRIM(value) as studio_name
        FROM Staging_Movies
        CROSS APPLY STRING_SPLIT(production_companies, '-')
        WHERE TRIM(value) != '' AND TRIM(value) != 'Unknown'
    """)
    
    studios = [row.studio_name for row in cursor.fetchall()]
    print(f"   Found {len(studios)} unique studios")
    
    # Clear existing data
    cursor.execute("DELETE FROM Dim_Studio")
    conn.commit()
    
    # Insert Unknown first
    cursor.execute("""
        INSERT INTO Dim_Studio (studio_name, studio_size)
        VALUES (?, ?)
    """, ('Unknown', 'Unknown'))
    
    studios_inserted = 1
    
    # Insert studios (simplified studio size logic)
    major_studios = ['Warner Bros', 'Universal', 'Paramount', 'Disney', '20th Century', 
                     'Sony', 'Columbia', 'Fox', 'Metro-Goldwyn-Mayer', 'Lionsgate']
    
    for studio in studios:
        # Determine studio size
        if any(major in studio for major in major_studios):
            size = 'Large'
        elif len(studio) > 30:
            size = 'Medium'
        else:
            size = 'Small'
        
        cursor.execute("""
            INSERT INTO Dim_Studio (studio_name, studio_size)
            VALUES (?, ?)
        """, (studio, size))
        studios_inserted += 1
        
        # Commit in batches
        if studios_inserted % 500 == 0:
            conn.commit()
            print(f"   📊 Processed {studios_inserted} studios...")
    
    conn.commit()
    total_rows_processed += studios_inserted
    
    print(f"   ✅ Inserted {studios_inserted} studios")
    
except Exception as e:
    print(f"   ❌ Error loading Dim_Studio: {e}")

# =============================================================================
# VERIFICATION
# =============================================================================
print("\n" + "=" * 70)
print("✅ Verification")
print("=" * 70)

dimension_counts = {
    'Dim_Genre': 0,
    'Dim_Time': 0,
    'Dim_Country': 0,
    'Dim_Studio': 0
}

for table in dimension_counts.keys():
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    dimension_counts[table] = cursor.fetchone()[0]
    print(f"   📊 {table}: {dimension_counts[table]:,} records")

# =============================================================================
# ETL JOB COMPLETION
# =============================================================================
end_time = datetime.now()
duration = (end_time - start_time).total_seconds()
status = "SUCCESS"

print(f"\n🕐 Job finished at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"⏱️  Duration: {duration:.2f} seconds")
print(f"📊 Total records inserted: {total_rows_processed:,}")

# Log to ETL_Log
log_etl_job(cursor, conn, job_name, start_time, end_time, total_rows_processed, 0, status, '')

cursor.close()
conn.close()

print("\n" + "=" * 70)
print(f"✅ ETL Job 2 completed - Status: {status}")
print("=" * 70)