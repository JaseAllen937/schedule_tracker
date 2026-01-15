# 🔌 PORT CONFIGURATION GUIDE

**Default Port: 5001**

The Momentum Tracker runs on port 5001 by default.

---

## 🌐 How to Access the App

**Main App:**
```
http://localhost:5001
```

**Test Page:**
```
http://localhost:5001/test-page
```

---

## 🔧 How to Change the Port

If port 5001 is also taken, you can change it to any port you want.

### **Step 1: Edit app.py**

Open `app.py` and find the last line:

```python
if __name__ == '__main__':
    app.run(debug=True, port=5001)  # Change this number
```

Change `5001` to whatever port you want:

```python
if __name__ == '__main__':
    app.run(debug=True, port=8080)  # Or 3000, 8000, etc.
```

**Common alternative ports:**
- 8080 (common for web apps)
- 8000 (common for development)
- 3000 (React default)
- 8888 (Jupyter default)
- Any number from 1024-65535

### **Step 2: Save and Restart**

1. Save `app.py`
2. Stop the server (Ctrl+C in terminal)
3. Start it again: `python app.py`
4. Server will show new port:
   ```
   * Running on http://127.0.0.1:8080
   ```

### **Step 3: Update Browser**

Open browser to the NEW port:
```
http://localhost:8080
```

**That's it!** The HTML automatically uses whatever port Flask is running on.

---

## 🔍 Finding What's Using a Port

### **Windows:**
```bash
netstat -ano | findstr :5001
```

### **Mac/Linux:**
```bash
lsof -i :5001
```

### **Kill Process on Port:**

**Windows:**
```bash
# Find PID from netstat command above, then:
taskkill /PID <PID> /F
```

**Mac/Linux:**
```bash
# Find PID from lsof command above, then:
kill -9 <PID>
```

---

## ❓ Why Port 5001 Instead of 5000?

**Flask's default is 5000**, but many things use that port:

- Airplay Receiver (Mac)
- ControlCenter (Mac)
- Some development servers
- Docker containers

**Port 5001 is usually free**, but if it's not, just pick another.

---

## 💡 Pro Tips

### **Use a High Port Number**
Ports below 1024 require admin privileges. Use 5000+ to avoid issues.

### **Avoid Common Ports**
These are often taken:
- 3000 (React, Node)
- 5000 (Flask default, Airplay)
- 8000 (Django, Python HTTP server)
- 8080 (Tomcat, proxies)
- 8888 (Jupyter)

### **Pick a Memorable Number**
- 6666 (easy to remember)
- 7777 (also easy)
- 9999 (very memorable)
- Your birthday (e.g., 1215)

### **The HTML Doesn't Need to Know**
Flask serves the HTML, so fetch requests use relative URLs like `/api/login`.

This means:
- **NO hardcoded ports in HTML** ✅
- **Change port = change one line** ✅
- **No HTML edits needed** ✅

---

## 🚨 Common Port Issues

### **"Address already in use"**

**Problem:** Something is already on that port.

**Solution:**
1. Kill the process using the port (see above)
2. Or change to a different port in `app.py`

### **"Permission denied"**

**Problem:** Port requires admin rights (usually < 1024).

**Solution:** Use a port > 1024 (like 5001, 8080, etc.)

### **Can't connect after changing port**

**Problem:** Browser is still trying old port.

**Solution:**
1. Check Flask terminal - what port does it say?
2. Update browser URL to match
3. Clear browser cache if needed

---

## 🎯 Quick Reference

**Current Port:** 5001

**To Access:**
```
http://localhost:5001
```

**To Change:**
Edit line 207 in `app.py`:
```python
app.run(debug=True, port=XXXX)
```

**To Check What's Running:**
```bash
# Windows
netstat -ano | findstr :5001

# Mac/Linux  
lsof -i :5001
```

**To Test:**
```bash
curl http://localhost:5001/test
```

Should return:
```json
{"message":"Flask server is running!","status":"ok"}
```

---

## 📝 Notes

- Port changes take effect when you restart the server
- No need to edit HTML files - they use relative URLs
- Multiple Flask apps can run on different ports simultaneously
- Bookmark your port so you don't forget it

---

**TL;DR:** App runs on port 5001 now. If that's taken, change the number in `app.py` line 207 and restart.
