import psycopg2
import os
from datetime import timedelta
from utils import get_current_time_in_singapore
from dotenv import load_dotenv

load_dotenv()

# INITIALISATIONS
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
    # cursor.execute('''
    #     DROP TABLE users
    # ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGSERIAL PRIMARY KEY,
            username TEXT NOT NULL,
            onboardDay INTEGER DEFAULT 1,
            onboardTime TIMESTAMP,
            age TEXT,
            gender TEXT,
            workouts TEXT,
            goal TEXT,
            limitations TEXT[]
        )
    ''')
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

def db_modify_limitation(user_id, limitation, action):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if action == "append":
        cursor.execute('''
            UPDATE users
            SET limitations = array_append(COALESCE(limitations, '{}'), %s)
            WHERE user_id = %s
        ''', (limitation, user_id))
    elif action == "remove":
        cursor.execute('''
            UPDATE users
            SET limitations = array_remove(limitations, %s)
            WHERE user_id = %s
        ''', (limitation, user_id))
    else:
        raise ValueError("Invalid action. Use 'append' or 'remove'.")
    
    conn.commit()
    conn.close()


def db_get_user_profile(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT onboardDay, onboardTime, age, gender, workouts, goal, limitations FROM users 
        WHERE user_id = %s
    ''', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result

def db_update_user_profile(user_id, field, value):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(f'''
            UPDATE users 
            SET {field} = %s
            WHERE user_id = %s
        ''', (value, user_id))
        conn.commit()
    except Exception as e:
        print(f"Error updating user profile: {e}")
        conn.rollback()
    finally:
        conn.close()

# STREAKS, POINTS, LEADERBOARDS
def update_streak(user_id, username, last_checkin, current_streak):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO streaks (user_id, username, last_checkin, current_streak)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (user_id) DO UPDATE SET
        last_checkin = EXCLUDED.last_checkin,
        current_streak = EXCLUDED.current_streak
    ''', (user_id, username, last_checkin, current_streak))
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

async def reset_streaks(context): # Context parameter required for job queue
    conn = get_db_connection()
    cursor = conn.cursor()
    today = get_current_time_in_singapore().date()

    cursor.execute('SELECT user_id, last_checkin, current_streak FROM streaks')
    users = cursor.fetchall()

    for user_id, last_checkin, current_streak in users:
        print(user_id)
        last_checkin_date = last_checkin
        if last_checkin_date < today - timedelta(days=1):
            cursor.execute('''
                UPDATE streaks
                SET current_streak = 0
                WHERE user_id = %s
            ''', (user_id,))
    
    conn.commit()
    conn.close()
