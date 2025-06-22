const API_BASE = "https://llts-app.onrender.com/api";


function parseJwt(token) {
    try {
        const base64Url = token.split('.')[1];
        const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
        const jsonPayload = decodeURIComponent(
            atob(base64).split('').map(c =>
                '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2)
            ).join('')
        );
        return JSON.parse(jsonPayload);
    } catch (e) {
        console.error('JWT parsing error:', e);
        return null;
    }
}

function redirectToLogin() {
    alert('Please login first to access the Worker Dashboard.');
    localStorage.clear();
    window.location.href = 'worker login.html';
}

function checkLogin() {
    const token = localStorage.getItem('token');
    const role = localStorage.getItem('role');

    if (!token || !role) {
        redirectToLogin();
        return null;
    }

    const decoded = parseJwt(token);
    if (!decoded || !decoded.id || !decoded.exp) {
        redirectToLogin();
        return null;
    }

    if (Date.now() >= decoded.exp * 1000) {
        alert('Session expired. Please login again.');
        redirectToLogin();
        return null;
    }

    if (role.toLowerCase() !== 'worker') {
        alert('Access denied: Worker role required.');
        redirectToLogin();
        return null;
    }

    return decoded;
}

function getAuthHeaders() {
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
    };
}

async function fetchUserProfile() {
    try {
        const res = await fetch(`${API_BASE}/worker/profile`, {
            method: 'GET',
            headers: getAuthHeaders()
        });

        if (!res.ok) throw new Error(`Profile fetch failed: ${res.status}`);
        const user = await res.json();

        document.getElementById('worker-name').textContent = user.name || 'Worker';
        document.getElementById('worker-email').textContent = user.email || '-';
        document.getElementById('worker-exp').textContent = user.experience || '-';
        document.getElementById('worker-skills').textContent = (user.skills || []).join(', ') || '-';
        document.getElementById('worker-location').textContent = user.location || '-';
    } catch (err) {
        console.error('Profile error:', err);
        redirectToLogin();
    }
}

async function fetchAvailableJobs() {
    try {
        const res = await fetch(`${API_BASE}/get-tenders`, {
            method: 'GET',
            headers: getAuthHeaders()
        });

        if (!res.ok) throw new Error('Failed to load jobs');
        const data = await res.json();
        const jobs = data.tenders || [];
        const jobsList = document.getElementById('jobs-list');
        jobsList.innerHTML = '';

        if (jobs.length === 0) {
            jobsList.innerHTML = '<li>No jobs available.</li>';
            return;
        }

        jobs.forEach(job => {
            const li = document.createElement('li');
            if (job.type === 'tender') {
                li.innerHTML = `
                    <strong>${job.title}</strong><br>
                    ₹${job.budget} — ${job.location || '-'} <br>
                    Deadline: ${job.deadline || '-'}<br>
                    <button class="apply-btn" onclick="applyForJob('${job.id}')">Apply</button>
                `;
            } else if (job.type === 'auction') {
                li.innerHTML = `
                    <strong>Auction: ${job.item_name}</strong><br>
                    Start Bid: ₹${job.starting_bid} — ${job.location || '-'}<br>
                    Ends on: ${job.end_date}<br>
                    <i>(No apply button yet)</i>
                `;
            }
            jobsList.appendChild(li);
        });

    } catch (err) {
        console.error('Job list error:', err);
        alert('Could not fetch jobs.');
    }
}

async function fetchActiveJobs(workerId) {
    try {
        const res = await fetch(`${API_BASE}/worker/active_jobs/${workerId}`, {
            method: 'GET',
            headers: getAuthHeaders()
        });

        if (!res.ok) throw new Error('Failed to load active jobs');
        const data = await res.json();
        const list = document.getElementById('active-jobs-list');
        list.innerHTML = '';

        if (!data.jobs?.length) {
            list.innerHTML = '<li>No active jobs.</li>';
            return;
        }

        data.jobs.forEach(job => {
            const li = document.createElement('li');
            li.textContent = `${job.title} — Status: ${job.status}`;
            list.appendChild(li);
        });

    } catch (err) {
        console.error('Active job error:', err);
        alert('Could not load active jobs.');
    }
}

async function applyForJob(jobId) {
    const decoded = parseJwt(localStorage.getItem('token'));
    if (!decoded || !decoded.id) return redirectToLogin();

    try {
        const res = await fetch(`${API_BASE}/worker/apply`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({
                worker_id: decoded.id,
                tender_id: jobId
            })
        });

        const data = await res.json();

        if (res.ok) {
            alert('Applied successfully!');
            fetchAvailableJobs();
            fetchActiveJobs(decoded.id);
        } else {
            alert(data.message || 'Failed to apply.');
        }
    } catch (err) {
        console.error('Apply error:', err);
        alert('Error applying for job.');
    }
}

function loadMyApplications(workerId) {
    fetch(`${API_BASE}/worker/active_jobs/${workerId}`, {
        method: 'GET',
        headers: getAuthHeaders()
    })
    .then(res => res.json())
    .then(data => {
        const applications = data.jobs || [];
        const container = document.getElementById("appliedJobsContainer");
        container.innerHTML = "";

        if (applications.length === 0) {
            container.innerHTML = "<p>No applications yet.</p>";
            return;
        }

        applications.forEach(app => {
            const box = document.createElement("div");
            box.className = "card";
            box.innerHTML = `
              <h3>${app.title}</h3>
              <p><strong>Status:</strong> ${app.status?.toUpperCase() || 'N/A'}</p>
              <p><strong>Applied On:</strong> ${app.applied_at || '-'}</p>
            `;
            container.appendChild(box);
        });
    })
    .catch(err => {
        console.error("Inbox error:", err);
        alert("Could not load your applications.");
    });
}

function setupLogout() {
    const btn = document.getElementById('logout-btn');
    btn?.addEventListener('click', () => {
        localStorage.clear();
        window.location.href = 'worker login.html';
    });
}

// ✅ Main Initialization on DOM load
document.addEventListener('DOMContentLoaded', () => {
    const decoded = checkLogin();
    if (!decoded) return;

    setupLogout();
    fetchUserProfile();
    fetchAvailableJobs();
    fetchActiveJobs(decoded.id);
    loadMyApplications(decoded.id);
});

    document.getElementById("logoutBtn").addEventListener("click", () => {
    localStorage.removeItem("token");  // ✅ Clear JWT token
    window.location.href = "welcome.html";  // ✅ Redirect to welcome
  });
  async function showTokenBalance() {
  const token = localStorage.getItem("token");
  if (!token) return;

  try {
    const res = await fetch("https://llts-app.onrender.com/api/user/token-info", {
      method: "GET",
      headers: {
        "Authorization": `Bearer ${token}`
      }
    });
    const data = await res.json();
    if (data.status === "success") {
      document.getElementById("token-balance").innerText = `🪙 Tokens: ${data.tokens}`;
    }
  } catch (err) {
    console.error("Token fetch error:", err);
    document.getElementById("token-balance").innerText = "🪙 Tokens: --";
  }
}
async function fetchAppliedTenderCount() {
  const token = localStorage.getItem("token");
  if (!token) return;

  try {
    const res = await fetch(`${API_BASE}/worker/applied-count`, {
      headers: {
        "Authorization": `Bearer ${token}`
      }
    });

    const data = await res.json();
    if (res.ok) {
      document.getElementById("applied-count").innerText = `📄 Tenders Applied: ${data.count}`;
    } else {
      console.error("Applied count fetch failed:", data);
    }
  } catch (err) {
    console.error("Applied count error:", err);
  }
}
