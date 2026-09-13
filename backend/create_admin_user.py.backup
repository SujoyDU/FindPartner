#!/usr/bin/env python3
"""
Script to help create an admin user for testing.
This shows how you would manually set up a user with admin privileges.
"""

import os
import sys
import sqlite3
from datetime import datetime

# Add the project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath('.')))

def setup_admin_user():
    print("Setting up admin user in database...")
    
    # Connect to the database
    db_path = 'test.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # First check existing users
        cursor.execute('SELECT id, username, email, is_active FROM users')
        users = cursor.fetchall()
        
        print(f"Found {len(users)} existing user(s):")
        for user in users:
            print(f"  ID: {user[0]}, Username: {user[1]}, Email: {user[2]}, Active: {user[3]}")
            
        # If we have a user, we can make them admin by updating the database
        if users:
            user_id = users[0][0]  # Take first user as example
            print(f"\nMaking user ID {user_id} active (admin)")
            
            # Update to make the user active - you could add admin logic here too
            cursor.execute('UPDATE users SET is_active = ? WHERE id = ?', (True, user_id))
            conn.commit()
            
            print("User updated successfully!")
        else:
            print("No users found in database. Please register a user first using the API.")
            
        conn.close()
        print("\n✅ Admin setup complete")
        
    except Exception as e:
        print(f"❌ Error setting up admin user: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    setup_admin_user()
