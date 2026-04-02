"""
AI Assistant for Flight Analysis using LLM.

This module uses Groq API (free tier available) to analyze flight characteristics
and generate insights about flight patterns, anomalies, and recommendations.

Groq API: https://console.groq.com/
- Free tier: 30 requests per minute
- No credit card required
- Fast inference with Mixtral-8x7B model

Setup:
    1. Get free API key from https://console.groq.com/
    2. Set environment variable: GROQ_API_KEY=your_key_here
    3. Or pass api_key parameter directly
"""

import os
import json
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


def analyze_flight_with_ai(
    metrics: Dict,
    gps_df,
    imu_df,
    api_key: Optional[str] = None
) -> Dict[str, str]:
    """
    Use LLM (Groq) to analyze flight characteristics and generate insights.
    
    Args:
        metrics: Dictionary with computed flight metrics
        gps_df: GPS DataFrame
        imu_df: IMU DataFrame
        api_key: Groq API key (can also use GROQ_API_KEY env var)
        
    Returns:
        Dictionary with 'summary', 'anomalies', 'recommendations' keys
    """
    
    # Try to get API key from env or parameter
    if api_key is None:
        api_key = os.getenv("GROQ_API_KEY")
    
    if not api_key:
        logger.warning("GROQ_API_KEY not found. Using fallback analysis.")
        return fallback_flight_analysis(metrics, gps_df, imu_df)
    
    try:
        from groq import Groq
    except ImportError:
        logger.warning("groq package not installed. Install with: pip install groq")
        return fallback_flight_analysis(metrics, gps_df, imu_df)
    
    try:
        client = Groq(api_key=api_key)
        
        # Prepare flight data summary
        flight_summary = prepare_flight_summary(metrics, gps_df, imu_df)
        
        # Create prompt for LLM
        prompt = f"""Analyze this drone/aircraft flight data and provide insights:

{flight_summary}

Please provide:
1. SUMMARY: 2-3 sentence overview of the flight characteristics
2. ANOMALIES: Any unusual patterns or concerning values (e.g., rapid altitude loss, speed spikes)
3. RECOMMENDATIONS: Suggestions for improvement or areas of concern

Format your response as JSON with keys: "summary", "anomalies", "recommendations"
"""
        
        message = client.messages.create(
            model="mixtral-8x7b-32768",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        
        response_text = message.content[0].text
        
        # Try to parse as JSON
        try:
            result = json.loads(response_text)
        except json.JSONDecodeError:
            # Fallback: extract sections from text
            result = extract_analysis_from_text(response_text)
        
        return result
        
    except Exception as e:
        logger.error(f"Error calling Groq API: {e}")
        return fallback_flight_analysis(metrics, gps_df, imu_df)


def prepare_flight_summary(metrics: Dict, gps_df, imu_df) -> str:
    """Prepare formatted flight data for AI analysis."""
    
    import numpy as np
    
    summary_lines = [
        "FLIGHT METRICS:",
        f"  Duration: {metrics.get('Flight Duration (s)', 0):.1f} seconds",
        f"  Total Distance: {metrics.get('Total Distance', 0):.2f} meters",
        f"  Max Horizontal Speed: {metrics.get('Max Horizontal Speed', 0):.2f} m/s",
        f"  Max Vertical Speed: {metrics.get('Max Vertical Speed', 0):.2f} m/s",
        f"  Max Acceleration: {metrics.get('Max Acceleration', 0):.2f} m/s²",
        f"  Max Altitude Gain: {metrics.get('Max Altitude Gain', 0):.2f} m",
        "",
        "FLIGHT ENVIRONMENT:",
        f"  Data Points: {len(gps_df)} GPS samples, {len(imu_df)} IMU samples",
    ]
    
    if not gps_df.empty:
        summary_lines.extend([
            f"  Altitude Range: {gps_df['alt'].min():.2f} - {gps_df['alt'].max():.2f} m",
            f"  Mean Altitude: {gps_df['alt'].mean():.2f} m",
        ])
    
    if not imu_df.empty:
        summary_lines.extend([
            f"  Mean Acceleration: {np.mean(np.sqrt(imu_df['acc_x']**2 + imu_df['acc_y']**2 + imu_df['acc_z']**2)):.2f} m/s²",
        ])
    
    return "\n".join(summary_lines)


def extract_analysis_from_text(text: str) -> Dict[str, str]:
    """Extract analysis sections from unstructured text response."""
    
    result = {
        "summary": "Unable to parse detailed analysis.",
        "anomalies": "No significant anomalies detected.",
        "recommendations": "Continue normal operations."
    }
    
    # Simple text parsing
    text_upper = text.upper()
    
    sections = {
        "summary": ("SUMMARY", "ANOMALIES"),
        "anomalies": ("ANOMALIES", "RECOMMENDATIONS"),
        "recommendations": ("RECOMMENDATIONS", "QUESTIONS")
    }
    
    for key, (start_marker, end_marker) in sections.items():
        start_idx = text_upper.find(start_marker)
        end_idx = text_upper.find(end_marker)
        
        if start_idx != -1:
            start_idx += len(start_marker)
            if end_idx == -1:
                end_idx = len(text)
            
            extracted = text[start_idx:end_idx].strip()
            # Clean up markdown formatting
            extracted = extracted.replace("**", "").replace("## ", "").replace("# ", "")
            
            if extracted:
                result[key] = extracted[:500]  # Limit to 500 chars
    
    return result


def fallback_flight_analysis(metrics: Dict, gps_df, imu_df) -> Dict[str, str]:
    """
    Fallback analysis without LLM (when API not available).
    Uses rule-based heuristics for flight assessment.
    """
    
    duration = metrics.get('Flight Duration (s)', 0)
    max_h_speed = metrics.get('Max Horizontal Speed', 0)
    max_v_speed = metrics.get('Max Vertical Speed', 0)
    max_acc = metrics.get('Max Acceleration', 0)
    max_alt_gain = metrics.get('Max Altitude Gain', 0)
    total_dist = metrics.get('Total Distance', 0)
    
    # Generate summary
    summary_parts = []
    if duration < 5:
        summary_parts.append("Very short flight duration")
    elif duration < 60:
        summary_parts.append("Short flight")
    else:
        summary_parts.append(f"Flight lasted {duration/60:.1f} minutes")
    
    if max_h_speed > 0:
        summary_parts.append(f"reaching speeds up to {max_h_speed:.1f} m/s")
    
    summary = ". ".join(summary_parts) + "."
    
    # Detect anomalies
    anomalies = []
    
    if max_h_speed > 50:
        anomalies.append(f"High horizontal speed ({max_h_speed:.1f} m/s) - verify wind or control inputs")
    
    if max_v_speed > 20:
        anomalies.append(f"High vertical speed ({max_v_speed:.1f} m/s) - steep climb or rapid descent")
    
    if max_acc > 50:
        anomalies.append(f"High acceleration ({max_acc:.1f} m/s²) - may indicate gusts or aggressive maneuvers")
    
    if max_acc < 10 and len(imu_df) > 10:
        anomalies.append("Low acceleration magnitude - check for IMU sensor issues")
    
    if total_dist == 0 and max_h_speed == 0:
        anomalies.append("No horizontal movement detected - stationary flight or GPS issues")
    
    anomalies_text = "\n".join(f"• {a}" for a in anomalies) if anomalies else "No major anomalies detected"
    
    # Recommendations
    recommendations = []
    
    if max_acc > 40:
        recommendations.append("Consider smoother control inputs to reduce vibration and mechanical stress")
    
    if duration > 30:
        recommendations.append("Long flight detected - verify battery performance and thermal stability")
    
    if max_v_speed > 10:
        recommendations.append("Monitor for wind conditions during vertical maneuvers")
    
    recommendations_text = "\n".join(f"• {r}" for r in recommendations) if recommendations else "Flight appears normal. No specific issues detected."
    
    return {
        "summary": summary,
        "anomalies": anomalies_text,
        "recommendations": recommendations_text
    }


def format_analysis_for_display(analysis: Dict[str, str]) -> str:
    """Format AI analysis for pretty display."""
    
    output = []
    output.append("\n" + "="*70)
    output.append("AI FLIGHT ANALYSIS")
    output.append("="*70)
    
    output.append("\n📋 SUMMARY:")
    output.append("-" * 70)
    output.append(analysis.get('summary', ''))
    
    output.append("\n⚠️  ANOMALIES DETECTED:")
    output.append("-" * 70)
    output.append(analysis.get('anomalies', ''))
    
    output.append("\n💡 RECOMMENDATIONS:")
    output.append("-" * 70)
    output.append(analysis.get('recommendations', ''))
    
    output.append("\n" + "="*70)
    
    return "\n".join(output)
