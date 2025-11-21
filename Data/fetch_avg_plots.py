import sys
from pathlib import Path
# Add the parent directory to Python path to import generated prisma client
sys.path.insert(0, str(Path(__file__).parent / "generated"))

from prisma import Prisma
import asyncio
from dotenv import load_dotenv
import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta, timezone
import numpy as np
from scipy.interpolate import make_interp_spline
from collections import defaultdict

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=env_path)

db = Prisma()

# IST Offset
IST_OFFSET = timedelta(hours=5, minutes=30)

def utc_to_ist(dt):
    """Convert UTC datetime to IST"""
    return dt + IST_OFFSET

async def fetch_today_data():
    """Fetch weather data from 7 AM IST today to now"""
    await db.connect()
    
    now_utc = datetime.now(timezone.utc).replace(tzinfo=None) # Prisma returns naive UTC
    now_ist = utc_to_ist(now_utc)
    
    # Today 7 AM IST in UTC
    today_7am_ist = now_ist.replace(hour=7, minute=0, second=0, microsecond=0)
    today_7am_utc = today_7am_ist - IST_OFFSET
    
    print(f"Fetching today's data from {today_7am_utc} UTC (7 AM IST) to now")
    
    rows = await db.weather_db_v2.find_many(
        where={
            'timestamp': {
                'gte': today_7am_utc
            }
        },
        order={
            'timestamp': 'asc'
        }
    )
    
    await db.disconnect()
    return rows

async def fetch_last_30_days_data():
    """Fetch weather data from the last 30 days"""
    await db.connect()
    
    # 30 days ago
    thirty_days_ago = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=30)
    
    print(f"Fetching last 30 days data from {thirty_days_ago}")
    
    rows = await db.weather_db_v2.find_many(
        where={
            'timestamp': {
                'gte': thirty_days_ago
            }
        },
        order={
            'timestamp': 'asc'
        }
    )
    
    await db.disconnect()
    return rows

def get_hourly_average(data):
    """Calculate hourly averages from data (logic from hourly-trends.py)"""
    avg = defaultdict(lambda : {"temp" :[], "humidity":[], "pressure": []})
    for d in data:
        # Convert to IST for hour grouping
        dt_ist = utc_to_ist(d.timestamp)
        hour = dt_ist.hour
        avg[hour]["temp"].append(d.temperature)
        avg[hour]["humidity"].append(d.humidity)
        avg[hour]["pressure"].append(d.pressure)
        
    hourly_avg = {}
    for hour in range(24):
        if hour in avg and avg[hour]["temp"]:
            hourly_avg[hour] = {
                "avg_temp" : sum(avg[hour]["temp"]) / len(avg[hour]["temp"]),
                "avg_humidity" :sum(avg[hour]["humidity"]) / len(avg[hour]["humidity"]),
                "avg_pressure" : sum(avg[hour]["pressure"]) / len(avg[hour]["pressure"]),
            }
    return hourly_avg

def create_smooth_plot(x_values, y_values, ylabel, filename, output_dir, is_time=True):
    """Create a smooth, centered plot"""
    if len(x_values) < 2:
        print(f"Not enough data points for {ylabel}")
        return
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    if is_time:
        x = mdates.date2num(x_values)
    else:
        x = np.array(x_values)
        
    y = np.array(y_values)
    
    # Smooth curve
    if len(x) >= 4:
        x_smooth = np.linspace(x.min(), x.max(), 300)
        spl = make_interp_spline(x, y, k=min(3, len(x)-1))
        y_smooth = spl(x_smooth)
        ax.plot(x_smooth, y_smooth, linewidth=2.5, color='#2E86AB', alpha=0.9)
    else:
        ax.plot(x, y, linewidth=2.5, color='#2E86AB', alpha=0.9, marker='o')
    
    ax.set_ylabel(ylabel, fontsize=12, fontweight='bold')
    
    # Remove x-axis labels
    ax.set_xticklabels([])
    ax.tick_params(axis='x', which='both', length=0)
    
    # Style y-axis
    ax.tick_params(axis='y', labelsize=10)
    
    # Center vertically
    y_margin = (y.max() - y.min()) * 0.15 if y.max() != y.min() else 1.0
    ax.set_ylim(y.min() - y_margin, y.max() + y_margin)
    
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    
    output_path = os.path.join(output_dir, filename)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✓ Saved {filename}")

async def main():
    # Output directory
    output_dir = os.path.expanduser("~/code/e-paper/fetch_avg")
    os.makedirs(output_dir, exist_ok=True)
    
    # --- Part 1: Today's Trends (7 AM to Now) ---
    print("\n--- Generating Today's Trends ---")
    today_rows = await fetch_today_data()
    
    if today_rows:
        # Convert timestamps to IST
        timestamps = [utc_to_ist(row.timestamp) for row in today_rows]
        temps = [row.temperature for row in today_rows]
        humis = [row.humidity for row in today_rows]
        press = [row.pressure for row in today_rows]
        
        create_smooth_plot(timestamps, temps, 'Temperature (°C)', 'today_temp.png', output_dir)
        create_smooth_plot(timestamps, humis, 'Humidity (%)', 'today_humi.png', output_dir)
        create_smooth_plot(timestamps, press, 'Pressure (hPa)', 'today_pressure.png', output_dir)
    else:
        print("No data found for today (since 7 AM IST).")

    # --- Part 2: Monthly Average Trends (Hourly) ---
    print("\n--- Generating Monthly Average Trends ---")
    month_rows = await fetch_last_30_days_data()
    
    if month_rows:
        hourly_avgs = get_hourly_average(month_rows)
        
        # Filter for hours from 7 AM to current hour
        now_ist = utc_to_ist(datetime.now(timezone.utc).replace(tzinfo=None))
        current_hour = now_ist.hour
        
        # If current time is before 7 AM, show 7 AM to 23 PM (or just return empty if strictly 7am-now)
        # Assuming the user wants 7 AM to Now. If Now < 7 AM, this range is empty.
        # Let's handle the case where we might cross midnight or just show available hours.
        # User said "7 am to to the time".
        
        target_hours = []
        if current_hour >= 7:
            target_hours = list(range(7, current_hour + 1))
        else:
            # It's early morning, maybe show yesterday's 7am-23pm? 
            # Or just show nothing? Let's assume we show up to current hour even if it wraps?
            # Actually, "7 am to current time" implies a single day span. 
            # If it's 3 AM, 7 AM hasn't happened yet today.
            # But this is "Monthly Avg". So we can show 7 AM to 3 AM (next day)?
            # Let's stick to 7 AM to Current Hour. If Current Hour < 7, we probably shouldn't plot anything or plot full day?
            # Let's assume standard day 7 AM to Current Hour. If < 7, maybe just 7-23?
            # For safety, if current_hour < 7, let's just show 7-23 (full day avg) or warn.
            # But usually this script runs during the day.
            target_hours = list(range(7, current_hour + 1)) if current_hour >= 7 else []
            
        if not target_hours and current_hour < 7:
             print("Current time is before 7 AM. Showing full day averages (7-23).")
             target_hours = list(range(7, 24))

        if target_hours:
            # Extract data for these hours
            plot_hours = []
            avg_temps = []
            avg_humis = []
            avg_press = []
            
            for h in target_hours:
                if h in hourly_avgs:
                    plot_hours.append(h)
                    avg_temps.append(hourly_avgs[h]['avg_temp'])
                    avg_humis.append(hourly_avgs[h]['avg_humidity'])
                    avg_press.append(hourly_avgs[h]['avg_pressure'])
            
            if plot_hours:
                # Use hours as x-axis
                create_smooth_plot(plot_hours, avg_temps, 'Avg Temp (°C)', 'month_avg_temp.png', output_dir, is_time=False)
                create_smooth_plot(plot_hours, avg_humis, 'Avg Humidity (%)', 'month_avg_humi.png', output_dir, is_time=False)
                create_smooth_plot(plot_hours, avg_press, 'Avg Pressure (hPa)', 'month_avg_pressure.png', output_dir, is_time=False)
            else:
                print("No average data available for the target hours.")
        else:
            print("No target hours determined.")
    else:
        print("No data found for the last 30 days.")

if __name__ == "__main__":
    asyncio.run(main())
