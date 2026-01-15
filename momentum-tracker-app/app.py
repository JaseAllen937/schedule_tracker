import os
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import json

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = '4017dfd7fde78f3d24f6ceb5fe285314'
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = True  # Set True if using HTTPS
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)  # Session expires after 24 hours
DATA_FILE = 'users_data.json'
DATA_FILE = 'users_data.json'

# Helper functions
def load_users():
    """Load all user data from file"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    """Save all user data to file"""
    with open(DATA_FILE, 'w') as f:
        json.dump(users, f, indent=2)

def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Not logged in'}), 401
        return f(*args, **kwargs)
    return decorated_function

def get_user_data(user_id):
    """Get data for specific user"""
    users = load_users()
    if user_id not in users:
        # Create new user with default data
        users[user_id] = {
            'passcode': '',
            'username': user_id,
            'created': datetime.now().isoformat(),
            'data': {
                'currentStreak': 0,
                'longestStreak': 0,
                'lastCompletedDate': None,
                'totalDaysCompleted': 0,
                'dailyTasks': [],
                'milestones': [],
                'endGoal': '',
                'history': [],
                'badHabits': []  # New: tracking habits to break
            }
        }
        save_users(users)
    if 'categories' not in users[user_id]['data']:
        users[user_id]['data']['categories'] = []
        save_users(users)

    return users[user_id]['data']

def save_user_data(user_id, data):
    """Save data for specific user"""
    users = load_users()
    if user_id in users:
        users[user_id]['data'] = data
        save_users(users)

def check_streak_status(data):
    """Check if streak should break"""
    if not data['lastCompletedDate']:
        return data
    
    last_date = datetime.fromisoformat(data['lastCompletedDate']).date()
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    
    if last_date < yesterday:
        data['currentStreak'] = 0
    
    return data

# Routes
@app.route('/')
def index():
    """Main page"""
    if 'user_id' in session:
        return render_template('dashboard.html', username=session['user_id'])
    return render_template('login.html')

@app.route('/test-page')
def test_page():
    """Test page to verify server is working"""
    return render_template('test.html')

@app.route('/test', methods=['GET'])
def test_api():
    """Simple test endpoint"""
    return jsonify({
        'status': 'ok',
        'message': 'Flask server is running!',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/register', methods=['POST'])
def register():
    """Register new user"""
    try:
        data = request.json
        print(f"Registration attempt: {data}")  # Debug logging
        
        user_id = data.get('username', '').strip().lower()
        passcode = data.get('passcode', '').strip()
        
        if not user_id or not passcode:
            print("Error: Missing username or passcode")
            return jsonify({'error': 'Username and passcode required'}), 400
        
        if len(passcode) != 4 or not passcode.isdigit():
            print("Error: Invalid passcode format")
            return jsonify({'error': 'Passcode must be 4 digits'}), 400
        
        users = load_users()
        
        if user_id in users:
            print(f"Error: Username {user_id} already exists")
            return jsonify({'error': 'Username already exists'}), 400
        
        # Create new user
        users[user_id] = {
            'passcode': passcode,
            'username': user_id,
            'created': datetime.now().isoformat(),
            'data': {
                'currentStreak': 0,
                'longestStreak': 0,
                'lastCompletedDate': None,
                'totalDaysCompleted': 0,
                'dailyTasks': [],
                'milestones': [],
                'endGoal': '',
                'history': [],
                'badHabits': []
            }
        }
        
        save_users(users)
        session['user_id'] = user_id
        
        print(f"Registration successful for {user_id}")
        return jsonify({'success': True, 'username': user_id})
    except Exception as e:
        print(f"Registration error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    """Login user"""
    try:
        data = request.json
        print(f"Login attempt: {data}")  # Debug logging
        
        user_id = data.get('username', '').strip().lower()
        passcode = data.get('passcode', '').strip()
        
        users = load_users()
        
        if user_id not in users:
            print(f"Error: User {user_id} not found")
            return jsonify({'error': 'User not found'}), 401
        
        if users[user_id]['passcode'] != passcode:
            print(f"Error: Invalid passcode for {user_id}")
            return jsonify({'error': 'Invalid passcode'}), 401
        
        session['user_id'] = user_id
        print(f"Login successful for {user_id}")
        
        return jsonify({'success': True, 'username': user_id})
    except Exception as e:
        print(f"Login error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    """Logout user"""
    session.pop('user_id', None)
    return jsonify({'success': True})

@app.route('/api/data', methods=['GET'])
@login_required
def get_data():
    """Get user data"""
    user_id = session['user_id']
    data = get_user_data(user_id)
    data = check_streak_status(data)
    save_user_data(user_id, data)
    return jsonify(data)

@app.route('/api/data', methods=['POST'])
@login_required
def update_data():
    """Update user data"""
    user_id = session['user_id']
    data = request.json
    save_user_data(user_id, data)
    return jsonify({'success': True})

@app.route('/api/complete-day', methods=['POST'])
@login_required
def complete_day():
    """Mark day as complete - only if ALL tasks are checked"""
    user_id = session['user_id']
    data = get_user_data(user_id)
    
    today = datetime.now().date()
    last_date = None
    
    if data['lastCompletedDate']:
        last_date = datetime.fromisoformat(data['lastCompletedDate']).date()
    
    if last_date == today:
        return jsonify({'error': 'Already completed today'}), 400
    
    # Check if ALL tasks across ALL categories are completed
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
    
    # Update streak
    yesterday = today - timedelta(days=1)
    
    if last_date == yesterday:
        data['currentStreak'] += 1
    else:
        data['currentStreak'] = 1
    
    # Update records
    if data['currentStreak'] > data['longestStreak']:
        data['longestStreak'] = data['currentStreak']
    
    data['totalDaysCompleted'] += 1
    data['lastCompletedDate'] = datetime.now().isoformat()
    
    # Add to history
    data['history'].append({
        'date': datetime.now().isoformat(),
        'tasksCompleted': total_tasks,
        'streak': data['currentStreak']
    })
    
    # Reset all task checkboxes for tomorrow
    for category in data['categories']:
        for task in category['tasks']:
            task['completed'] = False
    
    save_user_data(user_id, data)
    
    return jsonify({
        'success': True,
        'streak': data['currentStreak'],
        'data': data
    })

@app.route('/api/bad-habits/relapse', methods=['POST'])
@login_required
def mark_relapse():
    """Mark a relapse for a bad habit"""
    user_id = session['user_id']
    data = get_user_data(user_id)
    habit_index = request.json.get('habitIndex')
    
    if habit_index < 0 or habit_index >= len(data['badHabits']):
        return jsonify({'error': 'Invalid habit index'}), 400
    
    habit = data['badHabits'][habit_index]
    
    # Record the relapse
    if 'relapses' not in habit:
        habit['relapses'] = []
    
    habit['relapses'].append({
        'date': datetime.now().isoformat(),
        'daysSober': habit['currentDaysClean']
    })
    
    # Update longest streak if needed
    if habit['currentDaysClean'] > habit['longestStreak']:
        habit['longestStreak'] = habit['currentDaysClean']
    
    # Reset current streak
    habit['currentDaysClean'] = 0
    habit['lastRelapseDate'] = datetime.now().isoformat()
    habit['cleanSince'] = datetime.now().isoformat()
    
    save_user_data(user_id, data)
    
    return jsonify({
        'success': True,
        'data': data
    })

@app.route('/api/categories', methods=['POST'])
@login_required
def add_category():
    """Add new category"""
    user_id = session['user_id']
    data = get_user_data(user_id)
    
    category_data = request.json
    name = category_data.get('name', '').strip()
    icon = category_data.get('icon', '📁').strip()
    
    if not name:
        return jsonify({'error': 'Category name required'}), 400
    
    # Check if category already exists
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
    """Delete category"""
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
    """Add task to category"""
    user_id = session['user_id']
    data = get_user_data(user_id)
    
    task_data = request.json
    category_index = task_data.get('categoryIndex')
    task_text = task_data.get('task', '').strip()
    
    if category_index is None or not task_text:
        return jsonify({'error': 'Category and task required'}), 400
    
    if category_index < 0 or category_index >= len(data['categories']):
        return jsonify({'error': 'Invalid category'}), 400
    
    data['categories'][category_index]['tasks'].append({
        'text': task_text,
        'completed': False
    })
    
    save_user_data(user_id, data)
    return jsonify({'success': True, 'data': data})

@app.route('/api/tasks/<int:category_index>/<int:task_index>', methods=['DELETE'])
@login_required
def delete_task(category_index, task_index):
    """Delete task"""
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
    """Toggle task completion"""
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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=True, port=5001)