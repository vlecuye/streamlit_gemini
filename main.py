import streamlit as st
import random
import time
st.set_page_config(layout="wide")
st.logo("logo_full.svg",icon_image="logo.svg")
pages = { 
    "Segment Creation": [
        st.Page('chat.py',title='Persona Creation',icon=':material/chat:'),
        st.Page('rockpaperscissor.py',title='More stuff coming soon!',icon=':material/sports_kabaddi:')
        ]
         }

pg = st.navigation(pages)
pg.run()