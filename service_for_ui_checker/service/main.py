import tensorflow as tf
from keras.models import load_model
import io
from PIL import Image, ImageFile
from io import BytesIO
import asyncio
import uuid
import numpy as np
import os
import asyncio
import base64
from fastapi import FastAPI, Form, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
import traceback
import sys
sys.path.insert(0, "service_for_ui_checker")
from alternative_functions import *
from __version__ import __version__, __description__
from work_with_texts.typos import TypoCheck
from work_with_texts.contrast_ratios import ContrastCheck

from UIED_3_3 import run_single

import paddings.fix_paddings as fix_paddings


ImageFile.LOAD_TRUNCATED_IMAGES = True

THRESHOLD = 0.41

MESSAGES = {(0,10) : "There is a great room to improve the spacing system on the provided screenshot. If you want to know more details, get the report.",
            (10,20) : "The spacing system on this screenshot needs major improvements. If you want to know how to adjust it, get the report.",
            (20,40) : "This screenshot's spacing system is inconsistent. If you want to know how to adjust it, get the report.",
            (40,50) : "The spacing system on the provided screenshot is a bit messy. Get the report for detailed overview.",
            (50,60): "The spacing system on the provided screenshot is rather accurate than messy. Still, if you want more details, get the report.",
            (60,70) : "The spacing system is neither accurate nor messy. There are many changes needed to be made. If you want to know how to adjust it, get the report.",
            (70,80) : "The spacings are close to perfect, but still there are some fixes to be made. If you want more details, get the report.",
            (80,90) : "The spacings are quite accurate! There may be some minor fixes to be made. Get the report for more details.",
            (90,100) : "The spacings are perfectly accurate on this screenshot! There may be some minor fixes to be made. If you want more details, get the report. (edited)"}

# from quart import Quart

app = FastAPI()

# cache = Cache(app)

timeout_duration = 60
 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

    

def get_image(content):

    try:
        img_data = get_image_byte_data(content).encode()
        base64.b64encode(base64.decodebytes(img_data)) == img_data

    except:
        response_content = "Invalid type of data"
        response_content += '\n' + traceback.format_exc()
        raise HTTPException(500, response_content)

    img_size = base_size(str(img_data)) / (1024**2)


    if img_size > 24.0:
        response_content = "Image size must be less or equal than 24 mb"
        response_content += '\n' + traceback.format_exc()
        raise HTTPException(413, response_content)

    img_bytes = base64.decodebytes(img_data)
    image = Image.open(io.BytesIO(img_bytes))
    rgb_image = image.convert('RGB')

    return rgb_image


@app.get("/")
def info():
    return __description__


async def predict(best_model, input_arr):
    result = await asyncio.get_event_loop().run_in_executor(None, best_model.predict, input_arr)
    return result


@app.post("/check_UI")
async def check_ui(file = Form(...)):
    try:
        # print(file)
        batch_size = (512, 512)
        # class_names = ['Non_UI', 'UI']

        path = os.path.realpath(__file__)
        dir = os.path.dirname(path)

        best_model = load_model(dir + '/models/best_model.h5')

        # rgb_image.save('image.png')
        rgb_image = get_image(file)

        input_arr = tf.keras.utils.img_to_array(rgb_image.resize(batch_size))
        input_arr = np.array([input_arr])

        pred = await asyncio.wait_for(predict(best_model, input_arr), timeout=timeout_duration)
        
        return {'Status': 'ok', 'message': int(pred[0][1] > THRESHOLD)}
    
    except asyncio.TimeoutError:
        response_content = "Request Timeout"
        response_content += '\n' + traceback.format_exc()
        raise HTTPException(408, response_content)
    except:
        response_content = "Error in check_UI function"
        response_content += '\n' + traceback.format_exc()
        raise HTTPException(500, response_content)
        



async def get_paddings(loaded_img, id, parameters):
    
    return await asyncio.get_event_loop().run_in_executor(None, run_single.main, loaded_img, id, parameters)


@app.post("/check_paddings")
async def check_paddings(file = Form(...), data = File(None)):

    try:
        print("check_paddings")
        content = file
        loaded_img = get_image(content)
        print(loaded_img.size)
        if data:
            parameters = json.loads(data)
        
        else: parameters = {"merge_layers" : True, "min_area" : 50, "merge_texts" : 1, "merge_text_compo" : 0.2}

        # print(parameters)
        
        id = str(uuid.uuid1())

        # response = get_paddings(loaded_img, id, parameters)
        # returned_img, cons, all_compos, coords = response
        response = await asyncio.wait_for(get_paddings(loaded_img, id, parameters), timeout=timeout_duration)
        returned_img, cons, all_compos, coords, texts = await response
        
    except asyncio.TimeoutError:
        response_content = "Request Timeout"
        response_content += '\n' + traceback.format_exc()
        raise HTTPException(408, response_content)
        
    except: 
        response_content = "Error in check_paddings function"
        response_content += '\n' + traceback.format_exc()
        raise HTTPException(500, response_content)
    
    try:
        for interval, message in MESSAGES.items():
            start = interval[0]
            end = interval[1]
            if cons in range(start, end):
                break
        

        buffered = BytesIO()
        returned_img.save(buffered, format="JPEG")
        # Encode bytes as base64
        buffered.seek(0)
        encoded_string = base64.b64encode(buffered.getvalue()).decode('utf-8')
        buffered.close()
        
        return {'Status': 'ok', "base64": encoded_string, "message" : message, "all_compos" : all_compos, "coords" : {"coordinates" : coords}, "texts" : texts}
        
    except: 
        response_content = "Error in check_paddings function"
        response_content += '\n' + traceback.format_exc()
        raise HTTPException(500, response_content)
    
 

async def recommendation(input_image, all_compos, coords):
    args = fix_paddings.preprocess(all_compos, coords)
    return fix_paddings.get_correct(input_image, args)

    
    
@app.post("/get_recommendation")
async def get_recommendation(file = Form(...), all_compos = File(...), coords = File(...), texts = File(...)):

    content = file
    loaded_img = get_image(content)
    input_image = np.array(loaded_img)
    # print(input_image.shape)
    
    try:
        # recommended_img = await asyncio.wait_for(recommendation(input_image, json.loads(all_compos, strict=False), json.loads(coords, strict=False)["coordinates"]), timeout=timeout_duration)
        texts = json.loads(texts, strict=False)['texts']
        typo_check = TypoCheck(texts=texts)
        contrast_check= ContrastCheck(image=input_image, texts=texts)
        tasks = [typo_check.spell_checks(), typo_check.grammar_checks(), contrast_check.contrast_ratio(), 
                 asyncio.wait_for(recommendation(input_image, json.loads(all_compos, strict=False), json.loads(coords, strict=False)["coordinates"]), timeout=timeout_duration)]
        
        spell_recs, grammar_recs, contrast_ratios, recommended_img =  await asyncio.gather(*tasks)
        
        return {"recommendation" : recommended_img, "rec_texts_spell" : spell_recs, "contrast_ratios" : contrast_ratios, "rec_texts_grammar" : grammar_recs}
        
    except asyncio.TimeoutError:
        response_content = "Request Timeout"
        response_content += '\n' + traceback.format_exc()
        raise HTTPException(408, response_content)
        
    except: 
        response_content = "Error in get_recommendation function"
        response_content += '\n' + traceback.format_exc()
        raise HTTPException(500, response_content)

