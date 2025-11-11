import sys
from pathlib import Path
# Add the parent directory to Python path to import generated prisma client
sys.path.insert(0, str(Path(__file__).parent / "generated"))

from prisma import Prisma
import asyncio
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
from collections import defaultdict

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=env_path)

db = Prisma()


async def fetch_last_30_days_data():
    """Fetch weather data from the last 30 days"""
    await db.connect()
    
    # Calculate time 30 days ago
    thirty_days_ago = datetime.now() - timedelta(days=30)
    
    print(f"Fetching data from {thirty_days_ago.strftime('%Y-%m-%d %H:%M:%S')} to {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} IST")
    
    # Query data from the last 30 days, ordered by timestamp
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


def calculate_hourly_averages(rows):
    """Calculate average temp, humidity, and pressure for each hour of the day"""
    hourly_data = defaultdict(lambda: {'temps': [], 'humids': [], 'pressures': []})
    
    for row in rows:
        hour = row.timestamp.hour
        hourly_data[hour]['temps'].append(row.temperature)
        hourly_data[hour]['humids'].append(row.humidity)
        hourly_data[hour]['pressures'].append(row.pressure)
    
    # Calculate averages
    hourly_averages = {}
    for hour in range(24):
        if hour in hourly_data and hourly_data[hour]['temps']:
            hourly_averages[hour] = {
                'avg_temp': sum(hourly_data[hour]['temps']) / len(hourly_data[hour]['temps']),
                'avg_humidity': sum(hourly_data[hour]['humids']) / len(hourly_data[hour]['humids']),
                'avg_pressure': sum(hourly_data[hour]['pressures']) / len(hourly_data[hour]['pressures']),
                'data_points': len(hourly_data[hour]['temps'])
            }
    
    return hourly_averages


async def get_current_readings():
    """Get the most recent weather reading"""
    await db.connect()
    
    # Get the most recent reading
    latest = await db.weather_db_v2.find_first(
        order={
            'timestamp': 'desc'
        }
    )
    
    await db.disconnect()
    return latest


def determine_trend(current_value, historical_avg, metric_name):
    """Determine if current value is trending up, down, or stable"""
    if historical_avg == 0:
        return "No historical data for comparison"
    
    # Calculate percentage difference
    diff = current_value - historical_avg
    percent_diff = (diff / historical_avg) * 100
    
    # Determine trend with threshold of 2% for stability
    if abs(percent_diff) < 2:
        trend = "STABLE"
        symbol = "→"
    elif diff > 0:
        trend = "INCREASING"
        symbol = "↑"
    else:
        trend = "DECREASING"
        symbol = "↓"
    
    return f"{symbol} {trend} ({diff:+.2f} | {percent_diff:+.1f}%)"


async def main():
    print("=" * 80)
    print("HOURLY WEATHER TREND ANALYZER")
    print("=" * 80)
    
    # Fetch historical data
    print("\n[1/3] Fetching historical data from last 30 days...")
    rows = await fetch_last_30_days_data()
    
    if not rows:
        print("❌ No historical data found for the last 30 days.")
        return
    
    print(f"✓ Found {len(rows)} data points")
    
    # Calculate hourly averages
    print("\n[2/3] Calculating hourly averages...")
    hourly_averages = calculate_hourly_averages(rows)
    
    if not hourly_averages:
        print("❌ No hourly averages could be calculated.")
        return
    
    print(f"✓ Calculated averages for {len(hourly_averages)} hours")
    
    # Get current readings
    print("\n[3/3] Fetching current readings...")
    current = await get_current_readings()
    
    if not current:
        print("❌ No current reading available.")
        return
    
    print(f"✓ Latest reading from {current.timestamp.strftime('%Y-%m-%d %H:%M:%S')} IST")
    
    # Display hourly averages
    print("\n" + "=" * 80)
    print("HOURLY AVERAGES (Last 30 Days)")
    print("=" * 80)
    print(f"{'Hour':<6} {'Avg Temp (°C)':<15} {'Avg Humidity (%)':<18} {'Avg Pressure (hPa)':<20} {'Data Points':<12}")
    print("-" * 80)
    
    for hour in sorted(hourly_averages.keys()):
        data = hourly_averages[hour]
        print(f"{hour:02d}:00  {data['avg_temp']:>13.2f}  {data['avg_humidity']:>16.2f}  {data['avg_pressure']:>18.2f}  {data['data_points']:>11}")
    
    # Get current hour's historical average
    current_hour = current.timestamp.hour
    
    print("\n" + "=" * 80)
    print("CURRENT CONDITIONS & TREND ANALYSIS")
    print("=" * 80)
    print(f"Current Time: {current.timestamp.strftime('%Y-%m-%d %H:%M:%S')} IST (Hour: {current_hour:02d}:00)")
    print("-" * 80)
    
    if current_hour in hourly_averages:
        hist_data = hourly_averages[current_hour]
        
        print(f"\n📊 Temperature:")
        print(f"   Current:    {current.temperature:.2f}°C")
        print(f"   Historical: {hist_data['avg_temp']:.2f}°C (avg for hour {current_hour:02d}:00)")
        print(f"   Trend:      {determine_trend(current.temperature, hist_data['avg_temp'], 'Temperature')}")
        
        print(f"\n💧 Humidity:")
        print(f"   Current:    {current.humidity:.2f}%")
        print(f"   Historical: {hist_data['avg_humidity']:.2f}% (avg for hour {current_hour:02d}:00)")
        print(f"   Trend:      {determine_trend(current.humidity, hist_data['avg_humidity'], 'Humidity')}")
        
        print(f"\n🌡️  Pressure:")
        print(f"   Current:    {current.pressure:.2f} hPa")
        print(f"   Historical: {hist_data['avg_pressure']:.2f} hPa (avg for hour {current_hour:02d}:00)")
        print(f"   Trend:      {determine_trend(current.pressure, hist_data['avg_pressure'], 'Pressure')}")
        
        print(f"\n📈 Based on {hist_data['data_points']} historical readings for this hour")
    else:
        print(f"\n⚠️  No historical data available for hour {current_hour:02d}:00")
        print(f"\nCurrent Readings:")
        print(f"   Temperature: {current.temperature:.2f}°C")
        print(f"   Humidity:    {current.humidity:.2f}%")
        print(f"   Pressure:    {current.pressure:.2f} hPa")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
