# 🔥 Momentum Tracker - Full Stack Edition

**Multi-user habit tracker with Python Flask backend**

Build good habits. Break bad habits. Track everything.

---

## 🚀 What's New in This Version

### **Python Backend**
- Real Flask web server (not just localStorage)
- Multi-user support with 4-digit passcodes
- Persistent data storage in JSON file
- Proper session management

### **Habit Breaking System**
- Track sobriety from drugs, porn, alcohol, etc.
- Days clean counter (auto-calculates daily)
- Longest streak tracking
- Relapse recording with history
- Accountability features

### **Professional Design**
- Clean sidebar navigation
- Organized sections (Overview, Build Habits, Break Habits, Goals)
- Better information architecture
- Mobile-responsive layout

---

## ⚡ Quick Start (3 minutes)

### **1. Install Python Dependencies**
```bash
pip install -r requirements.txt
```

### **2. Run the Server**
```bash
python app.py
```

### **3. Open Your Browser**
```
http://localhost:5001
```

**That's it.** You're running.

---

## 📱 How to Use

### **First Time Setup**

1. **Register Account**
   - Choose a username (lowercase, no spaces)
   - Create a 4-digit passcode
   - **REMEMBER THIS.** No password recovery yet.

2. **Add Daily Tasks**
   - Go to "Build Habits" section
   - Click "+ Add Task"
   - Example: "30 min: Build one feature"
   - Add 3-5 daily non-negotiables

3. **Track Bad Habits (Optional)**
   - Go to "Break Habits" section
   - Click "+ Track New Habit"
   - Enter habit name (e.g., "Pornography", "Drugs")
   - Set your clean-since date
   - Days clean auto-calculates

4. **Set Goals**
   - Go to "Goals" section
   - Add 30-day milestones
   - Set your ultimate goal

---

## 🎯 Daily Usage

### **Every Morning (30 seconds)**
1. Login
2. Check your streaks
3. Review daily tasks
4. Close the app

### **Every Evening (1 minute)**
1. Login
2. Go to "Build Habits"
3. Did you complete all tasks?
   - **YES:** Click "Complete Today"
   - **NO:** Go do them first

### **If You Relapse (Bad Habit)**
1. Go to "Break Habits"
2. Click "Mark Relapse" on the habit
3. Counter resets to Day 0
4. Start again tomorrow

**No judgment. Just data.**

---

## 🔥 Key Features

### **Building Good Habits**
- Daily task tracker
- Streak counter (breaks if you miss a day)
- Longest streak record
- Warning banner when streak is in danger
- Completion history

### **Breaking Bad Habits**
- Days clean counter
- Auto-calculates from clean-since date
- Longest streak tracking
- Relapse history
- Multiple habits at once

### **Goals & Milestones**
- 30-day milestones with deadlines
- Overdue tracking
- Ultimate goal display
- Checkbox completion

### **Analytics**
- 7-day completion rate
- Last 10 completions
- Progress bar visualization
- All-time stats

---

## 🔒 User Management

### **Multi-User System**
- Each user has separate data
- Simple 4-digit passcode
- No email required
- No password recovery (keep it simple)

### **Data Storage**
- All data in `users_data.json`
- One file, all users
- Backup this file = backup everything

### **Session Management**
- Auto-login on return
- Logout button in sidebar
- Session expires on browser close

---

## 📂 File Structure

```
momentum-tracker/
│
├── app.py                  # Flask backend
├── requirements.txt        # Python dependencies
├── users_data.json        # All user data (auto-created)
│
└── templates/
    ├── login.html         # Login/register page
    └── dashboard.html     # Main app
```

---

## 🛡️ Data Security

### **Passcodes**
- Stored in plain text (it's a 4-digit code, not a bank)
- If someone has your JSON file, they have your data
- Keep `users_data.json` private

### **Privacy**
- No cloud sync (by design)
- No external API calls
- All data local to your machine
- No tracking, no analytics

### **Backup**
```bash
# Manual backup
cp users_data.json users_data_backup_$(date +%Y%m%d).json
```

---

## 🎨 Customization

### **Change Colors**
Edit the CSS in `dashboard.html`:
- Main blue: `#1e3c72` and `#2a5298`
- Green (complete): `#10b981`
- Red (bad habits): `#c33` and `#ff6b6b`

### **Add More Sections**
1. Add nav item in sidebar
2. Create new page-section div
3. Add corresponding JavaScript functions

### **Change Port**
In `app.py`:
```python
app.run(debug=True, port=5001)  # Change 5001 to your port
```

---

## ⚙️ Advanced Features

### **Export User Data**
```python
# In Python shell
import json
with open('users_data.json', 'r') as f:
    data = json.load(f)
    
# Get specific user
user_data = data['your_username']
print(json.dumps(user_data, indent=2))
```

### **Reset a User**
Delete their entry in `users_data.json` (they can re-register)

### **See All Users**
```python
import json
with open('users_data.json', 'r') as f:
    users = json.load(f)
    print(list(users.keys()))
```

---

## 🚨 Troubleshooting

### **"Address already in use"**
Port 5001 is taken. Either:
- Kill the existing process
- Change the port in `app.py`

### **"Module not found: Flask"**
```bash
pip install Flask
```

### **Changes not showing up**
- Hard refresh: `Ctrl+Shift+R` (Windows) or `Cmd+Shift+R` (Mac)
- Clear browser cache
- Restart Flask server

### **Lost passcode**
Edit `users_data.json` and change the passcode manually:
```json
{
  "username": {
    "passcode": "1234",  // Change this
    ...
  }
}
```

---

## 💡 Pro Tips

### **For Solo Use**
- Just use one account
- Pin the URL as a bookmark

### **For Couples/Roommates**
- Each person creates an account
- Compare streaks = competition
- Accountability partner system

### **For Teams**
- Everyone on same machine can have account
- Morning standup: check everyone's streaks
- Friendly competition

### **Breaking Bad Habits**
- Be honest about relapses
- Track multiple habits separately
- Progress > perfection
- Days clean is just data, not judgment

---

## 🔮 Roadmap (Future Features)

**What's NOT in this version (yet):**
- [ ] Password recovery
- [ ] Email notifications
- [ ] Mobile app
- [ ] Cloud sync
- [ ] API export
- [ ] Charts/graphs
- [ ] Habit notes/journal
- [ ] Sharing/social features

**Why not?**
You wanted it fast and functional. These can come later.

---

## 🎯 Philosophy

### **Why This Works**

1. **Accountability Through Data**
   - Numbers don't lie
   - Streaks hurt to lose
   - Visible progress = motivation

2. **Multi-Faceted Tracking**
   - Build good (daily tasks)
   - Break bad (sobriety)
   - Goals (direction)

3. **Simple > Perfect**
   - 4-digit passcode (not 12-char password)
   - JSON file (not SQL database)
   - Local (not cloud)

4. **Private & Honest**
   - Your data stays with you
   - No social pressure
   - Real accountability

---

## 📞 Support

**Issues?**
1. Check Troubleshooting section
2. Read the code (it's simple Python/HTML)
3. Debug yourself (you're learning!)

**Feature Requests?**
Fork it and build it. That's the point.

---

## 📜 License

Do whatever you want with this. It's yours.

Build discipline. Break bad habits. Make money.

**Now run it.** ⏰
