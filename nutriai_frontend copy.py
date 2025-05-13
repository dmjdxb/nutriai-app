import streamlit as st
import requests
import json
import os

# --- USDA API Setup ---
USDA_API_KEY = "5ooDGeyWxJmVcx6uIVfgu3Xwwg5BK0STXv3mfFff"

def search_usda_foods(query):
    try:
        url = "https://api.nal.usda.gov/fdc/v1/foods/search"
        params = {
            "query": query,
            "pageSize": 5,
            "api_key": USDA_API_KEY
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            return data.get("foods", [])
        else:
            st.error(f"USDA API Error: {response.status_code}")
            return []
    except Exception as e:
        st.error(f"USDA Search Error: {str(e)}")
        return []
from datetime import datetime



# Navigation
page = st.sidebar.radio("Navigate", ["Glucose & Chat", "Nutrition Profile", "USDA Food Search"])

# --- Nutrition Profile Page ---
if page == "Nutrition Profile":
    st.title("📋 Build Your Nutrition Profile")

    with st.form("profile_form"):
        st.subheader("Personal Information")
        sex = st.selectbox("Sex", ["Male", "Female"])
        age = st.number_input("Age", min_value=10, max_value=100, value=30)
        height = st.number_input("Height (cm)", min_value=120, max_value=250, value=175)
        weight = st.number_input("Weight (kg)", min_value=30, max_value=200, value=75)

        st.subheader("Lifestyle & Goals")
        activity = st.selectbox("Activity Level", [
            "Sedentary (little/no exercise)",
            "Lightly active (1-3 days/week)",
            "Moderately active (3-5 days/week)",
            "Very active (6-7 days/week)",
            "Extra active (athlete or 2x/day)"
        ])
        goal = st.selectbox("Goal", ["Cut (fat loss)", "Maintain", "Gain (muscle gain)"])

        st.subheader("Diet Type")
        diet_type = st.selectbox("Select Diet Type", [
            "Balanced", "Low Carb", "Keto", "High Carb", "Carnivore",
            "Vegetarian", "Vegan", "Paleo", "Mediterranean"
        ])

        submitted = st.form_submit_button("Calculate Plan")

    if submitted:
        # --- BMR Calculation ---
        if sex == "Male":
            bmr = 10 * weight + 6.25 * height - 5 * age + 5
        else:
            bmr = 10 * weight + 6.25 * height - 5 * age - 161

        # --- Activity Multiplier ---
        activity_map = {
            "Sedentary (little/no exercise)": 1.2,
            "Lightly active (1-3 days/week)": 1.375,
            "Moderately active (3-5 days/week)": 1.55,
            "Very active (6-7 days/week)": 1.725,
            "Extra active (athlete or 2x/day)": 1.9
        }
        tdee = bmr * activity_map[activity]

        # --- Goal Adjustment ---
        if "Cut" in goal:
            calories = tdee * 0.85
        elif "Gain" in goal:
            calories = tdee * 1.15
        else:
            calories = tdee

        # --- Macro Split Based on Diet Type ---
        protein_g = round(2.2 * weight)
        protein_kcal = protein_g * 4

        if diet_type == "Keto":
            carbs_g = round(0.5 * weight)
        elif diet_type == "Low Carb":
            carbs_g = round(1.0 * weight)
        elif diet_type == "High Carb":
            carbs_g = round(3.0 * weight)
        elif diet_type == "Carnivore":
            carbs_g = 0
        else:
            carbs_g = round(2.0 * weight)

        carbs_kcal = carbs_g * 4
        fat_kcal = calories - (protein_kcal + carbs_kcal)
        fat_g = round(fat_kcal / 9)
        # Save user macros to session state
        st.session_state.diet_type = diet_type
        st.session_state.protein_g = protein_g
        st.session_state.carbs_g = carbs_g
        st.session_state.fat_g = fat_g

        # --- Output ---
        st.success("✅ Personalized Daily Nutrition Plan")
        st.metric("Calories/day", round(calories))
        st.write("**Macros:**")
        st.write(f"- Protein: {protein_g}g")
        st.write(f"- Carbs: {carbs_g}g")
        st.write(f"- Fat: {fat_g}g")

        # --- Link to Meal Generator ---
    # --- Ensure allergy_list is initialized ---
if "allergy_list" not in st.session_state:
    st.session_state.allergy_list = []

if page == "Nutrition Profile":
    with st.form("meal_form"):
        st.subheader("🥗 Generate a Sample Meal Plan")
        st.session_state.allergy_list = st.multiselect(
            "Do you have any food allergies?",
            ["Gluten", "Dairy", "Eggs", "Soy", "Nuts", "Shellfish"],
            default=st.session_state.allergy_list
        )
        generate_meals = st.form_submit_button("Generate Meals From My Macros")

if page == "Nutrition Profile" and 'generate_meals' in locals() and generate_meals:
    st.markdown("### 🍽 Example Day Based on Your Macros")

    def exclude_allergens(meal):
        for allergen in st.session_state.allergy_list:
            if allergen.lower() in meal.lower():
                return False
        return True

    meal_options = {
        "Keto": [
            "Eggs cooked in butter with spinach and avocado",
            "Grilled salmon with olive oil, zucchini, and cauliflower mash",
            "Lamb chops with asparagus and creamy mushrooms",
            "Almond butter protein shake"
        ],
        "Vegetarian": [
            "Tofu scramble with sweet potato and spinach",
            "Chickpea salad with olive oil and roasted peppers",
            "Lentil curry with rice and steamed greens",
            "Greek yogurt with berries and seeds"
        ],
        "Carnivore": [
            "Steak and eggs",
            "Chicken thighs with bone broth",
            "Pork belly with hard boiled eggs",
            "Whey protein shake with beef collagen"
        ],
        "Balanced": [
            "Scrambled eggs with spinach and avocado",
            "Grilled chicken breast, quinoa, and roasted vegetables",
            "Salmon filet with asparagus and olive oil",
            "Protein shake with almond butter"
        ]
    }

    diet_choice = st.session_state.get("diet_type", "Balanced")
    protein_g = st.session_state.get("protein_g", 0)
    carbs_g = st.session_state.get("carbs_g", 0)
    fat_g = st.session_state.get("fat_g", 0)
    meals = meal_options.get(diet_choice, meal_options["Balanced"])
    filtered_meals = list(filter(exclude_allergens, meals))

    if not filtered_meals or len(filtered_meals) < 4:
        st.warning("⚠️ Not enough allergy-safe meals available. Please adjust preferences.")
    else:
        st.write(f"**Breakfast**: {filtered_meals[0]} (P: {int(protein_g*0.3)}g, C: {int(carbs_g*0.25)}g, F: {int(fat_g*0.3)}g)")
        st.write(f"**Lunch**: {filtered_meals[1]} (P: {int(protein_g*0.3)}g, C: {int(carbs_g*0.3)}g, F: {int(fat_g*0.3)}g)")
        st.write(f"**Dinner**: {filtered_meals[2]} (P: {int(protein_g*0.3)}g, C: {int(carbs_g*0.3)}g, F: {int(fat_g*0.3)}g)")
        st.write(f"**Snack**: {filtered_meals[3]} (P: {int(protein_g*0.1)}g, C: {int(carbs_g*0.15)}g, F: {int(fat_g*0.1)}g)")

# --- USDA Food Database Integration ---
        # Show saved meals
        if "saved_meals" in st.session_state and st.session_state.saved_meals:
            st.markdown("### ✅ Your Daily Meal Plan")
            total_cal = total_pro = total_carb = total_fat = 0.0

            for idx, meal in enumerate(st.session_state.saved_meals):
                st.write(f"{idx+1}. **{meal['description']}**")
                st.write(f"   - Calories: {meal['calories']}")
                st.write(f"   - Protein: {meal['protein']}")
                st.write(f"   - Carbs: {meal['carbs']}")
                st.write(f"   - Fat: {meal['fat']}")
                st.markdown("---")

                # Try parsing numeric values from strings like '26.3 G'
                def parse_val(val):
                    try:
                        return float(str(val).split()[0])
                    except:
                        return 0

                total_cal += parse_val(meal['calories'])
                total_pro += parse_val(meal['protein'])
                total_carb += parse_val(meal['carbs'])
                total_fat += parse_val(meal['fat'])

            # Totals
            st.markdown("### 🔢 Macro Totals for Today")
            st.write(f"**Calories:** {round(total_cal)} kcal")
            st.write(f"**Protein:** {round(total_pro)} g")
            st.write(f"**Carbs:** {round(total_carb)} g")
            st.write(f"**Fat:** {round(total_fat)} g")

        # --- Export Button ---
        if st.button("📤 Export Meal Plan to PDF"):
            from fpdf import FPDF

            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, txt="NutriAI: Daily Meal Plan", ln=True, align="C")
            pdf.ln(5)

            for idx, meal in enumerate(st.session_state.saved_meals):
                pdf.set_font("Arial", style="B", size=11)
                pdf.cell(0, 10, f"{idx+1}. {meal['description']}", ln=True)
                pdf.set_font("Arial", size=11)
                pdf.cell(0, 8, f"Calories: {meal['calories']}", ln=True)
                pdf.cell(0, 8, f"Protein: {meal['protein']}", ln=True)
                pdf.cell(0, 8, f"Carbs: {meal['carbs']}", ln=True)
                pdf.cell(0, 8, f"Fat: {meal['fat']}", ln=True)
                pdf.ln(4)

            pdf.set_font("Arial", style="B", size=12)
            pdf.cell(0, 10, "Macro Totals:", ln=True)
            pdf.set_font("Arial", size=11)
            pdf.cell(0, 8, f"Calories: {round(total_cal)} kcal", ln=True)
            pdf.cell(0, 8, f"Protein: {round(total_pro)} g", ln=True)
            pdf.cell(0, 8, f"Carbs: {round(total_carb)} g", ln=True)
            pdf.cell(0, 8, f"Fat: {round(total_fat)} g", ln=True)

            export_path = "daily_plan.pdf"
            pdf.output(export_path)

            with open(export_path, "rb") as file:
                st.download_button("⬇️ Download PDF", file, file_name="NutriAI_Meal_Plan.pdf")
        st.markdown("---")
if page == "USDA Food Search":
    st.title("🔍 Search Real Foods From USDA Database")
    with st.form("usda_form"):
        search_term = st.text_input("Type a food to look up:", value="chicken breast")
        usda_search = st.form_submit_button("Search USDA Foods")

    if 'usda_search' in locals() and usda_search:
        # Placeholder USDA search function until implemented
        results = search_usda_foods(search_term)
        if results:
            st.success(f"Top {len(results)} results for '{search_term}':")
            for food in results:
                st.write(f"**{food['description']}**")
                nutrients = food.get("foodNutrients", [])
                macros = {"Protein": None, "Carbohydrate, by difference": None, "Total lipid (fat)": None, "Energy": None}
                for nutrient in nutrients:
                    name = nutrient['nutrientName']
                    if name in macros:
                        macros[name] = f"{nutrient['value']} {nutrient['unitName']}"
                st.write(f"- Calories: {macros['Energy']}")
                st.write(f"- Protein: {macros['Protein']}")
                st.write(f"- Carbs: {macros['Carbohydrate, by difference']}")
                st.write(f"- Fat: {macros['Total lipid (fat)']}")

                # Auto-match feedback
                st.caption("📊 Matching this item to your current macros...")
                if 'protein_g' in st.session_state and 'carbs_g' in st.session_state and 'fat_g' in st.session_state:
                    def extract_numeric(val):
                        try:
                            return float(str(val).split()[0])
                        except:
                            return 0.0

                    p_goal = st.session_state.protein_g
                    c_goal = st.session_state.carbs_g
                    f_goal = st.session_state.fat_g

                    p_val = extract_numeric(macros['Protein'])
                    c_val = extract_numeric(macros['Carbohydrate, by difference'])
                    f_val = extract_numeric(macros['Total lipid (fat)'])

                    match_score = 100 - (
                        abs(p_val - (p_goal / 4)) / (p_goal / 4) * 33 +
                        abs(c_val - (c_goal / 4)) / (c_goal / 4) * 33 +
                        abs(f_val - (f_goal / 4)) / (f_goal / 4) * 33
                    )
                    match_score = max(0, min(100, round(match_score)))
                    st.write(f"🧮 Match Score: {match_score}% to your current macro target (1 of 4 meals)")
                save_key = f"save_{food['fdcId']}"
                if st.button("💾 Save this to my daily plan", key=save_key):
                    saved_meal = {
                        "description": food['description'],
                        "calories": macros['Energy'],
                        "protein": macros['Protein'],
                        "carbs": macros['Carbohydrate, by difference'],
                        "fat": macros['Total lipid (fat)']
                    }
                    if "saved_meals" not in st.session_state:
                        st.session_state.saved_meals = []
                    st.session_state.saved_meals.append(saved_meal)
                    st.success(f"✔️ Added {food['description']} to your daily plan.")
                st.markdown("---")
        else:
            st.warning("No results found.")

# --- Main Glucose & Chat App Page ---
if page == "Glucose & Chat":
    st.title("📊 NutriAI: Daily Glucose & Macro Planner")

    with st.form("glucose_form"):
        st.subheader("Enter your glucose data")
        user_id = st.text_input("Enter your name or user ID:", "david")
        st.session_state.user_id = user_id
        bodyweight = st.number_input("Bodyweight (kg)", min_value=30.0, max_value=150.0, value=75.0)
        goal = st.selectbox("Goal", ["cut", "maintain", "gain"])

        st.markdown("### Glucose Readings (at least 2)")
        glucose_data = st.text_area("Format: HH:MM,glucose (one per line)", "08:00,95 09:00,142 10:00,135 11:00,66 12:00,102")
        submitted = st.form_submit_button("Analyze")

    if submitted:
        try:
            lines = glucose_data.strip().split(" ")
            readings = []
            for line in lines:
                time_str, value_str = line.strip().split(",")
                readings.append({"time": time_str.strip(), "glucose": int(value_str.strip())})

            payload = {
                "glucose_readings": readings,
                "bodyweight_kg": bodyweight,
                "goal": goal
            }

            response = requests.post("http://localhost:8000/analyze", json=payload)

            if response.status_code == 200:
                st.session_state.response = response.json()
                st.success("✅ Analysis complete!")
                st.metric("Time in Range (%)", st.session_state.response["tir"])
                st.metric("# Spikes", len(st.session_state.response["spikes"]))
                st.metric("# Lows", len(st.session_state.response["lows"]))
                st.subheader("🥩 Daily Macros")
                st.json(st.session_state.response["macros"])
                st.subheader("🧠 Recommendation")
                st.write(st.session_state.response["recommendation"])
            else:
                st.error(f"API Error: {response.status_code}")
        except Exception as e:
            st.error(f"Error: {str(e)}")

# Re-enable chat interface after response
    if st.session_state.response:
        st.subheader("💬 Ask NutriAI Anything")
        user_input = st.text_input("Ask a question about your results:", "")

        if user_input:
            st.session_state.messages.append({"role": "user", "content": user_input})
            tir = st.session_state.response["tir"]
            spikes = st.session_state.response["spikes"]
            lows = st.session_state.response["lows"]
            macros = st.session_state.response["macros"]

            if "spike" in user_input.lower():
                if spikes:
                    s = spikes[-1]
                    reply = f"You had a glucose spike from {s['from']} to {s['to']} with a +{s['delta']} mg/dL increase. Likely due to high-GI carbs or low fiber."
                else:
                    reply = "No spikes were recorded today. Your post-meal control looks solid."
            elif "low" in user_input.lower():
                if lows:
                    l = lows[-1]
                    reply = f"You experienced a glucose low at {l['time']} with a reading of {l['value']} mg/dL. Consider a protein+fat snack in the late morning."
                else:
                    reply = "No low glucose events today. Great stability."
            elif "macro" in user_input.lower():
                reply = f"Today's macros are: Protein {macros['protein_g']}g, Carbs {macros['carbs_g']}g, Fat {macros['fat_g']}g."
            elif "recommendation" in user_input.lower():
                reply = st.session_state.response["recommendation"]
            else:
                reply = "I'm a mock AI today — ask about spikes, lows, macros, or recommendation. GPT mode coming soon!"

            st.session_state.messages.append({"role": "assistant", "content": reply})
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"chat_logs/{user_id}_{timestamp}.json"
            st.session_state.chat_file = filename
            with open(filename, "w") as f:
                json.dump(st.session_state.messages, f, indent=2)

        for msg in st.session_state.messages:
            if msg["role"] == "user":
                st.markdown(f"**You:** {msg['content']}")
            else:
                st.markdown(f"**NutriAI:** {msg['content']}")

        if st.session_state.chat_file:
            with open(st.session_state.chat_file, "r") as f:
                chat_json = f.read()
            st.download_button("📥 Download Chat History", chat_json, file_name=os.path.basename(st.session_state.chat_file), mime="application/json")

        st.markdown("---")
        st.subheader("📂 Reload a Previous Conversation")
        st.caption("Upload a previously saved chat history file (JSON format).")
        st.caption("Click 'Browse files' or drag & drop a file below.")
        uploaded_file = st.file_uploader("Load a saved conversation", type=["json"], label_visibility="collapsed")
        if uploaded_file:
            loaded_chat = json.load(uploaded_file)
            st.session_state.messages = loaded_chat
            st.success("✅ Chat history loaded!")


# Initialize Streamlit session state variables early
if "response" not in st.session_state:
    st.session_state.response = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_file" not in st.session_state:
    st.session_state.chat_file = None

# Create local storage directory
if "response" not in st.session_state:
    st.session_state.response = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_file" not in st.session_state:
    st.session_state.chat_file = None


