"""
Created on Thu Dec 5 14:12:00 2024

@author: piotr.janczewski
"""

from datetime import datetime, timedelta
import pandas as pd
import streamlit as st
import json
import io
import docx
from openai import AzureOpenAI
from PIL import Image
from llama_index.core import Settings, VectorStoreIndex
from llama_index.llms.azure_openai import AzureOpenAI
from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding
from llama_index.core.schema import TextNode
from llama_index.core.tools import QueryEngineTool
import nest_asyncio
nest_asyncio.apply()

# Load configuration from JSON file
with open("config.json", mode="r") as f:
    config = json.load(f)

# client = AzureOpenAI(
#         azure_endpoint=config["AZURE_ENDPOINT"],
#         api_version=config["AZURE_OPENAI_API_VERSION"])

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

    Settings.llm = AzureOpenAI(model=config["AZURE_GPT_DEPLOYMENT_NAME"], engine=config["AZURE_GPT_DEPLOYMENT_NAME"], api_key=config["AZURE_API_KEY"], azure_endpoint=config["AZURE_ENDPOINT"], api_version=config["AZURE_OPENAI_API_VERSION"])
    Settings.embed_model = AzureOpenAIEmbedding(model="text-embedding-ada-002", deployment_name="text-embedding-ada-002", api_key=config["AZURE_API_KEY"], azure_endpoint=config["AZURE_ENDPOINT"], api_version=config["AZURE_OPENAI_API_VERSION"])

    nodes = [TextNode(text=examined_file[i], id_=str(i)) for i in range(len(examined_file))]
    vector_index = VectorStoreIndex(nodes)
    global chat_engine
    chat_engine = vector_index.as_chat_engine(chat_mode="context")
    response = chat_engine.chat(prompt)
    if b13_eval():
        if b20_eval():
            print("There is an identfied asset.")
            outcome = "There is an identfied asset."
            return outcome
    
    outcome = "Contract does not contain a lease. Apply other standards."

    return outcome

def read_contract(uploaded_file):
    try:
        doc = docx.Document(uploaded_file)
        content = [paragraph.text for paragraph in doc.paragraphs if len(paragraph.text)>5]
        return content
    except:
        pass
    try:
        stringio = io.StringIO(uploaded_file.getvalue().decode("utf-8"))
        text = stringio.read()
        text_list=text.split('\n')
        text_list_corrected=[item for item in text_list if not item==""]

        i=30
        content = [' '.join(text_list_corrected[i*j : i*(j+1)]) for j in range(len(text_list_corrected)//i)]
        return content
    except:
        print("Error reading file")

def ask_question(key, expected_answer=None):
    questions = {
        "B.13": "At any point in the contract, is there an asset scecified (explicitly or implicitly)?",
        "B.13.1": "What is the grant of contact? Is it an asset but not service or goods?",
        "B.13.2": "Does the grant of contact comprise of office promises, parking spaces, storage premises, or similar?",
        "B.20": "Is the asset physically distinct or does the customer have the right to receive substantially all of the capacity of the asset?",
        "B.14": "Does the supplier have the practical ability to substitute alternative assets throughout the period of use and would the supplier benefit economically from the exercise of its right to substitute the asset? Only answer Yes, if both of the conditions are met, but afterwards explain whether if either are met.",
        "B.17": "Is the asset located at supplier's premises?",
        "B.15": "Does the supplier have a right or an obligation to substitute the asset only on or after either a particular date or the occurrence of a specified event?",
        "B.18": "Is the supplier's right or obligation to substitute the asset only for repairs and maintenance?",
        "B.19": "Is substantiveness of substitution right readily determined?"
    }
    response = chat_engine.chat(questions[key])
    print(f'Q: {questions[key]}\nA: {response}\n\n')
    if expected_answer:
        return str(response).startswith(expected_answer)
    return response

def b13_eval():
    if ask_question("B.13", "Yes"):
        return True
    if ask_question("B.13.1", "Yes"):
        return True
    if ask_question("B.13.2", "Yes"):
        return True
    
    print("Contract does not contain a lease. Apply other standards.")
    return False

def b20_eval():
    if ask_question("B.20", "No"):
        return False
    if ask_question("B.14", "No"):
        return True
    if ask_question("B.17", "No"):
        return True
    if ask_question("B.15", "Yes"):
        return True
    if ask_question("B.18", "Yes"):
        return True
    if ask_question("B.19", "No"):
        return True
    
    print("Contract does not contain a lease. Apply other standards.")
    return False


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

        examined_prompt = """
        You are a helpful assistant. Your task is to check if there is an asset specified in the document. 
        The asset can be an item, land, building, tower, parking, storage space, etc. After finding as asset check if there is a lease in the contract due to the asset.
        The asset of the agreement may be implicitly or explicitly provided.
        When analyzing the document, do not take mentions of a lease agreement into consideration/assumption/analysis when determining your answer. Skip any words, titles, headings directly mentioning a lease. Do not mention a lease in your answers.
        After analysis find all details you know about the asset. 
        Please provide concise detailed answers to the questions, always starting with Yes or No.
        After your answer in English, provide a translation to Polish below.
        """

        LeaseTrue_prompt = "Lorem ipsum 2. This is a sample correct lease contract, use to determine if the main file is similar, a lease contract indeed."

        LeaseFalse_prompt = "Lorem ipsum 3. This is a sample incorrect lease contract, use to determine if the main file isn't a lease contract."
        
        # Add a file uploader widget
        examined_file = st.file_uploader("Upload Word/PDF file to examine", type=["doc", "docx", "pdf", "txt"], key="document-1")

        if examined_file:
            st.session_state.examined_file = examined_file


        with st.expander("Scope of examination", expanded = True):
            col1, col2, col3 = st.columns(3)
            with col1:
                exam_asset = st.checkbox("Is there an identified asset?", value = True)
                exam_lease = st.checkbox("Is it a lease contract (as per IFRS 16)?", value = False, disabled = True)
                exam_annex = st.checkbox("Is it an annex to another contract?", value = False, disabled = True)
                exam_modif = st.checkbox("Is it an annex modifying the base (MSSF 16)?", value = False, disabled = True)
                exam_prlng = st.checkbox("Is there a prolongation option, how likely is it?", value = False, disabled = True)
            with col2:
                exam_value = st.checkbox("What is the contract value?", value = False)
                exam_currn = st.checkbox("What is the contract currency?", value = False, disabled = True)
                exam_freqn = st.checkbox("What is the payment frequency?", value = False, disabled = True)
                exam_schdl = st.checkbox("What is the payment schedule?", value = False, disabled = True)
                exam_index = st.checkbox("Are the payments indexed against inflation?", value = False, disabled = True)
            with col3:
                exam_sgndt = st.checkbox("What is the date of document signature?", value = False, disabled = False)
                exam_srtdt = st.checkbox("What is the date of leasing initiation?", value = False, disabled = True)
                exam_indef = st.checkbox("Is the leasing indefinite in time?", value = False, disabled = True)
                exam_priod = st.checkbox("What is the leasing period?", value = False, disabled = True)
                exam_enddt = st.checkbox("What is the ending date?", value = False, disabled = True)


        with st.expander("Extra options"):
            col1, col2 = st.columns(2)
            with col1:
                LeaseTrue_file = st.file_uploader("[Optional] Upload a sample SIMILAR contract to enrich the comparison base", type=["doc", "docx", "pdf", "txt"], key="document-2")
            with col2:
                LeaseFalse_file = st.file_uploader("[Optional] Upload a sample DISSIMILAR contract to enrich the comparison base", type=["doc", "docx", "pdf", "txt"], key="document-3")

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
            
            # Read feedback table from Excel file
            if st.session_state.examined_file is not None:
                # Read the file 
                read_file = read_contract(st.session_state.examined_file)
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
            outcome = examine_contract(read_file, prompt_feed)
            st.write("")
            st.write(outcome)
            st.write("")

        # Save feedback scenario to a text file
        # if produce:
        #     output = str(outcome).replace('\\n', '\n').replace('\\t', '\t')
        #     st.download_button('Download feedback scenario', data = output, file_name=output_file_name, mime='text/csv')

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

