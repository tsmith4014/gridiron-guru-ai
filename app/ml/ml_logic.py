import os
from typing import Any, Dict, List

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder, StandardScaler

from app.models.models import Player, Recommendation, RosterCounts


class DraftMLModel:
    def __init__(self):
        self.scaler = StandardScaler()
        self.position_encoder = LabelEncoder()
        self.team_encoder = LabelEncoder()
        self.tier_encoder = LabelEncoder()

        # Initialize models for different positions
        self.models = {
            "RB": RandomForestRegressor(n_estimators=100, random_state=42),
            "WR": RandomForestRegressor(n_estimators=100, random_state=42),
            "TE": RandomForestRegressor(n_estimators=100, random_state=42),
            "QB": RandomForestRegressor(n_estimators=100, random_state=42),
            "K": RandomForestRegressor(n_estimators=50, random_state=42),
            "DST": RandomForestRegressor(n_estimators=50, random_state=42),
        }

        self.is_trained = False
        self.load_or_train_models()

    def load_or_train_models(self):
        """Load pre-trained models or train new ones"""
        model_path = "models/draft_models.pkl"

        if os.path.exists(model_path):
            try:
                self.models = joblib.load(model_path)
                self.is_trained = True
                print("Loaded pre-trained models")
            except:
                print("Failed to load models, training new ones")
                self.train_models()
        else:
            self.train_models()

    def train_models(self):
        """Train ML models using historical fantasy data"""
        print("Training ML models...")

        # Generate synthetic training data (in production, use real historical data)
        training_data = self.generate_training_data()

        for position in self.models.keys():
            pos_data = training_data[training_data["position"] == position]
            if len(pos_data) > 0:
                X = pos_data[
                    ["adp", "tier_encoded", "age", "experience", "strength_of_schedule"]
                ].fillna(0)
                y = pos_data["fantasy_points"]

                if len(X) > 10:  # Need minimum data to train
                    self.models[position].fit(X, y)

        self.is_trained = True

        # Save models
        os.makedirs("models", exist_ok=True)
        model_path = "models/draft_models.joblib"
        joblib.dump(self.models, model_path)
        print("Models trained and saved")

    def generate_training_data(self) -> pd.DataFrame:
        """Generate synthetic training data (replace with real data in production)"""
        np.random.seed(42)

        data = []
        positions = ["RB", "WR", "TE", "QB", "K", "DST"]

        for pos in positions:
            n_samples = 200 if pos in ["RB", "WR"] else 100

            for i in range(n_samples):
                adp = np.random.randint(1, 200)
                tier = np.random.randint(1, 7)
                age = (
                    np.random.randint(21, 35)
                    if pos != "DST"
                    else np.random.randint(1, 10)
                )
                experience = (
                    np.random.randint(0, 15)
                    if pos != "DST"
                    else np.random.randint(1, 10)
                )
                strength_of_schedule = np.random.uniform(0.5, 1.5)

                # Generate fantasy points based on position and features
                base_points = {
                    "RB": 180,
                    "WR": 160,
                    "TE": 120,
                    "QB": 300,
                    "K": 140,
                    "DST": 100,
                }

                # Improved ADP impact - much steeper penalty for high ADP
                adp_penalty = (adp / 200) ** 3  # Cubic penalty for even steeper drop

                # Tier impact - lower tier = higher points
                tier_bonus = (6 - tier) * 0.15

                # Position-specific adjustments
                position_multiplier = {
                    "QB": 0.9,  # QBs get slight penalty
                    "RB": 1.0,  # RBs are baseline
                    "WR": 1.0,  # WRs are baseline
                    "TE": 0.95,  # TEs get slight penalty
                    "K": 0.7,  # Kickers get penalty
                    "DST": 0.7,  # DSTs get penalty
                }

                fantasy_points = (
                    base_points[pos]
                    * (1.0 - adp_penalty)  # Steeper ADP penalty
                    * (1.0 + tier_bonus)  # Tier bonus
                    * position_multiplier[pos]  # Position adjustment
                    * (1.0 + np.random.normal(0, 0.15))  # Reduced random variation
                )

                data.append(
                    {
                        "position": pos,
                        "adp": adp,
                        "tier": tier,
                        "tier_encoded": tier,
                        "age": age,
                        "experience": experience,
                        "strength_of_schedule": strength_of_schedule,
                        "fantasy_points": max(0, fantasy_points),
                    }
                )

        return pd.DataFrame(data)

    def get_recommendations(
        self,
        available_players: List[Player],
        current_roster: List[Player],
        current_round: int,
        draft_slot: int,
        teams: int,
        roster_counts: RosterCounts = None,
    ) -> List[Recommendation]:
        """Get ML-enhanced draft recommendations with proper roster constraints"""

        if not self.is_trained:
            self.train_models()

        print(
            f"🔍 DEBUG: Getting recommendations for Round {current_round}, Pick {draft_slot}"
        )
        print(f"🔍 DEBUG: Available players: {len(available_players)}")
        print(f"🔍 DEBUG: Current roster: {len(current_roster)} players")

        # Ensure we have roster counts
        if roster_counts is None:
            roster_counts = self.count_positions(current_roster)

        # Get critical needs and depth needs
        critical_needs = roster_counts.get_critical_needs()
        depth_needs = roster_counts.get_depth_needs()

        print(f"🔍 DEBUG: Critical needs: {critical_needs}")
        print(f"🔍 DEBUG: Depth needs: {depth_needs}")

        recommendations = []

        for player in available_players:
            try:
                # Check if we can add this position
                if not roster_counts.can_add_position(player.position, current_round):
                    print(
                        f"🔍 DEBUG: {player.name} - Position {player.position} cannot be added at round {current_round}"
                    )
                    continue

                # Calculate base score using ML model
                ml_score = self.predict_player_value(player)
                print(f"🔍 DEBUG: {player.name} - ML Score: {ml_score:.2f}")

                # Calculate positional need score (MUCH higher weight now)
                need_score = self.calculate_positional_need(
                    player, current_roster, current_round, roster_counts
                )
                print(f"🔍 DEBUG: {player.name} - Need Score: {need_score:.2f}")

                # Calculate risk-adjusted score
                risk_score = self.calculate_risk_adjusted_score(player, current_round)
                print(f"🔍 DEBUG: {player.name} - Risk Score: {risk_score:.2f}")

                # Calculate handcuff value
                handcuff_score = self.calculate_handcuff_value(player, current_roster)
                print(f"🔍 DEBUG: {player.name} - Handcuff Score: {handcuff_score:.2f}")

                # Calculate round-specific adjustments
                round_score = self.calculate_round_adjustments(
                    player, current_round, draft_slot, teams
                )
                print(f"🔍 DEBUG: {player.name} - Round Score: {round_score:.2f}")

                # Combine all scores with MUCH higher need weight
                total_score = (
                    ml_score * 0.4  # ML score (40% - reduced from 80%)
                    + need_score * 0.4  # Positional need (40% - increased from 10%)
                    + risk_score * 0.1  # Risk assessment (10% - increased from 5%)
                    + handcuff_score * 0.05  # Handcuff value (5% - increased from 3%)
                    + round_score * 0.05  # Round adjustments (5% - increased from 2%)
                )

                # Apply roster constraint bonuses
                if player.position in critical_needs:
                    total_score *= 2.0  # Double score for critical needs
                    print(f"🔍 DEBUG: {player.name} - Critical need bonus applied")

                # Final ADP validation - smarter round-based penalties
                if current_round <= 3:
                    if player.adp > 50:
                        total_score *= (
                            0.6  # Heavy penalty for ADP > 50 in first 3 rounds
                        )
                    elif player.adp > 30:
                        total_score *= (
                            0.8  # Moderate penalty for ADP > 30 in first 3 rounds
                        )
                elif current_round <= 5:
                    if player.adp > 80:
                        total_score *= 0.7  # Penalty for ADP > 80 in rounds 4-5
                elif current_round <= 8:
                    if player.adp > 120:
                        total_score *= 0.8  # Light penalty for ADP > 120 in rounds 6-8

                print(f"🔍 DEBUG: {player.name} - Total Score: {total_score:.2f}")

                # Generate reasoning
                reasoning = self.generate_reasoning(
                    player,
                    ml_score,
                    need_score,
                    risk_score,
                    handcuff_score,
                    round_score,
                    critical_needs,
                    depth_needs,
                )

                # Calculate confidence and risk factors
                confidence = self.calculate_confidence(player, current_round)
                risk_factor = self.calculate_risk_factor(player)
                upside_potential = self.calculate_upside_potential(player)

                # Determine priority
                priority = self.determine_priority(total_score, confidence, risk_factor)

                recommendations.append(
                    Recommendation(
                        player=player,
                        score=total_score,
                        priority=priority,
                        reasoning=reasoning,
                        confidence=confidence,
                        risk_factor=risk_factor,
                        upside_potential=upside_potential,
                        ml_score=ml_score,
                        need_score=need_score,
                        risk_score=risk_score,
                        handcuff_score=handcuff_score,
                        round_score=round_score,
                    )
                )

            except Exception as e:
                print(f"🔍 DEBUG: Error processing {player.name}: {str(e)}")
                continue

        # Sort by total score
        recommendations.sort(key=lambda x: x.score, reverse=True)

        print(f"🔍 DEBUG: Top 5 recommendations:")
        for i, rec in enumerate(recommendations[:5]):
            print(
                f"   {i+1}. {rec.player.name} ({rec.player.position}, ADP {rec.player.adp}): {rec.score:.2f}"
            )

        return recommendations[:10]  # Return top 10

    def predict_player_value(self, player: Player) -> float:
        """Predict player value using ML model"""
        try:
            # Use fallback scoring - ML models are disabled for now
            if False and player.position in self.models and self.is_trained:
                # Prepare features
                features = np.array(
                    [
                        [
                            player.adp,
                            int(player.tier),
                            player.age or 25,
                            player.experience or 3,
                            player.strength_of_schedule or 1.0,
                        ]
                    ]
                )

                # Scale features
                features_scaled = self.scaler.fit_transform(features)

                # Predict
                prediction = self.models[player.position].predict(features_scaled)[0]
                return max(0, prediction)
            else:
                # Improved fallback scoring that properly considers ADP vs tier
                base_score = 200

                # ADP penalty (higher ADP = lower score)
                adp_penalty = player.adp * 0.8

                # Tier bonus (lower tier number = higher score)
                tier_bonus = (6 - int(player.tier)) * 15

                # Position-specific adjustments
                position_multiplier = {
                    "QB": 0.9,  # QBs get slight penalty in early rounds
                    "RB": 1.0,  # RBs are baseline
                    "WR": 1.0,  # WRs are baseline
                    "TE": 0.95,  # TEs get slight penalty
                    "K": 0.3,  # Kickers heavily penalized early
                    "DST": 0.3,  # DSTs heavily penalized early
                }

                # Calculate final score
                final_score = (
                    base_score - adp_penalty + tier_bonus
                ) * position_multiplier.get(player.position, 1.0)

                # Ensure reasonable bounds
                return max(0, min(300, final_score))
        except:
            # Emergency fallback - simple ADP-based scoring
            return max(0, 200 - player.adp)

    def calculate_positional_need(
        self,
        player: Player,
        current_roster: List[Player],
        current_round: int,
        roster_counts: RosterCounts = None,
    ) -> float:
        """Calculate how much we need this position with proper roster constraints"""
        # Use the roster_counts passed from the API instead of recalculating
        if roster_counts is None:
            roster_counts = self.count_positions(current_roster)
        position = player.position

        # Get critical and depth needs
        critical_needs = roster_counts.get_critical_needs()
        depth_needs = roster_counts.get_depth_needs()

        # Base need scores - MUCH more aggressive for critical needs
        if position in critical_needs:
            # Critical need - extremely high score to force drafting
            if position == "QB":
                return 500.0  # Must have QB - extremely high priority
            elif position == "RB":
                return 400.0  # Must have 2 RBs
            elif position == "WR":
                return 400.0  # Must have 2 WRs
            elif position == "TE":
                return 350.0  # Must have TE
            elif position == "K":
                return 300.0  # Must have K in late rounds
            elif position == "DST":
                return 300.0  # Must have DST in late rounds

        elif position in depth_needs:
            # Depth need - moderate score
            if position == "RB":
                if roster_counts.RB < 3:
                    return 120.0  # Want 3rd RB
                elif roster_counts.RB < 4:
                    return 80.0  # Want 4th RB
                else:
                    return 20.0  # Additional RB depth (reduced)
            elif position == "WR":
                if roster_counts.WR < 3:
                    return 120.0  # Want 3rd WR
                elif roster_counts.WR < 4:
                    return 80.0  # Want 4th WR
                else:
                    return 20.0  # Additional WR depth (reduced)
            elif position == "TE":
                if roster_counts.TE < 2:
                    return 100.0  # Want backup TE
                else:
                    return 15.0  # Additional TE depth (reduced)
            elif position == "QB":
                if roster_counts.QB < 2:
                    return 80.0  # Want backup QB
                else:
                    return 10.0  # Additional QB depth (reduced)

        # Position not needed - very low score
        if position == "K" and current_round < 14:
            return 0.0  # Don't need K early
        elif position == "DST" and current_round < 14:
            return 0.0  # Don't need DST early
        else:
            return 5.0  # Minimal score for non-needed positions (reduced)

    def calculate_risk_adjusted_score(
        self, player: Player, current_round: int
    ) -> float:
        """Calculate risk-adjusted score based on round and player characteristics"""
        base_score = 50

        # Round-based risk adjustment
        if current_round <= 3:
            # Early rounds: lower risk tolerance - heavily penalize high ADP players
            if player.adp > 50:
                base_score -= 40  # Increased penalty
            if player.adp > 100:
                base_score -= 60  # Even bigger penalty for very high ADP
        elif current_round <= 7:
            # Mid rounds: moderate risk tolerance
            if player.adp > 100:
                base_score -= 30
        elif current_round >= 12:
            # Late rounds: higher risk tolerance
            if player.adp <= 100:
                base_score += 20

        # Position-based risk adjustment
        if player.position in ["K", "DST"] and current_round < 12:
            base_score -= 50  # Increased penalty for K/DST too early

        # Tier-based risk adjustment
        tier_risk = (6 - int(player.tier)) * 8  # Increased tier importance
        base_score += tier_risk

        # ADP vs Round validation
        expected_pick = current_round * 10  # Rough estimate
        if player.adp > expected_pick + 30:
            base_score -= 25  # Penalty for drafting too early

        return max(0, base_score)

    def calculate_handcuff_value(
        self, player: Player, current_roster: List[Player]
    ) -> float:
        """Calculate handcuff value for RBs"""
        if player.position != "RB":
            return 0

        # Check if this player is a backup to someone on our roster
        for roster_player in current_roster:
            if roster_player.position == "RB" and roster_player.team == player.team:
                # Higher bonus for handcuffs to your top RBs
                if roster_player.adp <= 20:  # Elite RB handcuff
                    return 40
                elif roster_player.adp <= 50:  # Good RB handcuff
                    return 30
                else:  # Depth RB handcuff
                    return 20

        return 0

    def calculate_round_adjustments(
        self, player: Player, current_round: int, draft_slot: int, teams: int
    ) -> float:
        """Calculate round-specific adjustments"""
        score = 0

        # Calculate expected pick number
        expected_pick = self.calculate_expected_pick(current_round, draft_slot, teams)

        # Value vs. need balance
        if player.adp < expected_pick - 20:
            score += 25  # Player fell significantly
        elif player.adp > expected_pick + 20:
            score -= 15  # Player is a reach

        # Position scarcity in later rounds
        if current_round >= 8:
            if player.position in ["K", "DST"]:
                score += 20

        return score

    def calculate_expected_pick(self, round_num: int, slot: int, teams: int) -> int:
        """Calculate expected pick number for a given round"""
        if round_num % 2 == 1:
            return (round_num - 1) * teams + slot
        else:
            return round_num * teams - slot + 1

    def count_positions(self, roster: List[Player]) -> Dict[str, int]:
        """Count players by position in roster"""
        counts = {"QB": 0, "RB": 0, "WR": 0, "TE": 0, "K": 0, "DST": 0}
        for player in roster:
            counts[player.position] += 1
        return counts

    def generate_reasoning(
        self,
        player: Player,
        ml_score: float,
        need_score: float,
        risk_score: float,
        handcuff_score: float,
        round_score: float,
        critical_needs: List[str] = None,
        depth_needs: List[str] = None,
    ) -> List[str]:
        """Generate reasoning for recommendation with roster context"""
        reasons = []

        # ML Score reasoning
        if ml_score > 180:
            reasons.append("🔥 Elite value")
        elif ml_score > 150:
            reasons.append("High ML-predicted value")
        elif ml_score > 100:
            reasons.append("Good ML-predicted value")

        # Need-based reasoning with roster context
        if critical_needs and player.position in critical_needs:
            reasons.append("🚨 CRITICAL NEED - Must fill this position!")
        elif depth_needs and player.position in depth_needs:
            reasons.append("📈 Depth need - Builds roster strength")
        elif need_score > 80:
            reasons.append("🚨 Critical need")
        elif need_score > 50:
            reasons.append("Fills positional need")

        # Risk assessment
        if risk_score > 70:
            reasons.append("✅ Low risk option")
        elif risk_score < 30:
            reasons.append("⚠️ Higher risk")

        # Handcuff value
        if handcuff_score > 30:
            reasons.append("🔒 Premium handcuff")
        elif handcuff_score > 0:
            reasons.append("Handcuff value")

        # Round value
        if round_score > 25:
            reasons.append("💎 Great value for round")
        elif round_score > 15:
            reasons.append("Good value for round")

        # ADP-based reasoning
        if player.adp <= 10:
            reasons.append("👑 Elite ADP")
        elif player.adp <= 20:
            reasons.append("Elite ADP")
        elif player.adp <= 50:
            reasons.append("Strong ADP")

        # Tier reasoning
        if player.tier == "1":
            reasons.append("⭐ Tier 1 talent")
        elif player.tier == "2":
            reasons.append("Tier 2 talent")

        # Roster constraint reasoning
        if critical_needs and player.position in critical_needs:
            if player.position == "QB":
                reasons.append("🎯 No QB on roster - MUST DRAFT")
            elif player.position == "RB":
                reasons.append("🎯 Need 2 RB starters - MUST DRAFT")
            elif player.position == "WR":
                reasons.append("🎯 Need 2 WR starters - MUST DRAFT")
            elif player.position == "TE":
                reasons.append("🎯 No TE on roster - MUST DRAFT")
            elif player.position == "K":
                reasons.append("🎯 No K on roster - MUST DRAFT")
            elif player.position == "DST":
                reasons.append("🎯 No DST on roster - MUST DRAFT")

        return reasons

    def determine_priority(
        self, total_score: float, confidence: float, risk_factor: float
    ) -> str:
        """Determine priority level based on scores"""
        if total_score > 180 and confidence > 0.8 and risk_factor < 0.3:
            return "🔥 TOP PICK"
        elif total_score > 150 and confidence > 0.7 and risk_factor < 0.4:
            return "⭐ HIGH PRIORITY"
        elif total_score > 120 and confidence > 0.6:
            return "✅ GOOD VALUE"
        elif total_score > 90:
            return "📋 CONSIDER"
        else:
            return "⚠️ LOW PRIORITY"

    def calculate_confidence(self, player: Player, current_round: int) -> float:
        """Calculate confidence in recommendation"""
        base_confidence = 0.7

        # Higher confidence for early round players
        if current_round <= 3 and player.adp <= 30:
            base_confidence += 0.2

        # Higher confidence for tier 1 players
        if player.tier == "1":
            base_confidence += 0.1

        # Lower confidence for K/DST in early rounds
        if player.position in ["K", "DST"] and current_round < 10:
            base_confidence -= 0.3

        return min(1.0, max(0.0, base_confidence))

    def calculate_risk_factor(self, player: Player) -> float:
        """Calculate risk factor for player"""
        base_risk = 0.5

        # Higher risk for players with injury history
        if player.injury_history:
            base_risk += 0.2

        # Lower risk for established players
        if player.experience and player.experience > 3:
            base_risk -= 0.1

        # Higher risk for very young players
        if player.age and player.age < 23:
            base_risk += 0.1

        return min(1.0, max(0.0, base_risk))

    def calculate_upside_potential(self, player: Player) -> float:
        """Calculate upside potential for player"""
        base_upside = 0.6

        # Higher upside for young players
        if player.age and player.age < 25:
            base_upside += 0.2

        # Higher upside for high ADP players
        if player.adp <= 20:
            base_upside += 0.1

        # Higher upside for tier 1 players
        if player.tier == "1":
            base_upside += 0.1

        return min(1.0, max(0.0, base_upside))

    def get_strategy_insights(
        self, current_round: int, roster_counts: RosterCounts
    ) -> str:
        """Get strategic insights for current round with roster constraints"""
        # Get current needs
        critical_needs = roster_counts.get_critical_needs()
        depth_needs = roster_counts.get_depth_needs()

        if current_round <= 3:
            if critical_needs:
                return f"🎯 EARLY ROUNDS: CRITICAL NEEDS - Must draft: {', '.join(critical_needs)}"
            else:
                return "🎯 EARLY ROUNDS: Focus on best available player"
        elif current_round <= 7:
            if critical_needs:
                return f"🏗️ MID ROUNDS: CRITICAL NEEDS - Must draft: {', '.join(critical_needs)}"
            elif depth_needs:
                return f"🏗️ MID ROUNDS: Build depth at: {', '.join(depth_needs)}"
            else:
                return "🏗️ MID ROUNDS: Build roster depth and value"
        elif current_round <= 11:
            if critical_needs:
                return f"📈 LATE MID: CRITICAL NEEDS remaining: {', '.join(critical_needs)}"
            else:
                return "📈 LATE MID: Focus on depth, value picks, and handcuffs"
        else:
            if critical_needs:
                return f"⏰ LATE ROUNDS: MUST FILL: {', '.join(critical_needs)}"
            else:
                return "⏰ LATE ROUNDS: Fill remaining needs and optimize bench"

    def get_draft_insights(
        self, available_players: List[Player], roster_counts: RosterCounts
    ) -> List[str]:
        """Get insights about the current draft state"""
        insights = []

        # Count available players by position
        position_counts = {}
        for player in available_players:
            pos = player.position
            position_counts[pos] = position_counts.get(pos, 0) + 1

        # Generate insights
        for pos, count in position_counts.items():
            if count < 5:
                insights.append(f"⚠️ Only {count} {pos}s remaining")
            elif count < 10:
                insights.append(f"💡 {pos} depth is thinning")
            elif count > 30:
                insights.append(f"✅ Strong {pos} depth available")

        return insights

    def get_next_round_focus(
        self, current_round: int, roster_counts: RosterCounts
    ) -> str:
        """Get focus for the next round"""
        if current_round <= 3:
            return "Best available player regardless of position"
        elif current_round <= 7:
            return "Balance positional needs with value"
        elif current_round <= 11:
            return "Build roster depth and consider handcuffs"
        else:
            return "Fill remaining needs and target K/DST"

    def get_risk_assessment(
        self, available_players: List[Player], roster_counts: RosterCounts
    ) -> str:
        """Get overall risk assessment"""
        high_risk_count = sum(1 for p in available_players if p.adp > 100)
        total_players = len(available_players)
        risk_percentage = (high_risk_count / total_players) * 100

        if risk_percentage > 70:
            return "High risk - many late-round players available"
        elif risk_percentage > 40:
            return "Moderate risk - mixed player quality"
        else:
            return "Low risk - many quality players available"

    def get_sample_players(self) -> List[Dict]:
        """Get sample player data - full 160 players from CSV"""
        return [
            {
                "name": "Ja'Marr Chase",
                "position": "WR",
                "team": "CIN",
                "adp": 1,
                "tier": "1",
            },
            {
                "name": "Bijan Robinson",
                "position": "RB",
                "team": "ATL",
                "adp": 2,
                "tier": "1",
            },
            {
                "name": "Saquon Barkley",
                "position": "RB",
                "team": "PHI",
                "adp": 3,
                "tier": "1",
            },
            {
                "name": "Justin Jefferson",
                "position": "WR",
                "team": "MIN",
                "adp": 4,
                "tier": "1",
            },
            {
                "name": "Jahmyr Gibbs",
                "position": "RB",
                "team": "DET",
                "adp": 5,
                "tier": "1",
            },
            {
                "name": "CeeDee Lamb",
                "position": "WR",
                "team": "DAL",
                "adp": 6,
                "tier": "1",
            },
            {
                "name": "Christian McCaffrey",
                "position": "RB",
                "team": "SF",
                "adp": 7,
                "tier": "1",
            },
            {
                "name": "Amon-Ra St. Brown",
                "position": "WR",
                "team": "DET",
                "adp": 8,
                "tier": "1",
            },
            {
                "name": "Malik Nabers",
                "position": "WR",
                "team": "NYG",
                "adp": 9,
                "tier": "1",
            },
            {
                "name": "Puka Nacua",
                "position": "WR",
                "team": "LAR",
                "adp": 10,
                "tier": "1",
            },
            {
                "name": "Nico Collins",
                "position": "WR",
                "team": "HOU",
                "adp": 11,
                "tier": "2",
            },
            {
                "name": "Tyreek Hill",
                "position": "WR",
                "team": "MIA",
                "adp": 12,
                "tier": "2",
            },
            {
                "name": "A.J. Brown",
                "position": "WR",
                "team": "PHI",
                "adp": 13,
                "tier": "2",
            },
            {
                "name": "Drake London",
                "position": "WR",
                "team": "ATL",
                "adp": 14,
                "tier": "2",
            },
            {
                "name": "Ashton Jeanty",
                "position": "RB",
                "team": "LV",
                "adp": 15,
                "tier": "2",
            },
            {
                "name": "Derrick Henry",
                "position": "RB",
                "team": "BAL",
                "adp": 16,
                "tier": "2",
            },
            {
                "name": "De'Von Achane",
                "position": "RB",
                "team": "MIA",
                "adp": 17,
                "tier": "2",
            },
            {
                "name": "Brian Thomas Jr.",
                "position": "WR",
                "team": "JAX",
                "adp": 18,
                "tier": "2",
            },
            {
                "name": "Jonathan Taylor",
                "position": "RB",
                "team": "IND",
                "adp": 19,
                "tier": "2",
            },
            {
                "name": "Josh Jacobs",
                "position": "RB",
                "team": "GB",
                "adp": 20,
                "tier": "2",
            },
            {
                "name": "Brock Bowers",
                "position": "TE",
                "team": "LV",
                "adp": 21,
                "tier": "2",
            },
            {
                "name": "Trey McBride",
                "position": "TE",
                "team": "ARI",
                "adp": 22,
                "tier": "2",
            },
            {
                "name": "Kyren Williams",
                "position": "RB",
                "team": "LAR",
                "adp": 23,
                "tier": "3",
            },
            {
                "name": "James Cook",
                "position": "RB",
                "team": "BUF",
                "adp": 24,
                "tier": "3",
            },
            {
                "name": "Tee Higgins",
                "position": "WR",
                "team": "CIN",
                "adp": 25,
                "tier": "3",
            },
            {
                "name": "Jaxon Smith-Njigba",
                "position": "WR",
                "team": "SEA",
                "adp": 26,
                "tier": "3",
            },
            {
                "name": "Mike Evans",
                "position": "WR",
                "team": "TB",
                "adp": 27,
                "tier": "3",
            },
            {
                "name": "Terry McLaurin",
                "position": "WR",
                "team": "WSH",
                "adp": 28,
                "tier": "3",
            },
            {
                "name": "Davante Adams",
                "position": "WR",
                "team": "LAR",
                "adp": 29,
                "tier": "3",
            },
            {
                "name": "DK Metcalf",
                "position": "WR",
                "team": "PIT",
                "adp": 30,
                "tier": "3",
            },
            {
                "name": "Garrett Wilson",
                "position": "WR",
                "team": "NYJ",
                "adp": 31,
                "tier": "3",
            },
            {
                "name": "DJ Moore",
                "position": "WR",
                "team": "CHI",
                "adp": 32,
                "tier": "3",
            },
            {
                "name": "DeVonta Smith",
                "position": "WR",
                "team": "PHI",
                "adp": 33,
                "tier": "3",
            },
            {
                "name": "Jaylen Waddle",
                "position": "WR",
                "team": "MIA",
                "adp": 34,
                "tier": "3",
            },
            {
                "name": "Chris Olave",
                "position": "WR",
                "team": "NO",
                "adp": 35,
                "tier": "3",
            },
            {
                "name": "Stefon Diggs",
                "position": "WR",
                "team": "NE",
                "adp": 36,
                "tier": "3",
            },
            {
                "name": "Cooper Kupp",
                "position": "WR",
                "team": "SEA",
                "adp": 37,
                "tier": "3",
            },
            {
                "name": "Zay Flowers",
                "position": "WR",
                "team": "BAL",
                "adp": 38,
                "tier": "3",
            },
            {
                "name": "Xavier Worthy",
                "position": "WR",
                "team": "KC",
                "adp": 39,
                "tier": "3",
            },
            {
                "name": "Jameson Williams",
                "position": "WR",
                "team": "DET",
                "adp": 40,
                "tier": "3",
            },
            {
                "name": "Isiah Pacheco",
                "position": "RB",
                "team": "KC",
                "adp": 41,
                "tier": "3",
            },
            {
                "name": "Kenneth Walker III",
                "position": "RB",
                "team": "SEA",
                "adp": 42,
                "tier": "3",
            },
            {
                "name": "David Montgomery",
                "position": "RB",
                "team": "DET",
                "adp": 43,
                "tier": "3",
            },
            {
                "name": "Alvin Kamara",
                "position": "RB",
                "team": "NO",
                "adp": 44,
                "tier": "3",
            },
            {
                "name": "Breece Hall",
                "position": "RB",
                "team": "NYJ",
                "adp": 45,
                "tier": "3",
            },
            {
                "name": "Chase Brown",
                "position": "RB",
                "team": "CIN",
                "adp": 46,
                "tier": "3",
            },
            {
                "name": "Bucky Irving",
                "position": "RB",
                "team": "TB",
                "adp": 47,
                "tier": "3",
            },
            {
                "name": "Omarion Hampton",
                "position": "RB",
                "team": "CAR",
                "adp": 48,
                "tier": "3",
            },
            {
                "name": "TreVeyon Henderson",
                "position": "RB",
                "team": "NE",
                "adp": 49,
                "tier": "3",
            },
            {
                "name": "Chuba Hubbard",
                "position": "RB",
                "team": "CAR",
                "adp": 50,
                "tier": "3",
            },
            {
                "name": "James Conner",
                "position": "RB",
                "team": "ARI",
                "adp": 51,
                "tier": "4",
            },
            {
                "name": "Aaron Jones",
                "position": "RB",
                "team": "MIN",
                "adp": 52,
                "tier": "4",
            },
            {
                "name": "Tony Pollard",
                "position": "RB",
                "team": "TEN",
                "adp": 53,
                "tier": "4",
            },
            {
                "name": "Rhamondre Stevenson",
                "position": "RB",
                "team": "NE",
                "adp": 54,
                "tier": "4",
            },
            {
                "name": "Travis Etienne",
                "position": "RB",
                "team": "JAX",
                "adp": 55,
                "tier": "4",
            },
            {
                "name": "Joe Mixon",
                "position": "RB",
                "team": "HOU",
                "adp": 56,
                "tier": "4",
            },
            {
                "name": "Khalil Shakir",
                "position": "WR",
                "team": "BUF",
                "adp": 57,
                "tier": "4",
            },
            {
                "name": "Emeka Egbuka",
                "position": "WR",
                "team": "TB",
                "adp": 58,
                "tier": "4",
            },
            {
                "name": "Ricky Pearsall",
                "position": "WR",
                "team": "SF",
                "adp": 59,
                "tier": "4",
            },
            {
                "name": "Jordan Addison",
                "position": "WR",
                "team": "MIN",
                "adp": 60,
                "tier": "4",
            },
            {
                "name": "Keon Coleman",
                "position": "WR",
                "team": "BUF",
                "adp": 61,
                "tier": "4",
            },
            {
                "name": "Rome Odunze",
                "position": "WR",
                "team": "CHI",
                "adp": 62,
                "tier": "4",
            },
            {
                "name": "Christian Kirk",
                "position": "WR",
                "team": "JAX",
                "adp": 63,
                "tier": "4",
            },
            {
                "name": "Brandin Cooks",
                "position": "WR",
                "team": "DAL",
                "adp": 64,
                "tier": "4",
            },
            {
                "name": "Josh Downs",
                "position": "WR",
                "team": "IND",
                "adp": 65,
                "tier": "4",
            },
            {
                "name": "Tyler Lockett",
                "position": "WR",
                "team": "SEA",
                "adp": 66,
                "tier": "4",
            },
            {
                "name": "Amari Cooper",
                "position": "WR",
                "team": "CLE",
                "adp": 67,
                "tier": "4",
            },
            {
                "name": "Deebo Samuel Sr.",
                "position": "WR",
                "team": "SF",
                "adp": 68,
                "tier": "4",
            },
            {
                "name": "Marquise Brown",
                "position": "WR",
                "team": "KC",
                "adp": 69,
                "tier": "4",
            },
            {
                "name": "Michael Pittman Jr.",
                "position": "WR",
                "team": "IND",
                "adp": 70,
                "tier": "4",
            },
            {
                "name": "George Pickens",
                "position": "WR",
                "team": "PIT",
                "adp": 71,
                "tier": "4",
            },
            {
                "name": "Courtland Sutton",
                "position": "WR",
                "team": "DEN",
                "adp": 72,
                "tier": "4",
            },
            {
                "name": "Jerry Jeudy",
                "position": "WR",
                "team": "CLE",
                "adp": 73,
                "tier": "4",
            },
            {
                "name": "Jakobi Meyers",
                "position": "WR",
                "team": "LV",
                "adp": 74,
                "tier": "4",
            },
            {
                "name": "Rashod Bateman",
                "position": "WR",
                "team": "BAL",
                "adp": 75,
                "tier": "4",
            },
            {
                "name": "Romeo Doubs",
                "position": "WR",
                "team": "GB",
                "adp": 76,
                "tier": "4",
            },
            {
                "name": "Jahan Dotson",
                "position": "WR",
                "team": "WSH",
                "adp": 77,
                "tier": "4",
            },
            {
                "name": "Elijah Moore",
                "position": "WR",
                "team": "CLE",
                "adp": 78,
                "tier": "4",
            },
            {
                "name": "Gabe Davis",
                "position": "WR",
                "team": "JAX",
                "adp": 79,
                "tier": "4",
            },
            {
                "name": "Curtis Samuel",
                "position": "WR",
                "team": "BUF",
                "adp": 80,
                "tier": "4",
            },
            {
                "name": "Tank Dell",
                "position": "WR",
                "team": "HOU",
                "adp": 81,
                "tier": "5",
            },
            {
                "name": "Quentin Johnston",
                "position": "WR",
                "team": "LAC",
                "adp": 82,
                "tier": "5",
            },
            {
                "name": "Wan'Dale Robinson",
                "position": "WR",
                "team": "NYG",
                "adp": 83,
                "tier": "5",
            },
            {
                "name": "Demario Douglas",
                "position": "WR",
                "team": "NE",
                "adp": 84,
                "tier": "5",
            },
            {
                "name": "Jalen Nailor",
                "position": "WR",
                "team": "MIN",
                "adp": 85,
                "tier": "5",
            },
            {
                "name": "Matthew Golden",
                "position": "WR",
                "team": "GB",
                "adp": 86,
                "tier": "5",
            },
            {
                "name": "Tyler Boyd",
                "position": "WR",
                "team": "TEN",
                "adp": 87,
                "tier": "5",
            },
            {
                "name": "Mecole Hardman",
                "position": "WR",
                "team": "KC",
                "adp": 88,
                "tier": "5",
            },
            {
                "name": "Darnell Mooney",
                "position": "WR",
                "team": "ATL",
                "adp": 89,
                "tier": "5",
            },
            {
                "name": "Adam Thielen",
                "position": "WR",
                "team": "CAR",
                "adp": 90,
                "tier": "5",
            },
            {
                "name": "Jayden Reed",
                "position": "WR",
                "team": "GB",
                "adp": 91,
                "tier": "5",
            },
            {
                "name": "Tutu Atwell",
                "position": "WR",
                "team": "LAR",
                "adp": 92,
                "tier": "5",
            },
            {
                "name": "Jonathan Mingo",
                "position": "WR",
                "team": "CAR",
                "adp": 93,
                "tier": "5",
            },
            {
                "name": "Kendrick Bourne",
                "position": "WR",
                "team": "NE",
                "adp": 94,
                "tier": "5",
            },
            {
                "name": "Michael Wilson",
                "position": "WR",
                "team": "ARI",
                "adp": 95,
                "tier": "5",
            },
            {
                "name": "Noah Brown",
                "position": "WR",
                "team": "HOU",
                "adp": 96,
                "tier": "5",
            },
            {
                "name": "Robert Woods",
                "position": "WR",
                "team": "HOU",
                "adp": 97,
                "tier": "5",
            },
            {
                "name": "Josh Palmer",
                "position": "WR",
                "team": "LAC",
                "adp": 98,
                "tier": "5",
            },
            {
                "name": "Marvin Mims Jr.",
                "position": "WR",
                "team": "DEN",
                "adp": 99,
                "tier": "5",
            },
            {
                "name": "Khalil Herbert",
                "position": "RB",
                "team": "CHI",
                "adp": 100,
                "tier": "5",
            },
            {
                "name": "Jaylen Warren",
                "position": "RB",
                "team": "PIT",
                "adp": 101,
                "tier": "5",
            },
            {
                "name": "Zack Moss",
                "position": "RB",
                "team": "CIN",
                "adp": 102,
                "tier": "5",
            },
            {
                "name": "Roschon Johnson",
                "position": "RB",
                "team": "CHI",
                "adp": 103,
                "tier": "5",
            },
            {
                "name": "Kendre Miller",
                "position": "RB",
                "team": "NO",
                "adp": 104,
                "tier": "5",
            },
            {
                "name": "Tyjae Spears",
                "position": "RB",
                "team": "TEN",
                "adp": 105,
                "tier": "5",
            },
            {
                "name": "Ezekiel Elliott",
                "position": "RB",
                "team": "DAL",
                "adp": 106,
                "tier": "5",
            },
            {
                "name": "Gus Edwards",
                "position": "RB",
                "team": "LAC",
                "adp": 107,
                "tier": "5",
            },
            {
                "name": "Raheem Mostert",
                "position": "RB",
                "team": "MIA",
                "adp": 108,
                "tier": "5",
            },
            {
                "name": "Jerome Ford",
                "position": "RB",
                "team": "CLE",
                "adp": 109,
                "tier": "5",
            },
            {
                "name": "Brian Robinson Jr.",
                "position": "RB",
                "team": "WSH",
                "adp": 110,
                "tier": "5",
            },
            {
                "name": "Antonio Gibson",
                "position": "RB",
                "team": "NE",
                "adp": 111,
                "tier": "5",
            },
            {
                "name": "Najee Harris",
                "position": "RB",
                "team": "LAC",
                "adp": 112,
                "tier": "5",
            },
            {
                "name": "Dameon Pierce",
                "position": "RB",
                "team": "HOU",
                "adp": 113,
                "tier": "5",
            },
            {
                "name": "Devin Singletary",
                "position": "RB",
                "team": "NYG",
                "adp": 114,
                "tier": "5",
            },
            {
                "name": "Cam Akers",
                "position": "RB",
                "team": "MIN",
                "adp": 115,
                "tier": "5",
            },
            {
                "name": "Cam Skattebo",
                "position": "RB",
                "team": "NYG",
                "adp": 116,
                "tier": "5",
            },
            {
                "name": "Jordan Mason",
                "position": "RB",
                "team": "MIN",
                "adp": 117,
                "tier": "5",
            },
            {
                "name": "Josh Allen",
                "position": "QB",
                "team": "BUF",
                "adp": 118,
                "tier": "5",
            },
            {
                "name": "Lamar Jackson",
                "position": "QB",
                "team": "BAL",
                "adp": 119,
                "tier": "5",
            },
            {
                "name": "Jalen Hurts",
                "position": "QB",
                "team": "PHI",
                "adp": 120,
                "tier": "5",
            },
            {
                "name": "Patrick Mahomes",
                "position": "QB",
                "team": "KC",
                "adp": 121,
                "tier": "6",
            },
            {
                "name": "Joe Burrow",
                "position": "QB",
                "team": "KC",
                "adp": 122,
                "tier": "6",
            },
            {
                "name": "C.J. Stroud",
                "position": "QB",
                "team": "HOU",
                "adp": 123,
                "tier": "6",
            },
            {
                "name": "Justin Herbert",
                "position": "QB",
                "team": "LAC",
                "adp": 124,
                "tier": "6",
            },
            {
                "name": "Tua Tagovailoa",
                "position": "QB",
                "team": "MIA",
                "adp": 125,
                "tier": "6",
            },
            {
                "name": "Brock Purdy",
                "position": "QB",
                "team": "SF",
                "adp": 126,
                "tier": "6",
            },
            {
                "name": "Dak Prescott",
                "position": "QB",
                "team": "DAL",
                "adp": 127,
                "tier": "6",
            },
            {
                "name": "Kyler Murray",
                "position": "QB",
                "team": "ARI",
                "adp": 128,
                "tier": "6",
            },
            {
                "name": "Trevor Lawrence",
                "position": "QB",
                "team": "JAX",
                "adp": 129,
                "tier": "6",
            },
            {
                "name": "Jared Goff",
                "position": "QB",
                "team": "DET",
                "adp": 130,
                "tier": "6",
            },
            {
                "name": "Kirk Cousins",
                "position": "QB",
                "team": "ATL",
                "adp": 131,
                "tier": "6",
            },
            {
                "name": "Jordan Love",
                "position": "QB",
                "team": "GB",
                "adp": 132,
                "tier": "6",
            },
            {
                "name": "Bo Nix",
                "position": "QB",
                "team": "DEN",
                "adp": 133,
                "tier": "6",
            },
            {
                "name": "Jayden Daniels",
                "position": "QB",
                "team": "WSH",
                "adp": 134,
                "tier": "6",
            },
            {
                "name": "Deshaun Watson",
                "position": "QB",
                "team": "CLE",
                "adp": 135,
                "tier": "6",
            },
            {
                "name": "Matthew Stafford",
                "position": "QB",
                "team": "LAR",
                "adp": 136,
                "tier": "6",
            },
            {
                "name": "Anthony Richardson",
                "position": "QB",
                "team": "IND",
                "adp": 137,
                "tier": "6",
            },
            {
                "name": "Brock Bowers",
                "position": "TE",
                "team": "LV",
                "adp": 138,
                "tier": "6",
            },
            {
                "name": "Trey McBride",
                "position": "TE",
                "team": "ARI",
                "adp": 139,
                "tier": "6",
            },
            {
                "name": "George Kittle",
                "position": "TE",
                "team": "SF",
                "adp": 140,
                "tier": "6",
            },
            {
                "name": "Sam LaPorta",
                "position": "TE",
                "team": "DET",
                "adp": 141,
                "tier": "6",
            },
            {
                "name": "Travis Kelce",
                "position": "TE",
                "team": "KC",
                "adp": 142,
                "tier": "6",
            },
            {
                "name": "T.J. Hockenson",
                "position": "TE",
                "team": "MIN",
                "adp": 143,
                "tier": "6",
            },
            {
                "name": "Mark Andrews",
                "position": "TE",
                "team": "BAL",
                "adp": 144,
                "tier": "6",
            },
            {
                "name": "David Njoku",
                "position": "TE",
                "team": "CLE",
                "adp": 145,
                "tier": "6",
            },
            {
                "name": "Evan Engram",
                "position": "TE",
                "team": "JAX",
                "adp": 146,
                "tier": "6",
            },
            {
                "name": "Dalton Kincaid",
                "position": "QB",
                "team": "BUF",
                "adp": 147,
                "tier": "6",
            },
            {
                "name": "Dallas Goedert",
                "position": "TE",
                "team": "PHI",
                "adp": 148,
                "tier": "6",
            },
            {
                "name": "Pat Freiermuth",
                "position": "TE",
                "team": "PIT",
                "adp": 149,
                "tier": "6",
            },
            {
                "name": "Kyle Pitts",
                "position": "TE",
                "team": "ATL",
                "adp": 150,
                "tier": "6",
            },
            {
                "name": "Cole Kmet",
                "position": "TE",
                "team": "CHI",
                "adp": 151,
                "tier": "6",
            },
            {
                "name": "Tyler Warren",
                "position": "TE",
                "team": "IND",
                "adp": 152,
                "tier": "6",
            },
            {
                "name": "Cade Otton",
                "position": "TE",
                "team": "TB",
                "adp": 153,
                "tier": "6",
            },
            {
                "name": "Brenton Strange",
                "position": "TE",
                "team": "JAX",
                "adp": 154,
                "tier": "6",
            },
            {
                "name": "Jake Ferguson",
                "position": "TE",
                "team": "DAL",
                "adp": 155,
                "tier": "6",
            },
            {
                "name": "Luke Musgrave",
                "position": "TE",
                "team": "GB",
                "adp": 156,
                "tier": "6",
            },
            {
                "name": "Hunter Henry",
                "position": "TE",
                "team": "NE",
                "adp": 157,
                "tier": "6",
            },
            {
                "name": "Zamir White",
                "position": "RB",
                "team": "LV",
                "adp": 158,
                "tier": "6",
            },
            {
                "name": "Ty Chandler",
                "position": "RB",
                "team": "MIN",
                "adp": 159,
                "tier": "6",
            },
            {
                "name": "Chase Edmonds",
                "position": "RB",
                "team": "TB",
                "adp": 160,
                "tier": "6",
            },
        ]

    def retrain_model(self):
        """Retrain the ML model with new data"""
        print("Retraining ML models...")
        self.train_models()
        return {"message": "Models retrained successfully"}
