from flask import render_template, flash, redirect, url_for, request, abort
from app import db
from app.main import bp
from app.main.forms import AttendanceForm, ReassignmentForm, ReassignmentRequestForm
from flask_login import current_user, login_required
from app.models import User, Schedule
from datetime import date, timedelta
import sqlalchemy as sa
from app.email import send_email, send_swap_request_email

# Constants for clarity
OFFICE_CAPACITY = 6
OFFICE_DAYS = [2, 3, 4] # Wednesday, Thursday, Friday

@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = AttendanceForm()

    # Consolidated logic to handle all POST requests from the index page
    if request.method == 'POST':
        day_str = request.form.get('day_date')
        new_status = request.form.get('status')

        if not day_str or not new_status:
            flash('Invalid request. Please try again.', 'danger')
            return redirect(url_for('main.index'))
            
        day_date = date.fromisoformat(day_str)
        
        # Fetch existing entry or create a new one
        schedule_entry = db.session.scalar(
            sa.select(Schedule).where(
                Schedule.user_id == current_user.id,
                Schedule.date == day_date
            )
        ) or Schedule(user_id=current_user.id, date=day_date)

        # Logic for when a user marks themselves as 'Yes'
        if new_status == 'Yes':
            if not form.validate_on_submit():
                # This happens if meal preference is missing
                flash('Please select a meal preference to confirm your attendance.', 'warning')
                return redirect(url_for('main.index'))
            
            # Check for office capacity before confirming
            attendees_count = db.session.scalar(
                sa.select(sa.func.count(Schedule.id)).where(
                    Schedule.date == day_date, Schedule.status == 'Yes'
                )
            )
            is_newly_attending = not schedule_entry.id or schedule_entry.status != 'Yes'
            if attendees_count >= OFFICE_CAPACITY and is_newly_attending:
                flash(f'Sorry, the office is already full for {day_date.strftime("%A, %b %d")}.', 'warning')
                return redirect(url_for('main.index'))
            
            schedule_entry.meal_preference = form.meal_preference.data

        # Logic for when a user marks themselves as 'No'
        elif new_status == 'No':
            schedule_entry.meal_preference = None # Clear meal preference

        was_attending = schedule_entry.id and schedule_entry.status == 'Yes'
        schedule_entry.status = new_status
        db.session.add(schedule_entry)
        db.session.commit()

        # If a user just cancelled, try to auto-assign a replacement
        if was_attending and new_status == 'No':
            # This logic can be extracted to a helper if it gets complex
            available_user_entry = db.session.scalars(
                sa.select(Schedule).where(
                    Schedule.date == day_date,
                    Schedule.is_available == True
                ).order_by(Schedule.id) # Simple ordering for now
            ).first()

            if available_user_entry:
                available_user_entry.status = 'Yes'
                available_user_entry.meal_preference = 'Veg' # Default
                available_user_entry.was_auto_assigned = True
                available_user_entry.is_available = False
                db.session.commit()
                # Consider notifying this user
                user_to_notify = db.session.get(User, available_user_entry.user_id)
                flash(f'You have cancelled your spot. {user_to_notify.username} has been auto-assigned to fill it.', 'info')
        
        flash('Your preference has been saved!', 'success')
        return redirect(url_for('main.index'))


    # --- GET request logic remains the same ---
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())
    if today.weekday() > OFFICE_DAYS[-1]:
        start_of_week += timedelta(weeks=1)

    week_dates = [start_of_week + timedelta(days=i) for i in range(5)]
    
    user_schedule_entries = db.session.scalars(
        sa.select(Schedule).where(
            Schedule.user_id == current_user.id,
            Schedule.date.in_(week_dates)
        )
    ).all()
    user_choices = {entry.date.isoformat(): entry for entry in user_schedule_entries}

    all_schedule_entries = db.session.scalars(
        sa.select(Schedule).where(
            Schedule.date.in_(week_dates)
        ).options(sa.orm.joinedload(Schedule.user))
    ).all()

    schedule_data = {}
    for i in OFFICE_DAYS:
        day_date = start_of_week + timedelta(days=i)
        day_name = day_date.strftime('%A')
        
        attendees = [e.user.username for e in all_schedule_entries if e.date == day_date and e.status == 'Yes']
        
        schedule_data[day_name] = {
            'date': day_date,
            'attendees': sorted(attendees),
            'slots_filled': len(attendees),
            'slots_available': OFFICE_CAPACITY - len(attendees),
            'user_choice': user_choices.get(day_date.isoformat()),
            'is_past': day_date < today
        }

    return render_template('index.html', title='Home', schedule_data=schedule_data, form=form, OFFICE_CAPACITY=OFFICE_CAPACITY)

@bp.route('/toggle_availability/<date_iso>', methods=['POST'])
@login_required
def toggle_availability(date_iso):
    day_date = date.fromisoformat(date_iso)
    
    schedule_entry = db.session.scalar(
        sa.select(Schedule).where(
            Schedule.user_id == current_user.id,
            Schedule.date == day_date
        )
    )

    if not schedule_entry:
        # Create a new entry if one doesn't exist, marking them available
        schedule_entry = Schedule(
            user_id=current_user.id, 
            date=day_date, 
            status='No', # Explicitly not attending
            is_available=True
        )
        db.session.add(schedule_entry)
        flash('You have been marked as available for this day.', 'success')
    else:
        # Toggle existing entry's availability
        schedule_entry.is_available = not schedule_entry.is_available
        if schedule_entry.is_available:
            flash('You have been marked as available for this day.', 'success')
        else:
            flash('You are no longer marked as available for this day.', 'info')
    
    db.session.commit()
    return redirect(url_for('main.index'))

@bp.route('/request_reassignment/<int:schedule_id>', methods=['GET', 'POST'])
@login_required
def request_reassignment(schedule_id):
    schedule_entry = db.get_or_404(Schedule, schedule_id)
    if schedule_entry.user_id != current_user.id:
        flash('You can only request reassignment for your own schedule.', 'danger')
        return redirect(url_for('main.index'))

    form = ReassignmentRequestForm()
    if form.validate_on_submit():
        schedule_entry.reassignment_request = True
        schedule_entry.reassignment_reason = form.reason.data
        db.session.commit()
        
        # Send notification email to admin
        send_swap_request_email(current_user, schedule_entry)
        
        flash('Your request for reassignment has been submitted.', 'success')
        return redirect(url_for('main.index'))
    
    return render_template('request_reassignment.html', 
                           title='Request Reassignment', 
                           form=form, 
                           schedule=schedule_entry) 