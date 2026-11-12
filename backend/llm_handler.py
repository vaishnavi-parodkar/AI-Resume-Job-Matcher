
import json
import logging
import os
import re
from datetime import date

from dotenv import load_dotenv
from groq import Groq
from pydantic import ValidationError

from models import CandidateProfile
from prompts import SYSTEM_PROMPT, create_user_prompt

load_dotenv()
logger = logging.getLogger(__name__)


def parse_month_year(duration: str):
    """
    Extract month and year from dates such as:
    Aug 2026 - Sep 2026
    January 2024 - Present

    Returns None if the dates cannot be reliably identified.
    """

    if not duration:
        return None

    text = duration.lower().replace("–", "-").replace("—", "-")

    month_map = {
        "jan": 1, "january": 1,
        "feb": 2, "february": 2,
        "mar": 3, "march": 3,
        "apr": 4, "april": 4,
        "may": 5,
        "jun": 6, "june": 6,
        "jul": 7, "july": 7,
        "aug": 8, "august": 8,
        "sep": 9, "sept": 9, "september": 9,
        "oct": 10, "october": 10,
        "nov": 11, "november": 11,
        "dec": 12, "december": 12,
    }

    matches = re.findall(
        r"\b([a-zA-Z]+)\s+(\d{4})\b",
        text
    )

    if not matches:
        return None

    dates = []

    for month_name, year in matches:
        month = month_map.get(month_name.lower())

        if month is None:
            return None

        dates.append((int(year), month))

    if len(dates) < 2:
        return None

    start = dates[0]
    end = dates[1]

    if end < start:
        return None

    return start, end


def calculate_professional_experience(experience):
    """
    Calculate experience using only employment and internships.

    Open-source contributions, projects, education and coursework
    must not be included.
    """

    intervals = []

    for item in experience:
        role = (item.role or "").lower()
        company = (item.company or "").lower()
        description = (item.description or "").lower()

        # Exclude open-source contributions.
        excluded_terms = [
            "open-source contributor",
            "open source contributor",
            "gssoc",
            "hacktoberfest",
        ]

        if any(term in role or term in company for term in excluded_terms):
            continue

        # Include employment and internships only.
        eligible = any(
            term in role
            for term in [
                "intern",
                "employee",
                "engineer",
                "developer",
                "consultant",
                "analyst",
                "trainee",
                "associate",
            ]
        )

        if not eligible:
            continue

        parsed_dates = parse_month_year(item.duration or "")

        if parsed_dates is None:
            continue

        start, end = parsed_dates

        intervals.append(
            (start[0] * 12 + start[1], end[0] * 12 + end[1])
        )

    if not intervals:
        return None

    # Merge overlapping employment periods to avoid double-counting.
    intervals.sort()

    merged = []
    current_start, current_end = intervals[0]

    for start, end in intervals[1:]:
        if start <= current_end + 1:
            current_end = max(current_end, end)
        else:
            merged.append((current_start, current_end))
            current_start, current_end = start, end

    merged.append((current_start, current_end))

    total_months = sum(
        end - start + 1
        for start, end in merged
    )

    return round(total_months / 12, 2)


def analyze_resume(resume_text: str) -> dict:
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is missing. Add it to backend/.env and restart the API."
        )

    model = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
    client = Groq(api_key=api_key)

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": create_user_prompt(resume_text)},
            ],
            temperature=0.1,
            max_completion_tokens=4096,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content or ""

        if not content.strip():
            raise RuntimeError("Groq returned an empty response.")

        parsed = json.loads(content)
        profile = CandidateProfile.model_validate(parsed)

    except json.JSONDecodeError:
        logger.exception("Groq returned invalid JSON.")
        raise RuntimeError(
            "Groq returned invalid JSON. Check the backend terminal."
        ) from None

    except ValidationError:
        logger.exception("Groq response did not match CandidateProfile.")
        raise RuntimeError(
            "Groq response did not match the candidate profile structure."
        ) from None

    except RuntimeError:
        raise

    except Exception:
        logger.exception("Groq API request failed.")
        raise RuntimeError(
            "Groq request failed. Check the backend terminal."
        ) from None

    # Calculate experience using Python, not the LLM estimate.
    calculated_experience = calculate_professional_experience(
        profile.experience
    )

    profile.total_experience_years = calculated_experience

    usage = response.usage

    return {
        "candidate": profile.model_dump(),
        "usage": {
            "prompt_tokens": getattr(usage, "prompt_tokens", None),
            "completion_tokens": getattr(usage, "completion_tokens", None),
            "total_tokens": getattr(usage, "total_tokens", None),
        },
        "model": model,
    }
