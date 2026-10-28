.pragma library

// Formats a duration in seconds as m:ss, or h:mm:ss from one hour up.
function formatTime(seconds) {
    const total = Math.floor(Number(seconds));
    if (!isFinite(total) || total <= 0)
        return "0:00";
    const hours = Math.floor(total / 3600);
    const minutes = Math.floor((total % 3600) / 60);
    const secs = total % 60;
    const ss = (secs < 10 ? "0" : "") + secs;
    if (hours > 0)
        return hours + ":" + (minutes < 10 ? "0" : "") + minutes + ":" + ss;
    return minutes + ":" + ss;
}

// Converts a 0-100 setting to a 0-1 opacity, falling back when unset or invalid.
function percent(value, fallback) {
    const n = Number(value);
    if (value === undefined || value === null || value === "" || !isFinite(n))
        return fallback / 100;
    return Math.max(0, Math.min(100, n)) / 100;
}

// Returns the y offset of a wave whose period divides width exactly, so a
// copy drawn at x + width lines up and a translated strip loops seamlessly.
function waveY(x, width, baseline, amplitude, cycles, phase) {
    if (width <= 0)
        return baseline;
    return baseline + Math.sin((x / width) * cycles * 2 * Math.PI + phase) * amplitude;
}
