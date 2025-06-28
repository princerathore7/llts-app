const API_BASE = 'https://llts-app.onrender.com/api';

// ========== JWT PARSER ==========
function parseJwt(token) {
    try {
        const base64Url = token.split('.')[1];
        const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
        const jsonPayload = decodeURIComponent(
            atob(base64)
                .split('')
                .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
                .join('')
        );
        return JSON.parse(jsonPayload);
    } catch (e) {
        console.error("JWT parse error:", e);
        return null;
    }
}

// ========== SIGNUP ==========
document.getElementById('signup-form')?.addEventListener('submit', async (event) => {
    event.preventDefault();

    const username = document.getElementById('signup-username')?.value.trim();
    const password = document.getElementById('signup-password')?.value;
    const name = document.getElementById('signup-name')?.value.trim();
    const email = document.getElementById('signup-email')?.value.trim();
    const role = document.querySelector('input[name="role"]:checked')?.value;

    if (!username || !password || !name || !email || !role) {
        alert('Please fill all fields and select a role.');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/signup`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password, name, email, role }),
            credentials: 'include'
        });

        const data = await response.json();

        if (response.ok) {
            const token = data.access_token || data.token;
            if (token) {
                localStorage.setItem('jwt', token);  // ✅ FIXED
                localStorage.setItem('role', data.role || role);
                localStorage.setItem('username', username);

                const decoded = parseJwt(token);
                if (decoded?.id) localStorage.setItem('owner_id', decoded.id);

                const finalRole = (data.role || role).toLowerCase();
                if (finalRole === 'owner') {
                    window.location.href = 'ownerDashboard.html';
                } else if (finalRole === 'worker') {
                    window.location.href = 'worker-dashboard.html';
                } else {
                    alert('Signup successful, but unknown role.');
                }
            } else {
                alert('Signup successful. Please login.');
                window.location.href = 'loginscreen.html';
            }
        } else {
            alert(data.message || 'Signup failed.');
        }
    } catch (err) {
        console.error('Signup error:', err);
        alert('Server error during signup.');
    }
});

// ========== LOGIN ==========
document.getElementById('loginForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();

    const username = document.getElementById('username')?.value.trim();
    const password = document.getElementById('password')?.value;

    if (!username || !password) {
        alert('Please enter username and password.');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password }),
            credentials: 'include'
        });

        const data = await response.json();

        if (response.ok && data.token) {
            localStorage.setItem('jwt', data.token);  // ✅ MATCHING
            localStorage.setItem('role', data.role);
            localStorage.setItem('username', username);

            const decoded = parseJwt(data.token);
            if (decoded?.id) localStorage.setItem('owner_id', decoded.id);

            const role = (data.role || decoded?.role || "").toLowerCase();
            if (role === 'owner') {
                window.location.href = 'ownerDashboard.html';
            } else if (role === 'worker') {
                window.location.href = 'worker-dashboard.html';
            } else {
                alert('Login successful, but unknown role.');
            }
        } else {
            alert(data.message || 'Invalid credentials.');
        }
    } catch (err) {
        console.error('❌ Error parsing JSON login response:', err);
        const text = await response.text();
        console.log('🔍 Raw response text:', text);
        alert('Server error during login. Check console.');
    }
});


// ========== POST TENDER ==========
document.getElementById('post-tender-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();

    const title = document.getElementById('tender-title')?.value;
    const description = document.getElementById('tender-description')?.value;
    const budget = parseFloat(document.getElementById('tender-budget')?.value);
    const category = document.getElementById('tender-category')?.value;
    const location = document.getElementById('tender-location')?.value;
    const deadline = document.getElementById('tender-deadline')?.value;

    const token = localStorage.getItem('token');
    if (!token) {
        alert('You must be logged in as owner.');
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/tenders`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ title, description, budget, category, location, deadline })
        });

        const result = await res.json();
        if (res.ok) {
            alert('Tender posted successfully!');
            window.location.href = 'ownerDashboard.html';
        } else {
            alert(result.message || 'Tender posting failed.');
        }
    } catch (err) {
        console.error('Tender posting error:', err);
        alert('Error posting tender.');
    }
});

// ========== APPLY FOR TENDER ==========
async function applyForTender(tenderId) {
    const token = localStorage.getItem('token');
    if (!token) return alert("You're not logged in.");

    const payload = parseJwt(token);
    const workerId = payload?.id;

    if (!workerId) return alert("Invalid token or user not found.");

    try {
        const res = await fetch(`${API_BASE}/worker/apply`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ worker_id: workerId, tender_id: tenderId })
        });

        const result = await res.json();
        alert(result.message || "Application response received.");
    } catch (err) {
        console.error("Application error:", err);
        alert("Failed to apply.");
    }
}

// ========== FETCH AND RENDER TENDERS ==========
async function fetchAndRenderTenders() {
    const token = localStorage.getItem('token');
    if (!token) return alert("You're not logged in.");

    try {
        const res = await fetch(`${API_BASE}/get-tenders`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const data = await res.json();

        const tenders = data?.tenders || [];
        const container = document.getElementById('tenderList');
        if (!container) return;

        container.innerHTML = '';
        tenders.forEach(tender => {
            const card = document.createElement('div');
            card.className = 'card';
            card.innerHTML = `
                <h3>${tender.title}</h3>
                <p>${tender.description}</p>
                <p><strong>Budget:</strong> ₹${tender.budget}</p>
                <p><strong>Category:</strong> ${tender.category}</p>
                <p><strong>Deadline:</strong> ${new Date(tender.deadline).toLocaleDateString()}</p>
                <button onclick="applyForTender('${tender._id}')">Apply</button>
            `;
            container.appendChild(card);
        });
    } catch (error) {
        console.error("Failed to fetch tenders:", error);
        alert("Error loading tenders.");
    }
}

// ========== FETCH AND RENDER AUCTIONS ==========
async function fetchAndRenderAuctions() {
    const token = localStorage.getItem('token');
    if (!token) return alert("You're not logged in.");

    try {
        const res = await fetch(`${API_BASE}/get-auctions`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const data = await res.json();

        const auctions = data?.auctions || [];
        const container = document.getElementById('auctionList');
        if (!container) return;

        container.innerHTML = '';
        auctions.forEach(auction => {
            const card = document.createElement('div');
            card.className = 'card';
            card.innerHTML = `
                <h3>${auction.item_name}</h3>
                <p>${auction.description}</p>
                <p><strong>Start Bid:</strong> ₹${auction.starting_bid}</p>
                <p><strong>Location:</strong> ${auction.location}</p>
                <p><strong>End Date:</strong> ${new Date(auction.end_date).toLocaleDateString()}</p>
            `;
            container.appendChild(card);
        });
    } catch (error) {
        console.error("Failed to fetch auctions:", error);
        alert("Error loading auctions.");
    }
}

// ========== AUTO OWNER SIGNUP ==========
document.getElementById('start-as-owner')?.addEventListener('click', async () => {
    const username = 'owner_' + Math.floor(Math.random() * 100000);
    const password = Math.random().toString(36).slice(-8);

    try {
const response = await fetch(`${API_BASE}/signup`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        username,
        password,
        name: 'Auto Owner',
        email: `${username}@llts.com`,
        role: 'owner'
    }),
    credentials: 'include'  // ✅ ADD THIS
});


        const data = await response.json();
        if (response.ok && data.access_token) {
            localStorage.setItem('token', data.access_token);
            localStorage.setItem('role', data.role);
            localStorage.setItem('username', username);

            if (data.role === 'owner') {
                window.location.href = 'ownerDashboard.html';
            } else if (data.role === 'worker') {
                window.location.href = 'worker-dashboard.html';
            } else {
                alert('Login successful, but unknown role.');
            }
        } else {
            alert(data.error || "Login failed");
        }
    } catch (err) {
        console.error('Auto signup failed:', err);
    }
});

// ========== REDIRECTION BUTTONS ==========
document.getElementById('already-user-btn')?.addEventListener('click', () => {
    window.location.href = 'loginscreen.html';
});

document.getElementById('new-user-btn')?.addEventListener('click', () => {
    window.location.href = 'signup.html';
});

// ========== GLOBAL ACCESS ==========
window.fetchAndRenderTenders = fetchAndRenderTenders;
window.fetchAndRenderAuctions = fetchAndRenderAuctions;
window.applyForTender = applyForTender;
//window.fetchAndRenderApplications = fetchAndRenderApplications;
window.openApplicationsModal = openApplicationsModal;

// ✅ Fetch and Render Received Applications
async function loadReceivedApplications() {
  const token = localStorage.getItem("jwt");  // ✅ correct key
  const container = document.getElementById("owner-applications");
  container.innerHTML = "";

  if (!token) {
    container.innerHTML = "<p>Token missing. Please log in again.</p>";
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/owner/my-applications`, {
      method: "GET",
      headers: {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json"
      }
    });

    if (!res.ok) {
      console.warn("❌ Application fetch failed:", res.status);
      container.innerHTML = "<p>Failed to load applications.</p>";
      return;
    }

    const data = await res.json();
    if (!data.applications || data.applications.length === 0) {
      container.innerHTML = "<p>No applications received yet.</p>";
      return;
    }

    data.applications.forEach(app => {
      const div = document.createElement("div");
      div.className = "card";
      div.innerHTML = `
        <h3>${app.worker_name || 'Unknown Worker'}</h3>
        <p><strong>Applied for:</strong> ${app.tender_title || '-'}</p>
        <p><strong>Status:</strong> ${app.status?.toUpperCase() || 'PENDING'}</p>
        <p><strong>Contact:</strong> ${app.worker_contact || 'N/A'}</p>
      `;
      container.appendChild(div);
    });

  } catch (err) {
    console.error("❌ Error loading applications:", err);
    container.innerHTML = "<p>Error fetching applications.</p>";
  }
}

// ✅ Open Application Modal
function openApplicationsModal() {
  const token = localStorage.getItem("jwt");
  if (!token) {
    alert("Token not found. Please login again.");
    window.location.href = "ownerlogin.html";
    return;
  }

  loadReceivedApplications();  // ✅ working version
  const modal = document.getElementById("applicationsModal");
  if (modal) modal.style.display = "block";
}

// ✅ LOAD RECEIVED APPLICATIONS - Nullified Version
// async function loadReceivedApplications() {
//   const token = localStorage.getItem("jwt");  // ✅ correct key
//   const container = document.getElementById("owner-applications");
//   container.innerHTML = "";

//   if (!token) {
//     container.innerHTML = "<p>Token missing. Please login again.</p>";
//     return;
//   }

//   try {
//     const res = await fetch(`${API_BASE}/owner/my-applications`, {
//       method: "GET",
//       headers: {
//         Authorization: `Bearer ${token}`,
//         "Content-Type": "application/json"
//       }
//     });

//     if (!res.ok) {
//       console.warn("❌ Application fetch failed:", res.status);
//       container.innerHTML = "<p>Failed to load applications.</p>";
//       return;
//     }

//     const data = await res.json();

//     if (!data.applications || data.applications.length === 0) {
//       container.innerHTML = "<p>No applications received yet.</p>";
//       return;
//     }

//     data.applications.forEach(app => {
//       const div = document.createElement("div");
//       div.className = "card";
//       div.innerHTML = `
//         <h3>${app.worker_name || 'Unknown Worker'}</h3>
//         <p><strong>Applied for:</strong> ${app.tender_title || '-'}</p>
//         <p><strong>Status:</strong> ${app.status?.toUpperCase() || 'PENDING'}</p>
//         <p><strong>Contact:</strong> ${app.worker_contact || 'N/A'}</p>
//       `;
//       container.appendChild(div);
//     });

//   } catch (err) {
//     console.error("❌ Error loading applications:", err);
//     container.innerHTML = "<p>Error fetching applications.</p>";
//   }
// }
