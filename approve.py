from app import app, db, User

with app.app_context():
    # List all unapproved users
    unapproved_users = User.query.filter_by(approved=False).all()
    for user in unapproved_users:
        print(f"User ID: {user.id}, Username: {user.username}, Email: {user.email}")

    # get user ID from input
    id = int(input('Enter ID to approve or delete: '))

    # Find the user by ID
    user = User.query.get(id)
    if user:
        action = input(f"Do you want to approve (a) or delete (d) user {user.username}? (a/d): ").strip().lower()
        
        if action == 'a':
            user.approved = True
            db.session.commit()
            print(f"User {user.username} has been approved.")
        elif action == 'd':
            db.session.delete(user)
            db.session.commit()
            print(f"User {user.username} has been deleted.")
        else:
            print("Invalid action. Please enter 'a' to approve or 'd' to delete.")
    else:
        print("User not found.")
