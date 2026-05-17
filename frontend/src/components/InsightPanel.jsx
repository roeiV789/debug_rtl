import ReactMarkdown from 'react-markdown'

function RecommendationItem({ recommendation, index }) {
  return (
    <details className="recommendation-item">
      <summary className="recommendation-summary">
        <span className="recommendation-index">{index + 1}</span>
        <span className="recommendation-title">{recommendation.title}</span>
        <span className="recommendation-chevron" aria-hidden="true">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="6 9 12 15 18 9" />
          </svg>
        </span>
      </summary>
      <div className="recommendation-body">
        <ReactMarkdown>{recommendation.body}</ReactMarkdown>
      </div>
    </details>
  )
}

export default function InsightPanel({ aiSummary, recommendations }) {
  const hasRecommendations = recommendations && recommendations.length > 0

  return (
    <section className="card insight-panel">
      <h2 className="card-title">AI Analysis</h2>

      {aiSummary && (
        <div className="subsection">
          <h3 className="subsection-title">Summary</h3>
          <div className="ai-summary markdown-body">
            <ReactMarkdown>{aiSummary}</ReactMarkdown>
          </div>
        </div>
      )}

      {hasRecommendations && (
        <div className="subsection">
          <h3 className="subsection-title">
            Recommendations
            <span className="count-badge">{recommendations.length}</span>
          </h3>
          <div className="recommendations-list">
            {recommendations.map((rec, i) => (
              <RecommendationItem key={i} recommendation={rec} index={i} />
            ))}
          </div>
        </div>
      )}

      {!aiSummary && !hasRecommendations && (
        <div className="empty-state">
          <p>No AI insights available.</p>
        </div>
      )}
    </section>
  )
}
