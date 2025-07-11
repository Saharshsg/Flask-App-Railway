from flask import render_template, flash, redirect, url_for, request, abort, current_app
from app import db
from app.admin import bp
from app.admin.forms import SwapForm, EditUserForm
from flask_login import current_user, login_required
from app.models import User, Schedule, WeekConfig
from datetime import date, timedelta
import sqlalchemy as sa
from functools import wraps
import random
from app.admin.utils import run_auto_assignment_for_date
from app.email import send_swap_confirmation_email

# Constants
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

def admin_required(fn):
    @wraps(fn)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return fn(*args, **kwargs)
    return decorated_view

@bp.route('/')
@login_required
@admin_required
def admin_dashboard():
    week_start = get_current_week_dates()
    week_dates = [week_start + timedelta(days=i) for i in OFFICE_DAYS]

    # Get week config
    week_config = db.session.scalar(
        sa.select(WeekConfig).where(WeekConfig.week_start_date == week_start)
    )

    all_schedule_entries = db.session.scalars(
        sa.select(Schedule).where(
            Schedule.date.in_(week_dates)
        ).options(sa.orm.joinedload(Schedule.user)).order_by(Schedule.date)
    ).all()

    admin_schedule_data = {}
    whatsapp_messages = {}

    for i, office_day in enumerate(OFFICE_DAYS):
        day_date = week_start + timedelta(days=office_day)
        day_name = OFFICE_DAY_NAMES[i]
        entries_for_day = [e for e in all_schedule_entries if e.date == day_date]
        
        attendees = [e for e in entries_for_day if e.status == 'Yes']
        absentees = [e for e in entries_for_day if e.status == 'No']
        available_for_swap = [e for e in absentees if e.is_available]
        
        veg_count = sum(1 for e in attendees if e.meal_preference == 'Veg')
        non_veg_count = sum(1 for e in attendees if e.meal_preference == 'Non-Veg')
        no_meal_count = sum(1 for e in attendees if e.meal_preference == 'No Meal')
        
        admin_schedule_data[day_name] = {
            'date': day_date,
            'attendees': sorted(attendees, key=lambda x: x.user.username),
            'absentees': sorted(absentees, key=lambda x: x.user.username),
            'available_for_swap': sorted(available_for_swap, key=lambda x: x.user.username),
            'veg_count': veg_count,
            'non_veg_count': non_veg_count,
            'no_meal_count': no_meal_count,
            'total_attendees': len(attendees)
        }

        if attendees:
            message = f"Office List for *{day_name}, {day_date.strftime('%d-%b-%Y')}*:\n\n"
            for i, entry in enumerate(admin_schedule_data[day_name]['attendees'], 1):
                message += f"{i}. {entry.user.username}\n"
            
            message += f"\nTotal: *{len(attendees)}*\n"
            if veg_count > 0 or non_veg_count > 0:
                message += f"Meals: Veg - *{veg_count}*, Non-Veg - *{non_veg_count}*"
                if no_meal_count > 0:
                    message += f", No Meal - *{no_meal_count}*"
            else:
                message += f"No Meal - *{no_meal_count}*"
            whatsapp_messages[day_name] = message

    return render_template('admin/dashboard.html', 
                           title='Admin Dashboard', 
                           schedule_data=admin_schedule_data,
                           whatsapp_messages=whatsapp_messages,
                           OFFICE_CAPACITY=OFFICE_CAPACITY,
                           week_start=week_start,
                           week_config=week_config,
                           is_week_locked=week_config.is_locked if week_config else True)

@bp.route('/toggle_week_lock', methods=['POST'])
@login_required
@admin_required
def toggle_week_lock():
    week_start_str = request.form.get('week_start')
    if not week_start_str:
        flash('Invalid week start date.', 'danger')
        return redirect(url_for('admin.admin_dashboard'))
    
    week_start = date.fromisoformat(week_start_str)
    
    week_config = db.session.scalar(
        sa.select(WeekConfig).where(WeekConfig.week_start_date == week_start)
    )
    
    if not week_config:
        # Create new week config
        week_config = WeekConfig(
            week_start_date=week_start,
            is_locked=False,  # Unlock it
            created_by=current_user.id
        )
        db.session.add(week_config)
        action = "unlocked"
    else:
        # Toggle existing config
        week_config.is_locked = not week_config.is_locked
        action = "locked" if week_config.is_locked else "unlocked"
    
    db.session.commit()
    
    flash(f'Week of {week_start.strftime("%B %d, %Y")} has been {action} for employee access.', 'success')
    return redirect(url_for('admin.manage_weeks'))

@bp.route('/test_weeks')
@login_required
@admin_required
def test_weeks():
    """Test route to debug template issues"""
    return "<h1>Test route working!</h1><p>If you see this, routing is working. The issue is in template rendering.</p>"

@bp.route('/manage_weeks')
@login_required
@admin_required
def manage_weeks():
    """View and manage multiple weeks"""
    try:
        today = date.today()
        
        # Simplified version with minimal data
        weeks = [{
            'week_start': today,
            'week_end': today + timedelta(days=4),
            'office_dates': [(today, 'Today')],
            'is_locked': False,
            'config_exists': True
        }]
        
        return render_template('admin/manage_weeks.html', 
                             title='Manage Weeks', 
                             weeks=weeks,
                             today=today)
    except Exception as e:
        current_app.logger.error(f"Error in manage_weeks: {str(e)}")
        return f"<h1>Error in manage_weeks:</h1><p>{str(e)}</p><a href='/admin'>Back to Admin</a>"

@bp.route('/swap/<int:schedule_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def swap_user(schedule_id):
    entry_to_swap = db.get_or_404(Schedule, schedule_id, description='Schedule entry not found.')
    if entry_to_swap.status != 'Yes':
        flash('Can only swap users who are attending.', 'warning')
        return redirect(url_for('admin.admin_dashboard'))

    form = SwapForm()

    # --- Logic to get available and other users ---
    swap_date = entry_to_swap.date
    
    attending_user_ids = db.session.scalars(
        sa.select(Schedule.user_id).where(
            Schedule.date == swap_date,
            Schedule.status == 'Yes'
        )
    ).all()

    available_schedules = db.session.scalars(
        sa.select(Schedule).where(
            Schedule.date == swap_date,
            Schedule.is_available == True,
            Schedule.user_id.notin_(attending_user_ids)
        ).options(sa.orm.joinedload(Schedule.user))
    ).all()
    available_users = sorted([s.user for s in available_schedules], key=lambda u: u.username)
    
    all_user_ids = db.session.scalars(sa.select(User.id)).all()
    non_attending_user_ids = [uid for uid in all_user_ids if uid not in attending_user_ids]
    
    available_user_ids = {u.id for u in available_users}
    other_user_ids = [uid for uid in non_attending_user_ids if uid not in available_user_ids]
    other_users = db.session.scalars(sa.select(User).where(User.id.in_(other_user_ids)).order_by(User.username)).all()

    # --- Set choices on the form ---
    all_possible_users = sorted(available_users + other_users, key=lambda u: u.username)
    form.replacement_user.choices = [(str(u.id), u.username) for u in all_possible_users]
    # Add a placeholder
    form.replacement_user.choices.insert(0, ('', 'Select a replacement...'))

    if form.validate_on_submit():
        replacement_user_id_str = form.replacement_user.data
        if not replacement_user_id_str:
            flash('You must select a replacement user.', 'danger')
            return render_template('admin/swap_user.html', 
                                   title='Swap User', 
                                   form=form, 
                                   user_to_swap=entry_to_swap.user, 
                                   date=entry_to_swap.date)

        replacement_user_id = int(replacement_user_id_str)
        
        # The user being swapped out
        entry_to_swap.status = 'No'
        entry_to_swap.meal_preference = None
        entry_to_swap.reassignment_request = False
        entry_to_swap.reassignment_reason = None
        
        # The user being swapped in
        replacement_entry = db.session.scalar(
            sa.select(Schedule).where(
                Schedule.user_id == replacement_user_id,
                Schedule.date == swap_date
            )
        )
        
        if replacement_entry:
            replacement_entry.status = 'Yes'
            replacement_entry.meal_preference = 'Veg' 
            replacement_entry.is_available = False
        else:
            new_entry = Schedule(user_id=replacement_user_id,
                                 date=swap_date,
                                 status='Yes',
                                 meal_preference='Veg')
            db.session.add(new_entry)
            
        db.session.commit()
        
        original_user = entry_to_swap.user
        replacement_user = db.session.get(User, replacement_user_id)
        
        # Send confirmation email
        send_swap_confirmation_email(original_user, replacement_user, swap_date)

        flash(f'{original_user.username} has been successfully swapped with {replacement_user.username}.', 'success')
        return redirect(url_for('admin.admin_dashboard'))

    return render_template('admin/swap_user.html', 
                           title='Swap User', 
                           form=form, 
                           user_to_swap=entry_to_swap.user, 
                           date=entry_to_swap.date)

@bp.route('/auto_assign/<date_iso>', methods=['POST'])
@login_required
@admin_required
def auto_assign(date_iso):
    try:
        assign_date = date.fromisoformat(date_iso)
    except (ValueError, TypeError):
        flash('Invalid date format.', 'danger')
        return redirect(url_for('admin.admin_dashboard'))

    run_auto_assignment_for_date(assign_date)
    
    flash(f'Auto-assignment for {assign_date.strftime("%A, %b %d")} has been run.', 'success')
    return redirect(url_for('admin.admin_dashboard'))

@bp.route('/clear_schedule', methods=['POST'])
@login_required
@admin_required
def clear_schedule():
    try:
        num_rows_deleted = db.session.query(Schedule).delete()
        db.session.commit()
        flash(f'Successfully cleared {num_rows_deleted} schedule entries.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error clearing schedule: {e}', 'danger')
    return redirect(url_for('admin.admin_dashboard'))

@bp.route('/users')
@login_required
@admin_required
def manage_users():
    users = db.session.scalars(sa.select(User).order_by(User.username)).all()
    return render_template('admin/manage_users.html', users=users, title="Manage Users")

@bp.route('/user/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = db.get_or_404(User, user_id)
    form = EditUserForm(obj=user)
    if form.validate_on_submit():
        user.is_admin = form.is_admin.data
        user.is_intern = form.is_intern.data
        db.session.commit()
        flash(f'{user.username}\'s roles have been updated.', 'success')
        return redirect(url_for('admin.manage_users'))
    return render_template('admin/edit_user.html', form=form, user=user, title="Edit User") 