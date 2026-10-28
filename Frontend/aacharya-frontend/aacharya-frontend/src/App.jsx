import { useEffect, useState } from "react";
import { api } from "./api.js";

const LEVELS = ["Remember", "Understand", "Apply", "Analyze", "Evaluate", "Create"];

/* ---------- Screen 1: at-risk students (rule engine) ---------- */
function AtRisk() {
  const [students, setStudents] = useState(null);
  const [resources, setResources] = useState({});
  const [error, setError] = useState("");

  useEffect(() => {
    api("/students/at-risk").then(setStudents).catch((e) => setError(e.message));
  }, []);

  async function loadResources(id) {
    try {
      setResources({ ...resources, [id]: await api(`/students/${id}/resources`) });
    } catch (e) { setError(e.message); }
  }

  if (error) return <p className="error">{error}</p>;
  if (!students) return <p>Loading...</p>;
  if (students.length === 0) return <p>No at-risk students. 🎉</p>;

  return (
    <div>
      {students.map((s) => (
        <div className="card" key={s.student_id}>
          <div className="row">
            <strong>{s.name}</strong>
            <span className={`badge ${s.risk}`}>{s.risk} risk</span>
          </div>
          <ul>{s.reasons.map((r) => <li key={r}>{r}</li>)}</ul>
          <button onClick={() => loadResources(s.student_id)}>Recommend resources</button>
          {resources[s.student_id] && (
            resources[s.student_id].length === 0
              ? <p className="muted">No weak topics with resources.</p>
              : resources[s.student_id].map((w) => (
                  <div key={w.weak_topic} className="resbox">
                    <b>Weak topic: {w.weak_topic}</b>
                    {w.resources.map((r) => <div key={r.url}><a href={r.url} target="_blank" rel="noreferrer">{r.title}</a></div>)}
                  </div>
                ))
          )}
        </div>
      ))}
    </div>
  );
}

/* ---------- Screen 2: question papers (AI draft -> teacher approval) ---------- */
function Papers() {
  const [papers, setPapers] = useState([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [subject, setSubject] = useState("Maths");
  const [topics, setTopics] = useState("Algebra, Integration");
  const [total, setTotal] = useState(10);
  const [mix, setMix] = useState({ Remember: 30, Understand: 0, Apply: 40, Analyze: 30, Evaluate: 0, Create: 0 });
  const [comments, setComments] = useState({});

  const sum = Object.values(mix).reduce((a, b) => a + Number(b), 0);
  const load = () => api("/papers").then(setPapers).catch((e) => setError(e.message));
  useEffect(() => { load(); }, []);

  async function generate() {
    setError(""); setBusy(true);
    try {
      const bloom_mix = Object.fromEntries(Object.entries(mix).filter(([, v]) => Number(v) > 0).map(([k, v]) => [k, Number(v)]));
      await api("/papers/generate", {
        method: "POST",
        body: JSON.stringify({
          subject, total_questions: Number(total), bloom_mix,
          topics: topics.split(",").map((t) => t.trim()).filter(Boolean),
        }),
      });
      await load();
    } catch (e) { setError(e.message); }
    setBusy(false);
  }

  async function review(id, decision) {
    setError("");
    try {
      await api(`/papers/${id}/review`, { method: "POST", body: JSON.stringify({ decision, comment: comments[id] || "" }) });
      await load();
    } catch (e) { setError(e.message); }
  }

  return (
    <div>
      <div className="card">
        <h3>Generate a question paper</h3>
        <label>Subject <input value={subject} onChange={(e) => setSubject(e.target.value)} /></label>
        <label>Topics (comma separated) <input value={topics} onChange={(e) => setTopics(e.target.value)} /></label>
        <label>Total questions <input type="number" min="1" max="50" value={total} onChange={(e) => setTotal(e.target.value)} /></label>
        <p className="muted">Bloom's Taxonomy mix (%) — must total 100:</p>
        <div className="mix">
          {LEVELS.map((l) => (
            <label key={l}>{l}
              <input type="number" min="0" max="100" value={mix[l]} onChange={(e) => setMix({ ...mix, [l]: e.target.value })} />
            </label>
          ))}
        </div>
        <p className={sum === 100 ? "ok" : "error"}>Total: {sum}%</p>
        <button disabled={busy || sum !== 100} onClick={generate}>{busy ? "Generating… (a local model can take a minute)" : "Generate draft"}</button>
      </div>

      {error && <p className="error">{error}</p>}

      {papers.map((p) => (
        <div className="card" key={p.id}>
          <div className="row">
            <strong>Paper #{p.id} — {p.subject}</strong>
            <span className={`badge ${p.status}`}>{p.status}</span>
          </div>
          <ol>
            {p.questions.map((q) => (
              <li key={q.id}>{q.text} <span className="tag">{q.bloom_level} · {q.marks}m</span></li>
            ))}
          </ol>
          {p.status === "draft" ? (
            <div className="row">
              <input placeholder="Review comment (optional)" value={comments[p.id] || ""} onChange={(e) => setComments({ ...comments, [p.id]: e.target.value })} />
              <button onClick={() => review(p.id, "approve")}>Approve</button>
              <button className="danger" onClick={() => review(p.id, "reject")}>Reject</button>
            </div>
          ) : <p className="muted">Final — cannot be changed.</p>}
        </div>
      ))}
    </div>
  );
}

/* ---------- Screen 3: audit log ---------- */
function Audit() {
  const [rows, setRows] = useState(null);
  useEffect(() => { api("/audit").then(setRows).catch(() => setRows([])); }, []);
  if (!rows) return <p>Loading...</p>;
  return (
    <table>
      <thead><tr><th>When</th><th>Action</th><th>Item</th><th>Details</th></tr></thead>
      <tbody>
        {rows.map((r) => (
          <tr key={r.id}><td>{new Date(r.at).toLocaleString()}</td><td>{r.action}</td><td>{r.entity}</td><td>{r.details}</td></tr>
        ))}
      </tbody>
    </table>
  );
}

export default function App() {
  const [tab, setTab] = useState("risk");
  const tabs = [["risk", "At-risk students"], ["papers", "Question papers"], ["audit", "Audit log"]];
  return (
    <div className="wrap">
      <h1>Aacharya <span className="muted">AI Teaching Co-Pilot</span></h1>
      <nav>
        {tabs.map(([k, label]) => (
          <button key={k} className={tab === k ? "active" : ""} onClick={() => setTab(k)}>{label}</button>
        ))}
      </nav>
      {tab === "risk" && <AtRisk />}
      {tab === "papers" && <Papers />}
      {tab === "audit" && <Audit />}
    </div>
  );
}
