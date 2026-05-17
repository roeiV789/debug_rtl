import { useState, useRef } from 'react'

function DropZone({ label, accept, file, onFile }) {
  const [dragOver, setDragOver] = useState(false)
  const inputRef = useRef(null)

  function handleDragOver(e) {
    e.preventDefault()
    e.stopPropagation()
    setDragOver(true)
  }

  function handleDragLeave(e) {
    e.preventDefault()
    e.stopPropagation()
    setDragOver(false)
  }

  function handleDrop(e) {
    e.preventDefault()
    e.stopPropagation()
    setDragOver(false)
    const dropped = e.dataTransfer.files[0]
    if (dropped) onFile(dropped)
  }

  function handleChange(e) {
    const selected = e.target.files[0]
    if (selected) onFile(selected)
  }

  function handleClick() {
    inputRef.current.click()
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      inputRef.current.click()
    }
  }

  return (
    <div
      className={`drop-zone${dragOver ? ' drag-over' : ''}${file ? ' has-file' : ''}`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      role="button"
      tabIndex={0}
      aria-label={`${label} — click or drag and drop`}
    >
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        className="file-input-hidden"
        onChange={handleChange}
        tabIndex={-1}
        aria-hidden="true"
      />
      <div className="drop-zone-icon" aria-hidden="true">
        {file ? (
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
            <polyline points="14 2 14 8 20 8" />
            <polyline points="9 15 12 18 15 15" />
            <line x1="12" y1="12" x2="12" y2="18" />
          </svg>
        ) : (
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#64748b" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="17 8 12 3 7 8" />
            <line x1="12" y1="3" x2="12" y2="15" />
          </svg>
        )}
      </div>
      <div className="drop-zone-label">{label}</div>
      {file ? (
        <div className="drop-zone-filename" title={file.name}>
          {file.name}
          <span className="file-size">({(file.size / 1024).toFixed(1)} KB)</span>
        </div>
      ) : (
        <div className="drop-zone-hint">
          Drag &amp; drop or <span className="drop-zone-browse">browse</span>
        </div>
      )}
    </div>
  )
}

export default function FileUpload({ onSubmit }) {
  const [specFile, setSpecFile] = useState(null)
  const [simFile, setSimFile] = useState(null)

  function handleSubmit(e) {
    e.preventDefault()
    if (specFile && simFile) {
      onSubmit(specFile, simFile)
    }
  }

  const canSubmit = specFile !== null && simFile !== null

  return (
    <div className="upload-container">
      <div className="upload-card">
        <div className="upload-card-header">
          <h2 className="upload-card-title">Upload Files for Analysis</h2>
          <p className="upload-card-subtitle">
            Provide your RTL specification and simulation trace to receive AI-powered debugging insights.
          </p>
        </div>

        <form onSubmit={handleSubmit} noValidate>
          <div className="drop-zones-row">
            <DropZone
              label="Specification File (.yml)"
              accept=".yml,.yaml"
              file={specFile}
              onFile={setSpecFile}
            />
            <DropZone
              label="Simulation Trace (.csv)"
              accept=".csv"
              file={simFile}
              onFile={setSimFile}
            />
          </div>

          <div className="upload-actions">
            <button
              type="submit"
              className="btn btn-primary"
              disabled={!canSubmit}
              aria-disabled={!canSubmit}
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <circle cx="11" cy="11" r="8" />
                <line x1="21" y1="21" x2="16.65" y2="16.65" />
              </svg>
              Run Analysis
            </button>
            {!canSubmit && (
              <p className="upload-hint">
                {!specFile && !simFile
                  ? 'Please upload both files to continue.'
                  : !specFile
                  ? 'Please upload a specification file.'
                  : 'Please upload a simulation trace file.'}
              </p>
            )}
          </div>
        </form>
      </div>
    </div>
  )
}
