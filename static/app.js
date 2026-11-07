const $ = (id) => document.getElementById(id);

function fillList(id, items, emptyText = "None") {
  const ul = $(id);
  ul.innerHTML = "";
  if (!items.length) {
    const li = document.createElement("li");
    li.className = "empty";
    li.textContent = emptyText;
    ul.appendChild(li);
    return;
  }
  for (const item of items) {
    const li = document.createElement("li");
    li.textContent = item;
    ul.appendChild(li);
  }
}

function render(data) {
  $("score").textContent = data.score;
  $("summary").textContent = data.summary;
  $("source").textContent = data.source === "claude" ? "Suggestions by Claude" : "Rule-based suggestions";
  fillList("req-matched", data.required.matched);
  fillList("req-missing", data.required.missing);
  fillList("nice-matched", data.nice_to_have.matched);
  fillList("nice-missing", data.nice_to_have.missing);
  fillList("suggestions", data.suggestions);
  fillList("keywords", data.missing_keywords);
  const score = document.querySelector(".score");
  score.dataset.level = data.score >= 75 ? "high" : data.score >= 50 ? "mid" : "low";
  $("results").hidden = false;
  $("results").scrollIntoView({ behavior: "smooth" });
}

$("form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const error = $("error");
  error.hidden = true;
  const button = $("submit");
  button.disabled = true;
  button.textContent = "Analyzing...";

  try {
    const job = $("job").value.trim();
    const pdf = $("pdf").files[0];
    let response;
    if (pdf) {
      const body = new FormData();
      body.append("job", job);
      body.append("resume_pdf", pdf);
      response = await fetch("/api/analyze-pdf", { method: "POST", body });
    } else {
      response = await fetch("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ job, resume: $("resume").value.trim() }),
      });
    }
    const data = await response.json();
    if (!response.ok) {
      const detail = Array.isArray(data.detail) ? "Please paste at least a few lines in both boxes." : data.detail;
      throw new Error(detail || "Something went wrong.");
    }
    render(data);
  } catch (err) {
    error.textContent = err.message;
    error.hidden = false;
  } finally {
    button.disabled = false;
    button.textContent = "Analyze match";
  }
});
