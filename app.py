import streamlit as st
import json
from utils.llm import call_llm
from utils.validator import validate_email, validate_phone, validate_experience


# CONFIG

FIELDS = [
    "Full Name",
    "Email",
    "Phone",
    "Years of Experience",
    "Desired Position",
    "Current Location",
    "Tech Stack"
]

EXIT_WORDS = ["bye", "exit", "quit", "thanks"]
QUESTIONS_PER_TECH = 3  # Adjust this to change interview length


# INIT SESSION

if "messages" not in st.session_state:
    st.session_state.messages = []

if "current_field" not in st.session_state:
    st.session_state.current_field = 0

if "candidate_data" not in st.session_state:
    st.session_state.candidate_data = {}

if "finished" not in st.session_state:
    st.session_state.finished = False

# Technical Interview state
if "tech_list" not in st.session_state:
    st.session_state.tech_list = []
if "current_tech_idx" not in st.session_state:
    st.session_state.current_tech_idx = 0
if "tech_q_count" not in st.session_state:
    st.session_state.tech_q_count = 0
if "transcript" not in st.session_state:
    st.session_state.transcript = [] # List of {"tech": ..., "q": ..., "a": ...}
if "awaiting_answer" not in st.session_state:
    st.session_state.awaiting_answer = False


# UI HEADER

st.title("TalentScout Hiring Assistant")
st.markdown("AI-powered candidate screening chatbot")


# DISPLAY CHAT

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])


# FIRST MESSAGE

if len(st.session_state.messages) == 0:
    greeting = "Hello! Welcome to TalentScout! Let's start your screening process.\n\nWhat is your Full Name?"
    st.session_state.messages.append({"role": "assistant", "content": greeting})
    st.rerun()


# USER INPUT

user_input = st.chat_input("Type your answer...")

if user_input:

    # Exit condition
    if any(word in user_input.lower() for word in EXIT_WORDS):
        st.session_state.messages.append({"role": "assistant", "content": "Thank you! We'll contact you soon"})
        st.session_state.finished = True
        st.rerun()

    st.session_state.messages.append({"role": "user", "content": user_input})


    # DATA COLLECTION / TECH INTERVIEW

    if not st.session_state.finished:

        # 1. Technical Interview Stage (Active loop)
        if st.session_state.awaiting_answer:
            # Save the answer for the current question
            current_entry = st.session_state.transcript[-1]
            current_entry["a"] = user_input
            
            st.session_state.tech_q_count += 1
            st.session_state.awaiting_answer = False

            # Check if we should move to next tech or finish
            if st.session_state.tech_q_count >= QUESTIONS_PER_TECH:
                st.session_state.current_tech_idx += 1
                st.session_state.tech_q_count = 0

            # If no more tech left, finish
            if st.session_state.current_tech_idx >= len(st.session_state.tech_list):
                st.session_state.candidate_data["Transcript"] = st.session_state.transcript
                
                # Ensure data directory exists
                import os
                if not os.path.exists("data"):
                    os.makedirs("data")

                # Save final data
                try:
                    with open("data/candidates.json", "r") as f:
                        data = json.load(f)
                except:
                    data = []
                data.append(st.session_state.candidate_data)
                with open("data/candidates.json", "w") as f:
                    json.dump(data, f, indent=4)

                st.session_state.finished = True
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": "Excellent! Your answers have been recorded. Our team will review your responses and get back to you soon. Have a great day!"
                })
                st.rerun()
            # Still have questions to ask? We'll generate next below...

        # 2. Standard field collection stage
        if st.session_state.current_field < len(FIELDS):
            field = FIELDS[st.session_state.current_field]

            # Validation
            valid = True
            error_msg = ""
            if field == "Email" and not validate_email(user_input):
                valid = False
                error_msg = "Invalid email."
            elif field == "Phone" and not validate_phone(user_input):
                valid = False
                error_msg = "Enter a 10-digit number."
            elif field == "Years of Experience" and not validate_experience(user_input):
                valid = False
                error_msg = "Enter a valid number."

            if not valid:
                with open("prompts/fallback_prompt.txt") as f:
                    fallback_template = f.read()
                fallback_prompt = fallback_template.format(input=user_input, stage=field)
                ai_fallback = call_llm(fallback_prompt)
                st.session_state.messages.append({"role": "assistant", "content": f"{error_msg}\n\n{ai_fallback}"})
                st.rerun()

            # Save field data
            st.session_state.candidate_data[field] = user_input
            st.session_state.current_field += 1

            # Transition to next question or tech interview
            if st.session_state.current_field < len(FIELDS):
                next_q = f"Please enter your {FIELDS[st.session_state.current_field]}:"
                st.session_state.messages.append({"role": "assistant", "content": next_q})
                st.rerun()
            else:
                # Prepare Tech List for interview
                tech_stack = st.session_state.candidate_data["Tech Stack"]
                st.session_state.tech_list = [t.strip() for t in tech_stack.split(",") if t.strip()]
                st.session_state.current_tech_idx = 0
                st.session_state.tech_q_count = 0

        # 3. Generate Next Technical Question (Shared by initial entry and intermediate steps)
        if st.session_state.current_tech_idx < len(st.session_state.tech_list) and not st.session_state.awaiting_answer:
            current_tech = st.session_state.tech_list[st.session_state.current_tech_idx]
            
            # Prepare context for the prompt
            prev_qs = [t["q"] for t in st.session_state.transcript if t["tech"] == current_tech]
            
            with open("prompts/dynamic_tech_prompt.txt") as f:
                prompt_template = f.read()
            
            prompt = prompt_template.format(
                tech=current_tech,
                experience=st.session_state.candidate_data.get("Years of Experience", "0"),
                previous_questions=str(prev_qs)
            )

            with st.spinner(f"Generating a question for {current_tech}..."):
                question = call_llm(prompt)

            # Record question and move to wait state
            st.session_state.transcript.append({
                "tech": current_tech,
                "q": question,
                "a": ""
            })
            st.session_state.awaiting_answer = True
            
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"**Question for {current_tech}:**\n\n{question}"
            })
            st.rerun()
