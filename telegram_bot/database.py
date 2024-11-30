from datetime import timedelta, datetime
from utils import get_current_time_in_singapore
from dotenv import load_dotenv
from telegram.ext import ContextTypes

import os
from google.cloud import firestore

load_dotenv()

# INITIALISATIONS
def initialise_firestore():
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "maibelai-firebase-adminsdk-e53q1-f0545c7cfa.json"
    return firestore.Client()

db = initialise_firestore()

# USER PROFILE
def db_get_user_profile(user_id:str):
    try:
        user_doc = db.collection("users").document(user_id).get()
        if user_doc.exists: return user_doc.to_dict()
        else: return None
    except Exception as e:
        print(f"Error retrieving user: {e}")
        return None
    
async def db_set_user_profile(user_id:str, user_info:dict):
    try:
        user_ref = db.collection("users").document(user_id)
        user_ref.set(user_info, merge=True)
    except Exception as e:
        print(f"Error setting user profile: {e}")
    
async def sync_user_profile(context: ContextTypes.DEFAULT_TYPE):
    await reset_streaks(context)
    userid = str(context.job.user_id)
    user_data = context.user_data
    user_info = user_data.get("user_info", {})
    try:
        user_ref = db.collection("users").document(userid)
        user_ref.set(user_info, merge=True)
    except Exception as e:
        print(f"Error setting user profile: {e}")



# STREAKS, POINTS, LEADERBOARDS
def get_leaderboard():
    """Scheduled server side, output as list of dicts, globally accessible"""
    try:
        users_ref = db.collection("users")
        # Query users by current_streak in descending order
        query = users_ref.order_by("Streak", direction=firestore.Query.DESCENDING).limit(10)
        docs = query.stream()

        leaderboard = []
        for doc in docs:
            user_data = doc.to_dict()
            leaderboard.append({
                "Username": user_data.get("Username"),
                "Streak": user_data.get("Streak")
            })
        return leaderboard
    except Exception as e:
        print(f"Error retrieving leaderboard: {e}")
        return []

async def reset_streaks(context:ContextTypes.DEFAULT_TYPE):
    """Reset streaks locally for users if difference between last checkin and today > 1 day"""
    try:
        lastCheckin = context.user_data.get("user_info", {})["Last Check-in"]
        today = get_current_time_in_singapore().date()
        last_checkin_date = datetime.strptime(lastCheckin, "%Y-%m-%d").date()

        if last_checkin_date < today - timedelta(days=1):
            context.user_data["user_info"]["Streak"] = 0
        
    except Exception as e:
        print(f"Error resetting streaks: {e}")