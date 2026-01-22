import json
from database import create_user

# Load existing users from JSON
with open('users_data.json', 'r') as f:
    users = json.load(f)

# Migrate each user
for username, user_info in users.items():
    passcode = user_info['passcode']
    data = user_info['data']
    
    success = create_user(username, passcode, data)
    
    if success:
        print(f"✅ Migrated: {username}")
    else:
        print(f"❌ Failed: {username}")

print("\nMigration complete!")