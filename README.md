# Weekly Workout Tracker

A Streamlit app to track your weekly workout plan with exercise logging, notes, and persistent cloud storage via GitHub.

## Features
- Import weekly training plans from JSON
- Log each exercise with weight, reps, pace, and personal notes
- Navigate back through exercises
- **Automatic GitHub persistence** - workouts persist across page refreshes
- Rest timers for between sets
- View completed workout history

## Setup (Local)

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create `.streamlit/secrets.toml`:
```toml
GITHUB_TOKEN = "your_github_token_here"
GITHUB_REPO = "your_username/workout-app"
GITHUB_FILE = "week_1.json"
```

3. Run locally:
```bash
streamlit run gym_app.py
```

## Setup (Streamlit Cloud)

1. Push code to GitHub (see below)

2. Create a GitHub Personal Access Token:
   - Go to https://github.com/settings/tokens
   - Create new token with "repo" scope
   - Copy the token

3. Deploy to Streamlit Cloud:
   - Go to https://share.streamlit.io
   - Select this repo and `gym_app.py`
   - Add your GitHub token to **Secrets** (gear icon → Secrets):
   ```toml
   GITHUB_TOKEN = "your_token_here"
   GITHUB_REPO = "your_username/workout-app"
   GITHUB_FILE = "week_1.json"
   ```

## How It Works

1. Upload your weekly plan JSON
2. Log exercises with notes each day
3. **Workouts auto-save to GitHub** - even if you refresh the page
4. Next time you open the app, your progress loads automatically
5. At the end of the week, download your complete workout log

## JSON Format

Upload a JSON file with this structure:
```json
{
  "macro_goal": "Your macro goal",
  "week_goal": "Your weekly goal",
  "Monday": {
    "theme": "Legs",
    "exercises": [
      {
        "name": "Squats",
        "type": "weight",
        "target_sets": 3,
        "target_reps": 10,
        "rest_sec": 90,
        "video": "https://youtube.com/..."
      }
    ]
  }
  ...
}
```

## Data Persistence

- Your plan and completed workouts are stored in your GitHub repo
- Data persists permanently across page refreshes and app restarts
- Perfect for logging workouts on your phone while at the gym
