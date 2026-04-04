"""
AI Assistant for Flight Analysis using LLM (Groq)
"""

import os
import json
import logging
from typing import Dict, Optional, Any

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


# =========================
# Configuration constants
# =========================

MAX_SAFE_H_SPEED = 50.0
MAX_SAFE_V_SPEED = 20.0
MAX_SAFE_ACC = 50.0
MIN_EXPECTED_ACC = 10.0

LLM_MODEL = "mixtral-8x7b-32768"
LLM_MAX_TOKENS = 1024


# =========================
# Main Orchestrator
# =========================

def analyze_flight_with_ai(
    metrics: Dict[str, float],
    gps_df: pd.DataFrame,
    imu_df: pd.DataFrame,
    api_key: Optional[str] = None
) -> Dict[str, str]:


    api_key = api_key or os.getenv("GROQ_API_KEY")

    if not api_key:
        logger.warning("GROQ_API_KEY not found. Using fallback analysis.")
        return fallback_flight_analysis(metrics, gps_df, imu_df)

    try:
        from groq import Groq
    except ImportError:
        logger.warning("groq package not installed. Using fallback analysis.")
        return fallback_flight_analysis(metrics, gps_df, imu_df)

    try:
        client = Groq(api_key=api_key)

        flight_summary = prepare_flight_summary(metrics, gps_df, imu_df)

        prompt = f"""
Analyze this drone/aircraft flight data and provide insights.

{flight_summary}

Provide your response strictly as raw valid JSON.
Do NOT wrap in markdown.
Return ONLY this JSON structure:

{{
  "summary": "...",
  "anomalies": "...",
  "recommendations": "..."
}}
"""

        response = client.chat.completions.create(
            model=LLM_MODEL,
            max_tokens=LLM_MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = safe_extract_llm_text(response)

        result = safe_parse_json(response_text)

        if not validate_analysis_schema(result):
            logger.warning("Invalid LLM schema. Using fallback.")
            return fallback_flight_analysis(metrics, gps_df, imu_df)

        return result

    except Exception as e:
        logger.error(f"Groq API error: {e}")
        return fallback_flight_analysis(metrics, gps_df, imu_df)


# =========================
# LLM Helpers
# =========================

def safe_extract_llm_text(response: Any) -> str:

    try:
        # Groq chat completions format: response.choices[0].message.content
        if hasattr(response, "choices") and response.choices:
            message = getattr(response.choices[0], "message", None)
            content = getattr(message, "content", "") if message else ""
            if isinstance(content, str):
                return content.strip()

        # Backward/alternate structure fallback
        if hasattr(response, "content") and response.content:
            first = response.content[0]
            text = getattr(first, "text", "")
            if isinstance(text, str):
                return text.strip()

        # Dict-like fallback
        if isinstance(response, dict):
            choices = response.get("choices", [])
            if choices:
                content = choices[0].get("message", {}).get("content", "")
                if isinstance(content, str):
                    return content.strip()

        logger.warning("Unexpected LLM response structure.")
        return ""
    except Exception:
        logger.warning("Failed to extract text from LLM response.")
        return ""


def safe_parse_json(text: str) -> Dict[str, str]:
    #Robust JSON parsing with markdown cleanup
    if not text:
        return {}

    cleaned = text.strip()

    # Remove markdown code fences if present
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.replace("json", "").strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        logger.warning("LLM returned invalid JSON. Attempting section extraction.")
        return extract_analysis_from_text(text)


def validate_analysis_schema(data: Dict[str, str]) -> bool:
    #Ensure response contains required fields
    required_keys = {"summary", "anomalies", "recommendations"}
    return isinstance(data, dict) and required_keys.issubset(data.keys())


# =========================
# Flight Data Preparation
# =========================

def prepare_flight_summary(
    metrics: Dict[str, float],
    gps_df: pd.DataFrame,
    imu_df: pd.DataFrame
) -> str:
    #Prepare structured summary for LLM prompt

    summary_lines = [
        "FLIGHT METRICS:",
        f"Duration: {metrics.get('Flight Duration (s)', 0):.1f} seconds",
        f"Total Distance: {metrics.get('Total Distance', 0):.2f} meters",
        f"Max Horizontal Speed: {metrics.get('Max Horizontal Speed', 0):.2f} m/s",
        f"Max Vertical Speed: {metrics.get('Max Vertical Speed', 0):.2f} m/s",
        f"Max Acceleration: {metrics.get('Max Acceleration', 0):.2f} m/s²",
        f"Max Altitude Gain: {metrics.get('Max Altitude Gain', 0):.2f} m",
        "",
        "DATA SAMPLES:",
        f"GPS samples: {len(gps_df)}",
        f"IMU samples: {len(imu_df)}",
    ]

    # GPS safe handling
    if not gps_df.empty and "alt" in gps_df.columns:
        summary_lines.extend([
            f"Altitude range: {gps_df['alt'].min():.2f} - {gps_df['alt'].max():.2f} m",
            f"Mean altitude: {gps_df['alt'].mean():.2f} m",
        ])

    # IMU safe handling
    required_imu_cols = {"acc_x", "acc_y", "acc_z"}
    if not imu_df.empty and required_imu_cols.issubset(imu_df.columns):
        acc_magnitude = np.sqrt(
            imu_df["acc_x"]**2 +
            imu_df["acc_y"]**2 +
            imu_df["acc_z"]**2
        )
        summary_lines.append(
            f"Mean acceleration magnitude: {acc_magnitude.mean():.2f} m/s²"
        )

    return "\n".join(summary_lines)


# =========================
# Text Fallback Parsing
# =========================

def extract_analysis_from_text(text: str) -> Dict[str, str]:
    #Extract structured sections from unstructured LLM output

    result = {
        "summary": "",
        "anomalies": "",
        "recommendations": ""
    }

    text_upper = text.upper()

    sections = {
        "summary": ("SUMMARY", "ANOMALIES"),
        "anomalies": ("ANOMALIES", "RECOMMENDATIONS"),
        "recommendations": ("RECOMMENDATIONS", None),
    }

    for key, (start_marker, end_marker) in sections.items():
        start_idx = text_upper.find(start_marker)
        if start_idx == -1:
            continue

        start_idx += len(start_marker)

        if end_marker:
            end_idx = text_upper.find(end_marker, start_idx)
            if end_idx == -1:
                end_idx = len(text)
        else:
            end_idx = len(text)

        extracted = text[start_idx:end_idx].strip()
        extracted = extracted.replace("**", "").replace("#", "").strip()

        result[key] = extracted[:1000] if extracted else ""

    return result


# =========================
# Rule-Based Fallback
# =========================

def fallback_flight_analysis(
    metrics: Dict[str, float],
    gps_df: pd.DataFrame,
    imu_df: pd.DataFrame
) -> Dict[str, str]:

    duration = metrics.get("Flight Duration (s)", 0)
    max_h_speed = metrics.get("Max Horizontal Speed", 0)
    max_v_speed = metrics.get("Max Vertical Speed", 0)
    max_acc = metrics.get("Max Acceleration", 0)
    total_dist = metrics.get("Total Distance", 0)

    # -------- Summary --------
    summary_parts = []

    if duration < 5:
        summary_parts.append("Very short flight duration")
    elif duration < 60:
        summary_parts.append("Short flight")
    else:
        summary_parts.append(f"Flight lasted {duration / 60:.1f} minutes")

    if max_h_speed > 0:
        summary_parts.append(f"reaching {max_h_speed:.1f} m/s horizontal speed")

    summary = ". ".join(summary_parts) + "."

    # -------- Anomalies --------
    anomalies = []

    if max_h_speed > MAX_SAFE_H_SPEED:
        anomalies.append(f"High horizontal speed ({max_h_speed:.1f} m/s)")

    if max_v_speed > MAX_SAFE_V_SPEED:
        anomalies.append(f"High vertical speed ({max_v_speed:.1f} m/s)")

    if max_acc > MAX_SAFE_ACC:
        anomalies.append(f"High acceleration ({max_acc:.1f} m/s²)")

    if max_acc < MIN_EXPECTED_ACC and len(imu_df) > 10:
        anomalies.append("Unusually low acceleration magnitude (possible IMU issue)")

    if total_dist == 0 and max_h_speed == 0:
        anomalies.append("No horizontal movement detected")

    anomalies_text = "\n".join(f"• {a}" for a in anomalies) if anomalies else "No major anomalies detected."

    # -------- Recommendations --------
    recommendations = []

    if max_acc > 40:
        recommendations.append("Use smoother control inputs to reduce mechanical stress.")

    if duration > 30:
        recommendations.append("Monitor battery performance during longer flights.")

    if max_v_speed > 10:
        recommendations.append("Evaluate wind conditions during vertical maneuvers.")

    recommendations_text = (
        "\n".join(f"• {r}" for r in recommendations)
        if recommendations
        else "Flight parameters appear within normal range."
    )

    return {
        "summary": summary,
        "anomalies": anomalies_text,
        "recommendations": recommendations_text
    }


# =========================
# Display Formatter
# =========================

def format_analysis_for_display(analysis: Dict[str, str]) -> str:
    #Console formatting

    return f"""
{'='*70}
AI FLIGHT ANALYSIS
{'='*70}

📋 SUMMARY
{'-'*70}
{analysis.get('summary', '')}

⚠️ ANOMALIES
{'-'*70}
{analysis.get('anomalies', '')}

💡 RECOMMENDATIONS
{'-'*70}
{analysis.get('recommendations', '')}

{'='*70}
"""