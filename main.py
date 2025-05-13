from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from datetime import datetime

app = FastAPI()

# ----------------------------
# Input Data Schema
# ----------------------------
class GlucoseReading(BaseModel):
    time: str  # e.g. "09:00"
    glucose: int

class AnalysisRequest(BaseModel):
    glucose_readings: List[GlucoseReading]
    bodyweight_kg: float
    goal: str  # "cut", "maintain", or "gain"

# ----------------------------
# Core Logic Functions
# ----------------------------
def parse_time(time_str):
    return datetime.strptime(time_str, "%H:%M")

def time_diff_mins(t1, t2):
    return abs((parse_time(t2) - parse_time(t1)).total_seconds() / 60)

def detect_glucose_events(data, spike_threshold=30, low_threshold=70, max_minutes=90):
    spikes, lows = [], []
    for i in range(1, len(data)):
        prev = data[i - 1]
        curr = data[i]
        delta = curr['glucose'] - prev['glucose']
        minutes = time_diff_mins(prev['time'], curr['time'])

        if delta >= spike_threshold and minutes <= max_minutes:
            spikes.append({"from": prev['time'], "to": curr['time'], "delta": delta})
        if curr['glucose'] < low_threshold:
            lows.append({"time": curr['time'], "value": curr['glucose']})
    return spikes, lows

def calculate_time_in_range(data, low=70, high=140):
    in_range = sum(1 for r in data if low <= r['glucose'] <= high)
    return round((in_range / len(data)) * 100, 1)

def calculate_macros(weight, goal, tir, spikes, lows):
    if goal == "cut": calories = 26 * weight
    elif goal == "gain": calories = 33 * weight
    else: calories = 30 * weight

    protein_g = round(2.2 * weight)
    protein_kcal = protein_g * 4

    carb_factor = 2.0 if tir < 60 or lows > 0 else 2.5 if spikes > 0 else 3.0
    carbs_g = round(carb_factor * weight)
    carb_kcal = carbs_g * 4

    fat_kcal = calories - (protein_kcal + carb_kcal)
    fat_g = round(fat_kcal / 9)

    return {
        "calories": round(calories),
        "protein_g": protein_g,
        "carbs_g": carbs_g,
        "fat_g": fat_g
    }

def generate_explainer(tir, spikes, lows, goal, macros, weight):
    out = []
    out.append(f"Your glucose was {'stable' if tir >= 80 else 'moderate' if tir >= 60 else 'unstable'} with {tir}% time in range.")
    if spikes: out.append(f"{len(spikes)} spike(s) detected.")
    if lows: out.append(f"{len(lows)} low(s) detected.")
    if not spikes and not lows: out.append("No spikes or lows recorded.")

    if goal == "cut":
        out.append(f"Fat-loss goal: calories set to ~{macros['calories']} kcal.")
    elif goal == "gain":
        out.append(f"Muscle gain goal: slight surplus ~{macros['calories']} kcal.")
    else:
        out.append(f"Maintenance goal: ~{macros['calories']} kcal.")

    out.append(f"Protein: {macros['protein_g']}g (2.2g/kg for {weight}kg), Carbs: {macros['carbs_g']}g, Fat: {macros['fat_g']}g.")

    if tir < 60 or len(spikes) > 1:
        out.append("Focus on low-glycemic carbs and higher fiber.")
    elif lows:
        out.append("Eat more consistently, avoid skipping meals.")
    else:
        out.append("Well done — glucose looks well controlled today.")

    return " ".join(out)

# ----------------------------
# API Endpoint
# ----------------------------
@app.post("/analyze")
def analyze(request: AnalysisRequest):
    data = [r.dict() for r in request.glucose_readings]
    if not data or len(data) < 2:
        raise HTTPException(status_code=400, detail="Not enough glucose data.")

    spikes, lows = detect_glucose_events(data)
    tir = calculate_time_in_range(data)
    macros = calculate_macros(request.bodyweight_kg, request.goal, tir, len(spikes), len(lows))
    explainer = generate_explainer(tir, spikes, lows, request.goal, macros, request.bodyweight_kg)

    return {
        "tir": tir,
        "spikes": spikes,
        "lows": lows,
        "macros": macros,
        "recommendation": explainer
    }
