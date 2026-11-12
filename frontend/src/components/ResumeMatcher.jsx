import { useMemo, useState } from "react";
import API_BASE_URL from "../api";
import CandidateDashboard from "./CandidateDashboard";

const emptyJob = {
  job_title: "",
  required_skills: "",
  preferred_skills: "",
  minimum_experience_years: "",
  education_requirement: "",
};

function splitSkills(value) {
  return value.split(",").map((item) => item.trim()).filter(Boolean);
}

export default function ResumeMatcher() {
  const [file, setFile] = useState(null);
  const [extractedText, setExtractedText] = useState("");
  const [candidate, setCandidate] = useState(null);
  const [usage, setUsage] = useState(null);
  const [shortlist, setShortlist] = useState([]);
  const [job, setJob] = useState(emptyJob);
  const [results, setResults] = useState([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const canAdd = Boolean(candidate);
  const candidateCountLabel = useMemo(
    () => `${shortlist.length} candidate${shortlist.length === 1 ? "" : "s"} added`,
    [shortlist.length]
  );

  function updateJob(event) {
    const { name, value } = event.target;
    setJob((current) => ({ ...current, [name]: value }));
  }

  function selectFile(event) {
    const selected = event.target.files?.[0] || null;
    setFile(selected);
    setExtractedText("");
    setCandidate(null);
    setUsage(null);
    setError("");
    setNotice("");
    setResults([]);
  }

  async function uploadAndAnalyze() {
    if (!file) {
      setError("Choose a PDF or DOCX resume first.");
      return;
    }

    setBusy(true);
    setError("");
    setNotice("");
    setCandidate(null);
    setUsage(null);

    try {
      const form = new FormData();
      form.append("file", file);

      const uploadResponse = await fetch(`${API_BASE_URL}/upload-resume`, {
        method: "POST",
        body: form,
      });
      const uploadData = await uploadResponse.json();
      if (!uploadResponse.ok) {
        throw new Error(uploadData.detail || "Resume upload failed.");
      }

      setExtractedText(uploadData.extracted_text);

      const analysisResponse = await fetch(`${API_BASE_URL}/analyze-resume`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ resume_text: uploadData.extracted_text }),
      });
      const analysisData = await analysisResponse.json();
      if (!analysisResponse.ok) {
        throw new Error(analysisData.detail || "Resume analysis failed.");
      }

      setCandidate({
        ...analysisData.candidate,
        source_filename: uploadData.filename,
        local_id: crypto.randomUUID(),
      });
      setUsage(analysisData.usage);
      setNotice("Resume analyzed. Review the extracted profile before shortlisting.");
    } catch (err) {
      setError(err.message || "Something went wrong.");
    } finally {
      setBusy(false);
    }
  }

  function addToShortlist() {
    if (!candidate) return;
    const email = candidate.email?.trim().toLowerCase();

    if (email && shortlist.some((item) => item.email?.trim().toLowerCase() === email)) {
      setError("A candidate with this email is already in the shortlist.");
      return;
    }

    setShortlist((current) => [...current, candidate]);
    setCandidate(null);
    setFile(null);
    setExtractedText("");
    setUsage(null);
    setError("");
    setNotice("Candidate added to the shortlist.");
  }

  function removeCandidate(localId) {
    setShortlist((current) => current.filter((item) => item.local_id !== localId));
    setResults([]);
  }

  async function compareCandidates(event) {
    event.preventDefault();
    setError("");
    setNotice("");
    setResults([]);

    if (!shortlist.length) {
      setError("Add at least one candidate before comparing.");
      return;
    }
    if (!job.job_title.trim()) {
      setError("Enter a job title.");
      return;
    }

    const required = splitSkills(job.required_skills);
    const preferred = splitSkills(job.preferred_skills);
    if (!required.length && !preferred.length && !job.minimum_experience_years && !job.education_requirement.trim()) {
      setError("Enter at least one job requirement.");
      return;
    }

    const experience = job.minimum_experience_years === ""
      ? null
      : Number(job.minimum_experience_years);

    if (experience !== null && (!Number.isFinite(experience) || experience < 0 || experience > 60)) {
      setError("Minimum experience must be between 0 and 60 years.");
      return;
    }

    setBusy(true);
    try {
      const payload = {
        candidates: shortlist.map(({ local_id, source_filename, ...profile }) => profile),
        job: {
          job_title: job.job_title.trim(),
          required_skills: required,
          preferred_skills: preferred,
          minimum_experience_years: experience,
          education_requirement: job.education_requirement.trim() || null,
        },
      };

      const response = await fetch(`${API_BASE_URL}/compare-candidates`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await response.json();
      if (!response.ok) {
        const detail = Array.isArray(data.detail)
          ? data.detail.map((item) => item.msg).join(", ")
          : data.detail;
        throw new Error(detail || "Candidate comparison failed.");
      }
      setResults(data.candidates);
      setNotice(`Compared ${data.total_candidates} candidates successfully.`);
    } catch (err) {
      setError(err.message || "Candidate comparison failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="workspace">
      <section className="panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">01 / CANDIDATE INTAKE</p>
            <h2>Analyze a resume</h2>
            <p className="muted">Upload one PDF or Word document at a time. Maximum file size: 5 MB.</p>
          </div>
          <span className="step-number">01</span>
        </div>

        <div className="upload-row">
          <label className="file-picker">
            <span>{file ? file.name : "Choose PDF or DOCX"}</span>
            <input type="file" accept=".pdf,.docx" onChange={selectFile} />
          </label>
          <button className="button button-primary" onClick={uploadAndAnalyze} disabled={busy || !file}>
            {busy ? "Working..." : "Extract candidate profile"}
          </button>
        </div>

        {usage && (
          <div className="usage-strip">
            <span>Model: <strong>{usage.model || "Groq"}</strong></span>
            <span>Prompt tokens: <strong>{usage.prompt_tokens ?? "—"}</strong></span>
            <span>Completion tokens: <strong>{usage.completion_tokens ?? "—"}</strong></span>
            <span>Total: <strong>{usage.total_tokens ?? "—"}</strong></span>
          </div>
        )}

        {candidate && (
          <div className="profile-preview">
            <div className="profile-topline">
              <div>
                <p className="eyebrow">EXTRACTED PROFILE</p>
                <h3>{candidate.name || "Name not found"}</h3>
                <p className="muted">{candidate.email || "Email not found"} · {candidate.source_filename}</p>
              </div>
              <button className="button button-primary" onClick={addToShortlist}>
                Add to shortlist
              </button>
            </div>

            <div className="profile-grid">
              <ProfileField title="Skills" value={candidate.skills?.join(", ") || "Not found"} />
              <ProfileField title="Professional experience" value={candidate.total_experience_years == null ? "Not assessable" : `${candidate.total_experience_years} years`} />
              <ProfileField title="Education" value={candidate.education?.map((item) => [item.degree, item.institution, item.year].filter(Boolean).join(" · ")).join("; ") || "Not found"} />
              <ProfileField title="Projects" value={candidate.projects?.map((item) => item.name).filter(Boolean).join(", ") || "Not found"} />
            </div>
            <p className="review-note">Please verify extracted information against the original resume before adding the candidate.</p>
          </div>
        )}

        {extractedText && (
          <details className="extracted-text">
            <summary>View extracted resume text</summary>
            <pre>{extractedText}</pre>
          </details>
        )}
      </section>

      <section className="panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">02 / SHORTLIST</p>
            <h2>Candidate shortlist</h2>
            <p className="muted">{candidateCountLabel}. Add resumes one by one above.</p>
          </div>
          <span className="step-number">02</span>
        </div>

        {shortlist.length === 0 ? (
          <div className="empty-state">Your shortlisted candidates will appear here.</div>
        ) : (
          <div className="shortlist">
            {shortlist.map((item, index) => (
              <div className="shortlist-item" key={item.local_id}>
                <div className="avatar">{(item.name || "C").charAt(0).toUpperCase()}</div>
                <div className="shortlist-info">
                  <strong>{item.name || `Candidate ${index + 1}`}</strong>
                  <span>{item.email || "Email not found"}</span>
                  <small>{item.source_filename}</small>
                </div>
                <button className="button button-quiet" onClick={() => removeCandidate(item.local_id)}>Remove</button>
              </div>
            ))}
          </div>
        )}
      </section>

      <section className="panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">03 / JOB CRITERIA</p>
            <h2>Define the role</h2>
            <p className="muted">Enter the criteria HR wants to assess for this shortlist.</p>
          </div>
          <span className="step-number">03</span>
        </div>

        <form onSubmit={compareCandidates}>
          <div className="form-grid">
            <label className="field full-width">
              Job title *
              <input name="job_title" value={job.job_title} onChange={updateJob} placeholder="e.g. Frontend Developer" />
            </label>
            <label className="field">
              Required skills
              <textarea name="required_skills" value={job.required_skills} onChange={updateJob} placeholder="React, JavaScript, HTML (comma separated)" />
            </label>
            <label className="field">
              Preferred skills
              <textarea name="preferred_skills" value={job.preferred_skills} onChange={updateJob} placeholder="TypeScript, Tailwind CSS (comma separated)" />
            </label>
            <label className="field">
              Minimum professional experience (years)
              <input name="minimum_experience_years" type="number" min="0" max="60" step="0.5" value={job.minimum_experience_years} onChange={updateJob} placeholder="e.g. 1" />
            </label>
            <label className="field">
              Education requirement (optional)
              <input name="education_requirement" value={job.education_requirement} onChange={updateJob} placeholder="e.g. Computer Engineering" />
            </label>
          </div>
          <button className="button button-primary" type="submit" disabled={busy || shortlist.length === 0}>
            {busy ? "Comparing..." : "Compare shortlisted candidates"}
          </button>
        </form>
      </section>

      {error && <div className="alert alert-error" role="alert">{error}</div>}
      {notice && <div className="alert alert-success" role="status">{notice}</div>}

      <CandidateDashboard results={results} />
    </div>
  );
}

function ProfileField({ title, value }) {
  return (
    <div className="profile-field">
      <span>{title}</span>
      <p>{value}</p>
    </div>
  );
}
