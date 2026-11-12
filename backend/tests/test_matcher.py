from matcher import compare_candidates, match_candidate, normalize_skill
from models import CandidateProfile, JobRequirements


def test_skill_aliases():
    assert normalize_skill("React.js") == "react"
    assert normalize_skill("ReactJS") == "react"
    assert normalize_skill("JS") == "javascript"
    assert normalize_skill("Springboot") == "spring boot"


def test_required_skill_matching():
    candidate = CandidateProfile(skills=["React", "JavaScript", "HTML"])
    job = JobRequirements(
        job_title="Frontend Developer",
        required_skills=["React.js", "JavaScript", "Python"],
    )
    result = match_candidate(candidate, job)
    assert len(result["skills"]["matched_required"]) == 2
    assert "python" in result["skills"]["missing_required"]


def test_experience_matching():
    candidate = CandidateProfile(total_experience_years=2)
    job = JobRequirements(job_title="Developer", minimum_experience_years=1)
    result = match_candidate(candidate, job)
    assert result["experience"]["status"] == "Meets requirement"


def test_missing_experience_is_not_assessed():
    candidate = CandidateProfile()
    job = JobRequirements(job_title="Developer", minimum_experience_years=2)
    result = match_candidate(candidate, job)
    assert result["experience"]["score"] is None
    assert result["experience"]["status"] == "Not assessable from resume"


def test_empty_criteria_has_no_score():
    candidate = CandidateProfile()
    job = JobRequirements(job_title="Developer")
    result = match_candidate(candidate, job)
    assert result["match_percentage"] is None


def test_batch_comparison_ranks_candidates():
    candidates = [
        CandidateProfile(name="Candidate A", skills=["Python"]),
        CandidateProfile(name="Candidate B", skills=["React", "JavaScript"]),
    ]
    job = JobRequirements(
        job_title="Frontend Developer",
        required_skills=["React", "JavaScript"],
    )
    results = compare_candidates(candidates, job)
    assert results[0]["candidate_name"] == "Candidate B"
    assert results[0]["rank"] == 1
    assert results[1]["rank"] == 2
