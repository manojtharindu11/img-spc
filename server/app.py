from flask import Flask, jsonify, request
from app.util import load_artifacts, classify_image, get_class_labels

app = Flask(__name__)
load_artifacts()

@app.route("/")
def index():
    return "The server is running...", 200

@app.route("/api/class_labels", methods=["GET"])
def class_labels_route():
    return jsonify(get_class_labels()), 200

@app.route("/api/classify-image", methods=["POST"])
def classify_image_route():
    image_data = request.form["image_data"]
    response = classify_image(image_data)
    
    return jsonify(response), 200

if __name__ == "__main__":
    app.run(debug=True)
