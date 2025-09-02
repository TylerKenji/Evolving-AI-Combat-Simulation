# Battle AI Development Setup Guide

## Quick Start

### 1. Install Python
Download and install Python 3.8+ from [python.org](https://www.python.org/downloads/)
- ✅ **Important**: Check "Add Python to PATH" during installation

### 2. Run Setup Script
```bash
# Windows
setup_env.bat

# Or manually:
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Verify Installation
```bash
# Activate environment
venv\Scripts\activate

# Run tests
pytest tests/

# Check core imports
python -c "from src.utils import Vector2D, Config; print('Setup successful!')"
```

## Project Structure

```
Battle AI Strategy Doc/
├── src/                          # Main source code
│   ├── __init__.py
│   ├── agents/                   # AI agent implementations
│   ├── environment/              # Battle environment and physics
│   ├── evolution/                # Genetic algorithms and evolution
│   └── utils/                    # Utility classes and functions
│       ├── vector2d.py          # ✅ 2D vector mathematics
│       └── config.py            # ✅ Configuration management
├── tests/                        # Unit tests
│   ├── test_vector2d.py         # ✅ Vector2D tests
│   └── test_config.py           # ✅ Config tests
├── config/                       # Configuration files
│   └── default.yaml             # ✅ Default settings
├── docs/                         # Documentation
├── requirements.txt              # ✅ Python dependencies
├── setup_env.bat                # ✅ Environment setup script
└── .gitignore                   # ✅ Git ignore rules
```

## Phase 1 Tasks Completed ✅

### Week 1: Project Setup & Core Architecture
- [x] 1.1.4 Initialize Git repository with proper .gitignore
- [x] 1.1.5 Create basic project folder structure  
- [x] 1.1.7 Create requirements.txt file
- [x] 1.2.4 Design configuration management system
- [x] 1.3.1 Implement Vector2D class for positions/velocities

### Testing Framework
- [x] Unit tests for Vector2D class
- [x] Unit tests for Configuration system
- [x] Test infrastructure setup

## Next Steps (Phase 1 Continuation)

### Immediate Tasks
1. **Install Python and run setup script**
2. **Verify tests pass**: `pytest tests/`
3. **Start Task 1.2.1**: Design Agent base class interface
4. **Start Task 1.2.2**: Design Environment base class interface

### Development Workflow
1. **Activate environment**: `venv\Scripts\activate`
2. **Run tests before coding**: `pytest tests/`
3. **Implement feature**
4. **Write tests for new feature**
5. **Run tests again**: `pytest tests/`
6. **Commit changes**: `git add . && git commit -m "Description"`

## Available Tools

### Testing
```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_vector2d.py

# Run with coverage
pytest --cov=src tests/
```

### Code Quality
```bash
# Format code (will be available after pip install)
black src/ tests/

# Lint code (will be available after pip install)
flake8 src/ tests/

# Type checking (will be available after pip install)
mypy src/
```

## Configuration

The system uses YAML configuration files in the `config/` directory:

```yaml
# config/default.yaml
simulation:
  max_agents: 10
  battlefield_width: 800
  battlefield_height: 600
  time_step: 0.1

agents:
  default_health: 100
  default_speed: 50.0
  collision_radius: 10.0
```

## Core Classes Ready for Use

### Vector2D
```python
from src.utils import Vector2D

# Create vectors
pos = Vector2D(100, 200)
velocity = Vector2D(10, -5)

# Vector operations
new_pos = pos + velocity
distance = pos.distance_to(Vector2D(0, 0))
unit_vector = velocity.normalize()
```

### Configuration
```python
from src.utils import Config, config_manager

# Load configuration
config = config_manager.load_config('config/default.yaml')

# Access configuration values
max_agents = config.simulation.max_agents
agent_health = config.agents.default_health
```

## Troubleshooting

### Python Not Found
- Reinstall Python with "Add to PATH" checked
- Restart terminal/command prompt
- Verify with: `python --version`

### Import Errors
- Ensure virtual environment is activated: `venv\Scripts\activate`
- Reinstall dependencies: `pip install -r requirements.txt`
- Check you're in the correct directory

### Test Failures
- Make sure virtual environment is activated
- Check all dependencies are installed
- Verify Python version is 3.8+

## Next Development Phase

Once setup is complete, continue with **Task 1.2.1** from `TASK_BREAKDOWN.md`:
- Design Agent base class interface
- Design Environment base class interface  
- Implement basic agent framework

The foundation is ready for rapid development! 🚀
