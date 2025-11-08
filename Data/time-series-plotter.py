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
from datetime import datetime, timedelta
import numpy as np
from scipy.interpolate import make_interp_spline

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=env_path)

db = Prisma()


async def fetch_last_hour_data():
    """Fetch weather data from the last hour"""
    await db.connect()
    
    # Calculate time 1 hour ago (system time is IST, DB stores as UTC but we treat it as IST)
    one_hour_ago = datetime.now() - timedelta(hours=1)
    
    print(f"Fetching data from {one_hour_ago.strftime('%Y-%m-%d %H:%M:%S')} to {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} IST")
    
    # Query data from the last hour, ordered by timestamp
    rows = await db.weather_db_v2.find_many(
        where={
            'timestamp': {
                'gte': one_hour_ago
            }
        },
        order={
            'timestamp': 'asc'
        }
    )
    
    await db.disconnect()
    return rows


def create_smooth_plot(timestamps, values, ylabel, filename, output_dir):
    """Create a smooth, centered plot for the given data"""
    if len(timestamps) < 2:
        print(f"Not enough data points for {ylabel}")
        return
    
    # Create figure with specific size
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Convert timestamps to matplotlib format
    x = mdates.date2num(timestamps)
    y = np.array(values)
    
    # Create smooth curve using spline interpolation if we have enough points
    if len(x) >= 4:
        # Create more points for smoother curve
        x_smooth = np.linspace(x.min(), x.max(), 300)
        
        # Use cubic spline interpolation for smoothness
        spl = make_interp_spline(x, y, k=min(3, len(x)-1))
        y_smooth = spl(x_smooth)
        
        # Plot smooth line
        ax.plot(x_smooth, y_smooth, linewidth=2.5, color='#2E86AB', alpha=0.9)
    else:
        # Not enough points for spline, use regular plot
        ax.plot(x, y, linewidth=2.5, color='#2E86AB', alpha=0.9, marker='o')
    
    # Set y-axis label
    ax.set_ylabel(ylabel, fontsize=12, fontweight='bold')
    
    # Remove x-axis labels as requested
    ax.set_xticklabels([])
    ax.tick_params(axis='x', which='both', length=0)
    
    # Style the y-axis
    ax.tick_params(axis='y', labelsize=10)
    
    # Add padding to y-axis to center the graph horizontally (vertically in the plot area)
    y_margin = (y.max() - y.min()) * 0.15
    ax.set_ylim(y.min() - y_margin, y.max() + y_margin)
    
    # Add grid for better readability
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
    
    # Remove top and right spines for cleaner look
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    # Adjust layout to prevent label cutoff
    plt.tight_layout()
    
    # Save the plot
    output_path = os.path.join(output_dir, filename)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✓ Saved {filename}")


async def main():
    # Create output directory
    output_dir = os.path.join(os.path.dirname(__file__), 'plots')
    os.makedirs(output_dir, exist_ok=True)
    
    print("Fetching data from the last hour...")
    rows = await fetch_last_hour_data()
    
    if not rows:
        print("No data found for the last hour.")
        return
    
    print(f"Found {len(rows)} data points")
    
    # Extract data
    timestamps = [row.timestamp for row in rows]
    temperatures = [row.temperature for row in rows]
    humidities = [row.humidity for row in rows]
    pressures = [row.pressure for row in rows]
    
    # Create plots
    print("\nGenerating plots...")
    create_smooth_plot(timestamps, temperatures, 'Temperature (°C)', 'temperature.png', output_dir)
    create_smooth_plot(timestamps, humidities, 'Humidity (%)', 'humidity.png', output_dir)
    create_smooth_plot(timestamps, pressures, 'Pressure (hPa)', 'pressure.png', output_dir)
    
    print(f"\n✓ All plots saved to: {output_dir}")


if __name__ == "__main__":
    asyncio.run(main())
