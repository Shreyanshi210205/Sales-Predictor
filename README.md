# AI Demand Forecasting System

A basic grocery demand forecasting dashboard that predicts the next 7 days of product demand and turns the forecast into inventory actions.

## Features

- 7-day product demand forecast
- Weather and holiday demand adjustments
- Seasonal and weekday demand patterns
- Auto reorder suggestions
- Low-stock and stockout alerts
- Demand heatmap
- Browser dashboard with category filter and product search

## Run

```powershell
python app.py
```

Open:

```text
http://127.0.0.1:8000
```


## How It Works

This starter version uses a lightweight forecasting model so it can run without external packages:

- recent 7-day sales average
- recent 28-day sales average
- same-weekday sales history
- weather multipliers
- holiday multipliers
- lead-time demand plus safety stock for reorder points

For a production version, the forecasting function can be replaced with XGBoost, LightGBM, Prophet, or an LSTM while keeping the dashboard and reorder logic.
