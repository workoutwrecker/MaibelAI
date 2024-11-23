import psycopg2
import os
from datetime import datetime, timedelta
from utils import get_current_time_in_singapore
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    return psycopg2.connect(
        dbname='maibel',
        user='postgres',
        password=os.getenv("POSTGRE_PASS"),
        host='localhost',
        port='5432'
    )

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS streaks (
            user_id BIGSERIAL PRIMARY KEY,
            username TEXT,
            last_checkin DATE,
            current_streak INTEGER
        )
    ''')
    conn.commit()
    conn.close()

def update_streak(user_id, username, last_checkin, current_streak):
    conn = get_db_connection()
    cursor = conn.cursor()
    print(f"Updating streak for user {user_id}: {last_checkin} - {current_streak}")
    cursor.execute('''
        INSERT INTO streaks (user_id, username, last_checkin, current_streak)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (user_id) DO UPDATE SET
        last_checkin = EXCLUDED.last_checkin,
        current_streak = EXCLUDED.current_streak
    ''', (user_id, username, last_checkin, current_streak))
    print(f"Updated streak for user {user_id}: {last_checkin} - {current_streak}")
    conn.commit()
    conn.close()

def get_leaderboard():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT username, current_streak FROM streaks
        ORDER BY current_streak DESC
        LIMIT 10
    ''')
    leaderboard = cursor.fetchall()
    conn.close()
    return leaderboard

def reset_streaks():
    conn = get_db_connection()
    cursor = conn.cursor()
    today = get_current_time_in_singapore().date()

    cursor.execute('SELECT user_id, last_checkin, current_streak FROM streaks')
    users = cursor.fetchall()

    for user_id, last_checkin, current_streak in users:
        last_checkin_date = last_checkin
        if last_checkin_date < today - timedelta(days=1):
            cursor.execute('''
                UPDATE streaks
                SET current_streak = 0
                WHERE user_id = %s
            ''', (user_id,))
    
    conn.commit()
    conn.close()
