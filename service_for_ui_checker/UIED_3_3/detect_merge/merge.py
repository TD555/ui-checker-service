import json
import cv2
import numpy as np
from os.path import join as pjoin
import os
import asyncio
import shutil
import config.CONFIG_UIED as conf
from detect_merge.Element import Element
from paddings import set_paddings as padding


def show_elements(org_img, eles, show=False, win_name='element', wait_key=0, shown_resize=None, line=2):
    color_map = conf.Config().COLOR
    img = org_img.copy()
    for ele in eles:
        color = color_map[ele.category]
        ele.visualize_element(img, color, line)
    img_resize = img
    if shown_resize is not None:
        img_resize = cv2.resize(img, shown_resize)
    if show:
        cv2.imwrite("test_imgs/filename.png", img_resize)
            
    return img_resize


def save_elements(output_file, elements, img_shape):
    components = {'compos': [], 'img_shape': img_shape}
    for i, ele in enumerate(elements):
        c = ele.wrap_info()
        # c['id'] = i
        components['compos'].append(c)
    json.dump(components, open(output_file, 'w'), indent=4)
    return components


def reassign_ids(elements):
    for i, element in enumerate(elements):
        element.id = i + 1


def refine_texts(texts):
    refined_texts = []
    for text in texts:
        # remove potential noise
        if len(text.text_content) >= 1:
            refined_texts.append(text)
    return refined_texts


def merge_text_line_to_paragraph(elements, max_line_gap=5):
    texts = []
    non_texts = []
    for ele in elements:
        if ele.category == 'Text':
            texts.append(ele)
        else:
            non_texts.append(ele)

    changed = True
    while changed:
        changed = False
        temp_set = []
        for text_a in texts:
            merged = False
            for text_b in temp_set:
                inter_area, _, _, _ = text_a.calc_intersection_area(
                    text_b, bias=(0, max_line_gap))
                if inter_area > 0:
                    text_b.element_merge(text_a)
                    merged = True
                    changed = True
                    break
            if not merged:
                temp_set.append(text_a)
        texts = temp_set.copy()
    return non_texts + texts


def refine_elements(compos, texts, merge_text_compo, intersection_bias=(2, 2), containment_ratio=0.7):
    '''
    1. remove compos contained in text
    2. remove compos containing text area that's too large
    3. store text in a compo if it's contained by the compo as the compo's text child element
    '''
    elements = []
    contained_texts = []
    for compo in compos:
        is_valid = True
        text_area = 0
        for text in texts:
            inter, iou, ioa, iob = compo.calc_intersection_area(
                text, bias=intersection_bias)
            if inter > 0:
                # the non-text is contained in the text compo
                if ioa >= merge_text_compo:
                    is_valid = False
                    # break
                text_area += inter
                # the text is contained in the non-text compo
                if iob >= 0.1 and compo.category != 'Block':
                    # print(text.text_content)
                    elements.append(text)
        if is_valid and text_area / compo.area < 0.8:
            # for t in contained_texts:
            #     t.parent_id = compo.id
            # compo.children += contained_texts
            elements.append(compo)

    # elements += texts
    for text in texts:
        if text not in contained_texts:
            elements.append(text)
    return elements


def check_containment(elements):
    for i in range(len(elements) - 1):
        for j in range(i + 1, len(elements)):
            relation = elements[i].element_relation(elements[j], bias=(2, 2))
            if relation == -1:
                elements[j].children.append(elements[i])
                elements[i].parent_id = elements[j].id
            if relation == 1:
                elements[i].children.append(elements[j])
                elements[j].parent_id = elements[i].id


def remove_top_bar(elements, img_height):
    new_elements = []
    max_height = img_height * 0.04
    for ele in elements:
        if ele.row_min < 10 and ele.height < max_height:
            continue
        new_elements.append(ele)
    return new_elements


def remove_bottom_bar(elements, img_height):
    new_elements = []
    for ele in elements:
        # parameters for 800-height GUI
        if ele.row_min > 750 and 20 <= ele.height <= 30 and 20 <= ele.width <= 30:
            continue
        new_elements.append(ele)
    return new_elements


def compos_clip_and_fill(clip_root, org, compos):
    def most_pix_around(pad=6, offset=2):
        '''
        determine the filled background color according to the most surrounding pixel
        '''
        up = row_min - pad if row_min - pad >= 0 else 0
        left = col_min - pad if col_min - pad >= 0 else 0
        bottom = row_max + pad if row_max + \
            pad < org.shape[0] - 1 else org.shape[0] - 1
        right = col_max + pad if col_max + \
            pad < org.shape[1] - 1 else org.shape[1] - 1
        most = []
        for i in range(3):
            val = np.concatenate((org[up:row_min - offset, left:right, i].flatten(),
                                  org[row_max + offset:bottom,
                                      left:right, i].flatten(),
                                  org[up:bottom, left:col_min -
                                      offset, i].flatten(),
                                  org[up:bottom, col_max + offset:right, i].flatten()))
            most.append(int(np.argmax(np.bincount(val))))
        return most

    if os.path.exists(clip_root):
        shutil.rmtree(clip_root)
    os.mkdir(clip_root)

    bkg = org.copy()
    cls_dirs = []
    for compo in compos:
        cls = compo['class']
        if cls == 'Background':
            compo['path'] = pjoin(clip_root, 'bkg.png')
            continue
        c_root = pjoin(clip_root, cls)
        c_path = pjoin(c_root, str(compo['id']) + '.jpg')
        compo['path'] = c_path
        if cls not in cls_dirs:
            os.mkdir(c_root)
            cls_dirs.append(cls)

        position = compo['position']
        col_min, row_min, col_max, row_max = position['column_min'], position[
            'row_min'], position['column_max'], position['row_max']
        cv2.imwrite(c_path, org[row_min:row_max, col_min:col_max])
        # Fill up the background area
        cv2.rectangle(bkg, (col_min, row_min),
                      (col_max, row_max), most_pix_around(), -1)
    cv2.imwrite(pjoin(clip_root, 'bkg.png'), bkg)


def scale_compos(data, x_scale, y_scale):
    for item in data['compos']:
        item['column_min'] = int(item['column_min'] * x_scale)
        item['column_max'] = int(item['column_max'] * x_scale)
        item['row_min'] = int(item['row_min'] * y_scale)
        item['row_max'] = int(item['row_max'] * y_scale)
        item['height'] = int(item['height'] * y_scale)
        item['width'] = int(item['width'] * x_scale)
            

def scale_texts(data, x_scale, y_scale):
    for item in data['texts']:
        item['column_min'] = int(item['column_min'] * x_scale)
        item['column_max'] = int(item['column_max'] * x_scale)
        item['row_min'] = int(item['row_min'] * y_scale)
        item['row_max'] = int(item['row_max'] * y_scale)
        item['height'] = int(item['height'] * y_scale)
        item['width'] = int(item['width'] * x_scale)         
            
            
def merge(img, id, compo_path, text_path, merge_text_compo, merge_root=None, is_paragraph=False, is_remove_bar=True, show=False, wait_key=0):

    compo_json = json.load(open(compo_path, 'r'))
    text_json = json.load(open(text_path, 'r'))

    scale_compos(compo_json, x_scale=img.shape[1] / compo_json['img_shape'][1], y_scale=img.shape[0] / compo_json['img_shape'][0])
    scale_texts(text_json, x_scale=img.shape[1] / text_json['img_shape'][1], y_scale=img.shape[0] / text_json['img_shape'][0])
    
    # load text and non-text compo
    ele_id = 0
    compos = []
    for compo in compo_json['compos']:
        element = Element(ele_id, (compo['column_min'], compo['row_min'],
                          compo['column_max'], compo['row_max']), compo['class'])
        compos.append(element)
        ele_id += 1

    texts = []
    for text in text_json['texts']:
        element = Element(ele_id, (text['column_min'], text['row_min'],
                          text['column_max'], text['row_max']), 'Text', text_content=text['content'])
        texts.append(element)
        ele_id += 1

    # if (compo_json['img_shape'] != text_json['img_shape']) and compo_json['img_shape']:
    #     resize_ratio = compo_json['img_shape'][0] / text_json['img_shape'][0]
    #     for text in texts:
    #         text.resize(resize_ratio)

    # if compo_json['img_shape']:
    #     img_resize = cv2.resize(
    #         img, (compo_json['img_shape'][1], compo_json['img_shape'][0]))
    # else:
    #     img_resize = cv2.resize(
    #         img, (text_json['img_shape'][1], text_json['img_shape'][0]))

    # show_elements(img, texts + compos, show=True,
    #               win_name='all elements before merging', wait_key=wait_key)

    texts = refine_texts(texts)
    elements = refine_elements(compos, texts, merge_text_compo)
    reassign_ids(elements)

    board = show_elements(img, elements, show=True,
                          win_name='elements after merging', wait_key=wait_key)

    save_elements(pjoin(merge_root, id + '.json'), elements, img.shape)

    print(2400 /img.shape[1], 1800 /img.shape[0], img.shape)
    all_compos = padding.__main__(id, x_scale = round(3400 /img.shape[1]) , y_scale = round(2000 /img.shape[0]))
    # print("all compos\n", all_compos)
    shape, coords = padding.find_coords(all_compos)
    return padding.draw_paddings(np.array(board), all_compos, shape, coords) + (text_json,)

