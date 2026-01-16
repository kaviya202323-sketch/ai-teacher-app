import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# --- CONFIGURATION & STYLING ---
st.set_page_config(page_title="AI Co-Teacher Pro", page_icon="🎓", layout="wide")

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

def clear_data():
    conn = sqlite3.connect('classroom_data.db')
    c = conn.cursor()
    c.execute('DELETE FROM interactions')
    conn.commit()
    conn.close()

init_db()

# --- AI LOGIC ---
def get_ai_response(user_query):
    user_query = user_query.lower()
    
    keywords = {
        "Computing": ["variable", "python", "code", "function", "loop", "algorithm", "data", "ai", "robot", "print", "list", "bug", "schrodinger", "qubit"],
        "Humanities": ["history", "war", "date", "king", "empire", "napoleon", "british", "rule", "india", "freedom", "gandhi", "1947", "world"],
        "Science": ["carbon", "properties", "physics", "chemistry", "biology", "cell", "atom", "force", "energy", "fourier", "transform", "math", "equation", "quantum", "superposition"],
        "Education": ["teach", "class", "exam", "grade", "syllabus", "attendance", "mark"]
    }

    topic = "General"
    for category, words in keywords.items():
        if any(word in user_query for word in words):
            topic = category
            break
        
    answer = f"**[AI Co-Teacher]**: I see you're asking about **{topic}**. Here is a clear explanation for '{user_query}'...\n\n*(Saved to Faculty Database)*"
    return answer, topic

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3426/3426653.png", width=100) 
    st.title("Rajalakshmi AI Portal")
    role = st.radio("Select Dashboard:", ["Student View", "Faculty View"])
    st.markdown("---")
    
    if role == "Faculty View":
        st.error("⚠️ Danger Zone")
        if st.button("🗑️ Reset All Data"):
            clear_data()
            st.success("Database Cleared!")
            st.rerun()
            
    st.caption("v4.0 Master Edition")

# --- STUDENT PAGE ---
if role == "Student View":
    st.markdown('<div class="main-header">🎓 Student Learning Hub</div>', unsafe_allow_html=True)
    
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

# --- FACULTY PAGE ---
elif role == "Faculty View":
    st.markdown('<div class="main-header">👨‍🏫 Faculty Insights Dashboard</div>', unsafe_allow_html=True)
    
    password = st.text_input("Enter Faculty Password:", type="password")
    
    if password == "1234":
        df = load_data()
        
        if df.empty:
            st.info("👋 No data yet. The database is clean. Go to Student View to start.")
        else:
            # 1. Metrics
            col1, col2, col3 = st.columns(3)
            top_topic = df['topic'].mode()[0]
            with col1: st.metric("Total Questions", len(df))
            with col2: st.metric("Primary Learning Gap", top_topic)
            last_active = pd.to_datetime(df['timestamp']).max().strftime("%H:%M")
            with col3: st.metric("Last Activity", last_active)

            st.markdown("---")

            # 2. Recommendations
            recommendations = {
                "Computing": "🔴 **Critical Gap:** Students struggling with Coding. **Action:** Schedule live coding.",
                "Humanities": "🟠 **Moderate Gap:** Confusion on History/Dates. **Action:** Upload timeline chart.",
                "Science": "🔵 **Science Gap:** Concepts in Physics/Chem are unclear. **Action:** Show a lab demonstration.",
                "Education": "🟢 **Admin Gap:** Exam queries. **Action:** Clarify grading rubric."
            }
            advice = recommendations.get(top_topic, "⚪ Monitoring: No specific trend yet.")
            st.success(f"💡 **AI Recommendation:** {advice}")

            # 3. Charts Area
            col_left, col_right = st.columns(2)
            with col_left:
                st.subheader("📊 Gap Analysis")
                st.bar_chart(df['topic'].value_counts(), color="#4A90E2")
            with col_right:
                st.subheader("📈 Activity Trend")
                st.line_chart(df['topic'].value_counts(), color="#FF4B4B")

            # --- NEW FEATURE: FILTER & URGENCY ---
            st.subheader("📝 Question Log")
            
            # A. Topic Filter
            topic_options = ["All Topics"] + list(df['topic'].unique())
            selected_topic = st.selectbox("🔍 Filter by Subject:", topic_options)
            
            # Filter Logic
            filtered_df = df if selected_topic == "All Topics" else df[df['topic'] == selected_topic]

            # B. Urgency Logic (Add a visual flag)
            def flag_urgency(text):
                urgent_words = ["urgent", "exam", "confused", "hard", "help", "don't understand", "loss"]
                if any(w in text.lower() for w in urgent_words):
                    return "🔴 URGENT"
                return ""

            # Apply flag to a new column for display
            display_df = filtered_df.copy()
            display_df['status'] = display_df['query'].apply(flag_urgency)

            # Pagination Logic on the FILTERED data
            rows_per_page = 5
            if 'page_number' not in st.session_state:
                st.session_state.page_number = 0

            # Calculate pages based on filtered length
            total_pages = max(1, (len(display_df) // rows_per_page) + 1)
            
            # Ensure page number is valid (e.g., if you filter and have fewer results)
            if st.session_state.page_number >= total_pages:
                st.session_state.page_number = 0

            start_idx = st.session_state.page_number * rows_per_page
            end_idx = start_idx + rows_per_page
            
            # Show Table (Reverse to see new first)
            final_view = display_df.iloc[::-1].iloc[start_idx:end_idx]
            
            # Show Status, Topic, Query, Timestamp
            st.dataframe(
                final_view[['status', 'topic', 'query', 'timestamp']], 
                use_container_width=True,
                column_config={
                    "status": st.column_config.TextColumn("Status", help="Red flags indicate student confusion"),
                }
            )

            # Pagination Controls
            col_prev, col_page, col_next = st.columns([1, 2, 1])
            with col_prev:
                if st.button("⬅️ Previous"):
                    if st.session_state.page_number > 0:
                        st.session_state.page_number -= 1
                        st.rerun()
            with col_next:
                if end_idx < len(display_df):
                    if st.button("Next ➡️"):
                        st.session_state.page_number += 1
                        st.rerun()
            with col_page:
                st.write(f"Page {st.session_state.page_number + 1} of {total_pages}")

            st.markdown("---")
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Full Report", csv, "classroom_data.csv", "text/csv")