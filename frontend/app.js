const apiBaseUrl = "http://127.0.0.1:8000";
const apiKey = "dev-admin-key";
const role = "analyst";
const indiaGeoJsonUrl = "https://cdn.jsdelivr.net/npm/world-geojson@3.4.0/countries/india.json";

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

function initCities() {
  const select = $("location");
  select.innerHTML = cities.map((c) => `<option value="${c}">${c}</option>`).join("");
  select.value = "New Delhi";
}

function projectLonLat(lon, lat) {
  if (!mapProjection) return null;
  const { minLon, maxLat, scale, xPad, yPad } = mapProjection;
  const x = (lon - minLon) * scale + xPad;
  const y = (maxLat - lat) * scale + yPad;
  return {
    x,
    y,
    xPct: (x / SVG_WIDTH) * 100,
    yPct: (y / SVG_HEIGHT) * 100,
  };
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

    mapProjection = computeProjection(polygons);
    const paths = polygons
      .map((polygon) => {
        const d = polygon.map((ring) => ringToPath(ring)).join(" ");
        return `<path class="india-shape" d="${d}" />`;
      })
      .join("");
    $("india-geo-layer").innerHTML = paths;
    $("india-heat-geo-layer").innerHTML = paths;
    $("india-heat-clip-paths").innerHTML = paths;
  } catch (error) {
    $("map-heat-info").textContent = `Boundary load failed: ${error.message}`;
  }
}

function heatColor(prob) {
  const p = Number(prob);
  if (p < 0.25) return "#45b36a";
  if (p < 0.45) return "#d2a500";
  if (p < 0.65) return "#d08b00";
  if (p < 0.8) return "#c05f00";
  return "#b00020";
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
      return `
        <span
          class="map-dot ${isActive ? "active" : ""}"
          style="left:${point.xPct}%;top:${point.yPct}%"
          title="${city}"
        ></span>
      `;
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
  const p = Math.max(0, Math.min(1, Number(prob)));
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

function renderSpatialHeat(items) {
  if (!mapProjection) return;
  const surfaceLayer = $("india-heat-surface");
  const blurLayer = $("india-heat-spots");
  const coreLayer = $("india-heat-spots-core");
  surfaceLayer.innerHTML = "";
  blurLayer.innerHTML = "";
  coreLayer.innerHTML = "";

  const validItems = items.filter((item) => cityGeo[item.location]);
  if (!validItems.length) return;

  const projected = validItems.map((item) => {
    const p = projectLonLat(cityGeo[item.location].lon, cityGeo[item.location].lat);
    return { x: p.x, y: p.y, w: Number(item.rain_probability) };
  });

  const sigma = 44;
  const sigma2 = sigma * sigma;
  const grid = 7;
  const cells = [];
  let maxVal = 0;

  for (let y = 0; y < SVG_HEIGHT; y += grid) {
    for (let x = 0; x < SVG_WIDTH; x += grid) {
      const cx = x + grid / 2;
      const cy = y + grid / 2;
      let val = 0;
      for (const point of projected) {
        const dx = cx - point.x;
        const dy = cy - point.y;
        const d2 = dx * dx + dy * dy;
        val += point.w * Math.exp(-d2 / (2 * sigma2));
      }
      maxVal = Math.max(maxVal, val);
      cells.push({ x, y, v: val });
    }
  }

  if (maxVal <= 0) return;

  surfaceLayer.innerHTML = cells
    .map((cell) => {
      const norm = cell.v / maxVal;
      if (norm < 0.06) return "";
      const rgb = heatScaleRgb(norm);
      const alpha = 0.18 + Math.pow(norm, 0.85) * 0.72;
      return `<rect x="${cell.x}" y="${cell.y}" width="${grid}" height="${grid}" fill="${rgbToCss(rgb, alpha)}"></rect>`;
    })
    .join("");

  blurLayer.innerHTML = validItems
    .map((item) => {
      const p = projectLonLat(cityGeo[item.location].lon, cityGeo[item.location].lat);
      const pr = Number(item.rain_probability);
      const rgb = heatScaleRgb(pr);
      const radius = 14 + pr * 20;
      return `<circle cx="${p.x.toFixed(2)}" cy="${p.y.toFixed(2)}" r="${radius.toFixed(2)}" fill="${rgbToCss(rgb, 0.4)}"></circle>`;
    })
    .join("");

  coreLayer.innerHTML = validItems
    .map((item) => {
      const p = projectLonLat(cityGeo[item.location].lon, cityGeo[item.location].lat);
      const pr = Number(item.rain_probability);
      const rgb = heatScaleRgb(pr);
      const radius = 3.5 + pr * 5;
      return `<circle cx="${p.x.toFixed(2)}" cy="${p.y.toFixed(2)}" r="${radius.toFixed(2)}" fill="${rgbToCss(rgb, 0.95)}"></circle>`;
    })
    .join("");
}

function openMapSidebar() {
  $("map-sidebar").classList.add("open");
  $("map-backdrop").classList.add("open");
  $("map-sidebar").setAttribute("aria-hidden", "false");
}

function closeMapSidebar() {
  $("map-sidebar").classList.remove("open");
  $("map-backdrop").classList.remove("open");
  $("map-sidebar").setAttribute("aria-hidden", "true");
}

function payload() {
  const temp = Number($("temperature_c").value);
  const humidity = Number($("humidity_pct").value);
  const cloud = Number($("cloud_cover_pct").value);
  const wind = Number($("wind_kph").value);
  const dew = Math.max(0, Math.round(temp - (100 - humidity) / 5));
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
      month: 7,
      hour_24: 16,
      season: "monsoon",
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

function headers() {
  return {
    "Content-Type": "application/json",
    "x-api-key": apiKey,
    "x-role": role,
  };
}

function pct(v) {
  return `${Math.round(Number(v) * 100)}%`;
}

function setStatus(txt) {
  $("status").textContent = txt;
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
  $("headline").textContent = `${data.location}: ${data.predicted_condition.toUpperCase()} (${data.alert_level})`;
  $("quick").innerHTML = `
    <span class="chip">Rain ${pct(data.rain_probability)}</span>
    <span class="chip">Rainfall ${data.expected_rainfall_mm} mm</span>
    <span class="chip">Confidence ${pct(data.confidence_score)}</span>
    <span class="chip">Mode ${data.risk_mode}</span>
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

function renderHeatmap(items) {
  $("heatmap").innerHTML = items
    .map(
      (item) => `
      <div class="heat-cell" style="background:${heatColor(item.rain_probability)}">
        ${item.location}
        <small>${pct(item.rain_probability)} rain | ${item.predicted_condition}</small>
      </div>
    `
    )
    .join("");
}

async function runForecast() {
  setStatus("Running forecast...");
  try {
    const res = await fetch(`${apiBaseUrl}/api/v1/infer`, {
      method: "POST",
      headers: headers(),
      body: JSON.stringify(payload()),
    });
    if (!res.ok) throw new Error(await res.text());
    const data = await res.json();
    renderMain(data);
    setStatus("Forecast ready.");
  } catch (error) {
    setStatus(`Forecast failed: ${error.message}`);
  }
}

async function runHeatmap() {
  setStatus("Running city heatmap...");
  try {
    const selectedCity = $("location").value;
    const heatmapCities = [selectedCity, ...cities.filter((c) => c !== selectedCity)].slice(0, 10);
    const body = {
      locations: heatmapCities,
      observation: payload().observation,
      horizon_hours: Number($("horizon_hours").value),
      risk_mode: $("risk_mode").value,
    };
    const res = await fetch(`${apiBaseUrl}/api/v1/infer/multi-location`, {
      method: "POST",
      headers: headers(),
      body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error(await res.text());
    const data = await res.json();
    renderHeatmap(data.items);
    renderSpatialHeat(data.items);
    setStatus(`Heatmap ready for ${data.count} cities.`);
  } catch (error) {
    setStatus(`Heatmap failed: ${error.message}`);
  }
}

initCities();
loadIndiaBoundary().then(renderMapMarkers);
$("run").addEventListener("click", runForecast);
$("run-multi").addEventListener("click", runHeatmap);
$("location").addEventListener("change", renderMapMarkers);
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
  $("theme-toggle").textContent = document.body.classList.contains("dark") ? "Light Mode" : "Dark Mode";
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") closeMapSidebar();
});
