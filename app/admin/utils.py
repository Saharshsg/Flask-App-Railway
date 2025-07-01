from datetime import date, timedelta
from app import db
from app.models import User, Schedule
import sqlalchemy as sa
import random

OFFICE_CAPACITY = 6

def get_previous_office_day(current_date):
    """
    Finds the previous office day (Mon, Tue, Wed).
    Returns None if the current day is Monday.
    """
    if current_date.weekday() == 1: # Tuesday
        return current_date - timedelta(days=1)
    if current_date.weekday() == 2: # Wednesday
        return current_date - timedelta(days=1)
    return None # Monday or other days

def run_auto_assignment_for_date(assign_date):
    """
    Core logic to run auto-assignment for a specific date.
    This can be called from both the scheduler and admin routes.
    """
    all_users = db.session.scalars(sa.select(User)).all()
    schedule_entries = db.session.scalars(sa.select(Schedule).where(Schedule.date == assign_date)).all()
    entry_map = {entry.user_id: entry for entry in schedule_entries}

    # Interns are auto-assigned 'Yes' unless they have explicitly said 'No'
    interns = [u for u in all_users if u.is_intern]
    for intern in interns:
        if intern.id not in entry_map:
            new_entry = Schedule(user_id=intern.id, date=assign_date, status='Yes', meal_preference='Veg', was_auto_assigned=True)
            db.session.add(new_entry)
        elif entry_map[intern.id].status is None:
             entry_map[intern.id].status = 'Yes'
             entry_map[intern.id].was_auto_assigned = True
    db.session.flush() # Ensure new entries get IDs for the next query

    # Re-fetch entries to get an accurate count
    current_yes_count = db.session.scalar(
        sa.select(sa.func.count(Schedule.id)).where(Schedule.date == assign_date, Schedule.status == 'Yes')
    )
    
    # Fill Remaining Slots
    slots_to_fill = OFFICE_CAPACITY - current_yes_count
    
    if slots_to_fill > 0:
        responded_ids = {entry.user_id for entry in schedule_entries}
        # Get all non-intern users who haven't responded yet
        unassigned_standard_users = [
            u for u in all_users if not u.is_intern and u.id not in responded_ids
        ]
        
        # --- New logic for rotation ---
        previous_day = get_previous_office_day(assign_date)
        if previous_day:
            prev_day_auto_assigned_ids = db.session.scalars(
                sa.select(Schedule.user_id).where(
                    Schedule.date == previous_day,
                    Schedule.was_auto_assigned == True,
                    Schedule.status == 'Yes'
                )
            ).all()
            
            # Prioritize users who were not assigned on the previous day
            priority_users = [u for u in unassigned_standard_users if u.id not in prev_day_auto_assigned_ids]
            other_users = [u for u in unassigned_standard_users if u.id in prev_day_auto_assigned_ids]

            random.shuffle(priority_users)
            random.shuffle(other_users)
            
            eligible_for_random = priority_users + other_users
        else:
            # For Monday, or if no previous day logic applies, just shuffle everyone
            eligible_for_random = unassigned_standard_users
            random.shuffle(eligible_for_random)
        
        num_to_assign = min(len(eligible_for_random), slots_to_fill)
        
        for i in range(num_to_assign):
            user_to_assign = eligible_for_random[i]
            new_entry = Schedule(user_id=user_to_assign.id, date=assign_date, status='Yes', meal_preference='Veg', was_auto_assigned=True)
            db.session.add(new_entry)
    
    db.session.commit() 