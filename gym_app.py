import streamlit as st
import time
import json
from datetime import datetime
from github import Github, GithubException

st.set_page_config(page_title="Weekly Block", page_icon="🏋️", layout="centered")

# --- 1. GitHub Integration ---
@st.cache_resource
def get_github_client():
    try:
        token = st.secrets.get("GITHUB_TOKEN")
        if not token or token == "your_github_token_here":
            return None
        return Github(token)
    except:
        return None

@st.cache_data(ttl=60)
def load_from_github():
    """Load plan and completed workouts from GitHub"""
    try:
        client = get_github_client()
        if not client:
            return None
        
        repo_name = st.secrets.get("GITHUB_REPO", "")
        file_name = st.secrets.get("GITHUB_FILE", "week_1.json")
        
        if not repo_name:
            return None
            
        repo = client.get_user().get_repo(repo_name.split("/")[1])
        file_content = repo.get_contents(file_name)
        return json.loads(file_content.decoded_content.decode())
    except Exception as e:
        st.warning(f"Could not load from GitHub: {str(e)}")
        return None

def save_to_github(data):
    """Save plan and workouts back to GitHub"""
    try:
        client = get_github_client()
        if not client:
            st.error("GitHub integration not configured. See secrets setup.")
            return False
        
        repo_name = st.secrets.get("GITHUB_REPO", "")
        file_name = st.secrets.get("GITHUB_FILE", "week_1.json")
        
        if not repo_name:
            st.error("GitHub repo not configured in secrets.")
            return False
            
        repo = client.get_user().get_repo(repo_name.split("/")[1])
        
        try:
            file_content = repo.get_contents(file_name)
            repo.update_file(
                file_name, 
                f"Update workout data - {datetime.now().isoformat()}", 
                json.dumps(data, indent=2),
                file_content.sha
            )
        except GithubException:
            repo.create_file(
                file_name,
                f"Create workout data - {datetime.now().isoformat()}",
                json.dumps(data, indent=2)
            )
        return True
    except Exception as e:
        st.error(f"Failed to save to GitHub: {str(e)}")
        return False

# --- 2. Empty Default State ---
default_plan = {
    "macro_goal": "Awaiting Plan Import...",
    "week_goal": "Upload your JSON file to begin.",
    "Monday": {"theme": "Rest", "exercises": []},
    "Tuesday": {"theme": "Rest", "exercises": []},
    "Wednesday": {"theme": "Rest", "exercises": []},
    "Thursday": {"theme": "Rest", "exercises": []},
    "Friday": {"theme": "Rest", "exercises": []}
}

if 'plan' not in st.session_state:
    github_data = load_from_github()
    if github_data:
        st.session_state.plan = {k: v for k, v in github_data.items() if k in ["macro_goal", "week_goal", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]}
        st.session_state.weekly_log = github_data.get("completed_workouts", [])
    else:
        st.session_state.plan = default_plan
        st.session_state.weekly_log = []
if 'view' not in st.session_state:
    st.session_state.view = 'dashboard'
if 'current_day' not in st.session_state:
    st.session_state.current_day = None
if 'exercise_index' not in st.session_state:
    st.session_state.exercise_index = 0
if 'workout_log' not in st.session_state:
    st.session_state.workout_log = []

# --- Helper Functions ---
def start_workout(day):
    st.session_state.current_day = day
    st.session_state.exercise_index = 0
    st.session_state.workout_log = []
    st.session_state.current_session = {
        "day": day,
        "theme": st.session_state.plan[day]["theme"],
        "exercises": []
    }
    st.session_state.view = 'workout'

def next_exercise(logged_data):
    st.session_state.workout_log.append(logged_data)
    if 'current_session' in st.session_state:
        st.session_state.current_session["exercises"].append(logged_data)
    st.session_state.exercise_index += 1
    total_ex = len(st.session_state.plan[st.session_state.current_day]["exercises"])
    if st.session_state.exercise_index >= total_ex:
        st.session_state.view = 'wrap_up'

def previous_exercise():
    if st.session_state.exercise_index <= 0:
        st.session_state.view = 'dashboard'
        st.session_state.current_day = None
        st.session_state.workout_log = []
        if 'current_session' in st.session_state:
            del st.session_state.current_session
        return

    st.session_state.exercise_index -= 1
    if st.session_state.workout_log:
        st.session_state.workout_log.pop()
    if 'current_session' in st.session_state and st.session_state.current_session["exercises"]:
        st.session_state.current_session["exercises"].pop()
    st.session_state.view = 'workout'

def finish_workout(notes):
    st.session_state.workout_log.append({"notes": notes})
    if 'current_session' in st.session_state:
        st.session_state.current_session["notes"] = notes
        st.session_state.current_session["completed_at"] = datetime.now().isoformat()
        st.session_state.weekly_log.append(st.session_state.current_session)
        del st.session_state.current_session
    
    # Save to GitHub
    github_data = {
        "macro_goal": st.session_state.plan["macro_goal"],
        "week_goal": st.session_state.plan["week_goal"],
        "Monday": st.session_state.plan["Monday"],
        "Tuesday": st.session_state.plan["Tuesday"],
        "Wednesday": st.session_state.plan["Wednesday"],
        "Thursday": st.session_state.plan["Thursday"],
        "Friday": st.session_state.plan["Friday"],
        "completed_workouts": st.session_state.weekly_log
    }
    
    if save_to_github(github_data):
        st.success("✅ Workout saved to GitHub!")
        st.cache_data.clear()
    
    st.session_state.view = 'dashboard'

# --- 3. The UI Layout ---
if st.session_state.view == 'dashboard':
    st.title("Weekly Training Block")
    
    # --- DATA MANAGEMENT (Moved to the top!) ---
    st.subheader("Data Management")
    uploaded_file = st.file_uploader("📥 Import Weekly Plan (JSON)", type="json")
    
    if uploaded_file is not None:
        try:
            new_plan = json.load(uploaded_file)
            st.session_state.plan = new_plan
            
            # Save new plan to GitHub
            github_data = {
                "macro_goal": new_plan.get("macro_goal", ""),
                "week_goal": new_plan.get("week_goal", ""),
                "Monday": new_plan.get("Monday", {"theme": "Rest", "exercises": []}),
                "Tuesday": new_plan.get("Tuesday", {"theme": "Rest", "exercises": []}),
                "Wednesday": new_plan.get("Wednesday", {"theme": "Rest", "exercises": []}),
                "Thursday": new_plan.get("Thursday", {"theme": "Rest", "exercises": []}),
                "Friday": new_plan.get("Friday", {"theme": "Rest", "exercises": []}),
                "completed_workouts": st.session_state.weekly_log
            }
            
            if save_to_github(github_data):
                st.success("✅ New plan loaded and saved to GitHub!")
                st.cache_data.clear()
            else:
                st.warning("Plan loaded locally, but couldn't save to GitHub. Your data may not persist.")
        except Exception as e:
            st.error(f"Invalid JSON file: {str(e)}")
            
    # Export button
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "📥 Download Results", 
            data=json.dumps(st.session_state.weekly_log, indent=2) if st.session_state.weekly_log else "[]", 
            file_name=f"workout_log_{datetime.now().strftime('%Y%m%d')}.json",
            use_container_width=True
        )
    with col2:
        if st.button("🔄 Refresh from GitHub", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    st.divider()
    
    # --- GitHub Status ---
    if get_github_client():
        st.success("✅ GitHub integration active - Your workouts auto-save!")
    else:
        st.warning("⚠️ GitHub integration not configured - Data won't persist on refresh. See README for setup.")

    # --- SCHEDULE DRAWING ---
    st.subheader("Macro Goal")
    st.info(st.session_state.plan["macro_goal"])
    
    st.subheader("This Week's Focus")
    st.info(st.session_state.plan["week_goal"])
    
    st.subheader("Your Schedule")
    
    for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]:
        day_data = st.session_state.plan[day]
        ex_count = len(day_data["exercises"])
        
        with st.container(border=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{day}: {day_data['theme']}**")
                st.caption(f"{ex_count} Exercises planned")
            with col2:
                if ex_count > 0:
                    st.button("Start", key=f"start_{day}", on_click=start_workout, args=(day,))
                else:
                    st.button("Rest", key=f"rest_{day}", disabled=True)

elif st.session_state.view == 'workout':
    day = st.session_state.current_day
    idx = st.session_state.exercise_index
    ex = st.session_state.plan[day]["exercises"][idx]
    total_ex = len(st.session_state.plan[day]["exercises"])
    
    progress_val = (idx) / total_ex
    st.progress(progress_val, text=f"Exercise {idx + 1} of {total_ex}")
    
    st.caption(f"{day} - {st.session_state.plan[day]['theme']}")
    st.header(ex["name"])
    
    if "video" in ex:
        st.link_button("📺 Watch Technique Tutorial", ex["video"], use_container_width=True)
    st.divider()
        
    logged_data = {"name": ex["name"], "type": ex["type"], "note": ""}
    
    with st.form(key=f"form_{idx}"):
        exercise_note = st.text_area("Exercise Note", placeholder="Optional note for this exercise")
        if ex["type"] == "weight":
            st.markdown(f"**Target:** {ex['target_sets']} Sets x {ex['target_reps']} Reps")
            col1, col2 = st.columns(2)
            with col1:
                weight = st.number_input("Weight Used (kg)", min_value=0.0, step=1.0)
            with col2:
                reps = st.number_input("Reps Achieved", min_value=0, step=1)
            logged_data["weight"] = weight
            logged_data["reps"] = reps
            
        elif ex["type"] == "cardio":
            st.markdown(f"**Target:** {ex['distance']} at {ex['target_pace']}")
            col1, col2 = st.columns(2)
            with col1:
                time_val = st.text_input("Actual Time")
            with col2:
                pace = st.text_input("Actual Pace")
            logged_data["time"] = time_val
            logged_data["pace"] = pace
            
        elif ex["type"] == "stretch":
            st.markdown(f"*{ex.get('notes', '')}*")

        logged_data["note"] = exercise_note

        nav_col1, nav_col2 = st.columns(2)
        with nav_col1:
            back_btn = st.form_submit_button("BACK", use_container_width=True)
        with nav_col2:
            submit_btn = st.form_submit_button("NEXT EXERCISE", use_container_width=True, type="primary")

        if back_btn:
            previous_exercise()
            st.rerun()
        if submit_btn:
            next_exercise(logged_data)
            st.rerun()

    if "rest_sec" in ex:
        st.divider()
        st.markdown(f"**Suggested Rest:** {ex['rest_sec']} seconds")
        if st.button("⏱️ Start Timer", use_container_width=True):
            timer_placeholder = st.empty()
            for i in range(ex['rest_sec'], 0, -1):
                timer_placeholder.markdown(f"### ⏳ {i}s remaining")
                time.sleep(1)
            timer_placeholder.success("TIME'S UP! Get ready.")

elif st.session_state.view == 'wrap_up':
    st.balloons()
    st.header("Workout Complete! 🏆")
    notes = st.text_area("Daily Notes", placeholder="How did you feel today?")
    if st.button("SAVE & FINISH", use_container_width=True, type="primary"):
        finish_workout(notes)
        st.rerun()