from collections import defaultdict
import json
import asyncio
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import base64
import io


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


def preprocess(compos, coords):
    
    compos_rels:dict = {}
    all_compos:list
    unique_compos:list
    layers_compos:dict = defaultdict(list)
    
    all_compos = remove_duplicates(compos['compos'])
    shape = compos['img_shape']
    
    layers = defaultdict(list)
    for compo in all_compos:
        i = 1
        while 1:
            if len(compo['parent']) == i :
                layers[i].extend([rel for rel in coords[:-1] if compo == rel[0]['compo'] and len(rel[0]['compare']['parent']) <=i \
                    or compo == rel[0]['compare'] and len(rel[0]['compo']['parent']) <=i])
                break
            else: 
                i += 1
                continue
            
    unique_layers = {}
    
    for key in layers.keys():
        unique_list = [list(t) for t in {tuple(json.dumps(d, sort_keys=True) for d in lst) for lst in layers[key]}]

        # Convert JSON strings back to dictionaries
        unique_list = [[json.loads(item) for item in sublist] for sublist in unique_list]
        unique_layers[key] = unique_list.copy()
        
    layer_compos = []

    for key in unique_layers.keys():
        for rel in unique_layers[key]:
            if len(rel[0]['compo']['parent']) == key:
                layers_compos[key].append(rel[0]['compo'])
            if len(rel[0]['compare']['parent']) == key:
                layers_compos[key].append(rel[0]['compare'])
                
            layer_compos.extend([rel[0]['compo'], rel[0]['compare']])

    unique_compos = remove_duplicates(layer_compos)

    for key in layers_compos.keys():
        layers_compos[key] = remove_duplicates(layers_compos[key])
        

    for compo in unique_compos:
        compos_rels[compo['id']] = defaultdict(list)
        
    for compo in unique_compos:
        # print(compo)
        for key in unique_layers.keys():
            for rel in unique_layers[key]:
                # print(rel)
                # print(rel[-2]['padding'])
                if compo == rel[0]['compo'] and not rel[1]['axis']:
                    if int(rel[1]['x_max']) == compo['column_min'] and rel[0]['compare']['id'] not in compos_rels[compo['id']]['left']:
                        compos_rels[compo['id']]['left'].append(rel[0]['compare']['id'])
                        compos_rels[compo['id']]['left_pad'].append(rel[2]['padding'])
                    if int(rel[1]['x_max']) == compo['column_max'] and compo['id'] not in compos_rels[rel[0]['compare']['id']]['right']:
                        compos_rels[rel[0]['compare']['id']]['right'].append(compo['id'])
                        compos_rels[rel[0]['compare']['id']]['right_pad'].append(rel[2]['padding'])
                        
                    if int(rel[1]['x_min']) == compo['column_max'] and rel[0]['compare']['id'] not in compos_rels[compo['id']]['right']: 
                        compos_rels[compo['id']]['right'].append(rel[0]['compare']['id'])
                        compos_rels[compo['id']]['right_pad'].append(rel[2]['padding'])
                    if int(rel[1]['x_min']) == compo['column_min'] and compo['id'] not in compos_rels[rel[0]['compare']['id']]['left']:
                        compos_rels[rel[0]['compare']['id']]['left'].append(compo['id'])
                        compos_rels[rel[0]['compare']['id']]['left_pad'].append(rel[2]['padding'])
                        
                if compo == rel[0]['compare'] and not rel[1]['axis']:
                    if int(rel[1]['x_max']) == compo['column_min'] and rel[0]['compo']['id'] not in compos_rels[compo['id']]['left']:
                        compos_rels[compo['id']]['left'].append(rel[0]['compo']['id'])
                        compos_rels[compo['id']]['left_pad'].append(rel[2]['padding'])
                    if int(rel[1]['x_max']) == compo['column_max'] and compo['id'] not in compos_rels[rel[0]['compo']['id']]['right']:
                        compos_rels[rel[0]['compo']['id']]['right'].append(compo['id'])
                        compos_rels[rel[0]['compo']['id']]['right_pad'].append(rel[2]['padding'])
                        
                    if int(rel[1]['x_min']) == compo['column_max'] and rel[0]['compo']['id'] not in compos_rels[compo['id']]['right']: 
                        compos_rels[compo['id']]['right'].append(rel[0]['compo']['id'])
                        compos_rels[compo['id']]['right_pad'].append(rel[2]['padding'])
                    if int(rel[1]['x_min']) == compo['column_min'] and compo['id'] not in compos_rels[rel[0]['compo']['id']]['left']:
                        compos_rels[rel[0]['compo']['id']]['left'].append(compo['id'])
                        compos_rels[rel[0]['compo']['id']]['left_pad'].append(rel[2]['padding'])
                        
                if compo == rel[0]['compo'] and rel[1]['axis']:
                    if int(rel[1]['y_max']) == compo['row_min'] and rel[0]['compare']['id'] not in compos_rels[compo['id']]['top']:
                        compos_rels[compo['id']]['top'].append(rel[0]['compare']['id'])
                        compos_rels[compo['id']]['top_pad'].append(rel[2]['padding'])
                    if int(rel[1]['y_max']) == compo['row_max'] and compo['id'] not in compos_rels[rel[0]['compare']['id']]['bottom']:
                        compos_rels[rel[0]['compare']['id']]['bottom'].append(compo['id'])
                        compos_rels[rel[0]['compare']['id']]['bottom_pad'].append(rel[2]['padding'])
                        
                    if int(rel[1]['y_min']) == compo['row_max'] and rel[0]['compare']['id'] not in compos_rels[compo['id']]['bottom']:
                        compos_rels[compo['id']]['bottom'].append(rel[0]['compare']['id'])
                        compos_rels[compo['id']]['bottom_pad'].append(rel[2]['padding'])
                    if int(rel[1]['y_min']) == compo['row_min'] and compo['id'] not in compos_rels[rel[0]['compare']['id']]['top']:
                        compos_rels[rel[0]['compare']['id']]['top'].append(compo['id'])
                        compos_rels[rel[0]['compare']['id']]['top_pad'].append(rel[2]['padding'])
                
                if compo == rel[0]['compare'] and rel[1]['axis']:
                    if int(rel[1]['y_max']) == compo['row_min'] and rel[0]['compo']['id'] not in compos_rels[compo['id']]['top']:
                        compos_rels[compo['id']]['top'].append(rel[0]['compo']['id'])
                        compos_rels[compo['id']]['top_pad'].append(rel[2]['padding'])
                    if int(rel[1]['y_max']) == compo['row_max'] and compo['id'] not in compos_rels[rel[0]['compo']['id']]['bottom']:
                        compos_rels[rel[0]['compo']['id']]['bottom'].append(compo['id'])
                        compos_rels[rel[0]['compo']['id']]['bottom_pad'].append(rel[2]['padding'])
                        
                    if int(rel[1]['y_min']) == compo['row_max'] and rel[0]['compo']['id'] not in compos_rels[compo['id']]['bottom']: 
                        compos_rels[compo['id']]['bottom'].append(rel[0]['compo']['id'])
                        compos_rels[compo['id']]['bottom_pad'].append(rel[2]['padding'])
                    if int(rel[1]['y_min']) == compo['row_min'] and compo['id'] not in compos_rels[rel[0]['compo']['id']]['top']:
                        compos_rels[rel[0]['compo']['id']]['top'].append(compo['id'])
                        compos_rels[rel[0]['compo']['id']]['top_pad'].append(rel[2]['padding'])
    
    if 0 in compos_rels.keys():
        del compos_rels[0]  
     
    x_min, y_min = coords[-1].values()

    return x_min, y_min, shape, all_compos, compos_rels, unique_compos, layers_compos

# Check if paddings are not correct in every layer

def update_childs(compo_id:int, dir:str, count:float, x_min, y_min, unique_compos):
    
    
    childs = []
    
    for i, compo in enumerate(unique_compos):
        if compo['id'] == compo_id:
            if dir == 'h':
                unique_compos[i]['column_min'] += count * x_min
                unique_compos[i]['column_max'] += count * x_min
            elif dir == 'v':
                unique_compos[i]['row_min'] += count * y_min
                unique_compos[i]['row_max'] += count * y_min
            if 'child' in compo.keys():
                childs = list(set(compo['child']))
            else: childs = []
            # print(compo_id, childs, unique_compos[i])

    
    for child_id in childs:
        update_childs(child_id, dir, count, x_min, y_min, unique_compos)
        
        
def update_compos(count:float, compo_id:int, compares1:list, compares2:list, axis:int, x_min, y_min, unique_compos, compos_rels):
    
    # print([compare['id'] for compare in compares1], [compare['id'] for compare in compares2])
    if axis:
            # print(count)
            # vertical
            for compare in compares1:
                # print(compo_id, compare['id'])
                if compare['id'] in compos_rels[compo_id]['top']:
                    compos_rels[compo_id]['top_pad'][compos_rels[compo_id]['top'].index(compare['id'])] += count
                if compare['id'] in compos_rels.keys() and compo_id in compos_rels[compare['id']]['bottom']:
                    compos_rels[compare['id']]['bottom_pad'][compos_rels[compare['id']]['bottom'].index(compo_id)] += count
                # update_layers(compo_id, compare['id'], compares1, compares2, count, axis)
                
            for compare in compares2:
                # print(compo_id, compare['id'])
                if compare['id'] in compos_rels[compo_id]['bottom']:
                    compos_rels[compo_id]['bottom_pad'][compos_rels[compo_id]['bottom'].index(compare['id'])] -= count
                if compare['id'] in compos_rels.keys() and compo_id in compos_rels[compare['id']]['top']:
                    compos_rels[compare['id']]['top_pad'][compos_rels[compare['id']]['top'].index(compo_id)] -= count
                # update_layers(compo_id, compare['id'], compares1, compares2, count, axis)
                
            update_childs(compo_id, "v", count, x_min, y_min, unique_compos) 
            
    else:
            # print(count)
            # horizontal
            for compare in compares1:
                # print(compo_id, compare['id'])
                if compare['id'] in compos_rels[compo_id]['left']:
                    compos_rels[compo_id]['left_pad'][compos_rels[compo_id]['left'].index(compare['id'])] += count
                if compare['id'] in compos_rels.keys() and compo_id in compos_rels[compare['id']]['right']:
                    compos_rels[compare['id']]['right_pad'][compos_rels[compare['id']]['right'].index(compo_id)] += count
                # update_layers(compo_id, compare['id'], compares1, compares2, count, axis)
                
            for compare in compares2:
                # print(compo_id, compare['id'])
                if compare['id'] in compos_rels[compo_id]['right']:
                    compos_rels[compo_id]['right_pad'][compos_rels[compo_id]['right'].index(compare['id'])] -= count
                if compare['id'] in compos_rels.keys() and compo_id in compos_rels[compare['id']]['left']:
                    compos_rels[compare['id']]['left_pad'][compos_rels[compare['id']]['left'].index(compo_id)] -= count
                # update_layers(compo_id, compare['id'], compares1, compares2, count, axis)
            
            update_childs(compo_id, "h", count, x_min, y_min, unique_compos)
 
 
def fix_paddings(compo_id, axis, args):
    BASE = 0.5
    THRESH = 0.16
    
    x_min, y_min, shape, all_compos, compos_rels, unique_compos, layers_compos = args
    
    if not axis:
        
        left_compares = defaultdict(list)
        right_compares = defaultdict(list)
    
        for i, compare_id in enumerate(compos_rels[compo_id]['left']):
            for c in unique_compos:
                if c['id'] == compare_id:
                    left_compares['compare'].append(c)
                    left_compares['padding'].append(compos_rels[compo_id]['left_pad'][i])
                    
        for i, compare_id in enumerate(compos_rels[compo_id]['right']):
            for c in unique_compos:
                if c['id'] == compare_id:
                    right_compares['compare'].append(c)
                    right_compares['padding'].append(compos_rels[compo_id]['right_pad'][i])
        
        # print(left_compares['padding'], right_compares['padding'])

        left_count = 0
        right_count = 0
        
        #left
        
        while True:
            left_count += 0.01
            
            for padd in [left - left_count for left in left_compares['padding']] + [right + left_count for right in right_compares['padding']]:
                
                # print(left_count, abs(round(padd * 2) * BASE - padd))
                if abs(round(padd * 2) * BASE - padd) > THRESH:
                    break
                    
            else: 
                break
            if left_count >=x_min:
                left_count = 0.01
                break
            continue
        
        #right
        
        if left_count != 0.01:
            while True:
                right_count += 0.01
                
                for padd in [left + right_count for left in left_compares['padding']] + [right - right_count for right in right_compares['padding']]:
                    
                    # print(right_count, abs(round(padd * 2) * BASE - padd))
                    if abs(round(padd * 2) * BASE - padd) > THRESH:
                        break
                        
                else: break
                if right_count >=x_min:
                    right_count = 0.01
                    break
                continue
        
            count = [left_count, right_count]
            # print(compo_id, count)
            index = count.index(max(count))
            
        else: 
            count = [left_count]
            index = 0
        
        if not index:
            update_compos(-left_count, compo_id, left_compares['compare'], right_compares['compare'], axis, x_min, y_min, unique_compos, compos_rels)
            # print('yes')
        else: 
            update_compos(right_count, compo_id, left_compares['compare'], right_compares['compare'], axis, x_min, y_min, unique_compos, compos_rels)
            # print('yes')
      
    else:
        
        top_compares = defaultdict(list)
        bottom_compares = defaultdict(list)
    
        for i, compare_id in enumerate(compos_rels[compo_id]['top']):
            for c in unique_compos:
                if c['id'] == compare_id:
                    top_compares['compare'].append(c)
                    top_compares['padding'].append(compos_rels[compo_id]['top_pad'][i])
                    
        for i, compare_id in enumerate(compos_rels[compo_id]['bottom']):
            for c in unique_compos:
                if c['id'] == compare_id:
                    bottom_compares['compare'].append(c)
                    bottom_compares['padding'].append(compos_rels[compo_id]['bottom_pad'][i])
        
        # print(top_compares['padding'], bottom_compares['padding'])

        # print(top_compares, bottom_compares)
        top_count = 0
        bottom_count = 0
        
        #up
        
        while True:
            top_count += 0.01
            
            for padd in [top - top_count for top in top_compares['padding']] + [bottom + top_count for bottom in bottom_compares['padding']]:
                
                # print(top_count, abs(round(padd * 2) * BASE - padd))
                if abs(round(padd * 2) * BASE - padd) > THRESH:
                    break
                    
            else: break
            if top_count >= y_min:
                top_count = 0.01
                break
            continue
        
        #down
        
        if top_count != 0.01:
            while True:
                bottom_count += 0.01
                
                for padd in [top + bottom_count for top in top_compares['padding']] + [bottom - bottom_count for bottom in bottom_compares['padding']]:
                    
                    # print(bottom_count, abs(round(padd * 2) * BASE - padd))
                    if abs(round(padd * 2) * BASE - padd) > THRESH:
                        break
                        
                else: break
                if bottom_count >=y_min:
                    bottom_count = 0.01
                    break
                continue
            
            count = [top_count, bottom_count]
            index = count.index(max(count))
        
        else:
            count = [top_count]
            index = 0
        
        # if compo_id == 67:
                # print(compo_id, count)
                
        if not index:
            update_compos(-top_count, compo_id, top_compares['compare'], bottom_compares['compare'], axis, x_min, y_min, unique_compos, compos_rels)
            # print(compos_rels[67])
            
        else: 
            update_compos(bottom_count, compo_id, top_compares['compare'], bottom_compares['compare'], axis, x_min, y_min, unique_compos, compos_rels) 
            # print('yes')
     

def correct(args):
    BASE = 0.5
    THRESH = 0.16
    x_min, y_min, shape, all_compos, compos_rels, unique_compos, layers_compos = args
    
    for i in range(100):
        all_correct = []
        for key in list(layers_compos.keys()):
            for compo in layers_compos[key]: 
                if compo['id']:
                    # print(compo['id'])
                    
                                
                    compo_left = compos_rels[compo['id']]['left_pad']
                    compo_right = compos_rels[compo['id']]['right_pad']
                    paddings0 = compo_left + compo_right
                    
                    for padding in paddings0:
                        if abs(round(padding * 2) * BASE - padding) > THRESH:
                            fix_paddings(compo['id'], 0, args)
                            all_correct.append(False)
                        
                    else: all_correct.append(True)
                        
                        
                    compo_top = compos_rels[compo['id']]['top_pad']
                    compo_bottom = compos_rels[compo['id']]['bottom_pad']
                    
                    paddings1 = compo_top + compo_bottom

                        
                    for padding in paddings1:
                        # print(paddings1)
                        if abs(round(padding * 2) * BASE - padding) > THRESH:
                            fix_paddings(compo['id'], 1, args)
                            all_correct.append(False)
                    
                    else: all_correct.append(True)
                    
        if np.all(all_correct):
            break
        
        
def get_correct(image, args):
    
    x_min, y_min, shape, all_compos, compos_rels, unique_compos, layers_compos = args
    
    correct(args)
    for compo in unique_compos:
        if compo['id'] == 0:
            unique_compos.remove(compo)
    
    # # Define the float coordinates of the bounding boxes

    original_boxes = [
        [compo['column_min'], compo['row_min'], compo['column_max'], compo['row_max']] for compo in all_compos
    ]

    changed_boxes = [
        [compo['column_min'], compo['row_min'], compo['column_max'], compo['row_max']] for compo in unique_compos
    ]



    fig, ax = plt.subplots()
    ax.imshow(image)
    ax.axis('off')



    for box in original_boxes:
        x_min, y_min, x_max, y_max = box
        x_min, y_min, x_max, y_max = x_min * image.shape[1]/shape[1], y_min * image.shape[0]/shape[0], x_max * image.shape[1]/shape[1], y_max * image.shape[0]/shape[0]
        rect = patches.Rectangle((x_min, y_min), x_max - x_min, y_max - y_min, linewidth=0.5, edgecolor='r', facecolor='none')
        ax.add_patch(rect)


    for box in changed_boxes:
        x_min, y_min, x_max, y_max = box
        x_min, y_min, x_max, y_max = x_min * image.shape[1]/shape[1], y_min * image.shape[0]/shape[0], x_max * image.shape[1]/shape[1], y_max * image.shape[0]/shape[0]
        rect = patches.Rectangle((x_min, y_min), x_max - x_min, y_max - y_min, linewidth=0.5, edgecolor='g', facecolor='none')
        ax.add_patch(rect)


    # Save the modified image
    buffer = io.BytesIO()
    
    matplotlib.use('Agg')
    if image.shape[0] > image.shape[1]:
        plt.savefig(buffer, format='png',bbox_inches='tight', pad_inches=0, dpi=plt.rcParams['figure.dpi'] * image.shape[0]/image.shape[1])
    else: plt.savefig(buffer, format='png', bbox_inches='tight', pad_inches=0, dpi=plt.rcParams['figure.dpi'] * image.shape[1]/image.shape[0])

    plt.show()
    buffer.seek(0)

    # Convert the image buffer to a Base64-encoded string
    encoded_string = base64.b64encode(buffer.read()).decode('utf-8')
    
    buffer.close()
    
    # Close the figure
    plt.close(fig)
    
    return encoded_string