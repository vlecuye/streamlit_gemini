import streamlit as st
import random
import av
from io import BytesIO
import numpy as np
import time
import threading
from PIL import Image
from streamlit_webrtc import webrtc_streamer,VideoTransformerBase
from typing import List, Tuple, Union,Generator
from vertexai.generative_models import (
    GenerationConfig,
    GenerativeModel,
    HarmBlockThreshold,
    HarmCategory,
    Part,
    ChatSession
)
image = ""
lock = threading.Lock()
img_container = {"img": None}

PROJECT_ID = "all-in-demo"
LOCATION = "us-central1"
model = GenerativeModel(
        "gemini-1.5-pro-001",system_instruction=[
            """You are a rock paper scissor match referee.
            Your goal is to decide who won in the current match.
            The player on the left is called Vincent and the player on the right is called Chloe.
            Only consider the hands you see and ignore all other information.
            Tell us who wins.
            Don't forget that paper beats rock, rock beats scissors, scissors beat paper and that if player shave the same symbol, it's a tie.
            If a player points upwards with one finger, the symbol is the match and is considered cheating!
            Always tell us which symbol you saw and who won"""])


def video_frame_callback(frame):
    img = frame.to_ndarray(format="bgr24")
    flipped = img[:,::-1,:]
    with lock:
        img_container["img"] = flipped

    return av.VideoFrame.from_ndarray(flipped, format="bgr24")

st.title(":material/sports_kabaddi: Rock papier scissor Bot!")
ctx = webrtc_streamer(key="sample",video_frame_callback=video_frame_callback,media_stream_constraints={
        'video': {
            'width': 1920
            },
        'audio': False
    },)
if st.button("Let's go!"):
    with st.status('3') as status :
        time.sleep(0.75)
        status.update(label='2')
        time.sleep(0.75)
        status.update(label='1')
        time.sleep(0.75)
        status.update(label='SHOOT!')
        time.sleep(0.75)
        with lock:
            img = img_container["img"]
        
        image = Image.fromarray(img)
        savedImage = BytesIO()
        status.update(label="Analyzing")
        image.save(savedImage,'JPEG')
        image.save('test.jpg','JPEG')
        response = model.generate_content([Part.from_data(savedImage.getvalue(),'image/jpeg'),"This is a rock paper scissor game. If both players show the same item, it's a tie.Rock beats scissors, Scissors beat paper and paper beats rock. Tell me who won."])
        print(response)
    if response:
        st.markdown(response.text)

