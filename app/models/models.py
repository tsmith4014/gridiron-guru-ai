from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum

class Position(str, Enum):
    QB = "QB"
    RB = "RB"
    WR = "WR"
    TE = "TE"
    K = "K"
    DST = "DST"

class Tier(str, Enum):
    TIER_1 = "1"
    TIER_2 = "2"
    TIER_3 = "3"
    TIER_4 = "4"
    TIER_5 = "5"
    TIER_6 = "6"

class Player(BaseModel):
    name: str
    position: Position
    team: str
    adp: int = Field(..., ge=1)
    tier: Tier
    drafted: bool = False
    mine: bool = False
    
    # Additional ML features
    age: Optional[int] = None
    experience: Optional[int] = None
    injury_history: Optional[str] = None
    strength_of_schedule: Optional[float] = None
    bye_week: Optional[int] = None
    
    class Config:
        use_enum_values = True

class RosterCounts(BaseModel):
    QB: int = 0
    RB: int = 0
    WR: int = 0
    TE: int = 0
    K: int = 0
    DST: int = 0
    FLEX: int = 0
    BENCH: int = 0

class DraftRequest(BaseModel):
    available_players: List[Player]
    current_roster: List[Player]
    current_round: int = Field(..., ge=1, le=16)
    draft_slot: int = Field(..., ge=1, le=20)
    teams: int = Field(..., ge=2, le=20)
    rounds: int = Field(..., ge=1, le=25)
    roster_counts: RosterCounts

class Recommendation(BaseModel):
    player: Player
    score: float
    priority: str
    reasoning: List[str]
    confidence: float = Field(..., ge=0.0, le=1.0)
    risk_factor: float = Field(..., ge=0.0, le=1.0)
    upside_potential: float = Field(..., ge=0.0, le=1.0)
    
    # Individual score components for debugging
    ml_score: Optional[float] = None
    need_score: Optional[float] = None
    risk_score: Optional[float] = None
    handcuff_score: Optional[float] = None
    round_score: Optional[float] = None

class DraftResponse(BaseModel):
    recommendations: List[Recommendation]
    strategy: str
    insights: List[str]
    next_round_focus: str
    risk_assessment: str

class PlayerAnalysis(BaseModel):
    player: Player
    projected_points: float
    consistency_score: float
    injury_risk: float
    upside_potential: float
    handcuff_value: Optional[float] = None
    bye_week_impact: float
    strength_of_schedule_impact: float
    overall_grade: str
    detailed_analysis: Dict[str, Any]
