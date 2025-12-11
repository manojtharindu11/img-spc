from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/")
def index():
    return "The server is running...", 200

@app.route("/classify-image", methods=["POST"])
def classify_image():
    pass

if __name__ == "__main__":
    app.run(debug=True)
