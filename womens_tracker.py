import streamlit as st
from google import genai
import pandas as pd
import datetime
import os
import json
from pydantic import BaseModel, Field
from PIL import Image
from dotenv import load_dotenv
from database import get_db_connection  # Imports your working Supabase connection helper

class MealMetrics(BaseModel):
    protein: float = Field(description="Total protein in grams")
    carbs: float = Field(description="Total carbohydrates in grams")
    fat: float = Field(description="Total fat in grams")
    fiber: float = Field(description="Total fiber in grams")
    estimated_items: list[str] = Field(description="List of items identified in the meal")

# --- 1. INITIAL SETUP & APP CONFIG ---
st.set_page_config(page_title="6-Month Wellness Blueprint", layout="wide")

script_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(script_dir, '.env')
load_dotenv(dotenv_path=env_path)

GENAI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Initialize persistent session states for dynamic DB auth
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'username' not in st.session_state:
    st.session_state.username = ""

# --- 2. DYNAMIC DATABASE AUTHENTICATION FLOW ---
if not st.session_state.logged_in:
    tab_login, tab_register = st.tabs(["🔒 Sign In", "✨ Create First-Time Account"])
    
    with tab_register:
        st.subheader("Welcome! Create Your Personalized Account")
        new_username = st.text_input("Choose Username", key="reg_user")
        new_email = st.text_input("Email Address", key="reg_email")
        new_password = st.text_input("Create Password", type="password", key="reg_pass")
        
        st.markdown("---")
        st.caption("Tell us a bit about your initial baseline stats:")
        init_weight = st.number_input("Current Weight (lbs)", value=150.50, step=0.1, key="reg_w")
        init_age = st.number_input("Age (Years)", value=31, step=1, key="reg_a")
        init_height = st.text_input("Height (e.g., 5'2\")", value="5'2\"", key="reg_h")
        
        if st.button("Register & Initialize My Blueprint", type="primary"):
            if new_username and new_email and new_password:
                conn = get_db_connection()
                if conn:
                    try:
                        cur = conn.cursor()
                        # 1. Store credentials inside 'users'
                        cur.execute(
                            """
                            INSERT INTO users (username, email, password_hash)
                            VALUES (%s, %s, %s) RETURNING user_id;
                            """,
                            (new_username, new_email, new_password)
                        )
                        inserted_id = cur.fetchone()[0]
                        
                        # 2. Seed initial targets into 'user_profiles'
                        cur.execute(
                            """
                            INSERT INTO user_profiles (user_id, current_weight, age, height_str)
                            VALUES (%s, %s, %s, %s);
                            """,
                            (inserted_id, init_weight, init_age, init_height)
                        )
                        conn.commit()
                        cur.close()
                        st.success("🎉 Account built successfully on Supabase! Please switch to the 'Sign In' tab.")
                    except Exception as e:
                        st.error(f"Registration failed (Username/Email might exist): {e}")
                    finally:
                        conn.close()
            else:
                st.warning("Please populate the username, email, and password blocks.")

    with tab_login:
        st.subheader("6-Month Blueprint Login")
        login_user = st.text_input("Username", key="auth_user")
        login_pass = st.text_input("Password", type="password", key="auth_pass")
        
        if st.button("Log In", type="primary"):
            conn = get_db_connection()
            if conn:
                try:
                    cur = conn.cursor()
                    cur.execute(
                        "SELECT user_id, username FROM users WHERE username = %s AND password_hash = %s;",
                        (login_user, login_pass)
                    )
                    user = cur.fetchone()
                    cur.close()
                    
                    if user:
                        st.session_state.logged_in = True
                        st.session_state.user_id = user[0]
                        st.session_state.username = user[1]
                        st.rerun()
                    else:
                        st.error("Invalid credentials. Try again or register an account.")
                except Exception as e:
                    st.error(f"Login pipeline failed: {e}")
                finally:
                    conn.close()

# --- 3. CORE LOGGED-IN APPLICATION ENVIRONMENT ---
else:
    # Sidebar control panel
    st.sidebar.write(f"Logged in as: **{st.session_state.username}** 👋")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.session_state.username = ""
        st.rerun()

    # Dynamic initialization of temporary page structures inside runtime state
    if "current_today_meals" not in st.session_state:
        st.session_state.current_today_meals = {}

    # Pull user targets directly from Supabase profile on load
    if "user_profile" not in st.session_state:
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT current_weight, age, height_str, calorie_target, protein_target, fiber_target, water_target, start_date 
                FROM user_profiles WHERE user_id = %s;
                """,
                (st.session_state.user_id,)
            )
            prof = cur.fetchone()
            cur.close()
            conn.close()
            
            if prof:
                st.session_state.user_profile = {
                    "weight": float(prof[0]), "age": int(prof[1]), "height": prof[2],
                    "calorie_target": int(prof[3]), "protein_target": int(prof[4]),
                    "fiber_target": int(prof[5]), "water_target": int(prof[6]), "start_date": prof[7]
                }
            else:
                # Default safety fallback structure if record parsing errors occur
                st.session_state.user_profile = {
                    "weight": 150.50, "age": 31, "height": "5'2\"",
                    "protein_target": 105, "fiber_target": 25, "calorie_target": 1785, "water_target": 10,
                    "start_date": datetime.date.today()
                }

    tab1, tab2, tab3 = st.tabs(["📋 1. Profile & 6-Month Goals", "📸 2. Daily Log", "📊 3. Scoreboard"])

    # ==========================================
    # TAB 1: USER DETAILS & TARGET CONFIGURATION
    # ==========================================
    with tab1:
        st.header("Personal Details & Targets")
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

        # Responsive Math formulas matching your logic setup
        weight_kg = weight * 0.45359237
        height_cm = 172.72 if "5'8" in height else (157.48 if "5'2" in height else 162.56)

        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 161
        responsive_calorie_target = int(bmr * 1.375)
        responsive_protein_target = int(weight_kg * 2.0)

        st.subheader("Daily Nutrient Targets")
        nut_col1, nut_col2, nut_col3, nut_col4 = st.columns(4)

        with nut_col1:
            target_protein = st.number_input("Target Protein (grams)", value=responsive_protein_target)
        with nut_col2:
            target_fiber = st.number_input("Target Fiber (grams)", value=st.session_state.user_profile["fiber_target"])
        with nut_col3:
            target_calories = st.number_input("Target Calories (kcal)", value=responsive_calorie_target)
        with nut_col4:
            responsive_water = 10 if weight_kg > 65 else 8
            target_water = st.number_input("Target Water (Cups)", value=responsive_water)

        if st.button("Lock In My Blueprint Settings", type="primary"):
            conn = get_db_connection()
            if conn:
                try:
                    cur = conn.cursor()
                    cur.execute(
                        """
                        UPDATE user_profiles 
                        SET current_weight=%s, age=%s, height_str=%s, calorie_target=%s, protein_target=%s, fiber_target=%s, water_target=%s, start_date=%s, updated_at=CURRENT_TIMESTAMP
                        WHERE user_id = %s;
                        """,
                        (weight, age, height, target_calories, target_protein, target_fiber, target_water, start_d, st.session_state.user_id)
                    )
                    conn.commit()
                    cur.close()
                    
                    st.session_state.user_profile.update({
                        "weight": weight, "age": age, "height": height, "protein_target": target_protein,
                        "fiber_target": target_fiber, "calorie_target": target_calories, "water_target": target_water, "start_date": start_d
                    })
                    st.success("🎯 Targets synced live to your database profile record!")
                except Exception as e:
                    st.error(f"Failed to update database profile: {e}")
                finally:
                    conn.close()

    # ==========================================
    # TAB 2: DAILY LOG (TEXT & OPTIONAL PHOTO)
    # ==========================================
    with tab2:
        st.header(f"Log Stats for {datetime.date.today().strftime('%A, %B %d')}")
        
        meta_col1, meta_col2 = st.columns(2)
        with meta_col1:
            steps = st.number_input("Total Daily Step Count", min_value=0, value=0, step=500)
        with meta_col2:
            water_cups = st.number_input("Total Water Consumed (Cups)", min_value=0, value=0, step=1)
            
        st.markdown("---")
        chosen_meal = st.selectbox("Which meal are you logging?", ["Breakfast", "Mid-Day Snack", "Lunch", "Tea & Evening Snack", "Dinner"])
        meal_time = st.time_input(f"What time did you have {chosen_meal}?", value=datetime.time(8, 0))
        
        result_json = None

        st.subheader("✍️ Record Your Meal Ingredients")
        user_text_input = st.text_area(
            "What did you eat?",
            placeholder="e.g., 1 cup of Greek yogurt, 100g strawberries, and a handful of almonds",
            key="manual_meal_text"
        )
        
        if st.button("Calculate Metrics from Text", type="primary"):
            if not user_text_input.strip():
                st.warning("Please type your meal contents before submitting.")
            else:
                with st.spinner("AI parsing your ingredients..."):
                    try:
                        client = genai.Client(api_key=GENAI_API_KEY)
                        
                        text_prompt = f"""
                        You are a strict nutritionist database app. Read this exact text meal description and compute total macronutrients.
                        Meal Description: "{user_text_input}"
                        Return ONLY a JSON object with exactly these keys: "protein", "carbs", "fat", "fiber", "estimated_items".
                        Do not include markdown formatting like ```json.
                        """
                        response = client.models.generate_content(
                            model='gemini-2.5-flash',
                            contents=text_prompt
                            )
                        result_json = json.loads(response.text.strip())
                    except Exception as e:
                        st.error(f"Error processing text input: {e}")

        st.markdown("---")
        with st.expander("📸 Prefer to use a picture instead? Click here to open Photo Mode"):
            uploaded_image = st.file_uploader(f"Choose a picture for {chosen_meal}", type=["jpg", "jpeg", "png"], key="meal_photo_uploader")
            if uploaded_image is not None:
                image = Image.open(uploaded_image)
                st.image(image, caption="Uploaded Food Plate", width=300)
                if st.button("Analyze Uploaded Image"):
                    with st.spinner("AI running visual ingestion mapping..."):
                        try:
                            genai.configure(api_key=GENAI_API_KEY)
                            model = genai.GenerativeModel('gemini-2.5-flash')
                            photo_prompt = """
                            Analyze this image of a meal and provide an accurate estimation of its nutritional properties.
                            Return ONLY a JSON object with exactly these keys: "protein", "carbs", "fat", "fiber", "estimated_items".
                            Do not include markdown formatting like ```json.
                            """
                            response = model.generate_content([photo_prompt, image])
                            result_json = json.loads(response.text.strip())
                        except Exception as e:
                            st.error(f"Error parsing image contents: {e}")

        if result_json:
            st.session_state.current_today_meals[chosen_meal] = {
                "time": meal_time.strftime("%I:%M %p"),
                "protein": float(result_json.get('protein', 0)),
                "carbs": float(result_json.get('carbs', 0)),
                "fat": float(result_json.get('fat', 0)),
                "fiber": float(result_json.get('fiber', 0))
            }
            st.rerun()

        if st.session_state.current_today_meals:
            st.markdown("---")
            st.subheader("Meals Tracked Today So Far:")
            for m, data in st.session_state.current_today_meals.items():
                st.markdown(f"🔹 **{m}** ({data['time']}) → Protein: {data['protein']}g | Carbs: {data['carbs']}g | Fat: {data['fat']}g | Fiber: {data.get('fiber', 0)}g")

            consumed_p = sum(info.get("protein", 0) for info in st.session_state.current_today_meals.values())
            consumed_c = sum(info.get("carbs", 0) for info in st.session_state.current_today_meals.values())
            consumed_f = sum(info.get("fat", 0) for info in st.session_state.current_today_meals.values())
            consumed_fib = sum(info.get("fiber", 0) for info in st.session_state.current_today_meals.values())
            consumed_cal = (consumed_p * 4) + (consumed_c * 4) + (consumed_f * 9)

            rem_cal = max(0, int(st.session_state.user_profile["calorie_target"] - consumed_cal))
            rem_p = max(0, int(st.session_state.user_profile["protein_target"] - consumed_p))
            rem_fib = max(0, int(st.session_state.user_profile["fiber_target"] - consumed_fib))

            st.markdown("#### 🔄 Updated Remaining Allowances")
            bot_col1, bot_col2, bot_col3 = st.columns(3)
            with bot_col1:
                st.metric(label="Calories Left", value=f"{rem_cal} kcal", delta=f"{int(consumed_cal)} consumed")
            with bot_col2:
                st.metric(label="Protein Remaining", value=f"{rem_p} g", delta=f"{int(consumed_p)}g tracked")
            with bot_col3:
                st.metric(label="Fiber Remaining", value=f"{rem_fib} g", delta=f"{int(consumed_fib)}g tracked")

        st.markdown("---")
        if st.button("Consolidate & Save Today's Final Metrics", type="primary"):
            if not st.session_state.current_today_meals:
                st.warning("Please record at least one meal first.")
            else:
                total_p = sum(info["protein"] for info in st.session_state.current_today_meals.values())
                total_c = sum(info["carbs"] for info in st.session_state.current_today_meals.values())
                total_f = sum(info["fat"] for info in st.session_state.current_today_meals.values())
                total_fib = sum(info.get("fiber", 0) for info in st.session_state.current_today_meals.values())
                calculated_calories = (total_p * 4) + (total_c * 4) + (total_f * 9)
                
                conn = get_db_connection()
                if conn:
                    try:
                        cur = conn.cursor()
                        # Execute UPSERT into daily_logs on Supabase
                        cur.execute(
                            """
                            INSERT INTO daily_logs (user_id, log_date, water_cups, step_count, meals_logged)
                            VALUES (%s, CURRENT_DATE, %s, %s, %s)
                            ON CONFLICT (user_id, log_date) 
                            DO UPDATE SET 
                                water_cups = EXCLUDED.water_cups,
                                step_count = EXCLUDED.step_count,
                                meals_logged = daily_logs.meals_logged || EXCLUDED.meals_logged;
                            """,
                            (st.session_state.user_id, water_cups, steps, json.dumps(st.session_state.current_today_meals))
                        )
                        conn.commit()
                        cur.close()
                        st.success("🎯 Metrics securely compiled and inserted directly to your cloud Supabase database!")
                    except Exception as e:
                        st.error(f"Database sync crash: {e}")
                    finally:
                        conn.close()

    # ==========================================
    # TAB 3: END-OF-DAY SCOREBOARD & ANALYSIS
    # ==========================================
    with tab3:
        st.header("📈 Compliance Tracking Dashboard")
        
        conn = get_db_connection()
        db_history = []
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("SELECT log_date, step_count, water_cups, meals_logged FROM daily_logs WHERE user_id = %s ORDER BY log_date ASC;", (st.session_state.user_id,))
                rows = cur.fetchall()
                cur.close()
                
                for r in rows:
                    m_logged = r[3] if isinstance(r[3], dict) else json.loads(r[3] if r[3] else '{}')
                    tp = sum(info.get("protein", 0) for info in m_logged.values())
                    tc = sum(info.get("carbs", 0) for info in m_logged.values())
                    tf = sum(info.get("fat", 0) for info in m_logged.values())
                    tfib = sum(info.get("fiber", 0) for info in m_logged.values())
                    tcal = (tp * 4) + (tc * 4) + (tf * 9)
                    
                    p_scr = 100 if tp >= st.session_state.user_profile["protein_target"] else int((tp / st.session_state.user_profile["protein_target"]) * 100)
                    w_scr = 100 if r[2] >= st.session_state.user_profile["water_target"] else int((r[2] / st.session_state.user_profile["water_target"]) * 100)
                    c_diff = abs(tcal - st.session_state.user_profile["calorie_target"])
                    c_scr = max(0, 100 - int((c_diff / st.session_state.user_profile["calorie_target"]) * 100)) if tcal > 0 else 0
                    
                    db_history.append({
                        "Date": r[0], "Steps": r[1], "Water": r[2], "Protein": tp, "Carbs": tc, "Fat": tf, "Fiber": tfib, "Calories": tcal, "Day Score": int((p_scr + w_scr + c_scr) / 3)
                    })
            except Exception as e:
                st.error(f"Error loading score tables: {e}")
            finally:
                conn.close()

        if db_history:
            df_history = pd.DataFrame(db_history)
            latest = df_history.iloc[-1]
            
            st.subheader("Latest Performance Breakdown")
            score_col1, score_col2, score_col3 = st.columns(3)
            with score_col1:
                st.metric(label="Total Daily Protein Logged", value=f"{latest['Protein']} g", delta=f"Target: {st.session_state.user_profile['protein_target']}g")
            with score_col2:
                st.metric(label="Calculated Energy Balance", value=f"{int(latest['Calories'])} kcal", delta=f"Target: {st.session_state.user_profile['calorie_target']} kcal", delta_color="inverse")
            with score_col3:
                st.metric(label="Execution Compliance Score", value=f"{latest['Day Score']} / 100")
                
            st.markdown("---")
            st.subheader("Macro Nutrient Split Today")
            macro_df = pd.DataFrame({
                "Macro": ["Protein", "Carbohydrates", "Fats", "Fiber"],
                "Grams": [latest['Protein'], latest['Carbs'], latest['Fat'], latest['Fiber']]
            })
            st.bar_chart(macro_df, x="Macro", y="Grams")
            
            st.subheader("Historical Performance Tracker Log")
            st.dataframe(df_history, use_container_width=True)
        else:
            st.info("No analytics records found in Supabase. Capture or type your meal logs in Tab 2 to populate historical charts!")