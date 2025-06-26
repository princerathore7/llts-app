document.getElementById('applyForm').addEventListener('submit', async function (e) {
  e.preventDefault();

  const fullName = document.getElementById('fullName').value.trim();
  const mobile = document.getElementById('mobile').value.trim();
  const amount = parseFloat(document.getElementById('amount').value.trim());
  const message = document.getElementById('message').value.trim();
  const token = localStorage.getItem("token");

  console.log("🔐 Raw JWT Token:", token);
  if (!token) {
    alert("❌ No token found. Please login again.");
    return;
  }

  // Decode token to verify structure
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    console.log("🧠 Decoded JWT Payload:", payload);
  } catch (e) {
    console.error("❌ Token decoding failed:", e);
    alert("Invalid or malformed token.");
    return;
  }

  const tenderId = localStorage.getItem("selectedTenderId");
  if (!tenderId) {
    alert("Tender ID not found.");
    return;
  }

  if (!fullName || !mobile || isNaN(amount) || amount <= 0) {
    alert("Please fill all fields correctly.");
    return;
  }

  const btn = document.getElementById("apply-btn");
  btn.disabled = true;
  btn.textContent = "Submitting...";

  try {
    const res = await fetch("https://llts-app.onrender.com/api/worker/apply-tender", {

      method: "POST",
      headers: {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        tender_id: tenderId,
        worker_name: fullName,
        contact: mobile,
        quoted_price: amount,
        message: message
      })
    });

    const data = await res.json();

    if (res.status === 409) {
      alert("⚠️ You have already applied to this tender.");
      return;
    }

    if (res.ok) {
      alert(data.msg || "✅ Application submitted!");
      localStorage.removeItem("selectedTenderId");
      
      // ✅ Redirect to success page
      window.location.href = "success.html";
    } else {
      alert("❌ Failed: " + (data?.error || "Unknown error"));
    }

  } catch (err) {
    console.error("🚨 Network/Server Error:", err);
    alert("Something went wrong while applying!");
  } finally {
    btn.disabled = false;
    btn.textContent = "🚀 Submit Application";
  }
});
