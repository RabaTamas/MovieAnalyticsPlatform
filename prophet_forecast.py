import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
from prophet import Prophet
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from datetime import datetime

load_dotenv()

print("=" * 70)
print("📈 Prophet Time Series Forecast - Movie Industry Revenue")
print("=" * 70)

# ── DATABASE CONNECTION ───────────────────────────────────────────────────────
SQL_SERVER   = os.getenv('AZURE_SQL_SERVER')
SQL_DATABASE = os.getenv('AZURE_SQL_DATABASE')
SQL_USERNAME = os.getenv('AZURE_SQL_USERNAME')
SQL_PASSWORD = os.getenv('AZURE_SQL_PASSWORD')

conn_string = (
    f"mssql+pyodbc://{SQL_USERNAME}:{SQL_PASSWORD}@{SQL_SERVER}/"
    f"{SQL_DATABASE}?driver=ODBC+Driver+17+for+SQL+Server"
)
engine = create_engine(conn_string)
print("✅ Connected to Azure SQL Database")

# ── LOAD YEARLY DATA ─────────────────────────────────────────────────────────
query = """
    SELECT
        year,
        total_revenue,
        total_films,
        avg_revenue
    FROM Agg_Yearly_Trends
    WHERE year >= 1980 AND year <= 2024
    ORDER BY year
"""
with engine.connect() as conn:
    df = pd.read_sql(text(query), conn)

print(f"✅ Loaded {len(df)} years of data (1980–2024)")

# ── PREPARE FOR PROPHET ───────────────────────────────────────────────────────
# Prophet requires columns: ds (date) and y (value)
df_prophet = pd.DataFrame({
    'ds': pd.to_datetime(df['year'].astype(str) + '-01-01'),
    'y':  df['total_revenue'] / 1e9  # Milliárd USD
})

print(f"\n📊 Revenue range: ${df_prophet['y'].min():.2f}B – ${df_prophet['y'].max():.2f}B")

# ── FIT PROPHET MODEL ─────────────────────────────────────────────────────────
print("\n⏳ Fitting Prophet model...")
model = Prophet(
    yearly_seasonality=False,
    weekly_seasonality=False,
    daily_seasonality=False,
    changepoint_prior_scale=0.3,
    interval_width=0.95
)
model.fit(df_prophet)
print("✅ Model fitted!")

# ── FORECAST 2025–2030 ────────────────────────────────────────────────────────
future = model.make_future_dataframe(periods=6, freq='YE')
forecast = model.predict(future)

# Filter forecast years
forecast_future = forecast[forecast['ds'].dt.year > 2024][
    ['ds', 'yhat', 'yhat_lower', 'yhat_upper']
].copy()
forecast_future.columns = ['year', 'predicted_revenue_B', 'lower_bound_B', 'upper_bound_B']
forecast_future['year'] = forecast_future['year'].dt.year

print("\n📈 Revenue Forecast 2025–2030:")
print(f"{'Year':<8} {'Predicted':>12} {'Lower (95%)':>14} {'Upper (95%)':>14}")
print("-" * 52)
for _, row in forecast_future.iterrows():
    print(f"{int(row['year']):<8} ${row['predicted_revenue_B']:>10.2f}B "
          f"  ${row['lower_bound_B']:>10.2f}B   ${row['upper_bound_B']:>10.2f}B")

# ── SAVE FORECAST CSV ─────────────────────────────────────────────────────────
os.makedirs('data/processed', exist_ok=True)
forecast_file = 'data/processed/prophet_forecast.csv'
forecast_future.to_csv(forecast_file, index=False)
print(f"\n✅ Forecast saved: {forecast_file}")

# ── PLOT ──────────────────────────────────────────────────────────────────────
fig, axes = plt.subplots(2, 1, figsize=(14, 10))

# Plot 1: Historical + Forecast
ax1 = axes[0]
ax1.plot(df['year'], df['total_revenue'] / 1e9,
         'b-o', linewidth=2, markersize=4, label='Historical Revenue', zorder=3)

forecast_all = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].copy()
forecast_all['year'] = forecast_all['ds'].dt.year

ax1.plot(forecast_all['year'], forecast_all['yhat'],
         'r--', linewidth=2, label='Prophet Forecast')
ax1.fill_between(forecast_all['year'],
                 forecast_all['yhat_lower'],
                 forecast_all['yhat_upper'],
                 alpha=0.2, color='red', label='95% Confidence Interval')

ax1.axvline(x=2024, color='gray', linestyle=':', linewidth=1.5, label='Forecast Start')
ax1.set_title('Movie Industry Annual Revenue: Historical & Prophet Forecast (1980–2030)',
              fontsize=13, fontweight='bold')
ax1.set_xlabel('Year')
ax1.set_ylabel('Total Revenue (Billion USD)')
ax1.legend()
ax1.grid(True, alpha=0.3)

# Plot 2: Forecast only 2020–2030
ax2 = axes[1]
hist_recent = df[df['year'] >= 2015]
ax2.bar(hist_recent['year'], hist_recent['total_revenue'] / 1e9,
        color='steelblue', alpha=0.7, label='Historical')
ax2.bar(forecast_future['year'], forecast_future['predicted_revenue_B'],
        color='tomato', alpha=0.7, label='Forecast')
ax2.errorbar(forecast_future['year'], forecast_future['predicted_revenue_B'],
             yerr=[forecast_future['predicted_revenue_B'] - forecast_future['lower_bound_B'],
                   forecast_future['upper_bound_B'] - forecast_future['predicted_revenue_B']],
             fmt='none', color='black', capsize=5)
ax2.set_title('Recent History & Near-Term Forecast (2015–2030)', fontsize=13, fontweight='bold')
ax2.set_xlabel('Year')
ax2.set_ylabel('Total Revenue (Billion USD)')
ax2.legend()
ax2.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plot_file = 'data/processed/prophet_forecast.png'
plt.savefig(plot_file, dpi=150, bbox_inches='tight')
plt.close()
print(f"✅ Plot saved: {plot_file}")

print("\n" + "=" * 70)
print("✅ Prophet Forecast Complete!")
print("=" * 70)