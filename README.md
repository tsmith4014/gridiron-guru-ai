# 🚀 Enhanced Fantasy Draft Assistant with ML

This is a **revolutionary fantasy football draft tool** that combines machine learning with strategic draft logic to give you the smartest possible recommendations.

## ✨ What Makes This Special?

### 🤖 **Machine Learning Powered**

- **Position-specific ML models** for RB, WR, TE, QB, K, DST
- **Historical data training** (synthetic data included, can be replaced with real data)
- **Continuous learning** - models improve with more data
- **Confidence scoring** for every recommendation

### 🧠 **Intelligent Logic**

- **Tier consideration** - Tier 1 players get significant bonuses
- **Late-round strategy** - K/DST priority in rounds 12+
- **Handcuff detection** - Automatically identifies backup RBs
- **Value vs. need balance** - Don't pass on steals
- **Position scarcity awareness** - Boosts scarce positions
- **Round-specific adjustments** - Different strategies for different rounds

### 🎯 **Advanced Features**

- **Risk assessment** for every player
- **Upside potential** calculations
- **Bye week conflict** detection
- **Roster balance** optimization
- **Strategic insights** for each round

## 🚀 Quick Start

### Option 1: Docker (Recommended)

```bash
# Build and run the entire system
docker-compose up --build

# Access the tool at: http://localhost:8000
```

### Option 2: Local Development

```bash
# Install Python dependencies
pip install -r requirements.txt

# Run the backend
python main.py

# Access the tool at: http://localhost:8000
```

## 🏗️ Architecture

```
Frontend (HTML/JS) ←→ FastAPI Backend ←→ ML Models + Database
```

### **Frontend**

- Enhanced HTML interface with modern styling
- Real-time updates via API calls
- Smart recommendation display

### **Backend (FastAPI)**

- RESTful API endpoints
- Database integration (PostgreSQL)
- ML model management

### **ML Engine**

- **Random Forest models** for each position
- **Feature engineering** (ADP, tier, age, experience, SOS)
- **Score combination** with strategic rules

### **Database**

- Player data storage
- Draft history tracking
- Model performance metrics

## 🔧 API Endpoints

### **Get Recommendations**

```http
POST /api/recommend
Content-Type: application/json

{
  "available_players": [...],
  "current_roster": [...],
  "current_round": 3,
  "draft_slot": 2,
  "teams": 10,
  "roster_counts": {...}
}
```

### **Analyze Player**

```http
POST /api/analyze-player
Content-Type: application/json

{
  "name": "Ja'Marr Chase",
  "position": "WR",
  "team": "CIN",
  "adp": 1,
  "tier": "1"
}
```

### **Update ML Model**

```http
POST /api/update-model
```

## 🧮 How the ML Logic Works

### **1. Base ML Scoring**

- Each position has its own trained model
- Models predict fantasy point potential
- Features: ADP, tier, age, experience, strength of schedule

### **2. Strategic Adjustments**

- **Positional needs** (RB < 2, WR < 2, etc.)
- **Round-specific logic** (early vs. late round strategies)
- **Risk assessment** (injury history, age, experience)
- **Value vs. need balance** (don't pass on steals)

### **3. Advanced Features**

- **Handcuff detection** (backup RBs to your starters)
- **Position scarcity** (fewer good TEs available)
- **Bye week conflicts** (avoid multiple starters on same bye)
- **Roster balance** (optimal depth distribution)

### **4. Final Scoring Formula**

```
Total Score = (ML Score × 0.4) +
              (Need Score × 0.3) +
              (Risk Score × 0.15) +
              (Handcuff Score × 0.1) +
              (Round Score × 0.05)
```

## 📊 Example ML Output

```json
{
  "recommendations": [
    {
      "player": {
        "name": "Bijan Robinson",
        "position": "RB",
        "team": "ATL",
        "adp": 2,
        "tier": "1"
      },
      "score": 187.5,
      "priority": "🔥 TOP PICK",
      "reasoning": [
        "High ML-predicted value",
        "Fills positional need",
        "Low risk option",
        "Elite ADP",
        "Tier 1 talent"
      ],
      "confidence": 0.95,
      "risk_factor": 0.15,
      "upside_potential": 0.85
    }
  ],
  "strategy": "Focus on best available player regardless of position",
  "insights": ["⚠️ Only 12 RBs remaining", "💡 Strong WR depth"]
}
```

## 🔄 Training Your Own Models

### **1. Replace Synthetic Data**

```python
# In ml_logic.py, replace generate_training_data() with:
def generate_training_data(self) -> pd.DataFrame:
    # Load your real historical fantasy data
    # Columns: position, adp, tier, age, experience, strength_of_schedule, fantasy_points
    return pd.read_csv("your_historical_data.csv")
```

### **2. Add More Features**

```python
# Extend the Player model in models.py:
class Player(BaseModel):
    # ... existing fields ...
    target_share: Optional[float] = None
    red_zone_touches: Optional[int] = None
    team_offensive_rank: Optional[int] = None
    weather_impact: Optional[float] = None
```

### **3. Custom ML Algorithms**

```python
# In ml_logic.py, replace RandomForest with:
from sklearn.ensemble import GradientBoostingRegressor, XGBRegressor
from sklearn.neural_network import MLPRegressor

self.models = {
    'RB': XGBRegressor(n_estimators=200, learning_rate=0.1),
    'WR': MLPRegressor(hidden_layer_sizes=(100, 50), max_iter=1000),
    # ... etc
}
```

## 🎯 Usage Examples

### **Round 1-3: Best Available**

- ML models identify elite players
- Strategic rules ensure no K/DST
- Focus on value over need

### **Round 4-7: Balanced Approach**

- Balance positional needs with value
- Build starter depth
- Avoid obvious reaches

### **Round 8-11: Depth Building**

- Focus on roster depth
- Consider handcuffs
- Prepare for late rounds

### **Round 12-16: Needs & K/DST**

- Prioritize filling needs
- High priority for K/DST
- Value picks for bench

## 🚀 Future Enhancements

### **Planned Features**

- **Real-time ADP updates** from major platforms
- **Weather integration** for game-day decisions
- **Injury risk modeling** using medical data
- **Team chemistry analysis** for handcuffs
- **Auction draft support** with bid optimization

### **ML Improvements**

- **Deep learning models** for complex patterns
- **Ensemble methods** combining multiple algorithms
- **Online learning** for real-time updates
- **Transfer learning** from previous seasons

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch**
3. **Add your improvements**
4. **Submit a pull request**

### **Areas for Contribution**

- **Data collection** scripts for real fantasy data
- **Additional ML algorithms**
- **Frontend improvements**
- **Testing and validation**
- **Documentation**

## 📈 Performance Metrics

The ML models are evaluated using:

- **R² Score** (how well predictions fit)
- **Mean Squared Error** (prediction accuracy)
- **Cross-validation** (model stability)
- **Feature importance** (what drives decisions)

## 🔒 Security & Privacy

- **No external API calls** (all processing local)
- **Database encryption** for sensitive data
- **Input validation** on all endpoints
- **Rate limiting** for API abuse prevention

## 📞 Support

- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Wiki**: Comprehensive usage guides

---

**Built with ❤️ for fantasy football enthusiasts who want to win their leagues!**
