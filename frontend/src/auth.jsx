import { createContext, useContext, useEffect, useState } from "react";
import api from "./api";

// A "context" lets any component ask "who is logged in?" without passing props around
const AuthContext = createContext(null);

// Where each role lands after login
export const HOME = { Admin: "/admin", Manager: "/manager", User: "/user" };

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true); // true until we know if a session exists

  // When the page opens, ask the backend if we are already logged in (cookie still valid)
  useEffect(() => {
    api.get("/auth/me")
      .then((res) => setUser(res.data))
      .catch(() => setUser(null))
      .finally(() => setLoading(false));

    // api.js fires this event when the session expires
    const onExpired = () => setUser(null);
    window.addEventListener("session-expired", onExpired);
    return () => window.removeEventListener("session-expired", onExpired);
  }, []);

  async function login(email, password) {
    const res = await api.post("/auth/login", { email, password });
    setUser(res.data);
    return res.data;
  }

  async function logout() {
    try {
      await api.post("/auth/logout");
    } finally {
      // even if the call fails, the user should look logged out on screen
      setUser(null);
    }
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
