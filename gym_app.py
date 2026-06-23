import streamlit as st
import time
import json

# --- 1. Empty Default State ---
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
    st.session_state.plan = default_plan
if 'view' not in st.session_state:
    st.session_state.view = 'dashboard'
if 'current_day' not in st.session_state:
    st.session_state.current_day = None
if 'exercise_index' not in st.session_state:
    st.session_state.exercise_index = 0
if 'workout_log' not in st.session_state:
    st.session_state.workout_log = []
if 'weekly_log' not in st.session_state:
    st.session_state.weekly_log = []

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
        st.session_state.weekly_log.append(st.session_state.current_session)
        del st.session_state.current_session
    st.session_state.view = 'dashboard'

# --- 2. The UI Layout ---
st.set_page_config(page_title="Weekly Block", page_icon="🏋️", layout="centered")

if st.session_state.view == 'dashboard':
    st.title("Weekly Training Block")
    
    # --- DATA MANAGEMENT (Moved to the top!) ---
    st.subheader("Data Management")
    uploaded_file = st.file_uploader("📥 Import Weekly Plan (JSON)", type="json")
    
    if uploaded_file is not None:
        try:
            st.session_state.plan = json.load(uploaded_file)
            st.success("Plan loaded successfully! Scroll down to see your week.")
        except Exception as e:
            st.error("Invalid JSON file.")
            
    # Export button is always visible now
    st.download_button(
        "📤 Export Results", 
        data=json.dumps(st.session_state.weekly_log, indent=2) if st.session_state.weekly_log else "[]", 
        file_name="completed_week_log.json",
        use_container_width=True
    )
    st.divider()

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