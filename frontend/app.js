const signOutBtn = document.getElementById("signOutBtn");
const navButtons = document.querySelectorAll(".nav-btn");
const views = {
  checker: document.getElementById("checkerView"),
  history: document.getElementById("historyView"),
  profile: document.getElementById("profileView"),
};

const symptomSearch = document.getElementById("symptomSearch");
const symptomList = document.getElementById("symptomList");
const selectedCount = document.getElementById("selectedCount");
const checkBtn = document.getElementById("checkBtn");
const resultCard = document.getElementById("resultCard");
const resultTitle = document.getElementById("resultTitle");
const resultDesc = document.getElementById("resultDesc");
const historyList = document.getElementById("historyList");
const clearHistoryBtn = document.getElementById("clearHistoryBtn");

const profileName = document.getElementById("profileName");
const profileEmail = document.getElementById("profileEmail");
const profileDate = document.getElementById("profileDate");
const userChip = document.getElementById("userChip");
const appStatus = document.getElementById("appStatus");

const STORAGE_KEYS = {
  user: "symptocare.user",
  token: "symptocare.token",
};

const STORAGE = sessionStorage;

const API_BASE = window.APP_CONFIG?.API_BASE || "http://127.0.0.1:8000";
let symptomData = [];
let lastPrediction = null;
let selectedSet = new Set();

const loadUser = () => {
  const raw = STORAGE.getItem(STORAGE_KEYS.user);
  return raw ? JSON.parse(raw) : null;
};

const loadToken = () => STORAGE.getItem(STORAGE_KEYS.token);

const clearSession = () => {
  STORAGE.removeItem(STORAGE_KEYS.user);
  STORAGE.removeItem(STORAGE_KEYS.token);
};

const setAppStatus = (message, tone = "") => {
  if (!appStatus) return;
  appStatus.textContent = message;
  appStatus.classList.toggle("is-error", tone === "error");
};

const setButtonLoading = (button, isLoading, label) => {
  if (!button) return;
  button.disabled = isLoading;
  button.textContent = isLoading ? label : button.dataset.label;
};

const handleAuthFailure = () => {
  clearSession();
  window.location.replace("login.html");
};

const requestJson = async (path, options = {}) => {
  const response = await fetch(`${API_BASE}${path}`, options);
  if (response.status === 401) {
    handleAuthFailure();
    throw new Error("Session expired. Please sign in again.");
  }
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || "Request failed.");
  }
  return response.json();
};

const showView = (key) => {
  Object.entries(views).forEach(([viewKey, node]) => {
    node.classList.toggle("is-active", viewKey === key);
  });
  navButtons.forEach((btn) => {
    btn.classList.toggle("is-active", btn.dataset.view === key);
  });
};

const renderProfile = (user, profile) => {
  if (!user) {
    profileName.textContent = "--";
    profileEmail.textContent = "--";
    profileDate.textContent = "--";
    return;
  }
  const name = profile?.full_name || user.name || "Anonymous";
  const created = profile?.created_at
    ? new Date(profile.created_at).toLocaleDateString()
    : "--";
  profileName.textContent = name;
  profileEmail.textContent = user.email || "--";
  profileDate.textContent = created === "--" ? "Joined --" : `Joined ${created}`;
  if (userChip) {
    userChip.textContent = user.email || "Signed in";
  }
};

const saveUser = (user) => {
  STORAGE.setItem(STORAGE_KEYS.user, JSON.stringify(user));
};

// Profile editing
const editProfileBtn = document.getElementById("editProfileBtn");
const profileEditForm = document.getElementById("profileEditForm");
const editName = document.getElementById("editName");
const editEmail = document.getElementById("editEmail");
const currentPassword = document.getElementById("currentPassword");
const newPassword = document.getElementById("newPassword");
const confirmPassword = document.getElementById("confirmPassword");
const saveProfileBtn = document.getElementById("saveProfileBtn");
const cancelProfileBtn = document.getElementById("cancelProfileBtn");

if (editProfileBtn) {
  editProfileBtn.addEventListener("click", () => {
    const user = loadUser() || {};
    editName.value = user.name || "";
    editEmail.value = user.email || "";
    editEmail.setAttribute("readonly", "readonly");
    currentPassword.value = "";
    newPassword.value = "";
    confirmPassword.value = "";
    profileEditForm.classList.remove("hidden");
    editProfileBtn.classList.add("hidden");
  });
}

if (cancelProfileBtn) {
  cancelProfileBtn.addEventListener("click", () => {
    profileEditForm.classList.add("hidden");
    editProfileBtn.classList.remove("hidden");
  });
}

if (saveProfileBtn) {
  saveProfileBtn.addEventListener("click", async () => {
    const user = loadUser() || {};
    const token = loadToken();
    const name = editName.value.trim();
    const currentValue = currentPassword.value.trim();
    const newValue = newPassword.value.trim();
    const confirmValue = confirmPassword.value.trim();

    if (!token) {
      clearSession();
      window.location.replace("login.html");
      return;
    }

    if (newValue || confirmValue) {
      if (newValue !== confirmValue) {
        alert("New passwords do not match.");
        return;
      }
      if (!currentValue) {
        alert("Enter your current password.");
        return;
      }
    }

    const originalLabel = saveProfileBtn.textContent;
    saveProfileBtn.dataset.label = originalLabel;
    setButtonLoading(saveProfileBtn, true, "Saving...");
    setAppStatus("Updating profile...");

    try {
      const profile = await requestJson("/profile", {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ full_name: name || null }),
      });
      user.name = profile.full_name || name || user.name;
      saveUser(user);
      renderProfile(user, profile);

      if (newValue) {
        await requestJson("/auth/password", {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ new_password: newValue }),
        });
      }

      profileEditForm.classList.add("hidden");
      editProfileBtn.classList.remove("hidden");
      currentPassword.value = "";
      newPassword.value = "";
      confirmPassword.value = "";
      setAppStatus("Profile updated.");
    } catch (error) {
      setAppStatus(error.message || "Unable to update profile.", "error");
    } finally {
      setButtonLoading(saveProfileBtn, false);
    }
  });
}

const renderHistory = (history) => {
  if (history.length === 0) {
    historyList.innerHTML = "<p class=\"muted\">No checks yet.</p>";
    return;
  }
  historyList.innerHTML = history
    .map((item, i) =>
      `<div class="history-item" role="button" tabindex="0" data-index="${i}" data-action="view">
        <div class="history-main">
          <p class="eyebrow">${new Date(item.created_at).toLocaleString()}</p>
          <strong>${item.predicted_disease}</strong>
          <p class="muted">${item.symptoms.join(", ")}</p>
        </div>
        <span class="history-actions">
          <button class="small-btn danger-btn" type="button" data-index="${i}" data-action="delete">Delete</button>
        </span>
      </div>`
    )
    .join("");
};

const fetchHistory = async () => {
  const token = loadToken();
  if (!token) return [];
  return requestJson("/history", {
    headers: { Authorization: `Bearer ${token}` },
  });
};

// History delete handler (event delegation)
let cachedHistory = [];

historyList.addEventListener("click", (e) => {
  const deleteBtn = e.target.closest("button[data-action='delete']");
  if (deleteBtn) {
    const idx = Number(deleteBtn.dataset.index);
    if (!Number.isFinite(idx) || idx < 0 || idx >= cachedHistory.length) return;
    const entry = cachedHistory[idx];
    if (!entry) return;
    const token = loadToken();
    if (!token) return;
    if (!confirm("Delete this history item?")) return;

    (async () => {
      try {
        await requestJson(`/history/${entry.id}`, {
          method: "DELETE",
          headers: { Authorization: `Bearer ${token}` },
        });
        cachedHistory = await fetchHistory();
        renderHistory(cachedHistory);
      } catch (error) {
        alert(error.message || "Unable to delete history.");
      }
    })();
    return;
  }

  const card = e.target.closest(".history-item[data-action='view']");
  if (!card) return;
  const idx = Number(card.dataset.index);
  const entry = cachedHistory[idx];
  if (!entry) return;
  resultTitle.textContent = entry.predicted_disease;
  resultDesc.textContent = entry.description || entry.symptoms.join(", ");
  resultCard.classList.remove("hidden");
  showView("checker");
});

historyList.addEventListener("keydown", (e) => {
  if (e.key !== "Enter" && e.key !== " ") return;
  const card = e.target.closest(".history-item[data-action='view']");
  if (!card) return;
  e.preventDefault();
  const idx = Number(card.dataset.index);
  const entry = cachedHistory[idx];
  if (!entry) return;
  resultTitle.textContent = entry.predicted_disease;
  resultDesc.textContent = entry.description || entry.symptoms.join(", ");
  resultCard.classList.remove("hidden");
  showView("checker");
});

if (clearHistoryBtn) {
  clearHistoryBtn.addEventListener("click", () => {
    const token = loadToken();
    if (!token) return;
    if (!confirm("Clear all history?")) return;

    (async () => {
      try {
        await requestJson("/history", {
          method: "DELETE",
          headers: { Authorization: `Bearer ${token}` },
        });
        cachedHistory = [];
        renderHistory(cachedHistory);
      } catch (error) {
        alert(error.message || "Unable to clear history.");
      }
    })();
  });
}

const updateSelectedCount = () => {
  selectedCount.textContent = `${selectedSet.size} selected`;
};

const renderSymptomList = (items) => {
  symptomList.innerHTML = items
    .map((symptom) => {
      const checked = selectedSet.has(symptom.key) ? "checked" : "";
      return `
        <label class="symptom-item">
          <input type="checkbox" value="${symptom.key}" ${checked} />
          <span>${symptom.label}</span>
        </label>`;
    })
    .join("");
  updateSelectedCount();
};

const filterSymptoms = () => {
  const query = symptomSearch.value.trim().toLowerCase();
  if (!query) {
    renderSymptomList(symptomData);
    return;
  }
  const filtered = symptomData.filter((item) =>
    item.label.toLowerCase().includes(query)
  );
  renderSymptomList(filtered);
};

const fetchSymptoms = async () => {
  const response = await fetch(`${API_BASE}/symptoms`);
  if (!response.ok) {
    throw new Error("Unable to load symptoms list.");
  }
  return response.json();
};

const predictDisease = async (symptoms) => {
  const token = loadToken();
  const headers = { "Content-Type": "application/json" };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  try {
    const response = await fetch(`${API_BASE}/predict`, {
      method: "POST",
      headers,
      credentials: "include",
      body: JSON.stringify({ symptoms }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const message = errorData.detail || `HTTP ${response.status}: Prediction failed.`;
      throw new Error(message);
    }

    return response.json();
  } catch (error) {
    console.error("Predict error:", error, "API Base:", API_BASE);
    throw error;
  }
};

const init = async () => {
  const user = loadUser();
  const token = loadToken();
  if (!user || !token) {
    clearSession();
    window.location.replace("signup.html");
    return;
  }
  let profile = null;
  setAppStatus("Syncing...");
  try {
    profile = await requestJson("/profile", {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (profile?.full_name && !user.name) {
      user.name = profile.full_name;
      saveUser(user);
    }
  } catch (error) {
    console.warn(error);
  }

  renderProfile(user, profile);
  try {
    cachedHistory = await fetchHistory();
    renderHistory(cachedHistory);
    setAppStatus("Synced");
  } catch (error) {
    historyList.innerHTML = `<p class="muted">${error.message}</p>`;
    setAppStatus("Sync failed", "error");
  }
  showView("checker");

  try {
    symptomData = await fetchSymptoms();
    renderSymptomList(symptomData);
  } catch (error) {
    symptomList.innerHTML = `<p class="muted">${error.message}</p>`;
  }
};

signOutBtn.addEventListener("click", () => {
  clearSession();
  window.location.replace("signup.html");
});

navButtons.forEach((btn) => {
  btn.addEventListener("click", () => showView(btn.dataset.view));
});

symptomSearch.addEventListener("input", filterSymptoms);

// Track checkbox changes and maintain selectedSet so selections persist across filters
symptomList.addEventListener("change", (e) => {
  const input = e.target;
  if (!input || input.tagName !== "INPUT" || input.type !== "checkbox") return;
  const key = input.value;
  if (input.checked) selectedSet.add(key);
  else selectedSet.delete(key);
  updateSelectedCount();
});

checkBtn.addEventListener("click", async () => {
  const checked = Array.from(symptomList.querySelectorAll("input:checked")).map(
    (input) => input.value
  );
  if (checked.length === 0) {
    alert("Select at least one symptom.");
    return;
  }

  checkBtn.dataset.label = checkBtn.textContent;
  setButtonLoading(checkBtn, true, "Predicting...");
  try {
    const prediction = await predictDisease(checked);
    const description = prediction.description || "Description not available.";
    resultTitle.textContent = prediction.predicted_disease;
    resultDesc.textContent = description;
    resultCard.classList.remove("hidden");

    const labelMap = new Map(symptomData.map((item) => [item.key, item.label]));
    lastPrediction = {
      disease: prediction.predicted_disease,
      symptoms: checked.map((item) => labelMap.get(item) || item),
      description,
    };

    const token = loadToken();
    if (token) {
      await requestJson("/history", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          symptoms: lastPrediction.symptoms,
          predicted_disease: lastPrediction.disease,
          confidence: null,
          description: lastPrediction.description,
        }),
      });

      cachedHistory = await fetchHistory();
      renderHistory(cachedHistory);
    }
  } catch (error) {
    alert(error.message);
  } finally {
    setButtonLoading(checkBtn, false);
  }
});

init();
