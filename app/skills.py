"""Skill taxonomy and extraction.

Each skill has a canonical name, a category and a list of aliases. Matching is
case-insensitive and respects word boundaries, so "Java" does not match
"JavaScript" and "Go" does not match "Google".
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Skill:
    name: str
    category: str
    aliases: tuple[str, ...]


SKILLS: tuple[Skill, ...] = (
    # Languages
    Skill("Python", "Languages", ("python", "python3")),
    Skill("Java", "Languages", ("java",)),
    Skill("JavaScript", "Languages", ("javascript", "js", "ecmascript")),
    Skill("TypeScript", "Languages", ("typescript", "ts")),
    Skill("C++", "Languages", ("c++", "cpp")),
    Skill("C#", "Languages", ("c#", "csharp", "c sharp")),
    Skill("C", "Languages", ("c",)),
    Skill("Go", "Languages", ("golang", "go lang")),
    Skill("Rust", "Languages", ("rust",)),
    Skill("PHP", "Languages", ("php",)),
    Skill("Ruby", "Languages", ("ruby",)),
    Skill("Kotlin", "Languages", ("kotlin",)),
    Skill("Swift", "Languages", ("swift",)),
    Skill("SQL", "Languages", ("sql",)),
    Skill("HTML/CSS", "Languages", ("html", "css", "html5", "css3")),
    Skill("Bash", "Languages", ("bash", "shell scripting", "shell")),
    Skill("MATLAB", "Languages", ("matlab",)),
    # Frameworks & libraries
    Skill("React", "Frameworks", ("react", "react.js", "reactjs")),
    Skill("Angular", "Frameworks", ("angular",)),
    Skill("Vue", "Frameworks", ("vue", "vue.js", "vuejs")),
    Skill("Next.js", "Frameworks", ("next.js", "nextjs")),
    Skill("Node.js", "Frameworks", ("node.js", "nodejs", "node")),
    Skill("Express", "Frameworks", ("express", "express.js")),
    Skill("Django", "Frameworks", ("django",)),
    Skill("Flask", "Frameworks", ("flask",)),
    Skill("FastAPI", "Frameworks", ("fastapi",)),
    Skill("Spring", "Frameworks", ("spring", "spring boot", "springboot")),
    Skill(".NET", "Frameworks", (".net", "dotnet", "asp.net")),
    Skill("Laravel", "Frameworks", ("laravel",)),
    Skill("Symfony", "Frameworks", ("symfony",)),
    Skill("WPF", "Frameworks", ("wpf",)),
    # Data & AI
    Skill("Machine Learning", "AI & Data", ("machine learning", "ml")),
    Skill("Deep Learning", "AI & Data", ("deep learning",)),
    Skill("LLMs", "AI & Data", ("llm", "llms", "large language model", "large language models", "generative ai", "genai")),
    Skill("NLP", "AI & Data", ("nlp", "natural language processing")),
    Skill("PyTorch", "AI & Data", ("pytorch",)),
    Skill("TensorFlow", "AI & Data", ("tensorflow",)),
    Skill("scikit-learn", "AI & Data", ("scikit-learn", "sklearn")),
    Skill("Pandas", "AI & Data", ("pandas",)),
    Skill("NumPy", "AI & Data", ("numpy",)),
    Skill("Data Analysis", "AI & Data", ("data analysis", "data analytics")),
    Skill("Snowflake", "AI & Data", ("snowflake",)),
    Skill("Spark", "AI & Data", ("spark", "pyspark", "apache spark")),
    # Databases
    Skill("PostgreSQL", "Databases", ("postgresql", "postgres")),
    Skill("MySQL", "Databases", ("mysql",)),
    Skill("MongoDB", "Databases", ("mongodb", "mongo")),
    Skill("Redis", "Databases", ("redis",)),
    Skill("SQLite", "Databases", ("sqlite",)),
    Skill("NoSQL", "Databases", ("nosql",)),
    # Cloud & DevOps
    Skill("AWS", "Cloud & DevOps", ("aws", "amazon web services", "lambda", "ec2", "s3", "dynamodb")),
    Skill("Azure", "Cloud & DevOps", ("azure",)),
    Skill("GCP", "Cloud & DevOps", ("gcp", "google cloud", "google cloud platform")),
    Skill("Docker", "Cloud & DevOps", ("docker", "containers", "containerization")),
    Skill("Kubernetes", "Cloud & DevOps", ("kubernetes", "k8s")),
    Skill("CI/CD", "Cloud & DevOps", ("ci/cd", "ci cd", "continuous integration", "continuous delivery", "github actions", "jenkins")),
    Skill("Terraform", "Cloud & DevOps", ("terraform",)),
    Skill("Linux", "Cloud & DevOps", ("linux", "unix")),
    Skill("Git", "Cloud & DevOps", ("git", "github", "gitlab", "version control")),
    Skill("Datadog", "Cloud & DevOps", ("datadog", "new relic", "observability")),
    # Practices
    Skill("REST APIs", "Practices", ("rest", "restful", "rest api", "rest apis", "api", "apis")),
    Skill("GraphQL", "Practices", ("graphql",)),
    Skill("Microservices", "Practices", ("microservices", "microservice")),
    Skill("Unit Testing", "Practices", ("unit testing", "unit tests", "pytest", "junit", "jest", "testing", "test automation")),
    Skill("Agile", "Practices", ("agile", "scrum", "sprint", "sprints", "kanban")),
    Skill("OOP", "Practices", ("oop", "object-oriented", "object oriented")),
    Skill("Data Structures & Algorithms", "Practices", ("data structures", "algorithms")),
    Skill("System Design", "Practices", ("system design", "distributed systems")),
    Skill("Security", "Practices", ("security", "cybersecurity", "secure coding")),
)

# Headings that mark the "nice to have" part of a job posting.
NICE_TO_HAVE_MARKERS = (
    "nice to have",
    "nice-to-have",
    "bonus",
    "preferred",
    "assets",
    "asset",
    "plus",
    "good to have",
)


def _alias_pattern(alias: str) -> re.Pattern[str]:
    # Lookarounds instead of \b so aliases with symbols (c++, c#, .net, ci/cd) still match.
    escaped = re.escape(alias.lower())
    return re.compile(rf"(?<![\w+#.]){escaped}(?![\w+#])")


_PATTERNS: dict[str, list[re.Pattern[str]]] = {
    s.name: [_alias_pattern(a) for a in s.aliases] for s in SKILLS
}
_BY_NAME = {s.name: s for s in SKILLS}

# Single-letter / very short aliases are noisy in prose ("c", "go", "ts").
# Only count "C" when it appears in a list-like context such as "C, C++" or "C/C++".
_STRICT = {"C"}
_C_CONTEXT = re.compile(r"(?:^|[\s,(/])c(?=\s*[,/)]|\s+(?:and|or)\s|\s*$)", re.MULTILINE)


def category_of(name: str) -> str:
    return _BY_NAME[name].category


def extract_skills(text: str) -> set[str]:
    """Return the canonical names of every skill mentioned in ``text``."""
    lowered = text.lower()
    found: set[str] = set()
    for name, patterns in _PATTERNS.items():
        if name in _STRICT:
            if _C_CONTEXT.search(lowered):
                found.add(name)
            continue
        if any(p.search(lowered) for p in patterns):
            found.add(name)
    return found


def split_requirements(job_text: str) -> tuple[str, str]:
    """Split a posting into (required part, nice-to-have part).

    Everything after the first line that looks like a nice-to-have heading is
    treated as optional. If no such heading exists, the whole posting is required.
    """
    lines = job_text.splitlines()
    for i, line in enumerate(lines):
        stripped = line.strip().lower().rstrip(":").strip("*#- ")
        if len(stripped) <= 40 and any(stripped.startswith(m) for m in NICE_TO_HAVE_MARKERS):
            return "\n".join(lines[:i]), "\n".join(lines[i:])
    return job_text, ""


def requirement_groups(text: str) -> list[frozenset[str]]:
    """Group skills that a posting lists as alternatives.

    "MySQL or PostgreSQL" means either one is enough, so those skills form a single
    group. A line with "or" groups the skills it mentions that share a category; every
    other skill is its own group.
    """
    groups: list[frozenset[str]] = []
    seen: set[str] = set()
    for line in text.splitlines():
        skills = extract_skills(line) - seen
        if not skills:
            continue
        if re.search(r"\bor\b", line.lower()):
            by_cat: dict[str, set[str]] = {}
            for name in skills:
                by_cat.setdefault(category_of(name), set()).add(name)
            for names in by_cat.values():
                groups.append(frozenset(names))
        else:
            groups.extend(frozenset({name}) for name in skills)
        seen |= skills
    return groups
