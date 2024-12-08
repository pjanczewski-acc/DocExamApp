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

st.set_page_config(page_title="Document Examination App",
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
    st.markdown("<h1><b>Determine content of a document</b></h1>", unsafe_allow_html=True)
        
    with st.form("Contract analysis", clear_on_submit=False):

        examined_prompt = "Lorem ipsum 1. Is the main file a lease contract?"

        LeaseTrue_prompt = "Lorem ipsum 2. This is a sample correct lease contract, use to determine if the main file is similar, a lease contract indeed."

        LeaseFalse_prompt = "Lorem ipsum 3. This is a sample incorrect lease contract, use to determine if the main file isn't a lease contract."
        
        # Add a file uploader widget
        examined_file = st.file_uploader("Upload Word/PDF file to examine", type=["doc", "docx", "pdf"])

        with st.expander("Scope of examination", expanded = True):
            col1, col2 = st.columns(2)
            with col1:
                exam_asset = st.checkbox("Is there an identified asset?", value = True)
                exam_lease = st.checkbox("Is it a lease contract (as per IFRS 16)?", value = False, disabled = True)
                exam_annex = st.checkbox("Is it an annex to another contract?", value = False, disabled = True)
                exam_modif = st.checkbox("Is it an annex modifying the base as per MSSF 16?", value = False, disabled = True)
                exam_prlng = st.checkbox("Is there a prolongation option, how likely is it?", value = False, disabled = True)
            with col2:
                exam_value = st.checkbox("What is the contract value?", value = False)
                exam_currn = st.checkbox("What is the contract currency?", value = False, disabled = True)
                exam_freqn = st.checkbox("What is the payment frequency?", value = False, disabled = True)
                exam_schdl = st.checkbox("Are the payments spread over time evenly, what is their schedule?", value = False, disabled = True)
                exam_index = st.checkbox("Are the payments indexed (against inflation or fixed value)?", value = False, disabled = True)


        with st.expander("Extra options"):
            col1, col2 = st.columns(2)
            with col1:
                LeaseTrue_file = st.file_uploader("[Optional] Upload a sample SIMILAR contract to enrich the comparison base", type=["doc", "docx", "pdf"])
            with col2:
                LeaseFalse_file = st.file_uploader("[Optional] Upload a sample DISSIMILAR contract to enrich the comparison base", type=["doc", "docx", "pdf"])

            examined_feed = st.text_area("Main part, edit if adequate", value = examined_prompt)
            LeaseTrue_feed = st.text_area("Sample lease contract part (optional), edit if adequate", value = LeaseTrue_prompt)
            LeaseFalse_feed = st.text_area("Sample non-lease contract part (optional), edit if adequate", value = LeaseFalse_prompt)
            st.write("")
            rigidness_val = st.slider("How cautious you want the verification to be?: 1=Very liberal, 5=Very strict",
                                      help="Liberal = risk of false yes/no (low temperature); \n Strict = risk of a 'hard to say' (high temperature)",
                                      min_value=1, max_value=5, value=3, disabled=True)
            st.write("")
                
        # Premilinary listing before final export
        
        outcome_display = st.checkbox("Display verification outcome", value = True)
        outcome_record = st.checkbox("Write the outcome to the database", value = False, disabled = True)
        outcome_csvfile = st.checkbox("Write the outcome to a csv file", value = False, disabled = True)
        
        produce = st.form_submit_button("Examine the document")

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

