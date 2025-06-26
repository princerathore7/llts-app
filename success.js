// success.js
// Redirect to worker dashboard after 5 seconds
setTimeout(() => {
  window.location.href = "worker-dashboard.html";
}, 5000);

// Optional: Based on context, show dynamic message
const params = new URLSearchParams(window.location.search);
const type = params.get("type");

if (type === "tender") {
  document.getElementById("success-message").innerHTML =
    "Your <strong>tender application</strong> was submitted successfully.<br/>The owner will contact you if selected.";
} else if (type === "auction") {
  document.getElementById("success-message").innerHTML =
    "Your <strong>auction bid</strong> was placed successfully.<br/>The auction owner will contact you if you win.";
}
