"""
Streamlit Frontend for AI Study Assistant.
Main application entry point
"""
import streamlit as st
import requests
from typing import Optional
import os

# Page configuration
st.set_page_config(
    page_title="AI Study Assistant",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


def check_api_health() -> bool:
    """Check if the API is running."""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False


def main():
    """Main application."""
    
    # Sidebar
    with st.sidebar:
        st.title("📚 AI Study Assistant")
        st.markdown("---")
        
        # Navigation
        page = st.radio(
            "Navigate to:",
            ["🏠 Home", "📄 Documents", "💬 Chat", "📝 Quiz", "📊 Progress"],
            index=0
        )
        
        st.markdown("---")
        
        # API Status
        api_healthy = check_api_health()
        if api_healthy:
            st.success("✅ API Connected")
        else:
            st.error("❌ API Offline")
            st.info("Start the API server:\n```\nuvicorn main:app --reload\n```")
    
    # Main content based on navigation
    if "Home" in page:
        show_home()
    elif "Documents" in page:
        show_documents()
    elif "Chat" in page:
        show_chat()
    elif "Quiz" in page:
        show_quiz()
    elif "Progress" in page:
        show_progress()


def show_home():
    """Display home page."""
    st.title("🎓 AI Study Assistant")
    st.markdown("""
    Welcome to your AI-powered study companion! This application helps you:
    
    - **📄 Upload** your study materials (PDFs, notes, textbooks)
    - **💬 Ask questions** and get answers from your documents
    - **📝 Generate quizzes** to test your knowledge
    - **📊 Track progress** and identify weak areas
    """)
    
    st.markdown("---")
    
    # Quick stats
    col1, col2, col3, col4 = st.columns(4)
    
    try:
        # Get stats from API
        docs_response = requests.get(f"{API_BASE_URL}/documents/list")
        progress_response = requests.get(f"{API_BASE_URL}/progress/stats")
        
        if docs_response.status_code == 200:
            docs_data = docs_response.json()
            col1.metric("📄 Documents", docs_data.get("total_count", 0))
        
        if progress_response.status_code == 200:
            progress_data = progress_response.json()
            col2.metric("❓ Questions Asked", progress_data.get("total_questions_asked", 0))
            col3.metric("📝 Quizzes Taken", progress_data.get("total_quizzes_taken", 0))
            col4.metric("📈 Avg Quiz Score", f"{progress_data.get('average_quiz_score', 0):.1f}%")
    except:
        col1.metric("📄 Documents", "—")
        col2.metric("❓ Questions Asked", "—")
        col3.metric("📝 Quizzes Taken", "—")
        col4.metric("📈 Avg Quiz Score", "—")
    
    st.markdown("---")
    
    # Getting started
    st.subheader("🚀 Getting Started")
    st.markdown("""
    1. **Upload your study materials** - Go to Documents and upload PDFs or text files
    2. **Start asking questions** - Use the Chat to ask about any topic
    3. **Test yourself** - Generate quizzes on topics you're studying
    4. **Review your progress** - Check the Progress page to see your learning journey
    """)


def show_documents():
    """Display documents page."""
    st.title("📄 Document Management")
    
    # Upload section
    st.subheader("Upload New Document")
    uploaded_file = st.file_uploader(
        "Choose a file to upload",
        type=["pdf", "txt", "md"],
        help="Supported formats: PDF, TXT, Markdown"
    )
    
    if uploaded_file is not None:
        if st.button("📤 Upload and Process", type="primary"):
            with st.spinner("Processing document..."):
                try:
                    files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
                    response = requests.post(f"{API_BASE_URL}/documents/upload", files=files)
                    
                    if response.status_code == 200:
                        data = response.json()
                        st.success(f"✅ {data['message']}")
                        st.info(f"Created {data['document']['chunk_count']} chunks for indexing")
                    else:
                        st.error(f"❌ Error: {response.json().get('detail', 'Unknown error')}")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    
    st.markdown("---")
    
    # Document list
    st.subheader("Uploaded Documents")
    
    try:
        response = requests.get(f"{API_BASE_URL}/documents/list")
        if response.status_code == 200:
            data = response.json()
            
            if data["total_count"] == 0:
                st.info("No documents uploaded yet. Upload your first document above!")
            else:
                for doc in data["documents"]:
                    with st.expander(f"📄 {doc['filename']}"):
                        col1, col2, col3 = st.columns(3)
                        col1.write(f"**Type:** {doc['file_type']}")
                        col2.write(f"**Chunks:** {doc['chunk_count']}")
                        col3.write(f"**Status:** {doc['status']}")
                        
                        if st.button("🗑️ Delete", key=f"del_{doc['id']}"):
                            del_response = requests.delete(f"{API_BASE_URL}/documents/{doc['id']}")
                            if del_response.status_code == 200:
                                st.success("Document deleted!")
                                st.rerun()
    except Exception as e:
        st.error(f"Error loading documents: {str(e)}")
    
    st.markdown("---")
    
    # Reset option
    with st.expander("⚠️ Danger Zone"):
        st.warning("This will delete all documents and reset the index!")
        if st.button("🗑️ Reset All Documents", type="secondary"):
            try:
                response = requests.post(f"{API_BASE_URL}/documents/reset")
                if response.status_code == 200:
                    st.success("All documents reset!")
                    st.rerun()
            except Exception as e:
                st.error(f"Error: {str(e)}")


def show_chat():
    """Display chat page."""
    st.title("💬 Chat with Your Study Materials")
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "sources" in message:
                with st.expander("📚 Sources"):
                    for source in message["sources"]:
                        st.markdown(f"**{source['source']}**")
                        st.markdown(f"_{source['content']}_")
    
    # Chat input
    if prompt := st.chat_input("Ask a question about your study materials..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = requests.post(
                        f"{API_BASE_URL}/chat/ask",
                        json={
                            "question": prompt,
                            "include_sources": True,
                            "num_results": 5
                        }
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        st.markdown(data["answer"])
                        
                        # Show sources
                        if data.get("sources"):
                            with st.expander("📚 Sources"):
                                for source in data["sources"]:
                                    st.markdown(f"**{source['source']}**")
                                    st.markdown(f"_{source['content']}_")
                        
                        # Save to history
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": data["answer"],
                            "sources": data.get("sources", [])
                        })
                    else:
                        st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    # Sidebar options
    with st.sidebar:
        st.subheader("Chat Options")
        if st.button("🗑️ Clear Chat History"):
            st.session_state.messages = []
            st.rerun()


def show_quiz():
    """Display quiz page."""
    st.title("📝 Practice Quiz")
    
    # Quiz generation
    st.subheader("Generate a New Quiz")
    
    col1, col2 = st.columns(2)
    with col1:
        topic = st.text_input("Topic", placeholder="e.g., Machine Learning Basics")
    with col2:
        num_questions = st.slider("Number of Questions", 3, 15, 5)
    
    question_type = st.selectbox(
        "Question Type",
        ["mixed", "mcq", "short_answer"],
        format_func=lambda x: {"mixed": "Mixed", "mcq": "Multiple Choice", "short_answer": "Short Answer"}[x]
    )
    
    if st.button("🎲 Generate Quiz", type="primary"):
        if not topic:
            st.warning("Please enter a topic!")
        else:
            with st.spinner("Generating quiz..."):
                try:
                    response = requests.post(
                        f"{API_BASE_URL}/quiz/generate",
                        json={
                            "topic": topic,
                            "num_questions": num_questions,
                            "question_type": question_type
                        }
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data["success"]:
                            st.session_state.current_quiz = data
                            st.session_state.quiz_answers = {}
                            st.success(f"✅ Generated {len(data['questions'])} questions!")
                        else:
                            st.error(data.get("error", "Failed to generate quiz"))
                    else:
                        st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    st.markdown("---")
    
    # Display current quiz
    if "current_quiz" in st.session_state and st.session_state.current_quiz:
        quiz = st.session_state.current_quiz
        st.subheader(f"Quiz: {quiz['topic']}")
        
        # Initialize answers dict if needed
        if "quiz_answers" not in st.session_state:
            st.session_state.quiz_answers = {}
        
        # Display questions
        for i, q in enumerate(quiz["questions"]):
            st.markdown(f"### Question {i+1}")
            st.markdown(f"**{q['question']}**")
            st.caption(f"Difficulty: {q['difficulty']}")
            
            if q["type"] == "mcq" and q.get("options"):
                answer = st.radio(
                    "Your answer:",
                    q["options"],
                    key=f"q_{q['id']}",
                    index=None
                )
                if answer:
                    st.session_state.quiz_answers[q['id']] = answer
            else:
                answer = st.text_input(
                    "Your answer:",
                    key=f"q_{q['id']}"
                )
                if answer:
                    st.session_state.quiz_answers[q['id']] = answer
            
            st.markdown("---")
        
        # Submit button
        if st.button("📨 Submit Quiz", type="primary"):
            if len(st.session_state.quiz_answers) < len(quiz["questions"]):
                st.warning("Please answer all questions before submitting!")
            else:
                # Calculate results locally since we have the answers
                correct = 0
                results = []
                
                for q in quiz["questions"]:
                    user_answer = st.session_state.quiz_answers.get(q['id'], "")
                    is_correct = user_answer.strip().lower() == q['correct_answer'].strip().lower()
                    if is_correct:
                        correct += 1
                    results.append({
                        "question": q['question'],
                        "user_answer": user_answer,
                        "correct_answer": q['correct_answer'],
                        "is_correct": is_correct,
                        "explanation": q['explanation']
                    })
                
                total = len(quiz["questions"])
                score = (correct / total) * 100
                
                st.session_state.quiz_results = {
                    "correct": correct,
                    "total": total,
                    "score": score,
                    "results": results
                }
                
                # Display results
                st.subheader("📊 Quiz Results")
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Score", f"{score:.1f}%")
                col2.metric("Correct", correct)
                col3.metric("Total", total)
                
                if score >= 80:
                    st.success("🎉 Excellent work!")
                elif score >= 60:
                    st.info("👍 Good job! Keep practicing!")
                else:
                    st.warning("📚 Review this topic and try again!")
                
                # Show detailed results
                for i, result in enumerate(results, 1):
                    if result["is_correct"]:
                        st.success(f"**Q{i}:** ✅ Correct!")
                    else:
                        st.error(f"**Q{i}:** ❌ Incorrect")
                        st.markdown(f"Your answer: {result['user_answer']}")
                        st.markdown(f"Correct answer: **{result['correct_answer']}**")
                    st.markdown(f"*Explanation: {result['explanation']}*")
                    st.markdown("---")
                
                # Clear quiz
                if st.button("🔄 Start New Quiz"):
                    st.session_state.current_quiz = None
                    st.session_state.quiz_answers = {}
                    st.session_state.quiz_results = None
                    st.rerun()


def show_progress():
    """Display progress page."""
    st.title("📊 Learning Progress")
    
    try:
        response = requests.get(f"{API_BASE_URL}/progress/stats")
        
        if response.status_code == 200:
            stats = response.json()
            
            # Overview metrics
            st.subheader("📈 Overview")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Questions Asked", stats["total_questions_asked"])
            col2.metric("Quizzes Taken", stats["total_quizzes_taken"])
            col3.metric("Avg Quiz Score", f"{stats['average_quiz_score']:.1f}%")
            col4.metric("Topics Studied", len(stats["topics_studied"]))
            
            st.markdown("---")
            
            # Weak and strong areas
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("⚠️ Areas to Improve")
                if stats["weak_areas"]:
                    for area in stats["weak_areas"]:
                        st.warning(f"**{area['topic']}** - Avg: {area['average_score']:.1f}%")
                else:
                    st.info("No weak areas identified yet. Take more quizzes!")
            
            with col2:
                st.subheader("🌟 Strong Areas")
                if stats["strong_areas"]:
                    for area in stats["strong_areas"]:
                        st.success(f"**{area['topic']}** - Avg: {area['average_score']:.1f}%")
                else:
                    st.info("Keep studying to identify your strengths!")
            
            st.markdown("---")
            
            # Topics studied
            st.subheader("📚 Topics Studied")
            if stats["topics_studied"]:
                for topic in stats["topics_studied"]:
                    st.markdown(f"- {topic}")
            else:
                st.info("Start asking questions or taking quizzes to track topics!")
            
            st.markdown("---")
            
            # Recent activity
            st.subheader("🕐 Recent Activity")
            
            recent = stats.get("recent_activity", {})
            
            if recent.get("recent_quizzes"):
                st.markdown("**Recent Quizzes:**")
                for quiz in recent["recent_quizzes"][:5]:
                    st.markdown(
                        f"- {quiz['topic']}: {quiz['score_percentage']:.1f}% "
                        f"({quiz['correct_answers']}/{quiz['total_questions']})"
                    )
            
            if recent.get("recent_questions"):
                st.markdown("**Recent Questions:**")
                for q in recent["recent_questions"][:5]:
                    st.markdown(f"- {q['question'][:100]}...")
            
        else:
            st.error("Error loading progress data")
            
    except Exception as e:
        st.error(f"Error: {str(e)}")
    
    st.markdown("---")
    
    # Recommendations
    st.subheader("💡 Study Recommendations")
    try:
        rec_response = requests.get(f"{API_BASE_URL}/progress/recommendations")
        if rec_response.status_code == 200:
            rec_data = rec_response.json()
            for rec in rec_data.get("recommendations", []):
                if rec["type"] == "focus_area":
                    st.warning(f"**{rec['topic']}**: {rec['reason']}. {rec['action']}")
                elif rec["type"] == "strength":
                    st.success(f"**{rec['topic']}**: {rec['reason']}. {rec['action']}")
                else:
                    st.info(f"**{rec['topic']}**: {rec['reason']}. {rec['action']}")
    except:
        pass
    
    # Reset option
    with st.expander("⚠️ Reset Progress"):
        st.warning("This will delete all your progress data!")
        if st.button("🗑️ Reset Progress", type="secondary"):
            try:
                response = requests.post(f"{API_BASE_URL}/progress/reset")
                if response.status_code == 200:
                    st.success("Progress reset!")
                    st.rerun()
            except Exception as e:
                st.error(f"Error: {str(e)}")


if __name__ == "__main__":
    main()
