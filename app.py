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


# INIT SESSION

if "messages" not in st.session_state:
    st.session_state.messages = []

if "current_field" not in st.session_state:
    st.session_state.current_field = 0

if "candidate_data" not in st.session_state:
    st.session_state.candidate_data = {}

if "finished" not in st.session_state:
    st.session_state.finished = False


# UI HEADER

st.title("TalentScout Hiring Assistant")
st.markdown("AI-powered candidate screening chatbot")


# DISPLAY CHAT

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])


# FIRST MESSAGE

if len(st.session_state.messages) == 0:
    greeting = "Hello Welcome to TalentScout! Let's start your screening process.\n\nWhat is your Full Name?"
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


    # DATA COLLECTION

    if not st.session_state.finished:

        field = FIELDS[st.session_state.current_field]

        # Validation
        valid = True
        error_msg = ""

        if field == "Email" and not validate_email(user_input):
            valid = False
            error_msg = "Invalid email. Please enter a valid email."

        elif field == "Phone" and not validate_phone(user_input):
            valid = False
            error_msg = "Enter a valid 10-digit phone number."

        elif field == "Years of Experience" and not validate_experience(user_input):
            valid = False
            error_msg = "Enter a valid number."

        if not valid:
            # Use fallback LLM to explain or redirect
            with open("prompts/fallback_prompt.txt") as f:
                fallback_template = f.read()
            
            fallback_prompt = fallback_template.format(input=user_input, stage=field)
            ai_fallback = call_llm(fallback_prompt)
            
            st.session_state.messages.append({"role": "assistant", "content": f"{error_msg}\n\n{ai_fallback}"})
            st.rerun()

        # Save data
        st.session_state.candidate_data[field] = user_input
        st.session_state.current_field += 1

        # Ask next question
        if st.session_state.current_field < len(FIELDS):
            next_q = f"Please enter your {FIELDS[st.session_state.current_field]}:"
            st.session_state.messages.append({"role": "assistant", "content": next_q})
            st.rerun()


        # GENERATE TECH QUESTIONS

        else:
            tech_stack = st.session_state.candidate_data["Tech Stack"]

            with open("prompts/tech_prompt.txt") as f:
                prompt_template = f.read()

            prompt = prompt_template.format(tech_stack=tech_stack)

            questions = call_llm(prompt)

            st.session_state.messages.append({
                "role": "assistant",
                "content": "Great! Here are your technical questions:\n\n" + questions
            })

            # Save data
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
                "content": "Thank you! Our team will review your responses and get back to you."
            })

            st.rerun()