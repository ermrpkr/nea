#!/usr/bin/env python
import os
import sys
import django

# Add the project path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nea_project.settings')
django.setup()

from nea_loss.models import NEAUser

def test_user_edit_issue():
    print("=== TESTING USER EDIT ISSUE ===")
    
    # Check existing users
    users = NEAUser.objects.all()
    print(f"Total users in database: {users.count()}")
    
    for user in users:
        print(f"User: {user.username} - Email: {user.email} - ID: {user.id}")
    
    # Look for potential duplicates
    print("\n=== CHECKING FOR DUPLICATES ===")
    email_groups = {}
    for user in users:
        if user.email not in email_groups:
            email_groups[user.email] = []
        email_groups[user.email].append(user)
    
    for email, user_list in email_groups.items():
        if len(user_list) > 1:
            print(f"DUPLICATE EMAIL FOUND: {email}")
            for user in user_list:
                print(f"  - Username: {user.username} (ID: {user.id})")
    
    username_groups = {}
    for user in users:
        if user.username not in username_groups:
            username_groups[user.username] = []
        username_groups[user.username].append(user)
    
    for username, user_list in username_groups.items():
        if len(user_list) > 1:
            print(f"DUPLICATE USERNAME FOUND: {username}")
            for user in user_list:
                print(f"  - Email: {user.email} (ID: {user.id})")

if __name__ == '__main__':
    test_user_edit_issue()
