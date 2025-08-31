from typing import List, Dict, Any
from app.models.models import Recommendation, Player, RosterCounts
import logging

class DraftLogic:
    """Applies strategic draft rules and constraints to ML recommendations"""
    
    def __init__(self):
        # Strategic rules and weights
        self.position_weights = {
            'RB': 1.0,
            'WR': 1.0,
            'TE': 0.8,
            'QB': 0.7,
            'K': 0.3,
            'DST': 0.3
        }
        
        # Round-specific strategies
        self.round_strategies = {
            'early': {'rounds': [1, 2, 3], 'focus': 'best_available'},
            'mid': {'rounds': [4, 5, 6, 7], 'focus': 'balanced'},
            'late_mid': {'rounds': [8, 9, 10, 11], 'focus': 'depth'},
            'late': {'rounds': [12, 13, 14, 15, 16], 'focus': 'needs'}
        }
    
    def apply_draft_strategy(
        self,
        recommendations: List[Recommendation],
        current_round: int,
        roster_counts: RosterCounts
    ) -> List[Recommendation]:
        """Apply strategic rules to ML recommendations"""
        
        # Get current round strategy
        strategy = self.get_round_strategy(current_round)
        
        # Apply position scarcity adjustments
        adjusted_recommendations = self.apply_position_scarcity(recommendations)
        
        # Apply roster balance rules
        adjusted_recommendations = self.apply_roster_balance(
            adjusted_recommendations, roster_counts, current_round
        )
        
        # Apply round-specific constraints
        adjusted_recommendations = self.apply_round_constraints(
            adjusted_recommendations, current_round, strategy
        )
        
        # Apply value vs. need balance
        adjusted_recommendations = self.apply_value_need_balance(
            adjusted_recommendations, current_round, roster_counts
        )
        
        # Re-sort by final adjusted scores
        adjusted_recommendations.sort(key=lambda x: x.score, reverse=True)
        
        return adjusted_recommendations
    
    def get_round_strategy(self, current_round: int) -> str:
        """Determine strategy for current round"""
        for strategy_name, strategy_info in self.round_strategies.items():
            if current_round in strategy_info['rounds']:
                return strategy_info['focus']
        return 'balanced'
    
    def apply_position_scarcity(self, recommendations: List[Recommendation]) -> List[Recommendation]:
        """Adjust scores based on position scarcity"""
        # Count available players by position
        position_counts = {}
        for rec in recommendations:
            pos = rec.player.position
            position_counts[pos] = position_counts.get(pos, 0) + 1
        
        # Apply scarcity bonuses
        for rec in recommendations:
            pos = rec.player.position
            count = position_counts.get(pos, 0)
            
            if count < 5:  # Very scarce
                rec.score += 30
            elif count < 10:  # Scarce
                rec.score += 20
            elif count < 15:  # Moderately scarce
                rec.score += 10
        
        return recommendations
    
    def apply_roster_balance(
        self,
        recommendations: List[Recommendation],
        roster_counts: RosterCounts,
        current_round: int
    ) -> List[Recommendation]:
        """Apply roster balance rules"""
        
        for rec in recommendations:
            pos = rec.player.position
            
            # Critical needs (must have starters)
            if pos == 'RB' and roster_counts.RB < 2:
                rec.score += 40
            elif pos == 'WR' and roster_counts.WR < 2:
                rec.score += 40
            elif pos == 'TE' and roster_counts.TE < 1:
                rec.score += 35
            elif pos == 'QB' and roster_counts.QB < 1:
                rec.score += 30
            
            # Depth needs
            elif pos == 'RB' and roster_counts.RB < 4:
                rec.score += 20
            elif pos == 'WR' and roster_counts.WR < 4:
                rec.score += 20
            elif pos == 'TE' and roster_counts.TE < 2:
                rec.score += 15
            
            # Late round K/DST priority
            elif current_round >= 12:
                if pos == 'K' and roster_counts.K < 1:
                    rec.score += 50
                elif pos == 'DST' and roster_counts.DST < 1:
                    rec.score += 50
        
        return recommendations
    
    def apply_round_constraints(
        self,
        recommendations: List[Recommendation],
        current_round: int,
        strategy: str
    ) -> List[Recommendation]:
        """Apply round-specific constraints"""
        
        for rec in recommendations:
            pos = rec.player.position
            
            # Early rounds: avoid K/DST
            if current_round <= 5 and pos in ['K', 'DST']:
                rec.score -= 100
            
            # Mid rounds: balance value and need
            elif 6 <= current_round <= 10:
                if pos in ['K', 'DST']:
                    rec.score -= 50
                elif rec.player.adp > 100:  # Avoid reaches
                    rec.score -= 20
            
            # Late rounds: prioritize needs
            elif current_round >= 11:
                if pos in ['K', 'DST'] and rec.score > 0:
                    rec.score += 30  # Boost K/DST in late rounds
            
            # Strategy-specific adjustments
            if strategy == 'best_available':
                # Boost high-ADP players in early rounds
                if current_round <= 3 and rec.player.adp <= 30:
                    rec.score += 25
            elif strategy == 'needs':
                # Boost players that fill critical needs
                if rec.score > 100:  # Already a good recommendation
                    rec.score += 15
        
        return recommendations
    
    def apply_value_need_balance(
        self,
        recommendations: List[Recommendation],
        current_round: int,
        roster_counts: RosterCounts
    ) -> List[Recommendation]:
        """Balance value vs. need based on draft stage"""
        
        for rec in recommendations:
            # Calculate value vs. need balance
            value_score = 200 - rec.player.adp  # Higher ADP = lower value
            need_score = self.calculate_need_score(rec.player.position, roster_counts, current_round)
            
            # Adjust based on round
            if current_round <= 3:
                # Early rounds: favor value over need
                rec.score = rec.score * 0.7 + value_score * 0.3
            elif current_round <= 7:
                # Mid rounds: balance value and need
                rec.score = rec.score * 0.8 + need_score * 0.2
            else:
                # Late rounds: favor need over value
                rec.score = rec.score * 0.6 + need_score * 0.4
        
        return recommendations
    
    def calculate_need_score(self, position: str, roster_counts: RosterCounts, current_round: int) -> float:
        """Calculate how much we need a specific position"""
        base_scores = {
            'QB': 100 if roster_counts.QB < 1 else 30,
            'RB': 100 if roster_counts.RB < 2 else 60 if roster_counts.RB < 4 else 20,
            'WR': 100 if roster_counts.WR < 2 else 60 if roster_counts.WR < 4 else 20,
            'TE': 100 if roster_counts.TE < 1 else 50 if roster_counts.TE < 2 else 15,
            'K': 100 if roster_counts.K < 1 and current_round >= 12 else 0,
            'DST': 100 if roster_counts.DST < 1 and current_round >= 12 else 0
        }
        
        return base_scores.get(position, 0)
    
    def validate_recommendation(self, rec: Recommendation, current_round: int) -> bool:
        """Validate if a recommendation makes sense for the current round"""
        
        # Early rounds: no K/DST
        if current_round <= 5 and rec.player.position in ['K', 'DST']:
            return False
        
        # Check for obvious reaches
        if rec.player.adp > 150 and current_round <= 8:
            return False
        
        # Check for obvious steals
        if rec.player.adp <= 20 and current_round >= 10:
            return False
        
        return True
    
    def get_strategy_insights(self, current_round: int, roster_counts: RosterCounts) -> Dict[str, Any]:
        """Get strategic insights for the current round"""
        
        strategy = self.get_round_strategy(current_round)
        
        insights = {
            'round_strategy': strategy,
            'critical_needs': [],
            'depth_needs': [],
            'late_round_focus': []
        }
        
        # Identify critical needs
        if roster_counts.RB < 2:
            insights['critical_needs'].append('RB')
        if roster_counts.WR < 2:
            insights['critical_needs'].append('WR')
        if roster_counts.TE < 1:
            insights['critical_needs'].append('TE')
        if roster_counts.QB < 1:
            insights['critical_needs'].append('QB')
        
        # Identify depth needs
        if roster_counts.RB < 4:
            insights['depth_needs'].append('RB')
        if roster_counts.WR < 4:
            insights['depth_needs'].append('WR')
        if roster_counts.TE < 2:
            insights['depth_needs'].append('TE')
        
        # Late round focus
        if current_round >= 12:
            if roster_counts.K < 1:
                insights['late_round_focus'].append('K')
            if roster_counts.DST < 1:
                insights['late_round_focus'].append('DST')
        
        return insights
    
    def apply_handcuff_logic(self, recommendations: List[Recommendation], current_roster: List[Player]) -> List[Recommendation]:
        """Apply handcuff logic for RBs"""
        
        # Get RBs on current roster
        my_rbs = [p for p in current_roster if p.position == 'RB']
        
        for rec in recommendations:
            if rec.player.position == 'RB':
                # Check if this is a handcuff
                for my_rb in my_rbs:
                    if my_rb.team == rec.player.team:
                        rec.score += 25  # Handcuff bonus
                        rec.reasoning.append("Handcuff")
                        break
        
        return recommendations
    
    def apply_bye_week_logic(self, recommendations: List[Recommendation], current_roster: List[Player]) -> List[Recommendation]:
        """Apply bye week logic to avoid conflicts"""
        
        # Get bye weeks of current roster
        bye_weeks = [p.bye_week for p in current_roster if p.bye_week]
        
        for rec in recommendations:
            if rec.player.bye_week and rec.player.bye_week in bye_weeks:
                # Penalize players with same bye week as multiple starters
                bye_count = bye_weeks.count(rec.player.bye_week)
                if bye_count >= 2:
                    rec.score -= 15
                    rec.reasoning.append("Bye week conflict")
        
        return recommendations
