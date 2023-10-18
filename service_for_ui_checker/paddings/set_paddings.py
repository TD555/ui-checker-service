import json
from PIL import Image, ImageDraw, ImageFont
from sympy import Symbol
from matplotlib import cm
import numpy as np
import cv2
import asyncio
import os

path = os.path.realpath(__file__)
dir = os.path.dirname(path)

X_MIN = 3
Y_MIN = 3

def remove_duplicates(lst):
    # await asyncio.sleep(0)
    seen = set()
    result = []
    for item in lst:
        item_tuple = tuple(sorted((k, tuple(v) if isinstance(v, list) else v) for k, v in item.items()))
        if item_tuple not in seen:
            seen.add(item_tuple)
            result.append(item)
    return result

def __main__(id, x_scale, y_scale):
    # Opening JSON file
    # await asyncio.sleep(0)
    global X_MIN, Y_MIN
    X_MIN = x_scale
    Y_MIN = y_scale
    
    print(X_MIN, Y_MIN)
    
    with open(dir + f'/../UIED_3_3/data/output/merge/{id}.json', "r+") as f:
        data = json.load(f)
        
        for compo in data['compos']:

            compo['column_min'], compo['column_max'], compo['row_min'], compo['row_max'] = compo["position"][
                'column_min'], compo["position"]['column_max'], compo["position"]['row_min'], compo["position"]['row_max']
            del compo["position"]

        for i, compo in enumerate(data['compos']):
            compo['parent'] = [0]
            for j, compare in enumerate(data['compos']):
                if compo['id'] != compare['id']:
                    """ add parents"""
                    if compo['column_min'] >= compare['column_min'] and compo['column_max'] <= compare['column_max'] and \
                            compo['row_min'] >= compare['row_min'] and compo['row_max'] <= compare['row_max']:
                        compo['parent'].append(compare['id'])

        for i, compo in enumerate(data['compos']):
            for j, compare in enumerate(data['compos']):
                if compo['id'] != compare['id']:
                    """ add childs"""
                    if 'parent' in compo.keys():
                        if compo['column_min'] >= compare['column_min'] and compo['column_max'] <= compare['column_max'] \
                                and compo['row_min'] >= compare['row_min'] and compo['row_max'] <= compare['row_max']:
                            if 'child' not in compare.keys():
                                compare["child"] = []
                            # print(compo, '\n', compare, '\n\n')
                            compare["child"].append(compo['id'])
                    

    os.remove(dir + f'/../UIED_3_3/data/output/ip/{id}.json')
    os.remove(dir + f'/../UIED_3_3/data/output/ocr/{id}.json')
    os.remove(dir + f'/../UIED_3_3/data/output/merge/{id}.json')

    os.makedirs(dir + '/../UIED_3_3/my_json', exist_ok=True)
    
    data['compos'] = remove_duplicates(data['compos'])
    
    return data

    
def find_coords(data):
    # await asyncio.sleep(0)
    coordinates = []
    x_min:int
    y_min:int         
    # Opening JSON file
    left_blocks = []
    right_blocks = []
    top_blocks = []
    bottom_blocks = []

    coords = []
    
    # print(data)
    
    y_min, x_min = img_height, img_width = data['img_shape'][:2]
    for i, compo in enumerate(data['compos']):
        for j, compare in enumerate(data['compos']):
            if compare['id'] == compo['parent'][-1]:

                "Paddings from parent boxes"

                for child in data['compos']:
                    # print(compare)
                    if child['id'] in compare['child']:
                        if compo['column_min'] > child['column_min'] and (compo['row_max'] > child['row_min'] and compo['row_min'] < child['row_max']):
                            left_blocks.append(child)
                        if compo['column_max'] < child['column_max'] and (compo['row_max'] > child['row_min'] and compo['row_min'] < child['row_max']):
                            right_blocks.append(child)
                        if compo['row_min'] > child['row_min'] and (compo['column_max'] > child['column_min'] and compo['column_min'] < child['column_max']):
                            top_blocks.append(child)
                        if compo['row_max'] < child['row_max'] and (compo['column_max'] > child['column_min'] and compo['column_min'] < child['column_max']):
                            bottom_blocks.append(child)

                if left_blocks:
                    child = max(
                        left_blocks, key=lambda item: item['column_max'])
                    compo_list = [compo['row_min'] +
                                    i for i in range(compo['height'] + 1)]
                    child_list = [child['row_min'] +
                                    i for i in range(child['height'] + 1)]
                    cross = [i for i in compo_list if i in child_list]
                    # print(compo_list, child_list, cross)
                    center = (cross[0] + cross[-1]) / 2
                    # print(child)
                    if compo['column_min'] - child['column_max'] >= X_MIN:
                        coordinates.append([{"compo" : compo, "compare" : child}, {'x_min': float(child['column_max']), 'x_max': float(
                            compo['column_min']), 'y_min': float(center), 'y_max': float(center), 'axis': 0}])
                        if x_min > compo['column_min'] - child['column_max']:
                            x_min = compo['column_min'] - \
                                child['column_max']

                    left_blocks.clear()
                else:
                    compo_list = [compo['row_min'] +
                                    i for i in range(compo['height'] + 1)]
                    compare_list = [compare['row_min'] +
                                    i for i in range(compare['height'] + 1)]
                    cross = [i for i in compo_list if i in compare_list]
                    # print(compo_list, child_list, cross)
                    center = (cross[0] + cross[-1]) / 2
                    if compo['column_min'] - compare['column_min'] >= X_MIN:
                        coordinates.append([{"compo" : compo, "compare" : compare}, {'x_min': float(compare['column_min']), 'x_max': float(
                            compo['column_min']), 'y_min': float(center), 'y_max': float(center), 'axis': 0}])
                        if x_min > compo['column_min'] - compare['column_min']:
                            x_min = compo['column_min'] - \
                                compare['column_min']

                if not right_blocks:
                    compo_list = [compo['row_min'] +
                                    i for i in range(compo['height'] + 1)]
                    compare_list = [compare['row_min'] +
                                    i for i in range(compare['height'] + 1)]
                    cross = [i for i in compo_list if i in compare_list]
                    # print(compo_list, child_list, cross)
                    center = (cross[0] + cross[-1]) / 2
                    if compare['column_max'] - compo['column_max'] >= X_MIN:
                        coordinates.append([{"compo" : compo, "compare" : compare}, {'x_min': float(compo['column_max']), 'x_max': float(
                            compare['column_max']), 'y_min': float(center), 'y_max': float(center), 'axis': 0}])
                        if x_min > compare['column_max'] - compo['column_max']:
                            x_min = compare['column_max'] - \
                                compo['column_max']

                else:
                    child = min(
                        right_blocks, key=lambda item: item['column_min'])
                    compo_list = [compo['row_min'] +
                                    i for i in range(compo['height'] + 1)]
                    child_list = [child['row_min'] +
                                    i for i in range(child['height'] + 1)]
                    cross = [i for i in compo_list if i in child_list]
                    # print(compo_list, child_list, cross)
                    center = (cross[0] + cross[-1]) / 2
                    if child['column_min'] - compo['column_max'] >= X_MIN:
                        coordinates.append([{"compo" : compo, "compare" : child}, {'x_min': float(compo['column_max']), 'x_max': float(
                            child['column_min']), 'y_min': float(center), 'y_max': float(center), 'axis': 0}])
                        if x_min > child['column_min'] - compo['column_max']:
                            x_min = child['column_min'] - \
                                compo['column_max']

                    right_blocks.clear()

                if top_blocks:
                    child = max(
                        top_blocks, key=lambda item: item['row_max'])
                    # print(child, compo)
                    compo_list = [compo['column_min'] +
                                    i for i in range(compo['width'] + 1)]
                    child_list = [child['column_min'] +
                                    i for i in range(child['width'] + 1)]
                    cross = [i for i in compo_list if i in child_list]
                    # print(compo_list, child_list, cross)
                    center = (cross[0] + cross[-1]) / 2
                    if compo['row_min'] - child['row_max'] >= Y_MIN:
                        coordinates.append([{'compo' : compo, "compare" : child}, {'x_min': float(center), 'x_max': float(center), 'y_min': float(
                            child['row_max']), 'y_max': float(compo['row_min']), 'axis': 1}])
                        if y_min > compo['row_min'] - child['row_max']:
                            y_min = compo['row_min'] - child['row_max']

                    top_blocks.clear()

                else:
                    compo_list = [compo['column_min'] +
                                    i for i in range(compo['width'] + 1)]
                    compare_list = [compare['column_min'] +
                                    i for i in range(compare['width'] + 1)]
                    cross = [i for i in compo_list if i in compare_list]
                    # print(compo_list, child_list, cross)
                    center = (cross[0] + cross[-1]) / 2
                    if compo['row_min'] - compare['row_min'] >= Y_MIN:
                        coordinates.append([{'compo' : compo, "compare" : compare}, {'x_min': float(center), 'x_max': float(center), 'y_min': float(
                            compare['row_min']), 'y_max': float(compo['row_min']), 'axis': 1}])
                        if y_min > compo['row_min'] - compare['row_min']:
                            y_min = compo['row_min'] - compare['row_min']

                if bottom_blocks:
                    child = min(bottom_blocks,
                                key=lambda item: item['row_min'])
                    # print(child, compo)
                    compo_list = [compo['column_min'] +
                                    i for i in range(compo['width'] + 1)]
                    child_list = [child['column_min'] +
                                    i for i in range(child['width'] + 1)]
                    cross = [i for i in compo_list if i in child_list]
                    # print(compo_list, child_list, cross)
                    center = (cross[0] + cross[-1]) / 2
                    if child['row_min'] - compo['row_max'] >= Y_MIN:
                        coordinates.append([{'compo' : compo, "compare" : child}, {'x_min': float(center), 'x_max': float(center), 'y_min': float(
                            compo['row_max']), 'y_max': float(child['row_min']), 'axis': 1}])
                        if y_min > child['row_min'] - compo['row_max']:
                            y_min = child['row_min'] - compo['row_max']

                    bottom_blocks.clear()

                else:
                    compo_list = [compo['column_min'] +
                                    i for i in range(compo['width'] + 1)]
                    compare_list = [compare['column_min'] +
                                    i for i in range(compare['width'] + 1)]
                    cross = [i for i in compo_list if i in compare_list]
                    # print(compo_list, child_list, cross)
                    center = (cross[0] + cross[-1]) / 2
                    if compare['row_max'] - compo['row_max'] >= Y_MIN:
                        coordinates.append([{'compo' : compo, "compare" : compare},{'x_min': float(center), 'x_max': float(center), 'y_min': float(
                            compo['row_max']), 'y_max': float(compare['row_max']), 'axis': 1}])
                        if y_min > compare['row_max'] - compo['row_max']:
                            y_min = compare['row_max'] - compo['row_max']

        else:

            "Paddings from main page"

            for child in data['compos']:
                # print(compare)
                if child['parent'] == [0]:
                    if compo['column_min'] > child['column_min'] and (compo['row_max'] > child['row_min'] and compo['row_min'] < child['row_max']):
                        left_blocks.append(child)
                    if compo['column_max'] < child['column_max'] and (compo['row_max'] > child['row_min'] and compo['row_min'] < child['row_max']):
                        right_blocks.append(child)
                    if compo['row_min'] > child['row_min'] and (compo['column_max'] > child['column_min'] and compo['column_min'] < child['column_max']):
                        top_blocks.append(child)
                    if compo['row_max'] < child['row_max'] and (compo['column_max'] > child['column_min'] and compo['column_min'] < child['column_max']):
                        bottom_blocks.append(child)

            if left_blocks:
                child = max(
                    left_blocks, key=lambda item: item['column_max'])
                compo_list = [compo['row_min'] +
                                i for i in range(compo['height'] + 1)]
                child_list = [child['row_min'] +
                                i for i in range(child['height'] + 1)]
                cross = [i for i in compo_list if i in child_list]
                # print(compo_list, child_list, cross)
                center = (cross[0] + cross[-1]) / 2
                # print(child)
                if compo['column_min'] - child['column_max'] >= X_MIN:
                    coordinates.append([{'compo' : compo, "compare" : child}, {'x_min': float(child['column_max']), 'x_max': float(
                        compo['column_min']), 'y_min': float(center), 'y_max': float(center), 'axis': 0}])
                    if x_min > compo['column_min'] - child['column_max']:
                        x_min = compo['column_min'] - child['column_max']

                left_blocks.clear()

            else:
                compo_list = [compo['row_min'] +
                                i for i in range(compo['height'] + 1)]
                compare_list = [i for i in range(img_height + 1)]
                cross = [i for i in compo_list if i in compare_list]
                # print(compo_list, child_list, cross)
                center = (cross[0] + cross[-1]) / 2
                if compo['column_min'] >= X_MIN:
                    coordinates.append([{'compo' : compo, "compare" : {'id': 0,
                                                                        'class': 'Compo',
                                                                        'height': data['img_shape'][0],
                                                                        'width': data['img_shape'][1],
                                                                        'column_min': 0,
                                                                        'column_max': data['img_shape'][1],
                                                                        'row_min': 0,
                                                                        'row_max': data['img_shape'][0],
                                                                        'parent': [0]}}, 
                                        
                    {'x_min': float(0), 'x_max': float(compo['column_min']), 'y_min': float(center), 'y_max': float(center), 'axis': 0}])
                    if x_min > compo['column_min']:
                        x_min = compo['column_min']

            if not right_blocks:
                compo_list = [compo['row_min'] +
                                i for i in range(compo['height'] + 1)]
                compare_list = [i for i in range(img_height + 1)]
                cross = [i for i in compo_list if i in compare_list]
                # print(compo_list, child_list, cross)
                center = (cross[0] + cross[-1]) / 2
                if img_width - compo['column_max'] >= X_MIN:
                    coordinates.append([{'compo' : compo, "compare" : {'id': 0,
                                                                        'class': 'Compo',
                                                                        'height': data['img_shape'][0],
                                                                        'width': data['img_shape'][1],
                                                                        'column_min': 0,
                                                                        'column_max': data['img_shape'][1],
                                                                        'row_min': 0,
                                                                        'row_max': data['img_shape'][0],
                                                                        'parent': [0]}}, 
                    {'x_min': float(compo['column_max']), 'x_max': float(img_width), 'y_min': float(center), 'y_max': float(center), 'axis': 0}])
                    if x_min > img_width - compo['column_max']:
                        x_min = img_width - compo['column_max']

            else:
                child = min(
                    right_blocks, key=lambda item: item['column_min'])
                compo_list = [compo['row_min'] +
                                i for i in range(compo['height'] + 1)]
                child_list = [child['row_min'] +
                                i for i in range(child['height'] + 1)]
                cross = [i for i in compo_list if i in child_list]
                # print(compo_list, child_list, cross)
                center = (cross[0] + cross[-1]) / 2
                if child['column_min'] - compo['column_max'] >= X_MIN:
                    coordinates.append([{'compo' : compo, "compare" : child}, {'x_min': float(compo['column_max']), 'x_max': float(
                        child['column_min']), 'y_min': float(center), 'y_max': float(center), 'axis': 0}])
                    if x_min > child['column_min'] - compo['column_max']:
                        x_min = child['column_min'] - compo['column_max']

                right_blocks.clear()

            if top_blocks:
                child = max(top_blocks, key=lambda item: item['row_max'])
                # print(child, compo)
                compo_list = [compo['column_min'] +
                                i for i in range(compo['width'] + 1)]
                child_list = [child['column_min'] +
                                i for i in range(child['width'] + 1)]
                cross = [i for i in compo_list if i in child_list]
                # print(compo_list, child_list, cross)
                center = (cross[0] + cross[-1]) / 2
                if compo['row_min'] - child['row_max'] >= Y_MIN:
                    coordinates.append([{'compo' : compo, "compare" : child}, {'x_min': float(center), 'x_max': float(center), 'y_min': float(
                        child['row_max']), 'y_max': float(compo['row_min']), 'axis': 1}])
                    if y_min > compo['row_min'] - child['row_max']:
                        y_min = compo['row_min'] - child['row_max']

                top_blocks.clear()

            else:
                compo_list = [compo['column_min'] +
                                i for i in range(compo['width'] + 1)]
                compare_list = [i for i in range(img_width + 1)]
                cross = [i for i in compo_list if i in compare_list]
                # print(compo_list, child_list, cross)
                center = (cross[0] + cross[-1]) / 2
                if compo['row_min'] >= Y_MIN:
                    coordinates.append([{'compo' : compo, "compare" : {'id': 0,
                                                                        'class': 'Compo',
                                                                        'height': data['img_shape'][0],
                                                                        'width': data['img_shape'][1],
                                                                        'column_min': 0,
                                                                        'column_max': data['img_shape'][1],
                                                                        'row_min': 0,
                                                                        'row_max': data['img_shape'][0],
                                                                        'parent': [0]}}, 
                    {'x_min': float(center), 'x_max': float(center), 'y_min': float(0), 'y_max': float(compo['row_min']), 'axis': 1}])
                    if y_min > compo['row_min']:
                        y_min = compo['row_min']

            if bottom_blocks:
                child = min(bottom_blocks,
                            key=lambda item: item['row_min'])
                # print(child, compo)
                compo_list = [compo['column_min'] +
                                i for i in range(compo['width'] + 1)]
                child_list = [child['column_min'] +
                                i for i in range(child['width'] + 1)]
                cross = [i for i in compo_list if i in child_list]
                # print(compo_list, child_list, cross)
                center = (cross[0] + cross[-1]) / 2
                if child['row_min'] - compo['row_max'] >= Y_MIN:
                    coordinates.append([{'compo' : compo, "compare" : child}, {'x_min': float(center), 'x_max': float(center), 'y_min': float(
                        compo['row_max']), 'y_max': float(child['row_min']), 'axis': 1}])
                    if y_min > child['row_min'] - compo['row_max']:
                        y_min = child['row_min'] - compo['row_max']

                bottom_blocks.clear()

            else:
                compo_list = [compo['column_min'] +
                                i for i in range(compo['width'] + 1)]
                compare_list = [i for i in range(img_width + 1)]
                cross = [i for i in compo_list if i in compare_list]
                # print(compo_list, child_list, cross)
                center = (cross[0] + cross[-1]) / 2
                if img_height - compo['row_max'] >= Y_MIN:
                    coordinates.append([{'compo' : compo, "compare" : {'id': 0,
                                                                        'class': 'Compo',
                                                                        'height': data['img_shape'][0],
                                                                        'width': data['img_shape'][1],
                                                                        'column_min': 0,
                                                                        'column_max': data['img_shape'][1],
                                                                        'row_min': 0,
                                                                        'row_max': data['img_shape'][0],
                                                                        'parent': [0]}}, 
                    {'x_min': float(center), 'x_max': float(center), 'y_min': float(compo['row_max']), 'y_max': float(img_height), 'axis': 1}])
                    if y_min > img_height - compo['row_max']:
                        y_min = img_height - compo['row_max']

    # save the image
    # print(x_min, y_min)
    unique_values = set()
    unique_items = []

    for item in coordinates:
        item_dict = item[1]
        item_values = tuple(item_dict.values())
        if item_values not in unique_values:
            unique_values.add(item_values)
            unique_items.append(item)
    # coords = [dict(t) for t in {tuple(d[2].items()) for d in coordinates}]

    coords = unique_items
    
    return (x_min, y_min), coords


def draw_paddings(img, all_compos, shape, coords):
    x = Symbol('x')
    y = Symbol('y')

    x_min, y_min = shape
    # await asyncio.sleep(0)
    # print(img.shape, '---', np_img.shape)
    
    imageRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    original_image = Image.fromarray(imageRGB)

    draw = ImageDraw.Draw(original_image)

    font = ImageFont.truetype(dir + "/../UIED_3_3/Gidole-Regular.ttf", size=7)

    BASE = 0.5

    # print(os.getcwd())
    count = len(coords)
    loss = 0
    
    for i, coord in enumerate([c[1] for c in coords]):
        if coord['axis']:
            round_to_base = round((coord['y_max'] - coord['y_min']) / y_min * 2) * BASE
            # print((coord['y_max'] - coord['y_min']) / y_min, round_to_base)
            coords[i].append({"padding" : (coord['y_max'] - coord['y_min']) / y_min})
            if abs((coord['y_max'] - coord['y_min']) / y_min - round_to_base)  > 0.16: 
                loss += abs((coord['y_max'] - coord['y_min']) / y_min - round_to_base) / 0.25
                color = "red"
                
            else: color = "black"
            if (round_to_base).is_integer() and round_to_base:
                draw.line((coord['x_min'], coord['y_min'], coord['x_max'],
                          coord['y_max']), fill=color, width=1)
                draw.text((coord['x_min'] + 2, (coord['y_min'] + coord['y_max'])/2 - 4), str(
                    int(round_to_base) * y).replace('*', ''), fill="red", font=font)
            elif not (round_to_base).is_integer():
                draw.line((coord['x_min'], coord['y_min'], coord['x_max'],
                          coord['y_max']), fill=color, width=1)
                draw.text((coord['x_min'] + 2, (coord['y_min'] + coord['y_max'])/2 - 4),
                          str(round_to_base * y).replace('*', ''), fill="red", font=font)
        else:
            round_to_base = round((coord['x_max'] - coord['x_min']) / x_min * 2) * BASE
            
            coords[i].append({"padding" : (coord['x_max'] - coord['x_min']) / x_min})
            if abs((coord['x_max'] - coord['x_min']) / x_min - round_to_base) > 0.16:
                loss += abs((coord['x_max'] - coord['x_min']) / x_min - round_to_base) / 0.25
                color = "red"
            else: color = "black"
            # if round_to_base <= 1:
            #     print(round_to_base,  (coord['x_max'] - coord['x_min']) / x_min * BASE)
            if (round_to_base).is_integer() and round_to_base:
                draw.line((coord['x_min'], coord['y_min'], coord['x_max'],
                          coord['y_max']), fill=color, width=1)
                draw.text(((coord['x_min'] + coord['x_max'])/2 - 3, coord['y_min']), str(
                    int(round_to_base) * x).replace('*', ''), fill="blue", font=font)
            elif not (round_to_base).is_integer():
                draw.line((coord['x_min'], coord['y_min'], coord['x_max'],
                          coord['y_max']), fill=color, width=1)
                draw.text(((coord['x_min'] + coord['x_max'])/2 - 3, coord['y_min']),
                          str(round_to_base * x).replace('*', ''), fill="blue", font=font)
        # original_image.save(f'/../UIED_3_3/output/test_image_{FILENAME}.png')

        coords[i].append({'color' : color})
        
    coords.append({'x_min' : x_min, 'y_min' : y_min})
     
    # with open(dir + "/compare.pickle", "wb") as output_file:
    #         pickle.dump(coords, output_file)
            
    cons = 100 - (loss / count) * 100
    # print(draw)
    # print("coords\n", coords)
    
    return original_image, round(cons), all_compos, coords
