import os
import psycopg2
from psycopg2.extras import RealDictCursor
import json
from datetime import datetime

DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    """Get database connection"""
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn

def init_db():
    """Initialize database tables"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Create users table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username VARCHAR(255) PRIMARY KEY,
            passcode VARCHAR(4) NOT NULL,
            created TIMESTAMP NOT NULL,
            data JSONB NOT NULL
        )
    ''')
    
    conn.commit()
    cur.close()
    conn.close()
    print("Database initialized successfully")

def get_user(username):
    """Get user by username"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('SELECT * FROM users WHERE username = %s', (username,))
    user = cur.fetchone()
    
    cur.close()
    conn.close()
    
    return dict(user) if user else None

def create_user(username, passcode, data):
    """Create new user with comprehensive error handling"""
    try:
        print(f"📊 DATABASE: Opening connection for user creation: {username}")
        conn = get_db_connection()
        print(f"📊 DATABASE: Connection opened successfully")
        cur = conn.cursor()
        
        try:
            print(f"📊 DATABASE: Executing INSERT for user: {username}")
            cur.execute(
                'INSERT INTO users (username, passcode, created, data) VALUES (%s, %s, %s, %s)',
                (username, passcode, datetime.now(), json.dumps(data))
            )
            print(f"📊 DATABASE: INSERT executed, committing...")
            conn.commit()
            print(f"📊 DATABASE: Commit successful for user: {username}")
            cur.close()
            conn.close()
            print(f"📊 DATABASE: Connection closed")
            return True
        except psycopg2.IntegrityError as ie:
            print(f"❌ DATABASE: IntegrityError (user already exists): {str(ie)}")
            conn.rollback()
            cur.close()
            conn.close()
            return False
    except psycopg2.OperationalError as oe:
        print(f"❌ DATABASE: OperationalError (connection/database issue): {str(oe)}")
        return False
    except Exception as e:
        print(f"❌ DATABASE: Unexpected exception in create_user: {type(e).__name__}: {str(e)}")
        import traceback
        print(f"❌ DATABASE: Full traceback: {traceback.format_exc()}")
        try:
            conn.rollback()
            cur.close()
            conn.close()
        except:
            pass
        return False

def update_user_data(username, data):
    """Update user data"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(
        'UPDATE users SET data = %s WHERE username = %s',
        (json.dumps(data), username)
    )
    
    conn.commit()
    cur.close()
    conn.close()

def get_all_users():
    """Get all users (for migration)"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('SELECT * FROM users')
    users = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return [dict(user) for user in users]