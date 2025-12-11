from flask import Flask, jsonify, request
from flask_cors import CORS
from app.util import load_artifacts, classify_image, get_class_labels

app = Flask(__name__)
CORS(app)

load_artifacts()

@app.route("/")
def index():
    return "The server is running...", 200

@app.route("/api/class_labels", methods=["GET"])
def class_labels_route():
    try:
        return jsonify(get_class_labels()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/classify-image", methods=["POST"])
def classify_image_route():
    try:
        if "image_data" not in request.form:
            return jsonify({"error": "Missing image_data parameter"}), 400
        
        image_data = request.form["image_data"]
        response = classify_image(image_data)
        
        return jsonify(response), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    app.run(debug=True)
