from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from .parsers.spec_parser import parse_spec
from .parsers.sim_parser import parse_sim
from .engine.rule_engine import run_rule_engine
from .engine.fsm_engine import run_fsm_engine
from .models.analysis_models import AnalysisContext, AnalysisResult
from .ai.claude_analyzer import ClaudeAnalyzer

app = FastAPI(title="RTL Debug Analyzer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.post("/api/analyze", response_model=AnalysisResult)
async def analyze(
    spec_file: UploadFile = File(...),
    sim_file: UploadFile = File(...),
):
    try:
        spec_bytes = await spec_file.read()
        sim_bytes = await sim_file.read()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to read uploaded files: {exc}")

    try:
        spec = parse_spec(spec_bytes)
        signal_db = parse_sim(sim_bytes)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Failed to parse files: {exc}")

    violations = run_rule_engine(spec, signal_db)
    transitions = run_fsm_engine(spec, signal_db)

    context = AnalysisContext(
        spec=spec,
        signal_db=signal_db,
        fsm_transitions=transitions,
        rule_violations=violations,
    )

    try:
        result = ClaudeAnalyzer().analyze(context)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI analysis failed: {exc}")

    return result
