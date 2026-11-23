import { Navigate, Route, Routes } from "react-router-dom";
import { HOME, useAuth } from "./auth";
import Layout from "./components/Layout";
import Login from "./pages/Login";
import ResetPassword from "./pages/ResetPassword";
import AdminDashboard from "./pages/AdminDashboard";
import ManagerDashboard from "./pages/ManagerDashboard";
import UserDashboard from "./pages/UserDashboard";

// Only lets the right role in. Everyone else is sent to login or to their own dashboard.
function Protected({ role, children }) {
  const { user, loading } = useAuth();
  if (loading) return <p className="center-note">Loading...</p>;
  if (!user) return <Navigate to="/login" replace />;
  if (user.role !== role) return <Navigate to={HOME[user.role]} replace />;
  return <Layout>{children}</Layout>;
}

// "/" sends you to the right place depending on who you are
function Home() {
  const { user, loading } = useAuth();
  if (loading) return <p className="center-note">Loading...</p>;
  return <Navigate to={user ? HOME[user.role] : "/login"} replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/login" element={<Login />} />
      <Route path="/forgot-password" element={<ResetPassword />} />
      <Route path="/reset-password" element={<ResetPassword />} />
      <Route path="/admin" element={<Protected role="Admin"><AdminDashboard /></Protected>} />
      <Route path="/manager" element={<Protected role="Manager"><ManagerDashboard /></Protected>} />
      <Route path="/user" element={<Protected role="User"><UserDashboard /></Protected>} />
      <Route path="*" element={<Home />} />
    </Routes>
  );
}
