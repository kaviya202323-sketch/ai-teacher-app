import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# --- CONFIGURATION & STYLING ---
st.set_page_config(page_title="AI Co-Teacher Pro", page_icon="🎓", layout="wide")

# Custom CSS for styling
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #4A90E2;
        text-align: center;
        font-weight: bold;
        margin-bottom: 20px;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #4A90E2;
    }
    </style>
""", unsafe_allow_html=True)

# --- DATABASE FUNCTIONS ---
def init_db():
    conn = sqlite3.connect('classroom_data.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            topic TEXT,
            query TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_interaction(topic, query):
    conn = sqlite3.connect('classroom_data.db')
    c = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute('INSERT INTO interactions (timestamp, topic, query) VALUES (?, ?, ?)', 
              (timestamp, topic, query))
    conn.commit()
    conn.close()

def load_data():
    conn = sqlite3.connect('classroom_data.db')
    df = pd.read_sql_query("SELECT * FROM interactions", conn)
    conn.close()
    return df

# Initialize DB
init_db()

# --- AI LOGIC ---
def get_ai_response(user_query):
    user_query = user_query.lower()
    
    # Topic Detection
    topic = "General"
    if any(word in user_query for word in ["variable", "python", "code", "function", "loop"]):
        topic = "Computing"
    elif any(word in user_query for word in ["history", "war", "date", "king", "empire"]):
        topic = "Humanities"
    elif any(word in user_query for word in ["teach", "class", "exam", "grade"]):
        topic = "Education"
        
    answer = f"**[AI Co-Teacher]**: I see you're asking about **{topic}**. Here is a clear explanation for '{user_query}'...\n\n*(Saved to Faculty Database)*"
    return answer, topic

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3426/3426653.png", width=100)
    st.title("University AI Portal")
    role = st.radio("Select Dashboard:", ["Student View", "Faculty View"])
    st.markdown("---")
    st.caption("v1.3 Secure Edition | Database Active")

# --- STUDENT PAGE ---
if role == "Student View":
    st.markdown('<div class="main-header">🎓 Student Learning Hub</div>', unsafe_allow_html=True)
    st.write("Welcome! Ask your questions below. Your professor will use this data to improve classes.")
    
    if 'chat_history' not in st.session_state:
        st.session_state['chat_history'] = []

    for msg in st.session_state['chat_history']:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("I have a doubt about..."):
        st.session_state['chat_history'].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            response, topic = get_ai_response(prompt)
            st.markdown(response)
            save_interaction(topic, prompt)
            
        st.session_state['chat_history'].append({"role": "assistant", "content": response})

# --- FACULTY PAGE (SECURE) ---
elif role == "Faculty View":
    st.markdown('<div class="main-header">👨‍🏫 Faculty Insights Dashboard</div>', unsafe_allow_html=True)
    
    # --- PASSWORD PROTECTION ---
    password = st.text_input("Enter Faculty Password to Access:", type="password")
    
    if password != "1234":
        st.info("🔒 **Access Restricted**: Only authorized faculty members can view this dashboard.")
        st.stop()  # STOPS the code here if password is wrong
        
    # --- IF PASSWORD IS CORRECT, SHOW DASHBOARD ---
    df = load_data()
    
    if df.empty:
        st.info("👋 No data yet. Switch to Student View and ask questions.")
    else:
        # Metrics
        col1, col2, col3 = st.columns(3)
        top_topic = df['topic'].mode()[0]
        
        with col1:
            st.metric("Total Questions", len(df))
        with col2:
            st.metric("Primary Learning Gap", top_topic)
        with col3:
            recent_time = pd.to_datetime(df['timestamp']).max()
            st.metric("Last Activity", recent_time.strftime("%H:%M"))

        st.markdown("---")

        # Recommendation
        recommendations = {
            "Computing": "🔴 **Critical Gap:** Students struggling with Python Syntax. **Action:** Schedule live coding.",
            "Humanities": "🟠 **Moderate Gap:** Confusion on Timelines. **Action:** Upload timeline chart.",
            "Education": "🟢 **Admin Gap:** Exam queries. **Action:** Clarify grading rubric.",
            "General": "⚪ **Monitoring:** No specific trend."
        }
        advice = recommendations.get(top_topic, "Review recent questions.")
        st.success(f"💡 **AI Recommendation:** {advice}")

        # Charts
        col_left, col_right = st.columns([2, 1])
        with col_left:
            st.subheader("📊 Gap Analysis")
            st.bar_chart(df['topic'].value_counts(), color="#4A90E2")
        with col_right:
            st.subheader("📝 Recent Log")
            st.dataframe(df[['topic', 'query']].tail(5), hide_index=True)