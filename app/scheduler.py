from datetime import date, timedelta
from flask import current_app
from apscheduler.schedulers.background import BackgroundScheduler
from app import create_app, db
from app.models import User, Schedule
from app.admin.utils import run_auto_assignment_for_date
from app.notifications import send_daily_schedule_email, send_teams_notification
import sqlalchemy as sa
from app.email import send_daily_roster_email
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

def get_next_office_day():
    """Determines the date for the next applicable office day."""
    today = date.today()
    # If it's a weekend or past Wednesday, schedule for next Monday.
    if today.weekday() >= 3: # Thursday, Friday, Saturday, Sunday
        return today + timedelta(days=(7 - today.weekday()))
    # If Mon, Tue, Wed, schedule for today
    return today

def run_daily_assignment_and_notifications():
    """The main job to be run by the scheduler."""
    app = create_app()
    with app.app_context():
        current_app.logger.info("Scheduler job started: Running daily assignment and notifications...")
        
        assign_date = get_next_office_day()
        
        # --- 1. Run Auto-Assignment ---
        run_auto_assignment_for_date(assign_date)
        
        # --- 2. Fetch Final Schedule Data ---
        all_users = db.session.scalars(sa.select(User)).all()
        week_start = assign_date - timedelta(days=assign_date.weekday())
        office_days = [week_start + timedelta(days=i) for i in range(3)]

        all_entries = db.session.scalars(
            sa.select(Schedule).where(Schedule.date.in_(office_days)).options(sa.orm.joinedload(Schedule.user))
        ).all()

        final_schedule = {}
        for day in office_days:
            day_name = day.strftime('%A')
            attendees = [e for e in all_entries if e.date == day and e.status == 'Yes']
            final_schedule[day_name] = {
                'date': day,
                'attendees': sorted(attendees, key=lambda x: x.user.username),
                'total_attendees': len(attendees),
                'veg_count': sum(1 for e in attendees if e.meal_preference == 'Veg'),
                'non_veg_count': sum(1 for e in attendees if e.meal_preference == 'Non-Veg')
            }

        # --- 3. Send Notifications ---
        if any(day['attendees'] for day in final_schedule.values()):
            send_daily_schedule_email(users=all_users, schedule_data=final_schedule)
            send_teams_notification(schedule_data=final_schedule)
        else:
            current_app.logger.info("No one is scheduled. Skipping notifications.")
            
        current_app.logger.info("Scheduler job finished.")

def auto_assign_job():
    """Runs the auto-assignment logic for two days from now."""
    assign_date = date.today() + timedelta(days=2)
    log.info(f"Running auto-assignment job for {assign_date}...")
    try:
        run_auto_assignment_for_date(assign_date)
        log.info(f"Auto-assignment for {assign_date} completed successfully.")
    except Exception as e:
        log.error(f"Error during auto-assignment for {assign_date}: {e}", exc_info=True)

def send_daily_roster_job():
    """Queries for today's attendees and sends the roster email."""
    roster_date = date.today()
    log.info(f"Running daily roster email job for {roster_date}...")
    try:
        attendees_schedules = db.session.scalars(
            sa.select(Schedule).where(
                Schedule.date == roster_date,
                Schedule.status == 'Yes'
            ).options(sa.orm.joinedload(Schedule.user))
        ).all()

        if attendees_schedules:
            attending_users = [schedule.user for schedule in attendees_schedules]
            send_daily_roster_email(attending_users, roster_date)
            log.info(f"Daily roster for {roster_date} sent to all users.")
        else:
            log.info(f"No attendees for {roster_date}. No roster email sent.")
    except Exception as e:
        log.error(f"Error during daily roster email job for {roster_date}: {e}", exc_info=True)

scheduler = BackgroundScheduler(daemon=True)
# Schedule to run every day at 6:00 PM (18:00)
scheduler.add_job(run_daily_assignment_and_notifications, 'cron', hour=18, minute=0)
# Schedule the auto-assignment job to run daily at a specific time, e.g., 1 AM
scheduler.add_job(auto_assign_job, 'cron', hour=1, minute=0)
# Schedule the daily roster email to run daily, e.g., at 7 AM
scheduler.add_job(send_daily_roster_job, 'cron', hour=7, minute=0)

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        log.info("Starting scheduled jobs...")
        auto_assign_job()
        send_daily_roster_job()
        log.info("Scheduled jobs finished.") 