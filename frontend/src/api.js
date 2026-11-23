import axios from "axios";

// All requests go to /api (the dev server / nginx forwards them to the backend)
// withCredentials = send the login cookie along with every request
// X-API-Key = the key the backend requires on every call (value comes from API_KEY in .env, see vite.config.js)
const api = axios.create({
  baseURL: "/api",
  withCredentials: true,
  headers: { "X-API-Key": import.meta.env.VITE_API_KEY },
});

// Before every request: copy the CSRF token from the cookie into a header.
// The backend compares both, which blocks forged requests from other websites.
api.interceptors.request.use((config) => {
  const match = document.cookie.match(/csrf_token=([^;]+)/);
  if (match) config.headers["X-CSRF-Token"] = match[1];
  return config;
});

// If the session ran out while the user was working, tell the app so it can show the login page.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const isLoginCall = error.config?.url?.includes("/auth/login");
    if (error.response?.status === 401 && !isLoginCall) {
      window.dispatchEvent(new Event("session-expired"));
    }
    return Promise.reject(error);
  }
);

// Turns any error into one readable sentence for the user
export function errorText(error) {
  if (!error.response) return "Cannot reach the server. Please check your connection.";
  const detail = error.response.data?.detail;
  if (typeof detail === "string") return detail;
  if (detail?.message) return detail.message;
  return "Something went wrong. Please try again.";
}

export default api;
