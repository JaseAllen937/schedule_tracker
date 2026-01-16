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
    """Create new user"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute(
            'INSERT INTO users (username, passcode, created, data) VALUES (%s, %s, %s, %s)',
            (username, passcode, datetime.now(), json.dumps(data))
        )
        conn.commit()
        cur.close()
        conn.close()
        return True
    except psycopg2.IntegrityError:
        conn.rollback()
        cur.close()
        conn.close()
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