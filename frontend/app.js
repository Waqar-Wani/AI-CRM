function getApiBase() {
  const el = document.getElementById("apiBase");
  return (el?.value || "http://127.0.0.1:8000").replace(/\/+$/, "");
}

async function api(path, options = {}) {
  const base = getApiBase();
  const res = await fetch(`${base}${path}`, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${text}`);
  }
  const ct = res.headers.get("content-type") || "";
  return ct.includes("application/json") ? res.json() : res.text();
}

function inr(n) {
  try {
    return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR" }).format(n);
  } catch {
    return `₹${n}`;
  }
}

function card(p, actionsHtml = "") {
  return `
    <div class="rounded-xl border bg-white p-4">
      <div class="space-y-1 min-h-[96px] flex flex-col justify-between">
        <div class="font-semibold text-sm sm:text-base">${escapeHtml(p.title)}</div>
        <div class="text-sm font-semibold text-slate-900">${inr(p.price)}</div>
        <div class="text-xs text-slate-600">${escapeHtml(p.location)}</div>
        <div class="text-xs text-slate-500">
          ${escapeHtml(p.property_type)} • ${p.area_sqft} sqft
        </div>
      </div>
      ${actionsHtml ? `<div class="mt-3 flex gap-2">${actionsHtml}</div>` : ""}
    </div>
  `;
}

function cardCompact(p) {
  // Use the same global layout without action buttons.
  return card(p);
}

function shuffled(items) {
  const arr = [...items];
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }
  return arr;
}

function escapeHtml(s) {
  return String(s ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function setMsg(id, msg) {
  const el = document.getElementById(id);
  if (el) el.textContent = msg || "";
}

function setFieldError(id, msg) {
  const el = document.getElementById(`err_${id}`);
  if (el) el.textContent = msg || "";
}

function setLoading(id, isLoading) {
  const el = document.getElementById(id);
  if (!el) return;
  el.classList.toggle("hidden", !isLoading);
  el.classList.toggle("flex", isLoading);
}

function formatNlpSourceLabel(source) {
  if (source === "llm") return "NLP engine: LLM";
  if (source === "heuristic") return "NLP engine: Heuristic fallback";
  return "NLP engine: Unknown";
}

// Simple routing (sections only)
const pageHome = document.getElementById("pageHome");
const pageAdminLogin = document.getElementById("pageAdminLogin");
const pageAdmin = document.getElementById("pageAdmin");
const pageUser = document.getElementById("pageUser");

let isAdmin = false;
let adminName = "";
const AUTH_ADMIN_KEY = "aiCrmIsAdmin";
const AUTH_NAME_KEY = "aiCrmAdminName";
const ROUTE_KEY = "aiCrmCurrentRoute";

if (typeof window !== "undefined" && window.sessionStorage) {
  isAdmin = window.sessionStorage.getItem(AUTH_ADMIN_KEY) === "true";
  adminName = window.sessionStorage.getItem(AUTH_NAME_KEY) || "";
}

function updateProfileUI() {
  if (profileLabel) {
    profileLabel.textContent = isAdmin ? adminName || "Admin" : "Admin login";
  }
  if (headerDashboard) {
    headerDashboard.classList.toggle("hidden", !isAdmin);
  }
  if (menuLogout) {
    menuLogout.classList.toggle("hidden", !isAdmin);
  }
  if (profileMenu) {
    profileMenu.classList.toggle("group-hover:block", isAdmin);
    profileMenu.classList.toggle("group-focus-within:block", isAdmin);
  }
  if (!isAdmin && profileMenu) {
    profileMenu.classList.add("hidden");
  }
}

function logoutAdmin() {
  isAdmin = false;
  adminName = "";
  if (window.sessionStorage) {
    window.sessionStorage.removeItem(AUTH_ADMIN_KEY);
    window.sessionStorage.removeItem(AUTH_NAME_KEY);
  }
  updateProfileUI();
  showHome();
}

function showHome() {
  pageHome.classList.remove("hidden");
  pageAdminLogin.classList.add("hidden");
  pageAdmin.classList.add("hidden");
  pageUser.classList.add("hidden");
  if (window.sessionStorage) {
    window.sessionStorage.setItem(ROUTE_KEY, "home");
  }
  updateProfileUI();
}

function showAdminLogin() {
  pageAdminLogin.classList.remove("hidden");
  pageHome.classList.add("hidden");
  pageAdmin.classList.add("hidden");
  pageUser.classList.add("hidden");
  if (window.sessionStorage) {
    window.sessionStorage.setItem(ROUTE_KEY, "admin_login");
  }
  updateProfileUI();
}

function showUser() {
  pageUser.classList.remove("hidden");
  pageAdminLogin.classList.add("hidden");
  pageAdmin.classList.add("hidden");
  pageHome.classList.add("hidden");
  if (window.sessionStorage) {
    window.sessionStorage.setItem(ROUTE_KEY, "user");
  }
  updateProfileUI();
}

function showAdmin() {
  if (!isAdmin) {
    // Redirect to admin login page
    showAdminLogin();
    return;
  }
  pageAdmin.classList.remove("hidden");
  pageUser.classList.add("hidden");
  pageHome.classList.add("hidden");
  pageAdminLogin.classList.add("hidden");
  if (window.sessionStorage) {
    window.sessionStorage.setItem(ROUTE_KEY, "admin");
  }
  updateProfileUI();
}

// Admin CRUD
const adminList = document.getElementById("adminList");
const refreshAdmin = document.getElementById("refreshAdmin");

async function loadAdmin() {
  setMsg("adminMsg", "Loading...");
  try {
    const items = await api("/admin/properties");
    adminList.innerHTML = items
      .map((p) =>
        card(
          p,
          `
          <button data-edit="${p.id}" class="rounded-lg bg-white border px-3 py-2 text-sm font-medium">Edit</button>
          <button data-del="${p.id}" class="rounded-lg bg-rose-600 px-3 py-2 text-sm font-medium text-white">Delete</button>
        `
        )
      )
      .join("");

    // bind buttons
    adminList.querySelectorAll("button[data-edit]").forEach((b) => {
      b.addEventListener("click", async () => {
        const id = Number(b.getAttribute("data-edit"));
        const p = items.find((x) => x.id === id);
        fillForm(p);
        setMsg("adminMsg", `Editing property #${id}`);
        window.scrollTo({ top: 0, behavior: "smooth" });
      });
    });
    adminList.querySelectorAll("button[data-del]").forEach((b) => {
      b.addEventListener("click", async () => {
        const id = Number(b.getAttribute("data-del"));
        if (!confirm(`Delete property #${id}?`)) return;
        await api(`/admin/properties/${id}`, { method: "DELETE" });
        setMsg("adminMsg", `Deleted property #${id}`);
        await loadAdmin();
        await loadUser();
      });
    });

    setMsg("adminMsg", `${items.length} properties loaded.`);
  } catch (e) {
    setMsg("adminMsg", String(e.message || e));
  }
}

refreshAdmin?.addEventListener("click", loadAdmin);

// Landing page search & admin login
const headerHome = document.getElementById("headerHome");
const homeSearch = document.getElementById("homeSearch");
const homeSearchBtn = document.getElementById("homeSearchBtn");
const homeResults = document.getElementById("homeResults");
const headerDashboard = document.getElementById("headerDashboard");
const headerProfile = document.getElementById("headerProfile");
const profileLabel = document.getElementById("profileLabel");
const profileMenu = document.getElementById("profileMenu");
const menuLogout = document.getElementById("menuLogout");
const adminBackHome = document.getElementById("adminBackHome");
const adminLoginForm = document.getElementById("adminLoginForm");

let homeScrollInterval;

function showHomeSamples(items) {
  if (!homeResults) return;
  // Horizontal carousel of a small sample
  const sample = shuffled(items).slice(0, 6);
  homeResults.className = "flex gap-4 overflow-x-auto pb-2";
  homeResults.innerHTML = sample
    .map((p) => `<div class="min-w-[260px] max-w-xs">${cardCompact(p)}</div>`)
    .join("");
  startHomeAutoScroll();
}

function showHomeSearchResults(items) {
  if (!homeResults) return;
  // Vertical list for explicit search results
  homeResults.className = "space-y-3";
  homeResults.innerHTML =
    items.length > 0
      ? shuffled(items).map((p) => cardCompact(p)).join("")
      : `<div class="text-sm text-slate-600">No matching properties found.</div>`;
  if (homeScrollInterval) {
    clearInterval(homeScrollInterval);
    homeScrollInterval = undefined;
  }
}

function startHomeAutoScroll() {
  if (!homeResults) return;
  if (homeScrollInterval) {
    clearInterval(homeScrollInterval);
    homeScrollInterval = undefined;
  }
  if (homeResults.scrollWidth <= homeResults.clientWidth + 8) {
    return; // nothing to scroll
  }
  homeScrollInterval = setInterval(() => {
    const el = homeResults;
    if (!el) return;
    if (el.scrollLeft + el.clientWidth + 4 >= el.scrollWidth) {
      el.scrollLeft = 0;
    } else {
      el.scrollLeft += 1;
    }
  }, 30);
}

headerProfile?.addEventListener("click", (e) => {
  e.preventDefault();
  if (!isAdmin) {
    showAdminLogin();
  }
});
updateProfileUI();
adminBackHome?.addEventListener("click", showHome);
headerHome?.addEventListener("click", showHome);
headerDashboard?.addEventListener("click", showAdmin);

adminLoginForm?.addEventListener("submit", (e) => {
  e.preventDefault();
  const email = document.getElementById("adminEmail").value.trim();
  const password = document.getElementById("adminPassword").value.trim();
  const msg = document.getElementById("loginMsg");

  if (email === "admin@example.com" && password === "admin123") {
    isAdmin = true;
    adminName = email.split("@")[0] || "Admin";
    if (window.sessionStorage) {
      window.sessionStorage.setItem(AUTH_ADMIN_KEY, "true");
      window.sessionStorage.setItem(AUTH_NAME_KEY, adminName);
    }
    if (msg) {
      msg.textContent = "Logged in as admin. Redirecting…";
      msg.className = "text-sm text-emerald-600";
    }
    updateProfileUI();
    setTimeout(() => {
      showAdmin();
    }, 500);
  } else {
    if (msg) {
      msg.textContent = "Invalid admin credentials for this demo.";
      msg.className = "text-sm text-rose-600";
    }
  }
});

menuLogout?.addEventListener("click", logoutAdmin);

const form = document.getElementById("propertyForm");
const resetFormBtn = document.getElementById("resetForm");

function fillForm(p) {
  document.getElementById("propertyId").value = p?.id ?? "";
  document.getElementById("title").value = p?.title ?? "";
  document.getElementById("location").value = p?.location ?? "";
  document.getElementById("price").value = p?.price ?? "";
  document.getElementById("area_sqft").value = p?.area_sqft ?? "";
  document.getElementById("property_type").value = p?.property_type ?? "Apartment";
  document.getElementById("description").value = p?.description ?? "";
}

function readForm() {
  return {
    title: document.getElementById("title").value.trim(),
    location: document.getElementById("location").value.trim(),
    price: Number(document.getElementById("price").value),
    area_sqft: Number(document.getElementById("area_sqft").value),
    property_type: document.getElementById("property_type").value,
    description: document.getElementById("description").value.trim(),
  };
}

function validateForm(payload) {
  // clear previous inline errors
  ["title", "location", "description", "price", "area_sqft", "property_type"].forEach((f) =>
    setFieldError(f, "")
  );

  const errors = [];
  if (!payload.title) {
    errors.push("Title is required.");
    setFieldError("title", "Title is required");
  }
  if (!payload.location) {
    errors.push("Location is required");
    setFieldError("location", "Location is required");
  }
  if (!payload.description) {
    errors.push("Description is required");
    setFieldError("description", "Description is required");
  }
  if (!Number.isFinite(payload.price) || payload.price <= 0) {
    errors.push("Enter the property price");
    setFieldError("price", "Enter the property price");
  }
  if (!Number.isFinite(payload.area_sqft) || payload.area_sqft <= 0) {
    errors.push("Enter the Area (sqft) of the property");
    setFieldError("area_sqft", "Enter the Area (sqft) of the property");
  }
  if (!payload.property_type) {
    errors.push("Property type is required");
    setFieldError("property_type", "Property type is required");
  }
  return errors;
}

resetFormBtn?.addEventListener("click", () => {
  fillForm(null);
  setMsg("adminMsg", "");
  ["title", "location", "description", "price", "area_sqft", "property_type"].forEach((f) =>
    setFieldError(f, "")
  );
});

form?.addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    const id = document.getElementById("propertyId").value;
    const payload = readForm();
    const errors = validateForm(payload);
    if (errors.length) {
      // show only inline messages; clear any global message
      setMsg("adminMsg", "");
      return;
    }
    setMsg("adminMsg", "Saving...");
    if (id) {
      await api(`/admin/properties/${id}`, { method: "PUT", body: JSON.stringify(payload) });
      setMsg("adminMsg", `Updated property #${id}`);
    } else {
      await api(`/admin/properties`, { method: "POST", body: JSON.stringify(payload) });
      setMsg("adminMsg", "Created property");
    }
    fillForm(null);
    await loadAdmin();
    await loadUser();
  } catch (e2) {
    setMsg("adminMsg", String(e2.message || e2));
  }
});

// User listings
const userList = document.getElementById("userList");
const refreshUser = document.getElementById("refreshUser");

async function loadUser() {
  try {
    const items = await api("/properties");
    userList.innerHTML = items.map((p) => card(p)).join("");
    // Seed landing page carousel on first load
    if (homeResults && !homeResults.dataset.initialised) {
      showHomeSamples(items);
      homeResults.dataset.initialised = "true";
    }
  } catch (e) {
    userList.innerHTML = `<div class="text-sm text-rose-700">${escapeHtml(e.message || e)}</div>`;
  }
}
refreshUser?.addEventListener("click", loadUser);

// Chat
const sendChat = document.getElementById("sendChat");
const clearChat = document.getElementById("clearChat");
const chatInput = document.getElementById("chatInput");
const chatNlpSource = document.getElementById("chatNlpSource");
const homeNlpSource = document.getElementById("homeNlpSource");
const chatResultCount = document.getElementById("chatResultCount");
const homeResultCount = document.getElementById("homeResultCount");

async function runChat() {
  try {
    const message = chatInput.value.trim();
    if (!message) {
      // Empty query => reset to all listings
      setMsg("chatMsg", "Showing all listings.");
      setMsg("chatNlpSource", "");
       setMsg("chatResultCount", "");
      await loadUser();
      return;
    }
    setLoading("chatLoader", true);
    setMsg("chatMsg", "Thinking...");
    setMsg("chatNlpSource", "");
    setMsg("chatResultCount", "");
    const out = await api("/chat/query", { method: "POST", body: JSON.stringify({ message }) });
    userList.innerHTML =
      out.results?.length && out.results.length > 0
        ? out.results.map((p) => card(p)).join("")
        : `<div class="text-sm text-slate-600">No matching properties found.</div>`;
    setMsg("chatResultCount", `Total results: ${out.results?.length || 0}`);
    if (chatNlpSource) {
      chatNlpSource.textContent = formatNlpSourceLabel(out.parser_source);
    }
    setMsg(
      "chatMsg",
      out.results?.length
        ? `Found ${out.results.length} matching properties.`
        : "No matches. Try broadening your query."
    );
  } catch (e) {
    console.error(e);
    setMsg("chatNlpSource", "");
    setMsg("chatResultCount", "");
    setMsg("chatMsg", "Something went wrong. Please try again.");
  } finally {
    setLoading("chatLoader", false);
  }
}

sendChat?.addEventListener("click", runChat);
chatInput?.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    runChat();
  }
});
clearChat?.addEventListener("click", () => {
  chatInput.value = "";
  setMsg("chatNlpSource", "");
  setMsg("chatResultCount", "");
  setMsg("chatMsg", "Showing all listings.");
  loadUser();
});

// Home search (reuses chat endpoint, displays results on landing page)
async function runHomeSearch() {
  try {
    const message = homeSearch.value.trim();
    if (!message) {
      // Empty query => show horizontal sample again
      const items = await api("/properties");
      showHomeSamples(items);
      setMsg("homeNlpSource", "");
      setMsg("homeResultCount", "");
      return;
    }
    setLoading("homeLoader", true);
    setMsg("homeResultCount", "");
    const out = await api("/chat/query", { method: "POST", body: JSON.stringify({ message }) });
    const results = out.results || [];
    showHomeSearchResults(results);
    setMsg("homeResultCount", `Total results: ${results.length}`);
    if (homeNlpSource) {
      homeNlpSource.textContent = formatNlpSourceLabel(out.parser_source);
    }
  } catch (e) {
    setMsg("homeNlpSource", "");
    setMsg("homeResultCount", "");
    homeResults.className = "space-y-3";
    homeResults.innerHTML = `<div class="text-sm text-rose-700">Something went wrong. Please try again.</div>`;
  } finally {
    setLoading("homeLoader", false);
  }
}

homeSearchBtn?.addEventListener("click", runHomeSearch);
homeSearch?.addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    e.preventDefault();
    runHomeSearch();
  }
});

// Initial load
const savedRoute =
  typeof window !== "undefined" && window.sessionStorage
    ? window.sessionStorage.getItem(ROUTE_KEY)
    : "";

if (savedRoute === "admin") {
  if (isAdmin) {
    showAdmin();
  } else {
    showAdminLogin();
  }
} else if (savedRoute === "admin_login") {
  showAdminLogin();
} else if (savedRoute === "user") {
  showUser();
} else {
  showHome();
}
loadAdmin();
loadUser();
