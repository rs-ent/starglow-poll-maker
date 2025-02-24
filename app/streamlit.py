##### starglow-poll-maker\app\streamlit.py #####

from quest import load_data, select_two_groups, build_prompt, generate_poll_title, generate_poll_options
import streamlit as st

# Streamlit 앱 설정
st.title("Poll Maker - Starglow")

if st.button("Create Quest"):
    df = load_data("groups_data_updated.csv")
    group_A, group_B = select_two_groups(df)
    prompt = build_prompt(group_A, group_B)
    
    st.subheader("Generated Prompt")
    st.code(prompt, language="python")
    
    poll_title = generate_poll_title(prompt)
    st.subheader("Generated Poll Title")
    st.write(poll_title)
    
    poll_options = generate_poll_options(group_A, group_B)
    st.subheader("Generated Poll Options")
    st.write(poll_options)