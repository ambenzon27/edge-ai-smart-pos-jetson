// =====================================================
// Elements
// =====================================================
const video = document.getElementById("video-feed");
const statusBanner = document.getElementById("status");
const orderList = document.getElementById("order-list");
const subtotalEl = document.getElementById("subtotal");
const grandTotalEl = document.getElementById("grand-total");
const itemCountEl = document.getElementById("item-count");
const payBtn = document.getElementById("pay-btn");
const checkoutModal = document.getElementById("checkout-modal");
const modalAmount = document.getElementById("modal-amount");
const modalClose = document.getElementById("modal-close");
const recordingIndicator = document.getElementById("recording-indicator");
const indicatorText = document.querySelector(".indicator-text");

// =====================================================
// State
// =====================================================
let order = [];
let itemPrices = {};
let isRecording = false;

// Duplicate protection
const recentlyAdded = new Map();
const DUPLICATE_WINDOW_MS = 1200;

// =====================================================
// Utilities
// =====================================================
const normalizeKey = k =>
  k?.toLowerCase().trim().replace(/\s+/g, "_");

// =====================================================
// Load Prices
// =====================================================
const loadPrices = async () => {
  try {
    const res = await fetch("/prices");
    if (!res.ok) {
      console.error("❌ Failed to load prices:", res.status);
      return;
    }

    const raw = await res.json();

    // Normalize price keys once
    itemPrices = {};
    Object.entries(raw).forEach(([k, v]) => {
      itemPrices[normalizeKey(k)] = Number(v) || 0;
    });

    console.log(
      "✅ Prices loaded:",
      Object.keys(itemPrices).length,
      itemPrices
    );
  } catch (e) {
    console.error("❌ Price fetch error:", e);
  }
};

// =====================================================
// Order Helpers
// =====================================================
const getTotalItemCount = () =>
  order.reduce((sum, item) => sum + item.quantity, 0);

const renderOrder = () => {
  if (order.length === 0) {
    orderList.innerHTML = `
      <div class="empty-order">
        <div class="empty-icon">🛍️</div>
        <p>Your cart is empty</p>
        <p class="empty-subtext">Start scanning items to add them</p>
      </div>
    `;
    return;
  }

  orderList.innerHTML = order.map(item => {
    const total = item.price * item.quantity;
    return `
      <div class="order-item">
        <div class="item-details">
          <span class="item-qty">${item.quantity}</span>
          <span class="item-name">${item.name}</span>
        </div>
        <div class="item-prices">
          ₱${total.toFixed(2)}
        </div>
      </div>
    `;
  }).join("");
};

const updateTotals = () => {
  const subtotal = order.reduce(
    (sum, i) => sum + (i.price * i.quantity),
    0
  );

  subtotalEl.textContent = `₱${subtotal.toFixed(2)}`;
  grandTotalEl.textContent = `₱${subtotal.toFixed(2)}`;

  const count = getTotalItemCount();
  itemCountEl.textContent = count === 1 ? "1 item" : `${count} items`;

  const btnText = payBtn.querySelector(".btn-text");
  if (btnText) {
    btnText.textContent = `Checkout - ₱${subtotal.toFixed(2)}`;
  }
};

// =====================================================
// Add / Increment Item (PRICE FIX CORE)
// =====================================================
const addOrIncrementItem = (className, detectedPrice) => {
  const now = Date.now();
  const key = normalizeKey(className);

  if (recentlyAdded.has(key)) {
    if (now - recentlyAdded.get(key) < DUPLICATE_WINDOW_MS) return;
  }
  recentlyAdded.set(key, now);

  const finalPrice =
    Number(detectedPrice) ||
    itemPrices[key] ||
    0;

  console.log(
    `🛒 ADD ITEM`,
    `raw="${className}"`,
    `key="${key}"`,
    `detected=`, detectedPrice,
    `priceMap=`, itemPrices[key],
    `final=`, finalPrice
  );

  const existing = order.find(i => i.name === className);

  if (existing) {
    existing.quantity++;
  } else {
    order.push({
      id: order.length + 1,
      name: className,
      price: finalPrice,
      quantity: 1
    });
  }

  renderOrder();
  updateTotals();
};

// =====================================================
// Video Stream Handling
// =====================================================
const showStatus = txt => {
  statusBanner.textContent = txt;
  statusBanner.hidden = false;
};

const hideStatus = () => {
  statusBanner.hidden = true;
};

const reloadStream = () => {
  video.src = `/video-stream?cb=${Date.now()}`;
};

video.addEventListener("error", () => {
  showStatus("Reconnecting camera…");
  setTimeout(reloadStream, 1500);
});

video.addEventListener("load", hideStatus);

// =====================================================
// Backend Polling
// =====================================================
const pollDetections = async () => {
  if (!isRecording) return;

  try {
    const res = await fetch("/detections");
    if (!res.ok) return;

    const detections = await res.json();

    detections.forEach(d => {
      addOrIncrementItem(d.class_name, d.price);
    });
  } catch (e) {
    console.error("❌ Detection polling error:", e);
  }
};

const pollRecordingState = async () => {
  try {
    const res = await fetch("/recording-state");
    if (!res.ok) return;

    const data = await res.json();
    isRecording = data.recording;
    updateRecordingIndicator(isRecording);
  } catch (e) {
    console.error("Recording state error:", e);
  }
};

// =====================================================
// Recording Indicator
// =====================================================
const updateRecordingIndicator = recording => {
  recordingIndicator.classList.toggle("recording", recording);
  recordingIndicator.classList.toggle("paused", !recording);
  indicatorText.textContent = recording ? "RECORDING" : "PAUSED";
};

// =====================================================
// Camera Health
// =====================================================
const checkCameraHealth = async () => {
  try {
    const res = await fetch("/health");
    if (!res.ok) return;

    const data = await res.json();
    if (data.status !== "ok") {
      showStatus(data.message || "Initializing camera…");
      setTimeout(checkCameraHealth, 1000);
    } else {
      hideStatus();
    }
  } catch {
    setTimeout(checkCameraHealth, 1000);
  }
};

// =====================================================
// Init
// =====================================================
loadPrices();
renderOrder();
updateTotals();
pollRecordingState();
checkCameraHealth();

setInterval(pollDetections, 800);
setInterval(pollRecordingState, 600);
