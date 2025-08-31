from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.models.models import DraftRequest, DraftResponse
from app.ml.ml_logic import DraftMLModel

app = FastAPI(title="Gridiron Guru AI - Fantasy Football Draft Assistant", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files (for serving the HTML frontend)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Initialize ML model
ml_model = DraftMLModel()

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main HTML file"""
    with open("app/frontend/enhanced_draft_assistant.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.get("/draft", response_class=HTMLResponse)
async def draft_page():
    """Serve the draft assistant page"""
    with open("app/frontend/enhanced_draft_assistant.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.get("/legacy", response_class=HTMLResponse)
async def legacy_page():
    """Serve the legacy draft assistant page"""
    with open("app/frontend/fixed_draft_assistant_prepopulated.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.post("/api/recommend", response_model=DraftResponse)
async def get_recommendations(
    request: DraftRequest,
    db: Session = Depends(get_db)
):
    """
    Get ML-enhanced draft recommendations based on current roster and draft state
    """
    try:
        # Use ML model to get enhanced recommendations
        recommendations = ml_model.get_recommendations(
            available_players=request.available_players,
            current_roster=request.current_roster,
            current_round=request.current_round,
            draft_slot=request.draft_slot,
            teams=request.teams
        )
        
        # Use ML recommendations directly
        final_recommendations = recommendations
        
        return DraftResponse(
            recommendations=final_recommendations,
            strategy=ml_model.get_strategy_insights(request.current_round, request.roster_counts),
            insights=ml_model.get_draft_insights(request.available_players, request.roster_counts),
            next_round_focus=ml_model.get_next_round_focus(request.current_round, request.roster_counts),
            risk_assessment=ml_model.get_risk_assessment(request.available_players, request.roster_counts)
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating recommendations: {str(e)}")

@app.post("/api/analyze-player")
async def analyze_player(
    player: dict,
    db: Session = Depends(get_db)
):
    """
    Analyze a specific player using ML models
    """
    try:
        analysis = ml_model.analyze_player(player)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing player: {str(e)}")

@app.get("/api/players")
async def get_players(db: Session = Depends(get_db)):
    """
    Get all available players
    """
    try:
        # This would typically come from database
        # For now, return sample data
        return {"players": ml_model.get_sample_players()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching players: {str(e)}")

@app.post("/api/update-model")
async def update_model(db: Session = Depends(get_db)):
    """
    Retrain the ML model with new data
    """
    try:
        ml_model.retrain_model()
        return {"message": "Model updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating model: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
