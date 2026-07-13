import os
import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load environment variables from your local .env file
load_dotenv()

# Read the connection string directly from environment variables
DB_URL = os.environ.get("DATABASE_URL")

def get_db_connection():
    """Establishes and returns a live connection to your Supabase PostgreSQL database."""
    try:
        # 1. Check Streamlit Cloud Secrets first; fallback to local environment variable
        db_url = st.secrets.get("DATABASE_URL", os.getenv("DATABASE_URL"))
        
        # 2. Connect using the resolved URL string
        conn = psycopg2.connect(db_url)
        return conn
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None

def init_db():
    """Creates the necessary database tables if they do not exist."""
    commands = (
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS user_profiles (
            profile_id SERIAL PRIMARY KEY,
            user_id INT REFERENCES users(user_id) ON DELETE CASCADE UNIQUE,
            current_weight NUMERIC(5, 2) NOT NULL DEFAULT 150.50,
            age INT NOT NULL DEFAULT 31,
            height_str VARCHAR(10) NOT NULL DEFAULT '5''2"',
            calorie_target INT NOT NULL DEFAULT 1785,
            protein_target INT NOT NULL DEFAULT 105,
            fiber_target INT NOT NULL DEFAULT 25,
            water_target INT NOT NULL DEFAULT 10,
            start_date DATE NOT NULL DEFAULT CURRENT_DATE,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS daily_logs (
            log_id SERIAL PRIMARY KEY,
            user_id INT REFERENCES users(user_id) ON DELETE CASCADE,
            log_date DATE NOT NULL DEFAULT CURRENT_DATE,
            weight_today NUMERIC(5, 2),
            water_cups INT DEFAULT 0,
            step_count INT DEFAULT 0,
            meals_logged JSONB DEFAULT '{}'::jsonb,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (user_id, log_date)
        )
        """
    )
    
    conn = get_db_connection()
    if not conn:
        print("❌ Cannot initialize database because connection failed.")
        return
        
    try:
        cur = conn.cursor()
        for command in commands:
            cur.execute(command)
        cur.close()
        conn.commit()
        print("✅ All database tables verified/created successfully!")
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    # This allows you to test the connection and schemas individually from your terminal!
    print("Testing database initialization...")
    init_db()