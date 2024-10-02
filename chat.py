import streamlit as st
import time
from typing import List, Union,Generator
from vertexai.generative_models import (
    GenerationConfig,
    GenerativeModel,
    HarmBlockThreshold,
    FunctionDeclaration,
    HarmCategory,
    Part,
    Tool,
    Content,
    grounding,
    ChatSession
)

# Declaration of the Function for Gemini
get_picture_func = FunctionDeclaration(
    name="get_picture",
    description="Get a photo or a picture from the current user before you roast them",
    # Function parameters are specified in OpenAPI JSON schema format
    parameters={
        "type": "object",
        "properties": {"Summary": {"type": "string", "description": "A detailed summary of the user's hobbies, job and pets"}},
    }
    ,
)
# Variable Initialization inside of the state
st.session_state['file_upload'] = False
st.session_state.summary = ""
#ID of the project
PROJECT_ID = "pc-smart-persona"
# Location of the gemini access
LOCATION = "us-central1"
# Prompt
text = """You are receiving a PDF document. This document states who you are and what you know. Adopt this persona and answer the questions from the user to the best of your ability """

# Define the tool used by Gemini to access the Get_picture function
tool = Tool.from_google_search_retrieval(grounding.GoogleSearchRetrieval())

#Definition of the model used for the roasting
roastingmodel = GenerativeModel(
        "gemini-1.5-pro-001") 
#Definition of the model used for the chat before the roast. 
model = GenerativeModel(
        "gemini-1.5-flash",system_instruction=[text])
generation_config: GenerationConfig = GenerationConfig(
        temperature=2, max_output_tokens=4096
    ,)

from google.cloud import firestore

# The `project` parameter is optional and represents which project the client
# will act on behalf of. If not supplied, the client falls back to the default
# project inferred from the environment.
db = firestore.Client(project="pc-smart-persona")
if "personas" not in st.session_state:
    st.session_state.personas = []
    array = db.collection('personas').stream()
    for field in array :
        st.session_state.personas.append(field.to_dict())

# Safety Settings definition used by models
safety_settings = {
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    }

def display_name(option):
    return option['name']
def picture_received():
    #responses = roastingmodel.generate_content
    """You are a roasting robot with the personality of the best roasting comedians of new york city.
    First, describe what you see in the picture. 
    Second, here is some more information about the person in the picture: {}.
    Now write the best roast possible using both the description of the picture and the additional information that has been provided.
    The response must ABSOLUTELY have more than 500 words and should end with a nice touch about the person.
    For your information, seats in sections 101 to 105 are close to the stage, while 201 to 205 are very far away."""
    #.format(st.session_state['summary'])])

    #with st.chat_message("assistant"):
    #    st.write(responses.text)
    #    st.session_state.messages.append({"role": "assistant", "content": responses.text})

def get_gemini_response(
    chat: ChatSession,
    contents: Union[str, List],
    generation_config: GenerationConfig = GenerationConfig(
        temperature=1, max_output_tokens=2048
    ),
    stream: bool = True,
) -> Generator:
    """Generate a response from the Gemini model."""
    responses = chat.send_message(
        contents,
        generation_config=generation_config,
        safety_settings=safety_settings,
        stream=stream
    )

    if not stream:
        return responses.text
    final_response = []
    for r in responses:
        try:
            if (r.candidates[0].content.parts[0].function_call.name=="get_picture"):
                print(r.candidates[0].content.parts[0].function_call)
                st.session_state['file_upload'] = True
                st.session_state.summary = r.candidates[0].content.parts[0].function_call.args['Summary']
                print(st.session_state.summary)
            elif r.text :
                for word in r.text.split():
                    yield word + " "
                    time.sleep(0.05)
        except IndexError:
            final_response.append("")
            continue

def change_func():
    print(st.session_state.persona)
    st.session_state.messages = []
    if st.session_state.persona is not None :
        model = GenerativeModel("gemini-1.5-flash",system_instruction=[st.session_state.persona['prompt']])
        st.session_state['chat'] = model.start_chat()
    else:
        st.session_state.messages.append({"role": "assistant", "content": "Choose your persona on the right to start!"})
        


st.title(":material/chat: Smart Persona Demo")
col1,col2,col3 = st.columns([4,2,2])


with col2:
    option = st.selectbox("Select your persona",st.session_state.personas,index=None,format_func=display_name,on_change=change_func,key="persona")
    if option:
        st.image(image=option['picture_url'],use_column_width=True)
        st.markdown(option['description'])
with col3:
    if option:
        st.header("Prompt used:")
        st.markdown(option['prompt'])

with col1:
    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.messages.append({"role": "assistant", "content": "Choose your persona on the right to start!"})
    if option:
        st.subheader("Currently speaking with " + option['name'])
    # Initialize chat history
    messages = st.container()
    # Start conversation if no messages are there
        
    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with messages.chat_message(message["role"]):
            st.markdown(message["content"])
    # Add user message to chat history
    # Display user message in chat message container

    # Accept user input

    if len(st.session_state.messages) == 0 :
            with messages.chat_message("assistant"):
                response = st.write_stream(get_gemini_response(st.session_state['chat'], ["Hello!"]))
                st.session_state.messages.append({"role":"assistant","content":response})
    if option:
        if prompt := st.chat_input("Write your question here"):
            

            with messages.chat_message("user"):
                st.markdown(prompt)
                st.session_state.messages.append({"role":"user","content":prompt})

            # Display assistant response in chat message container
            with messages.chat_message("assistant"):
                response = st.write_stream(get_gemini_response(st.session_state['chat']
                                    , [prompt]
                            ))
                # Add assistant response to chat history
                st.session_state.messages.append({"role": "assistant", "content": response})
        if st.session_state['file_upload']:
            with st.chat_message("assistant"):
                file = st.file_uploader('Send us your picture!',key='uploaded_picture',on_change=picture_received)
