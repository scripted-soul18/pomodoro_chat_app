import streamlit as st 
import time

# Page config
st.set_page_config(page_title="Pomodoro Chat", layout="centered")

# Title
st.title("Pomodoro + Study buddy chat")
st.markdown("Focus Time: 25:00")

# Initialize session state variables 
if "start_time" not in st.session_state:
    st.session_state.start_time = None

if "running" not in st.session_state:
    st.session_state.running = False

# Timer logic
def start_timer():
    st.session_state.start_time = time.time()
    st.session_state.running = True

def reset_timer():
    st.session_state.running = False
    st.session_state.start_time = None

# Time controls
st.markdown("⌚ Timer Controls")
col1, col2 = st.columns(2)
with col1:
    if st.button("▶ Start"):
        start_timer()

with col2:
    if st.button("🔁 Reset"):
        reset_timer()

# Countdown Display 
if st.session_state.running and st.session_state.start_time:
    elapsed = int(time.time() - st.session_state.start_time)
    remaining = max(0, 25 * 60 - elapsed)
    mins, secs = divmod(remaining, 60)
    st.markdown(f"Time Left: {mins:02d}:{secs:02d}")

    if remaining == 0:
        st.success("✅ Pomodoro Complete!")
        st.balloons()
        reset_timer()
    else:
        # Only rerun if timer is still running
        time.sleep(1)
        st.rerun()