import requests
from flask import current_app, render_template
from app.email import send_email

def send_daily_schedule_email(users, schedule_data):
    """
    Sends an email to all users with the daily schedule.
    """
    if not users:
        return
        
    recipients = [user.email for user in users]
    
    # Flatten the schedule for easier rendering
    flat_schedule = []
    for day_name, details in schedule_data.items():
        if details['attendees']:
            flat_schedule.append({
                'day': f"{day_name}, {details['date'].strftime('%d-%b-%Y')}",
                'attendees': [entry.user.username for entry in details['attendees']],
                'meals': f"Veg: {details['veg_count']}, Non-Veg: {details['non_veg_count']}"
            })

    send_email('[Office Planner] Daily Schedule Update',
               sender=current_app.config['ADMINS'][0],
               recipients=recipients,
               text_body=render_template('email/daily_update.txt', schedule=flat_schedule),
               html_body=render_template('email/daily_update.html', schedule=flat_schedule))
    current_app.logger.info("Daily schedule email sent.")


def send_teams_notification(schedule_data):
    """
    Sends a notification to a Microsoft Teams channel with the daily schedule.
    """
    webhook_url = current_app.config.get('MSTEAMS_WEBHOOK')
    if not webhook_url:
        current_app.logger.warning("MSTEAMS_WEBHOOK URL is not set. Skipping notification.")
        return

    # Create a Teams Adaptive Card
    card = {
        "type": "message",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": {
                    "type": "AdaptiveCard",
                    "version": "1.4",
                    "body": [
                        {
                            "type": "TextBlock",
                            "text": "Office Schedule Update",
                            "size": "large",
                            "weight": "bolder"
                        },
                        {
                            "type": "TextBlock",
                            "text": "Here is the final list for the coming days.",
                            "wrap": True
                        }
                    ],
                    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json"
                }
            }
        ]
    }

    # Add a section for each day with attendees
    for day_name, details in schedule_data.items():
        if details['attendees']:
            attendee_list = "\n".join([f"- {entry.user.username}" for entry in details['attendees']])
            card['attachments'][0]['content']['body'].append({
                "type": "Container",
                "style": "emphasis",
                "items": [
                    {
                        "type": "TextBlock",
                        "text": f"**{day_name}, {details['date'].strftime('%d-%b-%Y')}**",
                        "weight": "bolder",
                        "wrap": True
                    },
                    {
                        "type": "TextBlock",
                        "text": attendee_list,
                        "wrap": True,
                        "spacing": "small"
                    },
                    {
                        "type": "TextBlock",
                        "text": f"**Total:** {details['total_attendees']}\n**Meals:** Veg - {details['veg_count']}, Non-Veg - {details['non_veg_count']}",
                        "wrap": True,
                        "spacing": "small"
                    }
                ],
                "spacing": "medium"
            })
    
    try:
        response = requests.post(webhook_url, json=card, timeout=10)
        response.raise_for_status() # Raise an exception for bad status codes
        current_app.logger.info("Microsoft Teams notification sent successfully.")
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Failed to send Microsoft Teams notification: {e}")

 