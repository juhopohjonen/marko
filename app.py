from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from pydantic import BaseModel

import wikipediaapi as wpa
import markovify

from typing import Union

import os
import openai

from dotenv import load_dotenv


dev = False
if dev:
    load_dotenv()
    
openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()
origins_to_allow = ["http://localhost:3000", "https://essee.tk", "https://www.essee.tk", "http://essee.tk", "http://www.essee.tk"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins_to_allow,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.mount('/static', StaticFiles(directory='static'), name='static')

import random

default_wiki_code = 'fi'
other_accepted_wikis = ['en', 'sv']
code_definitions = [{ 'code': 'en', 'name': 'Englanti' }, { 'code': 'fi', 'name': 'Suomi' }, { 'code': 'sv', 'name': 'Ruotsi' }]


default_wiki = wpa.Wikipedia(default_wiki_code)
default_state_size = 2

@app.get('/api/marko/{article}')
def fetch_wiki(article: str, lang: Union[str, None] = None, accuracy: int = default_state_size):
    # state size based on accuracy val
    if accuracy < 1 or accuracy > 5:
        accuracy = default_state_size
    

    if lang in other_accepted_wikis:
        wiki = wpa.Wikipedia(lang)
    else:
        wiki = default_wiki

    try:
        page = wiki.page(article)
    except:
        print('exeption at loading wiki')
        raise HTTPException(status_code=503, detail="wiki error")

    if not page.exists():
        raise HTTPException(status_code=404, detail="Not found wiki")
    
    text = page.text.split('\n')
    text_model = markovify.Text(text, state_size=accuracy)

    sentences = []
    for i in range(30):
        sentence = text_model.make_sentence(tries=random.randint(1000, 50000))
        if sentence not in sentences:
            sentences.append(sentence)

    return sentences

@app.get('/api/wiki')
def getWikis():
    wiki_list = []

    wiki_list.append(default_wiki_code)
    for code in other_accepted_wikis:
        wiki_list.append(code)

    
    content = {
        'wikis': wiki_list,
        'definitions': code_definitions
    }

    return content

class Completion(BaseModel):
    query: str


@app.post('/api/ai/completion')
def complete(completion: Completion):
    if not completion:
        raise HTTPException(status_code=404, detail='No completion')

    moderation_res = openai.Moderation.create(input=completion.query)
    isFlagged = moderation_res.results[0].flagged

    print(moderation_res)
    
    if isFlagged:
        raise HTTPException(status_code=422, detail='TOS error')

    resreq = openai.Completion.create(engine="text-davinci-003", prompt=completion.query, temperature=0.9, max_tokens=2000)
    response = resreq.choices[0].text

    respObj = {
        "response": response
    }

    return respObj


@app.get('/api/ai/models')
def models():
    engines = openai.Engine.list()
    print(engines.data)

    return engines.data


@app.post('/api/ai/image')
def generate(completion: Completion):

    if not completion:
        raise HTTPException(status_code=404, detail='No completion')

    res = openai.Image.create(
        prompt=completion.query,
        n=1,
        size="1024x1024"
    )

    imgUrl = res['data'][0]['url']
    respObj = {
        "url": imgUrl
    }
    return respObj