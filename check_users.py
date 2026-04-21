import sqlite3
import os

def check_users_sqlite():
    print("=== CHECKING USERS IN DATABASE ===")
    
    db_path = os.path.join(os.path.dirname(__file__), 'db.sqlite3')
    
    if not os.path.exists(db_path):
        print("Database file not found")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Get all users
        cursor.execute("SELECT id, username, email, full_name FROM nea_loss_neauser ORDER BY username")
        users = cursor.fetchall()
        
        print(f"Total users: {len(users)}")
        print("\nAll users:")
        for user in users:
            print(f"  ID: {user[0]}, Username: {user[1]}, Email: {user[2]}, Name: {user[3]}")
        
        # Check for duplicate emails
        cursor.execute("SELECT email, COUNT(*) FROM nea_loss_neauser GROUP BY email HAVING COUNT(*) > 1")
        duplicate_emails = cursor.fetchall()
        
        if duplicate_emails:
            print("\n=== DUPLICATE EMAILS FOUND ===")
            for email, count in duplicate_emails:
                print(f"Email: {email} appears {count} times")
                cursor.execute("SELECT id, username, full_name FROM nea_loss_neauser WHERE email = ?", (email,))
                for user in cursor.fetchall():
                    print(f"  - ID: {user[0]}, Username: {user[1]}, Name: {user[2]}")
        
        # Check for duplicate usernames
        cursor.execute("SELECT username, COUNT(*) FROM nea_loss_neauser GROUP BY username HAVING COUNT(*) > 1")
        duplicate_usernames = cursor.fetchall()
        
        if duplicate_usernames:
            print("\n=== DUPLICATE USERNAMES FOUND ===")
            for username, count in duplicate_usernames:
                print(f"Username: {username} appears {count} times")
                cursor.execute("SELECT id, email, full_name FROM nea_loss_neauser WHERE username = ?", (username,))
                for user in cursor.fetchall():
                    print(f"  - ID: {user[0]}, Email: {user[1]}, Name: {user[2]}")
        
        if not duplicate_emails and not duplicate_usernames:
            print("\n=== NO DUPLICATES FOUND ===")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    check_users_sqlite()
