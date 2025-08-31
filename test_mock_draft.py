#!/usr/bin/env python3
"""
Mock Draft Test Script for Gridiron Guru AI
Tests the ML logic across multiple rounds to ensure proper player ranking
"""

import requests
import json
from typing import List, Dict

# API endpoint
BASE_URL = "http://localhost:8000"

def get_players() -> List[Dict]:
    """Get all available players from the API"""
    response = requests.get(f"{BASE_URL}/api/players")
    if response.status_code == 200:
        return response.json()["players"]
    else:
        raise Exception(f"Failed to get players: {response.status_code}")

def get_recommendations(available_players: List[Dict], current_roster: List[Dict], 
                       current_round: int, draft_slot: int) -> List[Dict]:
    """Get ML recommendations from the API"""
    
    # Calculate roster counts
    roster_counts = {
        'QB': len([p for p in current_roster if p['position'] == 'QB']),
        'RB': len([p for p in current_roster if p['position'] == 'RB']),
        'WR': len([p for p in current_roster if p['position'] == 'WR']),
        'TE': len([p for p in current_roster if p['position'] == 'TE']),
        'K': len([p for p in current_roster if p['position'] == 'K']),
        'DST': len([p for p in current_roster if p['position'] == 'DST']),
        'FLEX': 0,
        'BENCH': len(current_roster)
    }
    
    payload = {
        "available_players": available_players,
        "current_roster": current_roster,
        "current_round": current_round,
        "draft_slot": draft_slot,
        "teams": 10,
        "rounds": 16,
        "roster_counts": roster_counts
    }
    
    response = requests.post(f"{BASE_URL}/api/recommend", json=payload)
    if response.status_code == 200:
        return response.json()["recommendations"]
    else:
        raise Exception(f"Failed to get recommendations: {response.status_code}")

def print_round_header(round_num: int, pick_num: int, draft_slot: int):
    """Print round header information"""
    print(f"\n{'='*60}")
    print(f"ROUND {round_num} - PICK {pick_num} (Draft Slot {draft_slot})")
    print(f"{'='*60}")

def print_recommendations(recommendations: List[Dict], round_num: int):
    """Print recommendations for a round"""
    print(f"\nTop 5 Recommendations for Round {round_num}:")
    print(f"{'Rank':<4} {'Name':<20} {'Pos':<3} {'ADP':<4} {'Tier':<5} {'Score':<8} {'Priority':<10}")
    print("-" * 70)
    
    for i, rec in enumerate(recommendations[:5], 1):
        player = rec['player']
        print(f"{i:<4} {player['name']:<20} {player['position']:<3} {player['adp']:<4} {player['tier']:<5} {rec['score']:<8.1f} {rec['priority']:<10}")

def run_mock_draft():
    """Run a complete mock draft simulation"""
    print("🏈 GRIDIRON GURU AI - MOCK DRAFT SIMULATION")
    print("=" * 60)
    
    # Get all players
    print("Loading players...")
    all_players = get_players()
    print(f"Loaded {len(all_players)} players")
    
    # Initialize draft state
    draft_slot = 1  # Drafting 1st overall
    current_roster = []
    drafted_players = []
    available_players = all_players.copy()
    
    # Track picks by round
    picks_by_round = {}
    
    # Simulate first 8 rounds (most critical for testing)
    for round_num in range(1, 9):
        # Calculate current pick number
        if round_num % 2 == 1:
            pick_num = (round_num - 1) * 10 + draft_slot
        else:
            pick_num = round_num * 10 - draft_slot + 1
        
        print_round_header(round_num, pick_num, draft_slot)
        
        # Get recommendations
        try:
            recommendations = get_recommendations(available_players, current_roster, round_num, draft_slot)
            print_recommendations(recommendations, round_num)
            
            # Select the top recommendation
            if recommendations:
                selected_player = recommendations[0]['player']
                print(f"\n🎯 SELECTED: {selected_player['name']} ({selected_player['position']}) - ADP {selected_player['adp']}, Tier {selected_player['tier']}")
                
                # Add to roster
                current_roster.append(selected_player)
                drafted_players.append(selected_player)
                
                # Remove from available players
                available_players = [p for p in available_players if p['name'] != selected_player['name']]
                
                # Store pick info
                picks_by_round[round_num] = {
                    'pick_num': pick_num,
                    'player': selected_player,
                    'recommendations': recommendations[:5]
                }
                
                # Print roster summary
                roster_summary = {}
                for pos in ['QB', 'RB', 'WR', 'TE', 'K', 'DST']:
                    roster_summary[pos] = len([p for p in current_roster if p['position'] == pos])
                
                print(f"📊 Roster: QB:{roster_summary['QB']} RB:{roster_summary['RB']} WR:{roster_summary['WR']} TE:{roster_summary['TE']} K:{roster_summary['K']} DST:{roster_summary['DST']}")
                
        except Exception as e:
            print(f"❌ Error getting recommendations: {e}")
            break
    
    # Print draft summary
    print(f"\n{'='*60}")
    print("DRAFT SUMMARY")
    print(f"{'='*60}")
    
    for round_num in range(1, 9):
        if round_num in picks_by_round:
            pick_info = picks_by_round[round_num]
            player = pick_info['player']
            print(f"Round {round_num} (Pick {pick_info['pick_num']}): {player['name']} - {player['position']} - ADP {player['adp']}, Tier {player['tier']}")
    
    # Analyze draft quality
    print(f"\n{'='*60}")
    print("DRAFT QUALITY ANALYSIS")
    print(f"{'='*60}")
    
    # Check for reaches (ADP much higher than pick)
    reaches = []
    for round_num, pick_info in picks_by_round.items():
        pick_num = pick_info['pick_num']
        player = pick_info['player']
        adp = player['adp']
        
        if adp > pick_num + 20:
            reaches.append({
                'round': round_num,
                'pick': pick_num,
                'player': player['name'],
                'adp': adp,
                'reach': adp - pick_num
            })
    
    if reaches:
        print("🚨 REACHES DETECTED:")
        for reach in reaches:
            print(f"  Round {reach['round']}: {reach['player']} - Pick {reach['pick']}, ADP {reach['adp']} (Reach: +{reach['reach']})")
    else:
        print("✅ No significant reaches detected")
    
    # Check for steals (ADP much lower than pick)
    steals = []
    for round_num, pick_info in picks_by_round.items():
        pick_num = pick_info['pick_num']
        player = pick_info['player']
        adp = player['adp']
        
        if adp < pick_num - 20:
            steals.append({
                'round': round_num,
                'pick': pick_num,
                'player': player['name'],
                'adp': adp,
                'value': pick_num - adp
            })
    
    if steals:
        print("\n💎 STEALS DETECTED:")
        for steal in steals:
            print(f"  Round {steal['round']}: {steal['player']} - Pick {steal['pick']}, ADP {steal['adp']} (Value: +{steal['value']})")
    else:
        print("\n✅ No significant steals detected")
    
    # Position distribution analysis
    print(f"\n📊 POSITION DISTRIBUTION:")
    for pos in ['QB', 'RB', 'WR', 'TE', 'K', 'DST']:
        count = len([p for p in current_roster if p['position'] == pos])
        print(f"  {pos}: {count}")

if __name__ == "__main__":
    try:
        run_mock_draft()
    except Exception as e:
        print(f"❌ Mock draft failed: {e}")
        import traceback
        traceback.print_exc()
