import pytest
import pandas as pd
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# =============================================================================
# TEST: NULL Handling
# =============================================================================

def test_null_in_id():
    """Test that movie_id has no NULL values"""
    csv_path = 'data/processed/movies_cleaned.csv'
    df = pd.read_csv(csv_path)
    
    null_count = df['id'].isna().sum()
    assert null_count == 0, f"Found {null_count} NULL values in 'id' column"


def test_null_in_title():
    """Test that title has no NULL values"""
    csv_path = 'data/processed/movies_cleaned.csv'
    df = pd.read_csv(csv_path)
    
    null_count = df['title'].isna().sum()
    assert null_count == 0, f"Found {null_count} NULL values in 'title' column"


def test_null_percentage_budget():
    """Test that budget NULL percentage is acceptable"""
    csv_path = 'data/processed/movies_cleaned.csv'
    df = pd.read_csv(csv_path)
    
    null_pct = (df['budget'].isna().sum() / len(df)) * 100
    assert null_pct < 50, f"Budget has {null_pct:.2f}% NULL values (too high)"


def test_null_percentage_revenue():
    """Test that revenue NULL percentage is acceptable"""
    csv_path = 'data/processed/movies_cleaned.csv'
    df = pd.read_csv(csv_path)
    
    null_pct = (df['revenue'].isna().sum() / len(df)) * 100
    assert null_pct < 50, f"Revenue has {null_pct:.2f}% NULL values (too high)"


def test_genres_not_empty():
    """Test that genres column is not empty"""
    csv_path = 'data/processed/movies_cleaned.csv'
    df = pd.read_csv(csv_path)
    
    empty_genres = (df['genres'].isna() | (df['genres'] == '')).sum()
    empty_pct = (empty_genres / len(df)) * 100
    
    assert empty_pct < 10, f"Genres column has {empty_pct:.2f}% empty values"


# =============================================================================
# TEST: Data Consistency
# =============================================================================

def test_profit_calculation():
    """Test if profit is correctly calculated (revenue - budget)"""
    csv_path = 'data/processed/movies_cleaned.csv'
    df = pd.read_csv(csv_path)
    
    # Filter rows with valid budget and revenue
    valid_rows = df[(df['budget'].notna()) & (df['revenue'].notna()) & 
                    (df['budget'] > 0) & (df['revenue'] > 0)]
    
    if len(valid_rows) > 0:
        # Calculate expected profit
        expected_profit = valid_rows['revenue'] - valid_rows['budget']
        actual_profit = valid_rows['profit']
        
        # Check if calculation matches (with small tolerance for floating point)
        matches = (abs(expected_profit - actual_profit) < 1).sum()
        match_pct = (matches / len(valid_rows)) * 100
        
        assert match_pct > 95, f"Only {match_pct:.2f}% of profit calculations match expected values"


def test_roi_calculation():
    """Test if ROI is correctly calculated (profit / budget)"""
    csv_path = 'data/processed/movies_cleaned.csv'
    df = pd.read_csv(csv_path)
    
    # Filter rows with valid data for ROI
    valid_rows = df[(df['budget'].notna()) & (df['revenue'].notna()) & 
                    (df['profit'].notna()) & (df['roi'].notna()) &
                    (df['budget'] > 0)]
    
    if len(valid_rows) > 0:
        # Calculate expected ROI
        expected_roi = valid_rows['profit'] / valid_rows['budget']
        actual_roi = valid_rows['roi']
        
        # Check if calculation matches (with tolerance)
        matches = (abs(expected_roi - actual_roi) < 0.01).sum()
        match_pct = (matches / len(valid_rows)) * 100
        
        assert match_pct > 95, f"Only {match_pct:.2f}% of ROI calculations match expected values"