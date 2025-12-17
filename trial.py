import streamlit as st
import time
import json
import hashlib
from datetime import datetime
from typing import Dict, List

# Page config with better layout
st.set_page_config(
    page_title="Pomodoro Chat App",
    page_icon="🍅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern design
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(90deg, #FF6B6B, #4ECDC4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 2rem;
    }
    .timer-display {
        font-size: 4rem;
        font-weight: bold;
        text-align: center;
        padding: 2rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 20px;
        color: white;
        margin: 2rem 0;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }
    .timer-controls {
        display: flex;
        justify-content: center;
        gap: 1rem;
        margin: 2rem 0;
    }
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 3rem;
        font-size: 1.2rem;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.3);
    }
    .chat-container {
        background: #f8f9fa;
        border-radius: 15px;
        padding: 1.5rem;
        max-height: 500px;
        overflow-y: auto;
    }
    .chat-message {
        padding: 0.8rem;
        margin: 0.5rem 0;
        border-radius: 10px;
        background: white;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .chat-message.own {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        margin-left: 20%;
    }
    .chat-message.other {
        background: #e9ecef;
        margin-right: 20%;
    }
    .settings-card {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
def init_session_state():
    defaults = {
        "authenticated": False,
        "username": None,
        "user_id": None,
        "start_time": None,
        "running": False,
        "timer_mode": "focus",  # "focus" or "break"
        "focus_duration": 25 * 60,  # in seconds
        "break_duration": 10 * 60,  # in seconds
        "messages": {},
        "friends": [],
        "friend_requests": [],
        "current_chat": None,
        "users_db": {},
        "friends_db": {}
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# Simple user database (in production, use a real database)
def load_users():
    if "users_db" not in st.session_state:
        st.session_state.users_db = {}
    return st.session_state.users_db

def save_user(username, password, email):
    users = load_users()
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    user_id = hashlib.sha256(username.encode()).hexdigest()[:8]
    users[username] = {
        "password_hash": password_hash,
        "email": email,
        "user_id": user_id,
        "created_at": datetime.now().isoformat()
    }
    return user_id

def verify_user(username, password):
    users = load_users()
    if username in users:
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        if users[username]["password_hash"] == password_hash:
            return users[username]["user_id"]
    return None

def get_all_users():
    users = load_users()
    return [{"username": uname, "user_id": data["user_id"]} 
            for uname, data in users.items() 
            if uname != st.session_state.username]

# Authentication Functions
def login_page():
    st.markdown('<div class="main-header">🍅 Pomodoro Chat App</div>', unsafe_allow_html=True)
    st.markdown("### Welcome! Please sign in or create an account")
    
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Sign Up"])
    
    with tab1:
        st.subheader("Login")
        login_username = st.text_input("Username", key="login_user")
        login_password = st.text_input("Password", type="password", key="login_pass")
        
        if st.button("Login", type="primary", use_container_width=True):
            user_id = verify_user(login_username, login_password)
            if user_id:
                st.session_state.authenticated = True
                st.session_state.username = login_username
                st.session_state.user_id = user_id
                st.success("✅ Login successful!")
                st.rerun()
            else:
                st.error("❌ Invalid username or password")
    
    with tab2:
        st.subheader("Create Account")
        signup_username = st.text_input("Choose Username", key="signup_user")
        signup_email = st.text_input("Email", key="signup_email")
        signup_password = st.text_input("Password", type="password", key="signup_pass")
        signup_confirm = st.text_input("Confirm Password", type="password", key="signup_confirm")
        
        if st.button("Sign Up", type="primary", use_container_width=True):
            users = load_users()
            if signup_username in users:
                st.error("❌ Username already exists")
            elif signup_password != signup_confirm:
                st.error("❌ Passwords do not match")
            elif len(signup_password) < 6:
                st.error("❌ Password must be at least 6 characters")
            elif not signup_username or not signup_email:
                st.error("❌ Please fill in all fields")
            else:
                user_id = save_user(signup_username, signup_password, signup_email)
                st.session_state.authenticated = True
                st.session_state.username = signup_username
                st.session_state.user_id = user_id
                st.success("✅ Account created successfully!")
                st.rerun()

# Timer Functions
def format_time(seconds):
    mins, secs = divmod(int(seconds), 60)
    return f"{mins:02d}:{secs:02d}"

def start_timer():
    st.session_state.start_time = time.time()
    st.session_state.running = True

def reset_timer():
    st.session_state.running = False
    st.session_state.start_time = None

def pause_timer():
    if st.session_state.running and st.session_state.start_time:
        elapsed = time.time() - st.session_state.start_time
        if st.session_state.timer_mode == "focus":
            remaining = max(0, st.session_state.focus_duration - elapsed)
            st.session_state.focus_duration = remaining
        else:
            remaining = max(0, st.session_state.break_duration - elapsed)
            st.session_state.break_duration = remaining
        st.session_state.running = False
        st.session_state.start_time = None

def get_remaining_time():
    if not st.session_state.running or not st.session_state.start_time:
        if st.session_state.timer_mode == "focus":
            return st.session_state.focus_duration
        else:
            return st.session_state.break_duration
    
    elapsed = time.time() - st.session_state.start_time
    if st.session_state.timer_mode == "focus":
        remaining = st.session_state.focus_duration - elapsed
    else:
        remaining = st.session_state.break_duration - elapsed
    
    return max(0, remaining)

def timer_complete():
    if st.session_state.timer_mode == "focus":
        st.session_state.timer_mode = "break"
        st.balloons()
        st.success("🎉 Focus session complete! Time for a break!")
    else:
        st.session_state.timer_mode = "focus"
        st.success("✅ Break complete! Ready to focus again!")
    reset_timer()

# Main App
def main_app():
    # Sidebar for settings and friends
    with st.sidebar:
        st.markdown(f"### 👋 Welcome, {st.session_state.username}!")
        
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.username = None
            st.session_state.user_id = None
            st.rerun()
        
        st.divider()
        
        # Timer Settings
        st.markdown("### ⚙️ Timer Settings")
        focus_minutes = st.slider("Focus Duration (minutes)", 5, 60, 
                                   value=st.session_state.focus_duration // 60, 
                                   key="focus_slider")
        st.session_state.focus_duration = focus_minutes * 60
        
        break_minutes = st.slider("Break Duration (minutes)", 5, 30, 
                                  value=st.session_state.break_duration // 60, 
                                  key="break_slider")
        st.session_state.break_duration = break_minutes * 60
        
        if st.session_state.running:
            st.info("⏸️ Pause timer to apply new settings")
        
        st.divider()
        
        # Friends Section
        st.markdown("### 👥 Friends")
        
        # Add friend
        st.markdown("#### Add Friend")
        all_users = get_all_users()
        if all_users:
            friend_username = st.selectbox("Select a user to add", 
                                          [u["username"] for u in all_users],
                                          key="friend_select")
            if st.button("➕ Add Friend", use_container_width=True):
                if friend_username not in st.session_state.friends:
                    st.session_state.friends.append(friend_username)
                    st.success(f"✅ Added {friend_username} as friend!")
                    st.rerun()
        
        # Friend list
        if st.session_state.friends:
            st.markdown("#### Your Friends")
            for friend in st.session_state.friends:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"👤 {friend}")
                with col2:
                    if st.button("💬", key=f"chat_{friend}"):
                        st.session_state.current_chat = friend
                        st.rerun()
    
    # Main content area
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown('<div class="main-header">🍅 Pomodoro Timer</div>', unsafe_allow_html=True)
        
        # Timer display
        remaining = get_remaining_time()
        mode_text = "Focus Time" if st.session_state.timer_mode == "focus" else "Break Time"
        mode_color = "#FF6B6B" if st.session_state.timer_mode == "focus" else "#4ECDC4"
        
        st.markdown(f"""
        <div class="timer-display" style="background: linear-gradient(135deg, {mode_color} 0%, {mode_color}dd 100%);">
            <div style="font-size: 1.5rem; margin-bottom: 1rem;">{mode_text}</div>
            <div>{format_time(remaining)}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Timer controls
        col_start, col_pause, col_reset = st.columns(3)
        
        with col_start:
            if not st.session_state.running:
                if st.button("▶️ Start", type="primary", use_container_width=True):
                    start_timer()
                    st.rerun()
            else:
                if st.button("⏸️ Pause", use_container_width=True):
                    pause_timer()
                    st.rerun()
        
        with col_reset:
            if st.button("🔁 Reset", use_container_width=True):
                reset_timer()
                st.rerun()
        
        # Timer logic
        if st.session_state.running:
            if remaining <= 0:
                timer_complete()
            else:
                time.sleep(0.1)
                st.rerun()
    
    with col2:
        st.markdown("### 💬 Chat")
        
        # Chat selector
        if st.session_state.friends:
            chat_partner = st.selectbox("Chat with:", 
                                       ["General Chat"] + st.session_state.friends,
                                       key="chat_partner")
            if chat_partner != "General Chat":
                st.session_state.current_chat = chat_partner
        else:
            st.info("👥 Add friends to start chatting!")
            chat_partner = "General Chat"
        
        # Chat messages display
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        
        chat_key = st.session_state.current_chat if st.session_state.current_chat else "general"
        if chat_key not in st.session_state.messages:
            st.session_state.messages[chat_key] = []
        
        messages = st.session_state.messages.get(chat_key, [])
        
        for msg in messages:
            is_own = msg.get("sender") == st.session_state.username
            msg_class = "own" if is_own else "other"
            sender_name = "You" if is_own else msg.get("sender", "Unknown")
            
            st.markdown(f"""
            <div class="chat-message {msg_class}">
                <strong>{sender_name}</strong> ({msg.get("time", "")})<br>
                {msg.get("text", "")}
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Chat input with form for better control
        with st.form("chat_form", clear_on_submit=True):
            chat_input = st.text_input("Type a message...", key="chat_input")
            send_button = st.form_submit_button("Send 💬", type="primary", use_container_width=True)
            
            if send_button and chat_input.strip():
                new_message = {
                    "sender": st.session_state.username,
                    "text": chat_input.strip(),
                    "time": datetime.now().strftime("%H:%M"),
                    "timestamp": time.time()
                }
                if chat_key not in st.session_state.messages:
                    st.session_state.messages[chat_key] = []
                st.session_state.messages[chat_key].append(new_message)
                st.rerun()

# App routing
if not st.session_state.authenticated:
    login_page()
else:
    main_app()
