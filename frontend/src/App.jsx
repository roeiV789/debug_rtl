import { useState } from 'react'
import './App.css'
import FileUpload from './components/FileUpload.jsx'
import ViolationList from './components/ViolationList.jsx'
import InsightPanel from './components/InsightPanel.jsx'

export default function App() {
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  async function handleSubmit(specFile, simFile) {
    setLoading(true)
    setError(null)
    setResult(null)

    const formData = new FormData()
    formData.append('spec_file', specFile)
    formData.append('sim_file', simFile)

    try {
      const response = await fetch('http://localhost:8000/api/analyze', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        let errMsg = `Server error: ${response.status} ${response.statusText}`
        try {
          const errBody = await response.json()
          if (errBody.detail) errMsg = errBody.detail
        } catch (_) {}
        throw new Error(errMsg)
      }

      const data = await response.json()
      setResult(data)
    } catch (err) {
      setError(err.message || 'An unexpected error occurred.')
    } finally {
      setLoading(false)
    }
  }

  function handleReset() {
    setResult(null)
    setError(null)
    setLoading(false)
  }

  return (
    <div className="app-wrapper">
      <header className="app-header">
        <div className="header-inner">
          <span className="header-icon" aria-hidden="true">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="16 18 22 12 16 6" />
              <polyline points="8 6 2 12 8 18" />
            </svg>
          </span>
          <h1 className="app-title">RTL Debug Analyzer</h1>
          {result && (
            <button className="btn btn-secondary header-reset" onClick={handleReset}>
              New Analysis
            </button>
          )}
        </div>
      </header>

      <main className="app-main">
        {!result && !loading && (
          <FileUpload onSubmit={handleSubmit} />
        )}

        {loading && (
          <div className="loading-container">
            <div className="spinner" aria-label="Analyzing..." />
            <p className="loading-text">Analyzing your simulation trace…</p>
          </div>
        )}

        {error && !loading && (
          <div className="error-banner" role="alert">
            <span className="error-icon">⚠</span>
            <div className="error-content">
              <strong>Analysis Failed</strong>
              <p>{error}</p>
            </div>
            <button className="btn btn-secondary" onClick={handleReset}>
              Try Again
            </button>
          </div>
        )}

        {result && !loading && (
          <div className="results-container">
            <ViolationList
              violations={result.violations}
              fsmIssues={result.fsm_issues}
            />
            <InsightPanel
              aiSummary={result.ai_summary}
              recommendations={result.ai_recommendations}
            />
          </div>
        )}
      </main>

      <footer className="app-footer">
        <p>RTL Debug Analyzer — Hardware Validation Tool</p>
      </footer>
    </div>
  )
}
