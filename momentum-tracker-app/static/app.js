// Global state
let data = null;
let currentSection = "overview";

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
    const response = await fetch("/api/data");
    if (!response.ok) {
      window.location.href = "/";
      return;
    }
    data = await response.json();
    renderAll();
  } catch (error) {
    console.error("Error loading data:", error);
  }
}

// Save data
async function saveData() {
  try {
    await fetch("/api/data", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
  } catch (error) {
    console.error("Error saving data:", error);
  }
}

// Render all
function renderAll() {
  renderStats();
  renderWarnings();
  renderCategories();
  renderBadHabits();
  renderMilestones();
  renderGoal();
  renderHistory();
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
                            <span class="task-text">${task.text}</span>
                            <button class="delete-task-btn" onclick="deleteTask(${catIndex}, ${taskIndex})">🗑️</button>
                        </li>
                    `
                        )
                        .join("")
                }
            </ul>
        </div>
    `
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

// Modal functions
function openModal(modalId) {
  document.getElementById(modalId).classList.add("active");
}

function closeModal(modalId) {
  document.getElementById(modalId).classList.remove("active");
}

function openAddTaskModal(catIndex) {
  const select = document.getElementById("task-category-select");
  select.innerHTML = data.categories
    .map(
      (cat, idx) =>
        `<option value="${idx}" ${idx === catIndex ? "selected" : ""}>${
          cat.icon
        } ${cat.name}</option>`
    )
    .join("");

  openModal("task-modal");
  document.getElementById("task-input").focus();
}

function openAddCategoryModal() {
  openModal("category-modal");
  document.getElementById("category-name").focus();
}

// Add task
async function addTask() {
  const catIndex = parseInt(
    document.getElementById("task-category-select").value
  );
  const taskText = document.getElementById("task-input").value.trim();

  if (!taskText) return;

  try {
    const response = await fetch("/api/tasks", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ categoryIndex: catIndex, task: taskText }),
    });

    const result = await response.json();
    if (response.ok) {
      data = result.data;
      renderCategories();
      closeModal("task-modal");
      document.getElementById("task-input").value = "";
    }
  } catch (error) {
    console.error("Error adding task:", error);
  }
}

// Add category
async function addCategory() {
  const name = document.getElementById("category-name").value.trim();

  if (!name) {
    alert("Please enter a category name");
    return;
  }

  // Simple icon assignment
  let icon = "📝"; // default
  const lowerName = name.toLowerCase();

  if (lowerName.includes("school") || lowerName.includes("study")) icon = "🎓";
  else if (
    lowerName.includes("fitness") ||
    lowerName.includes("gym") ||
    lowerName.includes("workout")
  )
    icon = "💪";
  else if (lowerName.includes("social") || lowerName.includes("friends"))
    icon = "👥";
  else if (lowerName.includes("health") || lowerName.includes("medical"))
    icon = "🏥";
  else if (lowerName.includes("finance") || lowerName.includes("money"))
    icon = "💰";
  else if (lowerName.includes("family")) icon = "👨‍👩‍👧‍👦";
  else if (lowerName.includes("work") || lowerName.includes("career"))
    icon = "💼";

  console.log("Adding category:", name, icon); // Debug log

  try {
    const response = await fetch("/api/categories", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: name, icon: icon }),
    });

    console.log("Response:", response.status); // Debug log

    const result = await response.json();
    console.log("Result:", result); // Debug log

    if (response.ok) {
      data = result.data;
      renderCategories();
      closeModal("category-modal");
      document.getElementById("category-name").value = "";
    } else {
      alert("Error: " + (result.error || "Failed to add category"));
    }
  } catch (error) {
    console.error("Error adding category:", error);
    alert("Network error: " + error.message);
  }
}

// Delete category
async function deleteCategory(catIndex) {
  if (!confirm("Delete this category and all its tasks?")) return;

  try {
    const response = await fetch(`/api/categories/${catIndex}`, {
      method: "DELETE",
    });

    const result = await response.json();
    if (response.ok) {
      data = result.data;
      renderCategories();
    }
  } catch (error) {
    console.error("Error deleting category:", error);
  }
}

// Bad Habits functions
function renderBadHabits() {
  const container = document.getElementById("bad-habits-list");

  if (!data.badHabits || data.badHabits.length === 0) {
    container.innerHTML =
      '<div class="empty-state"><div class="empty-state-icon">🚫</div><p>Start tracking habits you want to break</p></div>';
    return;
  }

  const today = new Date();

  container.innerHTML = data.badHabits
    .map((habit, index) => {
      const cleanSince = new Date(habit.cleanSince);
      const daysClean = Math.floor(
        (today - cleanSince) / (1000 * 60 * 60 * 24)
      );
      data.badHabits[index].currentDaysClean = daysClean;

      return `
            <div class="habit-item">
                <div class="habit-header">
                    <div class="habit-name">${habit.name}</div>
                    <div class="item-actions">
                        <button class="relapse-btn" onclick="markRelapse(${index})">Mark Relapse</button>
                        <button class="icon-btn" onclick="deleteHabit(${index})">🗑️</button>
                    </div>
                </div>
                <div class="habit-stats">
                    <div class="habit-stat">
                        <div class="habit-stat-label">Days Clean</div>
                        <div class="habit-stat-value">${daysClean}</div>
                    </div>
                    <div class="habit-stat">
                        <div class="habit-stat-label">Longest Streak</div>
                        <div class="habit-stat-value">${
                          habit.longestStreak || 0
                        }</div>
                    </div>
                    <div class="habit-stat">
                        <div class="habit-stat-label">Total Relapses</div>
                        <div class="habit-stat-value">${
                          habit.relapses ? habit.relapses.length : 0
                        }</div>
                    </div>
                </div>
            </div>
        `;
    })
    .join("");
}

async function markRelapse(index) {
  if (!confirm("Mark a relapse? This will reset your clean days counter."))
    return;

  try {
    const response = await fetch("/api/bad-habits/relapse", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ habitIndex: index }),
    });

    const result = await response.json();
    if (response.ok) {
      data = result.data;
      renderBadHabits();
      alert(
        "Relapse recorded. Remember: Progress, not perfection. Start again."
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

// Milestones functions
function renderMilestones() {
  const list = document.getElementById("milestones-list");

  if (!data.milestones || data.milestones.length === 0) {
    list.innerHTML =
      '<div class="empty-state"><div class="empty-state-icon">🎯</div><p>Add your monthly targets</p></div>';
    return;
  }

  const today = new Date();
  today.setHours(0, 0, 0, 0);

  list.innerHTML = data.milestones
    .map((milestone, index) => {
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
                    <input type="checkbox" ${
                      milestone.completed ? "checked" : ""
                    } 
                           onchange="toggleMilestone(${index})">
                    <div>
                        <div>${milestone.text}</div>
                        <div style="font-size: 0.85em; margin-top: 5px;">${dateInfo}</div>
                    </div>
                </label>
                <button class="icon-btn" onclick="deleteMilestone(${index})">🗑️</button>
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
