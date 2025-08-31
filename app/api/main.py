from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app.ml.ml_logic import DraftMLModel
from app.models.database import get_db
from app.models.models import DraftRequest, DraftResponse

app = FastAPI(
    title="Gridiron Guru AI - Fantasy Football Draft Assistant", version="1.0.0"
)

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
async def get_recommendations(request: DraftRequest, db: Session = Depends(get_db)):
    """
    Get ML-enhanced draft recommendations based on current roster and draft state
    """
    try:
        # Debug logging
        print(
            f"🔍 DEBUG: Received request - Round {request.current_round}, Draft Slot {request.draft_slot}"
        )
        print(f"🔍 DEBUG: Available players count: {len(request.available_players)}")
        print(f"🔍 DEBUG: Current roster count: {len(request.current_roster)}")
        print(
            f"🔍 DEBUG: First few available players: {[p['name'] for p in request.available_players[:5]]}"
        )
        print(
            f"🔍 DEBUG: First few roster players: {[p['name'] for p in request.current_roster[:5]]}"
        )

        # Convert dictionaries to Player objects
        from app.models.models import Player, RosterCounts

        available_players = [
            Player(
                name=p["name"],
                position=p["position"],
                team=p["team"],
                adp=p["adp"],
                tier=p["tier"],
            )
            for p in request.available_players
        ]

        current_roster = [
            Player(
                name=p["name"],
                position=p["position"],
                team=p["team"],
                adp=p["adp"],
                tier=p["tier"],
            )
            for p in request.current_roster
        ]

        print(f"🔍 DEBUG: Converted available players count: {len(available_players)}")
        print(f"🔍 DEBUG: Converted roster players count: {len(current_roster)}")
        print(
            f"🔍 DEBUG: Available player names: {[p.name for p in available_players[:5]]}"
        )
        print(f"🔍 DEBUG: Roster player names: {[p.name for p in current_roster[:5]]}")

        # Create roster counts if not provided
        if request.roster_counts is None:
            roster_counts = RosterCounts()
            for player in current_roster:
                if player.position == "QB":
                    roster_counts.QB += 1
                elif player.position == "RB":
                    roster_counts.RB += 1
                elif player.position == "WR":
                    roster_counts.WR += 1
                elif player.position == "TE":
                    roster_counts.TE += 1
                elif player.position == "K":
                    roster_counts.K += 1
                elif player.position == "DST":
                    roster_counts.DST += 1

            # Calculate flex and bench counts
            roster_counts.FLEX = roster_counts.get_flex_eligible()
            roster_counts.BENCH = roster_counts.get_bench_used()
        else:
            # Convert dict to RosterCounts object
            roster_counts = RosterCounts(
                QB=request.roster_counts.get("QB", 0),
                RB=request.roster_counts.get("RB", 0),
                WR=request.roster_counts.get("WR", 0),
                TE=request.roster_counts.get("TE", 0),
                K=request.roster_counts.get("K", 0),
                DST=request.roster_counts.get("DST", 0),
            )
            # Calculate flex and bench counts
            roster_counts.FLEX = roster_counts.get_flex_eligible()
            roster_counts.BENCH = roster_counts.get_bench_used()

        print(
            f"🔍 DEBUG: Roster counts - QB: {roster_counts.QB}, RB: {roster_counts.RB}, WR: {roster_counts.WR}, TE: {roster_counts.TE}, K: {roster_counts.K}, DST: {roster_counts.DST}"
        )

        # Use ML model to get enhanced recommendations
        recommendations = ml_model.get_recommendations(
            available_players=available_players,
            current_roster=current_roster,
            current_round=request.current_round,
            draft_slot=request.draft_slot,
            teams=request.teams,
            roster_counts=roster_counts,  # Pass roster counts to ML model
        )

        print(f"🔍 DEBUG: ML model returned {len(recommendations)} recommendations")

        # Convert recommendations to dictionaries for JSON response
        final_recommendations = []
        for rec in recommendations:
            final_recommendations.append(
                {
                    "player": {
                        "name": rec.player.name,
                        "position": rec.player.position,
                        "team": rec.player.team,
                        "adp": rec.player.adp,
                        "tier": rec.player.tier,
                    },
                    "score": rec.score,
                    "reasoning": rec.reasoning,
                    "priority": rec.priority,
                    "confidence": rec.confidence,
                    "risk_factor": rec.risk_factor,
                    "upside_potential": rec.upside_potential,
                    "ml_score": rec.ml_score,
                    "need_score": rec.need_score,
                    "risk_score": rec.risk_score,
                    "handcuff_score": rec.handcuff_score,
                    "round_score": rec.round_score,
                }
            )

        return DraftResponse(
            recommendations=final_recommendations,
            strategy=ml_model.get_strategy_insights(
                request.current_round, roster_counts
            ),
            insights=ml_model.get_draft_insights(available_players, roster_counts),
            next_round_focus=ml_model.get_next_round_focus(
                request.current_round, roster_counts
            ),
            risk_assessment=ml_model.get_risk_assessment(
                available_players, roster_counts
            ),
        )

    except Exception as e:
        print(f"🔍 DEBUG: Error in get_recommendations: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error generating recommendations: {str(e)}"
        )


@app.post("/api/analyze-player")
async def analyze_player(player: dict, db: Session = Depends(get_db)):
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
