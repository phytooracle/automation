#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd 
import numpy as np 
import shutil 
import glob
import random
import os
import cv2
import sklearn


# In[8]:


img_path = '/xdisk/ericlyons/data/emmanuelgonzalez/download_env/season10_flir/plotclips/'


# In[9]:


img_list = glob.glob(f'{img_path}*/*/*/*_NaN.tif')


# In[24]:


sample = random.sample(img_list, 500)


# In[25]:


# random.shuffle(sample)
# train_data = sample[:int((len(sample)+1)*.80)]
# valid_data = sample[int(len(sample)*.80+1):] 


# # Output train data set

# In[34]:


out_path = '/xdisk/ericlyons/data/emmanuelgonzalez/download_env/season10_flir/plotclips/phytooracle_paper_test/'

if not os.path.isdir(out_path):
    os.makedirs(out_path)
    
cnt = 0
change_dict = {}

for img in sample:
    cnt += 1
    
    date = img.split('/')[-1].split('_')[0]

    new_out = '_'.join([str(date), str(cnt),'_plotclip.png'])
    new_out_full = os.path.join(out_path, new_out)

    src = cv2.imread(img, cv2.IMREAD_ANYCOLOR | cv2.IMREAD_ANYDEPTH | cv2.IMREAD_GRAYSCALE)
    src = cv2.normalize(src, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
    
    cv2.imwrite(new_out_full, src)
    
print(f'Done, see output in {out_path}.')


# # Output validation data set

# In[30]:


out_path = '/xdisk/ericlyons/big_data/egonzalez/flir_object_detection/full_valid/'

if not os.path.isdir(out_path):
    os.makedirs(out_path)
    
cnt = 0
change_dict = {}

for img in valid_data:
    cnt += 1
    
    img_base = img.split('/')[-1]
    new_out = str(cnt) + '_plotclip.png'
    new_out_full = os.path.join(out_path, new_out)
    
#     change_dict[img_base] = {
#         'new_filename': new_out
#     }
    
    src = cv2.imread(img, cv2.IMREAD_ANYCOLOR | cv2.IMREAD_ANYDEPTH | cv2.IMREAD_GRAYSCALE)
    src = cv2.normalize(src, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
    
    cv2.imwrite(new_out_full, src)
    
print(f'Done, see output in {out_path}.')


# In[84]:


df = pd.DataFrame.from_dict(data=change_dict, orient='index')


# In[86]:


df.to_csv('/xdisk/ericlyons/big_data/egonzalez/flir_image_ref.csv')


# In[ ]:




