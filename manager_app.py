import streamlit as st
import json

st.set_page_config(page_title="Hiring Manager Dashboard", layout="wide")

st.title("💼 Hiring Manager Dashboard")
st.markdown("Review candidate applications and iterative technical interview responses.")

# Load Data
try:
    with open("data/candidates.json", "r") as f:
        candidates = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    candidates = []

if not candidates:
    st.info("No candidate applications found yet.")
else:
    # Sidebar for navigation
    st.sidebar.header("Candidates")
    candidate_names = [f"{c.get('Full Name', 'N/A')} ({c.get('Email', 'N/A')})" for c in candidates]
    selected_idx = st.sidebar.selectbox("Select a candidate to review", range(len(candidate_names)), format_func=lambda x: candidate_names[x])

    if selected_idx is not None:
        candidate = candidates[selected_idx]
        
        # Display Candidate Header
        st.header(f"Candidate: {candidate.get('Full Name')}")
        
        # Split into columns for basic info
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Contact Information")
            st.write(f"**Email:** {candidate.get('Email')}")
            st.write(f"**Phone:** {candidate.get('Phone')}")
            st.write(f"**Location:** {candidate.get('Current Location')}")
            
        with col2:
            st.subheader("Professional Details")
            st.write(f"**Position:** {candidate.get('Desired Position')}")
            st.write(f"**Experience:** {candidate.get('Years of Experience')} years")
            st.write(f"**Tech Stack:** {candidate.get('Tech Stack')}")

        st.divider()

        # Interview Section
        st.subheader("Technical Interview Transcript")
        
        transcript = candidate.get("Transcript", [])
        
        if not transcript:
            # Fallback for old data format
            st.warning("This candidate has an older data format.")
            q_col, a_col = st.columns(2)
            with q_col:
                st.info("**Questions:**")
                st.write(candidate.get("Questions", "N/A"))
            with a_col:
                st.success("**Answers:**")
                st.write(candidate.get("Answers", "N/A"))
        else:
            # Display iterative transcript
            for i, entry in enumerate(transcript):
                with st.expander(f"Q{i+1}: {entry['tech'].upper()}", expanded=True):
                    st.markdown(f"**Question:**\n{entry['q']}")
                    st.success(f"**Candidate Answer:**\n{entry['a']}")

    # Summary Table at the bottom
    st.divider()
    st.subheader("Overview Table")
    table_data = []
    for c in candidates:
        table_data.append({
            "Name": c.get("Full Name"),
            "Email": c.get("Email"),
            "Experience": c.get("Years of Experience"),
            "Position": c.get("Desired Position"),
            "Tech Stack": c.get("Tech Stack")
        })
    st.table(table_data)
