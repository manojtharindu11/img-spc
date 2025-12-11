import joblib
import json
import base64
import cv2
from app.wavelet import w2d
import numpy as np
import os

__class_name_to_number = {}
__class_number_to_name = {}

__model = None

__artifacts_dir = os.path.join(os.path.dirname(__file__), '..', 'artifacts')
__test_dir = os.path.join(os.path.dirname(__file__), '..', 'test')

def get_base64_image():
    with open(os.path.join(__test_dir, "viratbase64.txt")) as f:
        return f.read()
    
def get_cv2_image_from_base64_string(b64str):
    encoded_data = b64str.split(",")[1]
    nparr = np.frombuffer(base64.b64decode(encoded_data), np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return img
    
def get_cropped_image_if_2_eyes(image_path, image_base64_data):
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
    
    if image_path:
        img = cv2.imread(image_path)
    else:
        img = get_cv2_image_from_base64_string(image_base64_data)

    # Bail early if image couldn't be loaded
    if img is None:
        return []
        
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    cropped_faces = []
    for (x, y, w, h) in faces:
        roi_gray = gray[y:y+h, x:x+w]
        roi_color = img[y:y+h, x:x+w]
        eyes = eye_cascade.detectMultiScale(roi_gray)
        if len(eyes) >= 2:
            cropped_faces.append(roi_color)

    return cropped_faces
    
def classify_image(base64_image_data, file_path=None):
    imgs = get_cropped_image_if_2_eyes(file_path, base64_image_data)

    if not imgs:
        return "No face with 2 eyes detected"

    results = []
    for img in imgs:
        # Ensure we have a 3-channel image for downstream processing
        if len(img.shape) == 2 or (len(img.shape) == 3 and img.shape[2] == 1):
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        
        scaled_raw_img = cv2.resize(img, (32, 32))
        img_har = w2d(img, 'db1', 5)
        scaled_img_har = cv2.resize(img_har, (32, 32))
        
        # Reshape both images: color is 3072 (32*32*3), grayscale is 1024 (32*32)
        combined_img = np.vstack((scaled_raw_img.reshape(32*32*3, 1), scaled_img_har.reshape(32*32, 1)))
        
        len_image_array = 32 * 32 * 3 + 32 * 32
        
        final = combined_img.reshape(1, len_image_array).astype(float)
        
        pred_num = __model.predict(final)[0]
        pred_probs = np.round(__model.predict_proba(final) * 100, 2).tolist()[0]
        
        results.append({
            "class": __class_number_to_name[pred_num],
            "class_probability": pred_probs,
            "class_labels": list(__class_number_to_name.values())
        })

    return results
        
def load_artifacts():
    print("Loading saved artifacts....")
    global __class_name_to_number
    global __class_number_to_name
    
    with open(os.path.join(__artifacts_dir, "class_dictionary.json"), "r") as f:
        __class_name_to_number = json.load(f)
        __class_number_to_name = {v: k for k, v in __class_name_to_number.items()}
        
    global __model
    
    if __model is None:
        with open(os.path.join(__artifacts_dir, "saved_model.pkl"), "rb") as f:
            __model = joblib.load(f)
            
    print("Loading saved artifacts.... done.")
    
def get_class_labels():
    # Return class labels (human-readable names)
    return list(__class_number_to_name.values())
    
if __name__ == "__main__":
    load_artifacts()
    print(classify_image(get_base64_image()))
