# 🙋‍♀️ 6-Month Personal Wellness & AI Nutrition Tracker

An AI-powered web application designed to help women track their 6-month weight loss milestones, log daily physical metrics, and automate nutritional analysis using computer vision. Built with Python, Streamlit, and the Gemini 3.5 Flash API.

![Streamlit App](https://img.shields.io/badge/Framework-Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)
![Google Gemini](https://img.shields.io/badge/AI-Google%20Gemini-4285F4?style=for-the-badge&logo=google&logoColor=white)
![Python](https://img.shields.io/badge/Language-Python-3776AB?style=for-the-badge&logo=python&logoColor=white)

---

## 🚀 Key Features

- **Personalized 6-Month Blueprint:** Captures user baseline telemetry (weight, age, height) and configures explicit daily nutrient parameters (protein, caloric ceiling, fluid targets).
- **Computer Vision Meal Logging:** Integrates a multimodal generative AI pipeline allowing users to upload plate images for automated food identification and macronutrient estimation (protein, carbs, fats).
- **Dynamic Session Architecture:** Utilizes continuous state preservation (`st.session_state`) across tab navigation arrays to maintain a seamless data workflow.
- **Execution Scoreboard Dashboard:** Consolidates daily inputs, performs physiological mass calculations ($1\text{g P/C} = 4\text{kcal}, 1\text{g F} = 9\text{kcal}$), and evaluates daily execution compliance via an algorithmic $0\text{-}100\%$ scoring system.
- **Secure Environment Configurations:** Implements runtime decryption of protected API credentials using standalone `.env` abstractions to isolate production keys.

---

## 🛠️ Tech Stack & Architecture

- **Frontend / UI:** Streamlit (Dynamic single-page script processing execution architecture)
- **AI Core Engine:** Google Gemini 1.5 Flash API (Multimodal prompt optimization layer)
- **Data Engineering:** Pandas (Dataframe restructuring and series mapping arrays)
- **Image Operations:** Pillow (PIL Image stream validation and metadata rendering)
- **Environment Logic:** Python-Dotenv (Local OS system environment parsing)

---

## ⚙️ Installation & Local Setup

### 1. Clone the Repository
```bash
git clone [https://github.com/your-username/womens-ai-wellness-tracker.git](https://github.com/your-username/womens-ai-wellness-tracker.git)
cd womens-ai-wellness-tracker
