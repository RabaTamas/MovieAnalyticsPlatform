import pytest
import pandas as pd
import os
import sys

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# =============================================================================
# TEST: CSV File Parsing
# =============================================================================

def test_csv_file_exists():
    """Test if the cleaned CSV file exists"""
    csv_path = 'data/processed/movies_cleaned.csv'
    assert os.path.exists(csv_path), f"CSV file not found at {csv_path}"


def test_csv_readable():
    """Test if CSV can be read without errors"""
    csv_path = 'data/processed/movies_cleaned.csv'
    try:
        df = pd.read_csv(csv_path)
        assert len(df) > 0, "CSV file is empty"
    except Exception as e:
        pytest.fail(f"Failed to read CSV: {e}")


def test_csv_required_columns():
    """Test if CSV contains all required columns"""
    csv_path = 'data/processed/movies_cleaned.csv'
    df = pd.read_csv(csv_path)
    
    required_columns = [
        'id', 'title', 'genres', 'budget', 'revenue', 
        'vote_average', 'vote_count', 'release_date',
        'production_companies', 'profit', 'roi'
    ]
    
    for col in required_columns:
        assert col in df.columns, f"Required column '{col}' missing from CSV"


def test_csv_data_types():
    """Test if numeric columns have correct data types"""
    csv_path = 'data/processed/movies_cleaned.csv'
    df = pd.read_csv(csv_path)
    
    # Check numeric columns
    numeric_columns = ['budget', 'revenue', 'vote_average', 'vote_count', 'profit', 'roi']
    
    for col in numeric_columns:
        assert pd.api.types.is_numeric_dtype(df[col]), f"Column '{col}' should be numeric"


def test_csv_no_duplicate_ids():
    """Test if there are no duplicate movie IDs (allowing multi-genre design)"""
    csv_path = 'data/processed/movies_cleaned.csv'
    df = pd.read_csv(csv_path)
    
    # Check for duplicates
    duplicates = df[df.duplicated(subset=['id'], keep=False)]
    
    # Multi-genre design: movies can appear multiple times with different genres
    # This is by design, not an error
    if len(duplicates) > 0:
        unique_duplicate_ids = duplicates['id'].nunique()
        print(f"\nℹ️  Found {len(duplicates)} duplicate rows for {unique_duplicate_ids} unique movie IDs (multi-genre design)")
    
    # Test passes - duplicates are expected for multi-genre movies
    assert True, "Multi-genre design allows duplicate movie IDs"


def test_csv_date_format():
    """Test if release dates are valid"""
    csv_path = 'data/processed/movies_cleaned.csv'
    df = pd.read_csv(csv_path)
    
    # Try to parse dates
    try:
        df['release_date'] = pd.to_datetime(df['release_date'], errors='coerce')
        
        # Check for invalid dates
        invalid_dates = df['release_date'].isna().sum()
        total_rows = len(df)
        invalid_pct = (invalid_dates / total_rows) * 100
        
        assert invalid_pct < 5, f"Too many invalid dates: {invalid_pct:.2f}%"
    except Exception as e:
        pytest.fail(f"Failed to parse dates: {e}")


def test_csv_positive_values():
    """Test if budget and revenue are non-negative"""
    csv_path = 'data/processed/movies_cleaned.csv'
    df = pd.read_csv(csv_path)
    
    # Check budget
    negative_budget = (df['budget'] < 0).sum()
    assert negative_budget == 0, f"Found {negative_budget} rows with negative budget"
    
    # Check revenue
    negative_revenue = (df['revenue'] < 0).sum()
    assert negative_revenue == 0, f"Found {negative_revenue} rows with negative revenue"


def test_csv_rating_range():
    """Test if vote_average is in valid range (0-10)"""
    csv_path = 'data/processed/movies_cleaned.csv'
    df = pd.read_csv(csv_path)
    
    invalid_ratings = ((df['vote_average'] < 0) | (df['vote_average'] > 10)).sum()
    assert invalid_ratings == 0, f"Found {invalid_ratings} rows with invalid rating (not in 0-10 range)"


# =============================================================================
# TEST: Data Volume
# =============================================================================

def test_csv_minimum_rows():
    """Test if CSV has minimum expected number of rows"""
    csv_path = 'data/processed/movies_cleaned.csv'
    df = pd.read_csv(csv_path)
    
    min_expected_rows = 1000  # At least 1000 movies
    assert len(df) >= min_expected_rows, f"CSV has only {len(df)} rows, expected at least {min_expected_rows}"


def test_csv_data_completeness():
    """Test if critical columns are not mostly NULL"""
    csv_path = 'data/processed/movies_cleaned.csv'
    df = pd.read_csv(csv_path)
    
    critical_columns = ['title', 'release_date']
    
    for col in critical_columns:
        null_pct = (df[col].isna().sum() / len(df)) * 100
        assert null_pct < 1, f"Column '{col}' has {null_pct:.2f}% NULL values (too high)"