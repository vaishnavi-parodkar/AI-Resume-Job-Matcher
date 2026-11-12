import { useMemo, useState } from "react";

export default function CandidateDashboard({ results }) {
  const [search, setSearch] = useState("");
  const [sortOrder, setSortOrder] = useState("highest");
  const [minimumScore, setMinimumScore] = useState("all");

  const filtered = useMemo(() => {
    let list = (results || []).filter((item) => {
      const query = search.trim().toLowerCase();
      const name = `${item.candidate_name} ${item.candidate_email || ""}`.toLowerCase();
      const score = item.match_report.match_percentage;

      const matchesSearch = name.includes(query);
      let matchesScore = true;
      if (minimumScore === "70") matchesScore = score !== null && score >= 70;
      if (minimumScore === "50") matchesScore = score !== null && score >= 50;
      if (minimumScore === "below50") matchesScore = score !== null && score < 50;
      if (minimumScore === "unscored") matchesScore = score === null;

      return matchesSearch && matchesScore;
    });

    list.sort((a, b) => {
      const scoreA = a.match_report.match_percentage;
      const scoreB = b.match_report.match_percentage;
      if (scoreA === null) return 1;
      if (scoreB === null) return -1;
      return sortOrder === "highest" ? scoreB - scoreA : scoreA - scoreB;
    });
    return list;
  }, [results, search, sortOrder, minimumScore]);

  if (!results?.length) return null;

  const scored = results.filter((item) => item.match_report.match_percentage !== null);
  const best = scored.length
    ? Math.max(...scored.map((item) => item.match_report.match_percentage))
    : null;

  function exportCSV() {
    const headers = [
      "Rank", "Candidate Name", "Email", "Match Percentage",
      "Matched Required Skills", "Missing Required Skills",
      "Experience Status", "Education Status",
    ];
    const rows = filtered.map((item, index) => {
      const report = item.match_report;
      return [
        index + 1,
        item.candidate_name,
        item.candidate_email || "",
        report.match_percentage ?? "Not assessable",
        report.skills.matched_required.join("; "),
        report.skills.missing_required.join("; "),
        report.experience.status,
        report.education.status,
      ];
    });
    const quote = (value) => `"${String(value).replace(/"/g, '""')}"`;
    const csv = [headers, ...rows].map((row) => row.map(quote).join(",")).join("\r\n");
    const blob = new Blob(["\uFEFF" + csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "candidate-comparison-report.csv";
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  }

  return (
    <section className="panel results-panel">
      <div className="section-heading">
        <div>
          <p className="eyebrow">04 / COMPARISON RESULTS</p>
          <h2>Candidate ranking</h2>
          <p className="muted">Scores are explainable screening indicators, not hiring decisions.</p>
        </div>
        <span className="step-number">04</span>
      </div>

      <div className="stats-grid">
        <Stat label="Candidates compared" value={results.length} />
        <Stat label="Candidates with a score" value={scored.length} />
        <Stat label="Highest match" value={best === null ? "—" : `${best}%`} />
      </div>

      <div className="toolbar">
        <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search name or email" aria-label="Search candidates" />
        <select value={sortOrder} onChange={(event) => setSortOrder(event.target.value)} aria-label="Sort candidates">
          <option value="highest">Highest match first</option>
          <option value="lowest">Lowest match first</option>
        </select>
        <select value={minimumScore} onChange={(event) => setMinimumScore(event.target.value)} aria-label="Filter match score">
          <option value="all">All scores</option>
          <option value="70">70% and above</option>
          <option value="50">50% and above</option>
          <option value="below50">Below 50%</option>
          <option value="unscored">Not assessable</option>
        </select>
        <button className="button button-secondary" onClick={exportCSV} disabled={!filtered.length}>Export CSV</button>
      </div>

      {filtered.length === 0 ? (
        <div className="empty-state">No candidates match this search or filter.</div>
      ) : (
        <div className="candidate-results">
          {filtered.map((item, index) => (
            <CandidateCard key={`${item.candidate_id}-${item.candidate_email || index}`} item={item} rank={index + 1} />
          ))}
        </div>
      )}

      <p className="disclaimer">
        Matching is based on the information extracted from the resume and the criteria entered by HR.
        Missing information is shown as not assessable where possible. Review the original resume and
        evaluate candidates individually before making decisions.
      </p>
    </section>
  );
}

function Stat({ label, value }) {
  return <div className="stat-card"><span>{label}</span><strong>{value}</strong></div>;
}

function CandidateCard({ item, rank }) {
  const report = item.match_report;
  const score = report.match_percentage;

  return (
    <article className="candidate-card">
      <div className="candidate-head">
        <div>
          <span className="rank-label">RANK #{rank}</span>
          <h3>{item.candidate_name}</h3>
          <p className="muted">{item.candidate_email || "Email not found"}</p>
        </div>
        <div className="score-block">
          <strong>{score === null ? "N/A" : `${score}%`}</strong>
          <span>overall match</span>
        </div>
      </div>

      <div className="score-track">
        <div className="score-fill" style={{ width: `${score === null ? 0 : Math.max(0, Math.min(100, score))}%` }} />
      </div>

      <div className="result-grid">
        <ResultList title="Matched required skills" values={report.skills.matched_required} empty="No required skills matched." />
        <ResultList title="Missing required skills" values={report.skills.missing_required} empty="No missing required skills identified." />
        <ResultList title="Matched preferred skills" values={report.skills.matched_preferred} empty="No preferred skills matched." />
        <ResultList title="Missing preferred skills" values={report.skills.missing_preferred} empty="No missing preferred skills identified." />
        <div className="result-cell">
          <h4>Experience</h4>
          <p>{report.experience.status}</p>
          {report.experience.candidate_years != null && <small>{report.experience.candidate_years} years stated in resume</small>}
        </div>
        <div className="result-cell">
          <h4>Education</h4>
          <p>{report.education.status}</p>
        </div>
      </div>

      <details className="recommendations">
        <summary>Screening notes and recommendations</summary>
        <ul>{report.recommendations.map((note, index) => <li key={index}>{note}</li>)}</ul>
      </details>
    </article>
  );
}

function ResultList({ title, values, empty }) {
  return (
    <div className="result-cell">
      <h4>{title}</h4>
      {values.length ? (
        <div className="chips">{values.map((value) => <span className="chip" key={value}>{value}</span>)}</div>
      ) : <p className="muted">{empty}</p>}
    </div>
  );
}
