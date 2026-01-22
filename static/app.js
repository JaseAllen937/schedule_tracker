// Global state
let data = null;
let currentSection = "overview";
let calendarMonth = new Date().getMonth(); // 0-11
let calendarYear = new Date().getFullYear();

// Navigation
function showSection(section) {
  currentSection = section;
  document
    .querySelectorAll(".nav-link")
    .forEach((link) => link.classList.remove("active"));
  event.target.closest(".nav-link").classList.add("active");
  document
    .querySelectorAll(".page-section")
    .forEach((sec) => sec.classList.remove("active"));
  document.getElementById(section + "-section").classList.add("active");
}

// Load data
async function loadData() {
  try {
    console.log("📥 Loading data...");
    const response = await fetch("/api/data");
    if (!response.ok) {
      console.error("❌ Load failed - Response not OK:", response.status);
      if (response.status === 401) {
        window.location.href = "/login";
      }
      return;
    }
    data = await response.json();
    console.log("✅ Data loaded successfully", data);
    renderAll();
  } catch (error) {
    console.error("❌ Error loading data:", error);
    alert("Failed to load data! Check console for details.");
  }
}

// Save data
async function saveData() {
  try {
    console.log("💾 Saving data...", data);
    const response = await fetch("/api/data", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      console.error("❌ Save failed - Response not OK:", response.status);
      const errorText = await response.text();
      console.error("Error details:", errorText);
      alert("Failed to save data! Check console for details.");
      return false;
    }

    const result = await response.json();
    console.log("✅ Data saved successfully", result);
    return true;
  } catch (error) {
    console.error("❌ Error saving data:", error);
    alert("Network error saving data! Check console.");
    return false;
  }
}

// Render all
function renderAll() {
  renderStats();
  renderWarnings();
  renderCategories();
  renderBadHabits();
  renderMilestones();
  renderDeadlines(); // NEW: Render deadline tasks
  renderGoal();
  renderHistory();
  renderMotivation(); // NEW: Render daily motivation
  renderCalendar(); // NEW: Render calendar
}

// Render stats
function renderStats() {
  document.getElementById("stat-streak").textContent = data.currentStreak;
  document.getElementById("stat-longest").textContent = data.longestStreak;
  document.getElementById("stat-total").textContent = data.totalDaysCompleted;

  const lastElem = document.getElementById("stat-last");
  if (data.lastCompletedDate) {
    const date = new Date(data.lastCompletedDate);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    date.setHours(0, 0, 0, 0);

    if (date.getTime() === today.getTime()) {
      lastElem.textContent = "✅ Today";
    } else {
      lastElem.textContent = date.toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
      });
    }
  } else {
    lastElem.textContent = "Never";
  }
}

// Render warnings
function renderWarnings() {
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  let lastDate = null;
  if (data.lastCompletedDate) {
    lastDate = new Date(data.lastCompletedDate);
    lastDate.setHours(0, 0, 0, 0);
  }

  const canComplete = !lastDate || lastDate.getTime() !== today.getTime();

  if (data.currentStreak > 0 && canComplete) {
    document.getElementById("warning-banner").classList.add("show");
    document.getElementById("building-warning").classList.add("show");
  } else {
    document.getElementById("warning-banner").classList.remove("show");
    document.getElementById("building-warning").classList.remove("show");
  }
}

// Render categories
function renderCategories() {
  const container = document.getElementById("categories-container");

  if (!data.categories || data.categories.length === 0) {
    container.innerHTML =
      '<div class="empty-state"><div class="empty-state-icon">📝</div><p>Add your first category to get started</p></div>';
    updateCompleteButton();
    return;
  }

  container.innerHTML = data.categories
    .map(
      (category, catIndex) => `
        <div class="category-card">
            <div class="category-header">
                <div class="category-title">
                    <span class="category-icon">${category.icon}</span>
                    <span>${category.name}</span>
                </div>
                <div style="display: flex; gap: 8px;">
                    <button class="add-task-btn" onclick="openAddTaskModal(${catIndex})">+ Add Task</button>
                    <button class="delete-task-btn" onclick="deleteCategory(${catIndex})">🗑️</button>
                </div>
            </div>
            <ul class="task-list">
                ${
                  category.tasks.length === 0
                    ? '<div class="empty-state"><p style="font-size: 0.9em;">No tasks yet</p></div>'
                    : category.tasks
                        .map(
                          (task, taskIndex) => `
                        <li class="task-item ${
                          task.completed ? "completed" : ""
                        }">
                            <input type="checkbox" 
                                   class="task-checkbox" 
                                   ${task.completed ? "checked" : ""}
                                   onchange="toggleTask(${catIndex}, ${taskIndex})">
                            <span class="task-text">
                                ${task.text}
                                ${
                                  task.recurring
                                    ? '<span style="color: #10b981; margin-left: 8px; font-size: 0.9em;" title="Repeats daily">🔁</span>'
                                    : ""
                                }
                            </span>
                            <button class="delete-task-btn" onclick="deleteTask(${catIndex}, ${taskIndex})">🗑️</button>
                        </li>
                    `,
                        )
                        .join("")
                }
            </ul>
        </div>
    `,
    )
    .join("");

  updateCompleteButton();
}

// Update complete button
function updateCompleteButton() {
  const btn = document.getElementById("complete-btn");
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  let lastDate = null;
  if (data.lastCompletedDate) {
    lastDate = new Date(data.lastCompletedDate);
    lastDate.setHours(0, 0, 0, 0);
  }

  let totalTasks = 0;
  let completedTasks = 0;

  if (data.categories) {
    data.categories.forEach((cat) => {
      cat.tasks.forEach((task) => {
        totalTasks++;
        if (task.completed) completedTasks++;
      });
    });
  }

  const canComplete =
    totalTasks > 0 && (!lastDate || lastDate.getTime() !== today.getTime());

  if (!canComplete) {
    btn.disabled = true;
    if (lastDate && lastDate.getTime() === today.getTime()) {
      btn.textContent = "✅ Already Completed Today";
    } else {
      btn.textContent = "Add Tasks First";
    }
  } else if (completedTasks < totalTasks) {
    btn.disabled = true;
    btn.textContent = `Complete All Tasks (${completedTasks}/${totalTasks})`;
  } else {
    btn.disabled = false;
    btn.textContent = "✅ COMPLETE TODAY";
  }
}

// Toggle task
async function toggleTask(catIndex, taskIndex) {
  try {
    const response = await fetch(`/api/tasks/${catIndex}/${taskIndex}/toggle`, {
      method: "POST",
    });

    const result = await response.json();
    if (response.ok) {
      data = result.data;
      renderCategories();
    }
  } catch (error) {
    console.error("Error toggling task:", error);
  }
}

// Complete day
async function completeDay() {
  try {
    const response = await fetch("/api/complete-day", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });

    const result = await response.json();

    if (response.ok) {
      data = result.data;
      renderAll();
      alert(`🔥 Day completed! Streak: ${result.streak} days!`);
    } else {
      alert(result.error || "Error completing day");
    }
  } catch (error) {
    alert("Network error. Please try again.");
  }
}

// Clear all checkboxes
async function clearAllCheckboxes() {
  if (!confirm("Clear all checkboxes? This will uncheck all tasks.")) return;

  try {
    const response = await fetch("/api/tasks/clear-all", {
      method: "POST",
    });

    const result = await response.json();
    if (response.ok) {
      data = result.data;
      renderCategories();
    }
  } catch (error) {
    console.error("Error clearing checkboxes:", error);
  }
}

// Modal functions
function openModal(modalId) {
  document.getElementById(modalId).classList.add("active");
}

function closeModal(modalId) {
  document.getElementById(modalId).classList.remove("active");
}

// Task modal functions
function openAddTaskModal(catIndex) {
  openModal("task-modal");
  const select = document.getElementById("task-category-select");
  select.innerHTML = data.categories
    .map(
      (cat, i) =>
        `<option value="${i}" ${i === catIndex ? "selected" : ""}>${
          cat.name
        }</option>`,
    )
    .join("");
  document.getElementById("task-input").value = "";
  document.getElementById("task-recurring").checked = true;
  document.getElementById("task-input").focus();
}

async function addTask() {
  const input = document.getElementById("task-input");
  const catIndex = parseInt(
    document.getElementById("task-category-select").value,
  );
  const recurring = document.getElementById("task-recurring").checked;
  const text = input.value.trim();

  if (text) {
    data.categories[catIndex].tasks.push({
      text: text,
      completed: false,
      recurring: recurring,
    });

    await saveData();
    renderCategories();
    closeModal("task-modal");
    input.value = "";
  }
}

async function deleteTask(catIndex, taskIndex) {
  if (confirm("Delete this task?")) {
    data.categories[catIndex].tasks.splice(taskIndex, 1);
    await saveData();
    renderCategories();
  }
}

// Category modal functions
function openAddCategoryModal() {
  openModal("category-modal");
  document.getElementById("category-name").value = "";
  document.getElementById("category-name").focus();
}

async function addCategory() {
  const input = document.getElementById("category-name");
  const name = input.value.trim();

  if (name) {
    if (!data.categories) data.categories = [];

    const icons = ["🎓", "💪", "❤️", "💼", "🎯", "📚", "🏃", "🎨", "💻", "🌟"];
    const icon = icons[data.categories.length % icons.length];

    data.categories.push({
      name: name,
      icon: icon,
      tasks: [],
    });

    await saveData();
    renderCategories();
    closeModal("category-modal");
    input.value = "";
  }
}

async function deleteCategory(index) {
  if (confirm("Delete this entire category and all its tasks?")) {
    data.categories.splice(index, 1);
    await saveData();
    renderCategories();
  }
}

// Bad habits functions
function renderBadHabits() {
  const container = document.getElementById("bad-habits-list");

  if (!data.badHabits || data.badHabits.length === 0) {
    container.innerHTML =
      '<div class="empty-state"><div class="empty-state-icon">🚫</div><p>Track habits you want to break</p></div>';
    return;
  }

  const today = new Date();

  container.innerHTML = data.badHabits
    .map((habit, index) => {
      const cleanSince = new Date(habit.cleanSince);
      const daysClean = Math.floor(
        (today - cleanSince) / (1000 * 60 * 60 * 24),
      );

      const longestStreak = habit.longestStreak || 0;
      const relapseCount = habit.relapses ? habit.relapses.length : 0;

      return `
            <div class="habit-item">
                <div class="habit-header">
                    <div class="habit-name">${habit.name}</div>
                    <button class="delete-task-btn" onclick="deleteHabit(${index})">🗑️</button>
                </div>
                <div class="habit-stats">
                    <div class="habit-stat">
                        <div class="habit-stat-label">Days Clean</div>
                        <div class="habit-stat-value">${daysClean}</div>
                    </div>
                    <div class="habit-stat">
                        <div class="habit-stat-label">Longest Streak</div>
                        <div class="habit-stat-value">${longestStreak}</div>
                    </div>
                    <div class="habit-stat">
                        <div class="habit-stat-label">Total Relapses</div>
                        <div class="habit-stat-value">${relapseCount}</div>
                    </div>
                </div>
                <button class="relapse-btn" onclick="markRelapse(${index})">Mark Relapse</button>
            </div>
        `;
    })
    .join("");
}

async function markRelapse(index) {
  if (!confirm("Record a relapse? This will reset your clean days.")) return;

  try {
    const response = await fetch(`/api/bad-habits/${index}/relapse`, {
      method: "POST",
    });

    const result = await response.json();
    if (response.ok) {
      data = result.data;
      renderBadHabits();
      alert(
        "Relapse recorded. Remember: Progress, not perfection. Start again.",
      );
    } else {
      alert(result.error || "Error recording relapse");
    }
  } catch (error) {
    alert("Network error. Please try again.");
  }
}

function openAddHabitModal() {
  openModal("habit-modal");
  document.getElementById("habit-date").value = new Date()
    .toISOString()
    .split("T")[0];
}

async function addBadHabit() {
  const name = document.getElementById("habit-name").value.trim();
  const date = document.getElementById("habit-date").value;

  if (name && date) {
    if (!data.badHabits) data.badHabits = [];

    data.badHabits.push({
      name: name,
      cleanSince: new Date(date).toISOString(),
      lastRelapseDate: null,
      currentDaysClean: 0,
      longestStreak: 0,
      relapses: [],
    });

    await saveData();
    renderBadHabits();
    closeModal("habit-modal");
    document.getElementById("habit-name").value = "";
  }
}

async function deleteHabit(index) {
  if (confirm("Delete this habit tracker?")) {
    data.badHabits.splice(index, 1);
    await saveData();
    renderBadHabits();
  }
}

// ========== NEW: DEADLINE TASKS FUNCTIONS ==========

function renderDeadlines() {
  const container = document.getElementById("deadlines-container");

  if (!data.milestones) {
    data.milestones = [];
  }

  // Filter for deadline tasks only (type: "deadline")
  const deadlines = data.milestones.filter((m) => m.type === "deadline");

  if (deadlines.length === 0) {
    container.innerHTML =
      '<div class="empty-state"><div class="empty-state-icon">📅</div><p>Add deadline tasks that won\'t affect your streak</p></div>';
    return;
  }

  const today = new Date();
  today.setHours(0, 0, 0, 0);

  // Sort by due date (soonest first)
  deadlines.sort((a, b) => new Date(a.targetDate) - new Date(b.targetDate));

  container.innerHTML = deadlines
    .map((deadline, index) => {
      const actualIndex = data.milestones.findIndex((m) => m === deadline);
      const target = new Date(deadline.targetDate);
      target.setHours(0, 0, 0, 0);
      const daysLeft = Math.ceil((target - today) / (1000 * 60 * 60 * 24));

      // Determine urgency styling
      let urgencyClass = "";
      let urgencyEmoji = "";
      let urgencyText = "";

      if (daysLeft < 0) {
        urgencyClass = "deadline-overdue";
        urgencyEmoji = "🔴";
        urgencyText = `OVERDUE (${Math.abs(daysLeft)} days ago)`;
      } else if (daysLeft === 0) {
        urgencyClass = "deadline-today";
        urgencyEmoji = "🟠";
        urgencyText = "DUE TODAY";
      } else if (daysLeft <= 3) {
        urgencyClass = "deadline-urgent";
        urgencyEmoji = "🟡";
        urgencyText = `${daysLeft} days left (URGENT)`;
      } else if (daysLeft <= 7) {
        urgencyClass = "deadline-soon";
        urgencyEmoji = "🟢";
        urgencyText = `${daysLeft} days left`;
      } else {
        urgencyClass = "deadline-normal";
        urgencyEmoji = "⚪";
        urgencyText = `${daysLeft} days left`;
      }

      const priorityBadge =
        deadline.priority === "high"
          ? "🔺 HIGH"
          : deadline.priority === "medium"
            ? "🔸 MEDIUM"
            : "🔹 LOW";

      return `
      <div class="deadline-item ${urgencyClass}" style="${deadline.completed ? "opacity: 0.5;" : ""}">
        <div class="deadline-header">
          <label style="flex: 1; cursor: pointer; display: flex; align-items: center; gap: 12px;">
            <input type="checkbox" 
                   ${deadline.completed ? "checked" : ""} 
                   onchange="toggleDeadline(${actualIndex})"
                   style="width: 20px; height: 20px; cursor: pointer;">
            <div style="flex: 1;">
              <div class="deadline-title" style="${deadline.completed ? "text-decoration: line-through;" : ""}">
                ${urgencyEmoji} ${deadline.text}
              </div>
              <div class="deadline-meta">
                <span class="deadline-date">${urgencyText}</span>
                ${deadline.category ? `<span class="deadline-category">📁 ${deadline.category}</span>` : ""}
                <span class="deadline-priority">${priorityBadge}</span>
              </div>
            </div>
          </label>
          <button class="icon-btn" onclick="deleteDeadline(${actualIndex})">🗑️</button>
        </div>
      </div>
    `;
    })
    .join("");
}

function openAddDeadlineModal() {
  openModal("deadline-modal");

  // Populate category dropdown
  const select = document.getElementById("deadline-category-select");
  if (data.categories && data.categories.length > 0) {
    select.innerHTML =
      '<option value="">None</option>' +
      data.categories
        .map((cat) => `<option value="${cat.name}">${cat.name}</option>`)
        .join("");
  } else {
    select.innerHTML = '<option value="">None</option>';
  }

  // Set default date to tomorrow
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  document.getElementById("deadline-date").value = tomorrow
    .toISOString()
    .split("T")[0];

  document.getElementById("deadline-input").value = "";
  document.getElementById("deadline-priority").value = "medium";
  document.getElementById("deadline-input").focus();
}

async function addDeadline() {
  const text = document.getElementById("deadline-input").value.trim();
  const date = document.getElementById("deadline-date").value;
  const category = document.getElementById("deadline-category-select").value;
  const priority = document.getElementById("deadline-priority").value;

  if (text && date) {
    if (!data.milestones) data.milestones = [];

    data.milestones.push({
      text: text,
      targetDate: date,
      type: "deadline", // This marks it as a deadline, not a milestone
      category: category || null,
      priority: priority,
      completed: false,
    });

    await saveData();
    renderDeadlines();
    closeModal("deadline-modal");
    document.getElementById("deadline-input").value = "";
  }
}

async function toggleDeadline(index) {
  data.milestones[index].completed = !data.milestones[index].completed;
  await saveData();
  renderDeadlines();
}

async function deleteDeadline(index) {
  if (confirm("Delete this deadline task?")) {
    data.milestones.splice(index, 1);
    await saveData();
    renderDeadlines();
  }
}

// ========== END DEADLINE TASKS FUNCTIONS ==========

// Milestones functions (now filters OUT deadline tasks)
function renderMilestones() {
  const list = document.getElementById("milestones-list");

  if (!data.milestones) {
    data.milestones = [];
  }

  // Filter for regular milestones only (NOT deadline type)
  const milestones = data.milestones.filter((m) => m.type !== "deadline");

  if (milestones.length === 0) {
    list.innerHTML =
      '<div class="empty-state"><div class="empty-state-icon">🎯</div><p>Add your monthly targets</p></div>';
    return;
  }

  const today = new Date();
  today.setHours(0, 0, 0, 0);

  list.innerHTML = milestones
    .map((milestone) => {
      const actualIndex = data.milestones.findIndex((m) => m === milestone);
      const target = new Date(milestone.targetDate);
      target.setHours(0, 0, 0, 0);
      const daysLeft = Math.ceil((target - today) / (1000 * 60 * 60 * 24));

      let dateInfo = "";
      if (daysLeft < 0) {
        dateInfo =
          '<span style="color: #c33; font-weight: 600;">⏰ OVERDUE</span>';
      } else if (daysLeft === 0) {
        dateInfo =
          '<span style="color: #f59e0b; font-weight: 600;">🚨 DUE TODAY</span>';
      } else {
        dateInfo = `<span style="color: #666;">${daysLeft} days left</span>`;
      }

      return `
      <li class="item" style="${
        milestone.completed
          ? "opacity: 0.6; text-decoration: line-through;"
          : ""
      }">
        <label style="flex: 1; cursor: pointer; display: flex; align-items: center; gap: 10px;">
          <input type="checkbox" ${milestone.completed ? "checked" : ""} 
                 onchange="toggleMilestone(${actualIndex})">
          <div>
            <div>${milestone.text}</div>
            <div style="font-size: 0.85em; margin-top: 5px;">${dateInfo}</div>
          </div>
        </label>
        <button class="icon-btn" onclick="deleteMilestone(${actualIndex})">🗑️</button>
      </li>
    `;
    })
    .join("");
}

function openAddMilestoneModal() {
  openModal("milestone-modal");
  const date = new Date();
  date.setDate(date.getDate() + 30);
  document.getElementById("milestone-date").value = date
    .toISOString()
    .split("T")[0];
}

async function addMilestone() {
  const text = document.getElementById("milestone-input").value.trim();
  const date = document.getElementById("milestone-date").value;

  if (text && date) {
    if (!data.milestones) data.milestones = [];

    data.milestones.push({
      text: text,
      targetDate: date,
      type: "milestone", // Regular milestone, not a deadline
      completed: false,
    });

    await saveData();
    renderMilestones();
    closeModal("milestone-modal");
    document.getElementById("milestone-input").value = "";
  }
}

async function toggleMilestone(index) {
  data.milestones[index].completed = !data.milestones[index].completed;
  await saveData();
  renderMilestones();
}

async function deleteMilestone(index) {
  if (confirm("Delete this milestone?")) {
    data.milestones.splice(index, 1);
    await saveData();
    renderMilestones();
  }
}

// ========== NEW: DAILY MOTIVATION FUNCTIONS ==========

function renderMotivation() {
  if (!data.dailyMotivation) {
    return; // Backend will create it on first load
  }

  const verseContainer = document.getElementById("bible-verse-container");
  const quoteContainer = document.getElementById("quote-container");

  const verse = data.dailyMotivation.bibleVerse;
  const quote = data.dailyMotivation.quote;

  if (verse) {
    verseContainer.innerHTML = `
      <div class="motivation-card bible-verse-card">
        <div class="motivation-icon">✝️</div>
        <div class="motivation-text">"${verse.text}"</div>
        <div class="motivation-reference">- ${verse.reference}</div>
      </div>
    `;
  }

  if (quote) {
    quoteContainer.innerHTML = `
      <div class="motivation-card quote-card">
        <div class="motivation-icon">💪</div>
        <div class="motivation-text">"${quote.text}"</div>
        <div class="motivation-reference">- ${quote.author}</div>
      </div>
    `;
  }
}

async function refreshMotivation() {
  const refreshBtn = document.getElementById("refreshBtn");
  const loadingSpinner = document.getElementById("loadingSpinner");
  const loadingText = document.getElementById("loadingText");

  try {
    // Show loading state
    refreshBtn.disabled = true;
    loadingSpinner.classList.add("active");
    loadingText.classList.add("active");

    const response = await fetch("/api/motivation/refresh", {
      method: "POST",
    });

    if (response.ok) {
      const result = await response.json();

      // Update local data with the full response
      if (result.data) {
        // Backend sent full data object
        data = result.data;
      } else {
        // Backend only sent motivation (legacy)
        data.dailyMotivation = result.motivation;
      }

      // Backend already saved - don't save again!
      renderMotivation();
      console.log("Motivation refreshed!");
    }
  } catch (error) {
    console.error("Error refreshing motivation:", error);
    alert("Failed to refresh motivation. Check console for details.");
  } finally {
    // Hide loading state
    refreshBtn.disabled = false;
    loadingSpinner.classList.remove("active");
    loadingText.classList.remove("active");
  }
}

// ========== END DAILY MOTIVATION FUNCTIONS ==========

// ========== NEW: CALENDAR FUNCTIONS ==========

function renderCalendar() {
  const monthNames = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
  ];

  // Update month/year display
  document.getElementById("calendar-month-year").textContent =
    `${monthNames[calendarMonth]} ${calendarYear}`;

  // Get first day of month and number of days
  const firstDay = new Date(calendarYear, calendarMonth, 1).getDay();
  const daysInMonth = new Date(calendarYear, calendarMonth + 1, 0).getDate();

  // Get today for highlighting
  const today = new Date();
  const isCurrentMonth =
    today.getMonth() === calendarMonth && today.getFullYear() === calendarYear;
  const todayDate = today.getDate();

  // Create calendar grid
  const container = document.getElementById("calendar-grid");

  // Remove any existing day cells (keep headers)
  const existingDays = container.querySelectorAll(".calendar-day");
  existingDays.forEach((day) => day.remove());

  // Add empty cells for days before month starts
  for (let i = 0; i < firstDay; i++) {
    const emptyDay = document.createElement("div");
    emptyDay.className = "calendar-day empty";
    container.appendChild(emptyDay);
  }

  // Add days of the month
  for (let day = 1; day <= daysInMonth; day++) {
    const dayCell = document.createElement("div");
    dayCell.className = "calendar-day";

    // Check if this is today
    if (isCurrentMonth && day === todayDate) {
      dayCell.classList.add("today");
    }

    // Create date object for this day
    const dateObj = new Date(calendarYear, calendarMonth, day);
    const dateStr = dateObj.toISOString().split("T")[0];

    // Check for completed day
    const isCompleted =
      data.history &&
      data.history.some((entry) => {
        const entryDate = new Date(entry.date);
        return (
          entryDate.getFullYear() === calendarYear &&
          entryDate.getMonth() === calendarMonth &&
          entryDate.getDate() === day
        );
      });

    // Check for deadlines
    const deadlines = data.milestones
      ? data.milestones.filter(
          (m) =>
            m.type === "deadline" && m.targetDate === dateStr && !m.completed,
        )
      : [];

    // Check for milestones
    const milestones = data.milestones
      ? data.milestones.filter(
          (m) =>
            m.type !== "deadline" && m.targetDate === dateStr && !m.completed,
        )
      : [];

    // Build day content
    dayCell.innerHTML = `
      <div class="calendar-day-number">${day}</div>
      <div class="calendar-day-indicators">
        ${isCompleted ? '<div class="calendar-indicator completed-indicator" title="Day completed">✓</div>' : ""}
        ${deadlines.length > 0 ? `<div class="calendar-indicator deadline-indicator" title="${deadlines.length} deadline(s)">${deadlines.length}</div>` : ""}
        ${milestones.length > 0 ? `<div class="calendar-indicator milestone-indicator" title="${milestones.length} milestone(s)">⭐</div>` : ""}
      </div>
    `;

    // Make clickable if there's any data for this day
    if (isCompleted || deadlines.length > 0 || milestones.length > 0) {
      dayCell.classList.add("has-data");
      dayCell.onclick = () =>
        showDayDetails(day, dateStr, isCompleted, deadlines, milestones);
    }

    container.appendChild(dayCell);
  }
}

function changeMonth(delta) {
  calendarMonth += delta;

  if (calendarMonth > 11) {
    calendarMonth = 0;
    calendarYear++;
  } else if (calendarMonth < 0) {
    calendarMonth = 11;
    calendarYear--;
  }

  renderCalendar();
}

function showDayDetails(day, dateStr, isCompleted, deadlines, milestones) {
  const monthNames = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
  ];

  // Update modal title
  document.getElementById("calendar-modal-title").textContent =
    `${monthNames[calendarMonth]} ${day}, ${calendarYear}`;

  // Build content
  let content = "";

  // Show completion status
  if (isCompleted) {
    const historyEntry = data.history.find((entry) => {
      const entryDate = new Date(entry.date);
      return (
        entryDate.getFullYear() === calendarYear &&
        entryDate.getMonth() === calendarMonth &&
        entryDate.getDate() === day
      );
    });

    content += `
      <div class="day-detail-section completed-section">
        <h4>✅ Day Completed</h4>
        <p>Streak: ${historyEntry ? historyEntry.streak : "?"} days</p>
      </div>
    `;
  }

  // Show deadlines
  if (deadlines.length > 0) {
    content += `
      <div class="day-detail-section deadline-section">
        <h4>📅 Deadlines Due (${deadlines.length})</h4>
        <ul class="day-detail-list">
          ${deadlines
            .map(
              (d) => `
            <li>
              <strong>${d.text}</strong>
              ${d.category ? `<br><small>📁 ${d.category}</small>` : ""}
              ${d.priority ? `<br><small>Priority: ${d.priority.toUpperCase()}</small>` : ""}
            </li>
          `,
            )
            .join("")}
        </ul>
      </div>
    `;
  }

  // Show milestones
  if (milestones.length > 0) {
    content += `
      <div class="day-detail-section milestone-section">
        <h4>⭐ Milestones (${milestones.length})</h4>
        <ul class="day-detail-list">
          ${milestones.map((m) => `<li><strong>${m.text}</strong></li>`).join("")}
        </ul>
      </div>
    `;
  }

  if (!content) {
    content =
      '<p style="text-align: center; color: #9ca3af; padding: 20px;">No events on this day</p>';
  }

  document.getElementById("calendar-modal-content").innerHTML = content;
  openModal("calendar-day-modal");
}

// ========== END CALENDAR FUNCTIONS ==========

// Goal functions
function renderGoal() {
  const container = document.getElementById("goal-display");

  if (data.endGoal) {
    container.innerHTML = `
      <div style="background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); 
                  color: white; padding: 30px; border-radius: 10px; text-align: center;">
        <div style="font-size: 1.3em; font-weight: 600; line-height: 1.5;">
          "${data.endGoal}"
        </div>
      </div>
    `;
  } else {
    container.innerHTML =
      '<div class="empty-state"><div class="empty-state-icon">🎯</div><p>Set your ultimate goal</p></div>';
  }
}

function openEditGoalModal() {
  openModal("goal-modal");
  document.getElementById("goal-input").value = data.endGoal || "";
  document.getElementById("goal-input").focus();
}

async function saveGoal() {
  const input = document.getElementById("goal-input");
  data.endGoal = input.value.trim();
  await saveData();
  renderGoal();
  closeModal("goal-modal");
}

// History functions
function renderHistory() {
  const container = document.getElementById("history-display");

  if (!data.history || data.history.length === 0) {
    container.innerHTML =
      '<div class="empty-state"><p>Complete your first day to see progress!</p></div>';
    document.getElementById("progress-bar").style.width = "0%";
    return;
  }

  const last7 = data.history.slice(-7);
  const rate = Math.round((last7.length / 7) * 100);

  document.getElementById("progress-bar").style.width = rate + "%";

  const recent = data.history.slice(-10).reverse();
  container.innerHTML = `
    <p style="margin-bottom: 15px; color: #666;">Last 10 completions (${rate}% completion rate last 7 days)</p>
    ${recent
      .map((entry) => {
        const date = new Date(entry.date);
        return `
          <div style="display: flex; justify-content: space-between; padding: 12px; 
                      background: #f8f9fa; margin-bottom: 5px; border-radius: 6px;">
            <span>${date.toLocaleDateString("en-US", {
              month: "short",
              day: "numeric",
              year: "numeric",
            })}</span>
            <span style="font-weight: 600; color: #1e3c72;">🔥 Streak: ${
              entry.streak
            } days</span>
          </div>
        `;
      })
      .join("")}
  `;
}

// Logout
async function logout() {
  if (confirm("Logout?")) {
    await fetch("/api/logout", { method: "POST" });
    window.location.href = "/";
  }
}

// Event listeners
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    document
      .querySelectorAll(".modal")
      .forEach((m) => m.classList.remove("active"));
  }
});

// Initialize
loadData();

// Mobile sidebar toggle functions
function toggleSidebar() {
  const sidebar = document.getElementById("sidebar");
  const overlay = document.querySelector(".sidebar-overlay");
  sidebar.classList.toggle("open");
  overlay.classList.toggle("show");
}

function closeSidebar() {
  const sidebar = document.getElementById("sidebar");
  const overlay = document.querySelector(".sidebar-overlay");
  sidebar.classList.remove("open");
  overlay.classList.remove("show");
}

// Auto-close sidebar when clicking nav links on mobile
document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll(".nav-link").forEach((link) => {
    link.addEventListener("click", () => {
      if (window.innerWidth <= 768) {
        closeSidebar();
      }
    });
  });
});
