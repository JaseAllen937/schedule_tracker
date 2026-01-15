# 🔧 DEBUGGING GUIDE - Login Not Working

## How Flask + JavaScript Connection Works

**This is NOT WordPress or static HTML. Here's how it actually works:**

1. **Flask Server** (Python) runs on your computer at `http://localhost:5001`
2. **HTML Pages** are served BY Flask (templates folder)
3. **JavaScript in the HTML** makes fetch requests BACK to Flask API endpoints
4. **Flask processes the request** and returns JSON
5. **JavaScript updates the page** based on the response

**Think of it like this:**
- Flask = Backend server (brain)
- HTML/JS = Frontend (face)
- API endpoints = The connection between them

---

## Step-by-Step Debugging

### **STEP 1: Is Flask Running?**

**Run the server:**
```bash
python app.py
```

**You should see:**
```
 * Running on http://127.0.0.1:5001
 * Running on http://localhost:5001
```

**If you DON'T see this:**
- Check if Flask is installed: `pip install Flask`
- Check for Python errors in the terminal
- Make sure you're in the right directory

---

### **STEP 2: Test the Server**

**Open your browser to:**
```
http://localhost:5001/test-page
```

**You should see:**
- A green terminal-style test page
- "Server is running ✓" message
- Test buttons

**If page doesn't load:**
- Server isn't running (go back to Step 1)
- Wrong URL (make sure it's localhost:5001)
- Port 5001 is blocked by firewall

**Click "Test Register":**
- Should create a test user
- Should show green success message
- Check the browser console (F12) for logs

---

### **STEP 3: Check Browser Console**

**Open Developer Tools:**
- Windows: `F12` or `Ctrl+Shift+I`
- Mac: `Cmd+Option+I`

**Go to Console tab**

**Try to login on main page, you should see:**
```
Attempting login... {username: "test", passcode: "****"}
Response status: 200
Response data: {success: true, username: "test"}
Login successful, redirecting...
```

**If you see errors:**
- `net::ERR_CONNECTION_REFUSED` = Server not running
- `404 Not Found` = Wrong URL or route doesn't exist
- `CORS error` = Shouldn't happen (Flask serves the HTML)
- `SyntaxError` = JavaScript bug in HTML

---

### **STEP 4: Check Flask Terminal**

**When you try to login, Flask terminal should show:**
```
Login attempt: {'username': 'test', 'passcode': '1234'}
Login successful for test
127.0.0.1 - - [15/Jan/2026 18:50:01] "POST /api/login HTTP/1.1" 200 -
```

**If you DON'T see this:**
- Request isn't reaching Flask
- Check the browser console for errors
- Make sure you're using the right port

**If you see errors:**
- `KeyError` = Missing data in request
- `500 Internal Server Error` = Bug in Flask code
- `401 Unauthorized` = Wrong username/passcode

---

## Common Issues & Fixes

### **Issue: "Cannot POST /api/login"**

**Problem:** Flask route not defined or wrong URL

**Fix:**
1. Check app.py has `@app.route('/api/login', methods=['POST'])`
2. Make sure server restarted after code changes
3. Check the URL in JavaScript is exactly `/api/login`

---

### **Issue: Form submits but nothing happens**

**Problem:** JavaScript not intercepting form submit

**Fix:**
1. Check browser console for JavaScript errors
2. Make sure form has `onsubmit="handleLogin(event)"`
3. Check function is defined in `<script>` tag

---

### **Issue: "User not found" or "Invalid passcode"**

**Problem:** Login data incorrect or not saved

**Fix:**
1. First REGISTER a user
2. Check `users_data.json` file exists and has your user
3. Username is case-insensitive (converted to lowercase)
4. Passcode must be exactly 4 digits

---

### **Issue: Logs in but redirects back to login page**

**Problem:** Session not being saved

**Fix:**
1. Check Flask has `app.secret_key` set (it does)
2. Make sure cookies are enabled in browser
3. Try incognito/private window
4. Check for JavaScript errors preventing redirect

---

### **Issue: "Module not found: flask"**

**Problem:** Flask not installed

**Fix:**
```bash
pip install Flask
# or
pip3 install Flask
```

---

### **Issue: "Address already in use"**

**Problem:** Port 5001 already taken

**Fix:**
```bash
# Find what's using port 5001
# Windows:
netstat -ano | findstr :5001

# Mac/Linux:
lsof -i :5001

# Kill the process or change port in app.py
```

---

## Manual Testing Process

### **Test 1: Server Responds**
```bash
# In terminal
curl http://localhost:5001/test

# Should return JSON:
{"message":"Flask server is running!","status":"ok","timestamp":"..."}
```

### **Test 2: Register User**
```bash
curl -X POST http://localhost:5001/api/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","passcode":"1234"}'

# Should return:
{"success":true,"username":"testuser"}
```

### **Test 3: Login User**
```bash
curl -X POST http://localhost:5001/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","passcode":"1234"}'

# Should return:
{"success":true,"username":"testuser"}
```

### **Test 4: Check Data File**
```bash
# Check if users_data.json was created
cat users_data.json

# Should show user data
```

---

## Understanding the Code Flow

### **When you click "Login":**

1. **JavaScript intercepts form:**
   ```javascript
   async function handleLogin(e) {
       e.preventDefault();  // Stop normal form submit
   ```

2. **JavaScript makes POST request:**
   ```javascript
   const response = await fetch('/api/login', {
       method: 'POST',
       headers: { 'Content-Type': 'application/json' },
       body: JSON.stringify({ username, passcode })
   });
   ```

3. **Flask receives request:**
   ```python
   @app.route('/api/login', methods=['POST'])
   def login():
       data = request.json  # Get the JSON data
       user_id = data.get('username')
   ```

4. **Flask validates and sets session:**
   ```python
   if users[user_id]['passcode'] == passcode:
       session['user_id'] = user_id  # Save login state
       return jsonify({'success': True})
   ```

5. **JavaScript receives response:**
   ```javascript
   if (response.ok) {
       window.location.href = '/';  // Redirect to dashboard
   }
   ```

6. **Browser requests '/' again:**
   ```python
   @app.route('/')
   def index():
       if 'user_id' in session:  # Now logged in!
           return render_template('dashboard.html')
   ```

---

## Quick Checklist

**Before asking for help, verify:**

- [ ] Flask is installed (`pip list | grep Flask`)
- [ ] Server is running (`python app.py`)
- [ ] You see Flask startup messages in terminal
- [ ] Browser is pointed to `http://localhost:5001`
- [ ] Browser console shows no JavaScript errors (F12)
- [ ] Test page works (`http://localhost:5001/test-page`)
- [ ] You can register a test user on test page
- [ ] Flask terminal shows request logs
- [ ] `users_data.json` file exists after registration
- [ ] You're using the correct username/passcode

---

## Still Not Working?

**Run these diagnostic commands:**

```bash
# 1. Check Python version (need 3.7+)
python --version

# 2. Check Flask is installed
python -c "import flask; print(flask.__version__)"

# 3. Test basic Flask
python -c "from flask import Flask; app=Flask(__name__); print('Flask OK')"

# 4. Check if port 5001 is available
# Windows:
netstat -an | findstr :5001
# Mac/Linux:
lsof -i :5001

# 5. Test with curl
curl http://localhost:5001/test
```

**Copy all output and check for errors.**

---

## Understanding "No JS Connection to Python"

**Your question was:** "Doesn't there need to be a js to connect the python to the html?"

**Answer:** The connection IS the HTTP requests (fetch).

**It's already there:**
```javascript
// This IS the connection:
const response = await fetch('/api/login', {
    method: 'POST',
    body: JSON.stringify({ username, passcode })
});
```

**What this does:**
1. Browser running JavaScript
2. Makes HTTP POST request to Flask server
3. Flask receives request at `/api/login` endpoint
4. Flask processes login
5. Flask returns JSON response
6. JavaScript receives response and reacts

**There's no "extra file" needed.** The fetch() function IS the connection.

**Think of it like:**
- Fetch = Phone call
- Flask endpoint = Phone number
- JSON = What you say on the call

---

## What's Different From Static HTML?

**Static HTML (what you might be used to):**
- HTML file opens directly in browser (file://)
- No server, no backend
- All data in localStorage or nowhere

**Flask App (what this is):**
- Python server runs first
- Server serves HTML at http://localhost:5001
- HTML makes requests back to server
- Data stored on server (users_data.json)

**This is a REAL web application, not just a webpage.**

---

## Emergency Reset

**If everything is broken:**

```bash
# 1. Stop the server (Ctrl+C)

# 2. Delete data file
rm users_data.json  # Mac/Linux
del users_data.json  # Windows

# 3. Reinstall Flask
pip uninstall Flask
pip install Flask

# 4. Restart server
python app.py

# 5. Go to test page
# http://localhost:5001/test-page

# 6. Click "Test Register"

# 7. If that works, go to main page
# http://localhost:5001
```

---

## Getting More Help

**When asking for help, include:**

1. **Flask terminal output** (copy all of it)
2. **Browser console errors** (F12 → Console tab → screenshot)
3. **What you see in browser** (screenshot)
4. **What you clicked/typed**
5. **Python version** (`python --version`)
6. **Operating system** (Windows/Mac/Linux)

**DON'T just say "login doesn't work"**

**DO say:**
"I clicked login with username 'test' and passcode '1234'. 
Browser console shows: [error message].
Flask terminal shows: [log output].
Test page shows: [result]."

---

Remember: The server needs to be RUNNING for the app to work. 

If you close the terminal, the server stops, and the app stops working.

This is normal for development. Later you can deploy it to run 24/7.
