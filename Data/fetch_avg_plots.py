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
from scipy.ndimage import gaussian_filter1d
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

def smooth_data(x, y, sigma=2):
    """Apply Gaussian smoothing and spline interpolation"""
    # First apply Gaussian filter to reduce noise
    y_filtered = gaussian_filter1d(y, sigma=sigma)
    
    # Then apply spline interpolation for visual smoothness
    if len(x) >= 4:
        x_smooth = np.linspace(x.min(), x.max(), 300)
        try:
            spl = make_interp_spline(x, y_filtered, k=3)
            y_smooth = spl(x_smooth)
            return x_smooth, y_smooth
        except Exception as e:
            print(f"Spline failed: {e}, returning filtered data")
            return x, y_filtered
    return x, y_filtered

def get_trend_text(y_values, unit, type_name):
    """Determine trend text based on first and last values"""
    if not len(y_values):
        return ""
    
    start = y_values[0]
    end = y_values[-1]
    diff = end - start
    
    # Thresholds for "Stable"
    thresholds = {
        '°C': 1.0,
        '%': 3.0,
        'hPa': 1.0
    }
    thresh = thresholds.get(unit, 0.5)
    
    status = ""
    if abs(diff) < thresh:
        status = "Stable"
    elif diff > 0:
        status = "Increased"
    else:
        status = "Decreased"
        
    return f"{status} {type_name}"

def create_smooth_plot(x_values, y_values, ylabel, filename, output_dir, is_time=True, 
                      overlay_x=None, overlay_y=None, overlay_label=None, extra_smooth=False,
                      unit="", type_name=""):
    """Create a smooth, centered plot with optional overlay, optimized for E-Paper"""
    if len(x_values) < 2:
        print(f"Not enough data points for {ylabel}")
        return
    
    # E-Paper Resolution: 1448 x 1072 (Landscape)
    dpi = 100
    fig_width = 1448 / dpi
    fig_height = 1072 / dpi
    
    fig, ax = plt.subplots(figsize=(fig_width, fig_height), dpi=dpi)
    
    # Prepare Main Data
    if is_time:
        x = mdates.date2num(x_values)
    else:
        x = np.array(x_values)
    y = np.array(y_values)
    
    # Plot Main Data
    sigma = 5 if extra_smooth else 2
    x_smooth, y_smooth = smooth_data(x, y, sigma=sigma)
    
    # E-Paper Styling: High Contrast
    
    if overlay_x is not None:
        # Main Line (Monthly Avg) - Dashed Dark Gray
        ax.plot(x_smooth, y_smooth, linewidth=4, color='#404040', linestyle='--', label='Monthly Avg', alpha=0.8)
        
        # Prepare Overlay Data (Today)
        if is_time:
             ox = mdates.date2num(overlay_x)
        else:
             ox = np.array(overlay_x)
        oy = np.array(overlay_y)
        
        # Smooth Overlay Data
        ox_smooth, oy_smooth = smooth_data(ox, oy, sigma=4)
        
        # Plot Overlay Line (Today) - Solid Black
        ax.plot(ox_smooth, oy_smooth, linewidth=5, color='black', label='Today')
        
        # Legend - Large Text
        ax.legend(frameon=False, fontsize=24, loc='upper left')
        
        # Trend Annotation (Based on Monthly Avg - Main Line)
        trend = get_trend_text(y_values, unit, type_name)
        if trend:
            # Add text to plot
            plt.text(0.5, 0.95, trend, transform=ax.transAxes, 
                     horizontalalignment='center', verticalalignment='top',
                     fontsize=40, fontweight='bold', color='black')
        
    else:
        # Single Plot (Today's Trend)
        ax.plot(x_smooth, y_smooth, linewidth=5, color='black')

    # Y-Label - Large Text
    ax.set_ylabel(ylabel, fontsize=32, fontweight='bold', labelpad=20)
    
    # Remove x-axis labels
    ax.set_xticklabels([])
    ax.tick_params(axis='x', which='both', length=0)
    
    # Style y-axis - Large Ticks
    ax.tick_params(axis='y', labelsize=24, length=10, width=2)
    
    # Center vertically
    all_y = y_smooth
    if overlay_y is not None:
        all_y = np.concatenate([y, np.array(overlay_y)])
        
    y_min, y_max = all_y.min(), all_y.max()
    y_margin = (y_max - y_min) * 0.2 if y_max != y_min else 1.0
    ax.set_ylim(y_min - y_margin, y_max + y_margin)
    
    # Grid
    ax.grid(True, alpha=0.2, linestyle=':', linewidth=1, color='black')
    
    # Spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_linewidth(2)
    ax.spines['bottom'].set_linewidth(2)
    
    plt.tight_layout()
    
    output_path = os.path.join(output_dir, filename)
    plt.savefig(output_path, dpi=dpi, bbox_inches='tight')
    plt.close()
    print(f"✓ Saved {filename}")

async def main():
    # Output directory
    output_dir = os.path.expanduser("~/Desktop/Code/Clock/fetch_avg/plots")
    os.makedirs(output_dir, exist_ok=True)
    
    # --- Fetch Data ---
    print("Fetching data...")
    today_rows = await fetch_today_data()
    month_rows = await fetch_last_30_days_data()
    
    # Process Today's Data
    today_timestamps = []
    today_temps = []
    today_humis = []
    today_press = []
    today_hours_float = [] 
    
    if today_rows:
        for row in today_rows:
            dt_ist = utc_to_ist(row.timestamp)
            today_timestamps.append(dt_ist)
            today_temps.append(row.temperature)
            today_humis.append(row.humidity)
            today_press.append(row.pressure)
            today_hours_float.append(dt_ist.hour + dt_ist.minute/60 + dt_ist.second/3600)

    # --- Part 1: Today's Trends (Smoother) ---
    print("\n--- Generating Today's Trends ---")
    if today_timestamps:
        create_smooth_plot(today_timestamps, today_temps, 'Temperature (°C)', 'today_temp.png', output_dir, extra_smooth=True)
        create_smooth_plot(today_timestamps, today_humis, 'Humidity (%)', 'today_humi.png', output_dir, extra_smooth=True)
        create_smooth_plot(today_timestamps, today_press, 'Pressure (hPa)', 'today_pressure.png', output_dir, extra_smooth=True)
    else:
        print("No data found for today.")

    # --- Part 2: Monthly Average Trends (Hourly) with Overlay ---
    print("\n--- Generating Monthly Average Trends ---")
    if month_rows:
        hourly_avgs = get_hourly_average(month_rows)
        
        now_ist = utc_to_ist(datetime.now(timezone.utc).replace(tzinfo=None))
        current_hour = now_ist.hour
        
        target_hours = list(range(7, current_hour + 1)) if current_hour >= 7 else []
        
        if not target_hours and current_hour < 7:
             target_hours = list(range(7, 24))

        if target_hours:
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
                create_smooth_plot(plot_hours, avg_temps, 'Avg Temp (°C)', 'month_avg_temp.png', output_dir, 
                                 is_time=False, overlay_x=today_hours_float, overlay_y=today_temps, overlay_label='Today', 
                                 unit='°C', type_name='Temp')
                                 
                create_smooth_plot(plot_hours, avg_humis, 'Avg Humidity (%)', 'month_avg_humi.png', output_dir, 
                                 is_time=False, overlay_x=today_hours_float, overlay_y=today_humis, overlay_label='Today', 
                                 unit='%', type_name='Humidity')
                                 
                create_smooth_plot(plot_hours, avg_press, 'Avg Pressure (hPa)', 'month_avg_pressure.png', output_dir, 
                                 is_time=False, overlay_x=today_hours_float, overlay_y=today_press, overlay_label='Today', 
                                 unit='hPa', type_name='Pressure')
            else:
                print("No average data available for the target hours.")
        else:
            print("No target hours determined.")
    else:
        print("No data found for the last 30 days.")

if __name__ == "__main__":
    asyncio.run(main())
