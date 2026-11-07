"""Resume vs. job posting scoring."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field

from .skills import category_of, extract_skills, requirement_groups, split_requirements

REQUIRED_WEIGHT = 2.0
NICE_WEIGHT = 1.0

STOPWORDS = set(
    """
    a about above after again all also am an and any are as at be because been before being below
    between both but by can could did do does doing down during each few for from further had has
    have having he her here hers him his how i if in into is it its itself just me more most my no
    nor not now of off on once only or other our ours out over own same she should so some such
    than that the their theirs them then there these they this those through to too under until up
    very was we were what when where which while who whom why will with would you your yours
    able ability across work working team teams role you'll we're our us including strong experience
    years year plus etc using use new well within based must required requirements responsibilities
    looking join help build building ensure knowledge understanding skills skill excellent good great
    opportunity candidate candidates position company apply time per one two three write writing
    environment co-op coop intern internship interns develop developing maintain components tools
    concepts interest exposure familiarity projects project nice have such like various related
    """.split()
)

_WORD = re.compile(r"[a-zA-Z][a-zA-Z+#.\-]{2,}")


@dataclass
class MatchResult:
    score: int
    required_matched: list[str] = field(default_factory=list)
    required_missing: list[str] = field(default_factory=list)
    nice_matched: list[str] = field(default_factory=list)
    nice_missing: list[str] = field(default_factory=list)
    missing_keywords: list[str] = field(default_factory=list)
    by_category: dict[str, dict[str, list[str]]] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "score": self.score,
            "required": {"matched": self.required_matched, "missing": self.required_missing},
            "nice_to_have": {"matched": self.nice_matched, "missing": self.nice_missing},
            "missing_keywords": self.missing_keywords,
            "by_category": self.by_category,
        }


def top_keywords(text: str, limit: int = 25) -> list[str]:
    words = [w.lower().strip(".-") for w in _WORD.findall(text)]
    counts = Counter(w for w in words if w not in STOPWORDS and len(w) > 2)
    return [w for w, _ in counts.most_common(limit)]


def _in_text(word: str, text_lower: str) -> bool:
    # Treat simple plurals as the same word ("apis" vs "api", "tests" vs "test").
    return word in text_lower or (word.endswith("s") and word[:-1] in text_lower)


def _label(group: frozenset[str]) -> str:
    return " / ".join(sorted(group))


def _score_groups(groups, resume_skills, weight):
    total = earned = 0.0
    matched, missing = [], []
    for group in groups:
        total += weight
        hits = group & resume_skills
        if hits:
            earned += weight
            matched.extend(sorted(hits))
        else:
            missing.append(_label(group))
    return total, earned, matched, missing


def match(resume_text: str, job_text: str) -> MatchResult:
    required_part, nice_part = split_requirements(job_text)
    resume_skills = extract_skills(resume_text)

    required_groups = requirement_groups(required_part)
    required_all = set().union(*required_groups) if required_groups else set()
    nice_groups = [g - required_all for g in requirement_groups(nice_part)]
    nice_groups = [g for g in nice_groups if g]

    r_total, r_earned, r_matched, r_missing = _score_groups(required_groups, resume_skills, REQUIRED_WEIGHT)
    n_total, n_earned, n_matched, n_missing = _score_groups(nice_groups, resume_skills, NICE_WEIGHT)
    total = r_total + n_total
    score = round(100 * (r_earned + n_earned) / total) if total else 0

    resume_lower = resume_text.lower()
    missing_kw = [k for k in top_keywords(job_text) if not _in_text(k, resume_lower)][:10]

    by_category: dict[str, dict[str, list[str]]] = {}
    for name in sorted(required_all | set().union(*nice_groups) if nice_groups else required_all):
        bucket = by_category.setdefault(category_of(name), {"matched": [], "missing": []})
        bucket["matched" if name in resume_skills else "missing"].append(name)

    return MatchResult(
        score=score,
        required_matched=sorted(set(r_matched)),
        required_missing=r_missing,
        nice_matched=sorted(set(n_matched)),
        nice_missing=n_missing,
        missing_keywords=missing_kw,
        by_category=by_category,
    )
