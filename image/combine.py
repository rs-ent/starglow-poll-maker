
import requests
from io import BytesIO
from PIL import Image, ImageOps
import numpy as np

def make_image(url_raw_a, url_raw_b):
    url_a = url_raw_a.split('/scale-to-width-down/')[0]
    url_b = url_raw_b.split('/scale-to-width-down/')[0]
    response_a = requests.get(url_a)
    response_b = requests.get(url_b)
    img_a = Image.open(BytesIO(response_a.content)).convert('RGBA')
    img_b = Image.open(BytesIO(response_b.content)).convert('RGBA')
    final_width, final_height = (1320, 660)
    target_size = (700, final_height)
    img_a_fit = ImageOps.fit(img_a, target_size, method=Image.Resampling.LANCZOS)
    img_b_fit = ImageOps.fit(img_b, target_size, method=Image.Resampling.LANCZOS)
    final_image = Image.new('RGBA', (final_width, final_height))
    final_image.paste(img_a_fit, (0, 0))
    paste_x = 620
    mask_array = np.ones((final_height, 700), dtype=np.uint8) * 255
    gradient = np.linspace(0, 255, 80, dtype=np.uint8)
    mask_array[:, :80] = np.tile(gradient, (final_height, 1))
    mask_right = Image.fromarray(mask_array, mode='L')
    final_image.paste(img_b_fit, (paste_x, 0), mask_right)
    file_path = 'blended_image.png'
    final_image.save(file_path)
    return file_path