const apiBaseUrl = "http://127.0.0.1:8000";
const apiKey = "dev-admin-key";
const role = "admin";
const indiaGeoJsonUrl = "https://cdn.jsdelivr.net/npm/world-geojson@3.4.0/countries/india.json";
const HEATMAP_CITY_LIMIT = 40;
const fallbackIndiaPolygons = [
  [
    [
      [68.1, 23.9],
      [68.7, 22.2],
      [69.2, 20.6],
      [69.9, 18.8],
      [70.8, 17.2],
      [71.8, 15.2],
      [72.6, 13.5],
      [73.3, 11.9],
      [74.2, 10.1],
      [75.2, 8.7],
      [76.7, 8.2],
      [78.4, 8.7],
      [79.9, 10.1],
      [81.1, 12.4],
      [82.2, 15.1],
      [83.3, 17.8],
      [84.6, 19.9],
      [86.0, 21.5],
      [87.4, 22.4],
      [88.7, 22.7],
      [90.0, 23.5],
      [91.6, 24.4],
      [93.2, 25.7],
      [94.2, 27.1],
      [93.5, 28.0],
      [92.0, 27.6],
      [90.4, 26.8],
      [88.5, 26.0],
      [86.6, 26.3],
      [84.7, 27.2],
      [82.7, 28.7],
      [80.6, 30.8],
      [78.4, 32.8],
      [76.1, 34.2],
      [74.4, 35.2],
      [73.3, 34.5],
      [74.2, 33.0],
      [76.2, 31.5],
      [78.3, 30.2],
      [80.3, 28.6],
      [81.9, 27.2],
      [81.5, 26.0],
      [80.0, 24.7],
      [78.5, 23.2],
      [77.2, 21.4],
      [76.0, 19.4],
      [75.0, 17.1],
      [74.0, 14.5],
      [72.9, 12.2],
      [72.0, 10.6],
      [71.2, 12.9],
      [70.6, 15.6],
      [70.0, 18.4],
      [69.3, 20.9],
      [68.6, 22.8],
      [68.1, 23.9],
    ],
  ],
];

const cities = [
  "New Delhi",
  "Mumbai",
  "Bengaluru",
  "Chennai",
  "Hyderabad",
  "Kolkata",
  "Pune",
  "Ahmedabad",
  "Jaipur",
  "Lucknow",
  "Kanpur",
  "Nagpur",
  "Indore",
  "Bhopal",
  "Patna",
  "Surat",
  "Vadodara",
  "Coimbatore",
  "Kochi",
  "Goa",
  "Shimla",
  "Leh",
];

const cityGeo = {
  "New Delhi": { lat: 28.6139, lon: 77.209 },
  Mumbai: { lat: 19.076, lon: 72.8777 },
  Bengaluru: { lat: 12.9716, lon: 77.5946 },
  Chennai: { lat: 13.0827, lon: 80.2707 },
  Hyderabad: { lat: 17.385, lon: 78.4867 },
  Kolkata: { lat: 22.5726, lon: 88.3639 },
  Pune: { lat: 18.5204, lon: 73.8567 },
  Ahmedabad: { lat: 23.0225, lon: 72.5714 },
  Jaipur: { lat: 26.9124, lon: 75.7873 },
  Lucknow: { lat: 26.8467, lon: 80.9462 },
  Kanpur: { lat: 26.4499, lon: 80.3319 },
  Nagpur: { lat: 21.1458, lon: 79.0882 },
  Indore: { lat: 22.7196, lon: 75.8577 },
  Bhopal: { lat: 23.2599, lon: 77.4126 },
  Patna: { lat: 25.5941, lon: 85.1376 },
  Surat: { lat: 21.1702, lon: 72.8311 },
  Vadodara: { lat: 22.3072, lon: 73.1812 },
  Coimbatore: { lat: 11.0168, lon: 76.9558 },
  Kochi: { lat: 9.9312, lon: 76.2673 },
  Goa: { lat: 15.2993, lon: 74.124 },
  Shimla: { lat: 31.1048, lon: 77.1734 },
  Leh: { lat: 34.1526, lon: 77.5771 },
};

const $ = (id) => document.getElementById(id);
const SVG_WIDTH = 420;
const SVG_HEIGHT = 520;
let mapProjection = null;
let lastForecast = null;
let lastHeatmapItems = [];
let hasIndiaBoundary = false;

function headers() {
  return {
    "Content-Type": "application/json",
    "x-api-key": apiKey,
    "x-role": role,
  };
}

async function apiGet(path) {
  const res = await fetch(`${apiBaseUrl}${path}`, { headers: headers() });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

async function apiPost(path, body) {
  const res = await fetch(`${apiBaseUrl}${path}`, {
    method: "POST",
    headers: headers(),
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

function initCities() {
  const select = $("location");
  select.innerHTML = cities.map((c) => `<option value="${c}">${c}</option>`).join("");
  select.value = "New Delhi";
}

function ensureFallbackProjection() {
  if (mapProjection) return;
  const coords = Object.values(cityGeo);
  if (!coords.length) return;
  let minLon = Number.POSITIVE_INFINITY;
  let maxLon = Number.NEGATIVE_INFINITY;
  let minLat = Number.POSITIVE_INFINITY;
  let maxLat = Number.NEGATIVE_INFINITY;
  for (const point of coords) {
    minLon = Math.min(minLon, point.lon);
    maxLon = Math.max(maxLon, point.lon);
    minLat = Math.min(minLat, point.lat);
    maxLat = Math.max(maxLat, point.lat);
  }
  const lonSpan = maxLon - minLon;
  const latSpan = maxLat - minLat;
  const pad = 18;
  const scale = Math.min((SVG_WIDTH - pad * 2) / lonSpan, (SVG_HEIGHT - pad * 2) / latSpan);
  const xPad = (SVG_WIDTH - lonSpan * scale) / 2;
  const yPad = (SVG_HEIGHT - latSpan * scale) / 2;
  mapProjection = { minLon, maxLon, minLat, maxLat, scale, xPad, yPad };
}

function setFullClipPath() {
  $("india-heat-clip-paths").innerHTML = '<rect x="0" y="0" width="420" height="520"></rect>';
}

function setStatus(txt) {
  $("status").textContent = txt;
}

function clamp01(value) {
  const n = Number(value);
  if (!Number.isFinite(n)) return 0;
  return Math.max(0, Math.min(1, n));
}

function emptyState(message) {
  return `<div class="empty-state">${message}</div>`;
}

function pct(v) {
  return `${Math.round(clamp01(v) * 100)}%`;
}

function payload() {
  const temp = Number($("temperature_c").value);
  const humidity = Number($("humidity_pct").value);
  const cloud = Number($("cloud_cover_pct").value);
  const wind = Number($("wind_kph").value);
  const dew = Math.max(0, Math.round(temp - (100 - humidity) / 5));
  const now = new Date();
  const month = now.getMonth() + 1;
  const hour = now.getHours();
  const season = month >= 6 && month <= 9 ? "monsoon" : month <= 2 ? "winter" : month <= 4 ? "spring" : month <= 5 ? "summer" : "autumn";

  return {
    location: $("location").value,
    risk_mode: $("risk_mode").value,
    horizon_hours: Number($("horizon_hours").value),
    custom_thresholds: {},
    observation: {
      temperature_c: temp,
      humidity_pct: humidity,
      pressure_hpa: Math.max(980, Math.round(1014 - cloud / 6)),
      wind_kph: wind,
      cloud_cover_pct: cloud,
      dew_point_c: dew,
      recent_rain_mm: Math.max(0, Math.round((humidity + cloud - 135) / 8)),
      uv_index: Math.max(1, Math.round((100 - cloud) / 13)),
      visibility_km: Math.max(2, Math.round((110 - cloud) / 10)),
      month,
      hour_24: hour,
      season,
      terrain: "urban",
      pressure_trend: $("pressure_trend").value,
      source_confidence: {
        manual: 0.8,
        station: 0.86,
        satellite: 0.83,
        radar: 0.88,
        model: 0.8,
      },
    },
  };
}

function renderBars(items) {
  $("probability-bars").innerHTML = items
    .map(
      (item) => `
      <div class="bar">
        <div class="bar-top"><span>${item.condition}</span><span>${pct(item.probability)}</span></div>
        <div class="track"><div class="fill" style="width:${pct(item.probability)}"></div></div>
      </div>
    `
    )
    .join("");
}

function renderChips(targetId, obj) {
  $(targetId).innerHTML = Object.entries(obj)
    .map(([k, v]) => `<span class="chip">${k}: ${pct(v)}</span>`)
    .join("");
}

function renderList(targetId, list, mapFn) {
  $(targetId).innerHTML = list.map((x) => `<li>${mapFn(x)}</li>`).join("");
}

function renderMain(data) {
  lastForecast = data;
  $("headline").textContent = `${data.location}: ${data.predicted_condition.toUpperCase()} (${data.alert_level})`;
  $("quick").innerHTML = `
    <span class="chip">Rain ${pct(data.rain_probability)}</span>
    <span class="chip">Rainfall ${data.expected_rainfall_mm} mm</span>
    <span class="chip">Confidence ${pct(data.confidence_score)}</span>
    <span class="chip">Mode ${data.risk_mode}</span>
    <span class="chip">Climatology Blend ${pct(data.climatology_meta.blend_alpha)}</span>
  `;

  renderBars(data.condition_probabilities);
  renderChips("bands", data.intensity_bands);
  renderChips("events", data.event_probabilities);
  $("scenarios").innerHTML = data.scenarios
    .map((s) => `<div class="chip">${s.label}: ${pct(s.rain_probability)} | ${s.expected_rainfall_mm} mm</div>`)
    .join("");
  $("horizons").innerHTML = data.horizons
    .map((h) => `<span class="chip">${h.horizon_hours}h ${h.predicted_condition} (${pct(h.rain_probability)})</span>`)
    .join("");
  $("quality").innerHTML = `
    <div class="chip">Sensor Reliability: ${pct(data.data_quality.sensor_reliability)}</div>
    <div class="chip">Uncertainty Penalty: ${pct(data.data_quality.uncertainty_penalty)}</div>
    <div class="chip">Imputed: ${
      data.data_quality.imputed_fields.length ? data.data_quality.imputed_fields.join(", ") : "none"
    }</div>
  `;
  renderList("recommendations", data.expert_recommendations, (x) => x);
  renderList("counterfactuals", data.counterfactuals, (x) => `${x.change} -> ${pct(x.impact_on_rain_probability)}`);
  renderList("rule-trace", data.rule_trace, (x) => `${x.condition}: ${x.reason}`);
  renderList("attribution", data.feature_attributions, (x) => `${x.factor} (${x.direction}, ${x.impact})`);
}

function heatColor(prob) {
  const p = clamp01(prob);
  if (p < 0.25) return "#45b36a";
  if (p < 0.45) return "#d2a500";
  if (p < 0.65) return "#d08b00";
  if (p < 0.8) return "#c05f00";
  return "#b00020";
}

function distanceBetweenCities(sourceCity, targetCity) {
  const source = cityGeo[sourceCity];
  const target = cityGeo[targetCity];
  if (!source || !target) return Number.POSITIVE_INFINITY;
  const dx = source.lon - target.lon;
  const dy = source.lat - target.lat;
  return dx * dx + dy * dy;
}

function buildHeatmapLocations(selectedCity) {
  const uniqueCities = Array.from(new Set(cities.filter((city) => cityGeo[city])));
  if (!uniqueCities.length) return [];
  if (!selectedCity || !cityGeo[selectedCity]) return uniqueCities.slice(0, HEATMAP_CITY_LIMIT);
  return [selectedCity, ...uniqueCities.filter((city) => city !== selectedCity).sort((a, b) => distanceBetweenCities(selectedCity, a) - distanceBetweenCities(selectedCity, b))].slice(
    0,
    HEATMAP_CITY_LIMIT
  );
}

function renderHeatmap(items, selectedCity = $("location").value) {
  if (!items.length) {
    $("heatmap").innerHTML = '<div class="heatmap-empty">Run a forecast to populate the city rain heatmap.</div>';
    return;
  }

  $("heatmap").innerHTML = items
    .map(
      (item) => `
      <div class="heat-cell ${item.location === selectedCity ? "active" : ""}" style="background:${heatColor(item.rain_probability)}">
        ${item.location}
        <small>${pct(item.rain_probability)} rain | ${item.predicted_condition} | ${item.alert_level}</small>
      </div>
    `
    )
    .join("");
}

async function loadForecastHeatmaps(basePayload) {
  const selectedCity = basePayload.location || $("location").value;
  const locations = buildHeatmapLocations(selectedCity);
  if (!locations.length) {
    lastHeatmapItems = [];
    renderHeatmap([], selectedCity);
    renderSpatialHeat([], selectedCity);
    return { count: 0, items: [] };
  }

  const data = await apiPost("/api/v1/infer/multi-location", {
    locations,
    observation: basePayload.observation,
    horizon_hours: basePayload.horizon_hours,
    risk_mode: basePayload.risk_mode,
  });
  const items = Array.isArray(data.items) ? data.items : [];
  lastHeatmapItems = items;
  renderHeatmap(items, selectedCity);
  renderSpatialHeat(items, selectedCity);
  return { count: items.length, items };
}

async function runForecast() {
  const basePayload = payload();
  setStatus(`Running forecast for ${basePayload.location}...`);
  const [forecastResult, heatmapResult] = await Promise.allSettled([
    apiPost("/api/v1/infer", basePayload),
    loadForecastHeatmaps(basePayload),
  ]);

  if (forecastResult.status === "rejected") {
    setStatus(`Forecast failed: ${forecastResult.reason.message}`);
    return;
  }

  renderMain(forecastResult.value);

  if (heatmapResult.status === "fulfilled") {
    const label = heatmapResult.value.count === 1 ? "city" : "cities";
    setStatus(`Forecast ready. Heatmaps updated for ${heatmapResult.value.count} ${label}.`);
    return;
  }

  lastHeatmapItems = [];
  renderHeatmap([], basePayload.location);
  renderSpatialHeat([], basePayload.location);
  setStatus(`Forecast ready, but heatmap update failed: ${heatmapResult.reason.message}`);
}

async function runHeatmap() {
  const basePayload = payload();
  setStatus(`Running heatmaps for ${basePayload.location}...`);
  try {
    const data = await loadForecastHeatmaps(basePayload);
    setStatus(`Heatmap ready for ${data.count} cities.`);
  } catch (error) {
    setStatus(`Heatmap failed: ${error.message}`);
  }
}

async function useLiveWeather() {
  setStatus("Fetching live weather...");
  try {
    const city = $("location").value;
    const geo = cityGeo[city];
    if (!geo) throw new Error("Missing city coordinates");
    const provider = $("live_provider").value;
    const data = await apiGet(`/api/v1/live-weather?lat=${geo.lat}&lon=${geo.lon}&provider=${provider}`);
    $("temperature_c").value = Number(data.temperature_c).toFixed(1);
    $("humidity_pct").value = Math.round(Number(data.humidity_pct));
    $("cloud_cover_pct").value = Math.round(Number(data.cloud_cover_pct));
    $("wind_kph").value = Number(data.wind_kph).toFixed(1);
    setStatus(`Live weather loaded from ${data.provider} (${data.source}).`);
  } catch (error) {
    setStatus(`Live weather failed: ${error.message}`);
  }
}

async function submitOutcome() {
  if (!lastForecast) {
    setStatus("Run a forecast before submitting outcome.");
    return;
  }
  setStatus("Submitting outcome...");
  try {
    const data = await apiPost("/api/v1/outcome", {
      location: lastForecast.location,
      risk_mode: lastForecast.risk_mode,
      horizon_hours: Number(lastForecast.horizon_hours),
      predicted_rain_probability: Number(lastForecast.rain_probability),
      actual_condition: $("actual_condition").value,
      actual_rain_mm: Number($("actual_rain_mm").value),
    });
    $("calibration-view").innerHTML = `<div class="chip">Brier score recorded: ${data.brier_score}</div>`;
    setStatus(`Outcome submitted for ${lastForecast.location}.`);
  } catch (error) {
    setStatus(`Outcome submit failed: ${error.message}`);
  }
}

async function loadCalibration() {
  setStatus("Loading calibration...");
  try {
    const data = await apiGet(`/api/v1/calibration?location=${encodeURIComponent($("location").value)}`);
    if (!data.overall.sample_count) {
      $("calibration-view").innerHTML = emptyState(`No calibration samples recorded yet for ${$("location").value}.`);
      setStatus("Calibration loaded.");
      return;
    }
    const bins = (data.reliability_bins || [])
      .map((b) => `<div class="chip">bin ${b.prob_bin / 10}-${(b.prob_bin + 1) / 10}: obs ${pct(b.observed_rain_frequency)}</div>`)
      .join("");
    $("calibration-view").innerHTML = `
      <div class="chip">Samples: ${data.overall.sample_count}</div>
      <div class="chip">Avg Brier: ${data.overall.avg_brier_score}</div>
      <div class="chip">Avg Abs Error: ${data.overall.avg_absolute_error}</div>
      ${bins}
    `;
    setStatus("Calibration loaded.");
  } catch (error) {
    setStatus(`Calibration failed: ${error.message}`);
  }
}

async function loadHistory() {
  setStatus("Loading history...");
  try {
    const data = await apiGet(`/api/v1/history?limit=20&location=${encodeURIComponent($("location").value)}`);
    if (!(data.items || []).length) {
      $("history-view").innerHTML = emptyState(`No forecast history found yet for ${$("location").value}.`);
      setStatus("History loaded.");
      return;
    }
    $("history-view").innerHTML = data.items
      .map((item) => `<div class="chip">${item.timestamp_utc.slice(0, 16)} | ${item.predicted_condition} | rain ${pct(item.rain_probability)} | ${item.alert_level}</div>`)
      .join("");
    setStatus("History loaded.");
  } catch (error) {
    setStatus(`History failed: ${error.message}`);
  }
}

async function loadAnalytics() {
  setStatus("Loading analytics...");
  try {
    const data = await apiGet(`/api/v1/history/analytics?location=${encodeURIComponent($("location").value)}`);
    if (!data.summary.total_forecasts) {
      $("analytics-view").innerHTML = emptyState(`No analytics are available yet for ${$("location").value}.`);
      setStatus("Analytics loaded.");
      return;
    }
    $("analytics-view").innerHTML = `
      <div class="chip">Total forecasts: ${data.summary.total_forecasts}</div>
      <div class="chip">Avg rain prob: ${pct(data.summary.avg_rain_probability)}</div>
      <div class="chip">High alert ratio: ${pct(data.summary.high_alert_ratio)}</div>
      ${(data.by_location || []).slice(0, 4).map((item) => `<div class="chip">${item.location}: ${item.count} runs | avg ${pct(item.avg_rain_probability)}</div>`).join("")}
      ${data.timeline
        .slice(0, 8)
        .map((d) => `<div class="chip">${d.date}: ${d.count} runs | severe ${d.severe_count}</div>`)
        .join("")}
    `;
    setStatus("Analytics loaded.");
  } catch (error) {
    setStatus(`Analytics failed: ${error.message}`);
  }
}

async function createSubscription() {
  setStatus("Creating subscription...");
  try {
    const data = await apiPost("/api/v1/alerts/subscriptions", {
      name: $("sub_name").value,
      channel: $("sub_channel").value,
      target: $("sub_target").value,
      location: $("location").value,
      risk_mode: $("risk_mode").value,
      min_rain_probability: Number($("sub_prob").value),
      min_alert_level: $("sub_alert").value,
      enabled: true,
    });
    setStatus(`Subscription created: ${data.id}`);
    await loadSubscriptions();
  } catch (error) {
    setStatus(`Create subscription failed: ${error.message}`);
  }
}

async function loadSubscriptions() {
  setStatus("Loading subscriptions...");
  try {
    const data = await apiGet("/api/v1/alerts/subscriptions?all=true");
    if (!data.items.length) {
      $("subscriptions-view").innerHTML = emptyState("No alert subscriptions created yet.");
      setStatus("Subscriptions loaded.");
      return;
    }
    $("subscriptions-view").innerHTML = data.items
      .map(
        (item) =>
          `<div class="chip">#${item.id} ${item.name} | ${item.channel} | ${item.location} | p>=${item.min_rain_probability} | ${
            item.enabled ? "enabled" : "disabled"
          } <button class="mini" data-sub-toggle="${item.id}" data-sub-enabled="${item.enabled ? "false" : "true"}">${
            item.enabled ? "Disable" : "Enable"
          }</button></div>`
      )
      .join("");
    setStatus("Subscriptions loaded.");
  } catch (error) {
    setStatus(`Subscriptions failed: ${error.message}`);
  }
}

async function loadNotifications() {
  setStatus("Loading notifications...");
  try {
    const data = await apiGet("/api/v1/alerts/notifications?limit=30");
    if (!data.items.length) {
      $("notifications-view").innerHTML = emptyState("No notifications have been logged yet.");
      setStatus("Notifications loaded.");
      return;
    }
    $("notifications-view").innerHTML = data.items
      .map((item) => `<div class="chip">${item.timestamp_utc.slice(0, 16)} | sub#${item.subscription_id} | ${item.delivery_status}</div>`)
      .join("");
    setStatus("Notifications loaded.");
  } catch (error) {
    setStatus(`Notifications failed: ${error.message}`);
  }
}

async function loadDatasetStats() {
  setStatus("Loading dataset stats...");
  try {
    const data = await apiGet("/api/v1/dataset/stats");
    $("dataset-view").innerHTML = `
      <div class="chip">Rows: ${data.rows}</div>
      <div class="chip">Cities: ${data.cities}</div>
      <div class="chip">Climate zones: ${data.climate_zones}</div>
      <div class="chip">Years: ${data.year_range[0]}-${data.year_range[1]}</div>
      <div class="chip">Records per row: ${data.records_per_row}</div>
      <div class="empty-state">${data.notes}</div>
    `;
    setStatus("Dataset stats loaded.");
  } catch (error) {
    setStatus(`Dataset stats failed: ${error.message}`);
  }
}

async function listKbVersions() {
  setStatus("Loading KB versions...");
  try {
    const data = await apiGet("/api/v1/knowledge-base/versions");
    if (!data.items.length) {
      $("kb-view").innerHTML = emptyState("No knowledge-base snapshots have been created yet.");
      setStatus("KB versions loaded.");
      return;
    }
    $("kb-view").innerHTML = data.items
      .map(
        (item) =>
          `<div class="chip">#${item.id} ${item.version_name} ${item.is_active ? "(active)" : ""} <button class="mini" data-kb-activate="${
            item.id
          }">Activate</button></div>`
      )
      .join("");
    setStatus("KB versions loaded.");
  } catch (error) {
    setStatus(`KB versions failed: ${error.message}`);
  }
}

async function createKbVersion() {
  setStatus("Creating KB snapshot...");
  try {
    await apiPost("/api/v1/knowledge-base/versions", {
      version_name: $("kb_version_name").value,
      notes: $("kb_notes").value,
      activate: false,
    });
    setStatus("KB snapshot created.");
    await listKbVersions();
  } catch (error) {
    setStatus(`Create KB snapshot failed: ${error.message}`);
  }
}

async function activateKbVersion(versionId) {
  setStatus(`Activating KB version ${versionId}...`);
  try {
    await apiPost(`/api/v1/knowledge-base/versions/${versionId}/activate`, {});
    setStatus(`KB version ${versionId} activated.`);
    await listKbVersions();
  } catch (error) {
    setStatus(`Activate KB version failed: ${error.message}`);
  }
}

async function runBatchJob() {
  setStatus("Starting batch job...");
  try {
    const data = await apiPost("/api/v1/jobs/forecast-batch", {
      locations: cities,
      observation: payload().observation,
      horizon_hours: Number($("horizon_hours").value),
      risk_mode: $("risk_mode").value,
      custom_thresholds: {},
    });
    const detail = await pollBatchJob(data.job_id);
    if (detail.status === "failed") {
      setStatus(`Batch job ${detail.job_id.slice(0, 8)} failed: ${detail.error || "unknown error"}`);
    } else if (detail.status === "completed") {
      setStatus(`Batch job ${detail.job_id.slice(0, 8)} completed for ${detail.done} cities.`);
    } else {
      setStatus(`Batch job ${data.job_id} started.`);
    }
    await loadBatchJobs(data.job_id);
  } catch (error) {
    setStatus(`Batch job failed: ${error.message}`);
  }
}

function renderBatchJobDetail(job) {
  if (!job) return "";
  const items = job.items || [];
  const meta = [
    `<div class="chip">Job ${job.job_id.slice(0, 8)}</div>`,
    `<div class="chip">Status: ${job.status}</div>`,
    `<div class="chip">Progress: ${job.done}/${job.total}</div>`,
  ];
  if (job.completed_utc) meta.push(`<div class="chip">Completed: ${job.completed_utc.slice(0, 16)}</div>`);
  if (job.error) meta.push(`<div class="chip">Error: ${job.error}</div>`);

  const resultHtml = items.length
    ? items
        .slice(0, 12)
        .map(
          (item) =>
            `<div class="chip">${item.location} | ${item.predicted_condition} | rain ${pct(item.rain_probability)} | ${item.alert_level}</div>`
        )
        .join("")
    : emptyState("No per-city results are available for this batch job yet.");

  return `
    <div class="batch-job-card">
      <div class="chips">${meta.join("")}</div>
      <div class="stack batch-results">${resultHtml}</div>
    </div>
  `;
}

async function pollBatchJob(jobId, maxAttempts = 80, delayMs = 250) {
  let detail = null;
  for (let attempt = 0; attempt < maxAttempts; attempt += 1) {
    detail = await apiGet(`/api/v1/jobs/forecast-batch/${jobId}`);
    $("batch-view").innerHTML = renderBatchJobDetail(detail);
    if (detail.status === "completed" || detail.status === "failed") {
      return detail;
    }
    await new Promise((resolve) => setTimeout(resolve, delayMs));
  }
  return detail || (await apiGet(`/api/v1/jobs/forecast-batch/${jobId}`));
}

async function loadBatchJobs(focusJobId = null) {
  setStatus("Loading batch jobs...");
  try {
    const data = await apiGet("/api/v1/jobs/forecast-batch?limit=12");
    if (!data.items.length) {
      $("batch-view").innerHTML = emptyState("No batch jobs have been started yet.");
      setStatus("Batch jobs loaded.");
      return;
    }
    let detail = null;
    const selectedJobId = focusJobId || data.items[0]?.job_id;
    if (selectedJobId) {
      try {
        detail = await apiGet(`/api/v1/jobs/forecast-batch/${selectedJobId}`);
      } catch (error) {
        detail = null;
      }
    }
    const listHtml = data.items
      .map((job) => {
        const errorText = job.error ? ` | error ${job.error}` : "";
        return `<div class="chip">${job.job_id.slice(0, 8)} | ${job.status} | ${job.done}/${job.total}${errorText}</div>`;
      })
      .join("");
    $("batch-view").innerHTML = `<div class="stack">${listHtml}</div>${renderBatchJobDetail(detail)}`;
    setStatus("Batch jobs loaded.");
  } catch (error) {
    setStatus(`Batch jobs failed: ${error.message}`);
  }
}

function projectLonLat(lon, lat) {
  if (!mapProjection) return null;
  const { minLon, maxLat, scale, xPad, yPad } = mapProjection;
  const x = (lon - minLon) * scale + xPad;
  const y = (maxLat - lat) * scale + yPad;
  return { x, y, xPct: (x / SVG_WIDTH) * 100, yPct: (y / SVG_HEIGHT) * 100 };
}

function ringsFromGeometry(geometry) {
  if (!geometry) return [];
  if (geometry.type === "Polygon") return [geometry.coordinates];
  if (geometry.type === "MultiPolygon") return geometry.coordinates;
  return [];
}

function computeProjection(polygons) {
  let minLon = Number.POSITIVE_INFINITY;
  let maxLon = Number.NEGATIVE_INFINITY;
  let minLat = Number.POSITIVE_INFINITY;
  let maxLat = Number.NEGATIVE_INFINITY;

  for (const polygon of polygons) {
    for (const ring of polygon) {
      for (const point of ring) {
        const [lon, lat] = point;
        minLon = Math.min(minLon, lon);
        maxLon = Math.max(maxLon, lon);
        minLat = Math.min(minLat, lat);
        maxLat = Math.max(maxLat, lat);
      }
    }
  }

  const lonSpan = maxLon - minLon;
  const latSpan = maxLat - minLat;
  const pad = 16;
  const scale = Math.min((SVG_WIDTH - pad * 2) / lonSpan, (SVG_HEIGHT - pad * 2) / latSpan);
  const xPad = (SVG_WIDTH - lonSpan * scale) / 2;
  const yPad = (SVG_HEIGHT - latSpan * scale) / 2;

  return { minLon, maxLon, minLat, maxLat, scale, xPad, yPad };
}

function renderIndiaBoundary(polygons) {
  mapProjection = computeProjection(polygons);
  const paths = polygons
    .map((polygon) => {
      const d = polygon.map((ring) => ringToPath(ring)).join(" ");
      return `<path class="india-shape" d="${d}" />`;
    })
    .join("");
  hasIndiaBoundary = true;
  $("india-geo-layer").innerHTML = paths;
  $("india-heat-geo-layer").innerHTML = paths;
  $("india-heat-clip-paths").innerHTML = paths;
}

function ringToPath(ring) {
  if (!ring.length) return "";
  const first = projectLonLat(ring[0][0], ring[0][1]);
  let d = `M ${first.x.toFixed(2)} ${first.y.toFixed(2)}`;
  for (let i = 1; i < ring.length; i += 1) {
    const p = projectLonLat(ring[i][0], ring[i][1]);
    d += ` L ${p.x.toFixed(2)} ${p.y.toFixed(2)}`;
  }
  return `${d} Z`;
}

async function loadIndiaBoundary() {
  try {
    const res = await fetch(indiaGeoJsonUrl);
    if (!res.ok) throw new Error(`boundary fetch failed (${res.status})`);
    const geo = await res.json();
    const feature = geo?.type === "FeatureCollection" ? geo.features?.[0] : geo;
    const polygons = ringsFromGeometry(feature?.geometry);
    if (!polygons.length) throw new Error("boundary data empty");
    renderIndiaBoundary(polygons);
  } catch (error) {
    renderIndiaBoundary(fallbackIndiaPolygons);
  }
  if (lastHeatmapItems.length) {
    renderSpatialHeat(lastHeatmapItems);
  }
}

function renderMapMarkers() {
  const wrap = $("india-map-markers");
  if (!mapProjection) {
    wrap.innerHTML = "";
    return;
  }

  wrap.innerHTML = cities
    .filter((city) => cityGeo[city])
    .map((city) => {
      const point = projectLonLat(cityGeo[city].lon, cityGeo[city].lat);
      const isActive = city === $("location").value;
      return `<span class="map-dot ${isActive ? "active" : ""}" style="left:${point.xPct}%;top:${point.yPct}%" title="${city}"></span>`;
    })
    .join("");

  $("map-selected").textContent = `Selected city: ${$("location").value}`;
}

function nearestCityFromPercent(x, y) {
  let best = cities[0];
  let bestDist = Number.POSITIVE_INFINITY;
  for (const city of cities) {
    const geo = cityGeo[city];
    if (!geo) continue;
    const p = projectLonLat(geo.lon, geo.lat);
    if (!p) continue;
    const dx = x - p.xPct;
    const dy = y - p.yPct;
    const d = dx * dx + dy * dy;
    if (d < bestDist) {
      bestDist = d;
      best = city;
    }
  }
  return best;
}

function selectCity(city) {
  if (!cities.includes(city)) return;
  $("location").value = city;
  renderMapMarkers();
}

function lerp(a, b, t) {
  return Math.round(a + (b - a) * t);
}

function heatScaleRgb(prob) {
  const p = clamp01(prob);
  if (p <= 0.5) {
    const t = p / 0.5;
    return { r: lerp(34, 255, t), g: lerp(197, 214, t), b: lerp(94, 10, t) };
  }
  const t = (p - 0.5) / 0.5;
  return { r: lerp(255, 216, t), g: lerp(214, 0, t), b: lerp(10, 0, t) };
}

function rgbToCss(rgb, alpha) {
  return `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, ${alpha})`;
}

function renderSpatialHeat(items, selectedCity = $("location").value) {
  ensureFallbackProjection();
  if (!mapProjection) {
    $("map-heat-info").textContent = "Heatmap projection is unavailable.";
    return;
  }
  const surfaceLayer = $("india-heat-surface");
  const blurLayer = $("india-heat-spots");
  const coreLayer = $("india-heat-spots-core");
  surfaceLayer.innerHTML = "";
  blurLayer.innerHTML = "";
  coreLayer.innerHTML = "";

  const validItems = items.filter((item) => cityGeo[item.location] && Number.isFinite(Number(item.rain_probability)));
  if (!validItems.length) {
    $("map-heat-info").textContent = "Run a forecast to populate the India spatial heatmap.";
    return;
  }

  const projected = validItems.map((item) => {
    const p = projectLonLat(cityGeo[item.location].lon, cityGeo[item.location].lat);
    return { x: p.x, y: p.y, w: clamp01(item.rain_probability) };
  });

  if (!hasIndiaBoundary) {
    setFullClipPath();
  }

  const sigma = 52;
  const sigma2 = sigma * sigma;
  const grid = 4;
  const densityReference = 0.9;
  const cells = [];

  for (let y = 0; y < SVG_HEIGHT; y += grid) {
    for (let x = 0; x < SVG_WIDTH; x += grid) {
      const cx = x + grid / 2;
      const cy = y + grid / 2;
      let weightedProb = 0;
      let weightTotal = 0;
      for (const point of projected) {
        const dx = cx - point.x;
        const dy = cy - point.y;
        const d2 = dx * dx + dy * dy;
        const influence = Math.exp(-d2 / (2 * sigma2));
        weightedProb += point.w * influence;
        weightTotal += influence;
      }
      const localProbability = weightTotal > 0 ? weightedProb / weightTotal : 0;
      const density = Math.min(1, weightTotal / densityReference);
      cells.push({ x, y, v: localProbability * density });
    }
  }

  surfaceLayer.innerHTML = cells
    .map((cell) => {
      const norm = clamp01(cell.v);
      if (norm < 0.08) return "";
      const rgb = heatScaleRgb(norm);
      const alpha = 0.04 + Math.pow(norm, 1.2) * 0.76;
      return `<rect x="${cell.x}" y="${cell.y}" width="${grid}" height="${grid}" fill="${rgbToCss(rgb, alpha)}"></rect>`;
    })
    .join("");

  blurLayer.innerHTML = validItems
    .map((item) => {
      const p = projectLonLat(cityGeo[item.location].lon, cityGeo[item.location].lat);
      const pr = clamp01(item.rain_probability);
      const rgb = heatScaleRgb(pr);
      const radius = 18 + pr * 26;
      return `<circle cx="${p.x.toFixed(2)}" cy="${p.y.toFixed(2)}" r="${radius.toFixed(2)}" fill="${rgbToCss(rgb, 0.5)}"></circle>`;
    })
    .join("");

  coreLayer.innerHTML = validItems
    .map((item) => {
      const p = projectLonLat(cityGeo[item.location].lon, cityGeo[item.location].lat);
      const pr = clamp01(item.rain_probability);
      const rgb = heatScaleRgb(pr);
      const radius = 3.5 + pr * 6.2;
      return `<circle cx="${p.x.toFixed(2)}" cy="${p.y.toFixed(2)}" r="${radius.toFixed(2)}" fill="${rgbToCss(rgb, 0.95)}"></circle>`;
    })
    .join("");

  const peak = validItems.reduce((best, item) => (clamp01(item.rain_probability) > clamp01(best.rain_probability) ? item : best), validItems[0]);
  $("map-heat-info").textContent = `Spatial heatmap for ${selectedCity}. Peak rain signal: ${peak.location} ${pct(peak.rain_probability)}.`;
}

function renderRestoreButtons() {
  const wrap = $("panel-restores");
  const hiddenPanels = Array.from(document.querySelectorAll(".heat-panel.hidden-panel"));
  if (!hiddenPanels.length) {
    wrap.innerHTML = "";
    return;
  }
  wrap.innerHTML = hiddenPanels
    .map((panel) => {
      const title = panel.querySelector("h2")?.textContent || "Panel";
      return `<button class="mini" data-panel-restore="${panel.id}" type="button">Restore ${title}</button>`;
    })
    .join("");
}

function handlePanelAction(action, panelId) {
  const panel = document.getElementById(panelId);
  if (!panel) return;
  if (action === "minimize") {
    panel.classList.toggle("minimized");
  } else if (action === "close") {
    panel.classList.add("hidden-panel");
  }
  renderRestoreButtons();
}

function openMapSidebar() {
  renderMapMarkers();
  $("map-sidebar").classList.add("open");
  $("map-backdrop").classList.add("open");
  $("map-sidebar").setAttribute("aria-hidden", "false");
}

function closeMapSidebar() {
  $("map-sidebar").classList.remove("open");
  $("map-backdrop").classList.remove("open");
  $("map-sidebar").setAttribute("aria-hidden", "true");
}

initCities();
setFullClipPath();
renderHeatmap([]);
renderSpatialHeat([]);
loadIndiaBoundary().then(renderMapMarkers);

$("run").addEventListener("click", runForecast);
$("run-multi").addEventListener("click", runHeatmap);
$("fetch-live").addEventListener("click", useLiveWeather);
$("run-batch").addEventListener("click", runBatchJob);

$("submit-outcome").addEventListener("click", submitOutcome);
$("load-calibration").addEventListener("click", loadCalibration);
$("load-history").addEventListener("click", loadHistory);
$("load-analytics").addEventListener("click", loadAnalytics);
$("create-subscription").addEventListener("click", createSubscription);
$("load-subscriptions").addEventListener("click", loadSubscriptions);
$("load-notifications").addEventListener("click", loadNotifications);
$("dataset-stats").addEventListener("click", loadDatasetStats);
$("list-kb-versions").addEventListener("click", listKbVersions);
$("create-kb-version").addEventListener("click", createKbVersion);
$("list-batch-jobs").addEventListener("click", loadBatchJobs);
document.addEventListener("click", (event) => {
  const target = event.target;
  if (!(target instanceof Element)) return;
  const panelAction = target.getAttribute("data-panel-action");
  const panelId = target.getAttribute("data-panel-id");
  if (panelAction && panelId) {
    handlePanelAction(panelAction, panelId);
    return;
  }
  const restoreId = target.getAttribute("data-panel-restore");
  if (restoreId) {
    const panel = document.getElementById(restoreId);
    if (!panel) return;
    panel.classList.remove("hidden-panel");
    panel.classList.remove("minimized");
    renderRestoreButtons();
  }
});

$("subscriptions-view").addEventListener("click", async (event) => {
  const target = event.target;
  const subId = target.getAttribute("data-sub-toggle");
  if (!subId) return;
  const nextEnabled = target.getAttribute("data-sub-enabled") === "true";
  try {
    await apiPost(`/api/v1/alerts/subscriptions/${subId}/toggle?enabled=${nextEnabled}`, {});
    await loadSubscriptions();
  } catch (error) {
    setStatus(`Subscription toggle failed: ${error.message}`);
  }
});

$("kb-view").addEventListener("click", async (event) => {
  const target = event.target;
  const versionId = target.getAttribute("data-kb-activate");
  if (!versionId) return;
  await activateKbVersion(versionId);
});

$("location").addEventListener("change", () => {
  renderMapMarkers();
  if (lastHeatmapItems.length) {
    renderHeatmap(lastHeatmapItems, $("location").value);
    renderSpatialHeat(lastHeatmapItems, $("location").value);
  }
});
$("map-toggle").addEventListener("click", openMapSidebar);
$("map-close").addEventListener("click", closeMapSidebar);
$("map-backdrop").addEventListener("click", closeMapSidebar);

$("india-map").addEventListener("click", async (event) => {
  if (!mapProjection) return;
  const rect = $("india-map").getBoundingClientRect();
  const xPct = ((event.clientX - rect.left) / rect.width) * 100;
  const yPct = ((event.clientY - rect.top) / rect.height) * 100;
  const city = nearestCityFromPercent(xPct, yPct);
  selectCity(city);
  setStatus(`Map selected ${city}. Running forecast...`);
  await runForecast();
});

$("india-map").addEventListener("keydown", async (event) => {
  if (event.key !== "Enter" && event.key !== " ") return;
  event.preventDefault();
  setStatus(`Running forecast for ${$("location").value}...`);
  await runForecast();
});

$("theme-toggle").addEventListener("click", () => {
  document.body.classList.toggle("dark");
  $("theme-toggle").textContent = document.body.classList.contains("dark") ? "Day Theme" : "Storm Theme";
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") closeMapSidebar();
});
