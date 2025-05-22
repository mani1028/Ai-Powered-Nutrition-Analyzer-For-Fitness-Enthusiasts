from flask import Flask, render_template, request, jsonify, redirect, url_for, session, g
import os
import numpy as np
import pandas as pd
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
import requests
from difflib import get_close_matches
import firebase_admin
from firebase_admin import credentials, auth, firestore
from functools import wraps

app = Flask(__name__, template_folder="../templates", static_folder="../static")
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024
app.secret_key = 'supersecretkey'

cred = credentials.Certificate(r'C:\Users\Admin\Desktop\flask\uploads\firebase-adminsdk.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

model = load_model(r'C:\Users\Admin\Desktop\flask\uploads\nutrition.h5')
nutrition_df = pd.read_csv(r"C:\Users\Admin\Desktop\flask\uploads\cleaned_food_data.csv")
nutrition_df['name'] = nutrition_df['name'].str.strip().str.lower()

def firebase_token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        id_token = request.cookies.get('token')
        if not id_token:
            return redirect(url_for('login'))
        try:
            decoded_token = auth.verify_id_token(id_token)
            request.user = decoded_token
            g.user_id = decoded_token.get('uid')
        except Exception as e:
            print("Token validation failed:", e)
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/")
def home():
    return render_template("index.html")

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/logout')
def logout():
    return redirect(url_for('login')) 
    
@app.route('/image')
@firebase_token_required
def image_upload():
    uid = g.user_id
    doc = db.collection('user_profiles').document(uid).get()
    if not doc.exists:
        return redirect('/profile')
    return render_template("image.html")

@app.route('/about')
def about():
    return render_template("about.html")

@app.route('/dashboard')
@firebase_token_required
def dashboard():
    uid = g.user_id
    doc = db.collection('user_profiles').document(uid).get()
    if not doc.exists:
        return redirect('/profile')

    profile = doc.to_dict()
    nutrition = {
        "calories": profile["calories"],
        "protein": round(profile["weight"] * 1.5),
        "carbs": round(profile["calories"] * 0.5 / 4),
        "fats": round(profile["calories"] * 0.3 / 9)
    }

    today_intake = {
        "calories": 1700,
        "protein": 40,
        "carbs": 180,
        "fats": 50,
        "fiber": 12
    }

    caloric_balance = today_intake["calories"] - nutrition["calories"]

    tips = []
    if today_intake["protein"] < nutrition["protein"]:
        tips.append("Try increasing your protein intake to support your goals—consider lean meats or legumes.")
    if today_intake["fiber"] < 25:
        tips.append("You're a bit low on fiber. Add more vegetables, fruits, or whole grains to meals.")
    if profile["activity"] == "sedentary":
        tips.append("Consider adding light movement like a walk to your day to boost metabolism.")
    if caloric_balance > 200:
        tips.append("You’ve consumed more than your daily needs—try balancing with lighter meals.")
    elif caloric_balance < -200:
        tips.append("You’re under your caloric goal. Ensure you're eating enough for energy.")

    return render_template("dashboard.html", profile=profile, user_name=profile['name'], nutrition=nutrition, caloric_balance=caloric_balance, tips=tips)

@app.route('/service')
def service():
    return render_template("service.html")

@app.route('/team')
def team():
    return render_template("team.html")

@app.route('/contact')
def contact():
    return render_template("contact.html")

@app.route('/predict', methods=['POST'])
@firebase_token_required
def predict():
    predicted_label = None
    nutrition_data = None

    try:
        if 'file' in request.files:
            file = request.files['file']
            basepath = os.path.dirname(__file__)
            upload_dir = os.path.join(basepath, "upload")
            os.makedirs(upload_dir, exist_ok=True)
            filepath = os.path.join(upload_dir, file.filename)
            file.save(filepath)

            img = image.load_img(filepath, target_size=(64, 64))
            img_array = image.img_to_array(img)
            img_array = np.expand_dims(img_array, axis=0)

            prediction = np.argmax(model.predict(img_array), axis=1)
            labels = ['apple', 'banana', 'orange', 'pineapple', 'watermelon']
            predicted_label = labels[prediction[0]]

            nutrition_data = get_nutrition_api(predicted_label)

        elif 'description' in request.form:
            description = request.form['description']
            predicted_label = match_description(description)
            nutrition_data = get_nutrition_csv(predicted_label)

    except Exception as e:
        print("Prediction error:", e)

    return render_template("image.html", showcase=nutrition_data, showcase1=predicted_label)

@app.route('/profile', methods=['GET', 'POST'])
@firebase_token_required
def profile():
    uid = g.user_id
    user_ref = db.collection('user_profiles').document(uid)

    if request.method == 'POST':
        name = request.form['name']
        age = int(request.form['age'])
        weight = float(request.form['weight'])
        height = float(request.form['height'])
        gender = request.form['gender']
        activity = request.form['activity']
        goal = request.form['goal']

        bmr = 10 * weight + 6.25 * height - 5 * age + (5 if gender == 'male' else -161)
        activity_factors = {
            "sedentary": 1.2,
            "lightly active": 1.375,
            "moderately active": 1.55,
            "very active": 1.725,
            "extra active": 1.9
        }
        calories = bmr * activity_factors.get(activity, 1.2)
        if goal == "lose":
            calories -= 500
        elif goal == "gain":
            calories += 500

        user_ref.set({
            "name": name,
            "age": age,
            "weight": weight,
            "height": height,
            "gender": gender,
            "activity": activity,
            "goal": goal,
            "calories": round(calories)
        }, merge=True)

        return redirect('/dashboard')

    doc = user_ref.get()
    profile_data = doc.to_dict() if doc.exists else None
    return render_template("profile.html", profile=profile_data)

def get_nutrition_api(query):
    url = "https://nutrition-by-api-ninjas.p.rapidapi.com/v1/nutrition"
    headers = {
        "x-rapidapi-key": "edfe3870b0mshbe155f99bc15a7bp1fb5a7jsn3ee827c63613",
        "x-rapidapi-host": "nutrition-by-api-ninjas.p.rapidapi.com"
    }
    try:
        response = requests.get(url, headers=headers, params={"query": query}, timeout=5)
        json_data = response.json()
        data = json_data[0] if isinstance(json_data, list) and json_data else {}
        return {
            "name": data.get("name", "N/A").title(),
            "protein_g": data.get("protein_g", "N/A"),
            "calories_kcal": data.get("calories", "N/A"),
            "fat_total_g": data.get("fat_total_g", "N/A"),
            "fat_saturated_g": data.get("fat_saturated_g", "N/A"),
            "magnesium_mg": data.get("magnesium_mg", "N/A"),
            "caffeine_mg": data.get("caffeine_mg", "N/A"),
            "iron_mg": data.get("iron_mg", "N/A"),
            "sodium_mg": data.get("sodium_mg", "N/A"),
            "potassium_mg": data.get("potassium_mg", "N/A"),
            "cholesterol_mg": data.get("cholesterol_mg", "N/A"),
            "carbohydrates_total_g": data.get("carbohydrates_total_g", "N/A"),
            "fiber_g": data.get("fiber_g", "N/A"),
            "sugar_g": data.get("sugar_g", "N/A")
        }
    except Exception as e:
        print("API error:", e)
        return {"name": query, "error": "API failed"}

def get_nutrition_csv(query):
    query_norm = query.strip().lower()
    row = nutrition_df[nutrition_df['name'] == query_norm]

    if not row.empty:
        row = row.iloc[0]
        return {
            "name": query.title(),
            "protein_g": row.get("protein", "N/A"),
            "calories_kcal": row.get("calories", "N/A"),
            "fat_total_g": row.get("total_fat", "N/A"),
            "fat_saturated_g": row.get("saturated_fat", "N/A"),
            "magnesium_mg": row.get("magnesium", "N/A"),
            "caffeine_mg": row.get("caffeine", "N/A"),
            "iron_mg": row.get("iron", "N/A"),
            "sodium_mg": row.get("sodium", "N/A"),
            "potassium_mg": row.get("potassium", "N/A"),
            "cholesterol_mg": row.get("cholesterol", "N/A"),
            "carbohydrates_total_g": row.get("carbohydrate", "N/A"),
            "fiber_g": row.get("fiber", "N/A"),
            "sugar_g": row.get("sugars", "N/A")
        }
    else:
        return {key: "N/A" for key in [
            "name", "protein_g", "calories_kcal", "fat_total_g", "fat_saturated_g",
            "magnesium_mg", "caffeine_mg", "iron_mg", "sodium_mg", "potassium_mg",
            "cholesterol_mg", "carbohydrates_total_g", "fiber_g", "sugar_g"
        ]}

def match_description(description):
    all_names = nutrition_df['name'].tolist()
    matches = get_close_matches(description.lower(), all_names, n=1, cutoff=0.3)
    return matches[0] if matches else description

if __name__ == "__main__":
    app.run(debug=True)
