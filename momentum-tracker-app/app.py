from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from datetime import datetime, timedelta
from functools import wraps
import json
import os
from database import init_db, get_user, create_user, update_user_data, get_all_users

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = True  # Set True if using HTTPS
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# Initialize database on startup
if os.environ.get('DATABASE_URL'):
    try:
        init_db()
        print("✅ Database connected and initialized")
    except Exception as e:
        print(f"❌ Database initialization error: {e}")
else:
    print("⚠️ No DATABASE_URL found - running without database")

def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Not logged in'}), 401
        return f(*args, **kwargs)
    return decorated_function

def get_user_data(username):
    """Get data for specific user"""
    user = get_user(username)
    
    if not user:
        return None
    
    user_data = user['data'] if isinstance(user['data'], dict) else json.loads(user['data'])
    
    # Ensure categories exist (migration from old structure)
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
        update_user_data(username, user_data)
    
    return user_data

def save_user_data(username, data):
    """Save user data to database"""
    update_user_data(username, data)

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
        username = data.get('username', '').strip()
        passcode = data.get('passcode', '').strip()
        
        print(f"📝 Registration attempt: {username}")
        
        if not username or not passcode:
            return jsonify({'error': 'Username and passcode required'}), 400
        
        if len(passcode) != 4 or not passcode.isdigit():
            return jsonify({'error': 'Passcode must be 4 digits'}), 400
        
        # Check if user exists
        if get_user(username):
            return jsonify({'error': 'Username already taken'}), 400
        
        # Create new user data
        user_data = {
            'currentStreak': 0,
            'longestStreak': 0,
            'lastCompletedDate': None,
            'totalDaysCompleted': 0,
            'categories': [
                {'name': 'General', 'icon': '📝', 'tasks': []},
            ],
            'milestones': [],
            'endGoal': '',
            'history': [],
            'badHabits': []
        }
        
        # Create user in database
        success = create_user(username, passcode, user_data)
        
        if not success:
            return jsonify({'error': 'Failed to create user'}), 500
        
        print(f"✅ User {username} created successfully")
        
        # Log them in
        session['user_id'] = username
        
        return jsonify({'success': True, 'username': username})
        
    except Exception as e:
        print(f"❌ Registration error: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/login', methods=['POST'])
def login():
    """Login user"""
    try:
        data = request.json
        username = data.get('username', '').strip()
        passcode = data.get('passcode', '').strip()
        
        print(f"🔑 Login attempt: {username}")
        
        if not username or not passcode:
            return jsonify({'error': 'Username and passcode required'}), 400
        
        user = get_user(username)
        
        if not user or user['passcode'] != passcode:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        session['user_id'] = username
        print(f"✅ User {username} logged in successfully")
        
        return jsonify({'success': True, 'username': username})
        
    except Exception as e:
        print(f"❌ Login error: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

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
    
    # 🔁 NEW: Reset task checkboxes BUT keep recurring tasks
    for category in data['categories']:
        # Filter: keep recurring tasks, remove one-time tasks
        category['tasks'] = [
            {**task, 'completed': False}  # Reset checkbox
            for task in category['tasks']
            if task.get('recurring', False)  # Only keep if recurring
        ]
    
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
    icon = category_data.get('icon', '📝').strip()
    
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
    recurring = task_data.get('recurring', False)  # 🔁 NEW: Get recurring flag
    
    if category_index is None or not task_text:
        return jsonify({'error': 'Category and task required'}), 400
    
    if category_index < 0 or category_index >= len(data['categories']):
        return jsonify({'error': 'Invalid category'}), 400
    
    data['categories'][category_index]['tasks'].append({
        'text': task_text,
        'completed': False,
        'recurring': recurring  # 🔁 NEW: Save recurring flag
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

@app.route('/api/tasks/clear-all', methods=['POST'])
@login_required
def clear_all_checkboxes():
    """Clear all task checkboxes (set all to uncompleted)"""
    user_id = session['user_id']
    data = get_user_data(user_id)
    
    # Reset all tasks to uncompleted
    for category in data['categories']:
        for task in category['tasks']:
            task['completed'] = False
    
    save_user_data(user_id, data)
    return jsonify({'success': True, 'data': data})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=True, port=port)