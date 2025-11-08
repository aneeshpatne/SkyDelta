# Timezone Configuration Summary

## How Timestamps Work in This Project

### Database Storage
- PostgreSQL stores timestamps with timezone (`timestamptz`)
- All timestamps are stored as **IST time but marked as UTC** (e.g., `2025-11-08 16:41:32+00:00` means 4:41 PM IST)
- This is because your system is already in IST timezone

### Data Ingestion (Node.js - Ingest/main.js)
- **System timezone**: IST (Asia/Kolkata)
- When `new Date()` is called, it gets IST time
- Prisma uses the default `@default(now())` which takes system time
- **Result**: IST time is stored directly (not converted)

### Data Retrieval (Python - time-series-plotter.py)
- Uses `datetime.now()` which gives IST time (since system is IST)
- Queries database using IST time values
- **No timezone conversion needed** - everything is IST

### Key Points
1. ✅ System timezone is IST
2. ✅ Database stores times as IST (marked as UTC timezone)
3. ✅ All comparisons and queries work in IST
4. ✅ No conversion needed anywhere

### Files Modified
1. **Ingest/main.js** - Saves data with default timestamp (IST from system)
2. **Data/time-series-plotter.py** - Queries and plots using IST time
3. **Data/revert_timestamps.py** - Script to fix incorrectly converted timestamps
4. **Data/convert_to_ist.py** - ⚠️ DO NOT USE - this was incorrect

### Current Status
- ✅ All 93 existing records have correct IST timestamps
- ✅ New data will be saved with IST timestamps
- ✅ Plotter correctly fetches last 1 hour of data
- ✅ Graphs generated successfully in the `plots/` folder

### Generated Files
The plotter creates a `plots/` folder with:
- `temperature.png` - Temperature over last hour
- `humidity.png` - Humidity over last hour  
- `pressure.png` - Pressure over last hour

All graphs feature:
- Smooth curves (no harsh transitions)
- No X-axis labels
- Y-axis with proper units
- Center-aligned with proper margins
- High resolution (300 DPI)
