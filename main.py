from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List, Optional
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import joblib
import os

from models import DraftRequest, DraftResponse, Player, RosterCounts
from database import get_db, engine
from ml_logic import DraftMLModel
from draft_logic import DraftLogic

# Create database tables
from database import Base
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Enhanced Fantasy Draft Assistant API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files (for serving the HTML frontend)
app.mount("/static", StaticFiles(directory="."), name="static")

# Initialize ML model
ml_model = DraftMLModel()

@app.get("/")
async def root():
    """Serve the main HTML file"""
    with open("enhanced_draft_assistant.html", "r") as f:
        return {"html": f.read()}

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
        
        # Apply draft logic rules
        draft_logic = DraftLogic()
        final_recommendations = draft_logic.apply_draft_strategy(
            recommendations=recommendations,
            current_round=request.current_round,
            roster_counts=request.roster_counts
        )
        
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
    player: Player,
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
    uvicorn.run(app, host="0.0.0.0", port=8000)
