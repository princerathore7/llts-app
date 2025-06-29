let allTenders = [];

// Format date safely
function formatDate(dateStr) {
  if (!dateStr) return "Not set";
  const date = new Date(dateStr);
  return isNaN(date.getTime()) ? "Invalid date" : date.toLocaleDateString();
}

// ✅ Render tender cards with Apply + Report buttons and Owner ID
function displayTenders(tenders) {
  const tenderList = document.getElementById("tenderList");
  tenderList.innerHTML = "";

  if (!tenders.length) {
    tenderList.innerHTML = "<p>No tenders available.</p>";
    return;
  }

  tenders.forEach(tender => {
    const card = document.createElement("div");
    card.className = "card";

    const ownerId = tender.created_by || "Unknown";
    const ownerPhone = tender.owner_phone || "919999999999"; // ✅ Ensure this is coming from DB
    const tenderTitle = tender.title || "Untitled";

    card.innerHTML = `
      <h3>${tenderTitle}</h3>
      <p><strong>Owner ID:</strong> ${tender.owner_id || 'Unknown'}</p>
      <p>${tender.description}</p>
      <p><strong>Budget:</strong> ₹${tender.budget}</p>
      <p><strong>Location:</strong> ${tender.location}</p>
      <p><strong>Deadline:</strong> ${formatDate(tender.deadline)}</p>
      <p><strong>Category:</strong> ${tender.category}</p>
      <button class="btn" onclick="applyForTender('${tender._id}', '${ownerPhone}', \`${tenderTitle}\`)">📲 Apply via WhatsApp</button>
      <button class="btn btn-report" onclick="reportTender('${tender._id}', '${ownerId}')">🚩 Report</button>
    `;

    tenderList.appendChild(card);
  });
}


// ✅ Render auction cards (unchanged)
function displayAuctions(auctions) {
  const auctionList = document.getElementById("auctionList");
  auctionList.innerHTML = "";

  if (!auctions.length) {
    auctionList.innerHTML = "<p>No auctions available.</p>";
    return;
  }

  auctions.forEach(auction => {
    const card = document.createElement("div");
    card.className = "card";
    card.innerHTML = `
      <h3>${auction.item_name || 'Untitled'}</h3>
      <p><strong>Owner:</strong> ${auction.owner || 'N/A'}</p>
      <p><strong>Description:</strong> ${auction.description || 'No description provided.'}</p>
      <p><strong>Starting Bid:</strong> ₹${auction.starting_bid || 0}</p>
      <p><strong>Location:</strong> ${auction.location || 'Unknown'}</p>
      <p><strong>End Date:</strong> ${formatDate(auction.end_date)}</p>
      <a href="#" class="btn">Place Bid</a>
    `;
    auctionList.appendChild(card);
  });
}

// ✅ Updated reportTender to include ownerId
function reportTender(tenderId, ownerId) {
  const token = localStorage.getItem("token");
  if (!token) return alert("Please login first.");

  const payload = JSON.parse(atob(token.split(".")[1]));
  const reporterId = payload.user_id || payload.id;

  const reportUrl = `report.html?tender_id=${tenderId}&reporter_id=${reporterId}&owner_id=${ownerId}`;
  window.open(reportUrl, "_blank");
}


// ✅ Fetch tenders & auctions from backend
function fetchTendersAndAuctions() {
  const token = localStorage.getItem("token");
  if (!token) {
    alert("You must be logged in to view tenders and auctions.");
    return;
  }

  fetch('https://llts-app.onrender.com/api/get-tenders', {
    headers: {
      Authorization: 'Bearer ' + token
    }
  })
    .then(response => {
      if (!response.ok) throw new Error('Network error');
      return response.json();
    })
    .then(data => {
      allTenders = data.tenders || [];
const selectedCategory = document.getElementById("categoryFilter")?.value || "All";
filterTendersByCategory(selectedCategory); // ✅ This applies category filter correctly
displayAuctions(allTenders.filter(t => t.type === 'auction'));

    })
    .catch(err => {
      console.error("Fetch error:", err);
      document.getElementById("tenderList").innerHTML = "<p style='color:red;'>Error loading tenders.</p>";
      document.getElementById("auctionList").innerHTML = "<p style='color:red;'>Error loading auctions.</p>";
    });
}

// 🔍 Filter tenders by category
function filterTendersByCategory(category) {
  if (category === "All") {
    // ✅ Show all tenders of type 'tender'
    displayTenders(allTenders.filter(t => t.type === 'tender'));
  } else {
    // ✅ Filter by actual category
    const filtered = allTenders.filter(t => t.type === 'tender' && t.category === category);
    displayTenders(filtered);
  }
}

// ✅ Apply logic
function applyForTender(tenderId, ownerPhone, tenderTitle) {
  if (!tenderId || !ownerPhone) {
    console.error("❌ Missing tender ID or owner phone");
    return;
  }

  localStorage.setItem("selectedTenderId", tenderId);
  localStorage.setItem("selectedOwnerPhone", ownerPhone);
  localStorage.setItem("selectedTenderTitle", tenderTitle);

  console.log("✅ Saved tender ID, phone & title to localStorage.");
  window.location.href = "apply.html";
}



// 🚩 Report tender logic
function reportTender(tenderId) {
  const token = localStorage.getItem("token");
  if (!token) {
    alert("Login required to report tender.");
    return;
  }

  try {
    const payload = JSON.parse(atob(token.split(".")[1]));
    const reporterId = payload.user_id || payload.id || "unknown";
    const url = `report.html?tender_id=${tenderId}&reporter_id=${reporterId}`;
    window.open(url, "_blank");
  } catch (e) {
    console.error("❌ Error decoding token for reporter ID:", e);
  }
}

// 🚀 Init on page load
window.fetchTendersAndAuctions = function () {
  const token = localStorage.getItem("token");
  if (!token) {
    alert("You must be logged in to view tenders and auctions.");
    return;
  }

  fetch('https://llts-app.onrender.com/api/get-tenders', {
    headers: {
      Authorization: 'Bearer ' + token
    }
  })
    .then(response => {
      if (!response.ok) throw new Error('Network error');
      return response.json();
    })
    .then(data => {
      allTenders = data.tenders || [];
      displayTenders(allTenders.filter(t => t.type === 'tender'));
      displayAuctions(allTenders.filter(t => t.type === 'auction'));
    })
    .catch(err => {
      console.error("Fetch error:", err);
      document.getElementById("tenderList").innerHTML = "<p style='color:red;'>Error loading tenders.</p>";
      document.getElementById("auctionList").innerHTML = "<p style='color:red;'>Error loading auctions.</p>";
    });
};

// 🔁 Initial load
document.addEventListener("DOMContentLoaded", function () {
  fetchTendersAndAuctions();

  const categoryFilter = document.getElementById("categoryFilter");
  if (categoryFilter) {
    categoryFilter.addEventListener("change", function () {
      filterTendersByCategory(this.value);
    });
  }
});
