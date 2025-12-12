# Sports Person Image Classifier

A machine learning project that classifies images of sports personalities using computer vision and deep learning techniques.

## Project Structure

- **model/** - ML model training and data processing

  - `sports_person_classifier.ipynb` - Jupyter notebook for model training
  - `image_scraping.py` - Script for collecting training images
  - `datasets/` - Training images and cropped faces
  - `opencv/` - Haar cascade files for face detection

- **server/** - Flask backend server

  - `app.py` - Main server application
  - `app/` - Server utilities and helper functions
  - `artifacts/` - Trained model and class dictionary

- **ui/** - Frontend web interface
  - `app.html` - Main web page
  - `app.js` - Client-side logic
  - `app.css` - Styling

## Setup

### Model Training

```bash
cd model
pip install -r requirements.txt
# Run the Jupyter notebook to train the model
```

### Server

```bash
cd server
pip install -r requirements.txt
python app.py
```

### UI

Open `ui/app.html` in a web browser or serve it using a local web server.

## Classified Athletes

- Lionel Messi
- Maria Sharapova
- Roger Federer
- Serena Williams
- Virat Kohli

## Technologies

- Python
- OpenCV (Face Detection)
- Machine Learning
- Flask
- HTML/CSS/JavaScript
