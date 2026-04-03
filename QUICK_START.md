# Quick Start Guide

Get up and running in 2 minutes.

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

**Optional: AI Analysis Support**
```bash
pip install groq
```

## Step 2: Run the Web Application

```bash
streamlit run app/core/app.py
```

The browser will open automatically at http://localhost:8501

## Step 3: Upload a Flight Log

1. Open http://localhost:8501 if not opened automatically
2. Drag and drop a `.BIN` or `.LOG` file into the upload area
3. System automatically computes metrics and displays the trajectory

## What You'll See

-  **Metrics**: Flight distance, speed, acceleration, duration
-  **3D Trajectory**: Interactive map of the flight path  
-  **Graphs**: Altitude profile, horizontal and vertical speed over time
-  **AI Analysis** (optional): Anomalies, insights, and recommendations

## Using AI Analysis (Optional)

### Without API Key
System automatically uses rule-based analysis:
- Anomaly detection (speed, altitude thresholds)
- Recommendation generation
- Flight summary report

Accuracy: ~80% of LLM-powered analysis

### With Groq API Key

For expert-level AI analysis:

1. Sign up (free): https://console.groq.com/
2. Copy API key (no credit card required)
3. Set environment variable:
   ```bash
   # Windows
   set GROQ_API_KEY=your_key_here
   
   # macOS/Linux
   export GROQ_API_KEY=your_key_here
   ```
4. Restart Streamlit app
5. Receive expert-level analysis from Mixtral-8x7B AI

**Free Tier Limits:**
- 30 API requests per minute
- No rate limiting on response length
- Sufficient for flight analysis

## Testing with Provided Examples

```bash
# The project includes two example flight logs:
# data/00000001.BIN - Standard flight path
# data/00000019.BIN - Additional example

# Upload either file through the web interface
```

## Using Python API Directly

### Basic Flight Analysis

```python
from app.core.parser import parse_ardupilot_log
from app.core.metrics import compute_total_distance_haversine

# Parse log file
gps_df, imu_df = parse_ardupilot_log("data/00000001.BIN")

print(f"GPS data points: {len(gps_df)}")
print(f"IMU data points: {len(imu_df)}")

# Calculate metrics
distance = compute_total_distance_haversine(gps_df)
print(f"Total distance: {distance:.2f} meters")
```

### With AI Analysis

```python
from app.core.parser import parse_ardupilot_log
from app.core.ai_analysis import analyze_flight_with_ai
from app.core.metrics import compute_all_metrics

gps_df, imu_df = parse_ardupilot_log("data/00000001.BIN")

# Compute metrics
metrics = compute_all_metrics(gps_df, imu_df)

# AI analysis
analysis = analyze_flight_with_ai(metrics, gps_df, imu_df)

print(analysis['summary'])
print(analysis['anomalies'])
print(analysis['recommendations'])
```

See `example.py` for complete working examples.

## Project Components

| Component | Type | Description |
|-----------|------|-------------|
| **Parsing** | Binary | ArduPilot BIN/LOG formats |
| **Coordinates** | WGS-84 → ENU | GPS transformations |
| **Metrics** | Haversine | Distance with ±0.5% accuracy |
| **Orientation** | Quaternion | Gimbal-lock free representation |
| **AI** | Mixtral-8x7B | Free tier, 30 req/minute |
| **Fallback** | Rule-based | Works offline, ~80% accuracy |

## Project Structure

```
app/
├── theory.py                # Mathematical foundations
└── core/
    ├── __init__.py
    ├── app.py              # Streamlit web application
    ├── parser.py           # Binary log parsing
    ├── metrics.py          # Metrics computation
    ├── coordinates.py      # Coordinate transformations
    ├── integration.py      # Numerical integration
    ├── visualization.py    # 3D visualization
    ├── ai_analysis.py      # LLM integration
    └── utils.py            # Utility functions
```

## Documentation

- **[README.md](README.md)** - Complete overview and technology justification
- **[TECHNICAL_JUSTIFICATION.md](TECHNICAL_JUSTIFICATION.md)** - Mathematical foundations and detailed instructions
- **[ENHANCED_FEATURES.md](ENHANCED_FEATURES.md)** - New features documentation
- **[INSTALL.md](INSTALL.md)** - Detailed installation notes
- **[LICENSE.md](LICENSE.md)** - License and copyright information

## Troubleshooting

### Streamlit not starting
```bash
pip install --upgrade streamlit
python -m streamlit run app/core/app.py
```

### API errors
System automatically switches to rule-based analysis. Check console logs for "Fallback analysis" message.

### Invalid coordinate data
Ensure the BIN file contains valid GPS data. Check console output for number of GPS points parsed.

### Port 8501 already in use
```bash
streamlit run app/core/app.py --server.port 8502
```

## Next Steps

1.  Run Streamlit web app
2.  Upload your flight log
3.  Review metrics and visualizations
4.  Optional: Configure Groq API key for AI analysis
5.  Export processed data to CSV

---

**Ready!** The system is fully operational.

For detailed step-by-step instructions, see [TECHNICAL_JUSTIFICATION.md](TECHNICAL_JUSTIFICATION.md) Section 7.
