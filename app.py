from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from datetime import datetime, timedelta
from functools import wraps
import json
import os
import random
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Try to import database functions, fall back to JSON if no DATABASE_URL
USE_DATABASE = bool(os.environ.get('DATABASE_URL', '').strip())

if USE_DATABASE:
    try:
        from database import init_db, get_user, create_user, update_user_data, get_all_users
        print("✅ Using PostgreSQL database")
    except ImportError as e:
        USE_DATABASE = False
        print(f"⚠️ Database module not found, using JSON file")
        print(f"❌ Import error details: {type(e).__name__}: {str(e)}")
        import traceback
        print(f"❌ Full traceback:\n{traceback.format_exc()}")
else:
    print("⚠️ No DATABASE_URL found, using JSON file for local development")

app = Flask(__name__, static_folder='static', static_url_path='/static')

# Configure Gemini API
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '').strip()
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-2.5-flash')
    print("✅ Gemini API configured")
else:
    gemini_model = None
    print("⚠️ No GEMINI_API_KEY found, using static quotes")
app.secret_key = os.environ.get('SECRET_KEY', '').strip() or 'dev-key-change-in-production'
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False  # Set True only for HTTPS
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

DATA_FILE = 'users_data.json'

# Initialize database if using it
if USE_DATABASE:
    try:
        print(f"📊 DATABASE_URL detected: {os.environ.get('DATABASE_URL', '')[:60]}...")
        init_db()
        print("✅ Database connected and initialized")
        # Test database connectivity
        try:
            all_users = get_all_users()
            print(f"📊 Database currently has {len(all_users)} users")
        except Exception as test_error:
            print(f"⚠️ Database query test failed: {str(test_error)}")
    except Exception as e:
        print(f"❌ Database initialization error: {type(e).__name__}: {str(e)}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        USE_DATABASE = False
        print("⚠️ Falling back to JSON file")

# Bible verses for daily motivation
BIBLE_VERSES = [
    {"text": "I can do all things through Christ who strengthens me.", "reference": "Philippians 4:13"},
    {"text": "For God has not given us a spirit of fear, but of power and of love and of a sound mind.", "reference": "2 Timothy 1:7"},
    {"text": "Trust in the Lord with all your heart and lean not on your own understanding.", "reference": "Proverbs 3:5"},
    {"text": "Be strong and courageous. Do not be afraid; do not be discouraged, for the Lord your God will be with you wherever you go.", "reference": "Joshua 1:9"},
    {"text": "The Lord is my strength and my shield; my heart trusts in him, and he helps me.", "reference": "Psalm 28:7"},
    {"text": "But those who hope in the Lord will renew their strength. They will soar on wings like eagles.", "reference": "Isaiah 40:31"},
    {"text": "Cast all your anxiety on him because he cares for you.", "reference": "1 Peter 5:7"},
    {"text": "And we know that in all things God works for the good of those who love him.", "reference": "Romans 8:28"},
    {"text": "The Lord is close to the brokenhearted and saves those who are crushed in spirit.", "reference": "Psalm 34:18"},
    {"text": "Do not be anxious about anything, but in every situation, by prayer and petition, present your requests to God.", "reference": "Philippians 4:6"},
    {"text": "The joy of the Lord is your strength.", "reference": "Nehemiah 8:10"},
    {"text": "Commit to the Lord whatever you do, and he will establish your plans.", "reference": "Proverbs 16:3"},
    {"text": "He gives strength to the weary and increases the power of the weak.", "reference": "Isaiah 40:29"},
    {"text": "This is the day the Lord has made; let us rejoice and be glad in it.", "reference": "Psalm 118:24"},
    {"text": "Let us run with perseverance the race marked out for us, fixing our eyes on Jesus.", "reference": "Hebrews 12:1-2"},
    {"text": "The Lord will fight for you; you need only to be still.", "reference": "Exodus 14:14"},
    {"text": "Therefore do not worry about tomorrow, for tomorrow will worry about itself.", "reference": "Matthew 6:34"},
    {"text": "For I know the plans I have for you, declares the Lord, plans to prosper you and not to harm you.", "reference": "Jeremiah 29:11"},
    {"text": "The Lord is my shepherd, I lack nothing.", "reference": "Psalm 23:1"},
    {"text": "In their hearts humans plan their course, but the Lord establishes their steps.", "reference": "Proverbs 16:9"}
]

# Motivational quotes
MOTIVATION_QUOTES = [
    {"text": "Discipline is the bridge between goals and accomplishment.", "author": "Jim Rohn"},
    {"text": "The secret of getting ahead is getting started.", "author": "Mark Twain"},
    {"text": "Success is the sum of small efforts repeated day in and day out.", "author": "Robert Collier"},
    {"text": "You don't have to be great to start, but you have to start to be great.", "author": "Zig Ziglar"},
    {"text": "The only way to do great work is to love what you do.", "author": "Steve Jobs"},
    {"text": "Believe you can and you're halfway there.", "author": "Theodore Roosevelt"},
    {"text": "Your limitation—it's only your imagination.", "author": "Unknown"},
    {"text": "Push yourself, because no one else is going to do it for you.", "author": "Unknown"},
    {"text": "Great things never come from comfort zones.", "author": "Unknown"},
    {"text": "Dream it. Wish it. Do it.", "author": "Unknown"},
    {"text": "Success doesn't just find you. You have to go out and get it.", "author": "Unknown"},
    {"text": "The harder you work for something, the greater you'll feel when you achieve it.", "author": "Unknown"},
    {"text": "Dream bigger. Do bigger.", "author": "Unknown"},
    {"text": "Don't stop when you're tired. Stop when you're done.", "author": "Unknown"},
    {"text": "Wake up with determination. Go to bed with satisfaction.", "author": "Unknown"},
    {"text": "Do something today that your future self will thank you for.", "author": "Sean Patrick Flanery"},
    {"text": "Little things make big days.", "author": "Unknown"},
    {"text": "It's going to be hard, but hard does not mean impossible.", "author": "Unknown"},
    {"text": "Don't wait for opportunity. Create it.", "author": "Unknown"},
    {"text": "Sometimes we're tested not to show our weaknesses, but to discover our strengths.", "author": "Unknown"}
]

# JSON file functions
def load_users():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_users(users):
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(users, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving users: {str(e)}")
        return False

# Wrapper functions
def get_user_wrapper(username):
    if USE_DATABASE:
        return get_user(username)
    else:
        users = load_users()
        return users.get(username)

def create_user_wrapper(username, passcode, data):
    if USE_DATABASE:
        try:
            print(f"🔍 Attempting to create user '{username}' in PostgreSQL database...")
            result = create_user(username, passcode, data)
            if result:
                print(f"✅ Successfully created user '{username}' in database")
                # Verify the user was actually saved
                try:
                    verify = get_user(username)
                    if verify:
                        print(f"✅ Verified: User '{username}' exists in database")
                    else:
                        print(f"⚠️ WARNING: create_user returned True but user '{username}' NOT found in database!")
                except Exception as verify_error:
                    print(f"⚠️ Could not verify user creation: {str(verify_error)}")
            else:
                print(f"❌ create_user returned False for '{username}' (user may already exist)")
            return result
        except Exception as e:
            import traceback
            print(f"❌ EXCEPTION in create_user_wrapper for '{username}': {type(e).__name__}: {str(e)}")
            print(f"❌ Full traceback: {traceback.format_exc()}")
            return False
    else:
        users = load_users()
        if username in users:
            return False
        users[username] = {
            'passcode': passcode,
            'username': username,
            'created': datetime.now().isoformat(),
            'data': data
        }
        return save_users(users)

def update_user_data_wrapper(username, data):
    """Update user data with proper error handling"""
    try:
        if USE_DATABASE:
            update_user_data(username, data)
            print(f"✅ Database updated for {username}")
            return True
        else:
            users = load_users()
            if username in users:
                users[username]['data'] = data
                success = save_users(users)
                if success:
                    print(f"✅ JSON file updated for {username}")
                else:
                    print(f"❌ JSON file save failed for {username}")
                return success
            else:
                print(f"❌ User {username} not found")
                return False
    except Exception as e:
        print(f"❌ Error updating user data for {username}: {str(e)}")
        return False

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Not logged in'}), 401
        return f(*args, **kwargs)
    return decorated_function

def get_user_data(username):
    user = get_user_wrapper(username)
    if not user:
        return None
    
    user_data = user['data'] if isinstance(user['data'], dict) else json.loads(user['data'])
    
    # Ensure categories exist
    if 'categories' not in user_data:
        old_tasks = user_data.get('dailyTasks', [])
        user_data['categories'] = [
            {
                'name': 'General',
                'icon': '📝',
                'tasks': [
                    {'text': task, 'completed': False, 'recurring': True}
                    for task in old_tasks
                ]
            }
        ]
        if 'dailyTasks' in user_data:
            del user_data['dailyTasks']
        update_user_data_wrapper(username, user_data)
    
    # Ensure milestones array exists
    if 'milestones' not in user_data:
        user_data['milestones'] = []
    
    # Ensure dailyMotivation exists and is current
    if 'dailyMotivation' not in user_data or not is_today(user_data.get('dailyMotivation', {}).get('date')):
        user_data['dailyMotivation'] = get_daily_motivation()
        update_user_data_wrapper(username, user_data)
    
    return user_data

def save_user_data(username, data):
    """Save user data and return success status"""
    return update_user_data_wrapper(username, data)

def check_streak_status(data):
    if not data['lastCompletedDate']:
        return data
    
    last_date = datetime.fromisoformat(data['lastCompletedDate']).date()
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    
    if last_date < yesterday:
        data['currentStreak'] = 0
    
    return data


def generate_10_motivation_batch():
    """Generate 10 unique motivations in one API call"""
    if not gemini_model:
        print("⚠️ No Gemini API, using static quotes")
        return None
    
    try:
        prompt = """Generate 10 motivations for a college student. CRITICAL: EVERY item needs BOTH a Bible verse AND a quote.

TARGET: College freshman, building discipline, fighting procrastination.

CONTENT MIX:
• 40% Discipline quotes (Goggins, Jocko, Jim Rohn)
• 25% Bible verses (Proverbs, Philippians, Joshua, Isaiah)
• 20% Entrepreneurship (Jobs, Dalio, Kobe)
• 15% Resilience & Habits (Aurelius, Clear)

REQUIREMENTS:
- BOTH bibleVerse AND quote in EVERY item
- Vary Bible books (Proverbs, Philippians, Joshua, Isaiah, Romans, Psalms, Matthew)
- Vary quote authors (no author >2 times)
- Authentic Bible verses only
- Full author names

JSON format (NO markdown):
[
  {
    "bibleVerse": {"text": "I can do all things through Christ who strengthens me.", "reference": "Philippians 4:13"},
    "quote": {"text": "Discipline equals freedom.", "author": "Jocko Willink"}
  },
  {
    "bibleVerse": {"text": "Trust in the Lord with all your heart.", "reference": "Proverbs 3:5"},
    "quote": {"text": "The only way to do great work is to love what you do.", "author": "Steve Jobs"}
  }
  ... (8 more with BOTH fields)
]"""
        
        print("🤖 Generating 10 quotes with Gemini... (this takes ~3-5 seconds)")
        response = gemini_model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Clean markdown if present
        if response_text.startswith('```'):
            response_text = response_text.split('```')[1]
            if response_text.startswith('json'):
                response_text = response_text[4:].strip()
        
        # Parse JSON
        batch = json.loads(response_text)
        
        if not isinstance(batch, list) or len(batch) < 7:
            print(f"❌ Invalid batch: expected 10, got {len(batch) if isinstance(batch, list) else 'not a list'}")
            return None
        
        # CRITICAL: Filter out items missing bibleVerse or quote
        valid_batch = []
        for i, item in enumerate(batch):
            if 'bibleVerse' in item and 'quote' in item:
                # Check that bibleVerse has required fields
                verse = item.get('bibleVerse', {})
                quote = item.get('quote', {})
                if verse.get('text') and verse.get('reference') and quote.get('text') and quote.get('author'):
                    valid_batch.append(item)
                else:
                    print(f"⚠️ Item {i+1} incomplete: missing fields in verse or quote")
            else:
                print(f"⚠️ Item {i+1} missing {'bibleVerse' if 'bibleVerse' not in item else 'quote'}")
        
        if len(valid_batch) < 7:
            print(f"❌ Too many invalid items: only {len(valid_batch)}/10 valid")
            return None
        
        print(f"✅ Validated: {len(valid_batch)}/{len(batch)} items have both verse and quote")
        
        # Shuffle for randomness
        random.shuffle(valid_batch)
        
        print(f"✅ Generated and shuffled {len(valid_batch)} unique quotes!")
        return valid_batch
        
    except Exception as e:
        print(f"❌ Batch generation failed: {str(e)}")
        return None


def get_next_motivation_from_queue(user_data):
    """Get next motivation from queue, regenerate if depleted"""
    
    # If no Gemini API, just use static quotes (don't bother with queue)
    if not gemini_model:
        print("⚠️ No Gemini API, using static quotes")
        return get_daily_motivation()
    
    # Initialize queue if not exists
    if 'quoteQueue' not in user_data or not user_data.get('quoteQueue'):
        print("📥 Quote queue empty, generating new batch...")
        new_batch = generate_10_motivation_batch()
        
        if new_batch:
            user_data['quoteQueue'] = new_batch
            user_data['queuePosition'] = 0
        else:
            # Gemini failed, fallback to static
            print("⚠️ Generation failed, using static quote")
            return get_daily_motivation()
    
    # Check if queue is depleted
    if user_data.get('queuePosition', 0) >= len(user_data.get('quoteQueue', [])):
        print("📥 Quote queue depleted, regenerating...")
        new_batch = generate_10_motivation_batch()
        
        if new_batch:
            user_data['quoteQueue'] = new_batch
            user_data['queuePosition'] = 0
        else:
            print("⚠️ Regeneration failed, using static quote")
            return get_daily_motivation()
    
    # Get next quote from queue
    if user_data.get('quoteQueue') and user_data.get('queuePosition', 0) < len(user_data['quoteQueue']):
        motivation = user_data['quoteQueue'][user_data['queuePosition']]
        user_data['queuePosition'] = user_data.get('queuePosition', 0) + 1
        
        # Add current date
        motivation['date'] = datetime.now().isoformat()
        
        print(f"✅ Served quote {user_data['queuePosition']}/{len(user_data['quoteQueue'])} from queue")
        return motivation
    else:
        # Final fallback
        print("⚠️ Queue error, using static quote")
        return get_daily_motivation()



def is_today(date_str):
    if not date_str:
        return False
    try:
        date = datetime.fromisoformat(date_str).date()
        return date == datetime.now().date()
    except:
        return False

def get_daily_motivation():
    today = datetime.now().date()
    random.seed(today.toordinal())
    
    verse = random.choice(BIBLE_VERSES)
    quote = random.choice(MOTIVATION_QUOTES)
    
    random.seed()
    
    return {
        'bibleVerse': verse,
        'quote': quote,
        'date': datetime.now().isoformat()
    }



@app.route('/')
def index():
    if 'user_id' in session:
        return render_template('dashboard.html', username=session['user_id'])
    return render_template('login.html')

@app.route('/test', methods=['GET'])
def test_api():
    return jsonify({
        'status': 'ok',
        'message': 'Flask server is running!',
        'storage': 'PostgreSQL' if USE_DATABASE else 'JSON file',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.json
        username = data.get('username', '').strip()
        passcode = data.get('passcode', '').strip()
        
        if not username or not passcode:
            return jsonify({'error': 'Username and passcode required'}), 400
        
        if len(passcode) != 4 or not passcode.isdigit():
            return jsonify({'error': 'Passcode must be 4 digits'}), 400
        
        if get_user_wrapper(username):
            return jsonify({'error': 'Username already taken'}), 400
        
        user_data = {
            'currentStreak': 0,
            'longestStreak': 0,
            'lastCompletedDate': None,
            'totalDaysCompleted': 0,
            'categories': [
                {'name': 'General', 'icon': '📝', 'tasks': []},
            ],
            'milestones': [],
            'dailyMotivation': get_daily_motivation(),
            'endGoal': '',
            'history': [],
            'badHabits': []
        }
        
        success = create_user_wrapper(username, passcode, user_data)
        
        if not success:
            return jsonify({'error': 'Failed to create user'}), 500
        
        session['user_id'] = username
        
        return jsonify({'success': True, 'username': username})
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.json
        username = data.get('username', '').strip()
        passcode = data.get('passcode', '').strip()
        
        if not username or not passcode:
            return jsonify({'error': 'Username and passcode required'}), 400
        
        user = get_user_wrapper(username)
        
        if not user or user['passcode'] != passcode:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        session['user_id'] = username
        
        return jsonify({'success': True, 'username': username})
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return jsonify({'success': True})

@app.route('/api/data', methods=['GET'])
@login_required
def get_data():
    user_id = session['user_id']
    data = get_user_data(user_id)
    data = check_streak_status(data)
    
    # Check if this is a new user (no quoteQueue yet)
    is_new_user = 'quoteQueue' not in data or not data.get('quoteQueue')
    
    if is_new_user:
        print(f"🎉 New user detected! Generating initial quote queue...")
        # Generate quotes for new user
        data['dailyMotivation'] = get_next_motivation_from_queue(data)
        print(f"🔍 Initial motivation set for new user")
        save_user_data(user_id, data)
    elif not is_today(data.get('dailyMotivation', {}).get('date')):
        # Use queue system for daily motivation (existing user, new day)
        data['dailyMotivation'] = get_next_motivation_from_queue(data)
        print(f"🔍 Daily motivation on page load: {data['dailyMotivation']}")
        save_user_data(user_id, data)
    
    return jsonify(data)

@app.route('/api/data', methods=['POST'])
@login_required
def save_data_endpoint():
    """Save all user data at once - PRESERVES backend-only fields"""
    try:
        user_id = session['user_id']
        new_data = request.json
        
        # Validate data structure
        if not isinstance(new_data, dict):
            return jsonify({'error': 'Invalid data format'}), 400
        
        # CRITICAL: Get existing data first to preserve backend-only fields!
        existing_data = get_user_data(user_id)
        
        # Preserve backend-only fields (quoteQueue, queuePosition)
        if 'quoteQueue' in existing_data:
            new_data['quoteQueue'] = existing_data['quoteQueue']
        if 'queuePosition' in existing_data:
            new_data['queuePosition'] = existing_data['queuePosition']
        
        print(f"💾 Saving with quoteQueue: {('quoteQueue' in new_data)}, pos: {new_data.get('queuePosition', 'N/A')}")
        
        # Save merged data to database or JSON file
        success = save_user_data(user_id, new_data)
        
        if success:
            print(f"✅ Data saved successfully for user {user_id}")
            return jsonify({'success': True, 'message': 'Data saved successfully'})
        else:
            print(f"❌ Save failed for user {user_id}")
            return jsonify({'error': 'Failed to save data'}), 500
    except Exception as e:
        print(f"❌ Error saving data: {str(e)}")
        return jsonify({'error': f'Save failed: {str(e)}'}), 500

@app.route('/api/motivation/refresh', methods=['POST'])
@login_required
def refresh_motivation():
    user_id = session['user_id']
    data = get_user_data(user_id)
    
    # Get next motivation from queue (auto-generates if depleted)
    new_motivation = get_next_motivation_from_queue(data)
    data['dailyMotivation'] = new_motivation
    
    # Debug: Print what we're sending
    print(f"🔍 Sending motivation: {new_motivation}")
    
    # Debug: Print what we're about to save
    print(f"🔍 About to save data with keys: {list(data.keys())}")
    if 'quoteQueue' in data:
        print(f"   quoteQueue length: {len(data['quoteQueue'])}")
        print(f"   queuePosition: {data.get('queuePosition')}")
    else:
        print(f"   ⚠️ NO quoteQueue in data!")
    
    save_user_data(user_id, data)
    
    # Return full data object so frontend stays in sync
    return jsonify({'success': True, 'data': data, 'motivation': data['dailyMotivation']})

@app.route('/api/complete-day', methods=['POST'])
@login_required
def complete_day():
    user_id = session['user_id']
    data = get_user_data(user_id)
    
    today = datetime.now().date()
    last_date = None
    
    if data['lastCompletedDate']:
        last_date = datetime.fromisoformat(data['lastCompletedDate']).date()
    
    if last_date == today:
        return jsonify({'error': 'Already completed today'}), 400
    
    total_tasks = 0
    completed_tasks = 0
    
    for category in data['categories']:
        for task in category['tasks']:
            total_tasks += 1
            if task.get('completed', False):
                completed_tasks += 1
    
    if total_tasks == 0:
        return jsonify({'error': 'Add daily tasks first'}), 400
    
    if completed_tasks < total_tasks:
        return jsonify({'error': f'Complete all tasks first ({completed_tasks}/{total_tasks} done)'}), 400
    
    yesterday = today - timedelta(days=1)
    
    if last_date == yesterday:
        data['currentStreak'] += 1
    else:
        data['currentStreak'] = 1
    
    if data['currentStreak'] > data['longestStreak']:
        data['longestStreak'] = data['currentStreak']
    
    data['totalDaysCompleted'] += 1
    data['lastCompletedDate'] = datetime.now().isoformat()
    
    data['history'].append({
        'date': datetime.now().isoformat(),
        'tasksCompleted': total_tasks,
        'streak': data['currentStreak']
    })
    
    for category in data['categories']:
        category['tasks'] = [
            {**task, 'completed': False}
            for task in category['tasks']
            if task.get('recurring', False)
        ]
    
    save_user_data(user_id, data)
    
    return jsonify({
        'success': True,
        'streak': data['currentStreak'],
        'data': data
    })

@app.route('/api/categories', methods=['POST'])
@login_required
def add_category():
    user_id = session['user_id']
    data = get_user_data(user_id)
    
    category_data = request.json
    name = category_data.get('name', '').strip()
    icon = category_data.get('icon', '📝').strip()
    
    if not name:
        return jsonify({'error': 'Category name required'}), 400
    
    for cat in data['categories']:
        if cat['name'].lower() == name.lower():
            return jsonify({'error': 'Category already exists'}), 400
    
    data['categories'].append({
        'name': name,
        'icon': icon,
        'tasks': []
    })
    
    save_user_data(user_id, data)
    return jsonify({'success': True, 'data': data})

@app.route('/api/categories/<int:index>', methods=['DELETE'])
@login_required
def delete_category(index):
    user_id = session['user_id']
    data = get_user_data(user_id)
    
    if index < 0 or index >= len(data['categories']):
        return jsonify({'error': 'Invalid category'}), 400
    
    data['categories'].pop(index)
    save_user_data(user_id, data)
    
    return jsonify({'success': True, 'data': data})

@app.route('/api/tasks', methods=['POST'])
@login_required
def add_task():
    user_id = session['user_id']
    data = get_user_data(user_id)
    
    task_data = request.json
    category_index = task_data.get('categoryIndex')
    task_text = task_data.get('task', '').strip()
    recurring = task_data.get('recurring', False)
    
    if category_index is None or not task_text:
        return jsonify({'error': 'Category and task required'}), 400
    
    if category_index < 0 or category_index >= len(data['categories']):
        return jsonify({'error': 'Invalid category'}), 400
    
    data['categories'][category_index]['tasks'].append({
        'text': task_text,
        'completed': False,
        'recurring': recurring
    })
    
    save_user_data(user_id, data)
    return jsonify({'success': True, 'data': data})

@app.route('/api/tasks/<int:category_index>/<int:task_index>', methods=['DELETE'])
@login_required
def delete_task(category_index, task_index):
    user_id = session['user_id']
    data = get_user_data(user_id)
    
    if category_index < 0 or category_index >= len(data['categories']):
        return jsonify({'error': 'Invalid category'}), 400
    
    tasks = data['categories'][category_index]['tasks']
    if task_index < 0 or task_index >= len(tasks):
        return jsonify({'error': 'Invalid task'}), 400
    
    tasks.pop(task_index)
    save_user_data(user_id, data)
    
    return jsonify({'success': True, 'data': data})

@app.route('/api/tasks/<int:category_index>/<int:task_index>/toggle', methods=['POST'])
@login_required
def toggle_task(category_index, task_index):
    user_id = session['user_id']
    data = get_user_data(user_id)
    
    if category_index < 0 or category_index >= len(data['categories']):
        return jsonify({'error': 'Invalid category'}), 400
    
    tasks = data['categories'][category_index]['tasks']
    if task_index < 0 or task_index >= len(tasks):
        return jsonify({'error': 'Invalid task'}), 400
    
    tasks[task_index]['completed'] = not tasks[task_index].get('completed', False)
    
    save_user_data(user_id, data)
    return jsonify({'success': True, 'data': data})

@app.route('/api/tasks/clear-all', methods=['POST'])
@login_required
def clear_all_checkboxes():
    user_id = session['user_id']
    data = get_user_data(user_id)
    
    for category in data['categories']:
        for task in category['tasks']:
            task['completed'] = False
    
    save_user_data(user_id, data)
    return jsonify({'success': True, 'data': data})

@app.route('/api/milestones', methods=['POST'])
@login_required
def add_milestone():
    user_id = session['user_id']
    data = get_user_data(user_id)
    
    milestone_data = request.json
    text = milestone_data.get('text', '').strip()
    target_date = milestone_data.get('targetDate')
    milestone_type = milestone_data.get('type', 'milestone')
    category = milestone_data.get('category', None)
    priority = milestone_data.get('priority', 'medium')
    
    if not text or not target_date:
        return jsonify({'error': 'Text and date required'}), 400
    
    if 'milestones' not in data:
        data['milestones'] = []
    
    data['milestones'].append({
        'text': text,
        'targetDate': target_date,
        'completed': False,
        'type': milestone_type,
        'category': category,
        'priority': priority
    })
    
    save_user_data(user_id, data)
    return jsonify({'success': True, 'data': data})

@app.route('/api/milestones/<int:index>', methods=['DELETE'])
@login_required
def delete_milestone(index):
    user_id = session['user_id']
    data = get_user_data(user_id)
    
    if 'milestones' not in data or index < 0 or index >= len(data['milestones']):
        return jsonify({'error': 'Invalid milestone'}), 400
    
    data['milestones'].pop(index)
    save_user_data(user_id, data)
    
    return jsonify({'success': True, 'data': data})

@app.route('/api/milestones/<int:index>/toggle', methods=['POST'])
@login_required
def toggle_milestone(index):
    user_id = session['user_id']
    data = get_user_data(user_id)
    
    if 'milestones' not in data or index < 0 or index >= len(data['milestones']):
        return jsonify({'error': 'Invalid milestone'}), 400
    
    data['milestones'][index]['completed'] = not data['milestones'][index].get('completed', False)
    save_user_data(user_id, data)
    
    return jsonify({'success': True, 'data': data})

@app.route('/api/bad-habits/relapse', methods=['POST'])
@login_required
def mark_relapse():
    user_id = session['user_id']
    data = get_user_data(user_id)
    habit_index = request.json.get('habitIndex')
    
    if habit_index < 0 or habit_index >= len(data['badHabits']):
        return jsonify({'error': 'Invalid habit index'}), 400
    
    habit = data['badHabits'][habit_index]
    
    if 'relapses' not in habit:
        habit['relapses'] = []
    
    habit['relapses'].append({
        'date': datetime.now().isoformat(),
        'daysSober': habit['currentDaysClean']
    })
    
    if habit['currentDaysClean'] > habit['longestStreak']:
        habit['longestStreak'] = habit['currentDaysClean']
    
    habit['currentDaysClean'] = 0
    habit['lastRelapseDate'] = datetime.now().isoformat()
    habit['cleanSince'] = datetime.now().isoformat()
    
    save_user_data(user_id, data)
    
    return jsonify({
        'success': True,
        'data': data
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    print(f"\n🚀 Starting server on http://localhost:{port}")
    print(f"📁 Storage mode: {'PostgreSQL' if USE_DATABASE else 'JSON file (local)'}\n")
    app.run(debug=True, port=port, host='0.0.0.0')
# Admin endpoint to manually generate quote queue (optional)
@app.route('/api/admin/generate-quotes', methods=['POST'])
@login_required
def admin_generate_quotes():
    """Manually trigger quote generation (for testing/admin)"""
    user_id = session['user_id']
    data = get_user_data(user_id)
    
    new_batch = generate_10_motivation_batch()
    
    if new_batch:
        data['quoteQueue'] = new_batch
        data['queuePosition'] = 0
        save_user_data(user_id, data)
        
        return jsonify({
            'success': True, 
            'message': f'Generated {len(new_batch)} quotes',
            'count': len(new_batch)
        })
    else:
        return jsonify({'error': 'Failed to generate quotes'}), 500