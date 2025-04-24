from flask import Flask, render_template, request, jsonify
import os
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
import requests

app = Flask(__name__, template_folder="../templates", static_folder='../static')

# Load the model
model = load_model(r'C:\Users\RAMYASREEKASULA\Downloads\major project07\uploads\nutrition.h5')
print("Loaded model from disk")


@app.route('/')
def home():
    """Render the home page."""
    return render_template('index.html')


@app.route('/image', methods=['GET', 'POST'])
def image1():
    """Render the image upload page."""
    return render_template("image.html")

@app.route('/about', methods=['GET', 'POST'])
def about():
    """Render the about page."""
    return render_template("about.html")

@app.route('/service', methods=['GET', 'POST'])
def service():
    """Render the about page."""
    return render_template("service.html")

@app.route('/team', methods=['GET', 'POST'])
def team():
    """Render the about page."""
    return render_template("team.html")

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    """Render the about page."""
    return render_template("contact.html")

@app.route('/predict', methods=['GET', 'POST'])
def launch():
    """Handle prediction and nutrition API call."""
    if request.method == 'POST':
        f = request.files['file']
        
        # Set the basepath
        basepath = os.path.dirname(__file__)
        
        # Ensure the 'upload' directory exists
        upload_dir = os.path.join(basepath, "upload")
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
        
        # Save the file in the 'upload' directory
        filepath = os.path.join(upload_dir, f.filename)
        f.save(filepath)

        # Process the image
        img = image.load_img(filepath, target_size=(64, 64))
        x = image.img_to_array(img)
        x = np.expand_dims(x, axis=0)

        # Predict the class
        pred = np.argmax(model.predict(x), axis=1)
        print("Prediction:", pred)

        # Class index to label mapping
        index = ['APPLES', 'BANANA', 'ORANGE', 'PINEAPPLE', 'WATERMELON']

        result = str(index[pred[0]])
        x = result
        print(x)
        
        # Call the nutrition API
        result = nutrition(result)
        print(result)
        return render_template("image.html", showcase=(result), showcase1=(x))


def nutrition(index):
    """Fetch nutritional information using the RapidAPI endpoint."""
    url = "https://nutrition-by-api-ninjas.p.rapidapi.com/v1/nutrition"
    querystring = {"query": index}

    headers = {
        "x-rapidapi-key": "edfe3870b0mshbe155f99bc15a7bp1fb5a7jsn3ee827c63613",
        "x-rapidapi-host": "nutrition-by-api-ninjas.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)
    return response.json()


if __name__ == "__main__":
    app.run(debug=False)
