import cv2
from os.path import join as pjoin
import asyncio
import json
import numpy as np
import os
import detect_compo.lib_ip.ip_preprocessing as pre
import detect_compo.lib_ip.ip_draw as draw
import detect_compo.lib_ip.ip_detection as det
import detect_compo.lib_ip.file_utils as file
import detect_compo.lib_ip.Component as Compo
from config.CONFIG_UIED import Config

C = Config()


def nesting_inspection(org, grey, compos, ffl_block):
    '''
    Inspect all big compos through block division by flood-fill
    :param ffl_block: gradient threshold for flood-fill
    :return: nesting compos
    '''
    nesting_compos = []
    for i, compo in enumerate(compos):
        if compo.height > 50:
            replace = False
            clip_grey = compo.compo_clipping(grey)
            n_compos = det.nested_components_detection(clip_grey, org, grad_thresh=ffl_block, show=False)
            Compo.cvt_compos_relative_pos(n_compos, compo.bbox.col_min, compo.bbox.row_min)

            for n_compo in n_compos:
                if n_compo.redundant:
                    compos[i] = n_compo
                    replace = True
                    break
            if not replace:
                nesting_compos += n_compos
    return nesting_compos


async def compo_detection(input_img_path, id, output_root, uied_params,
                          resize_by_height=800, show=False, wai_key=100):
    name = id
    ip_root = file.build_directory(pjoin(output_root, "ip"))

    # *** Step 1 *** pre-processing: read img -> get binary map
    org, grey = pre.read_img(input_img_path, resize_by_height)
    binary = pre.binarization(org, grad_min=int(uied_params['min-grad']))

    # *** Step 2 *** element detection
    det.rm_line(binary, show=show, wait_key=wai_key)
    uicompos = det.component_detection(binary, min_obj_area=int(uied_params['min-ele-area']))

    # *** Step 3 *** results refinement
    uicompos = det.compo_filter(uicompos, min_area=int(uied_params['min-ele-area']), img_shape=binary.shape)
    uicompos = det.merge_intersected_compos(uicompos)
    det.compo_block_recognition(binary, uicompos)
    if uied_params['merge-contained-ele']:
        uicompos = det.rm_contained_compos_not_in_block(uicompos)
    Compo.compos_update(uicompos, org.shape)
    Compo.compos_containment(uicompos)

    # *** Step 4 ** nesting inspection: check if big compos have nesting element
    uicompos += nesting_inspection(org, grey, uicompos, ffl_block=uied_params['ffl-block'])
    Compo.compos_update(uicompos, org.shape)
    draw.draw_bounding_box(org, uicompos, show=show, name='merged compo', write_path=None, wait_key=wai_key)

    # *** Step 5 *** image inspection: recognize image -> remove noise in image -> binarize with larger threshold and reverse -> rectangular compo detection
    # if classifier is not None:
    #     classifier['Image'].predict(seg.clipping(org, uicompos), uicompos)
    #     draw.draw_bounding_box_class(org, uicompos, show=show)
    #     uicompos = det.rm_noise_in_large_img(uicompos, org)
    #     draw.draw_bounding_box_class(org, uicompos, show=show)
    #     det.detect_compos_in_img(uicompos, binary_org, org)
    #     draw.draw_bounding_box(org, uicompos, show=show)
    # if classifier is not None:
    #     classifier['Noise'].predict(seg.clipping(org, uicompos), uicompos)
    #     draw.draw_bounding_box_class(org, uicompos, show=show)
    #     uicompos = det.rm_noise_compos(uicompos)

    # *** Step 6 *** save detection result
    Compo.compos_update(uicompos, org.shape)
    file.save_corners_json(pjoin(ip_root, name + '.json'), uicompos)


    # print("[Compo Detection Completed ] Output: %s" % ( pjoin(ip_root, name + '.json')))
    
    # *** Step 7 *** element classification: all category classification
    # if classifier is not None:
    #     classifier['Elements'].predict([compo.compo_clipping(org) for compo in uicompos], uicompos)
        # img = draw.draw_bounding_box_class(org, uicompos, show=show, name='cls', write_path=None)

    
