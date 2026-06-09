// API base URL for backend API. Leave empty string to use same-origin.
// You can set `window.API_BASE` before this script loads to override.
// Default to localhost during local development for convenience.
(function () {
	if (typeof window === "undefined") return;
	if (window.API_BASE) return; // already set by environment
	const host = (window.location && window.location.hostname) || "";
	if (host === "localhost" || host === "127.0.0.1") {
		window.API_BASE = "http://localhost:5000";
	} else {
		window.API_BASE = ""; // same-origin in production; set to your backend URL when deployed
	}
})();
