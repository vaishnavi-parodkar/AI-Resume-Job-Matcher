
import re

SKILL_ALIASES = {
    "react.js": "react",
    "reactjs": "react",
    "react": "react",
    "js": "javascript",
    "javascript": "javascript",
    "node.js": "node",
    "nodejs": "node",
    "node": "node",
    "springboot": "spring boot",
    "spring-boot": "spring boot",
    "spring boot": "spring boot",
    "tailwindcss": "tailwind css",
    "html5": "html",
    "css3": "css",
    "mysql database": "mysql",
    "restful api": "rest api",
    "rest apis": "rest api",
    "rest apis development": "rest api",
}


def normalize_skill(skill: str) -> str:
    normalized = " ".join(skill.strip().lower().split())
    normalized = SKILL_ALIASES.get(normalized, normalized)
    return normalized


def normalize_text(value: str) -> str:
    """Normalize text for flexible education comparisons."""
    value = value.lower()
    value = re.sub(r"[^a-z0-9\s]", " ", value)
    return " ".join(value.split())


def match_education(candidate, requirement: str):
    """
    Match education using explicit degree or field-of-study evidence.

    Does not assume that unrelated qualifications are equivalent.
    """

    if not candidate.education:
        return None, "Not assessable from resume"

    candidate_entries = []

    for item in candidate.education:
        degree = item.degree or ""
        institution = item.institution or ""

        candidate_entries.append(
            normalize_text(degree + " " + institution)
        )

    requirement_text = normalize_text(requirement)

    # Remove generic degree wording so that the actual field
    # of study can be compared separately.
    generic_terms = [
        "bachelor",
        "bachelors",
        "degree",
        "master",
        "masters",
        "in",
        "of",
        "the",
    ]

    requirement_words = [
        word for word in requirement_text.split()
        if word not in generic_terms
    ]

    # Match explicit fields of study.
    # Example:
    # Computer Engineering matches
    # Bachelor of Engineering in Computer Engineering.
    field_terms = [
        "computer engineering",
        "computer science",
        "information technology",
        "information science",
        "software engineering",
        "electronics engineering",
        "electrical engineering",
    ]

    requested_fields = [
        field for field in field_terms
        if field in requirement_text
    ]

    for entry in candidate_entries:
        if not entry.strip():
            continue

        # Explicit field-of-study match.
        if any(field in entry for field in requested_fields):
            return 100, "Requirement found"

        # General phrase match for other requirements.
        if requirement_text and requirement_text in entry:
            return 100, "Requirement found"

        # Match meaningful words when no known field is specified.
        if not requested_fields and requirement_words:
            meaningful_words = [
                word for word in requirement_words
                if len(word) > 2
            ]

            if meaningful_words and all(
                word in entry for word in meaningful_words
            ):
                return 100, "Requirement found"

    return 0, "Requirement not found"


def match_candidate(candidate, job) -> dict:
    candidate_skills = {
        normalize_skill(skill)
        for skill in candidate.skills
        if skill and skill.strip()
    }

    required = {
        normalize_skill(skill)
        for skill in job.required_skills
        if skill and skill.strip()
    }

    preferred = {
        normalize_skill(skill)
        for skill in job.preferred_skills
        if skill and skill.strip()
    }

    matched_required = candidate_skills & required
    missing_required = required - candidate_skills

    matched_preferred = candidate_skills & preferred
    missing_preferred = preferred - candidate_skills

    # SKILL SCORE
    skill_score = None

    if required or preferred:
        required_score = (
            len(matched_required) / len(required)
            if required else None
        )

        preferred_score = (
            len(matched_preferred) / len(preferred)
            if preferred else None
        )

        if required_score is not None and preferred_score is not None:
            skill_score = (
                required_score * 0.8 +
                preferred_score * 0.2
            ) * 100

        elif required_score is not None:
            skill_score = required_score * 100

        else:
            skill_score = preferred_score * 100

    # EXPERIENCE SCORE
    experience_score = None
    experience_status = "Not specified by HR"

    if job.minimum_experience_years is not None:

        required_years = job.minimum_experience_years
        candidate_years = candidate.total_experience_years

        # If HR requires zero years, the candidate automatically
        # satisfies the experience requirement.
        if required_years == 0:
            experience_score = 100
            experience_status = "No prior experience required"

        elif candidate_years is None:
            experience_status = "Not assessable from resume"

        elif candidate_years >= required_years:
            experience_score = 100
            experience_status = "Meets requirement"

        else:
            experience_score = 0
            experience_status = "Below requirement"

    # EDUCATION SCORE
    education_score = None
    education_status = "Not specified by HR"

    if job.education_requirement and job.education_requirement.strip():
        education_score, education_status = match_education(
            candidate,
            job.education_requirement
        )

    # OVERALL SCORE
    components = []

    if skill_score is not None:
        components.append((skill_score, 60))

    if experience_score is not None:
        components.append((experience_score, 25))

    if education_score is not None:
        components.append((education_score, 15))

    overall_score = None

    if components:
        total_weight = sum(weight for _, weight in components)

        overall_score = round(
            sum(score * weight for score, weight in components)
            / total_weight,
            2
        )

    # RECOMMENDATIONS
    recommendations = []

    if missing_required:
        recommendations.append(
            "Review evidence for missing required skills: "
            + ", ".join(sorted(missing_required))
        )

    if missing_preferred:
        recommendations.append(
            "Preferred skills not found: "
            + ", ".join(sorted(missing_preferred))
        )

    if experience_status == "Below requirement":
        recommendations.append(
            "The stated professional experience is below "
            "the minimum requirement."
        )

    elif experience_status == "Not assessable from resume":
        recommendations.append(
            "Verify the candidate's professional experience "
            "during screening."
        )

    if education_status == "Requirement not found":
        recommendations.append(
            "Review the candidate's educational qualifications manually."
        )

    elif education_status == "Not assessable from resume":
        recommendations.append(
            "Verify the candidate's education details."
        )

    if not recommendations:
        recommendations.append(
            "The available information matches the configured criteria. "
            "Review the original resume before making a decision."
        )

    return {
        "job_title": job.job_title,
        "match_percentage": overall_score,

        "skills": {
            "matched_required": sorted(matched_required),
            "missing_required": sorted(missing_required),
            "matched_preferred": sorted(matched_preferred),
            "missing_preferred": sorted(missing_preferred),
            "score": round(skill_score, 2)
            if skill_score is not None else None,
        },

        "experience": {
            "candidate_years": candidate.total_experience_years,
            "required_years": job.minimum_experience_years,
            "status": experience_status,
            "score": experience_score,
        },

        "education": {
            "requirement": job.education_requirement,
            "status": education_status,
            "score": education_score,
        },

        "recommendations": recommendations,
    }


def compare_candidates(candidates, job) -> list[dict]:
    results = []

    for index, candidate in enumerate(candidates, start=1):
        report = match_candidate(candidate, job)

        results.append({
            "candidate_id": index,
            "candidate_name": candidate.name or f"Candidate {index}",
            "candidate_email": candidate.email,
            "match_report": report,
        })

    results.sort(
        key=lambda item: (
            item["match_report"]["match_percentage"] is not None,
            item["match_report"]["match_percentage"]
            if item["match_report"]["match_percentage"] is not None
            else -1,
        ),
        reverse=True,
    )

    for rank, item in enumerate(results, start=1):
        item["rank"] = rank

    return results
