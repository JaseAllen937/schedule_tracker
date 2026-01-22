#!/usr/bin/env python3
"""
Database Diagnostic Script
Run this on Render to test PostgreSQL connection and operations
"""
import os
import sys

print("=" * 60)
print("🔍 DATABASE DIAGNOSTIC SCRIPT")
print("=" * 60)

# Step 1: Check environment variables
print("\n1️⃣ Checking Environment Variables...")
DATABASE_URL = os.environ.get('DATABASE_URL', '')
if DATABASE_URL:
    print(f"✅ DATABASE_URL found: {DATABASE_URL[:60]}...")
else:
    print("❌ DATABASE_URL not found!")
    sys.exit(1)

# Step 2: Try importing psycopg2
print("\n2️⃣ Testing psycopg2 import...")
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    print("✅ psycopg2 imported successfully")
except ImportError as e:
    print(f"❌ Failed to import psycopg2: {e}")
    sys.exit(1)

# Step 3: Test database connection
print("\n3️⃣ Testing database connection...")
try:
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    print("✅ Database connection successful")
    conn.close()
except Exception as e:
    print(f"❌ Database connection failed: {type(e).__name__}: {str(e)}")
    sys.exit(1)

# Step 4: Test table creation
print("\n4️⃣ Testing table initialization...")
try:
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    cur = conn.cursor()
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username VARCHAR(255) PRIMARY KEY,
            passcode VARCHAR(4) NOT NULL,
            created TIMESTAMP NOT NULL,
            data JSONB NOT NULL
        )
    ''')
    
    conn.commit()
    print("✅ Users table created/verified")
    
    # Check if table exists
    cur.execute("SELECT COUNT(*) FROM users")
    count = cur.fetchone()['count']
    print(f"✅ Users table currently has {count} records")
    
    cur.close()
    conn.close()
except Exception as e:
    print(f"❌ Table initialization failed: {type(e).__name__}: {str(e)}")
    sys.exit(1)

# Step 5: Test user creation
print("\n5️⃣ Testing user creation...")
try:
    import json
    from datetime import datetime
    
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    cur = conn.cursor()
    
    test_username = f"test_user_{datetime.now().timestamp()}"
    test_passcode = "1234"
    test_data = {"test": True, "timestamp": datetime.now().isoformat()}
    
    cur.execute(
        'INSERT INTO users (username, passcode, created, data) VALUES (%s, %s, %s, %s)',
        (test_username, test_passcode, datetime.now(), json.dumps(test_data))
    )
    conn.commit()
    print(f"✅ Test user created: {test_username}")
    
    # Verify user exists
    cur.execute('SELECT * FROM users WHERE username = %s', (test_username,))
    user = cur.fetchone()
    if user:
        print(f"✅ Test user verified in database: {dict(user)}")
    else:
        print(f"❌ Test user NOT found after creation!")
    
    # Clean up
    cur.execute('DELETE FROM users WHERE username = %s', (test_username,))
    conn.commit()
    print(f"✅ Test user cleaned up")
    
    cur.close()
    conn.close()
except Exception as e:
    print(f"❌ User creation test failed: {type(e).__name__}: {str(e)}")
    import traceback
    print(f"❌ Traceback: {traceback.format_exc()}")
    sys.exit(1)

# Success!
print("\n" + "=" * 60)
print("🎉 ALL DIAGNOSTIC TESTS PASSED!")
print("=" * 60)
print("\n✅ Database is working correctly")
print("✅ Ready for production use")
print("\nIf users still aren't persisting, check:")
print("  1. Render logs during actual user registration")
print("  2. Verify app.py is using DATABASE_URL correctly")
print("  3. Check for any middleware/proxy issues")