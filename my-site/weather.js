// my-site/weather.js - Weather utility with autocomplete and 10-day forecast

const weatherApiKey = '';
const weatherForm = document.getElementById('weatherForm');
const weatherInput = document.getElementById('weatherInput');
const citySuggestions = document.getElementById('citySuggestions');
const weatherResult = document.getElementById('weatherResult');
const weatherForecast = document.getElementById('weatherForecast');
let selectedCity = null;
let lastSuggestions = [];
let lastInputValue = '';

// --- City autocomplete using GeoDB Cities API ---
async function fetchCitySuggestions(query) {
  if (!query || query.length < 2) return [];
  const url = `https://geodb-free-service.wirefreethought.com/v1/geo/cities?limit=7&offset=0&namePrefix=${encodeURIComponent(query)}`;
  const res = await fetch(url);
  if (!res.ok) return [];
  const data = await res.json();
  return data.data.map(city => ({
    name: city.city,
    region: city.regionCode || city.region || '',
    country: city.countryCode,
    lat: city.latitude,
    lon: city.longitude
  }));
}

weatherInput.addEventListener('input', async function() {
  const val = this.value.trim();
  lastInputValue = val;
  if (/^\d{5}$/.test(val)) {
    citySuggestions.style.display = 'none';
    selectedCity = null;
    lastSuggestions = [];
    return;
  }
  citySuggestions.innerHTML = '<li style="color:#888;">Loading...</li>';
  citySuggestions.style.display = 'block';
  const suggestions = await fetchCitySuggestions(val);
  lastSuggestions = suggestions.map(city => {
    const display = [city.name, city.region, city.country].filter(Boolean).join(', ');
    return { ...city, display };
  });
  citySuggestions.innerHTML = '';
  if (lastSuggestions.length) {
    citySuggestions.style.display = 'block';
    lastSuggestions.forEach(city => {
      const li = document.createElement('li');
      li.textContent = city.display;
      li.style.cursor = 'pointer';
      li.onmousedown = (e) => {
        weatherInput.value = city.display;
        selectedCity = city;
        lastInputValue = city.display;
        setTimeout(() => { citySuggestions.style.display = 'none'; }, 100);
      };
      citySuggestions.appendChild(li);
    });
  } else {
    citySuggestions.innerHTML = '<li style="color:#d32f2f;">No matching cities found.</li>';
    citySuggestions.style.display = 'block';
  }
});

// Only hide suggestions if clicking outside input or dropdown
weatherInput.addEventListener('blur', function(e) {
  setTimeout(() => {
    if (!document.activeElement || document.activeElement.tagName !== 'LI') {
      citySuggestions.style.display = 'none';
    }
  }, 200);
});
document.addEventListener('mousedown', e => {
  if (!citySuggestions.contains(e.target) && e.target !== weatherInput) {
    citySuggestions.style.display = 'none';
  }
});

// --- Weather API: Open-Meteo (no API key required) ---
async function fetchWeather(lat, lon) {
  const url = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current_weather=true&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode&forecast_days=10&timezone=auto`;
  const res = await fetch(url);
  if (!res.ok) throw new Error('Weather fetch failed');
  return await res.json();
}

// --- Geocoding for zip code (Nominatim) ---
async function geocodeZip(zip) {
  const url = `https://nominatim.openstreetmap.org/search?postalcode=${encodeURIComponent(zip)}&format=json&limit=1`;
  const res = await fetch(url);
  if (!res.ok) return null;
  const data = await res.json();
  if (!data.length) return null;
  return { lat: data[0].lat, lon: data[0].lon, name: data[0].display_name };
}

// Weather code to icon/description mapping
const weatherIcons = {
  0: {icon: '☀️', desc: 'Clear'},
  1: {icon: '🌤️', desc: 'Mainly Clear'},
  2: {icon: '⛅', desc: 'Partly Cloudy'},
  3: {icon: '☁️', desc: 'Overcast'},
  45: {icon: '🌫️', desc: 'Fog'},
  48: {icon: '🌫️', desc: 'Depositing Rime Fog'},
  51: {icon: '🌦️', desc: 'Light Drizzle'},
  53: {icon: '🌦️', desc: 'Drizzle'},
  55: {icon: '🌦️', desc: 'Dense Drizzle'},
  56: {icon: '🌧️', desc: 'Freezing Drizzle'},
  57: {icon: '🌧️', desc: 'Freezing Drizzle'},
  61: {icon: '🌦️', desc: 'Slight Rain'},
  63: {icon: '🌧️', desc: 'Rain'},
  65: {icon: '🌧️', desc: 'Heavy Rain'},
  66: {icon: '🌧️', desc: 'Freezing Rain'},
  67: {icon: '🌧️', desc: 'Freezing Rain'},
  71: {icon: '🌨️', desc: 'Slight Snow'},
  73: {icon: '🌨️', desc: 'Snow'},
  75: {icon: '❄️', desc: 'Heavy Snow'},
  77: {icon: '❄️', desc: 'Snow Grains'},
  80: {icon: '🌦️', desc: 'Rain Showers'},
  81: {icon: '🌧️', desc: 'Rain Showers'},
  82: {icon: '🌧️', desc: 'Violent Rain Showers'},
  85: {icon: '🌨️', desc: 'Snow Showers'},
  86: {icon: '❄️', desc: 'Heavy Snow Showers'},
  95: {icon: '⛈️', desc: 'Thunderstorm'},
  96: {icon: '⛈️', desc: 'Thunderstorm w/ Hail'},
  99: {icon: '⛈️', desc: 'Thunderstorm w/ Hail'}
};

// Fetch severe weather alerts (Open-Meteo)
async function fetchAlerts(lat, lon) {
  const url = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&alerts=true`;
  const res = await fetch(url);
  if (!res.ok) return [];
  const data = await res.json();
  return (data.alerts && data.alerts.length) ? data.alerts : [];
}

weatherForm.addEventListener('submit', async function(e) {
  e.preventDefault();
  weatherResult.textContent = '';
  weatherForecast.innerHTML = '';
  let loc = null;
  const val = weatherInput.value.trim();
  // Only allow weather lookup if input matches a suggestion
  if (/^\d{5}$/.test(val)) {
    loc = await geocodeZip(val);
    if (!loc) {
      weatherResult.textContent = 'Could not find location for that zip code.';
      weatherForecast.innerHTML = '';
      return;
    }
  } else if (lastSuggestions.length) {
    // Match input to the display string of suggestions
    let match = lastSuggestions.find(city => val.toLowerCase() === city.display.toLowerCase());
    if (match) {
      loc = match;
      selectedCity = match;
    } else {
      weatherResult.textContent = 'Please select a city from the suggestions.';
      weatherForecast.innerHTML = '';
      return;
    }
  } else {
    weatherResult.textContent = 'Please select a city from the suggestions.';
    weatherForecast.innerHTML = '';
    return;
  }
  try {
    const [weather, alerts] = await Promise.all([
      fetchWeather(loc.lat, loc.lon),
      fetchAlerts(loc.lat, loc.lon)
    ]);
    // Only after successful fetch, update the UI
    // Parse location name
    let locName = loc.name || weatherInput.value;
    let locParts = locName.split(',').map(s => s.trim());
    let city = locParts[0] || '';
    let state = locParts[1] || '';
    let country = locParts[locParts.length - 1] || '';
    // Today min/max
    const todayMin = weather.daily.temperature_2m_min[0];
    const todayMax = weather.daily.temperature_2m_max[0];
    const todayIcon = weatherIcons[weather.current_weather.weathercode]?.icon || '';
    const todayDesc = weatherIcons[weather.current_weather.weathercode]?.desc || '';
    weatherResult.innerHTML = `<b>${city}${state ? ', ' + state : ''}${country ? ', ' + country : ''}</b><br>
      <span style="font-size:1.2em;">${todayIcon} ${todayDesc}</span><br>
      Current: ${weather.current_weather.temperature}°C<br>
      Min: ${todayMin}°C, Max: ${todayMax}°C`;
    // 10-day forecast
    let html = '<h4>10-Day Forecast</h4><table style="width:100%;background:#f7f7f7;color:#222;border-radius:6px;"><tr><th>Date</th><th>Min</th><th>Max</th><th>Weather</th></tr>';
    for (let i = 0; i < weather.daily.time.length; i++) {
      const code = weather.daily.weathercode[i];
      const icon = weatherIcons[code]?.icon || '';
      const desc = weatherIcons[code]?.desc || '';
      html += `<tr><td>${weather.daily.time[i]}</td><td>${weather.daily.temperature_2m_min[i]}°C</td><td>${weather.daily.temperature_2m_max[i]}°C</td><td>${icon} ${desc}</td></tr>`;
    }
    html += '</table>';
    weatherForecast.innerHTML = html;
    // Alerts
    if (alerts && alerts.length) {
      let severe = alerts.filter(a => /tornado|hurricane|cyclone|storm/i.test(a.event || ''));
      if (severe.length) {
        weatherForecast.innerHTML += `<div style="color:#d32f2f;font-weight:bold;margin-top:16px;">⚠️ Severe Weather Alerts:<ul>${severe.map(a => `<li>${a.event}: ${a.description || ''}</li>`).join('')}</ul></div>`;
      }
    }
  } catch (err) {
    weatherResult.textContent = 'Failed to fetch weather.';
    weatherForecast.innerHTML = '';
  }
});

// On page load, try to get user's location and show weather
window.addEventListener('DOMContentLoaded', async function() {
  async function showWeatherForCoords(lat, lon) {
    try {
      const [weather, alerts] = await Promise.all([
        fetchWeather(lat, lon),
        fetchAlerts(lat, lon)
      ]);
      // Reverse geocode to get city display name
      const url = `https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lon}&format=json`;
      const res = await fetch(url);
      let cityDisplay = '';
      if (res.ok) {
        const data = await res.json();
        cityDisplay = data.display_name || '';
      }
      let locParts = cityDisplay.split(',').map(s => s.trim());
      let city = locParts[0] || '';
      let state = locParts[1] || '';
      let country = locParts[locParts.length - 1] || '';
      const todayMin = weather.daily.temperature_2m_min[0];
      const todayMax = weather.daily.temperature_2m_max[0];
      const todayIcon = weatherIcons[weather.current_weather.weathercode]?.icon || '';
      const todayDesc = weatherIcons[weather.current_weather.weathercode]?.desc || '';
      weatherResult.innerHTML = `<b>${city}${state ? ', ' + state : ''}${country ? ', ' + country : ''}</b><br>
        <span style="font-size:1.2em;">${todayIcon} ${todayDesc}</span><br>
        Current: ${weather.current_weather.temperature}°C<br>
        Min: ${todayMin}°C, Max: ${todayMax}°C`;
      let html = '<h4>10-Day Forecast</h4><table style="width:100%;background:#f7f7f7;color:#222;border-radius:6px;"><tr><th>Date</th><th>Min</th><th>Max</th><th>Weather</th></tr>';
      for (let i = 0; i < weather.daily.time.length; i++) {
        const code = weather.daily.weathercode[i];
        const icon = weatherIcons[code]?.icon || '';
        const desc = weatherIcons[code]?.desc || '';
        html += `<tr><td>${weather.daily.time[i]}</td><td>${weather.daily.temperature_2m_min[i]}°C</td><td>${weather.daily.temperature_2m_max[i]}°C</td><td>${icon} ${desc}</td></tr>`;
      }
      html += '</table>';
      weatherForecast.innerHTML = html;
      if (alerts && alerts.length) {
        let severe = alerts.filter(a => /tornado|hurricane|cyclone|storm/i.test(a.event || ''));
        if (severe.length) {
          weatherForecast.innerHTML += `<div style="color:#d32f2f;font-weight:bold;margin-top:16px;">⚠️ Severe Weather Alerts:<ul>${severe.map(a => `<li>${a.event}: ${a.description || ''}</li>`).join('')}</ul></div>`;
        }
      }
    } catch (err) {
      weatherResult.textContent = 'Failed to fetch weather.';
      weatherForecast.innerHTML = '';
    }
  }
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      pos => {
        showWeatherForCoords(pos.coords.latitude, pos.coords.longitude);
      },
      err => {
        // If denied or failed, default to Plano, TX
        showWeatherForCoords(33.0198, -96.6989);
      },
      {timeout: 7000}
    );
  } else {
    // If geolocation not available, default to Plano, TX
    showWeatherForCoords(33.0198, -96.6989);
  }
});

// Show/hide logic for Weather utility
const showWeatherLink = document.getElementById('showWeatherLink');
const closeWeatherLink = document.getElementById('closeWeatherLink');
const weatherDetails = document.getElementById('weatherDetails');
showWeatherLink.addEventListener('click', function(e) {
  e.preventDefault();
  weatherDetails.style.display = 'block';
  this.style.display = 'none';
  document.getElementById('showMortgageLink').style.display = 'inline';
  document.getElementById('showDaysBetweenLink').style.display = 'inline';
  document.getElementById('mortgageCalculatorDetails').style.display = 'none';
  document.getElementById('daysBetweenDetails').style.display = 'none';
});
closeWeatherLink.addEventListener('click', function(e) {
  e.preventDefault();
  weatherDetails.style.display = 'none';
  showWeatherLink.style.display = 'inline';
});
