# Project Structure

```
gridiron-guru-ai/
├── app/                           # Main application package
│   ├── __init__.py               # Package initialization
│   ├── api/                      # API layer
│   │   ├── __init__.py
│   │   └── main.py              # FastAPI application
│   ├── models/                   # Data models and database
│   │   ├── __init__.py
│   │   ├── models.py            # Pydantic models
│   │   └── database.py          # Database configuration
│   ├── ml/                      # Machine Learning logic
│   │   ├── __init__.py
│   │   ├── ml_logic.py          # ML models and scoring
│   │   └── draft_logic.py       # Draft strategy rules
│   ├── frontend/                # HTML frontend files
│   │   ├── enhanced_draft_assistant.html
│   │   └── fixed_draft_assistant_prepopulated.html
│   └── static/                  # Static assets
│       └── top160_upload_2025-08-30.csv
├── models/                       # Trained ML models (auto-generated)
├── main.py                      # Application entry point
├── setup.py                     # Python package setup
├── requirements.txt              # Python dependencies
├── Dockerfile                    # Docker container definition
├── docker-compose.yml           # Docker services orchestration
├── start.sh                     # Quick start script
├── .gitignore                   # Git ignore rules
├── README.md                    # Project documentation
└── PROJECT_STRUCTURE.md         # This file
```

## Package Organization

### `app.api`
- **main.py**: FastAPI application with all endpoints
- Handles HTTP requests and responses
- Integrates ML models with API endpoints

### `app.models`
- **models.py**: Pydantic data models for API requests/responses
- **database.py**: SQLAlchemy database configuration and models
- Defines data structures and database schema

### `app.ml`
- **ml_logic.py**: Core ML functionality
  - Random Forest models for each position
  - Player scoring and ranking algorithms
  - Feature engineering and model training
- **draft_logic.py**: Strategic draft rules
  - Position scarcity adjustments
  - Round-specific strategies
  - Roster balance rules

### `app.frontend`
- Modern HTML/CSS/JavaScript interface
- Real-time draft board updates
- ML recommendation display
- Draft state management

### `app.static`
- CSV data files
- Player databases
- Static assets for the application
