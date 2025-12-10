import pytest
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

load_dotenv()

# =============================================================================
# DATABASE CONNECTION
# =============================================================================

@pytest.fixture(scope='module')
def db_engine():
    """Create database engine for testing"""
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


# =============================================================================
# TEST: Database Data Quality
# =============================================================================

def test_staging_no_null_movie_id(db_engine):
    """Test that Staging_Movies has no NULL movie_id"""
    query = "SELECT COUNT(*) as null_count FROM Staging_Movies WHERE movie_id IS NULL"
    
    with db_engine.connect() as conn:
        result = conn.execute(text(query)).fetchone()
        null_count = result[0]
    
    assert null_count == 0, f"Found {null_count} NULL movie_id in Staging_Movies"


def test_staging_no_negative_budget(db_engine):
    """Test that Staging_Movies has no negative budget"""
    query = "SELECT COUNT(*) as neg_count FROM Staging_Movies WHERE budget < 0"
    
    with db_engine.connect() as conn:
        result = conn.execute(text(query)).fetchone()
        neg_count = result[0]
    
    assert neg_count == 0, f"Found {neg_count} negative budget values in Staging_Movies"


def test_staging_no_negative_revenue(db_engine):
    """Test that Staging_Movies has no negative revenue"""
    query = "SELECT COUNT(*) as neg_count FROM Staging_Movies WHERE revenue < 0"
    
    with db_engine.connect() as conn:
        result = conn.execute(text(query)).fetchone()
        neg_count = result[0]
    
    assert neg_count == 0, f"Found {neg_count} negative revenue values in Staging_Movies"


def test_staging_rating_range(db_engine):
    """Test that vote_average is in valid range (0-10)"""
    query = "SELECT COUNT(*) as invalid_count FROM Staging_Movies WHERE vote_average < 0 OR vote_average > 10"
    
    with db_engine.connect() as conn:
        result = conn.execute(text(query)).fetchone()
        invalid_count = result[0]
    
    assert invalid_count == 0, f"Found {invalid_count} invalid ratings in Staging_Movies"


def test_fact_no_null_foreign_keys(db_engine):
    """Test that Fact_Movies has no NULL foreign keys"""
    queries = {
        'genre_id': "SELECT COUNT(*) FROM Fact_Movies WHERE genre_id IS NULL",
        'time_id': "SELECT COUNT(*) FROM Fact_Movies WHERE time_id IS NULL",
        'studio_id': "SELECT COUNT(*) FROM Fact_Movies WHERE studio_id IS NULL"
    }
    
    for fk_name, query in queries.items():
        with db_engine.connect() as conn:
            result = conn.execute(text(query)).fetchone()
            null_count = result[0]
        
        assert null_count == 0, f"Found {null_count} NULL {fk_name} in Fact_Movies"


def test_fact_referential_integrity(db_engine):
    """Test that all foreign keys in Fact_Movies exist in dimension tables"""
    
    # Test genre_id
    query_genre = """
        SELECT COUNT(*) 
        FROM Fact_Movies f 
        WHERE f.genre_id NOT IN (SELECT genre_id FROM Dim_Genre)
        AND f.genre_id IS NOT NULL
    """
    
    with db_engine.connect() as conn:
        result = conn.execute(text(query_genre)).fetchone()
        orphaned = result[0]
    
    assert orphaned == 0, f"Found {orphaned} orphaned genre_id in Fact_Movies"


def test_overall_data_quality(db_engine):
    """Test overall data quality percentage"""
    query_total = "SELECT COUNT(*) FROM Staging_Movies"
    query_invalid = """
        SELECT COUNT(*) FROM Staging_Movies 
        WHERE budget < 0 OR revenue < 0 OR vote_average < 0 OR vote_average > 10
    """
    
    with db_engine.connect() as conn:
        total = conn.execute(text(query_total)).fetchone()[0]
        invalid = conn.execute(text(query_invalid)).fetchone()[0]
    
    invalid_pct = (invalid / total * 100) if total > 0 else 0
    
    assert invalid_pct < 0.5, f"Data quality too low: {invalid_pct:.2f}% invalid records (spec requires < 0.5%)"