from __future__ import annotations

import csv
import json
import math
import random
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


DATA_DIR = Path("data")
SALES_FILE = DATA_DIR / "sample_sales.csv"
HOST = "127.0.0.1"
PORT = 8000

HOLIDAYS = {
    "2026-01-01": "New Year",
    "2026-01-26": "Republic Day",
    "2026-03-04": "Holi",
    "2026-08-15": "Independence Day",
    "2026-10-20": "Diwali",
    "2026-12-25": "Christmas",
}

PRODUCTS = [
    {
        "sku": "MILK-1L",
        "name": "Milk 1L",
        "category": "Dairy",
        "base_demand": 86,
        "stock": 430,
        "lead_time": 2,
        "weather": {"hot": 1.05, "rain": 0.94, "cold": 0.98},
        "holiday": 1.12,
    },
    {
        "sku": "BREAD-WHT",
        "name": "White Bread",
        "category": "Bakery",
        "base_demand": 72,
        "stock": 270,
        "lead_time": 1,
        "weather": {"hot": 0.96, "rain": 1.08, "cold": 1.03},
        "holiday": 1.08,
    },
    {
        "sku": "EGGS-12",
        "name": "Eggs 12 Pack",
        "category": "Protein",
        "base_demand": 52,
        "stock": 180,
        "lead_time": 2,
        "weather": {"hot": 0.97, "rain": 1.04, "cold": 1.05},
        "holiday": 1.1,
    },
    {
        "sku": "RICE-5KG",
        "name": "Rice 5kg",
        "category": "Staples",
        "base_demand": 28,
        "stock": 95,
        "lead_time": 4,
        "weather": {"hot": 1.0, "rain": 1.03, "cold": 1.0},
        "holiday": 1.25,
    },
    {
        "sku": "ICECREAM",
        "name": "Ice Cream",
        "category": "Frozen",
        "base_demand": 34,
        "stock": 115,
        "lead_time": 3,
        "weather": {"hot": 1.48, "rain": 0.72, "cold": 0.6},
        "holiday": 1.18,
    },
    {
        "sku": "UMBRELLA",
        "name": "Umbrella",
        "category": "Seasonal",
        "base_demand": 12,
        "stock": 36,
        "lead_time": 5,
        "weather": {"hot": 0.55, "rain": 2.25, "cold": 0.8},
        "holiday": 1.0,
    },
    {
        "sku": "SOUP",
        "name": "Instant Soup",
        "category": "Packaged",
        "base_demand": 24,
        "stock": 70,
        "lead_time": 3,
        "weather": {"hot": 0.58, "rain": 1.16, "cold": 1.62},
        "holiday": 1.06,
    },
    {
        "sku": "SODA",
        "name": "Soda Cans",
        "category": "Beverages",
        "base_demand": 44,
        "stock": 210,
        "lead_time": 2,
        "weather": {"hot": 1.36, "rain": 0.86, "cold": 0.74},
        "holiday": 1.2,
    },
]


@dataclass(frozen=True)
class Product:
    sku: str
    name: str
    category: str
    base_demand: int
    stock: int
    lead_time: int
    weather: dict[str, float]
    holiday: float


def product_catalog() -> list[Product]:
    return [Product(**item) for item in PRODUCTS]


def weather_for(day: date) -> str:
    month = day.month
    if month in {6, 7, 8, 9}:
        return random.choices(["rain", "hot", "cold"], weights=[62, 32, 6], k=1)[0]
    if month in {11, 12, 1, 2}:
        return random.choices(["cold", "rain", "hot"], weights=[60, 18, 22], k=1)[0]
    return random.choices(["hot", "rain", "cold"], weights=[58, 25, 17], k=1)[0]


def ensure_sample_data() -> None:
    if SALES_FILE.exists():
        return

    DATA_DIR.mkdir(exist_ok=True)
    random.seed(42)
    today = date.today()
    start = today - timedelta(days=180)
    products = product_catalog()

    with SALES_FILE.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["date", "sku", "product", "category", "units_sold", "weather", "holiday"],
        )
        writer.writeheader()

        for offset in range(181):
            day = start + timedelta(days=offset)
            weather = weather_for(day)
            is_holiday = day.isoformat() in HOLIDAYS
            weekend_multiplier = 1.18 if day.weekday() >= 5 else 1.0
            payday_multiplier = 1.13 if day.day in {1, 2, 15, 16} else 1.0
            seasonal_wave = 1 + 0.08 * math.sin((day.timetuple().tm_yday / 365) * 2 * math.pi)

            for product in products:
                weather_multiplier = product.weather[weather]
                holiday_multiplier = product.holiday if is_holiday else 1.0
                noise = random.uniform(0.86, 1.16)
                units = round(
                    product.base_demand
                    * weekend_multiplier
                    * payday_multiplier
                    * seasonal_wave
                    * weather_multiplier
                    * holiday_multiplier
                    * noise
                )
                writer.writerow(
                    {
                        "date": day.isoformat(),
                        "sku": product.sku,
                        "product": product.name,
                        "category": product.category,
                        "units_sold": max(1, units),
                        "weather": weather,
                        "holiday": HOLIDAYS.get(day.isoformat(), ""),
                    }
                )


def read_sales() -> list[dict[str, Any]]:
    ensure_sample_data()
    with SALES_FILE.open(encoding="utf-8") as file:
        return list(csv.DictReader(file))


def future_weather(day: date) -> str:
    month = day.month
    if month in {6, 7, 8, 9}:
        pattern = ["rain", "rain", "hot", "rain", "hot", "rain", "cold"]
    elif month in {11, 12, 1, 2}:
        pattern = ["cold", "cold", "hot", "cold", "rain", "cold", "hot"]
    else:
        pattern = ["hot", "rain", "hot", "hot", "rain", "cold", "hot"]
    return pattern[day.toordinal() % len(pattern)]


def group_sales(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(row["sku"], []).append(row)
    for sku_rows in grouped.values():
        sku_rows.sort(key=lambda item: item["date"])
    return grouped


def average(values: list[float], fallback: float = 0) -> float:
    return sum(values) / len(values) if values else fallback


def forecast_product(product: Product, rows: list[dict[str, Any]]) -> dict[str, Any]:
    recent = rows[-28:]
    last_7_avg = average([float(row["units_sold"]) for row in recent[-7:]], product.base_demand)
    last_28_avg = average([float(row["units_sold"]) for row in recent], product.base_demand)
    same_weekday: dict[int, list[float]] = {}
    weather_history: dict[str, list[float]] = {"hot": [], "rain": [], "cold": []}

    for row in rows:
        day = datetime.strptime(row["date"], "%Y-%m-%d").date()
        units = float(row["units_sold"])
        same_weekday.setdefault(day.weekday(), []).append(units)
        weather_history[row["weather"]].append(units)

    weather_baseline = average([float(row["units_sold"]) for row in rows], product.base_demand)
    days = []
    today = date.today()

    for index in range(1, 8):
        day = today + timedelta(days=index)
        weather = future_weather(day)
        weekday_avg = average(same_weekday.get(day.weekday(), [])[-8:], last_28_avg)
        weather_avg = average(weather_history.get(weather, [])[-30:], weather_baseline)
        weather_factor = max(0.65, min(1.65, weather_avg / weather_baseline if weather_baseline else 1))
        holiday_name = HOLIDAYS.get(day.isoformat(), "")
        holiday_factor = product.holiday if holiday_name else 1.0
        blended = (last_7_avg * 0.45) + (last_28_avg * 0.25) + (weekday_avg * 0.3)
        prediction = max(1, round(blended * weather_factor * holiday_factor))

        days.append(
            {
                "date": day.isoformat(),
                "day": day.strftime("%a"),
                "weather": weather,
                "holiday": holiday_name,
                "forecast": prediction,
            }
        )

    total = sum(item["forecast"] for item in days)
    lead_time_demand = sum(item["forecast"] for item in days[: min(product.lead_time, 7)])
    safety_stock = math.ceil(last_28_avg * 0.4)
    reorder_point = math.ceil(lead_time_demand + safety_stock)
    recommended_order = max(0, math.ceil(total + safety_stock - product.stock))
    stockout_day = None
    projected_stock = product.stock

    for item in days:
        projected_stock -= item["forecast"]
        if projected_stock < 0 and stockout_day is None:
            stockout_day = item["date"]

    status = "healthy"
    if stockout_day:
        status = "stockout-risk"
    elif product.stock <= reorder_point:
        status = "reorder-soon"

    return {
        "sku": product.sku,
        "name": product.name,
        "category": product.category,
        "stock": product.stock,
        "leadTime": product.lead_time,
        "forecastDays": days,
        "forecast7d": total,
        "reorderPoint": reorder_point,
        "recommendedOrder": recommended_order,
        "stockoutDay": stockout_day,
        "status": status,
    }


def build_payload() -> dict[str, Any]:
    rows = read_sales()
    grouped = group_sales(rows)
    products = product_catalog()
    forecasts = [forecast_product(product, grouped[product.sku]) for product in products]
    category_totals: dict[str, int] = {}

    for item in forecasts:
        category_totals[item["category"]] = category_totals.get(item["category"], 0) + item["forecast7d"]

    heatmap = [
        {
            "product": item["name"],
            "values": [day["forecast"] for day in item["forecastDays"]],
        }
        for item in forecasts
    ]

    return {
        "generatedAt": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "summary": {
            "products": len(forecasts),
            "forecast7d": sum(item["forecast7d"] for item in forecasts),
            "lowStock": sum(1 for item in forecasts if item["status"] != "healthy"),
            "reorderUnits": sum(item["recommendedOrder"] for item in forecasts),
        },
        "forecasts": forecasts,
        "categoryTotals": category_totals,
        "heatmap": heatmap,
        "days": forecasts[0]["forecastDays"] if forecasts else [],
    }


def custom_forecast(payload: dict[str, Any]) -> dict[str, Any]:
    name = str(payload.get("name") or "Custom Product").strip()[:60]
    stock = max(0, int(float(payload.get("stock") or 0)))
    lead_time = max(1, min(7, int(float(payload.get("leadTime") or 2))))
    weather = str(payload.get("weather") or "hot")
    holiday = bool(payload.get("holiday"))
    recent_sales = payload.get("recentSales") or []

    clean_sales = []
    for value in recent_sales:
        try:
            clean_sales.append(max(0, float(value)))
        except (TypeError, ValueError):
            continue

    if not clean_sales:
        clean_sales = [20, 22, 19, 24, 26, 28, 25]

    last_7 = clean_sales[-7:]
    avg_sales = average(last_7, 20)
    trend = 0
    if len(last_7) >= 2:
        trend = (last_7[-1] - last_7[0]) / max(1, len(last_7) - 1)

    weather_factor = {"hot": 1.18, "rain": 1.08, "cold": 0.94}.get(weather, 1.0)
    holiday_factor = 1.18 if holiday else 1.0
    weekend_factor = {5: 1.14, 6: 1.18}
    today = date.today()
    forecast_days = []

    for index in range(1, 8):
        day = today + timedelta(days=index)
        weekday_boost = weekend_factor.get(day.weekday(), 1.0)
        trend_adjustment = 1 + ((trend / max(avg_sales, 1)) * index)
        prediction = round(avg_sales * trend_adjustment * weather_factor * holiday_factor * weekday_boost)
        forecast_days.append(
            {
                "date": day.isoformat(),
                "day": day.strftime("%a"),
                "forecast": max(1, prediction),
                "weather": weather,
                "holiday": "Yes" if holiday else "",
            }
        )

    total = sum(day["forecast"] for day in forecast_days)
    lead_time_demand = sum(day["forecast"] for day in forecast_days[:lead_time])
    safety_stock = math.ceil(avg_sales * 0.4)
    reorder_point = math.ceil(lead_time_demand + safety_stock)
    recommended_order = max(0, math.ceil(total + safety_stock - stock))
    projected_stock = stock - total

    return {
        "name": name,
        "stock": stock,
        "leadTime": lead_time,
        "forecastDays": forecast_days,
        "forecast7d": total,
        "reorderPoint": reorder_point,
        "recommendedOrder": recommended_order,
        "projectedStock": projected_stock,
        "status": "stockout-risk" if projected_stock < 0 else "reorder-soon" if stock <= reorder_point else "healthy",
    }


HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AI Demand Forecasting</title>
  <style>
    :root {
      color-scheme: light;
      --ink: #17202a;
      --muted: #5d6978;
      --line: #dce3ea;
      --panel: #ffffff;
      --wash: #f4f7fa;
      --accent: #0f766e;
      --alert: #b42318;
      --warn: #b7791f;
      --blue: #1d4ed8;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Inter, Segoe UI, system-ui, sans-serif;
      color: var(--ink);
      background: var(--wash);
    }
    header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 16px;
      padding: 24px 32px;
      background: #ffffff;
      border-bottom: 1px solid var(--line);
    }
    h1, h2, p { margin: 0; }
    h1 { font-size: clamp(24px, 3vw, 34px); letter-spacing: 0; }
    h2 { font-size: 18px; margin-bottom: 14px; }
    .muted { color: var(--muted); }
    main { padding: 24px 32px 40px; display: grid; gap: 22px; }
    .toolbar { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
    select, input {
      border: 1px solid var(--line);
      background: #fff;
      border-radius: 6px;
      padding: 10px 12px;
      min-height: 42px;
      font: inherit;
    }
    .grid { display: grid; gap: 16px; }
    .metrics { grid-template-columns: repeat(4, minmax(160px, 1fr)); }
    .metric, section {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 18px;
    }
    .metric strong { display: block; font-size: 30px; margin-top: 8px; }
    .layout { grid-template-columns: minmax(0, 1.6fr) minmax(320px, 0.8fr); align-items: start; }
    .formGrid { display: grid; grid-template-columns: repeat(2, minmax(160px, 1fr)); gap: 12px; }
    label { display: grid; gap: 6px; color: var(--muted); font-size: 13px; font-weight: 650; }
    button {
      border: 0;
      background: var(--accent);
      color: #fff;
      border-radius: 6px;
      padding: 10px 14px;
      min-height: 42px;
      font: inherit;
      font-weight: 750;
      cursor: pointer;
    }
    .wide { grid-column: 1 / -1; }
    table { width: 100%; border-collapse: collapse; font-size: 14px; }
    th, td { padding: 12px 10px; text-align: left; border-bottom: 1px solid var(--line); vertical-align: middle; }
    th { color: var(--muted); font-weight: 650; }
    .status {
      display: inline-flex;
      align-items: center;
      min-height: 28px;
      padding: 4px 9px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 700;
      white-space: nowrap;
    }
    .healthy { background: #def7ec; color: #046c4e; }
    .reorder-soon { background: #fef3c7; color: #92400e; }
    .stockout-risk { background: #fee2e2; color: #991b1b; }
    .bars { display: grid; grid-template-columns: repeat(7, 1fr); gap: 10px; min-height: 210px; align-items: end; }
    .barWrap { display: grid; gap: 8px; align-items: end; justify-items: center; min-width: 0; }
    .bar { width: 100%; max-width: 44px; min-height: 8px; border-radius: 6px 6px 2px 2px; background: var(--accent); }
    .barLabel { font-size: 12px; color: var(--muted); text-align: center; }
    .heatmap { display: grid; gap: 8px; overflow-x: auto; }
    .heatrow { display: grid; grid-template-columns: 130px repeat(7, minmax(44px, 1fr)); gap: 6px; align-items: center; }
    .cell {
      min-height: 36px;
      border-radius: 6px;
      display: grid;
      place-items: center;
      color: #fff;
      font-size: 12px;
      font-weight: 700;
    }
    .alerts { display: grid; gap: 10px; }
    .alert {
      border-left: 4px solid var(--warn);
      background: #fffbeb;
      padding: 12px;
      border-radius: 6px;
    }
    .alert.risk { border-left-color: var(--alert); background: #fff1f2; }
    @media (max-width: 900px) {
      header, main { padding-left: 18px; padding-right: 18px; }
      .metrics, .layout, .formGrid { grid-template-columns: 1fr; }
      table { font-size: 13px; }
      th, td { padding: 10px 6px; }
    }
  </style>
</head>
<body>
  <header>
    <div>
      <h1>AI Demand Forecasting</h1>
      <p class="muted">7-day grocery inventory forecast with weather, seasonality, holidays, and reorder signals.</p>
    </div>
    <div class="toolbar">
      <select id="categoryFilter" aria-label="Filter by category"></select>
      <input id="search" type="search" placeholder="Search product">
    </div>
  </header>
  <main>
    <div class="grid metrics" id="metrics"></div>
    <div class="grid layout">
      <section>
        <h2>Try Your Data</h2>
        <form id="customForm" class="formGrid">
          <label>Product name
            <input name="name" value="Mango Juice">
          </label>
          <label>Current stock
            <input name="stock" type="number" min="0" value="120">
          </label>
          <label>Lead time days
            <input name="leadTime" type="number" min="1" max="7" value="2">
          </label>
          <label>Expected weather
            <select name="weather">
              <option value="hot">Hot</option>
              <option value="rain">Rain</option>
              <option value="cold">Cold</option>
            </select>
          </label>
          <label class="wide">Last 7 days sales, comma separated
            <input name="recentSales" value="22, 25, 24, 30, 34, 38, 36">
          </label>
          <label>
            Holiday coming?
            <select name="holiday">
              <option value="false">No</option>
              <option value="true">Yes</option>
            </select>
          </label>
          <button type="submit">Predict</button>
        </form>
      </section>
      <section>
        <h2>Custom Prediction Output</h2>
        <div id="customOutput" class="muted">Enter values and click Predict.</div>
      </section>
    </div>
    <div class="grid layout">
      <section>
        <h2>Inventory Forecast</h2>
        <table>
          <thead>
            <tr>
              <th>Product</th>
              <th>Stock</th>
              <th>7-day demand</th>
              <th>Reorder point</th>
              <th>Order</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody id="forecastRows"></tbody>
        </table>
      </section>
      <section>
        <h2>Selected Product</h2>
        <div id="selectedForecast"></div>
      </section>
    </div>
    <div class="grid layout">
      <section>
        <h2>Demand Heatmap</h2>
        <div class="heatmap" id="heatmap"></div>
      </section>
      <section>
        <h2>Low-stock Alerts</h2>
        <div class="alerts" id="alerts"></div>
      </section>
    </div>
  </main>
  <script>
    let state = { data: null, selectedSku: null };

    const labels = {
      healthy: "Healthy",
      "reorder-soon": "Reorder soon",
      "stockout-risk": "Stockout risk"
    };

    function moneyless(value) {
      return Number(value).toLocaleString("en-IN");
    }

    async function loadData() {
      const response = await fetch("/api/forecast");
      state.data = await response.json();
      state.selectedSku = state.data.forecasts[0].sku;
      renderFilters();
      render();
    }

    function filteredProducts() {
      const category = document.querySelector("#categoryFilter").value;
      const term = document.querySelector("#search").value.toLowerCase().trim();
      return state.data.forecasts.filter(item => {
        const categoryMatch = category === "All" || item.category === category;
        const textMatch = !term || item.name.toLowerCase().includes(term) || item.sku.toLowerCase().includes(term);
        return categoryMatch && textMatch;
      });
    }

    function renderFilters() {
      const select = document.querySelector("#categoryFilter");
      const categories = ["All", ...new Set(state.data.forecasts.map(item => item.category))];
      select.innerHTML = categories.map(category => `<option>${category}</option>`).join("");
      select.addEventListener("change", render);
      document.querySelector("#search").addEventListener("input", render);
    }

    function renderMetrics(items = state.data.forecasts) {
      const lowStock = items.filter(item => item.status !== "healthy").length;
      const reorderUnits = items.reduce((sum, item) => sum + item.recommendedOrder, 0);
      const demand = items.reduce((sum, item) => sum + item.forecast7d, 0);
      document.querySelector("#metrics").innerHTML = [
        ["Products", items.length],
        ["7-day demand", moneyless(demand)],
        ["Low-stock alerts", lowStock],
        ["Suggested order", moneyless(reorderUnits)]
      ].map(([label, value]) => `<div class="metric"><span class="muted">${label}</span><strong>${value}</strong></div>`).join("");
    }

    function renderTable(items) {
      document.querySelector("#forecastRows").innerHTML = items.map(item => `
        <tr role="button" tabindex="0" onclick="selectProduct('${item.sku}')">
          <td><strong>${item.name}</strong><br><span class="muted">${item.sku} · ${item.category}</span></td>
          <td>${moneyless(item.stock)}</td>
          <td>${moneyless(item.forecast7d)}</td>
          <td>${moneyless(item.reorderPoint)}</td>
          <td><strong>${moneyless(item.recommendedOrder)}</strong></td>
          <td><span class="status ${item.status}">${labels[item.status]}</span></td>
        </tr>
      `).join("");
    }

    function selectProduct(sku) {
      state.selectedSku = sku;
      renderSelected();
    }

    function renderSelected() {
      const item = state.data.forecasts.find(product => product.sku === state.selectedSku) || state.data.forecasts[0];
      const max = Math.max(...item.forecastDays.map(day => day.forecast));
      const bars = item.forecastDays.map(day => `
        <div class="barWrap">
          <div class="bar" title="${day.date}: ${day.forecast}" style="height:${24 + (day.forecast / max) * 150}px"></div>
          <div class="barLabel">${day.day}<br>${day.forecast}<br>${day.weather}${day.holiday ? "<br>" + day.holiday : ""}</div>
        </div>
      `).join("");
      document.querySelector("#selectedForecast").innerHTML = `
        <p><strong>${item.name}</strong> · ${item.category}</p>
        <p class="muted">Lead time ${item.leadTime} days · projected 7-day demand ${moneyless(item.forecast7d)} units</p>
        <div class="bars">${bars}</div>
      `;
    }

    function renderHeatmap(items) {
      const max = Math.max(...items.flatMap(item => item.forecastDays.map(day => day.forecast)));
      const header = `<div class="heatrow"><strong></strong>${state.data.days.map(day => `<strong class="muted">${day.day}</strong>`).join("")}</div>`;
      const rows = items.map(item => `
        <div class="heatrow">
          <strong>${item.name}</strong>
          ${item.forecastDays.map(day => {
            const intensity = day.forecast / max;
            const color = `rgb(${Math.round(29 + intensity * 150)}, ${Math.round(78 + intensity * 70)}, ${Math.round(216 - intensity * 110)})`;
            return `<div class="cell" style="background:${color}">${day.forecast}</div>`;
          }).join("")}
        </div>
      `).join("");
      document.querySelector("#heatmap").innerHTML = header + rows;
    }

    function renderAlerts(items) {
      const alerts = items.filter(item => item.status !== "healthy");
      document.querySelector("#alerts").innerHTML = alerts.length
        ? alerts.map(item => `
          <div class="alert ${item.status === "stockout-risk" ? "risk" : ""}">
            <strong>${item.name}</strong>
            <p>${labels[item.status]}${item.stockoutDay ? " by " + item.stockoutDay : ""}. Suggested order: ${moneyless(item.recommendedOrder)} units.</p>
          </div>
        `).join("")
        : `<p class="muted">No low-stock alerts for the current filter.</p>`;
    }

    async function predictCustom(event) {
      event.preventDefault();
      const form = new FormData(event.currentTarget);
      const payload = {
        name: form.get("name"),
        stock: Number(form.get("stock")),
        leadTime: Number(form.get("leadTime")),
        weather: form.get("weather"),
        holiday: form.get("holiday") === "true",
        recentSales: String(form.get("recentSales"))
          .split(",")
          .map(value => Number(value.trim()))
          .filter(value => Number.isFinite(value))
      };

      const response = await fetch("/api/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const result = await response.json();
      const max = Math.max(...result.forecastDays.map(day => day.forecast));
      const bars = result.forecastDays.map(day => `
        <div class="barWrap">
          <div class="bar" style="height:${24 + (day.forecast / max) * 130}px"></div>
          <div class="barLabel">${day.day}<br>${day.forecast}</div>
        </div>
      `).join("");

      document.querySelector("#customOutput").innerHTML = `
        <p><strong>${result.name}</strong> · <span class="status ${result.status}">${labels[result.status]}</span></p>
        <p>Predicted 7-day demand: <strong>${moneyless(result.forecast7d)}</strong> units</p>
        <p>Reorder point: <strong>${moneyless(result.reorderPoint)}</strong> · Suggested order: <strong>${moneyless(result.recommendedOrder)}</strong></p>
        <p>Projected stock after 7 days: <strong>${moneyless(result.projectedStock)}</strong></p>
        <div class="bars">${bars}</div>
      `;
    }

    function render() {
      const items = filteredProducts();
      if (!items.find(item => item.sku === state.selectedSku) && items[0]) {
        state.selectedSku = items[0].sku;
      }
      renderMetrics(items);
      renderTable(items);
      renderSelected();
      renderHeatmap(items);
      renderAlerts(items);
    }

    document.querySelector("#customForm").addEventListener("submit", predictCustom);
    loadData();
  </script>
</body>
</html>
"""


class ForecastHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/forecast":
            self.send_json(build_payload())
            return
        if path in {"/", "/index.html"}:
            self.send_html(HTML)
            return
        self.send_error(404)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path != "/api/predict":
            self.send_error(404)
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(length).decode("utf-8")
            payload = json.loads(raw_body or "{}")
            self.send_json(custom_forecast(payload))
        except (json.JSONDecodeError, ValueError, TypeError):
            self.send_error(400, "Invalid prediction input")

    def log_message(self, format: str, *args: Any) -> None:
        return

    def send_json(self, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_html(self, html: str) -> None:
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    ensure_sample_data()
    server = ThreadingHTTPServer((HOST, PORT), ForecastHandler)
    print(f"AI Demand Forecasting dashboard running at http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
