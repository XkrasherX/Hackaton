"""
Mathematical Foundations and Theory for ArduPilot Log Analysis

This module contains theoretical explanations of the mathematical transformations
and algorithms used throughout the flight log analyzer.

## 1. COORDINATE SYSTEMS AND TRANSFORMATIONS

### 1.1 WGS-84 Geodetic Coordinate System
- Used by GPS receivers worldwide
- Coordinates: (latitude, longitude, altitude)
- Latitude: -90° to +90° (North-South)
- Longitude: -180° to +180° (East-West)
- Altitude: Height above ellipsoid (meters)

### 1.2 ECEF (Earth-Centered, Earth-Fixed) System
Purpose: Cartesian representation of WGS-84
Conversion from WGS-84:
    
    x = (N(φ) + h) * cos(φ) * cos(λ)
    y = (N(φ) + h) * cos(φ) * sin(λ)
    z = (N(φ) * (1 - e²) + h) * sin(φ)
    
Where:
    φ = latitude (radians)
    λ = longitude (radians)
    h = altitude (meters)
    e = eccentricity of WGS-84 ellipsoid
    N(φ) = a / √(1 - e² * sin²(φ))  [radius of curvature]
    a = semi-major axis ≈ 6,378,137 m

### 1.3 ENU (East-North-Up) Local Tangent Plane
Purpose: Local Cartesian system relative to reference point
- East axis: tangent to east
- North axis: tangent to north
- Up axis: radial direction (anti-gravity)

ECEF to ENU rotation matrix R:
    
    R = [ -sin(λ)              cos(λ)              0    ]
        [-sin(φ)cos(λ)   -sin(φ)sin(λ)     cos(φ)    ]
        [ cos(φ)cos(λ)    cos(φ)sin(λ)     sin(φ)    ]
    
The transformation applies R to ECEF deltas:
    [e]   [ΔECEF_x]
    [n] = R * [ΔECEF_y]
    [u]   [ΔECEF_z]

Why ENU?
- Intuitive for local flight analysis
- Altitude as 'Up' component
- Horizontal distance meaningful for trajectory

## 2. DISTANCE CALCULATIONS

### 2.1 Haversine Formula
Purpose: Calculate geodetic distance between two GPS points accounting for Earth's curvature

Formula:
    a = sin²(Δφ/2) + cos(φ₁) * cos(φ₂) * sin²(Δλ/2)
    c = 2 * arctan2(√a, √(1-a))
    d = R * c
    
Where:
    φ₁, φ₂ = latitudes (radians)
    λ₁, λ₂ = longitudes (radians)
    Δφ = φ₂ - φ₁
    Δλ = λ₂ - λ₁
    R = Earth radius ≈ 6,371,000 m

Accuracy:
- ±0.5% for distances < 1000 km
- Assumes spherical Earth (close to WGS-84 for small scales)

Why not use Euclidean distance?
- GPS coordinates are angles, not Cartesian
- Euclidean distance would be meaningless
- Haversine accounts for spherical geometry

### 2.2 Speed Calculation
Horizontal speed = distance / time interval
    v_h[i] = haversine(pos[i-1], pos[i]) / Δt[i]

Vertical speed = altitude change / time interval
    v_v[i] = (alt[i] - alt[i-1]) / Δt[i]

## 3. NUMERICAL INTEGRATION

### 3.1 Trapezoidal Rule
Purpose: Integrate acceleration to obtain velocity

Principle: Approximate integral as sum of trapezoids

    ∫ₐᵇ f(x)dx ≈ Σ(i=1 to n) (f(xᵢ) + f(xᵢ₋₁))/2 * Δx

For velocity from acceleration:
    
    v[i] = v[i-1] + (a[i] + a[i-1])/2 * Δt

Error analysis:
- Truncation error: O(Δt²)  [quadratic in time step]
- Accumulation error: O(n*Δt³) = O((T)²*Δt) where T = total time
- Drift error: Cumulative numerical errors grow with integration time

Why drift is a problem in IMU:
- Small biases in acceleration accumulate over time
- v_error = bias * T  (linear growth)
- position_error = bias * T²/2  (quadratic growth)
- Without GPS correction: Errors become large

Mitigation strategies:
1. High-quality IMU with low bias
2. Sensor fusion with GPS (Kalman filter)
3. Use short integration windows
4. Subtract bias estimate before integration

### 3.2 Why Trapezoidal vs. Simpson's Rule?
Trapezoidal:
- O(Δt²) local error
- Simple implementation
- Adequate precision for most flight analysis
- Good speed/accuracy ratio

Simpson's Rule (O(Δt⁴)):
- Higher accuracy but requires even spacing
- More complex
- Not necessary for flight data (often irregularly sampled)

## 4. ORIENTATION AND ATTITUDE

### 4.1 Why Quaternions Instead of Euler Angles?

Euler Angles (Roll, Pitch, Yaw):
- Intuitive to understand
- 3 numbers per orientation
- **GIMBAL LOCK PROBLEM**: When pitch = ±90°, roll and yaw become indistinguishable
  - Singularity makes small angle changes produce large rotations
  - Causes numerical instability and loss of one DOF
  - Real issue in inverted flights

Quaternions (w, x, y, z):
- 4 numbers (one redundant constraint: w² + x² + y² + z² = 1)
- NO gimbal lock (singularities removed)
- Smooth interpolation (SLERP)
- Efficient composition: q₁ * q₂ (vs. matrix multiplication)
- Natural for integration of angular velocity

Quaternion from angular velocity (ω):
    dq/dt = 0.5 * q * [0, ωₓ, ωᵧ, ωᵤ]
    
Integration (rate form):
    q[i] = q[i-1] + 0.5 * q[i-1] * ω[i] * Δt

From Quaternion to Euler:
    roll = arctan2(2(qw*qx + qy*qz), 1 - 2(qx² + qy²))
    pitch = arcsin(2(qw*qy - qz*qx))
    yaw = arctan2(2(qw*qz + qx*qy), 1 - 2(qy² + qz²))

## 5. ACCELERATION AND FORCES

### 5.1 IMU Acceleration Bias
- IMU measures: a_measured = a_true + a_bias + a_noise
- Bias is nearly constant (but temperature dependent)
- Typical bias: 50-200 mg (0.5-2 m/s² for MEMS IMU)

### 5.2 Acceleration Magnitude
    a_mag = √(ax² + ay² + az²)
    
This combines accelerations in all three body axes.
Note: Includes gravity component if measured in body frame!
    
If body frame:
    a_measured = a_motion + g
    
Where g = 9.81 m/s² (downward in body frame when aircraft is level)

## 6. ALTITUDE GAIN (VERTICAL CLIMB)

### 6.1 Definition
Maximum cumulative altitude gain = max(Σ(positive altitude changes))

Algorithm:
    gain = 0
    max_gain = 0
    for each time step:
        Δh = h[i] - h[i-1]
        if Δh > 0:
            gain += Δh
        max_gain = max(max_gain, gain)

This counts only upward movement, not altitude at end of flight.

### 6.2 Why Not Just (h_max - h_min)?
Because aircraft may climb and descend multiple times:
    Climb 100m, descend 50m, climb 100m
    - max_gain_altitude = 150m ✓
    - h_max - h_min = 100m ✗ (misses middle climb)

## 7. DATA QUALITY AND SOURCES OF ERROR

### 7.1 GPS Errors
- Dilution of Precision (DOP): Geometry-dependent
- Multipath: Reflections from surfaces
- Atmospheric effects: Troposphere, ionosphere delays
- Typical accuracy: ±3-10 meters (without DGPS)

### 7.2 IMU Errors
- Quantization: Discrete measurement steps
- Randomness (Brownian motion): ∝ 1/√f
- Bias instability: Changes slowly over time
- Temperature sensitivity: Affects zero-g bias
- Saturation: Limited dynamic range (typically ±16g for flight)

### 7.3 Integration Drift
- Single integration (velocity): bias * T
- Double integration (position): bias * T²/2
- Grows quadratically over time
- Example: 1 m/s² bias over 100s flight
  - velocity error: 100 m/s (huge!)
  - position error: 5 km (useless)
- Solution: Sensor fusion (Kalman filter) with GPS

## 8. RECOMMENDED FURTHER READING

1. "Understanding the Kalman Filter" - Greg Welch & Gary Bishop
2. "Fundamentals of Inertial Navigation" - Paul Groves
3. "Quaternions and Rotation Sequences" - Jack B. Kuipers
4. NASA Technical Reports on aircraft guidance
5. ArduPilot documentation on Extended Kalman Filter (EKF)

## 9. PRACTICAL IMPLICATIONS

### For Flight Analysis:
1. GPS gives absolute position (drifts < 10m/min)
2. IMU gives motion (drifts rapidly)
3. Fusion needed for accurate long flight paths
4. High-frequency IMU useful for acceleration detection
5. GPS useful for final position verification

### For Log Interpretation:
1. Heights are relative to ellipsoid, not local datum
2. Horizontal speed from GPS may lag actual motion (sampling)
3. Vertical speed from IMU integration unreliable long-term
4. Acceleration spikes may indicate gusts or control inputs
5. Compare multiple flights for calibration insights
"""

import numpy as np
from typing import Tuple


def quaternion_from_euler(roll: float, pitch: float, yaw: float) -> Tuple[float, float, float, float]:
    """
    Convert Euler angles (Roll-Pitch-Yaw) to quaternion.
    
    Theory: Euler angles suffer from gimbal lock at pitch = ±90°.
    Quaternions avoid this singularity while maintaining smooth interpolation.
    
    Args:
        roll: Roll angle in radians (rotation around X axis)
        pitch: Pitch angle in radians (rotation around Y axis)
        yaw: Yaw angle in radians (rotation around Z axis)
        
    Returns:
        Quaternion as (w, x, y, z) where w is scalar part
    """
    cy = np.cos(yaw * 0.5)
    sy = np.sin(yaw * 0.5)
    cp = np.cos(pitch * 0.5)
    sp = np.sin(pitch * 0.5)
    cr = np.cos(roll * 0.5)
    sr = np.sin(roll * 0.5)

    w = cr * cp * cy + sr * sp * sy
    x = sr * cp * cy - cr * sp * sy
    y = cr * sp * cy + sr * cp * sy
    z = cr * cp * sy - sr * sp * cy

    return w, x, y, z


def euler_from_quaternion(w: float, x: float, y: float, z: float) -> Tuple[float, float, float]:
    """
    Convert quaternion to Euler angles.
    
    Note: Converts back to Euler despite gimbal lock issues because they're
    more intuitive for human interpretation. Use quaternions only for calculations.
    
    Args:
        w, x, y, z: Quaternion components (w is scalar)
        
    Returns:
        (roll, pitch, yaw) in radians
    """
    # Roll (X-axis rotation)
    sinr_cosp = 2 * (w * x + y * z)
    cosr_cosp = 1 - 2 * (x * x + y * y)
    roll = np.arctan2(sinr_cosp, cosr_cosp)

    # Pitch (Y-axis rotation)
    sinp = 2 * (w * y - z * x)
    sinp = np.clip(sinp, -1, 1)  # Clamp to avoid numerical errors
    pitch = np.arcsin(sinp)

    # Yaw (Z-axis rotation)
    siny_cosp = 2 * (w * z + x * y)
    cosy_cosp = 1 - 2 * (y * y + z * z)
    yaw = np.arctan2(siny_cosp, cosy_cosp)

    return roll, pitch, yaw


def quaternion_multiply(q1: Tuple, q2: Tuple) -> Tuple:
    """
    Multiply two quaternions.
    
    Theory: Quaternion multiplication represents composition of rotations.
    q1 * q2 means "first rotate by q2, then by q1"
    
    This is more efficient and numerically stable than matrix multiplication.
    
    Args:
        q1: First quaternion (w, x, y, z)
        q2: Second quaternion (w, x, y, z)
        
    Returns:
        Result quaternion (w, x, y, z)
    """
    w1, x1, y1, z1 = q1
    w2, x2, y2, z2 = q2
    
    w = w1*w2 - x1*x2 - y1*y2 - z1*z2
    x = w1*x2 + x1*w2 + y1*z2 - z1*y2
    y = w1*y2 - x1*z2 + y1*w2 + z1*x2
    z = w1*z2 + x1*y2 - y1*x2 + z1*w2
    
    return (w, x, y, z)


def estimate_bias_from_data(acceleration: np.ndarray, stationary_threshold: float = 0.1) -> float:
    """
    Estimate accelerometer bias from flight data.
    
    Theory: When aircraft is stationary or in steady flight, acceleration
    magnitude should be ≈ 9.81 m/s² (gravity). Deviation indicates bias.
    
    Algorithm:
    1. Find periods where motion is minimal (low variance)
    2. Calculate expected vs. measured magnitude
    3. Average the bias over stationary segments
    
    Args:
        acceleration: [N, 3] array of ax, ay, az measurements
        stationary_threshold: Max net acceleration for "stationary"
        
    Returns:
        Estimated bias magnitude in m/s²
    """
    acc_magnitude = np.linalg.norm(acceleration, axis=1)
    
    # Find stationary periods (magnitude near 1g)
    expected_magnitude = 9.81
    deviation = np.abs(acc_magnitude - expected_magnitude)
    
    stationary_mask = deviation < stationary_threshold
    
    if np.sum(stationary_mask) > 0:
        avg_magnitude = np.mean(acc_magnitude[stationary_mask])
        bias = avg_magnitude - expected_magnitude
    else:
        bias = 0.0
    
    return bias
