import ResumeMatcher from "./components/ResumeMatcher";

export default function App() {
  return (
    <main className="page-shell">
      <header className="hero">
        <div className="hero-mark">RM</div>
        <div>
          <p className="eyebrow">RECRUITMENT WORKSPACE</p>
          <h1>AI Resume–Job Matcher</h1>
          <p className="hero-copy">
            Turn resumes into structured profiles and compare candidates
            against the requirements that matter.
          </p>
        </div>
      </header>
      <ResumeMatcher />
      <footer className="footer">
        AI-assisted screening support · Final hiring decisions require human review.
      </footer>
    </main>
  );
}
