"""
Created on Thu Dec 5 14:12:00 2024

@author: piotr.janczewski
"""

from datetime import datetime, timedelta
import pandas as pd
import streamlit as st
import json
import openai
from PIL import Image

# Load configuration from JSON file
with open("config.json", mode="r") as f:
    config = json.load(f)

client = openai.AzureOpenAI(
        azure_endpoint=config["AZURE_ENDPOINT"],
        api_key= config["AZURE_API_KEY"],
        api_version="2023-12-01-preview")

st.set_page_config(page_title="Lease App",
                   layout="wide",
                   initial_sidebar_state="expanded"
                   )

##############
# Functions
##############

# Function to generate feedback scenario using Language Model
def examine_contract(examined_file, prompt_feed):
    
    prompt = prompt_feed

    messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": examined_file}
            ]

    response= client.chat.completions.create(
            messages=messages,
            model="PiotrJ_feedback",
            temperature=0,
            seed=445566)
    
    outcome = response.choices[0].message.content

    return outcome

def main_page():

    output = ''

    # Display the images in the header next to each other

    # Load images
    accenture_logo = Image.open("images/accenture_logo.png")
    orange_logo = Image.open("images/orange_logo.png")

    # Resize images to the same size
    # accenture_logo = accenture_logo.resize((150, 150))
    # orange_logo = orange_logo.resize((150, 150))

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.image(accenture_logo, use_column_width=True)
    with col4:
        st.image(orange_logo, use_column_width=True)

    st.write('')
    st.markdown("<h1><b>Verify consistency of contract with IFRS 16</b></h1>", unsafe_allow_html=True)
        
    with st.form("Lease analysis", clear_on_submit=False):

        examined_prompt = "Lorem ipsum 1. Is the main file a lease contract?"

        LeaseTrue_prompt = "Lorem ipsum 2. This is a sample correct lease contract, use to determine if the main file is similar, a lease contract indeed."

        LeaseFalse_prompt = "Lorem ipsum 3. This is a sample incorrect lease contract, use to determine if the main file isn't a lease contract."
        
        # Add a file uploader widget
        examined_file = st.file_uploader("Upload Word/PDF file to verify for lease presence", type=["doc", "docx", "pdf"])

        with st.expander("Extra options"):
            col1, col2 = st.columns(2)
            with col1:
                LeaseTrue_file = st.file_uploader("[Optional] Upload a sample lease contract to augment the analysis ", type=["doc", "docx", "pdf"])
            with col2:
                LeaseFalse_file = st.file_uploader("[Optional] Upload a sample NON-lease contract to enhance analysis accuracy", type=["doc", "docx", "pdf"])

            examined_feed = st.text_area("Main part, edit if adequate", value = examined_prompt)
            LeaseTrue_feed = st.text_area("Sample lease contract part (optional), edit if adequate", value = LeaseTrue_prompt)
            LeaseFalse_feed = st.text_area("Sample non-lease contract part (optional), edit if adequate", value = LeaseFalse_prompt)
            st.write("")
            rigidness_val = st.slider("How rigorous you want the verification to be?: 1=Very liberal, 5=Very strict",
                                    min_value=1, max_value=5, value=3)
            st.write("")
                
        # Premilinary listing before final export
        
        outcome_display = st.checkbox("Display verification outcome", value = True)
        outcome_record = st.checkbox("Write the outcome to the database", value = True)
        
        produce = st.form_submit_button("Verify the document")

        if produce:
            
            prompt_feed = ''
            
            # Read feedback table from Excel file
            if examined_file is not None:
                # Read the file 
                    # Read file command
                prompt_feed = examined_feed

            # Read Clifton ranks from text file
            if LeaseTrue_file is not None:
                # Read the file 
                    # Read file command
                prompt_feed += LeaseTrue_feed

            # Read Clifton ranks from text file
            if LeaseFalse_file is not None:
                # Read the Excel file 
                    # Read file command
                prompt_feed += LeaseFalse_feed

            # Generate feedback scenario
            outcome = examine_contract(examined_file, prompt_feed)
            st.write("")
            st.write(outcome)
            st.write("")

        # Save feedback scenario to a text file
        if produce:
            output = str(outcome).replace('\\n', '\n').replace('\\t', '\t')
            st.download_button('Download feedback scenario', data = output, file_name=output_file_name, mime='text/csv')

        st.markdown('[This is the end](https://www.youtube.com/watch?v=WNnzw90vxrE) of this form')

        
##############
# PAGE SET UP
##############

hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """

main_page()

