import pytz
from datetime import time as datetime_time
from telegram.ext import CallbackContext
from database import reset_streaks, db_set_user_profile, get_leaderboard

async def sync_data_job(context:CallbackContext, userid:str):
    sync_time = datetime_time(hour=1, minute=5, second=30, tzinfo=pytz.timezone("Asia/Singapore"))
    job_name = "sync"
    existing_jobs = context.job_queue.get_jobs_by_name(job_name)
    for job in existing_jobs:
        if job.user_id == userid:
            print("Removing job: ", job)
            job.schedule_removal()
    context.job_queue.run_daily(db_set_user_profile, time=sync_time, name=job_name, user_id=userid)
    existing_jobs = context.job_queue.get_jobs_by_name(job_name)
        