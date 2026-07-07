import streamlit as st
import google.generativeai as genai
import pandas as pd
import datetime
import os
import json
from PIL import Image
from dotenv import load_dotenv

# --- 1. INITIAL SETUP & APP CONFIG ---
st.set_page_config(page_title="6-Month Wellness Blueprint", layout="wide")

script_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(script_dir, '.env')
load_dotenv(dotenv_path=env_path)

GENAI_API_KEY = os.environ.get("GEMINI_API_KEY")

# --- 2. STATE MANAGEMENT (Initialize Profile if missing) ---
if "user_profile" not in st.session_state:
    st.session_state.user_profile = {
        "weight": 150.50,
        "age": 31,
        "height": "5'2\"",
        "protein_target": 105,
        "fiber_target": 25,
        "calorie_target": 1785,
        "water_target": 10,
        "start_date": datetime.date.today()
    }

#  ADD THIS BLOCK TO INITIALIZE YOUR MEAL LOG LIST
if "current_today_meals" not in st.session_state:
    st.session_state.current_today_meals = []

#  ADD THIS BLOCK to track historical daily performance records
if "daily_history" not in st.session_state:
    st.session_state.daily_history = []

# --- 3. APP NAVIGATION TABS ---
tab1, tab2, tab3 = st.tabs(["📋 1. Profile & 6-Month Goals", "📸 2. Daily Log (AI Photo & Steps)", "📊 3. End-of-Day Scoreboard"])

# ==========================================
# TAB 1: USER DETAILS & TARGET CONFIGURATION
# ==========================================
with tab1:
    st.header("Personal Details & Targets")
    
    # 1. First, render the input widgets so Python captures the live user variables
    col1, col2, col3 = st.columns(3)
    
    with col1:
        weight = st.number_input("Current Weight (lbs)", value=st.session_state.user_profile["weight"], step=0.1)
        age = st.number_input("Age (Years)", value=st.session_state.user_profile["age"], step=1)
    with col2:
        height = st.text_input("Height", value=st.session_state.user_profile["height"])
        start_d = st.date_input("Plan Start Date", value=st.session_state.user_profile["start_date"])
    with col3:
        end_date = start_d + datetime.timedelta(days=180)
        st.metric(label="6-Month Plan Timeline", value="180 Days Active")
        st.caption(f"Your transformation blueprint runs until: **{end_date.strftime('%B %d, %Y')}**")

    # 2. RUN RESPONSIVE MATH (Directly mapping to live input widget parameters)
    current_weight_lbs = weight    
    current_age = age              
    current_height_str = height    

    weight_kg = current_weight_lbs * 0.45359237

    if "5'8" in current_height_str:
        height_cm = 172.72
    elif "5'2" in current_height_str:
        height_cm = 157.48
    else:
        height_cm = 162.56 

    bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * current_age) - 161
    responsive_calorie_target = int(bmr * 1.375)
    responsive_protein_target = int(weight_kg * 2.0)

    # 3. FIX: Move subheader OUT of column 3 so it spans the left side cleanly
    st.subheader("Daily Nutrient Targets")

    # 4. Render the dynamically calculated nutrient targets
    nut_col1, nut_col2, nut_col3, nut_col4 = st.columns(4)

    with nut_col1:
        target_protein = st.number_input("Target Protein (grams)", value=responsive_protein_target)

    with nut_col2:
        target_fiber = st.number_input("Target Fiber (grams)", value=25)

    with nut_col3:
        target_calories = st.number_input("Target Calories (kcal)", value=responsive_calorie_target)

    with nut_col4:
        responsive_water = 10 if weight_kg > 65 else 8
        target_water = st.number_input("Target Water (Cups)", value=responsive_water)

    # 5. Lock-in save button actions
    if st.button("Lock In My Blueprint Settings"):
        st.session_state.user_profile.update({
            "weight": weight, "age": age, "height": height,
            "protein_target": target_protein, "fiber_target": target_fiber, 
            "calorie_target": target_calories, "water_target": target_water, "start_date": start_d
        })
        st.success("Profile goals updated! Move to Tab 2 to log metrics.")


# ==========================================
# TAB 2: DAILY LOG (TEXT & OPTIONAL PHOTO)
# ==========================================
with tab2:
    st.header(f"Log Stats for {datetime.date.today().strftime('%A, %B %d')}")
    
    # 1. Step and Water Inputs
    meta_col1, meta_col2 = st.columns(2)
    with meta_col1:
        steps = st.number_input("Total Daily Step Count", min_value=0, value=0, step=500)
    with meta_col2:
        water_cups = st.number_input("Total Water Consumed (Cups)", min_value=0, value=0, step=1)
        
    st.markdown("---")
    
    # 2. Meal Meta-data Selection
    chosen_meal = st.selectbox("Which meal are you logging?", ["Breakfast", "Mid-Day Snack", "Lunch", "Tea & Evening Snack", "Dinner"])
    meal_time = st.time_input(f"What time did you have {chosen_meal}?", value=datetime.time(8, 0))
    
    # Initialize the shared runtime JSON variable
    result_json = None

    # ==========================================
    # PRIMARY METHOD: ✍️ MANUAL TEXT ENTRY
    # ==========================================
    st.subheader("✍️ Record Your Meal Ingredients")
    user_text_input = st.text_area(
        "What did you eat? (Specify quantities if known)",
        placeholder="e.g., 1 cup of Greek yogurt, 100g strawberries, and a handful of almonds",
        key="manual_meal_text"
    )
    
    if st.button("Calculate Metrics from Text", type="primary"):
        if not user_text_input.strip():
            st.warning("Please type your meal contents before submitting.")
        else:
            with st.spinner("AI parsing your ingredients..."):
                try:
                    genai.configure(api_key=GENAI_API_KEY)
                    model = genai.GenerativeModel('gemini-2.5-flash')
                    
                    text_prompt = f"""
                    You are a strict nutritionist database app. Read this exact text meal description and compute total macronutrients.
                    Meal Description: "{user_text_input}"
                    
                    Return ONLY a JSON object with exactly these keys: "protein", "carbs", "fat", "fiber", "estimated_items".
                    The "estimated_items" value should copy or lightly clean up the user's description.
                    Do not include any markdown formatting like ```json or text outside the JSON object.
                    """
                    
                    response = model.generate_content(text_prompt)
                    result_json = json.loads(response.text.strip())
                except Exception as e:
                    st.error(f"Error processing text input: {e}")

    # ==========================================
    # OPTIONAL METHOD: 📸 AI PHOTO ANALYZER EXPANDER
    # ==========================================
    st.markdown("---")
    with st.expander("📸 Prefer to use a picture instead? Click here to open Photo Mode"):
        st.caption("Upload or take a quick photo of your plate to let Gemini identify your food visually.")
        uploaded_image = st.file_uploader(f"Choose a picture for {chosen_meal}", type=["jpg", "jpeg", "png"], key="meal_photo_uploader")
        
        if uploaded_image is not None:
            image = Image.open(uploaded_image)
            st.image(image, caption="Uploaded Food Plate", width=300)

            if st.button("Analyze Uploaded Image", type="secondary"):
                with st.spinner("AI running visual ingestion mapping..."):
                    try:
                        genai.configure(api_key=GENAI_API_KEY)
                        model = genai.GenerativeModel('gemini-2.5-flash')
                        
                        photo_prompt = """
                        You are an expert nutritionist AI. Analyze this image of a meal and provide an accurate estimation of its nutritional properties.
                        Return ONLY a JSON object with exactly these keys: "protein", "carbs", "fat", "fiber", "estimated_items".
                        Do not include any markdown formatting like ```json or text outside the JSON object.
                        """
                        
                        response = model.generate_content([photo_prompt, image])
                        result_json = json.loads(response.text.strip())
                    except Exception as e:
                        st.error(f"Error parsing image contents: {e}")

    # ==========================================
    # UNIFIED LOGIC PIPELINE
    # ==========================================
    if result_json:
        # Commit directly to state
        st.session_state.current_today_meals[chosen_meal] = {
            "time": meal_time.strftime("%I:%M %p"),
            "protein": float(result_json.get('protein', 0)),
            "carbs": float(result_json.get('carbs', 0)),
            "fat": float(result_json.get('fat', 0)),
            "fiber": float(result_json.get('fiber', 0))
        }
        # Force immediate synchronized rerun
        st.rerun()

    # Show items logged so far today
    if st.session_state.current_today_meals:
        st.markdown("---")
        st.subheader("Meals Tracked Today So Far:")
        for m, data in st.session_state.current_today_meals.items():
            st.markdown(f"🔹 **{m}** ({data['time']}) → Protein: {data['protein']}g | Carbs: {data['carbs']}g | Fat: {data['fat']}g | Fiber: {data.get('fiber', 0)}g")

        # --- CALCULATIONS FOR THE METRICS ---
        consumed_p = sum(info.get("protein", 0) for info in st.session_state.current_today_meals.values())
        consumed_c = sum(info.get("carbs", 0) for info in st.session_state.current_today_meals.values())
        consumed_f = sum(info.get("fat", 0) for info in st.session_state.current_today_meals.values())
        consumed_fib = sum(info.get("fiber", 0) for info in st.session_state.current_today_meals.values())
        consumed_cal = (consumed_p * 4) + (consumed_c * 4) + (consumed_f * 9)

        rem_cal = max(0, int(st.session_state.user_profile["calorie_target"] - consumed_cal))
        rem_p = max(0, int(st.session_state.user_profile["protein_target"] - consumed_p))
        rem_fib = max(0, int(st.session_state.user_profile["fiber_target"] - consumed_fib))

        # --- BOTTOM SCOREBOARD ONLY ---
        st.markdown("#### 🔄 Updated Remaining Allowances")
        bot_col1, bot_col2, bot_col3 = st.columns(3)
        with bot_col1:
            st.metric(label="Calories Left to Eat", value=f"{rem_cal} kcal", delta=f"{int(consumed_cal)} consumed")
        with bot_col2:
            st.metric(label="Protein Remaining", value=f"{rem_p} g", delta=f"{int(consumed_p)}g tracked")
        with bot_col3:
            st.metric(label="Fiber Remaining", value=f"{rem_fib} g", delta=f"{int(consumed_fib)}g tracked")

    # ==========================================
    # EOD CONSOLIDATION & SCOREBOARD SUBMISSION
    # ==========================================
    st.markdown("---")
    if st.button("Consolidate & Save Today's Final Metrics", type="primary"):
        if not st.session_state.current_today_meals:
            st.warning("Please record or analyze at least one meal before compiling your final execution score.")
        else:
            total_p = sum(info["protein"] for info in st.session_state.current_today_meals.values())
            total_c = sum(info["carbs"] for info in st.session_state.current_today_meals.values())
            total_f = sum(info["fat"] for info in st.session_state.current_today_meals.values())
            total_fib = sum(info.get("fiber", 0) for info in st.session_state.current_today_meals.values())
            
            calculated_calories = (total_p * 4) + (total_c * 4) + (total_f * 9)
            
            p_score = 100 if total_p >= st.session_state.user_profile["protein_target"] else int((total_p / st.session_state.user_profile["protein_target"]) * 100)
            w_score = 100 if water_cups >= st.session_state.user_profile["water_target"] else int((water_cups / st.session_state.user_profile["water_target"]) * 100)
            
            cal_diff = abs(calculated_calories - st.session_state.user_profile["calorie_target"])
            c_score = max(0, 100 - int((cal_diff / st.session_state.user_profile["calorie_target"]) * 100)) if calculated_calories > 0 else 0
            
            final_daily_score = int((p_score + w_score + c_score) / 3)
            
            today_entry = {
                "Date": datetime.date.today(),
                "Steps": steps,
                "Water": water_cups,
                "Protein": total_p,
                "Carbs": total_c,
                "Fat": total_f,
                "Fiber": total_fib,
                "Calories": calculated_calories,
                "Day Score": final_daily_score
            }
            
            st.session_state.daily_history = [entry for entry in st.session_state.daily_history if entry["Date"] != datetime.date.today()]
            st.session_state.daily_history.append(today_entry)
            st.success(f"Log compiled successfully! Day Score: **{final_daily_score}/100** 🎉 Check out Tab 3!")

# ==========================================
# TAB 3: END-OF-DAY SCOREBOARD & ANALYSIS
# ==========================================
with tab3:
    st.header("📈 Compliance Tracking Dashboard")
    
    if st.session_state.daily_history:
        df_history = pd.DataFrame(st.session_state.daily_history)
        latest = df_history.iloc[-1]
        
        st.subheader("Today's Performance Breakdown")
        score_col1, score_col2, score_col3 = st.columns(3)
        with score_col1:
            st.metric(label="Total Daily Protein Logged", value=f"{latest['Protein']} g", 
                      delta=f"Target: {st.session_state.user_profile['protein_target']}g")
        with score_col2:
            st.metric(label="Calculated Energy Balanced", value=f"{int(latest['Calories'])} kcal", 
                      delta=f"Target: {st.session_state.user_profile['calorie_target']} kcal", delta_color="inverse")
        with score_col3:
            st.metric(label="Execution Compliance Score", value=f"{latest['Day Score']} / 100")
            
        st.markdown("---")
        st.subheader("Macro Nutrient Split Today")
        macro_df = pd.DataFrame({
            "Macro": ["Protein", "Carbohydrates", "Fats", "Fiber"],
            "Grams": [latest['Protein'], latest['Carbs'], latest['Fat'], latest.get('Fiber', 0)]
        })
        st.bar_chart(macro_df, x="Macro", y="Grams")
        
        st.subheader("Historical Performance Tracker Log")
        st.dataframe(df_history, use_container_width=True)
    else:
        st.info("No analytics records generated for today yet. Capture your meal pictures in Tab 2 to populate the charts!")