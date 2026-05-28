const STORAGE_KEYS = {
  user: "symptocare.user",
  token: "symptocare.token",
};

const STORAGE = sessionStorage;

const API_BASE = window.APP_CONFIG?.API_BASE || "http://127.0.0.1:8000";

const saveSession = (user, token) => {
  STORAGE.setItem(STORAGE_KEYS.user, JSON.stringify(user));
  STORAGE.setItem(STORAGE_KEYS.token, token);
};

const clearSession = () => {
  STORAGE.removeItem(STORAGE_KEYS.user);
  STORAGE.removeItem(STORAGE_KEYS.token);
};

const requestJson = async (url, options = {}) => {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail || "Request failed.");
  }
  return response.json();
};

const statusEl = document.getElementById("authStatus");

const setStatus = (message = "", tone = "") => {
  if (!statusEl) return;
  statusEl.textContent = message;
  statusEl.classList.remove("is-error", "is-success");
  if (tone === "error") statusEl.classList.add("is-error");
  if (tone === "success") statusEl.classList.add("is-success");
};

const setLoading = (button, isLoading, label) => {
  if (!button) return;
  button.disabled = isLoading;
  button.textContent = isLoading ? label : button.dataset.label;
};

const signInForm = document.getElementById("signInForm");
const signUpForm = document.getElementById("signUpForm");

if (signUpForm) {
  signUpForm.addEventListener("submit", (event) => {
    event.preventDefault();
    setStatus("");
    const formData = new FormData(event.target);
    const password = formData.get("password");
    const confirm = formData.get("confirm");
    if (password !== confirm) {
      setStatus("Passwords do not match.", "error");
      return;
    }

    const email = String(formData.get("email") || "").trim();
    const name = String(formData.get("name") || "").trim();

    const submitBtn = signUpForm.querySelector("button[type='submit']");
    if (submitBtn) {
      submitBtn.dataset.label = submitBtn.textContent;
      setLoading(submitBtn, true, "Creating...");
    }

    (async () => {
      try {
        await requestJson(`${API_BASE}/auth/signup`, {
          method: "POST",
          body: JSON.stringify({ email, password }),
        });

        const session = await requestJson(`${API_BASE}/auth/login`, {
          method: "POST",
          body: JSON.stringify({ email, password }),
        });

        const token = session.access_token;
        const user = { email, name };
        if (!token) {
          throw new Error("Login failed. Please try again.");
        }

        saveSession(user, token);

        await requestJson(`${API_BASE}/profile`, {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ full_name: name || null }),
        });

        setStatus("Account created. Redirecting...", "success");
        window.location.href = "app.html";
      } catch (error) {
        clearSession();
        setStatus(error.message || "Unable to sign up.", "error");
      } finally {
        if (submitBtn) setLoading(submitBtn, false);
      }
    })();
  });
}

if (signInForm) {
  signInForm.addEventListener("submit", (event) => {
    event.preventDefault();
    setStatus("");
    const formData = new FormData(event.target);
    const email = String(formData.get("email") || "").trim();
    const password = formData.get("password");

    const submitBtn = signInForm.querySelector("button[type='submit']");
    if (submitBtn) {
      submitBtn.dataset.label = submitBtn.textContent;
      setLoading(submitBtn, true, "Signing in...");
    }

    (async () => {
      try {
        const session = await requestJson(`${API_BASE}/auth/login`, {
          method: "POST",
          body: JSON.stringify({ email, password }),
        });

        const token = session.access_token;
        const user = { email };
        if (!token) {
          throw new Error("Login failed. Please try again.");
        }

        saveSession(user, token);
        setStatus("Signed in. Redirecting...", "success");
        window.location.href = "app.html";
      } catch (error) {
        clearSession();
        setStatus(error.message || "Unable to sign in.", "error");
      } finally {
        if (submitBtn) setLoading(submitBtn, false);
      }
    })();
  });
}
