const API_BASE = "https://llts-app.onrender.com/api";

document.addEventListener('DOMContentLoaded', async () => {
  const token = localStorage.getItem('token');
  const container = document.getElementById('application-list');

  if (!token) {
    alert("Please login first.");
    window.location.href = 'ownerlogin.html';
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/owner/received-applications`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    const data = await res.json();

    if (!res.ok) {
      alert("Error fetching applications.");
      console.error(data);
      return;
    }

    if (data.applications.length === 0) {
      container.innerHTML = `<p>No applications received yet.</p>`;
      return;
    }

    container.innerHTML = ''; // Clear existing content

    data.applications.forEach(app => {
      const card = document.createElement('div');
      card.className = 'application-card';

      card.innerHTML = `
        <h3>${app.worker_name || "Unnamed Worker"}</h3>
        <p><strong>Tender:</strong> ${app.tender_title}</p>
        <p><strong>Message:</strong> ${app.message || "No message provided."}</p>
        <p><strong>Quoted Price:</strong> ₹${app.quoted_price || "N/A"}</p>
        <p><strong>Date:</strong> ${new Date(app.applied_at).toLocaleString()}</p>
        <div class="application-actions">
          <button onclick="acceptAndChat('${app._id}', '${app.contact || ""}')">✅ Accept & Chat</button>
          <button onclick="rejectApplication('${app._id}')">❌ Reject</button>
        </div>
      `;

      container.appendChild(card);
    });

  } catch (err) {
    console.error("Error loading applications:", err);
    container.innerHTML = `<p>Failed to load applications.</p>`;
  }
});

async function rejectApplication(appId) {
  const token = localStorage.getItem('token');
  if (!confirm("Are you sure you want to reject this application?")) return;

  try {
    const res = await fetch(`${API_BASE}/owner/reject-application/${appId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    const data = await res.json();
    if (res.ok) {
      alert("Application rejected successfully.");
      location.reload();
    } else {
      alert("Failed to reject application.");
      console.error(data);
    }

  } catch (err) {
    console.error("Error rejecting application:", err);
    alert("An error occurred while rejecting the application.");
  }
}

async function acceptAndChat(appId, contactNumber) {
  const token = localStorage.getItem('token');
  if (!token) return alert("Unauthorized");

  try {
    const res = await fetch(`${API_BASE}/owner/accept-application/${appId}`, {
      method: 'PATCH',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    const data = await res.json();
    if (res.ok) {
      alert("Application accepted!");

      if (contactNumber) {
        // ✅ Format number for WhatsApp (India: +91)
        let phone = contactNumber.replace(/\D/g, '');
        if (!phone.startsWith("91")) {
          phone = "91" + phone;
        }

        const autoMessage = encodeURIComponent(
          "Hello! Congratulations, your tender is almost selected. Just want to confirm a few things. regards from s&p developments- Prince Rathore..."
        );

        // ✅ Open WhatsApp chat with prefilled message
        window.open(`https://wa.me/${phone}?text=${autoMessage}`, "_blank");
      } else {
        alert("Worker contact not available.");
      }

    } else {
      alert("Failed to accept application.");
      console.error(data);
    }

  } catch (err) {
    console.error("Error during accept:", err);
    alert("An error occurred while accepting the application.");
  }
}
