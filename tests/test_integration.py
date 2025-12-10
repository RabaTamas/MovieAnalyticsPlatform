import pytest
import pandas as pd
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

load_dotenv()

# =============================================================================
# INTEGRATION TEST
# =============================================================================

@pytest.fixture(scope='module')
def sample_data():
    """Load 100 sample records from cleaned CSV"""
    csv_path = 'data/processed/movies_cleaned.csv'
    df = pd.read_csv(csv_path)
    
    # Take first 100 rows
    sample = df.head(100).copy()
    
    return sample


@pytest.fixture(scope='module')
def db_engine():
    """Create database engine"""
    SQL_SERVER = os.getenv('AZURE_SQL_SERVER')
    SQL_DATABASE = os.getenv('AZURE_SQL_DATABASE')
    SQL_USERNAME = os.getenv('AZURE_SQL_USERNAME')
    SQL_PASSWORD = os.getenv('AZURE_SQL_PASSWORD')
    
    connection_string = (
        f"mssql+pyodbc://{SQL_USERNAME}:{SQL_PASSWORD}@{SQL_SERVER}/"
        f"{SQL_DATABASE}?driver=ODBC+Driver+17+for+SQL+Server"
    )
    
    engine = create_engine(connection_string)
    
    # Test connection
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        pytest.skip(f"Database connection failed: {e}")
    
    return engine


def test_sample_data_loaded(sample_data):
    """Test that sample data is loaded correctly"""
    assert len(sample_data) == 100, f"Expected 100 samples, got {len(sample_data)}"


def test_sample_data_in_staging(db_engine, sample_data):
    """Test that sample movie IDs exist in Staging_Movies"""
    sample_ids = sample_data['id'].tolist()
    
    # Check how many of these IDs exist in Staging_Movies
    placeholders = ','.join(['?' for _ in sample_ids])
    query = f"SELECT COUNT(DISTINCT movie_id) FROM Staging_Movies WHERE movie_id IN ({placeholders})"
    
    with db_engine.connect() as conn:
        # Note: SQLAlchemy text() doesn't support IN with list directly, so we use string formatting
        query_safe = f"SELECT COUNT(DISTINCT movie_id) FROM Staging_Movies WHERE movie_id IN ({','.join(map(str, sample_ids))})"
        result = conn.execute(text(query_safe)).fetchone()
        found_count = result[0]
    
    # At least 80% should be in the database
    match_pct = (found_count / len(sample_ids)) * 100
    assert match_pct >= 80, f"Only {match_pct:.2f}% of sample IDs found in Staging_Movies (expected >= 80%)"


def test_sample_data_in_fact(db_engine, sample_data):
    """Test that sample movie IDs exist in Fact_Movies"""
    sample_ids = sample_data['id'].tolist()
    
    query_safe = f"SELECT COUNT(DISTINCT movie_id) FROM Fact_Movies WHERE movie_id IN ({','.join(map(str, sample_ids))})"
    
    with db_engine.connect() as conn:
        result = conn.execute(text(query_safe)).fetchone()
        found_count = result[0]
    
    # At least 70% should be in Fact_Movies (some might not have valid dimensions)
    match_pct = (found_count / len(sample_ids)) * 100
    assert match_pct >= 70, f"Only {match_pct:.2f}% of sample IDs found in Fact_Movies (expected >= 70%)"


def test_end_to_end_data_flow(db_engine):
    """Test that data flows correctly through all layers"""
    
    # Count records in each layer
    queries = {
        'Staging': "SELECT COUNT(*) FROM Staging_Movies",
        'Dim_Genre': "SELECT COUNT(*) FROM Dim_Genre",
        'Dim_Time': "SELECT COUNT(*) FROM Dim_Time",
        'Dim_Studio': "SELECT COUNT(*) FROM Dim_Studio",
        'Fact': "SELECT COUNT(*) FROM Fact_Movies"
    }
    
    counts = {}
    with db_engine.connect() as conn:
        for table, query in queries.items():
            result = conn.execute(text(query)).fetchone()
            counts[table] = result[0]
    
    # Assertions
    assert counts['Staging'] > 1000, f"Staging has only {counts['Staging']} rows"
    assert counts['Dim_Genre'] >= 10, f"Dim_Genre has only {counts['Dim_Genre']} rows (expected >= 10)"
    assert counts['Dim_Time'] >= 100, f"Dim_Time has only {counts['Dim_Time']} rows (expected >= 100)"
    assert counts['Dim_Studio'] >= 50, f"Dim_Studio has only {counts['Dim_Studio']} rows (expected >= 50)"
    assert counts['Fact'] > 1000, f"Fact_Movies has only {counts['Fact']} rows"
    
    print(f"\n✅ Data flow verified:")
    for table, count in counts.items():
        print(f"   {table}: {count:,} rows")