import { useCallback, useEffect, useState } from "react";
import ProfileCard from "../components/ProfileCard";
import api, { errorText } from "../api";
import { useAuth } from "../auth";

const EMPTY_FORM = { email: "", full_name: "", password: "", role_id: "", location_id: "", team_id: "" };

export default function AdminDashboard() {
  const { user: me } = useAuth();
  const [users, setUsers] = useState([]);
  const [activity, setActivity] = useState([]);
  const [meta, setMeta] = useState({ roles: [], locations: [], teams: [] });
  const [form, setForm] = useState(EMPTY_FORM);
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  // loads the three lists we need on this page
  const load = useCallback(async () => {
    try {
      const [u, a, m] = await Promise.all([api.get("/users"), api.get("/activity"), api.get("/meta")]);
      setUsers(u.data);
      setActivity(a.data);
      setMeta(m.data);
    } catch (err) {
      setError(errorText(err));
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  async function createUser(e) {
    e.preventDefault();
    setError(""); setSuccess("");
    try {
      await api.post("/users", {
        ...form,
        role_id: Number(form.role_id), location_id: Number(form.location_id), team_id: Number(form.team_id),
      });
      setSuccess(`User ${form.email} created.`);
      setForm(EMPTY_FORM);
      setShowForm(false);
      load();
    } catch (err) {
      setError(errorText(err));
    }
  }

  async function toggleStatus(u) {
    setError(""); setSuccess("");
    try {
      await api.patch(`/users/${u.id}/status`, { is_active: !u.is_active });
      load();
    } catch (err) {
      setError(errorText(err));
    }
  }

  // small helper so the three dropdowns don't repeat the same code
  const select = (name, label, options, text) => (
    <label>{label}
      <select required value={form[name]} onChange={(e) => setForm({ ...form, [name]: e.target.value })}>
        <option value="">Choose...</option>
        {options.map((o) => <option key={o.id} value={o.id}>{text(o)}</option>)}
      </select>
    </label>
  );

  return (
    <>
      <ProfileCard title="Admin dashboard" />

      <section id="users" className="card">
        <div className="card-title-row">
          <h2>Users <span className="muted">({users.length})</span></h2>
          <button className="btn" onClick={() => setShowForm(!showForm)}>{showForm ? "Close" : "+ Add user"}</button>
        </div>

        {error && <div className="alert alert-error">{error}</div>}
        {success && <div className="alert alert-success">{success}</div>}

        {showForm && (
          <form className="inline-form" onSubmit={createUser}>
            <label>Full name
              <input required value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} />
            </label>
            <label>Email
              <input required type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
            </label>
            <label>Temporary password
              <input required type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
            </label>
            {select("role_id", "Role", meta.roles, (r) => r.name)}
            {select("location_id", "Location", meta.locations, (l) => `${l.code} - ${l.name}`)}
            {select("team_id", "Team", meta.teams, (t) => `${t.code} - ${t.name}`)}
            <button className="btn">Create user</button>
          </form>
        )}

        <div className="table-wrap">
          <table>
            <thead>
              <tr><th>Name</th><th>Email</th><th>Role</th><th>Location</th><th>Team</th><th>Status</th><th></th></tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id}>
                  <td>{u.full_name}</td>
                  <td>{u.email}</td>
                  <td><span className={`badge badge-${u.role.toLowerCase()}`}>{u.role}</span></td>
                  <td>{u.location}</td>
                  <td>{u.team}</td>
                  <td>{u.is_active ? (u.is_locked ? "Locked" : "Active") : "Disabled"}</td>
                  <td className="actions">
                    {/* nobody can disable their own account */}
                    {u.id !== me.id && (
                      <button className={`btn btn-small ${u.is_active ? "btn-danger" : ""}`} onClick={() => toggleStatus(u)}>
                        {u.is_active ? "Disable" : "Enable"}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section id="activity" className="card">
        <h2>Recent login activity</h2>
        <div className="table-wrap">
          <table>
            <thead><tr><th>Time</th><th>Email</th><th>Result</th><th>Reason</th><th>IP</th></tr></thead>
            <tbody>
              {activity.map((a) => (
                <tr key={a.id}>
                  <td>{new Date(a.created_at + "Z").toLocaleString()}</td>
                  <td>{a.email}</td>
                  <td className={a.success ? "ok" : "bad"}>{a.success ? "Success" : "Failed"}</td>
                  <td>{a.reason}</td>
                  <td>{a.ip_address}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </>
  );
}
