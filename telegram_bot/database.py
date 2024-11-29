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
    
async def db_set_user_profile(context: ContextTypes.DEFAULT_TYPE):
    userid = str(context.job.user_id)
    user_data = context.user_data
    user_info = user_data.get("user_info", {})
    try:
        user_ref = db.collection("users").document(userid)
        user_ref.set(user_info, merge=True)
        print(f"User profile for {userid} updated successfully in Firestore.")
    except Exception as e:
        print(f"Error setting user profile: {e}")



# STREAKS, POINTS, LEADERBOARDS
def get_leaderboard():
    """Scheduled server side, output as list of dicts, globally accessible"""
    try:
        users_ref = db.collection("users")
        # Query users by current_streak in descending order
        query = users_ref.order_by("current_streak", direction=firestore.Query.DESCENDING).limit(10)
        docs = query.stream()

        leaderboard = []
        for doc in docs:
            user_data = doc.to_dict()
            leaderboard.append({
                "username": user_data.get("username"),
                "current_streak": user_data.get("current_streak")
            })
        return leaderboard
    except Exception as e:
        print(f"Error retrieving leaderboard: {e}")
        return []

async def reset_streaks(context):
    """Reset streaks locally for users if difference between last checkin and today > 1 day"""
    try:
        user_id = context.user_data.get("userid", None)
        if user_id is None: print("User ID not found in context."); return
        
        user_profile = db_get_user_profile(user_id)
        if not user_profile: print(f"No profile found for user {user_id}."); return

        last_checkin = user_profile.get("last_checkin")
        if not last_checkin: print("No last check-in found."); return
        
        today = get_current_time_in_singapore().date()
        last_checkin_date = last_checkin.date()
        if last_checkin_date < today - timedelta(days=1):
            context.user_data["current_streak"] = 0
            context.user_data["last_checkin"] = today
        
    except Exception as e:
        print(f"Error resetting streaks: {e}")