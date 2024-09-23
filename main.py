import streamlit as st
import random
import time

st.logo("my_cloud.png",icon_image="my_cloud.png")
pages = { 
    "Segment Creation": [
        st.Page('chat.py',title='Persona Creation',icon=':material/chat:'),
        st.Page('rockpaperscissor.py',title='Rock Paper Scissor Bot',icon=':material/sports_kabaddi:')
        ]
         }

pg = st.navigation(pages)
pg.run()