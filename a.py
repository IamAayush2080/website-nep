from app import app, db, User, hash_password  # Import app, db, and User

# Create the admin user
with app.app_context():
    admin_user = User(
        name="Admin",
        email="ak2183874@gmail.com",  # Admin's email
        phone="1234567890",         # Admin's phone
        password=hash_password("1234567890ASDFGHJKL"),  # Admin's password
        is_admin=True               # Mark as admin
    )
    
    db.session.add(admin_user)  # Add the user to the database
    db.session.commit()         # Save the changes
    
    print("Admin user created successfully!")


# # from app import app, db, User
# # from werkzeug.security import generate_password_hash

# # with app.app_context():
# #     admin_user = User.query.filter_by(email="admin@example.com").first()
# #     if admin_user:
# #         admin_user.password = generate_password_hash("Avengers123@@")
# #         db.session.commit()
# #         print("Admin password reset.")

# from werkzeug.security import generate_password_hash
# from app import db, User
# from app import app

# with app.app_context():
#     admin_user = User.query.filter_by(email="ak2183874@gmail.com").first()
#     if admin_user:
#         admin_user.password = generate_password_hash("Avengers12345@@##")
#         db.session.commit()
#         print("Password reset successfully!")
#     else:
#         print("Admin user not found!")
# from app import db, User,app

# with app.app_context():
#     admin_user = User.query.filter_by(email="admin@example.com").first()
#     if admin_user:
#         print("Admin user found:", admin_user)
#     else:
#         print("Admin user not found.")
# for user in admin_user[1:]:  # Keep only the first one
#     db.session.delete(user)
# db.session.commit()
# print("Duplicate admin accounts removed!")
