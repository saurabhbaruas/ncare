import { useAuth } from "../auth";

// One small label + value pair
function Field({ label, value }) {
  return (
    <div className="field">
      <span className="field-label">{label}</span>
      <span className="field-value">{value}</span>
    </div>
  );
}

// Shows all the details of the logged-in user. Every role sees this at the top of their dashboard.
export default function ProfileCard({ title }) {
  const { user } = useAuth();
  const initials = user.full_name.split(" ").map((w) => w[0]).slice(0, 2).join("");

  return (
    <section id="profile" className="card">
      <div className="profile-head">
        <div className="avatar">{initials}</div>
        <div>
          <h2>{title}</h2>
          <p className="muted">{user.email}</p>
        </div>
      </div>

      <div className="grid">
        <Field label="Full name" value={user.full_name} />
        <Field label="Role" value={user.role} />
        <Field label="Location" value={`${user.location} - ${user.location_name}`} />
        <Field label="Team" value={`${user.team} - ${user.team_name}`} />
        <Field label="Account status" value={user.is_active ? "Active" : "Disabled"} />
        <Field label="Member since" value={new Date(user.created_at).toLocaleDateString()} />
      </div>

      <p className="field-label">What you can do</p>
      <div className="chips">
        {user.permissions.map((p) => <span key={p} className="chip">{p}</span>)}
      </div>
    </section>
  );
}
