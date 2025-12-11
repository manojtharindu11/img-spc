import pywt
import cv2
import numpy as np

def w2d(img, mode='haar', level=1):
    # Convert to grayscale and normalize; handle both color and grayscale inputs
    if len(img.shape) == 2 or (len(img.shape) == 3 and img.shape[2] == 1):
        imArray = np.float32(img) / 255.0
    else:
        imArray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        imArray = np.float32(imArray) / 255.0
    
    # Compute wavelet coefficients
    coeffs = pywt.wavedec2(imArray, mode, level=level)
    
    # Zero out the approximation coefficients
    coeffs[0] *= 0
    
    # Reconstruct image
    imArray_H = pywt.waverec2(coeffs, mode)
    imArray_H = np.uint8(imArray_H * 255)
    
    return imArray_H