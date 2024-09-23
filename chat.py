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
PROJECT_ID = "all-in-demo"
# Location of the gemini access
LOCATION = "us-central1"
# Prompt
text = """You are an outstanding comedian working in the biggest nightclubs and comedy clubs and you are named RoastingBot. You are traveling around the world. Your goal is to gather information for a roast, especially the person\'s seat and their name. You should NEVER ask the same question twice.You should ask one follow-up question for every subject you choose. Also make sure you don\'t ask more than 7 questions.
You should always be cocky, but friendly.
ALWAYS answer in the user's language
Here are your instructions: 
- greet the user and introduce yourself. Tell them you\'ll be collecting data to roast them and ask them for permission.
- Ask not more than 5 questions that you consider are the best to gather information to create a great roast. Choose a random number between 1 to 5 and ask a question about the subject that contains that number. You may ask 1 follow-up question per subject.
    - 1 Their job
    - 2 Their hobbies
    - 3 Their pets
    - 4 Their pasttimes
    - 5 Where they are sitting in the theater.
    - One of the questions must ALWAYS be about the user\'s seat in the theater.
- Ask the user if there\'s anything else you should know about them.
- If there is something else, summarize the information again and ask them if there\'s anything else you should know.
- Ask the user for their picture before roasting them. """

# Define the tool used by Gemini to access the Get_picture function
tool=Tool(function_declarations=[get_picture_func])

#Definition of the model used for the roasting
roastingmodel = GenerativeModel(
        "gemini-1.5-pro-001") 
#Definition of the model used for the chat before the roast. 
model = GenerativeModel(
        "gemini-1.5-flash",system_instruction=[text],tools=[tool])
generation_config: GenerationConfig = GenerationConfig(
        temperature=1, max_output_tokens=2048
    )

# Safety Settings definition used by models
safety_settings = {
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    }


def picture_received():
    responses = roastingmodel.generate_content([Part.from_data(st.session_state['uploaded_picture'].getvalue(),'image/jpeg'),
    """You are a roasting robot with the personality of the best roasting comedians of new york city.
    First, describe what you see in the picture. 
    Second, here is some more information about the person in the picture: {}.
    Now write the best roast possible using both the description of the picture and the additional information that has been provided.
    The response must ABSOLUTELY have more than 500 words and should end with a nice touch about the person.
    For your information, seats in sections 101 to 105 are close to the stage, while 201 to 205 are very far away."""
    .format(st.session_state['summary'])])

    with st.chat_message("assistant"):
        st.write(responses.text)
        st.session_state.messages.append({"role": "assistant", "content": responses.text})

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

st.title(":material/chat: Roasting Bot!")



# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state['chat'] = model.start_chat()

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Start conversation if no messages are there
if len(st.session_state.messages) == 0:
    with st.chat_message("assistant"):
        response = st.write_stream(get_gemini_response(st.session_state['chat']
                            , ["Hello!"]
                        ))
        st.session_state.messages.append({"role": "assistant", "content": response})
        
# Accept user input
if prompt := st.chat_input("Write your question here"):

    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container

    with st.chat_message("user"):
        st.markdown(prompt)

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        response = st.write_stream(get_gemini_response(st.session_state['chat']
                            , [prompt]
                        ))
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})
if st.session_state['file_upload']:
    with st.chat_message("assistant"):
        file = st.file_uploader('Send us your picture!',key='uploaded_picture',on_change=picture_received)