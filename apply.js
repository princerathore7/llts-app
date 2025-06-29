// ✅ Handle tender application via WhatsApp
document.getElementById('applyForm').addEventListener('submit', function (e) {
  e.preventDefault();

  // Get input values from form
  const fullName = document.getElementById('fullName').value.trim();
  const mobile = document.getElementById('mobile').value.trim();
  const amount = document.getElementById('amount').value.trim();
  const message = document.getElementById('message').value.trim();

  // Get tender info from localStorage
  const ownerPhone = localStorage.getItem("selectedOwnerPhone") || "919999999999";
  const tenderTitle = localStorage.getItem("selectedTenderTitle") || "a tender";

  // 🛑 Basic validation
  if (!fullName || !mobile || !amount || !message) {
    alert("⚠️ Please fill in all fields.");
    return;
  }

  if (!ownerPhone || !/^(\+?\d{10,15})$/.test(ownerPhone)) {
    alert("⚠️ Invalid or missing owner contact number.");
    return;
  }

  // 📝 Compose message
  const finalMessage = `Hello, I'm interested in your tender "${tenderTitle}".\n\n👤 Name: ${fullName}\n📱 Contact: ${mobile}\n💰 Quoted Price: ₹${amount}\n📄 Reason: ${message}\n\nRegards,\nLLTS Corporations`;

  const encodedMessage = encodeURIComponent(finalMessage);
  const whatsappURL = `https://wa.me/${ownerPhone}?text=${encodedMessage}`;

  // 🧹 Cleanup storage
  localStorage.removeItem("selectedTenderId");
  localStorage.removeItem("selectedOwnerPhone");
  localStorage.removeItem("selectedTenderTitle");

  // 📲 Redirect to WhatsApp
  window.location.href = whatsappURL;
});
