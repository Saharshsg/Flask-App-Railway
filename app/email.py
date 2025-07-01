from threading import Thread
from flask import current_app, render_template
from flask_mail import Message
from app import mail, db
from app.models import User
import sqlalchemy as sa

def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    Thread(target=send_async_email, args=(current_app._get_current_object(), msg)).start()

def send_password_reset_email(user):
    token = user.get_reset_password_token()
    send_email('[Office Planner] Reset Your Password',
               sender=current_app.config['ADMINS'][0],
               recipients=[user.email],
               text_body=render_template('email/reset_password.txt',
                                         user=user, token=token),
               html_body=render_template('email/reset_password.html',
                                         user=user, token=token))

def send_swap_request_email(user, schedule):
    admin_email = current_app.config['ADMINS'][0]
    send_email('[Office Planner] Reassignment Request',
               sender=current_app.config['ADMINS'][0],
               recipients=[admin_email],
               text_body=render_template('email/swap_request_admin.txt',
                                         user=user, 
                                         schedule_date=schedule.date,
                                         reason=schedule.reassignment_reason),
               html_body=render_template('email/swap_request_admin.html',
                                         user=user, 
                                         schedule_date=schedule.date,
                                         reason=schedule.reassignment_reason))

def send_swap_confirmation_email(original_user, replacement_user, schedule_date):
    recipients = [original_user.email, replacement_user.email]
    send_email('[Office Planner] Swap Confirmation',
               sender=current_app.config['ADMINS'][0],
               recipients=recipients,
               text_body=render_template('email/swap_confirmation.txt',
                                         original_user=original_user,
                                         replacement_user=replacement_user,
                                         schedule_date=schedule_date),
               html_body=render_template('email/swap_confirmation.html',
                                         original_user=original_user,
                                         replacement_user=replacement_user,
                                         schedule_date=schedule_date))

def send_daily_roster_email(attendees, schedule_date):
    all_users = db.session.scalars(sa.select(User)).all()
    recipients = [user.email for user in all_users if user.email]
    if not recipients:
        return
        
    send_email(f'[Office Planner] Office Roster for {schedule_date.strftime("%b %d")}',
               sender=current_app.config['ADMINS'][0],
               recipients=recipients,
               text_body=render_template('email/daily_update.txt',
                                         attendees=attendees,
                                         schedule_date=schedule_date),
               html_body=render_template('email/daily_update.html',
                                         attendees=attendees,
                                         schedule_date=schedule_date)) 