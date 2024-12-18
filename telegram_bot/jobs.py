import pytz
from datetime import time as datetime_time
from telegram.ext import CallbackContext
from database import reset_streaks, sync_user_profile, get_leaderboard

async def sync_data_job(context:CallbackContext, userid:str):
    sync_time = datetime_time(hour=0, minute=0, second=0, tzinfo=pytz.timezone("Asia/Singapore"))
    job_name = "sync"
    existing_jobs = context.job_queue.get_jobs_by_name(job_name)
    for job in existing_jobs:
        if job.user_id == userid:
            job.schedule_removal()
    context.job_queue.run_daily(sync_user_profile, time=sync_time, name=job_name, user_id=userid)
    existing_jobs = context.job_queue.get_jobs_by_name(job_name)

        