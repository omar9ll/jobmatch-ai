"""Optional LLM-powered suggestions.

If ``ANTHROPIC_API_KEY`` is set, Claude writes tailored suggestions for the
resume. Without a key (or if the call fails) the app falls back to rule-based
suggestions, so it always works offline and in tests.
"""

from __future__ import annotations

import json
import logging
import os

from .matcher import MatchResult

log = logging.getLogger(__name__)

DEFAULT_MODEL = "claude-sonnet-4-5"

PROMPT = """You are a career coach helping a student tailor their resume to a job posting.

Job posting:
<job>
{job}
</job>

Resume:
<resume>
{resume}
</resume>

Skill analysis: matched required = {matched}; missing required = {missing}; missing nice-to-have = {nice_missing}.

Return ONLY a JSON object with:
- "summary": 2 sentences on how well the resume fits the role.
- "suggestions": 3 to 5 specific, actionable edits. Rewrite or strengthen existing resume bullets
  so they reflect the posting's language. Never invent experience, employers, numbers or skills
  that are not already in the resume; if a required skill is missing, say to add it only if the
  candidate really has it.
"""


def rule_based_suggestions(result: MatchResult) -> dict:
    suggestions: list[str] = []
    for skill in result.required_missing[:3]:
        suggestions.append(
            f"The posting requires {skill}. If you have used it (courses, projects or work), "
            f"add it to your skills section and mention it in a relevant bullet."
        )
    if result.missing_keywords:
        kws = ", ".join(result.missing_keywords[:5])
        suggestions.append(f"Mirror the posting's wording where it is accurate for you, e.g. {kws}.")
    if result.required_matched:
        top = ", ".join(result.required_matched[:3])
        suggestions.append(
            f"Lead your strongest bullets with skills they asked for ({top}) and add measurable impact."
        )
    if not suggestions:
        suggestions.append("Your resume already covers the listed skills. Focus on quantifying impact.")

    if result.score >= 75:
        fit = "Strong match"
    elif result.score >= 50:
        fit = "Moderate match"
    else:
        fit = "Weak match"
    summary = f"{fit}: your resume covers {result.score}% of the weighted skills in this posting."
    return {"summary": summary, "suggestions": suggestions, "source": "rules"}


def ai_suggestions(resume: str, job: str, result: MatchResult) -> dict:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return rule_based_suggestions(result)
    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model=os.getenv("ANTHROPIC_MODEL", DEFAULT_MODEL),
            max_tokens=800,
            messages=[
                {
                    "role": "user",
                    "content": PROMPT.format(
                        job=job[:8000],
                        resume=resume[:8000],
                        matched=result.required_matched,
                        missing=result.required_missing,
                        nice_missing=result.nice_missing,
                    ),
                }
            ],
        )
        text = "".join(block.text for block in message.content if getattr(block, "type", "") == "text")
        start, end = text.find("{"), text.rfind("}")
        data = json.loads(text[start : end + 1])
        return {
            "summary": str(data.get("summary", "")),
            "suggestions": [str(s) for s in data.get("suggestions", [])][:5],
            "source": "claude",
        }
    except Exception as exc:  # network, auth, parsing: never break the request
        log.warning("LLM suggestions failed, using rules: %s", exc)
        return rule_based_suggestions(result)
