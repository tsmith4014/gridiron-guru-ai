# 🏈 Gridiron Guru AI - Fantasy Football Draft Assistant

> **AI-Powered Fantasy Football Draft Assistant with ML-driven recommendations, advanced strategy logic, and real-time insights for 2025 NFL drafts**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com)
[![ML](https://img.shields.io/badge/ML-Scikit--learn-orange.svg)](https://scikit-learn.org)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://docker.com)

## 🚀 Features

### 🤖 **Machine Learning Powered**
- **Position-specific ML models** for RB, WR, TE, QB, K, DST
- **Random Forest algorithms** trained on comprehensive fantasy data
- **Feature engineering** including ADP, tier, age, experience, strength of schedule
- **Real-time scoring** with confidence intervals and risk assessment

### 🧠 **Intelligent Logic**
- **Critical Need Prioritization** - Unfilled positions (QB, TE, K, DST) get extremely high priority
- **Roster Constraint Enforcement** - Ensures 1 QB, 2 RB, 2 WR, 1 TE, 1 K, 1 DST minimum requirements
- **Late-round strategy** - K/DST priority in rounds 14-16 (fixed timing)
- **Handcuff logic** - Backup RB recommendations for roster security
- **Value vs. need balance** - Prevents passing on steals while filling critical needs
- **Position scarcity** - Adjusts for dwindling position depth
- **Round-specific strategies** - Different approaches for early/mid/late rounds

### 🎯 **Advanced Features**
- **Risk assessment** for every player recommendation
- **Upside potential** calculations
- **Strategic insights** for each round
- **Next round focus** guidance
- **Real-time draft board** with live updates
- **Export/import** draft states
- **ADP Score Tracking** - Monitor total draft value in real-time

### 📊 **Full 160-Player Database**
- Complete 2025 NFL draft projections
- ADP rankings from major platforms
- Tier classifications (1-6)
- Team assignments and position data

### 🆕 **Recent Improvements (v1.1.0)**
- **Fixed DST/K Priority** - Now properly required and drafted in rounds 14-16
- **Enhanced Critical Need Scoring** - QB/TE get 500/350 base scores vs 20 for depth
- **Improved Draft Status Display** - Reactive UI that only shows after slot selection
- **Better Roster Constraint Logic** - Enforces 9 starters + 7 bench spots correctly
- **Fixed Turn-Based Draft Flow** - Proper round advancement and pick tracking
- **Added ADP Score Tracking** - Real-time tracking of total ADP points drafted

## 🏗️ Architecture

```
Gridiron Guru AI
├── 🎯 FastAPI Backend
│   ├── ML Engine (Scikit-learn)
│   ├── Strategic Rules Engine
│   └── PostgreSQL Database
├── 🎨 Modern Frontend
│   ├── Real-time Draft Board
│   ├── ML Recommendations
│   └── Roster Management
└── 🐳 Docker Deployment
    ├── Python Backend
    └── PostgreSQL Database
```

## 🚀 Quick Start

### Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/tsmith4014/gridiron-guru-ai.git
cd gridiron-guru-ai

# Start the entire system
./start.sh

# Access the application
open http://localhost:8000
```

### Option 2: Local Development

```bash
# Clone and setup
git clone https://github.com/tsmith4014/gridiron-guru-ai.git
cd gridiron-guru-ai

# Install Python dependencies
pip install -r requirements.txt

# Install PostgreSQL (or use Docker)
# Start the application
python main.py

# Access at http://localhost:8000
```

## 📁 Project Structure

```
gridiron-guru-ai/
├── app/                           # Main application package
│   ├── api/                      # FastAPI endpoints
│   ├── models/                   # Data models & database
│   ├── ml/                      # Machine Learning logic
│   ├── frontend/                # HTML interface
│   └── static/                  # Static assets
├── models/                       # Trained ML models
├── main.py                      # Application entry point
├── Dockerfile                    # Container definition
└── docker-compose.yml           # Services orchestration
```

## 🔌 API Endpoints

### **Get Recommendations**
```http
POST /api/recommend
{
  "available_players": [...],
  "current_roster": [...],
  "current_round": 1,
  "draft_slot": 1,
  "teams": 10,
  "rounds": 16,
  "roster_counts": {...}
}
```

### **Get Players**
```http
GET /api/players
```

### **Analyze Player**
```http
POST /api/analyze-player
```

### **Update ML Model**
```http
POST /api/update-model
```

## 🧠 How ML Logic Works

### **1. Base ML Scoring**
- Each position has its own trained Random Forest model
- Models predict fantasy point potential
- Features: ADP, tier, age, experience, strength of schedule

### **2. Strategic Adjustments**
- **Positional needs** (RB < 2, WR < 2, etc.)
- **Round-specific logic** (early vs. late round strategies)
- **Position scarcity** (fewer good TEs available)
- **Handcuff detection** (backup RBs to your starters)

### **3. Final Scoring Formula**
```
Total Score = (ML Score × 0.4) +
              (Need Score × 0.4) +
              (Risk Score × 0.1) +
              (Handcuff Score × 0.05) +
              (Round Score × 0.05)

Critical Need Bonus: ×2.0 for unfilled positions
```

## 🎯 Usage Examples

### **Roster Requirements**
- **Starters (9)**: 1 QB, 2 RB, 2 WR, 1 TE, 1 K, 1 DST, 1 FLEX
- **Bench (7)**: Additional depth at RB/WR/TE/QB
- **Total**: 16 players exactly

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
- **Rounds 12-13**: Fill remaining critical needs (QB, TE if missing)
- **Round 14**: K becomes available and gets high priority
- **Round 15**: DST becomes available and gets high priority
- **Round 16**: Bench depth and optimization

## 🔧 Configuration

### **Environment Variables**
```bash
DATABASE_URL=postgresql://user:pass@localhost/gridiron_guru
MODEL_PATH=models/draft_models.joblib
```

### **Docker Environment**
```yaml
environment:
  - DATABASE_URL=postgresql://postgres:password@db/gridiron_guru
```

## 🚀 Deployment

### **Production Setup**
```bash
# Build and deploy
docker-compose -f docker-compose.prod.yml up -d

# Scale services
docker-compose up -d --scale backend=3
```

### **Monitoring**
```bash
# View logs
docker-compose logs -f

# Check status
docker-compose ps

# Restart services
docker-compose restart backend
```

## 🤝 Contributing

### **Areas for Contribution**
- **Data collection** scripts for real fantasy data
- **Additional ML algorithms** (XGBoost, LightGBM)
- **Frontend improvements** (React, Vue.js)
- **Mobile app** development
- **API enhancements** and new endpoints

### **Development Setup**
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Format code
black app/
flake8 app/
```

## 📊 Performance & Metrics

The ML models are evaluated using:
- **R² Score** (how well predictions fit)
- **Mean Squared Error** (prediction accuracy)
- **Cross-validation** scores for robustness

## 🔒 Security

- **CORS configuration** for frontend integration
- **Input validation** with Pydantic models
- **SQL injection protection** via SQLAlchemy
- **Environment variable** management

## 📚 Documentation

- **API Docs**: http://localhost:8000/docs
- **Interactive API**: http://localhost:8000/redoc
- **Project Structure**: [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/tsmith4014/gridiron-guru-ai/issues)
- **Discussions**: [GitHub Discussions](https://github.com/tsmith4014/gridiron-guru-ai/discussions)
- **Wiki**: [Project Wiki](https://github.com/tsmith4014/gridiron-guru-ai/wiki)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Fantasy Football Community** for strategy insights
- **Scikit-learn** for ML capabilities
- **FastAPI** for modern web framework
- **PostgreSQL** for reliable data storage

---

**Built with ❤️ for fantasy football enthusiasts who want to win their leagues!**

*Gridiron Guru AI - Where AI meets fantasy football strategy*
