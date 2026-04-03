# License and Copyright

## ArduPilot Flight Log Analyzer

**Copyright © 2026 Team of Danylo Chemerys, Maksim Yakymovych, Nataliia Oleskiv**

All rights reserved.

---

## MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

### The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

### THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

---

## Third-Party Credits

This project includes and depends on the following open-source libraries. We gratefully acknowledge their creators and contributors:

### Data Processing
- **pandas** - https://pandas.pydata.org/
  - License: BSD 3-Clause License
  - Copyright © 2008-2024, AQR Capital Management, LLC, Lambda Foundry, Inc. and PyData Development Team

- **NumPy** - https://numpy.org/
  - License: BSD License
  - Copyright © 2005-2024, NumPy Developers

### Flight Log Parsing
- **pymavlink** - https://github.com/ArduPilot/pymavlink
  - License: LGPL v3
  - Copyright © ArduPilot Project Contributors

### Coordinate Transformations
- **pyproj** - https://proj.org/
  - License: MIT License
  - Copyright © Kartverket, Lantmäteriet, NLS, OS, NRCan, GeoGratis contributors

### Visualization
- **Plotly** - https://plotly.com/
  - License: MIT License
  - Copyright © 2016-2024, Plotly, Inc.

- **Streamlit** - https://streamlit.io/
  - License: Apache License 2.0
  - Copyright © Streamlit, Inc.

### Scientific Computing
- **SciPy** - https://scipy.org/
  - License: BSD License
  - Copyright © 2001-2024, SciPy Developers and NumFOCUS

### AI Integration
- **Groq** - https://console.groq.com/
  - License: Groq Terms of Service
  - Copyright © Groq, Inc.

---

## Mathematical Foundations

The mathematical implementations in this project are based on peer-reviewed research and industry standards:

1. **Coordinate Transformations**
   - WGS-84 to ECEF: Based on NIMA TR8350.2 (National Imagery and Mapping Agency Standards)
   - ECEF to ENU: Based on Wikipedia Geographic Coordinate System article and standard geodetic literature

2. **Haversine Formula**
   - Reference: R. W. Sinnott, "Virtues of the Haversine", Sky and Telescope, 1984
   - Provides accurate great-circle distance calculation on spheroid Earth models

3. **Numerical Integration**
   - Trapezoidal Rule: Standard numerical analysis method (Press et al., Numerical Recipes)
   - Error analysis: Standard computational mathematics references

4. **Quaternion Representation**
   - Based on Shoemake, K. "Animating Rotation with Quaternion Curves" (SIGGRAPH 1985)
   - Addresses gimbal lock problem in flight attitude representation

---

## Data Privacy

This application processes flight telemetry data locally on your machine. No data is transmitted to external servers unless you explicitly:

1. Enable the Groq API integration
2. Configure a custom API endpoint

When using Groq AI Analysis:
- Flight metrics and summaries are sent to Groq servers
- Data is processed according to Groq Terms of Service: https://console.groq.com/
- No raw GPS coordinates are transmitted; only aggregated metrics are used

---

## Trademark Notices

- **ArduPilot** is a trademark of the ArduPilot Project
- **Streamlit** is a trademark of Streamlit, Inc.
- **Groq** is a trademark of Groq, Inc.
- Other trademarks mentioned are property of their respective owners

---

## Contributing

By submitting contributions to this project, you agree that:

1. Your work may be distributed under the same MIT License
2. You have the legal right to grant such license
3. You retain copyright to your individual contributions
4. Your contributions will be attributed appropriately

---

## Distribution

This software may be freely distributed under the terms of the MIT License. No warranty or support is implied or provided.

---

## Version Information

- **Project Version**: 1.0.0
- **Last Updated**: April 2026
- **License Version**: MIT License

---

## Full License Text

```
MIT License

Copyright (c) 2026 Team of Danylo Chemerys, Maksim Yakymovych, Nataliia Oleskiv

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## Questions?

For license-related questions, please refer to the main project documentation or contact the project maintainers.

For third-party library licenses, refer to their respective repositories:
- pandas: https://github.com/pandas-dev/pandas
- NumPy: https://github.com/numpy/numpy
- pymavlink: https://github.com/ArduPilot/pymavlink
- pyproj: https://github.com/pyproj4/pyproj
- Plotly: https://github.com/plotly/plotly.py
- Streamlit: https://github.com/streamlit/streamlit
- SciPy: https://github.com/scipy/scipy
