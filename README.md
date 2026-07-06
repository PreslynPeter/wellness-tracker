# 6-Month Wellness Blueprint & Diet Tracker 🥗📊

A goal-oriented, interactive AI wellness application designed to help users track, manage, and optimize their health and nutritional goals over a structured 6-month timeline. Built using Python, Streamlit, and the Google Gemini API, this tool combines multimodal AI analysis with data tracking to turn everyday food logging into actionable wellness insights.

---

### 🌐 Live Deployment

* **Live Demo:** [🚀 Launch the App Live](https://wellness-tracker-goal-oriented.streamlit.app)
* **Source Code:** [💻 GitHub Repository](https://github.com/PreslynPeter/wellness-tracker)

---

### ⏳ The 6-Month Goal Tracking Framework

The application is structured around a **6-month timeline** to help users transition from baseline habits to sustainable wellness success. It tracks progression across key phases:

* **Months 1–2 (Foundation & Baseline):** Focuses on consistent logging, uncovering nutritional gaps, and establishing daily caloric and high-protein baselines.
* **Months 3–4 (Optimization & Conditioning):** Measures tracking consistency against target goals, fine-tuning macronutrient ratios based on personal fitness metrics.
* **Months 5–6 (Sustainability & Blueprint Generation):** Evaluates long-term trends and uses accumulated historical data to generate a customized, long-term personal health blueprint.

---

### ✨ Salient Features

* **Multimodal AI Food Analysis:** Users can upload food images or provide text descriptions of meals. Integrated with the **Google Gemini API**, the app instantly analyzes the inputs to estimate calorie counts and break down protein, fat, and carbohydrate content.
* **Dynamic Daily Metrics Tracking:** Features interactive dashboards to track daily water intake, sleep patterns, workout duration (e.g., treadmill sessions), and exact protein consumption targets.
* **Progressive Interactive Analytics:** Utilizes pandas-driven data frames to store tracking history, visualizing user metrics over time to show exact progress against the 6-month timeline goals.
* **Secure Environment Architecture:** Configured via encrypted Streamlit Secrets (`TOML` formatting) to keep internal API keys protected and completely safe from public exposure.
* **Production-Ready Deployment:** Packaged cleanly with an automated dependency pipeline (`requirements.txt`), fully optimized for lightweight cloud hosting environments.

---

### 🛠️ Tech Stack & Dependencies

* **Frontend/UI:** Streamlit
* **AI Core:** Google Generative AI Python SDK (`google-generativeai`)
* **Data Processing:** Pandas
* **Image Management:** Pillow (PIL)
* **Configuration:** Python-Dotenv / TOML
