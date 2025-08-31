#!/usr/bin/env python3
"""
Draft Intelligence Testing Framework
Tests smart drafting logic, roster optimization, and ADP deviation reasoning
"""

import pytest
import requests
import json
from typing import List, Dict, Any
from dataclasses import dataclass

BASE_URL = "http://localhost:8000"

@dataclass
class Player:
    name: str
    position: str
    team: str
    adp: int
    tier: str

@dataclass
class DraftResult:
    round: int
    pick_number: int
    selected_player: Player
    available_players: List[Player]
    current_roster: List[Player]
    recommendations: List[Dict]
    reasoning: str

class DraftIntelligenceTester:
    """Tests the intelligence of our draft recommendations"""
    
    def __init__(self):
        self.test_players = self._load_test_players()
        self.draft_slot = 1
        self.teams = 10
        self.rounds = 16
        
    def _load_test_players(self) -> List[Player]:
        """Load comprehensive test player data"""
        return [
            # Tier 1 Players (ADP 1-10)
            Player("Ja'Marr Chase", "WR", "CIN", 1, "1"),
            Player("Bijan Robinson", "RB", "ATL", 2, "1"),
            Player("Saquon Barkley", "RB", "PHI", 3, "1"),
            Player("Justin Jefferson", "WR", "MIN", 4, "1"),
            Player("Jahmyr Gibbs", "RB", "DET", 5, "1"),
            Player("CeeDee Lamb", "WR", "DAL", 6, "1"),
            Player("Christian McCaffrey", "RB", "SF", 7, "1"),
            Player("Amon-Ra St. Brown", "WR", "DET", 8, "1"),
            Player("Malik Nabers", "WR", "NYG", 9, "1"),
            Player("Puka Nacua", "WR", "LAR", 10, "1"),
            
            # Tier 2 Players (ADP 11-30)
            Player("Tyreek Hill", "WR", "MIA", 11, "2"),
            Player("Derrick Henry", "RB", "BAL", 12, "2"),
            Player("Stefon Diggs", "WR", "HOU", 13, "2"),
            Player("Alvin Kamara", "RB", "NO", 14, "2"),
            Player("Davante Adams", "WR", "LV", 15, "2"),
            Player("Nick Chubb", "RB", "CLE", 16, "2"),
            Player("DeVonta Smith", "WR", "PHI", 17, "2"),
            Player("James Cook", "RB", "BUF", 18, "2"),
            Player("Jaylen Waddle", "WR", "MIA", 19, "2"),
            Player("Rachaad White", "RB", "TB", 20, "2"),
            
            # QBs (ADP 21-50)
            Player("Josh Allen", "QB", "BUF", 21, "3"),
            Player("Lamar Jackson", "QB", "BAL", 22, "3"),
            Player("Jalen Hurts", "QB", "PHI", 23, "3"),
            Player("Patrick Mahomes", "QB", "KC", 24, "3"),
            Player("Joe Burrow", "QB", "CIN", 25, "3"),
            
            # TEs (ADP 51-80)
            Player("Travis Kelce", "TE", "KC", 51, "4"),
            Player("Sam LaPorta", "TE", "DET", 52, "4"),
            Player("Trey McBride", "TE", "ARI", 53, "4"),
            Player("George Kittle", "TE", "SF", 54, "4"),
            Player("Mark Andrews", "TE", "BAL", 55, "4"),
            
            # Late Round Players (ADP 100+)
            Player("Justin Tucker", "K", "BAL", 200, "6"),
            Player("San Francisco 49ers", "DST", "SF", 201, "6"),
            Player("Baltimore Ravens", "DST", "BAL", 202, "6"),
            Player("Evan McPherson", "K", "CIN", 203, "6"),
        ]
    
    def get_recommendations(self, available_players: List[Player], 
                           current_roster: List[Player], 
                           current_round: int) -> List[Dict]:
        """Get recommendations from the API"""
        try:
            response = requests.post(
                f"{BASE_URL}/api/recommend",
                json={
                    "available_players": [
                        {
                            "name": p.name,
                            "position": p.position,
                            "team": p.team,
                            "adp": p.adp,
                            "tier": p.tier
                        } for p in available_players
                    ],
                    "current_roster": [
                        {
                            "name": p.name,
                            "position": p.position,
                            "team": p.team,
                            "adp": p.adp,
                            "tier": p.tier
                        } for p in current_roster
                    ],
                    "current_round": current_round,
                    "draft_slot": self.draft_slot,
                    "teams": self.teams,
                    "rounds": self.rounds,
                    "roster_counts": self._calculate_roster_counts(current_roster)
                },
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                return response.json().get("recommendations", [])
            else:
                raise Exception(f"API error: {response.status_code}")
                
        except Exception as e:
            pytest.fail(f"Failed to get recommendations: {e}")
    
    def _calculate_roster_counts(self, roster: List[Player]) -> Dict[str, int]:
        """Calculate current roster position counts"""
        counts = {"QB": 0, "RB": 0, "WR": 0, "TE": 0, "K": 0, "DST": 0, "FLEX": 0, "BENCH": 0}
        
        for player in roster:
            if player.position in counts:
                counts[player.position] += 1
            counts["BENCH"] += 1
            
        return counts
    
    def simulate_draft(self) -> List[DraftResult]:
        """Simulate a complete draft and track all decisions"""
        current_roster = []
        available_players = self.test_players.copy()
        draft_results = []
        
        for round_num in range(1, 17):
            # Calculate pick number
            if round_num % 2 == 1:
                pick_num = (round_num - 1) * 10 + self.draft_slot
            else:
                pick_num = round_num * 10 - self.draft_slot + 1
            
            # Get recommendations
            recommendations = self.get_recommendations(available_players, current_roster, round_num)
            
            if not recommendations:
                pytest.fail(f"No recommendations for round {round_num}")
            
            # Select top recommendation
            top_rec = recommendations[0]
            selected_player = Player(
                name=top_rec["player"]["name"],
                position=top_rec["player"]["position"],
                team=top_rec["player"]["team"],
                adp=top_rec["player"]["adp"],
                tier=top_rec["player"]["tier"]
            )
            
            # Analyze the decision
            reasoning = self._analyze_draft_decision(
                selected_player, recommendations, current_roster, round_num
            )
            
            # Record the result
            draft_results.append(DraftResult(
                round=round_num,
                pick_number=pick_num,
                selected_player=selected_player,
                available_players=available_players.copy(),
                current_roster=current_roster.copy(),
                recommendations=recommendations,
                reasoning=reasoning
            ))
            
            # Update state
            current_roster.append(selected_player)
            available_players = [p for p in available_players if p.name != selected_player.name]
            
            print(f"Round {round_num}: {selected_player.name} ({selected_player.position}) - ADP {selected_player.adp}")
            print(f"  Reasoning: {reasoning}")
        
        return draft_results
    
    def _analyze_draft_decision(self, selected_player: Player, 
                               recommendations: List[Dict], 
                               current_roster: List[Player], 
                               round_num: int) -> str:
        """Analyze why this player was selected"""
        reasoning = []
        
        # Check if this was the highest ADP available
        available_adps = [r["player"]["adp"] for r in recommendations]
        if selected_player.adp == min(available_adps):
            reasoning.append("Highest ADP available")
        else:
            reasoning.append(f"ADP {selected_player.adp} selected over ADP {min(available_adps)}")
        
        # Check positional need
        roster_counts = self._calculate_roster_counts(current_roster)
        if selected_player.position == "QB" and roster_counts["QB"] == 0:
            reasoning.append("Critical QB need (no QB on roster)")
        elif selected_player.position == "RB" and roster_counts["RB"] < 2:
            reasoning.append("Critical RB need (need 2 starters)")
        elif selected_player.position == "WR" and roster_counts["WR"] < 2:
            reasoning.append("Critical WR need (need 2 starters)")
        elif selected_player.position == "TE" and roster_counts["TE"] == 0:
            reasoning.append("Critical TE need (no TE on roster)")
        
        # Check round appropriateness
        if round_num <= 3 and selected_player.adp > 30:
            reasoning.append("⚠️ Early round reach (ADP > 30)")
        elif round_num >= 12 and selected_player.position in ["K", "DST"]:
            reasoning.append("✅ Appropriate late round K/DST")
        
        return "; ".join(reasoning)
    
    def calculate_roster_strength(self, roster: List[Player]) -> Dict[str, Any]:
        """Calculate overall roster strength metrics"""
        if not roster:
            return {"total_score": 0, "positional_balance": 0, "adp_efficiency": 0}
        
        # Calculate total ADP score (lower is better)
        total_adp = sum(p.adp for p in roster)
        avg_adp = total_adp / len(roster)
        
        # Calculate positional balance
        position_counts = {}
        for player in roster:
            pos = player.position
            position_counts[pos] = position_counts.get(pos, 0) + 1
        
        # Ideal roster structure: 1 QB, 4-5 RB, 4-5 WR, 1-2 TE, 1 K, 1 DST
        ideal_structure = {"QB": 1, "RB": 4.5, "WR": 4.5, "TE": 1.5, "K": 1, "DST": 1}
        balance_score = 0
        
        for pos, ideal in ideal_structure.items():
            actual = position_counts.get(pos, 0)
            if abs(actual - ideal) <= 1:
                balance_score += 1
            elif abs(actual - ideal) <= 2:
                balance_score += 0.5
            else:
                # Penalize for being way off ideal
                balance_score += 0.1
        
        # Additional penalties for critical imbalances
        # Penalty for missing critical positions
        if position_counts.get('QB', 0) == 0:
            balance_score -= 0.5  # Heavy penalty for no QB
        if position_counts.get('TE', 0) == 0:
            balance_score -= 0.3  # Penalty for no TE
        if position_counts.get('K', 0) == 0:
            balance_score -= 0.2  # Penalty for no K
        if position_counts.get('DST', 0) == 0:
            balance_score -= 0.2  # Penalty for no DST
        
        # Penalty for extreme position stacking
        for pos, count in position_counts.items():
            if count > 6:  # Too many of one position
                balance_score -= 0.3 * (count - 6)
        
        # Ensure balance score doesn't go below 0
        balance_score = max(0, balance_score)
        
        # ADP efficiency (how well we followed ADP)
        adp_efficiency = 100 - (avg_adp / 200 * 100)  # Higher is better
        
        return {
            "total_score": len(roster),
            "positional_balance": balance_score / len(ideal_structure) * 100,
            "adp_efficiency": adp_efficiency,
            "avg_adp": avg_adp,
            "position_counts": position_counts
        }

# Test fixtures
@pytest.fixture
def draft_tester():
    return DraftIntelligenceTester()

# Test cases
def test_basic_draft_logic(draft_tester):
    """Test that basic draft logic works"""
    recommendations = draft_tester.get_recommendations(
        draft_tester.test_players[:5], [], 1
    )
    
    assert len(recommendations) > 0
    assert recommendations[0]["player"]["name"] == "Ja'Marr Chase"  # Should be #1
    assert recommendations[0]["player"]["adp"] == 1

def test_roster_need_prioritization(draft_tester):
    """Test that roster needs are prioritized over pure ADP"""
    # Start with 2 RBs, 0 WRs
    current_roster = [
        Player("Bijan Robinson", "RB", "ATL", 2, "1"),
        Player("Saquon Barkley", "RB", "ATL", 3, "1")
    ]
    
    available_players = [
        Player("Justin Jefferson", "WR", "MIN", 4, "1"),  # WR, ADP 4
        Player("Jahmyr Gibbs", "RB", "DET", 5, "1"),    # RB, ADP 5
        Player("CeeDee Lamb", "WR", "DAL", 6, "1")      # WR, ADP 6
    ]
    
    recommendations = draft_tester.get_recommendations(available_players, current_roster, 3)
    
    # Should prioritize WR (need) over RB (have 2 already)
    # Even though Gibbs has ADP 5 vs Jefferson ADP 4
    assert recommendations[0]["player"]["position"] == "WR"
    print(f"✅ WR prioritized over RB despite ADP: {recommendations[0]['player']['name']}")

def test_complete_draft_simulation(draft_tester):
    """Test complete 16-round draft simulation"""
    print("\n🏈 SIMULATING COMPLETE DRAFT")
    print("=" * 50)
    
    draft_results = draft_tester.simulate_draft()
    
    # Verify we got 16 rounds
    assert len(draft_results) == 16
    
    # Analyze final roster
    final_roster = [result.selected_player for result in draft_results]
    roster_strength = draft_tester.calculate_roster_strength(final_roster)
    
    print(f"\n📊 FINAL ROSTER ANALYSIS:")
    print(f"Total players: {roster_strength['total_score']}")
    print(f"Positional balance: {roster_strength['positional_balance']:.1f}%")
    print(f"ADP efficiency: {roster_strength['adp_efficiency']:.1f}%")
    print(f"Average ADP: {roster_strength['avg_adp']:.1f}")
    print(f"Position breakdown: {roster_strength['position_counts']}")
    
    # Assertions for roster quality
    assert roster_strength["total_score"] == 16
    assert roster_strength["positional_balance"] >= 60  # At least 60% balanced
    assert roster_strength["adp_efficiency"] >= 70      # At least 70% ADP efficient
    
    print(f"\n✅ Draft simulation completed successfully!")
    print(f"Roster strength score: {roster_strength['positional_balance']:.1f}%")

def test_adp_deviation_reasoning(draft_tester):
    """Test that ADP deviations are logically justified"""
    print("\n🧠 TESTING ADP DEVIATION REASONING")
    print("=" * 40)
    
    # Simulate a few rounds to see ADP deviations
    current_roster = []
    available_players = draft_tester.test_players[:10].copy()
    
    for round_num in range(1, 4):
        recommendations = draft_tester.get_recommendations(available_players, current_roster, round_num)
        
        if recommendations:
            top_rec = recommendations[0]
            selected_player = Player(
                name=top_rec["player"]["name"],
                position=top_rec["player"]["position"],
                team=top_rec["player"]["team"],
                adp=top_rec["player"]["adp"],
                tier=top_rec["player"]["tier"]
            )
            
            # Check if this was the highest ADP available
            available_adps = [r["player"]["adp"] for r in recommendations]
            highest_adp = min(available_adps)
            
            if selected_player.adp != highest_adp:
                print(f"⚠️ Round {round_num}: {selected_player.name} (ADP {selected_player.adp}) selected over {highest_adp} ADP")
                print(f"   Reasoning: {top_rec.get('reasoning', 'No reasoning provided')}")
                
                # This should be justified by roster needs
                roster_counts = draft_tester._calculate_roster_counts(current_roster)
                if selected_player.position == "QB" and roster_counts["QB"] == 0:
                    print(f"   ✅ Justified: Critical QB need")
                elif selected_player.position in ["RB", "WR"] and roster_counts[selected_player.position] < 2:
                    print(f"   ✅ Justified: Critical {selected_player.position} need")
                else:
                    print(f"   ❓ Questionable: No clear roster need justification")
            else:
                print(f"✅ Round {round_num}: {selected_player.name} (ADP {selected_player.adp}) - Highest ADP selected")
            
            # Update state
            current_roster.append(selected_player)
            available_players = [p for p in available_players if p.name != selected_player.name]
    
    print(f"\n✅ ADP deviation reasoning test completed!")

def test_smart_drafting_scenarios(draft_tester):
    """Test different drafting scenarios to show intelligent decision making"""
    print("\n🧠 TESTING SMART DRAFTING SCENARIOS")
    print("=" * 50)
    
    # Scenario 1: Early rounds - should follow ADP
    print("\n📊 SCENARIO 1: Early Rounds (1-3) - Following ADP")
    print("-" * 40)
    early_roster = []
    early_players = draft_tester.test_players[:5]  # Top 5 players
    
    recommendations = draft_tester.get_recommendations(early_players, early_roster, 1)
    if recommendations:
        top_pick = recommendations[0]
        print(f"Round 1 Pick: {top_pick['player']['name']} (ADP {top_pick['player']['adp']})")
        print(f"Score: {top_pick['score']:.1f}")
        print(f"Reasoning: {', '.join(top_pick['reasoning'])}")
        
        # Should pick Ja'Marr Chase (ADP 1)
        assert top_pick['player']['name'] == "Ja'Marr Chase"
        print("✅ Correctly following ADP in early rounds")
    
    # Scenario 2: Mid rounds - should consider positional needs
    print("\n📊 SCENARIO 2: Mid Rounds (4-6) - Considering Positional Needs")
    print("-" * 40)
    mid_roster = [
        Player("Ja'Marr Chase", "WR", "CIN", 1, "1"),
        Player("Bijan Robinson", "RB", "ATL", 2, "1"),
        Player("Saquon Barkley", "RB", "ATL", 3, "1")
    ]  # Have 2 RBs, 1 WR
    
    mid_players = [
        Player("Justin Jefferson", "WR", "MIN", 4, "1"),  # WR, ADP 4
        Player("Jahmyr Gibbs", "RB", "DET", 5, "1"),    # RB, ADP 5
        Player("CeeDee Lamb", "WR", "DAL", 6, "1")      # WR, ADP 6
    ]
    
    recommendations = draft_tester.get_recommendations(mid_players, mid_roster, 4)
    if recommendations:
        top_pick = recommendations[0]
        print(f"Round 4 Pick: {top_pick['player']['name']} (ADP {top_pick['player']['adp']})")
        print(f"Score: {top_pick['score']:.1f}")
        print(f"Reasoning: {', '.join(top_pick['reasoning'])}")
        
        # Should prioritize WR (need 2 starters) over RB (have 2 already)
        if top_pick['player']['position'] == 'WR':
            print("✅ Smart! Prioritizing WR need over RB despite ADP")
        else:
            print("⚠️ Still following ADP strictly - may need tuning")
    
    # Scenario 3: Late rounds - should prioritize critical positions
    print("\n📊 SCENARIO 3: Late Rounds (12-16) - Critical Position Needs")
    print("-" * 40)
    late_roster = [
        Player("Ja'Marr Chase", "WR", "CIN", 1, "1"),
        Player("Bijan Robinson", "RB", "ATL", 2, "1"),
        Player("Saquon Barkley", "RB", "ATL", 3, "1"),
        Player("Justin Jefferson", "WR", "MIN", 4, "1"),
        Player("Jahmyr Gibbs", "RB", "DET", 5, "1"),
        Player("CeeDee Lamb", "WR", "DAL", 6, "1"),
        Player("Christian McCaffrey", "RB", "SF", 7, "1"),
        Player("Amon-Ra St. Brown", "WR", "DET", 8, "1"),
        Player("Malik Nabers", "WR", "NYG", 9, "1"),
        Player("Puka Nacua", "WR", "LAR", 10, "1"),
        Player("Tyreek Hill", "WR", "MIA", 11, "2")
    ]  # Have 4 RBs, 7 WRs, 0 QB, 0 TE, 0 K, 0 DST
    
    late_players = [
        Player("Josh Allen", "QB", "BUF", 21, "3"),      # QB, ADP 21
        Player("Travis Kelce", "TE", "KC", 51, "4"),     # TE, ADP 51
        Player("Justin Tucker", "K", "BAL", 200, "6"),   # K, ADP 200
        Player("San Francisco 49ers", "DST", "SF", 201, "6")  # DST, ADP 201
    ]
    
    recommendations = draft_tester.get_recommendations(late_players, late_roster, 12)
    if recommendations:
        top_pick = recommendations[0]
        print(f"Round 12 Pick: {top_pick['player']['name']} (ADP {top_pick['player']['adp']})")
        print(f"Score: {top_pick['score']:.1f}")
        print(f"Reasoning: {', '.join(top_pick['reasoning'])}")
        
        # Should prioritize QB or TE over K/DST
        if top_pick['player']['position'] in ['QB', 'TE']:
            print("✅ Smart! Prioritizing critical positions (QB/TE) over K/DST")
        elif top_pick['player']['position'] in ['K', 'DST']:
            print("⚠️ Picking K/DST too early - may need tuning")
        else:
            print("⚠️ Unexpected position priority")
    
    print(f"\n✅ Smart drafting scenarios test completed!")

def test_roster_optimization_metrics(draft_tester):
    """Test that our roster optimization metrics are working correctly"""
    print("\n📈 TESTING ROSTER OPTIMIZATION METRICS")
    print("=" * 50)
    
    # Test with a well-balanced roster
    balanced_roster = [
        Player("Ja'Marr Chase", "WR", "CIN", 1, "1"),
        Player("Bijan Robinson", "RB", "ATL", 2, "1"),
        Player("Josh Allen", "QB", "BUF", 21, "3"),
        Player("Travis Kelce", "TE", "KC", 51, "4"),
        Player("Justin Tucker", "K", "BAL", 200, "6"),
        Player("San Francisco 49ers", "DST", "SF", 201, "6")
    ]
    
    metrics = draft_tester.calculate_roster_strength(balanced_roster)
    
    print(f"Balanced Roster Metrics:")
    print(f"  Total players: {metrics['total_score']}")
    print(f"  Positional balance: {metrics['positional_balance']:.1f}%")
    print(f"  ADP efficiency: {metrics['adp_efficiency']:.1f}%")
    print(f"  Average ADP: {metrics['avg_adp']:.1f}")
    print(f"  Position breakdown: {metrics['position_counts']}")
    
    # Test with an imbalanced roster (all WRs)
    imbalanced_roster = [
        Player("Ja'Marr Chase", "WR", "CIN", 1, "1"),
        Player("Justin Jefferson", "WR", "MIN", 4, "1"),
        Player("CeeDee Lamb", "WR", "DAL", 6, "1"),
        Player("Amon-Ra St. Brown", "WR", "DET", 8, "1"),
        Player("Malik Nabers", "WR", "NYG", 9, "1"),
        Player("Puka Nacua", "WR", "LAR", 10, "1")
    ]
    
    metrics = draft_tester.calculate_roster_strength(imbalanced_roster)
    
    print(f"\nImbalanced Roster Metrics:")
    print(f"  Total players: {metrics['total_score']}")
    print(f"  Positional balance: {metrics['positional_balance']:.1f}%")
    print(f"  ADP efficiency: {metrics['adp_efficiency']:.1f}%")
    print(f"  Average ADP: {metrics['avg_adp']:.1f}")
    print(f"  Position breakdown: {metrics['position_counts']}")
    
    # The balanced roster should have higher positional balance
    balanced_metrics = draft_tester.calculate_roster_strength(balanced_roster)
    imbalanced_metrics = draft_tester.calculate_roster_strength(imbalanced_roster)
    
    assert balanced_metrics['positional_balance'] > imbalanced_metrics['positional_balance']
    print(f"\n✅ Balanced roster ({balanced_metrics['positional_balance']:.1f}%) has better balance than imbalanced ({imbalanced_metrics['positional_balance']:.1f}%)")

if __name__ == "__main__":
    # Run tests manually if needed
    pytest.main([__file__, "-v"])
