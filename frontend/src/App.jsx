import { useState } from "react";
import "./App.css";

const API_URL = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";

const SAMPLE_TEXTS = [
  {
    title: "Legal / Terms",
    text: "Notwithstanding anything to the contrary contained herein, the Licensor hereby disclaims all warranties, express or implied, including without limitation warranties of merchantability and fitness for a particular purpose.",
    level: 6,
  },
  {
    title: "Academic / Medical",
    text: "Hypercholesterolemia, particularly characterized by elevated serum low-density lipoprotein cholesterol levels, serves as a predominant etiology in the pathogenesis of atherosclerotic cardiovascular pathology.",
    level: 7,
  },
  {
    title: "Technical",
    text: "The asynchronous non-blocking event-driven architecture optimizes throughput by delegating input-output operations to ambient system threads, thereby mitigating thread context-switching overhead.",
    level: 5,
  },
];

const METRIC_CONFIG = {
  flesch_kincaid_grade: { label: "Grade Level", unit: "" },
  syllable_count: { label: "Syllables", unit: "" },
  average_sentence_length: {
    label: "Avg. Sentence Length",
    unit: " words",
  },
  average_dependency_depth: {
    label: "Avg. Syntax Depth",
    unit: "",
  },
  maximum_dependency_depth: {
    label: "Max Syntax Depth",
    unit: "",
  },
};

function DeltaBadge({ original, rewritten, config, direction }) {
  if (original === undefined || rewritten === undefined) {
    return null;
  }

  const diff = Math.round((rewritten - original) * 10) / 10;

  if (diff === 0) {
    return <span className="delta neutral">No change</span>;
  }

  const movedInExpectedDirection =
    direction === "simplify"
      ? diff < 0
      : direction === "elevate"
        ? diff > 0
        : false;

  const formattedDiff = diff > 0 ? `+${diff}` : `${diff}`;

  return (
    <span
      className={`delta ${movedInExpectedDirection ? "improved" : "increased"}`}
    >
      {formattedDiff}
      {config.unit}
    </span>
  );
}

function Metrics({ originalMetrics, rewrittenMetrics, direction }) {
  if (!originalMetrics) return null;

  return (
    <div className="metrics-grid">
      {Object.entries(METRIC_CONFIG).map(([key, config]) => {
        const orig = originalMetrics[key];
        const rew = rewrittenMetrics ? rewrittenMetrics[key] : null;

        return (
          <div className="metric-card" key={key}>
            <div className="metric-header">
              <span className="metric-label">{config.label}</span>
              {rew !== null && (
                <DeltaBadge
                  original={orig}
                  rewritten={rew}
                  config={config}
                  direction={direction}
                />
              )}
            </div>
            <div className="metric-values">
              {rew !== null ? (
                <>
                  <span className="val-new">
                    {typeof rew === "number" ? rew.toFixed(1) : rew}
                  </span>
                  <span className="val-old">
                    from {typeof orig === "number" ? orig.toFixed(1) : orig}
                  </span>
                </>
              ) : (
                <span className="val-single">
                  {typeof orig === "number" ? orig.toFixed(1) : orig}
                </span>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}

function App() {
  const [text, setText] = useState("");
  const [targetLevel, setTargetLevel] = useState(5);
  const [result, setResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);

  const wordCount = text.trim() ? text.trim().split(/\s+/).length : 0;
  const charCount = text.length;

  const GRADE_TIERS = [
    { level: 3, label: "Elementary" },
    { level: 5, label: "Upper Elementary" },
    { level: 8, label: "Middle School" },
    { level: 11, label: "High School" },
    { level: 14, label: "College" },
  ];

  async function handleSubmit(event) {
    event?.preventDefault();

    if (!text.trim()) {
      setError("Please enter or select a passage to tune.");
      return;
    }

    setIsLoading(true);
    setError("");
    setResult(null);
    setCopied(false);

    try {
      const response = await fetch(`${API_URL}/api/adjust`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text,
          target_level: Number(targetLevel),
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : "The text could not be tuned.",
        );
      }

      setResult(data);
    } catch (requestError) {
      setError(
        requestError.message || "Could not connect to the tuned server.",
      );
    } finally {
      setIsLoading(false);
    }
  }

  function handleCopy() {
    if (!result?.rewritten_text) return;
    navigator.clipboard.writeText(result.rewritten_text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  function loadSample(sample) {
    setText(sample.text);
    setTargetLevel(sample.level);
    setResult(null);
    setError("");
    setCopied(false);
  }

  return (
    <div className="app-layout">
      <nav className="navbar">
        <div className="name">
          <span>ReadabilityLab</span>
        </div>
        <a
          href="https://github.com"
          target="_blank"
          rel="noreferrer"
          className="nav-link"
        >
          Docs & API
        </a>
      </nav>

      <main className="container">
        <header className="hero">
          <h1 className="hero-title">
            Rewrite for the <em>reading level you need.</em>
          </h1>
          <p className="hero-subtitle">
            Simplify complex writing or elevate simple prose while preserving
            its original meaning.
          </p>
        </header>

        <div className="samples-bar">
          <span className="samples-label">Try a sample:</span>
          {SAMPLE_TEXTS.map((sample, idx) => (
            <button
              key={idx}
              type="button"
              className="sample-chip"
              onClick={() => loadSample(sample)}
            >
              {sample.title}
            </button>
          ))}
        </div>

        <div className="workspace">
          <div className="panel panel-input">
            <div className="panel-header">
              <span className="panel-title">Original Content</span>
              <div className="panel-actions">
                {text && (
                  <button
                    type="button"
                    className="btn-ghost"
                    onClick={() => {
                      setText("");
                      setResult(null);
                    }}
                  >
                    Clear
                  </button>
                )}
              </div>
            </div>

            <textarea
              className="editor-textarea"
              value={text}
              onChange={(event) => {
                setText(event.target.value);
                setResult(null);
                setError("");
                setCopied(false);
              }}
              placeholder="Paste or type here..."
              rows={8}
            />

            <div className="editor-meta">
              <span className="word-count">
                {wordCount} words • {charCount} characters
              </span>
            </div>

            <div className="controls-footer">
              <div className="grade-selector">
                <label className="field-label">Target Reading Level</label>
                <div className="pill-grid">
                  {GRADE_TIERS.map((tier) => {
                    const isActive = Number(targetLevel) === tier.level;
                    return (
                      <button
                        key={tier.level}
                        type="button"
                        className={`grade-pill ${isActive ? "active" : ""}`}
                        onClick={() => setTargetLevel(tier.level)}
                      >
                        <span className="pill-grade">Grade {tier.level}</span>
                        <span className="pill-tier">{tier.label}</span>
                      </button>
                    );
                  })}
                </div>
                <label htmlFor="target-level" className="field-label">
                  Target grade: {targetLevel}
                </label>

                <input
                  id="target-level"
                  type="range"
                  min="1"
                  max="16"
                  value={targetLevel}
                  onChange={(event) =>
                    setTargetLevel(Number(event.target.value))
                  }
                />
              </div>

              <button
                type="button"
                className="btn-primary"
                onClick={handleSubmit}
                disabled={isLoading || !text.trim()}
              >
                {isLoading ? (
                  <span className="loading-state">
                    <span className="spinner" /> Tuning...
                  </span>
                ) : (
                  <>Tune Readability →</>
                )}
              </button>
            </div>
          </div>

          <div className="panel panel-output">
            <div className="panel-header">
              <div className="panel-title-group">
                <span className="panel-title">Tuned Output</span>
                {result && (
                  <>
                    <span className="direction-badge">
                      {result.direction === "simplify"
                        ? "Simplified"
                        : result.direction === "elevate"
                          ? "Elevated"
                          : "Already on target"}
                    </span>

                    <span className="iteration-badge">
                      {result.iterations}{" "}
                      {result.iterations === 1 ? "pass" : "passes"}
                    </span>
                  </>
                )}
              </div>
              {result && (
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={handleCopy}
                >
                  {copied ? "✓ Copied" : "Copy Result"}
                </button>
              )}
            </div>

            <div className="output-content">
              {isLoading && (
                <div className="skeleton-loader">
                  <div className="skeleton-line" style={{ width: "92%" }} />
                  <div className="skeleton-line" style={{ width: "85%" }} />
                  <div className="skeleton-line" style={{ width: "78%" }} />
                  <div className="skeleton-line" style={{ width: "60%" }} />
                </div>
              )}

              {error && <div className="error-banner">{error}</div>}

              {!isLoading && !error && !result && (
                <div className="placeholder-state">
                  <div className="placeholder-icon">✍️</div>
                  <p className="placeholder-text">
                    Your tuned text will appear here with readability metrics
                    breakdown.
                  </p>
                </div>
              )}

              {!isLoading && result && (
                <div className="result-display">
                  <p className="rewritten-text">{result.rewritten_text}</p>
                </div>
              )}
            </div>

            {result && (
              <div className="metrics-section">
                <h3 className="metrics-title">Readability Breakdown</h3>
                <Metrics
                  originalMetrics={result.original_metrics}
                  rewrittenMetrics={result.rewritten_metrics}
                  direction={result.direction}
                />
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
