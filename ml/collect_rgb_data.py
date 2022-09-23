#!/usr/bin/env python
# coding: utf-8

# In[3]:


import os
import numpy as np 
import pandas as pd
import glob 
import random
import cv2
import matplotlib.pyplot as plt
import multiprocessing


# In[4]:


def collect_image_list(path, num):
    
    img_list = glob.glob(path)
    random.shuffle(img_list)

    random_select_list = random.sample(img_list, num)
    random.shuffle(random_select_list)
    
    return random_select_list

def convert_tif_png(img):
    file_name = os.path.splitext(os.path.basename(img))[0]
    out_filename = f'{out_path}{file_name}.png'
    
    src = cv2.imread(img)

    cv2.imwrite(out_filename, src)
    
def process_image(img):
    convert_tif_png(img)


# In[6]:


random.seed(1)

out_path = './season11_rgb_data/'

if not os.path.isdir(out_path):
    os.makedirs(out_path)
    
image_dir = '/xdisk/cjfrost/egonzalez/PhytoOracle/stereoTopRGB/season11_tifs/'
os.chdir(image_dir)

image_path = '*/bin2tif_out/*.tif'
num = 2000
image_list = collect_image_list(image_path, num)


with multiprocessing.Pool(multiprocessing.cpu_count()) as p:
    p.map(process_image, image_list)


# In[44]:


# val_ratio = 0.10
# test_ratio = 0.10

# train, val, test = np.split(np.array(random_select_list),
#                                                           [int(len(random_select_list)* (1 - (val_ratio + test_ratio))), 
#                                                            int(len(random_select_list)* (1 - test_ratio))])

