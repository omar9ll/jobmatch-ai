from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

JOB = "Requirements: Python, FastAPI, Docker and AWS experience. Nice to have: Kubernetes."
RESUME = "Python developer who built REST APIs with FastAPI and deployed with Docker."


def test_health():
    assert client.get("/api/health").json() == {"status": "ok"}


def test_analyze(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    res = client.post("/api/analyze", json={"resume": RESUME, "job": JOB})
    assert res.status_code == 200
    data = res.json()
    assert data["source"] == "rules"
    assert "AWS" in data["required"]["missing"]
    assert "FastAPI" in data["required"]["matched"]
    assert isinstance(data["suggestions"], list) and data["suggestions"]


def test_analyze_rejects_short_input():
    res = client.post("/api/analyze", json={"resume": "hi", "job": JOB})
    assert res.status_code == 422


def test_pdf_rejects_non_pdf():
    res = client.post(
        "/api/analyze-pdf",
        data={"job": JOB},
        files={"resume_pdf": ("resume.txt", b"not a pdf", "text/plain")},
    )
    assert res.status_code == 400


def test_index_served():
    res = client.get("/")
    assert res.status_code == 200
    assert "JobMatch" in res.text
