from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

import wikipediaapi as wpa
import markovify

app = FastAPI()
origins_to_allow = ["http://localhost:3000", "https://essee.tk", "https://www.essee.tk", "http://essee.tk", "http://www.essee.tk"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins_to_allow,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

import random

wiki = wpa.Wikipedia('fi')

@app.get('/api/marko/{article}')
def fetch_wiki(article: str):
    page = wiki.page(article)
    if not page.exists():
        raise HTTPException(status_code=404, detail="Not found wiki")
    
    text = page.text.split('\n')
    text_model = markovify.Text(text)

    sentences = []
    for i in range(30):
        sentence = text_model.make_sentence(tries=random.randint(1000, 50000))
        if sentence not in sentences:
            sentences.append(sentence)

    return sentences