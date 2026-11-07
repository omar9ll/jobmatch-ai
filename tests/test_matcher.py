from app.llm import rule_based_suggestions
from app.matcher import match
from app.skills import extract_skills, split_requirements

JOB = """Software Developer Co-op

Requirements:
- Experience with Python and React
- Familiarity with SQL databases such as PostgreSQL
- Git and Agile workflows

Nice to have:
- Docker
- Exposure to LLMs
"""

RESUME = """Built backend pipelines in Python and a React website.
Wrote SQL queries and used Git daily on an Agile team."""


def test_java_does_not_match_javascript():
    assert extract_skills("Built apps in JavaScript") == {"JavaScript"}
    assert "Java" in extract_skills("Strong Java and Spring Boot skills")


def test_symbol_skills():
    found = extract_skills("Languages: C++, C#, and .NET; CI/CD with GitHub Actions")
    assert {"C++", "C#", ".NET", "CI/CD"} <= found


def test_split_requirements():
    required, nice = split_requirements(JOB)
    assert "Python" in required
    assert "Docker" in nice and "Docker" not in required


def test_match_scores_and_lists():
    result = match(RESUME, JOB)
    assert "Python" in result.required_matched
    assert "PostgreSQL" in result.required_missing
    assert "Docker" in result.nice_missing
    assert 0 < result.score < 100


def test_perfect_match_scores_100():
    resume = RESUME + " PostgreSQL, Docker and LLM experience."
    assert match(resume, JOB).score == 100


def test_empty_posting_scores_zero():
    assert match(RESUME, "We are hiring a great person to join us.").score == 0


def test_rule_based_suggestions_mention_missing_skill():
    result = match(RESUME, JOB)
    out = rule_based_suggestions(result)
    assert out["source"] == "rules"
    assert any("PostgreSQL" in s for s in out["suggestions"])


def test_alternatives_count_once():
    job = "Requirements:\n- Relational databases (MySQL or PostgreSQL)\n- Python"
    result = match("Python and PostgreSQL experience.", job)
    assert result.score == 100
    assert result.required_missing == []
    result = match("Python only.", job)
    assert result.required_missing == ["MySQL / PostgreSQL"]
