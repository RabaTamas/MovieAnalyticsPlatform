import os
import pandas as pd
import numpy as np
from dotenv import load_dotenv
from sklearn.model_selection import train_test_split, cross_val_score, KFold
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

load_dotenv()

print("=" * 70)
print("🤖 Movie Revenue Prediction - Linear Regression Model")
print("=" * 70)

# =============================================================================
# 1. LOAD DATA
# =============================================================================
print("\n📂 Loading cleaned data...")

df = pd.read_csv('data/processed/movies_cleaned.csv')
print(f"✅ Loaded {len(df):,} movies")

# Basic info
print(f"\n📊 Dataset info:")
print(f"   Columns: {list(df.columns)}")
print(f"   Shape: {df.shape}")

# =============================================================================
# 2. FEATURE ENGINEERING
# =============================================================================
print("\n" + "=" * 70)
print("🔧 Feature Engineering")
print("=" * 70)

# Select features for prediction
features_df = df[['budget', 'runtime', 'popularity', 'vote_average', 
                   'vote_count', 'release_year', 'release_month', 
                   'genres', 'production_companies']].copy()

# Target variable
target = df['revenue'].copy()

print(f"\n✅ Selected features: {list(features_df.columns)}")

# Handle categorical variables - GENRES
print("\n🎭 Processing genres...")
# Get first genre (primary genre)
features_df['primary_genre'] = features_df['genres'].apply(
    lambda x: x.split('-')[0].strip() if pd.notna(x) and x != '' else 'Unknown'
)

# Encode genres
genre_encoder = LabelEncoder()
features_df['genre_encoded'] = genre_encoder.fit_transform(features_df['primary_genre'])

print(f"   Unique genres: {len(genre_encoder.classes_)}")
print(f"   Top 5 genres: {list(genre_encoder.classes_[:5])}")

# Handle categorical variables - STUDIOS
print("\n🎬 Processing studios...")
# Get first studio (primary studio)
features_df['primary_studio'] = features_df['production_companies'].apply(
    lambda x: x.split('-')[0].strip() if pd.notna(x) and x != '' else 'Unknown'
)

# For studios, use frequency encoding (too many unique values for label encoding)
studio_freq = features_df['primary_studio'].value_counts()
features_df['studio_freq'] = features_df['primary_studio'].map(studio_freq)

print(f"   Unique studios: {len(features_df['primary_studio'].unique())}")
print(f"   Top 5 studios: {list(studio_freq.head().index)}")

# Create final feature set
X = features_df[[
    'budget', 
    'runtime', 
    'popularity', 
    'vote_average', 
    'vote_count',
    'release_year',
    'release_month',
    'genre_encoded',
    'studio_freq'
]].copy()

y = target

# Remove any rows with NaN values
print(f"\n🧹 Cleaning data...")
print(f"   Before: {len(X)} rows")

X = X.assign(
    runtime=X['runtime'].fillna(X['runtime'].median()),
    popularity=X['popularity'].fillna(0),
    vote_average=X['vote_average'].fillna(0),
    vote_count=X['vote_count'].fillna(0),
    studio_freq=X['studio_freq'].fillna(1)
)

# Remove rows where target (revenue) is 0 or NaN
valid_idx = (y > 0) & (y.notna())
X = X[valid_idx]
y = y[valid_idx]

print(f"   After: {len(X)} rows")
print(f"   Features shape: {X.shape}")

# =============================================================================
# 3. TRAIN/TEST SPLIT
# =============================================================================
print("\n" + "=" * 70)
print("✂️  Train/Test Split (80/20)")
print("=" * 70)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

print(f"   Training set: {len(X_train):,} samples")
print(f"   Test set: {len(X_test):,} samples")

# =============================================================================
# 4. TRAIN MODEL
# =============================================================================
print("\n" + "=" * 70)
print("🤖 Training Linear Regression Model")
print("=" * 70)

model = LinearRegression()

print("⏳ Training...")
model.fit(X_train, y_train)
print("✅ Model trained!")

# =============================================================================
# 5. MODEL EVALUATION
# =============================================================================
print("\n" + "=" * 70)
print("📊 Model Evaluation")
print("=" * 70)

# Predictions
y_train_pred = model.predict(X_train)
y_test_pred = model.predict(X_test)

# Metrics
train_r2 = r2_score(y_train, y_train_pred)
test_r2 = r2_score(y_test, y_test_pred)

train_mae = mean_absolute_error(y_train, y_train_pred)
test_mae = mean_absolute_error(y_test, y_test_pred)

train_rmse = np.sqrt(mean_squared_error(y_train, y_train_pred))
test_rmse = np.sqrt(mean_squared_error(y_test, y_test_pred))

print(f"\n📈 Training Set:")
print(f"   R² Score: {train_r2:.4f}")
print(f"   MAE: ${train_mae:,.0f}")
print(f"   RMSE: ${train_rmse:,.0f}")

print(f"\n📉 Test Set:")
print(f"   R² Score: {test_r2:.4f}")
print(f"   MAE: ${test_mae:,.0f}")
print(f"   RMSE: ${test_rmse:,.0f}")

# Check if R² > 0.6
if test_r2 > 0.6:
    print(f"\n✅ SUCCESS! R² = {test_r2:.4f} > 0.6")
else:
    print(f"\n⚠️  WARNING! R² = {test_r2:.4f} < 0.6 (Target: > 0.6)")

# =============================================================================
# 6. CROSS-VALIDATION (5-fold)
# =============================================================================
print("\n" + "=" * 70)
print("🔄 5-Fold Cross-Validation")
print("=" * 70)

kf = KFold(n_splits=5, shuffle=True, random_state=42)
cv_scores = cross_val_score(model, X, y, cv=kf, scoring='r2')

print(f"\n📊 Cross-validation R² scores:")
for i, score in enumerate(cv_scores, 1):
    print(f"   Fold {i}: {score:.4f}")

print(f"\n   Mean R²: {cv_scores.mean():.4f}")
print(f"   Std Dev: {cv_scores.std():.4f}")

# =============================================================================
# 7. FEATURE IMPORTANCE
# =============================================================================
print("\n" + "=" * 70)
print("🔍 Feature Importance (Coefficients)")
print("=" * 70)

feature_importance = pd.DataFrame({
    'feature': X.columns,
    'coefficient': model.coef_
}).sort_values('coefficient', key=abs, ascending=False)

print("\n   Top features:")
for idx, row in feature_importance.head(9).iterrows():
    print(f"   {row['feature']:20s}: {row['coefficient']:>15,.2f}")

# =============================================================================
# 8. GENERATE PREDICTIONS FOR ALL DATA
# =============================================================================
print("\n" + "=" * 70)
print("💾 Generating Predictions for All Movies")
print("=" * 70)

# Predict for all data
y_pred_all = model.predict(X)

# Create predictions dataframe
predictions_df = df[valid_idx][['id', 'title', 'budget', 'revenue', 
                                  'genres', 'production_companies', 
                                  'release_year']].copy()

predictions_df['predicted_revenue'] = y_pred_all
predictions_df['prediction_error'] = predictions_df['revenue'] - predictions_df['predicted_revenue']
predictions_df['error_percentage'] = (predictions_df['prediction_error'] / predictions_df['revenue'] * 100).abs()

# Categorize predictions
predictions_df['performance'] = predictions_df.apply(
    lambda row: 'Over-performing' if row['prediction_error'] > 0 else 'Under-performing',
    axis=1
)

print(f"\n✅ Generated predictions for {len(predictions_df):,} movies")

# Top over-performing films
print(f"\n💎 Top 10 Over-Performing Films:")
top_over = predictions_df.nlargest(10, 'prediction_error')[
    ['title', 'revenue', 'predicted_revenue', 'prediction_error']
]
for idx, row in top_over.iterrows():
    print(f"   {row['title'][:40]:40s} | Actual: ${row['revenue']/1e9:.2f}B | Predicted: ${row['predicted_revenue']/1e9:.2f}B | Diff: ${row['prediction_error']/1e9:.2f}B")

# Top under-performing films
print(f"\n📉 Top 10 Under-Performing Films:")
top_under = predictions_df.nsmallest(10, 'prediction_error')[
    ['title', 'revenue', 'predicted_revenue', 'prediction_error']
]
for idx, row in top_under.iterrows():
    print(f"   {row['title'][:40]:40s} | Actual: ${row['revenue']/1e9:.2f}B | Predicted: ${row['predicted_revenue']/1e9:.2f}B | Diff: ${row['prediction_error']/1e9:.2f}B")

# =============================================================================
# 9. SAVE PREDICTIONS TO CSV
# =============================================================================
print("\n" + "=" * 70)
print("💾 Saving Predictions to CSV")
print("=" * 70)

output_file = 'data/processed/ml_predictions.csv'
predictions_df.to_csv(output_file, index=False)

print(f"✅ Saved to: {output_file}")
print(f"   Rows: {len(predictions_df):,}")
print(f"   Columns: {list(predictions_df.columns)}")

# =============================================================================
# 10. SUMMARY
# =============================================================================
print("\n" + "=" * 70)
print("📋 ML Model Summary")
print("=" * 70)

print(f"\n✅ Model trained successfully!")
print(f"   Algorithm: Linear Regression")
print(f"   Features: {len(X.columns)}")
print(f"   Training samples: {len(X_train):,}")
print(f"   Test samples: {len(X_test):,}")
print(f"   Test R² Score: {test_r2:.4f}")
print(f"   5-Fold CV Mean R²: {cv_scores.mean():.4f}")
print(f"   Predictions saved: {len(predictions_df):,}")

print("\n" + "=" * 70)
print("✅ ML Model complete!")
print("=" * 70)