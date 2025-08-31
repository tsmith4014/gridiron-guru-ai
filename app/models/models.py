from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


@dataclass
class Player:
    name: str
    position: str
    team: str
    adp: int
    tier: str
    age: Optional[int] = None
    experience: Optional[int] = None
    strength_of_schedule: Optional[float] = None
    injury_history: Optional[bool] = None


@dataclass
class Recommendation:
    player: Player
    score: float
    reasoning: List[str]
    priority: str
    confidence: float
    risk_factor: float
    upside_potential: float
    ml_score: float
    need_score: float
    risk_score: float
    handcuff_score: float
    round_score: float


@dataclass
class RosterCounts:
    QB: int = 0
    RB: int = 0
    WR: int = 0
    TE: int = 0
    K: int = 0
    DST: int = 0
    FLEX: int = 0  # RB/WR/TE beyond starters
    BENCH: int = 0  # Total bench spots used

    def get_total_players(self) -> int:
        """Get total players on roster"""
        return self.QB + self.RB + self.WR + self.TE + self.K + self.DST

    def get_flex_eligible(self) -> int:
        """Get players eligible for flex position (RB/WR/TE beyond starters)"""
        return max(0, (self.RB - 2) + (self.WR - 2) + (self.TE - 1))

    def get_bench_used(self) -> int:
        """Get how many bench spots are used"""
        starters = 1 + 2 + 2 + 1 + 1 + 1  # QB + 2 RB + 2 WR + TE + K + DST
        flex = self.get_flex_eligible()
        return max(0, self.get_total_players() - starters - flex)

    def is_position_filled(self, position: str) -> bool:
        """Check if a position requirement is filled"""
        if position == "QB":
            return self.QB >= 1
        elif position == "RB":
            return self.RB >= 2
        elif position == "WR":
            return self.WR >= 2
        elif position == "TE":
            return self.TE >= 1
        elif position == "K":
            return self.K >= 1
        elif position == "DST":
            return self.DST >= 1
        elif position == "FLEX":
            return self.get_flex_eligible() >= 1
        return False

    def get_critical_needs(self) -> List[str]:
        """Get list of critical position needs"""
        needs = []
        if self.QB < 1:
            needs.append("QB")
        if self.RB < 2:
            needs.append("RB")
        if self.WR < 2:
            needs.append("WR")
        if self.TE < 1:
            needs.append("TE")
        if self.K < 1:
            needs.append("K")
        if self.DST < 1:
            needs.append("DST")
        return needs

    def get_depth_needs(self) -> List[str]:
        """Get list of depth needs (positions that could use more players)"""
        needs = []
        if self.RB < 4:  # Want at least 4 RBs total
            needs.append("RB")
        if self.WR < 4:  # Want at least 4 WRs total
            needs.append("WR")
        if self.TE < 2:  # Want at least 2 TEs total
            needs.append("TE")
        if self.QB < 2:  # Want at least 2 QBs total
            needs.append("QB")
        return needs

    def can_add_position(self, position: str, current_round: int) -> bool:
        """Check if we can add a player at this position given current roster and round"""
        if position == "QB":
            # Can always add QB if we don't have one, or add backup in later rounds
            return self.QB < 1 or (current_round >= 8 and self.QB < 2)
        elif position == "RB":
            # Need at least 2, can add more for depth
            return self.RB < 2 or (current_round >= 6 and self.RB < 5)
        elif position == "WR":
            # Need at least 2, can add more for depth
            return self.WR < 2 or (current_round >= 6 and self.WR < 5)
        elif position == "TE":
            # Need at least 1, can add backup in later rounds
            return self.TE < 1 or (current_round >= 10 and self.TE < 2)
        elif position == "K":
            # Must have K by round 16 - allow in rounds 14-16
            return (current_round >= 14 and self.K < 1) or (
                current_round >= 16 and self.K < 1
            )
        elif position == "DST":
            # Must have DST by round 16 - allow in rounds 14-16
            return (current_round >= 14 and self.DST < 1) or (
                current_round >= 16 and self.DST < 1
            )
        return False


# Pydantic models for API requests/responses
class DraftRequest(BaseModel):
    available_players: List[Dict[str, Any]]
    current_roster: List[Dict[str, Any]]
    current_round: int
    draft_slot: int
    teams: int
    roster_counts: Optional[Dict[str, int]] = None


class DraftResponse(BaseModel):
    recommendations: List[Dict[str, Any]]
    strategy: str
    insights: List[str]
    next_round_focus: str
    risk_assessment: str
