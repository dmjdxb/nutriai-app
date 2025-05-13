from datetime import datetime

# ----------------------------
# Simulated CGM Data
# ----------------------------
glucose_readings = [
    {"time": "06:00", "glucose": 90},
    {"time": "07:00", "glucose": 100},
    {"time": "08:00", "glucose": 112},
    {"time": "09:00", "glucose": 145},  # spike
    {"time": "10:00", "glucose": 138},
    {"time": "11:00", "glucose": 65},   # low
    {"time": "12:00", "glucose": 101},
    {"time": "13:00", "glucose": 150}   # spike
]

# ----------------------------
# Utility: Time Functions
# ----------------------------

def parse_time(time_str):
    return datetime.strptime(time_str, "%H:%M")

def time_diff_mins(t1, t2):
    t1_dt = parse_time(t1)
    t2_dt = parse_time(t2)
    return abs((t2_dt - t1_dt).total_seconds() / 60)

# ----------------------------
# Spike + Low Detection
# ----------------------------

def detect_glucose_events(data, spike_threshold=30, low_threshold=70, max_minutes=90):
    spikes = []
    lows = []
    for i in range(1, len(data)):
        prev = data[i - 1]
        curr = data[i]
        delta = curr["glucose"] - prev["glucose"]
        minutes = time_diff_mins(prev["time"], curr["time"])

        if delta >= spike_threshold and minutes <= max_minutes:
            spikes.append({
                "start_time": prev["time"],
                "spike_time": curr["time"],
                "glucose_start": prev["glucose"],
                "glucose_peak": curr["glucose"],
                "delta": delta,
                "duration": minutes
            })

        if curr["glucose"] < low_threshold:
            lows.append({
                "time": curr["time"],
                "glucose": curr["glucose"]
            })

    return spikes, lows

# ----------------------------
# Time-in-Range Calculation
# ----------------------------

def calculate_time_in_range(data, low=70, high=140):
    in_range_count = sum(1 for r in data if low <= r["glucose"] <= high)
    return round((in_range_count / len(data)) * 100, 1)

# ----------------------------
# Nutrition Advice Logic
# ----------------------------

def generate_macro_guidance(spikes, lows, tir_percent):
    if tir_percent < 60:
        return (
            f"Time in range: {tir_percent}%. Glucose very unstable.\n"
            "Follow a strict low-glycemic diet. Eliminate sugar and refined carbs."
        )
    elif tir_percent < 80:
        if lows:
            return (
                f"Time in range: {tir_percent}%. Low glucose events detected.\n"
                "Eat smaller, more frequent meals. Avoid skipping meals."
            )
        if spikes:
            return (
                f"Time in range: {tir_percent}%. Some instability detected.\n"
                "Reduce fast carbs. Add protein and fiber to each meal."
            )
        return (
            f"Time in range: {tir_percent}%. Stable but not optimal.\n"
            "Stick to balanced meals and avoid late eating."
        )
    else:
        if spikes:
            return (
                f"Time in range: {tir_percent}%. But glucose spikes were seen.\n"
                "Minimize processed carbs, add more fiber and healthy fats."
            )
        return (
            f"Time in range: {tir_percent}%. Glucose is stable.\n"
            "Balanced nutrition is appropriate today."
        )

# ----------------------------
# Macro Calculator
# ----------------------------

def calculate_macros(bodyweight_kg, goal="maintain", tir=100, spikes=0, lows=0):
    if goal == "cut":
        calories = 26 * bodyweight_kg
    elif goal == "gain":
        calories = 33 * bodyweight_kg
    else:
        calories = 30 * bodyweight_kg

    protein_g = round(2.2 * bodyweight_kg)
    protein_kcal = protein_g * 4

    if tir < 60 or lows > 0:
        carb_factor = 2.0
    elif spikes > 0:
        carb_factor = 2.5
    else:
        carb_factor = 3.0

    carb_g = round(carb_factor * bodyweight_kg)
    carb_kcal = carb_g * 4

    fat_kcal = calories - (protein_kcal + carb_kcal)
    fat_g = round(fat_kcal / 9)

    return {
        "calories": round(calories),
        "protein_g": protein_g,
        "carbs_g": carb_g,
        "fat_g": fat_g
    }

# ----------------------------
# GPT Explainer Generator
# ----------------------------

def build_gpt_macro_explainer(tir, spikes, lows, goal, macros, weight_kg):
    reasoning = []

    if tir >= 80:
        reasoning.append(f"Your glucose was stable today with {tir}% time in range.")
    elif tir >= 60:
        reasoning.append(f"Your glucose stability was moderate, with {tir}% time in range.")
    else:
        reasoning.append(f"Your glucose was unstable today with only {tir}% in range.")

    if spikes > 0:
        reasoning.append(f"{spikes} spike(s) were detected, suggesting high post-meal blood sugar.")
    if lows > 0:
        reasoning.append(f"{lows} low glucose episode(s) were detected, indicating a risk of hypoglycemia.")
    if spikes == 0 and lows == 0:
        reasoning.append("No glucose spikes or lows were recorded, indicating excellent control.")

    if goal == "cut":
        reasoning.append(f"You're in a fat-loss phase. Calories are set to slightly below maintenance at ~{macros['calories']} kcal.")
    elif goal == "gain":
        reasoning.append(f"You're in a muscle gain phase. Calories are slightly elevated to support lean mass growth.")
    else:
        reasoning.append(f"You're maintaining your current bodyweight. Calories are set around maintenance (~{macros['calories']} kcal).")

    reasoning.append(
        f"Protein is set at {macros['protein_g']}g (2.2g/kg for {weight_kg} kg), "
        f"carbs at {macros['carbs_g']}g (adjusted for stability), "
        f"and fats at {macros['fat_g']}g to complete the energy balance."
    )

    if tir < 60 or spikes > 1:
        reasoning.append("Focus on lower-glycemic carbs, increase vegetable fiber, and eat slower-digesting meals.")
    elif lows > 0:
        reasoning.append("Try to eat more consistently and avoid fasting for long periods.")
    else:
        reasoning.append("Keep doing what you’re doing — today’s glucose profile looks good.")

    return "\n".join(reasoning)

# ----------------------------
# Main Engine
# ----------------------------

if __name__ == "__main__":
    tir = calculate_time_in_range(glucose_readings)
    spikes, lows = detect_glucose_events(glucose_readings)

    print("\n--- Glucose Event Summary ---")
    if spikes:
        print(f"{len(spikes)} spike(s):")
        for s in spikes:
            print(f" - +{s['delta']} mg/dL from {s['glucose_start']} → {s['glucose_peak']} "
                  f"({s['start_time']} to {s['spike_time']})")
    else:
        print("No spikes detected.")

    if lows:
        print(f"{len(lows)} low(s):")
        for l in lows:
            print(f" - {l['time']}: {l['glucose']} mg/dL")
    else:
        print("No lows detected.")

    print(f"\nTime in Range: {tir}%")
    print("\n--- Nutrition Recommendation ---")
    print(generate_macro_guidance(spikes, lows, tir))

    bodyweight_kg = 75
    goal = "maintain"

    macros = calculate_macros(bodyweight_kg, goal, tir, len(spikes), len(lows))

    print("\n--- Macro Plan ---")
    print(f"Calories: {macros['calories']} kcal")
    print(f"Protein:  {macros['protein_g']} g")
    print(f"Carbs:    {macros['carbs_g']} g")
    print(f"Fat:      {macros['fat_g']} g")

    print("\n--- GPT Explainer ---")
    explanation = build_gpt_macro_explainer(tir, len(spikes), len(lows), goal, macros, bodyweight_kg)
    print(explanation)
