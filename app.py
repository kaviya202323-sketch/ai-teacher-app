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
            if 'chat_history' in st.session_state:
                st.session_state['chat_history'] = []
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
        
        # --- TOP METRICS ---
        col1, col2, col3 = st.columns(3)
        
        if not df.empty:
            top_topic = df['topic'].mode()[0]
            total_q = len(df)
            last_active = pd.to_datetime(df['timestamp']).max()
            if not isinstance(last_active, str): 
                last_active = last_active.strftime("%H:%M")
        else:
            top_topic = "None"
            total_q = 0
            last_active = "--:--"

        with col1: st.metric("Total Questions", total_q)
        with col2: st.metric("Primary Learning Gap", top_topic)
        with col3: st.metric("Last Activity", last_active)

        st.markdown("---")

        # --- RECOMMENDATIONS ---
        if not df.empty:
            recommendations = {
                "Computing": "🔴 **Critical Gap:** Students struggling with Coding. **Action:** Schedule live coding.",
                "Humanities": "🟠 **Moderate Gap:** Confusion on History/Dates. **Action:** Upload timeline chart.",
                "Science": "🔵 **Science Gap:** Concepts in Physics/Chem are unclear. **Action:** Show a lab demonstration.",
                "Education": "🟢 **Admin Gap:** Exam queries. **Action:** Clarify grading rubric."
            }
            advice = recommendations.get(top_topic, "⚪ Monitoring: No specific trend yet.")
            st.success(f"💡 **AI Recommendation:** {advice}")

        # --- CHARTS ---
        if not df.empty:
            col_chart1, col_chart2 = st.columns(2)
            with col_chart1:
                st.subheader("📊 Gap Analysis")
                st.bar_chart(df['topic'].value_counts(), color="#4A90E2")
            with col_chart2:
                st.subheader("📈 Activity Trend")
                st.line_chart(df['topic'].value_counts(), color="#FF4B4B")

            # --- TABLE WITH FILTERS & PAGINATION ---
            st.subheader("📝 Question Log")
            
            # 1. Filter
            all_topics = ["All Topics"] + list(df['topic'].unique())
            selected_filter = st.selectbox("🔍 Filter by Subject:", all_topics)
            
            if selected_filter == "All Topics":
                filtered_df = df
            else:
                filtered_df = df[df['topic'] == selected_filter]

            # 2. Urgency Flag
            def flag_urgency(text):
                urgent_words = ["urgent", "exam", "confused", "hard", "fail", "help"]
                if any(w in text.lower() for w in urgent_words):
                    return "🔴 URGENT"
                return ""
            
            display_df = filtered_df.copy()
            display_df['status'] = display_df['query'].apply(flag_urgency)

            # 3. Pagination (5 rows for v4)
            rows_per_page = 5
            if 'page_number' not in st.session_state: st.session_state.page_number = 0
            
            total_pages = max(1, (len(display_df) // rows_per_page) + 1)
            # Reset if filter changes reduces pages
            if st.session_state.page_number >= total_pages: st.session_state.page_number = 0
            
            start_idx = st.session_state.page_number * rows_per_page
            end_idx = start_idx + rows_per_page
            
            # Reverse for newest first
            final_view = display_df.iloc[::-1].iloc[start_idx:end_idx]

            st.dataframe(
                final_view[['timestamp', 'status', 'topic', 'query']], 
                use_container_width=True,
                column_config={"status": st.column_config.TextColumn("Status")}
            )

            # Pagination Controls
            c_prev, c_txt, c_next = st.columns([1, 2, 1])
            with c_prev:
                if st.button("⬅️ Previous"):
                    if st.session_state.page_number > 0:
                        st.session_state.page_number -= 1
                        st.rerun()
            with c_next:
                if end_idx < len(display_df):
                    if st.button("Next ➡️"):
                        st.session_state.page_number += 1
                        st.rerun()
            with c_txt:
                st.write(f"Page {st.session_state.page_number + 1} of {total_pages}")
                
            # Download
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Report", csv, "data.csv", "text/csv")
        else:
            st.info("No data available yet. Go to Student View to start.")
