const yearEl = document.getElementById("year");
const themeToggle = document.getElementById("theme-toggle");

if (yearEl) {
  yearEl.textContent = new Date().getFullYear();
}

const setTheme = (theme) => {
  const lightMode = theme === "light";
  document.body.classList.toggle("light", lightMode);
  if (themeToggle) {
    themeToggle.textContent = lightMode ? "Dark" : "Light";
  }
  localStorage.setItem("theme", theme);
};

const savedTheme = localStorage.getItem("theme");
const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
setTheme(savedTheme || (prefersDark ? "dark" : "light"));

if (themeToggle) {
  themeToggle.addEventListener("click", () => {
    const current = document.body.classList.contains("light") ? "light" : "dark";
    setTheme(current === "light" ? "dark" : "light");
  });
}

// Safe JSON fetch helper: throws a clear error when response isn't JSON.
window.safeFetch = async function (input, init) {
  const res = await fetch(input, init);
  const ct = res.headers.get("content-type") || "";
  if (ct.includes("application/json")) {
    const data = await res.json();
    if (!res.ok) throw new Error(data && data.error ? data.error : JSON.stringify(data));
    return data;
  }
  const text = await res.text();
  throw new Error(`Non-JSON response (${res.status}): ${text}`);
};

