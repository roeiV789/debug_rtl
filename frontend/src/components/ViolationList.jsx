const SEVERITY_CONFIG = {
  CRITICAL: { label: 'CRITICAL', className: 'badge-critical' },
  ERROR:    { label: 'ERROR',    className: 'badge-error' },
  WARNING:  { label: 'WARNING',  className: 'badge-warning' },
}

function SeverityBadge({ severity }) {
  const config = SEVERITY_CONFIG[severity] || { label: severity, className: 'badge-warning' }
  return (
    <span className={`severity-badge ${config.className}`}>
      {config.label}
    </span>
  )
}

function CycleChip({ cycle }) {
  return <span className="cycle-chip">cycle {cycle}</span>
}

function ViolationItem({ violation }) {
  return (
    <li className="list-item violation-item">
      <div className="violation-header">
        <SeverityBadge severity={violation.severity} />
        <span className="violation-rule-name">{violation.rule_name}</span>
        <span className="violation-rule-id">({violation.rule_id})</span>
      </div>
      <div className="violation-trigger">
        Triggered at cycle <strong>{violation.trigger_cycle}</strong>
      </div>
      <p className="violation-details">{violation.details}</p>
      {violation.relevant_cycles && violation.relevant_cycles.length > 0 && (
        <div className="relevant-cycles">
          <span className="relevant-cycles-label">Relevant cycles:</span>
          <div className="cycle-chips">
            {violation.relevant_cycles.map((c, i) => (
              <CycleChip key={i} cycle={c} />
            ))}
          </div>
        </div>
      )}
    </li>
  )
}

function FsmIssueItem({ issue }) {
  return (
    <li className="list-item fsm-item">
      <div className="fsm-transition">
        <span className="fsm-label">Invalid transition:</span>
        <span className="fsm-state">{issue.from_state}</span>
        <span className="fsm-arrow" aria-hidden="true">→</span>
        <span className="fsm-state">{issue.to_state}</span>
        <span className="fsm-cycle">at cycle <strong>{issue.cycle}</strong></span>
      </div>
      {issue.allowed_next && issue.allowed_next.length > 0 && (
        <div className="fsm-allowed">
          <span className="fsm-allowed-label">Allowed from {issue.from_state}:</span>
          <div className="cycle-chips">
            {issue.allowed_next.map((s, i) => (
              <span key={i} className="state-chip">{s}</span>
            ))}
          </div>
        </div>
      )}
    </li>
  )
}

export default function ViolationList({ violations, fsmIssues }) {
  const hasViolations = violations && violations.length > 0
  const hasFsmIssues = fsmIssues && fsmIssues.length > 0

  if (!hasViolations && !hasFsmIssues) {
    return (
      <section className="card">
        <h2 className="card-title">Violations &amp; FSM Issues</h2>
        <div className="empty-state">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
            <polyline points="22 4 12 14.01 9 11.01" />
          </svg>
          <p>No violations or FSM issues detected.</p>
        </div>
      </section>
    )
  }

  return (
    <section className="card">
      <h2 className="card-title">Violations &amp; FSM Issues</h2>

      {hasViolations && (
        <div className="subsection">
          <h3 className="subsection-title">
            Rule Violations
            <span className="count-badge">{violations.length}</span>
          </h3>
          <ul className="issue-list">
            {violations.map((v, i) => (
              <ViolationItem key={i} violation={v} />
            ))}
          </ul>
        </div>
      )}

      {hasFsmIssues && (
        <div className="subsection">
          <h3 className="subsection-title">
            FSM Issues
            <span className="count-badge">{fsmIssues.length}</span>
          </h3>
          <ul className="issue-list">
            {fsmIssues.map((issue, i) => (
              <FsmIssueItem key={i} issue={issue} />
            ))}
          </ul>
        </div>
      )}
    </section>
  )
}
