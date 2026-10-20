(() => {
  "use strict";

  const STORAGE_KEY = "ai-empire.tasks.v1";
  const form = document.querySelector("#task-form");
  const input = document.querySelector("#task-input");
  const list = document.querySelector("#task-list");
  const count = document.querySelector("#task-count");
  const clearButton = document.querySelector("#clear-completed");

  function loadTasks() {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      const parsed = saved ? JSON.parse(saved) : [];
      return Array.isArray(parsed)
        ? parsed.filter((task) => task && typeof task.title === "string" && typeof task.done === "boolean")
        : [];
    } catch {
      return [];
    }
  }

  let tasks = loadTasks();

  function saveTasks() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(tasks));
    } catch {
      // The task board still works for this page session if storage is unavailable.
    }
  }

  function render() {
    count.textContent = String(tasks.length);
    list.replaceChildren();

    if (tasks.length === 0) {
      const empty = document.createElement("div");
      empty.className = "empty";
      empty.textContent = "Your queue is empty. Add a task above to begin.";
      list.append(empty);
      return;
    }

    for (const task of tasks) {
      const row = document.createElement("div");
      row.className = "task-row";

      const checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.checked = task.done;
      checkbox.setAttribute("aria-label", "Mark task complete");
      checkbox.addEventListener("change", () => {
        task.done = checkbox.checked;
        saveTasks();
        render();
      });

      const title = document.createElement("div");
      title.className = "task-title" + (task.done ? " done" : "");
      title.textContent = task.title;

      const state = document.createElement("span");
      state.className = "task-state" + (task.done ? " complete" : "");
      state.textContent = task.done ? "Done" : "Queued";

      row.append(checkbox, title, state);
      list.append(row);
    }
  }

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const title = input.value.trim();
    if (!title) return;

    tasks.unshift({
      id: typeof crypto !== "undefined" && crypto.randomUUID ? crypto.randomUUID() : String(Date.now()),
      title,
      done: false,
      createdAt: new Date().toISOString()
    });

    saveTasks();
    render();
    input.value = "";
    input.focus();
  });

  clearButton.addEventListener("click", () => {
    tasks = tasks.filter((task) => !task.done);
    saveTasks();
    render();
  });

  render();
})();