const dropzone = document.getElementById("dropzone");
const fileInput = document.getElementById("fileInput");
const selectButton = document.getElementById("selectButton");
const statusEl = document.getElementById("status");
const resultsEl = document.getElementById("results");
const previewEl = document.getElementById("preview");
const playersListEl = document.getElementById("playersList");
const galleryEl = document.getElementById("gallery");
const classifyButton = document.getElementById("classifyButton");

const apiUrl = "http://localhost:5000/api/";

let classLabels = [];
let currentImageData = null;
const defaultLabels = [
  "lionel_messi",
  "maria_sharapova",
  "roger_federer",
  "serena_williams",
  "virat_kohli",
];

const playerImages = {
  lionel_messi: "images/lionel_messi.webp",
  maria_sharapova: "images/maria_sharapova.jpg",
  roger_federer: "images/roger_federer.jpg",
  serena_williams: "images/serena_williams.webp",
  virat_kohli: "images/virat_kohli.webp",
};

const renderPlayerList = (labels) => {
  if (!playersListEl) return;
  const list = labels && labels.length ? labels : defaultLabels;
  playersListEl.innerHTML = "";
  list.forEach((name) => {
    const pill = document.createElement("span");
    pill.className = "pill";
    const pretty = name
      .split("_")
      .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
      .join(" ");
    pill.textContent = pretty;
    playersListEl.appendChild(pill);
  });
};

renderPlayerList(defaultLabels);

const renderGallery = (labels) => {
  if (!galleryEl) return;
  const list = labels && labels.length ? labels : defaultLabels;
  galleryEl.innerHTML = "";

  list.forEach((name) => {
    const card = document.createElement("div");
    card.className = "gallery-card";

    const img = document.createElement("img");
    const src = playerImages[name] || `images/${name}.webp`;
    img.src = src;
    img.alt = name;
    img.onerror = () => {
      console.log("Failed to load image:", src);
      img.style.display = "none";
    };

    const caption = document.createElement("div");
    caption.className = "caption";
    const pretty = name
      .split("_")
      .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
      .join(" ");
    caption.textContent = pretty;

    card.append(img, caption);
    galleryEl.appendChild(card);
  });
};

renderGallery(defaultLabels);

// Load class labels once to label probability rows
fetch(apiUrl + "class_labels")
  .then((res) => res.json())
  .then((labels) => {
    classLabels = labels;
    renderPlayerList(labels);
    renderGallery(labels);
  })
  .catch(() => {
    statusEl.textContent = "Could not load class labels.";
    statusEl.classList.add("error");
    renderPlayerList(defaultLabels);
    renderGallery(defaultLabels);
  });

const preventDefaults = (e) => {
  e.preventDefault();
  e.stopPropagation();
};

const setStatus = (text, variant = "") => {
  statusEl.textContent = text;
  statusEl.classList.remove("error", "ok");
  if (variant) statusEl.classList.add(variant);
};

const clearResults = () => {
  resultsEl.innerHTML = "";
};

const highlight = () => dropzone.classList.add("dragging");
const unhighlight = () => dropzone.classList.remove("dragging");

// Drag & drop wiring
["dragenter", "dragover", "dragleave", "drop"].forEach((eventName) => {
  dropzone.addEventListener(eventName, preventDefaults, false);
});

["dragenter", "dragover"].forEach((eventName) => {
  dropzone.addEventListener(eventName, highlight, false);
});

["dragleave", "drop"].forEach((eventName) => {
  dropzone.addEventListener(eventName, unhighlight, false);
});

dropzone.addEventListener("drop", (e) => {
  const dt = e.dataTransfer;
  const files = dt?.files;
  if (!files || !files.length) return;
  handleFile(files[0]);
});

dropzone.addEventListener("click", () => fileInput.click());
selectButton.addEventListener("click", () => fileInput.click());
fileInput.addEventListener("change", (e) => {
  const file = e.target.files?.[0];
  if (file) handleFile(file);
});

const handleFile = (file) => {
  if (!file.type.startsWith("image/")) {
    setStatus("Please drop an image file.", "error");
    return;
  }

  clearResults();
  setStatus(`Reading ${file.name}...`);

  const reader = new FileReader();
  reader.onload = () => {
    const dataUrl = reader.result;
    currentImageData = dataUrl;
    previewEl.src = dataUrl;
    previewEl.hidden = false;
    dropzone.setAttribute("data-has-image", "true");
    classifyButton.hidden = false;
    setStatus("Image loaded. Click 'Classify Image' to analyze.", "ok");
    clearResults();
  };
  reader.onerror = () => setStatus("Could not read the file.", "error");
  reader.readAsDataURL(file);
};

classifyButton.addEventListener("click", () => {
  if (currentImageData) {
    classify(currentImageData);
  }
});

const classify = async (dataUrl) => {
  setStatus("Classifying image...");
  clearResults();

  const formData = new FormData();
  formData.append("image_data", dataUrl);

  try {
    const res = await fetch(apiUrl + "classify-image", {
      method: "POST",
      body: formData,
    });

    if (!res.ok) {
      setStatus(`Request failed (${res.status}).`, "error");
      return;
    }

    const data = await res.json();
    renderResults(data);
  } catch (err) {
    setStatus("Network error while classifying.", "error");
  }
};

const renderResults = (data) => {
  if (typeof data === "string") {
    setStatus(data, "error");
    return;
  }

  if (!Array.isArray(data) || !data.length) {
    setStatus("No prediction returned.", "error");
    return;
  }

  const frag = document.createDocumentFragment();

  data.forEach((item, idx) => {
    const card = document.createElement("div");
    card.className = "result-card";

    const pillRow = document.createElement("div");
    pillRow.className = "pill-row";
    const pill = document.createElement("span");
    pill.className = "pill";

    // Format the class name nicely
    const prettyClass = item.class
      .split("_")
      .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
      .join(" ");

    pill.textContent = `${prettyClass}`;
    pillRow.appendChild(pill);

    const probs = document.createElement("div");
    probs.className = "probabilities";

    // Use class_labels from response if available, otherwise fallback to classLabels
    const labels =
      item.class_labels && item.class_labels.length > 0
        ? item.class_labels
        : classLabels && classLabels.length === item.class_probability.length
        ? classLabels
        : item.class_probability.map((_, i) => `Class ${i}`);

    item.class_probability.forEach((p, i) => {
      const row = document.createElement("div");
      row.className = "prob-row";

      const name = document.createElement("span");
      // Format label with proper capitalization
      const prettyLabel = labels[i]
        .split("_")
        .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
        .join(" ");
      name.textContent = `${prettyLabel}`;

      const value = document.createElement("span");
      value.textContent = `${p}%`;
      row.append(name, value);

      const meter = document.createElement("div");
      meter.className = "meter";
      const fill = document.createElement("span");
      fill.style.width = `${Math.min(p, 100)}%`;
      meter.appendChild(fill);

      probs.append(row, meter);
    });

    card.append(pillRow, probs);
    frag.appendChild(card);
  });

  resultsEl.innerHTML = "";
  resultsEl.appendChild(frag);
  setStatus("Done", "ok");
};
