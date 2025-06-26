// ✅ JS to fetch and render received applications for the owner

const token = localStorage.getItem("token");
const API_URL = "https://llts-app.onrender.com/api/owner/fetch-received"; // Update if needed

// 🔁 Fetch applications
fetch(API_URL, {
  method: "GET",
  headers: {
    "Authorization": "Bearer " + token
  }
})
.then(res => res.json())
.then(data => {
  if (data.status === "success") {
    console.log("✅ Applications Fetched:", data.applications);
    renderApplications(data.applications);
  } else {
    console.error("❌ Error:", data.message);
    document.getElementById("applications-container").innerHTML = "<p>Error fetching applications.</p>";
  }
})
.catch(err => {
  console.error("🚨 Fetch error:", err);
  document.getElementById("applications-container").innerHTML = "<p>Error loading applications.</p>";
});

// 🧾 Render logic
function renderApplications(applications) {
  const container = document.getElementById("applications-container");
  container.innerHTML = "";

  if (!applications.length) {
    container.innerHTML = "<p>No applications received yet.</p>";
    return;
  }

  applications.forEach(app => {
    const div = document.createElement("div");
    div.className = "app-card";
    div.innerHTML = `
      <h3>${app.tender_title}</h3>
      <p><strong>Worker:</strong> ${app.worker_name}</p>
      <p><strong>Contact:</strong> ${app.contact || "N/A"}</p>
      <p><strong>Quoted Price:</strong> ₹${app.quoted_price}</p>
      <p><strong>Message:</strong> ${app.message}</p>
      <p><strong>Applied At:</strong> ${new Date(app.applied_at).toLocaleString()}</p>
      <p><strong>Status:</strong> ${app.status}</p>
    `;
    container.appendChild(div);
  });
}
