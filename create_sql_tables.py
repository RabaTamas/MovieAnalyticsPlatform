import os
from dotenv import load_dotenv
import pyodbc

load_dotenv()

print("=" * 70)
print("🗄️  Create SQL Database Tables - Star Schema")
print("=" * 70)

# Connection
server = os.getenv('AZURE_SQL_SERVER')
database = os.getenv('AZURE_SQL_DATABASE')
username = os.getenv('AZURE_SQL_USERNAME')
password = os.getenv('AZURE_SQL_PASSWORD')

conn_string = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'

print(f"\n⏳ Connecting to: {server}/{database}")
conn = pyodbc.connect(conn_string, timeout=30)
cursor = conn.cursor()
print("✅ Connected!")

# =============================================================================
# STAGING TABLES
# =============================================================================
print("\n" + "=" * 70)
print("📥 Creating STAGING Tables")
print("=" * 70)

staging_tables = [
    # Staging_Movies - Raw data from CSV/API
    """
    CREATE TABLE Staging_Movies (
        staging_id INT IDENTITY(1,1) PRIMARY KEY,
        movie_id INT,
        title NVARCHAR(500),
        genres NVARCHAR(500),
        original_language NVARCHAR(10),
        overview NVARCHAR(MAX),
        popularity FLOAT,
        production_companies NVARCHAR(MAX),
        release_date DATE,
        budget FLOAT,
        revenue FLOAT,
        runtime FLOAT,
        vote_average FLOAT,
        vote_count FLOAT,
        profit FLOAT,
        roi FLOAT,
        release_year INT,
        release_month INT,
        load_date DATETIME DEFAULT GETDATE(),
        source NVARCHAR(50)
    );
    """,
]

for i, sql in enumerate(staging_tables, 1):
    table_name = sql.split("TABLE")[1].split("(")[0].strip()
    try:
        # Drop if exists
        cursor.execute(f"IF OBJECT_ID('{table_name}', 'U') IS NOT NULL DROP TABLE {table_name};")
        # Create table
        cursor.execute(sql)
        conn.commit()
        print(f"   ✅ Created: {table_name}")
    except Exception as e:
        print(f"   ❌ Error creating {table_name}: {e}")

# =============================================================================
# DIMENSION TABLES (Star Schema)
# =============================================================================
print("\n" + "=" * 70)
print("⭐ Creating DIMENSION Tables (Star Schema)")
print("=" * 70)

dimension_tables = [
    # Dim_Genre
    """
    CREATE TABLE Dim_Genre (
        genre_id INT IDENTITY(1,1) PRIMARY KEY,
        genre_name NVARCHAR(100) NOT NULL UNIQUE,
        created_date DATETIME DEFAULT GETDATE()
    );
    """,
    
    # Dim_Time
    """
    CREATE TABLE Dim_Time (
        time_id INT IDENTITY(1,1) PRIMARY KEY,
        full_date DATE NOT NULL UNIQUE,
        year INT NOT NULL,
        quarter INT NOT NULL,
        month INT NOT NULL,
        month_name NVARCHAR(20),
        day_of_month INT,
        day_of_week INT,
        day_name NVARCHAR(20),
        is_weekend BIT,
        created_date DATETIME DEFAULT GETDATE()
    );
    """,
    
    # Dim_Country
    """
    CREATE TABLE Dim_Country (
        country_id INT IDENTITY(1,1) PRIMARY KEY,
        country_code NVARCHAR(10),
        country_name NVARCHAR(100) NOT NULL UNIQUE,
        region NVARCHAR(100),
        created_date DATETIME DEFAULT GETDATE()
    );
    """,
    
    # Dim_Studio
    """
    CREATE TABLE Dim_Studio (
        studio_id INT IDENTITY(1,1) PRIMARY KEY,
        studio_name NVARCHAR(500) NOT NULL UNIQUE,
        studio_size NVARCHAR(20),
        created_date DATETIME DEFAULT GETDATE()
    );
    """,
]

for sql in dimension_tables:
    table_name = sql.split("TABLE")[1].split("(")[0].strip()
    try:
        cursor.execute(f"IF OBJECT_ID('{table_name}', 'U') IS NOT NULL DROP TABLE {table_name};")
        cursor.execute(sql)
        conn.commit()
        print(f"   ✅ Created: {table_name}")
    except Exception as e:
        print(f"   ❌ Error creating {table_name}: {e}")

# =============================================================================
# FACT TABLE (Star Schema)
# =============================================================================
print("\n" + "=" * 70)
print("🌟 Creating FACT Table")
print("=" * 70)

fact_table = """
CREATE TABLE Fact_Movies (
    fact_id INT IDENTITY(1,1) PRIMARY KEY,
    movie_id INT NOT NULL,
    title NVARCHAR(500),
    genre_id INT,
    time_id INT,
    country_id INT,
    studio_id INT,
    budget FLOAT,
    revenue FLOAT,
    profit FLOAT,
    roi FLOAT,
    runtime FLOAT,
    vote_average FLOAT,
    vote_count FLOAT,
    popularity FLOAT,
    original_language NVARCHAR(10),
    created_date DATETIME DEFAULT GETDATE(),
    
    FOREIGN KEY (genre_id) REFERENCES Dim_Genre(genre_id),
    FOREIGN KEY (time_id) REFERENCES Dim_Time(time_id),
    FOREIGN KEY (country_id) REFERENCES Dim_Country(country_id),
    FOREIGN KEY (studio_id) REFERENCES Dim_Studio(studio_id)
);
"""

try:
    cursor.execute("IF OBJECT_ID('Fact_Movies', 'U') IS NOT NULL DROP TABLE Fact_Movies;")
    cursor.execute(fact_table)
    conn.commit()
    print("   ✅ Created: Fact_Movies")
except Exception as e:
    print(f"   ❌ Error creating Fact_Movies: {e}")

# =============================================================================
# AGGREGATED TABLES (for Power BI performance)
# =============================================================================
print("\n" + "=" * 70)
print("📊 Creating AGGREGATED Tables")
print("=" * 70)

agg_tables = [
    # Agg_Genre_Performance
    """
    CREATE TABLE Agg_Genre_Performance (
        agg_id INT IDENTITY(1,1) PRIMARY KEY,
        genre_id INT,
        genre_name NVARCHAR(100),
        total_films INT,
        total_revenue FLOAT,
        total_budget FLOAT,
        avg_revenue FLOAT,
        avg_budget FLOAT,
        avg_roi FLOAT,
        avg_rating FLOAT,
        last_updated DATETIME DEFAULT GETDATE(),
        
        FOREIGN KEY (genre_id) REFERENCES Dim_Genre(genre_id)
    );
    """,
    
    # Agg_Yearly_Trends
    """
    CREATE TABLE Agg_Yearly_Trends (
        agg_id INT IDENTITY(1,1) PRIMARY KEY,
        year INT NOT NULL,
        total_films INT,
        total_revenue FLOAT,
        total_budget FLOAT,
        avg_revenue FLOAT,
        avg_budget FLOAT,
        avg_roi FLOAT,
        avg_rating FLOAT,
        last_updated DATETIME DEFAULT GETDATE()
    );
    """,
]

for sql in agg_tables:
    table_name = sql.split("TABLE")[1].split("(")[0].strip()
    try:
        cursor.execute(f"IF OBJECT_ID('{table_name}', 'U') IS NOT NULL DROP TABLE {table_name};")
        cursor.execute(sql)
        conn.commit()
        print(f"   ✅ Created: {table_name}")
    except Exception as e:
        print(f"   ❌ Error creating {table_name}: {e}")

# =============================================================================
# ETL LOG TABLE
# =============================================================================
print("\n" + "=" * 70)
print("📝 Creating ETL LOG Table")
print("=" * 70)

etl_log_table = """
CREATE TABLE ETL_Log (
    log_id INT IDENTITY(1,1) PRIMARY KEY,
    job_name NVARCHAR(200),
    start_time DATETIME,
    end_time DATETIME,
    rows_processed INT,
    rows_failed INT,
    status NVARCHAR(50),
    error_message NVARCHAR(MAX),
    created_date DATETIME DEFAULT GETDATE()
);
"""

try:
    cursor.execute("IF OBJECT_ID('ETL_Log', 'U') IS NOT NULL DROP TABLE ETL_Log;")
    cursor.execute(etl_log_table)
    conn.commit()
    print("   ✅ Created: ETL_Log")
except Exception as e:
    print(f"   ❌ Error creating ETL_Log: {e}")

# =============================================================================
# SUMMARY
# =============================================================================
print("\n" + "=" * 70)
print("📋 Database Schema Summary")
print("=" * 70)

cursor.execute("""
    SELECT 
        TABLE_NAME,
        TABLE_TYPE
    FROM INFORMATION_SCHEMA.TABLES
    WHERE TABLE_TYPE = 'BASE TABLE'
    ORDER BY TABLE_NAME
""")

tables = cursor.fetchall()

print(f"\n✅ Total tables created: {len(tables)}\n")

for table in tables:
    print(f"   📄 {table[0]}")

cursor.close()
conn.close()

print("\n" + "=" * 70)
print("✅ Database schema created successfully!")
print("=" * 70)