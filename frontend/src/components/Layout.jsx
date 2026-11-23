import { useAuth } from "../auth";

// Links in the top bar depend on the role (they scroll to a section of the dashboard)
const NAV = {
  Admin: [["Profile", "#profile"], ["Users", "#users"], ["Login activity", "#activity"]],
  Manager: [["Profile", "#profile"], ["Upload", "#upload"], ["Patients", "#patients"]],
  User: [["My profile", "#profile"]],
};

export default function Layout({ children }) {
  const { user, logout } = useAuth();

  return (
    <>
      <header className="navbar">
        <div className="navbar-inner">
          <span className="brand">Ncare</span>
          <nav>
            {NAV[user.role].map(([label, href]) => (
              <a key={href} href={href}>{label}</a>
            ))}
          </nav>
          <div className="navbar-user">
            <span>{user.full_name}</span>
            <span className={`badge badge-${user.role.toLowerCase()}`}>{user.role}</span>
            <button className="btn btn-light" onClick={logout}>Log out</button>
          </div>
        </div>
      </header>
      <main className="container">{children}</main>
    </>
  );
}
