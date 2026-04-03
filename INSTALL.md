# Installation and Setup Guide

## System Requirements

- Python 3.8 or higher
- Windows, macOS, or Linux
- At least 2GB of disk space (for dependencies)
- 4GB of RAM (recommended)

## Step 1: Clone/Setup Project

```bash
cd d:\PyCharm\PyCharmProjects
```

## Step 2: Create Virtual Environment

### On Windows (PowerShell):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### On macOS/Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

## Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

Or manually:
```bash
pip install pandas numpy pymavlink pyproj plotly scipy streamlit
```

## Step 4: Verify Installation

Test the installation:
```bash
python -c "import app.core; print('Installation successful!')"
```

## Running the Application

### Option 1: CLI Interface

Analyze a single log file:
```bash
python app/main.py data/00000001.BIN
```

Outputs:
- Console summary report
- `00000001_trajectory.html` - 3D visualization
- `00000001_processed.csv` - Processed GPS data

### Option 2: Web Interface (Streamlit)

Start the web application:
```bash
streamlit run app/core/app.py
```

Then open in browser: `http://localhost:8501`

Features:
- Drag-and-drop file upload
- Real-time metric computation
- Interactive 3D visualization
- CSV export

### Option 3: Example Script

Run the example analysis:
```bash
python example.py data/00000001.BIN
```

## Testing

Run the test suite:
```bash
python << 'EOF'
import sys
import os
sys.path.insert(0, 'd:/PyCharm/PyCharmProjects')

from app.core import *

log_file = 'd:/PyCharm/PyCharmProjects/data/00000001.BIN'
gps_df, imu_df = parse_ardupilot_log(log_file)

print(f"✓ Parsed {len(gps_df)} GPS and {len(imu_df)} IMU records")
print("✓ All modules loaded successfully!")
EOF
```

## Troubleshooting

### Missing pymavlink module
```bash
pip install pymavlink --upgrade
```

### Issues with pyproj (coordinate transformation)
```bash
pip install pyproj --upgrade
pip install proj-data
```

### Streamlit not starting
```bash
streamlit cache clear
streamlit run app/core/app.py --logger.level=debug
```

### Memory issues with large log files
- Close other applications
- Use CLI interface instead of Streamlit (lower memory usage)
- Process smaller log file chunks

## File Structure After Installation

```
d:/PyCharm/PyCharmProjects/
├── .venv/                          # Virtual environment
│   └── Scripts/
│       └── python.exe, pip.exe     # Python executables
├── app/
│   ├── theory.py                 # Mathematical foundations
│   └── core/
│       ├── __init__.py
│       ├── app.py               # Streamlit web app
│       ├── parser.py            # Binary log parsing
│       ├── coordinates.py       # Coordinate transformations
│       ├── metrics.py           # Flight metrics computation
│       ├── integration.py       # Numerical integration
│       ├── visualization.py     # 3D visualization
│       ├── utils.py             # Utility functions
│       └── ai_analysis.py       # LLM integration
├── data/
│   ├── 00000001.BIN             # Example flight log
│   └── 00000019.BIN             # Example flight log
├── requirements.txt              # Python dependencies
├── README.md                     # This file
├── QUICK_START.md               # 2-minute quickstart
├── INSTALL.md                   # Installation instructions
├── TECHNICAL_JUSTIFICATION.md    # Technology choices & math (NEW!)
├── ENHANCED_FEATURES.md          # New features documentation
└── example.py                    # Example script
├── .streamlit/
│   └── config.toml                # Streamlit configuration
├── example.py                     # Example usage script
└── .gitignore                     # Git ignore rules
```

## Next Steps

1. Read [README.md](README.md) for detailed documentation
2. Try the example: `python example.py data/00000001.BIN`
3. Explore the Streamlit UI: `streamlit run app/core/app.py`
4. Check out the test suite in each module

## Support

For issues and questions:
1. Check the README.md for more details
2. Review example.py for usage patterns
3. Check the logging output for error messages
4. Verify all dependencies are installed: `pip list | grep -E "pandas|numpy|pymavlink|plotly"`

## Performance Tips

- **Faster processing**: Use CLI interface instead of Streamlit
- **Lower memory**: Process logs locally, not on remote storage
- **Better visualization**: Use modern browser (Chrome, Firefox, Edge)
- **Development**: Keep venv activated during work

## Contributing

To add new features:
1. Add functions to appropriate module in `app/core/`
2. Update `app/core/__init__.py` with exports
3. Add tests in the function docstrings
4. Update documentation in README.md

## License

MIT License - Free to use and distribute
