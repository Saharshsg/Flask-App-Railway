from flask import render_template, flash, redirect, url_for, request, abort
from app import db
from app.main import bp
from app.main.forms import AttendanceForm, ReassignmentForm
from flask_login import current_user, login_required
from app.models import User, Schedule, WeekConfig
from datetime import date, timedelta
import sqlalchemy as sa
from app.email import send_email, send_swap_request_email
import calendar

# Constants for clarity
OFFICE_CAPACITY = 6
OFFICE_DAYS = [1, 2, 4]  # Tuesday, Wednesday, Friday (0=Monday, 1=Tuesday, etc.)
OFFICE_DAY_NAMES = ['Tuesday', 'Wednesday', 'Friday']

def get_week_start(target_date):
    """Get Monday of the week containing target_date"""
    return target_date - timedelta(days=target_date.weekday())

def get_current_week_dates():
    """Get the dates for the current active week based on today's date"""
    today = date.today()
    
    # If today is Saturday or Sunday, show next week
    if today.weekday() >= 5:  # Saturday or Sunday
        next_monday = today + timedelta(days=(7 - today.weekday()))
        week_start = next_monday
    else:
        # Check if we've passed Friday of current week
        week_start = get_week_start(today)
        friday_of_week = week_start + timedelta(days=4)  # Friday
        
        if today > friday_of_week:
            # Move to next week
            week_start = week_start + timedelta(weeks=1)
    
    return week_start

def is_week_unlocked(week_start_date):
    """Check if a week is unlocked for employee access"""
    week_config = db.session.scalar(
        sa.select(WeekConfig).where(WeekConfig.week_start_date == week_start_date)
    )
    
    if not week_config:
        # Week doesn't exist in config, so it's locked by default
        return False
    
    return not week_config.is_locked

@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    # Redirect to the current week view
    week_start = get_current_week_dates()
    return redirect(url_for('main.index_week', week_start=week_start.isoformat()))

@bp.route('/toggle_availability/<date_iso>', methods=['POST'])
@login_required
def toggle_availability(date_iso):
    day_date = date.fromisoformat(date_iso)
    week_start = get_week_start(day_date)
    
    # Check if week is unlocked (admins can always access)
    if not current_user.is_admin and not is_week_unlocked(week_start):
        flash('Cannot modify availability - this week is locked.', 'danger')
        return redirect(url_for('main.index'))
    
    # Prevent changes to past days (except for admins)
    if not current_user.is_admin and day_date < date.today():
        flash('Cannot modify past dates.', 'danger')
        return redirect(url_for('main.index'))
    
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
    # Try to redirect back to the week view if possible
    week_start = get_week_start(day_date)
    return redirect(url_for('main.index_week', week_start=week_start.isoformat()))

@bp.route('/request_reassignment/<int:schedule_id>', methods=['GET', 'POST'])
@login_required
def request_reassignment(schedule_id):
    schedule_entry = db.get_or_404(Schedule, schedule_id)
    if schedule_entry.user_id != current_user.id:
        flash('You can only request reassignment for your own schedule.', 'danger')
        return redirect(url_for('main.index'))

    week_start = get_week_start(schedule_entry.date)
    
    # Check if week is unlocked (admins can always access)
    if not current_user.is_admin and not is_week_unlocked(week_start):
        flash('Cannot request reassignment - this week is locked.', 'danger')
        return redirect(url_for('main.index'))

    form = ReassignmentForm()
    if form.validate_on_submit():
        schedule_entry.reassignment_request = True
        schedule_entry.reassignment_reason = form.reason.data
        db.session.commit()
        
        # Send notification email to admin
        send_swap_request_email(current_user, schedule_entry)
        
        flash('Your request for reassignment has been submitted.', 'success')
        week_start = get_week_start(schedule_entry.date)
        return redirect(url_for('main.index_week', week_start=week_start.isoformat()))
    
    return render_template('request_reassignment.html', 
                           title='Request Reassignment', 
                           form=form, 
                           schedule_entry=schedule_entry)

@bp.route('/calendar')
@bp.route('/calendar/<int:year>/<int:month>')
@login_required
def calendar_view(year=None, month=None):
    """Display a monthly calendar view"""
    today = date.today()
    
    if year is None or month is None:
        year, month = today.year, today.month
    
    # Get the first day of the month and calculate calendar
    first_day = date(year, month, 1)
    
    # Get previous and next months
    if month == 1:
        prev_month = date(year - 1, 12, 1)
    else:
        prev_month = date(year, month - 1, 1)
    
    if month == 12:
        next_month = date(year + 1, 1, 1)
    else:
        next_month = date(year, month + 1, 1)
    
    # Get all days in the month calendar view (including padding days from prev/next month)
    cal = calendar.monthcalendar(year, month)
    
    # Get all schedule data for the month
    month_start = first_day.replace(day=1)
    if month == 12:
        month_end = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        month_end = date(year, month + 1, 1) - timedelta(days=1)
    
    # Include a few days from prev/next month for calendar display
    cal_start = month_start - timedelta(days=10)
    cal_end = month_end + timedelta(days=10)
    
    all_schedule_entries = db.session.scalars(
        sa.select(Schedule).where(
            Schedule.date >= cal_start,
            Schedule.date <= cal_end
        ).options(sa.orm.joinedload(Schedule.user))
    ).all()
    
    user_schedule_entries = db.session.scalars(
        sa.select(Schedule).where(
            Schedule.user_id == current_user.id,
            Schedule.date >= cal_start,
            Schedule.date <= cal_end
        )
    ).all()
    
    # Organize schedule data by date
    schedule_by_date = {}
    user_schedule_by_date = {entry.date: entry for entry in user_schedule_entries}
    
    for entry in all_schedule_entries:
        if entry.date not in schedule_by_date:
            schedule_by_date[entry.date] = {'attending': 0, 'total': 0}
        if entry.status == 'Yes':
            schedule_by_date[entry.date]['attending'] += 1
        schedule_by_date[entry.date]['total'] += 1
    
    # Build calendar weeks
    calendar_weeks = []
    for week_days in cal:
        week_start_date = None
        week_data = {'days': []}
        
        for day_num in week_days:
            if day_num == 0:
                # Day from previous or next month
                if len(week_data['days']) == 0:
                    # Beginning of month - days from previous month
                    if month == 1:
                        day_date = date(year - 1, 12, calendar.monthrange(year - 1, 12)[1] - (7 - len([d for d in week_days if d != 0])) + len(week_data['days']) + 1)
                    else:
                        day_date = date(year, month - 1, calendar.monthrange(year, month - 1)[1] - (7 - len([d for d in week_days if d != 0])) + len(week_data['days']) + 1)
                else:
                    # End of month - days from next month
                    if month == 12:
                        day_date = date(year + 1, 1, len(week_data['days']) - len([d for d in week_days[:len(week_data['days'])] if d != 0]) + 1)
                    else:
                        day_date = date(year, month + 1, len(week_data['days']) - len([d for d in week_days[:len(week_data['days'])] if d != 0]) + 1)
                is_current_month = False
            else:
                day_date = date(year, month, day_num)
                is_current_month = True
            
            if week_start_date is None and day_date.weekday() == 0:  # Monday
                week_start_date = day_date
            
            is_office_day = day_date.weekday() in OFFICE_DAYS
            is_today = day_date == today
            
            # Get schedule info
            schedule_info = None
            user_status = None
            if day_date in schedule_by_date:
                schedule_info = schedule_by_date[day_date]
            if day_date in user_schedule_by_date:
                user_entry = user_schedule_by_date[day_date]
                user_status = user_entry.status
                if user_entry.status == 'Yes' and user_entry.meal_preference:
                    user_status += f" ({user_entry.meal_preference})"
            
            week_data['days'].append({
                'date': day_date,
                'is_current_month': is_current_month,
                'is_office_day': is_office_day,
                'is_today': is_today,
                'schedule_info': schedule_info,
                'user_status': user_status
            })
        
        if week_start_date is None:
            week_start_date = get_week_start(week_data['days'][0]['date'])
        
        week_data['week_start'] = week_start_date
        calendar_weeks.append(week_data)
    
    return render_template('calendar_view.html',
                         title=f'{calendar.month_name[month]} {year} Calendar',
                         current_month=first_day,
                         prev_month=prev_month,
                         next_month=next_month,
                         calendar_weeks=calendar_weeks,
                         today=today)

@bp.route('/week/<week_start>')
@login_required
def week_view(week_start):
    """Display a specific week view"""
    try:
        week_start_date = date.fromisoformat(week_start)
    except ValueError:
        flash('Invalid week date.', 'danger')
        return redirect(url_for('main.calendar_view'))
    
    # Redirect to the normal index view but with the specific week
    return redirect(url_for('main.index_week', week_start=week_start))

@bp.route('/week/<week_start>/schedule', methods=['GET', 'POST'])
@login_required
def index_week(week_start):
    """Display the schedule for a specific week"""
    try:
        week_start_date = date.fromisoformat(week_start)
    except ValueError:
        flash('Invalid week date.', 'danger')
        return redirect(url_for('main.index'))
    
    form = AttendanceForm()
    
    # Check if week is unlocked (admins can always access)
    if not current_user.is_admin and not is_week_unlocked(week_start_date):
        flash('The schedule for this week is currently locked. Please wait for admin to unlock it.', 'info')
        return render_template('locked_week.html', title='Schedule Locked', week_start=week_start_date)

    # Consolidated logic to handle all POST requests from the index page
    if request.method == 'POST':
        # Additional check for non-admins during POST
        if not current_user.is_admin and not is_week_unlocked(week_start_date):
            flash('Cannot save changes - this week is locked.', 'danger')
            return redirect(url_for('main.index_week', week_start=week_start))
            
        day_str = request.form.get('day_date')
        new_status = request.form.get('status')

        if not day_str or not new_status:
            flash('Invalid request. Please try again.', 'danger')
            return redirect(url_for('main.index_week', week_start=week_start))
            
        day_date = date.fromisoformat(day_str)
        
        # Prevent changes to past days (except for admins)
        today = date.today()
        if not current_user.is_admin and day_date < today:
            flash('Cannot modify past dates.', 'danger')
            return redirect(url_for('main.index_week', week_start=week_start))
        
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
                return redirect(url_for('main.index_week', week_start=week_start))
            
            # Check for office capacity before confirming
            attendees_count = db.session.scalar(
                sa.select(sa.func.count(Schedule.id)).where(
                    Schedule.date == day_date, Schedule.status == 'Yes'
                )
            )
            is_newly_attending = not schedule_entry.id or schedule_entry.status != 'Yes'
            if attendees_count >= OFFICE_CAPACITY and is_newly_attending:
                flash(f'Sorry, the office is already full for {day_date.strftime("%A, %b %d")}.', 'warning')
                return redirect(url_for('main.index_week', week_start=week_start))
            
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
        return redirect(url_for('main.index_week', week_start=week_start))

    # --- GET request logic for displaying the schedule ---
    today = date.today()
    
    # Get the office days for the specified week
    week_dates = [week_start_date + timedelta(days=i) for i in OFFICE_DAYS]
    
    # Filter out past dates (except for admins who can see all)
    if not current_user.is_admin:
        week_dates = [d for d in week_dates if d >= today]
    
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
    for i, office_day in enumerate(OFFICE_DAYS):
        day_date = week_start_date + timedelta(days=office_day)
        
        # Skip past days for non-admins
        if not current_user.is_admin and day_date < today:
            continue
            
        day_name = OFFICE_DAY_NAMES[i]
        
        attendees = [e.user.username for e in all_schedule_entries if e.date == day_date and e.status == 'Yes']
        
        schedule_data[day_name] = {
            'date': day_date,
            'attendees': sorted(attendees),
            'slots_filled': len(attendees),
            'slots_available': OFFICE_CAPACITY - len(attendees),
            'user_choice': user_choices.get(day_date.isoformat()),
            'is_past': day_date < today
        }

    return render_template('index.html', 
                         title='Home', 
                         schedule_data=schedule_data, 
                         form=form, 
                         OFFICE_CAPACITY=OFFICE_CAPACITY,
                         week_start=week_start_date,
                         is_week_unlocked=is_week_unlocked(week_start_date),
                         show_calendar_link=True) 