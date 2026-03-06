const form = document.getElementById("inference-form");
const summary = document.getElementById("summary");
const bars = document.getElementById("bars");
const recommendationsEl = document.getElementById("recommendations");
const factorsEl = document.getElementById("factors");
const explanationEl = document.getElementById("explanation");

function value(id, cast = Number) {
  const raw = document.getElementById(id).value;
  return cast === String ? raw : cast(raw);
}

function getPayload() {
  return {
    location: value("location", String),
    horizon_hours: value("horizon_hours"),
    observation: {
      temperature_c: value("temperature_c"),
      humidity_pct: value("humidity_pct"),
      pressure_hpa: value("pressure_hpa"),
      wind_kph: value("wind_kph"),
      cloud_cover_pct: value("cloud_cover_pct"),
      dew_point_c: value("dew_point_c"),
      recent_rain_mm: value("recent_rain_mm"),
      uv_index: value("uv_index"),
      visibility_km: value("visibility_km"),
      month: value("month"),
      hour_24: value("hour_24"),
      season: value("season", String),
      terrain: value("terrain", String),
      pressure_trend: value("pressure_trend", String),
    },
  };
}

function renderBars(items) {
  bars.innerHTML = "";
  items.forEach((item) => {
    const row = document.createElement("div");
    row.className = "bar";
    const pct = Math.round(item.probability * 100);
    row.innerHTML = `
      <div class="bar-head">
        <span>${item.condition}</span>
        <span>${pct}%</span>
      </div>
      <div class="bar-fill" style="width:${pct}%"></div>
    `;
    bars.appendChild(row);
  });
}

function renderList(target, list, mapper) {
  target.innerHTML = "";
  list.forEach((item) => {
    const li = document.createElement("li");
    li.textContent = mapper(item);
    target.appendChild(li);
  });
}

function renderResult(data) {
  const rainPct = Math.round(data.rain_probability * 100);
  const confidence = Math.round(data.confidence_score * 100);
  const alertClass = data.alert_level === "severe" || data.alert_level === "high" ? "high-risk" : "";
  summary.innerHTML = `
    <strong>Condition:</strong> ${data.predicted_condition}<br />
    <strong>Rain Probability:</strong> ${rainPct}%<br />
    <strong>Expected Rainfall:</strong> ${data.expected_rainfall_mm} mm<br />
    <strong>Confidence:</strong> ${confidence}%<br />
    <strong class="${alertClass}">Alert:</strong> <span class="${alertClass}">${data.alert_level}</span>
  `;

  renderBars(data.condition_probabilities);
  renderList(recommendationsEl, data.expert_recommendations, (x) => x);
  renderList(
    factorsEl,
    data.key_factors,
    (f) => `${f.factor} (${f.direction}, impact=${f.impact})`
  );
  explanationEl.textContent = data.explanation;
}

async function runInference(event) {
  event.preventDefault();
  const baseUrl = value("apiBaseUrl", String).replace(/\/+$/, "");
  const payload = getPayload();
  summary.textContent = "Running inference...";

  try {
    const res = await fetch(`${baseUrl}/api/v1/infer`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`API ${res.status}: ${text}`);
    }
    const data = await res.json();
    renderResult(data);
  } catch (err) {
    summary.textContent = `Error: ${err.message}`;
    bars.innerHTML = "";
    recommendationsEl.innerHTML = "";
    factorsEl.innerHTML = "";
    explanationEl.textContent = "";
  }
}

form.addEventListener("submit", runInference);

