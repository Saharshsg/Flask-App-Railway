from datetime import date, timedelta
from flask import current_app
from apscheduler.schedulers.background import BackgroundScheduler
from app import create_app, db
from app.models import User, Schedule
from app.admin.utils import run_auto_assignment_for_date
from app.notifications import send_daily_schedule_email, send_teams_notification
import sqlalchemy as sa

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

scheduler = BackgroundScheduler(daemon=True)
# Schedule to run every day at 6:00 PM (18:00)
scheduler.add_job(run_daily_assignment_and_notifications, 'cron', hour=18, minute=0) 