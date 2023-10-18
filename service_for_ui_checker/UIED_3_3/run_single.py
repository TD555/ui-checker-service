from os.path import join as pjoin
import cv2
import os
import numpy as np
import time
import asyncio
import sys
sys.path.insert(0, 'service_for_ui_checker/UIED_3_3')
from cnn.CNN import CNN
import detect_compo.ip_region_proposal as ip

from concurrent.futures import ThreadPoolExecutor
executor = ThreadPoolExecutor()


def resize_height_by_longest_edge(img, resize_length=800):
    height, width = img.shape[:2]
    if height > width:
        return resize_length
    else:
        return int(resize_length * (height / width))


def color_tips():
    color_map = {'Text': (0, 0, 255), 'Compo': (0, 255, 0), 'Block': (
        0, 255, 255), 'Text Content': (255, 0, 255)}
    board = np.zeros((200, 200, 3), dtype=np.uint8)

    board[:50, :, :] = (0, 0, 255)
    board[50:100, :, :] = (0, 255, 0)
    board[100:150, :, :] = (255, 0, 255)
    board[150:200, :, :] = (0, 255, 255)
    cv2.putText(board, 'Text', (10, 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
    cv2.putText(board, 'Non-text Compo', (10, 70),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
    cv2.putText(board, "Compo's Text Content", (10, 120),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
    cv2.putText(board, "Block", (10, 170),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
    # cv2.imshow('colors', board)


async def main(pil_image, id, parameters):
    key_params = {
        'min-grad': 2,
        'ffl-block': 3,
        'min-ele-area': parameters.get('min_area', 50),
        'merge-contained-ele': bool(parameters.get('merge_layers', 1)),
        'merge-line-to-paragraph': False,
        'remove-bar': True
    }

    input_image = np.array(pil_image)
    # height, width = input_image.shape[:2]
    input_img = input_image[:, :, ::-1].copy()

    path = os.path.realpath(__file__)
    dir = os.path.dirname(path)
    output_root = dir + '/data/output'

    resized_height = resize_height_by_longest_edge(input_img, resize_length=800)
    color_tips()

    is_ip = True
    is_ocr = True
    is_merge = True

    tasks = []

    if is_ocr:
        import detect_text.text_detection as text
        time.sleep(0.01)
        print('text')
        os.makedirs(pjoin(output_root, 'ocr'), exist_ok=True)
        tasks.append(text.text_detection(input_img, id, parameters['merge_texts'], output_root))

    if is_ip:
        import detect_compo.ip_region_proposal as ip
        print('compo')
        os.makedirs(pjoin(output_root, 'ip'), exist_ok=True)
        tasks.append(ip.compo_detection(input_img, id, output_root, key_params, resized_height))

    await asyncio.gather(tasks[0], tasks[1])
    
    if is_merge:
        import detect_merge.merge as merge
        print('merge')
        os.makedirs(pjoin(output_root, 'merge'), exist_ok=True)
        compo_path = pjoin(output_root, 'ip', id + '.json')
        ocr_path = pjoin(output_root, 'ocr', id + '.json')
        return merge.merge(input_img, id, compo_path, ocr_path, parameters.get('merge_text_compo', 0.38), pjoin(output_root, 'merge'),
                                 key_params['remove-bar'], key_params['merge-line-to-paragraph'])
        


if __name__ == '__main__':
    main()
    '''
        ele:min-grad: gradient threshold to produce binary map         
        ele:ffl-block: fill-flood threshold
        ele:min-ele-area: minimum area for selected elements 
        ele:merge-contained-ele: if True, merge elements contained in others
        text:max-word-inline-gap: words with smaller distance than the gap are counted as a line
        text:max-line-gap: lines with smaller distance than the gap are counted as a paragraph

        Tips:
        1. Larger *min-grad* produces fine-grained binary-map while prone to over-segment element to small pieces
        2. Smaller *min-ele-area* leaves tiny elements while prone to produce noises
        3. If not *merge-contained-ele*, the elements inside others will be recognized, while prone to produce noises
        4. The *max-word-inline-gap* and *max-line-gap* should be dependent on the input image size and resolution

        mobile: {'min-grad':4, 'ffl-block':5, 'min-ele-area':50, 'max-word-inline-gap':6, 'max-line-gap':1}
        web   : {'min-grad':3, 'ffl-block':5, 'min-ele-area':25, 'max-word-inline-gap':4, 'max-line-gap':4}
    '''
