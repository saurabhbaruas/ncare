import ProfileCard from "../components/ProfileCard";

// Normal users only get their own details
export default function UserDashboard() {
  return <ProfileCard title="Welcome to your dashboard" />;
}
