from app import create_app, db
from app.models import User

# --- Configuration ---
# Define your list of employees here.
# The first user in this list will be made an admin.
EMPLOYEES = [
    {'username': 'saharsh', 'email': 'saharsh@arcwide.com', 'is_intern': False, 'is_admin': True},
    {'username': 'ritesh', 'email': 'ritesh@arcwide.com', 'is_intern': False, 'is_admin': False},
    {'username': 'Jospeh', 'email': 'emp3@arcwide.com', 'is_intern': False, 'is_admin': False},
    {'username': 'intern1', 'email': 'intern1@arcwide.com', 'is_intern': True, 'is_admin': False},
    {'username': 'intern2', 'email': 'intern2@arcwide.com', 'is_intern': True, 'is_admin': False},
    {'username': 'intern3', 'email': 'intern3@arcwide.com', 'is_intern': True, 'is_admin': False},
    {'username': 'Manoj', 'email': 'Manoj@arcwide.com', 'is_intern': False, 'is_admin': False},
    {'username': 'Philip', 'email': 'Philip@arcwide.com', 'is_intern': False, 'is_admin': False},
    {'username': 'Lance', 'email': 'Lance@arcwide.com', 'is_intern': False, 'is_admin': False},
    {'username': 'Sakshi', 'email': 'Sakshi@arcwide.com', 'is_intern': False, 'is_admin': False},
    {'username': 'Shiva', 'email': 'Shiva@arcwide.com', 'is_intern': False, 'is_admin': False},
    # Add all 11-12 members here
]
DEFAULT_PASSWORD = "password123" # Users should change this after first login


def create_users():
    """
    Creates user accounts based on the EMPLOYEES list.
    """
    app = create_app()
    with app.app_context():
        print("Creating user accounts...")
        for emp_data in EMPLOYEES:
            # Check if user already exists
            user = db.session.scalar(db.select(User).where(User.username == emp_data['username']))
            if user:
                print(f"User '{emp_data['username']}' already exists. Skipping.")
                continue

            # Create new user
            new_user = User(
                username=emp_data['username'],
                email=emp_data['email'],
                is_admin=emp_data.get('is_admin', False),
                is_intern=emp_data.get('is_intern', False)
            )
            new_user.set_password(DEFAULT_PASSWORD)
            db.session.add(new_user)
            print(f"Created user: {new_user.username}")

        db.session.commit()
        print("User creation process finished.")

if __name__ == '__main__':
    create_users() 