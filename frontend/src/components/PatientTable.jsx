import { useEffect, useState } from "react";
import api, { errorText } from "../api";

// column key -> heading shown in the table
const COLUMNS = [
  ["patient_id", "Patient ID"],
  ["first_name", "First Name"],
  ["last_name", "Last Name"],
  ["dob", "Date of Birth"],
  ["gender", "Gender"],
];
const PAGE_SIZES = [10, 25, 50, 100, 500];

export default function PatientTable({ refreshKey }) {
  const [rows, setRows] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [genders, setGenders] = useState([]);

  // table controls
  const [page, setPage] = useState(1);
  const [size, setSize] = useState(25);
  const [sort, setSort] = useState("patient_id");
  const [order, setOrder] = useState("asc");
  const [search, setSearch] = useState("");
  const [query, setQuery] = useState(""); // the search text we actually send (after a short pause)

  // inline editing: which row is open and what the user has typed so far
  const [editingId, setEditingId] = useState(null);
  const [draft, setDraft] = useState({});
  const [saving, setSaving] = useState(false);

  // load the gender options once (they come from the backend config)
  useEffect(() => {
    api.get("/meta").then((res) => setGenders(res.data.genders)).catch(() => {});
  }, []);

  // wait until the user stops typing for 400 ms before searching
  useEffect(() => {
    const timer = setTimeout(() => { setQuery(search); setPage(1); }, 400);
    return () => clearTimeout(timer);
  }, [search]);

  // fetch the current page whenever a control changes (or after a new upload)
  useEffect(() => {
    let cancelled = false; // ignore answers that arrive after a newer request was made
    setLoading(true);
    api.get("/patients", { params: { page, size, sort, order, q: query } })
      .then((res) => {
        if (cancelled) return;
        setRows(res.data.items);
        setTotal(res.data.total);
        setError("");
      })
      .catch((err) => !cancelled && setError(errorText(err)))
      .finally(() => !cancelled && setLoading(false));
    return () => { cancelled = true; };
  }, [page, size, sort, order, query, refreshKey]);

  // click a heading: sort by it, click again to flip the direction
  function changeSort(key) {
    if (key === sort) setOrder(order === "asc" ? "desc" : "asc");
    else { setSort(key); setOrder("asc"); }
    setPage(1);
  }

  function startEdit(row) {
    setEditingId(row.id);
    setDraft({ first_name: row.first_name, last_name: row.last_name, dob: row.dob, gender: row.gender });
    setError("");
  }

  // Optimistic update: show the new values immediately, undo them if the server says no
  async function saveEdit(original) {
    const changes = {};
    for (const key of Object.keys(draft)) {
      if (draft[key] !== original[key]) changes[key] = draft[key];
    }
    if (!Object.keys(changes).length) return setEditingId(null); // nothing changed

    // quick check in the browser (the server validates again)
    if (changes.first_name === "" || changes.last_name === "") {
      return setError("First and last name cannot be empty.");
    }

    const backup = rows;
    setRows(rows.map((r) => (r.id === original.id ? { ...r, ...changes } : r)));
    setEditingId(null);
    setSaving(true);

    try {
      const res = await api.patch(`/patients/${original.id}`, changes);
      // use what the server returns (it may have cleaned the values)
      setRows((current) => current.map((r) => (r.id === original.id ? res.data : r)));
    } catch (err) {
      setRows(backup); // roll back
      setError(errorText(err));
    } finally {
      setSaving(false);
    }
  }

  async function remove(row) {
    if (!window.confirm(`Delete patient ${row.patient_id}? This cannot be undone.`)) return;
    try {
      await api.delete(`/patients/${row.id}`);
      if (rows.length === 1 && page > 1) {
        // that was the last row on this page, so go back one page (this reloads the table)
        setPage(page - 1);
      } else {
        setRows(rows.filter((r) => r.id !== row.id));
        setTotal(total - 1);
      }
    } catch (err) {
      setError(errorText(err));
    }
  }

  const pages = Math.max(1, Math.ceil(total / size));
  const edited = (row, key) => editingId === row.id && draft[key] !== row[key]; // highlights changed cells

  // the cell is either plain text or an input, depending on edit mode
  function cell(row, key) {
    if (editingId !== row.id || key === "patient_id") return row[key];
    if (key === "gender") {
      return (
        <select className={edited(row, key) ? "edited" : ""} value={draft.gender}
                onChange={(e) => setDraft({ ...draft, gender: e.target.value })}>
          {genders.map((g) => <option key={g}>{g}</option>)}
        </select>
      );
    }
    return (
      <input className={edited(row, key) ? "edited" : ""} type={key === "dob" ? "date" : "text"}
             value={draft[key]} onChange={(e) => setDraft({ ...draft, [key]: e.target.value })} />
    );
  }

  return (
    <section id="patients" className="card">
      <div className="card-title-row">
        <h2>Patients <span className="muted">({total})</span></h2>
        <input className="search" placeholder="Search any field..." value={search}
               onChange={(e) => setSearch(e.target.value)} />
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              {COLUMNS.map(([key, label]) => (
                <th key={key} onClick={() => changeSort(key)} className="sortable">
                  {label} {sort === key ? (order === "asc" ? "▲" : "▼") : ""}
                </th>
              ))}
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading && <tr><td colSpan="6" className="empty">Loading patients...</td></tr>}
            {!loading && rows.length === 0 && (
              <tr><td colSpan="6" className="empty">
                {query ? "No patients match your search." : "No patients yet. Upload an Excel file above to get started."}
              </td></tr>
            )}
            {!loading && rows.map((row) => (
              <tr key={row.id} className={editingId === row.id ? "editing" : ""}>
                {COLUMNS.map(([key]) => <td key={key}>{cell(row, key)}</td>)}
                <td className="actions">
                  {editingId === row.id ? (
                    <>
                      <button className="btn btn-small" onClick={() => saveEdit(row)}>Save</button>
                      <button className="btn btn-small btn-light-dark" onClick={() => setEditingId(null)}>Cancel</button>
                    </>
                  ) : (
                    <>
                      <button className="btn btn-small btn-light-dark" disabled={saving} onClick={() => startEdit(row)}>Edit</button>
                      <button className="btn btn-small btn-danger" onClick={() => remove(row)}>Delete</button>
                    </>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="pagination">
        <label>
          Rows per page{" "}
          <select value={size} onChange={(e) => { setSize(Number(e.target.value)); setPage(1); }}>
            {PAGE_SIZES.map((s) => <option key={s}>{s}</option>)}
          </select>
        </label>
        <span>Page {page} of {pages}</span>
        <button className="btn btn-small btn-light-dark" disabled={page <= 1} onClick={() => setPage(page - 1)}>Previous</button>
        <button className="btn btn-small btn-light-dark" disabled={page >= pages} onClick={() => setPage(page + 1)}>Next</button>
      </div>
    </section>
  );
}
