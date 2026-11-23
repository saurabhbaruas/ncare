import { useState } from "react";
import ProfileCard from "../components/ProfileCard";
import UploadBox from "../components/UploadBox";
import PatientTable from "../components/PatientTable";

export default function ManagerDashboard() {
  // bump this number after an upload so the table fetches fresh data
  const [refreshKey, setRefreshKey] = useState(0);

  return (
    <>
      <ProfileCard title="Manager dashboard" />
      <UploadBox onUploaded={() => setRefreshKey((k) => k + 1)} />
      <PatientTable refreshKey={refreshKey} />
    </>
  );
}
