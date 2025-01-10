from flask import (
    Flask,
    render_template,
    request,
    redirect,
    session,
    abort,
    url_for,
    flash,
    jsonify,
)
import requests
import os
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol
import google.auth.transport.requests
import pathlib
from datetime import datetime
from .config import config
from . import my_db
from .my_db import Car, Distance
from werkzeug.utils import secure_filename

# from . import my_db

db = my_db.db

app = Flask(__name__)
app.secret_key = config.get("APP_SECRET_KEY")

app.config["SQLALCHEMY_DATABASE_URI"] = config.get("SQLALCHEMY_DATABASE_URI")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
with app.app_context():
    db.create_all()
# os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

GOOGLE_CLIENT_ID = config.get("GOOGLE_CLIENT_ID")

client_secret_file = os.path.join(pathlib.Path(__file__).parent, ".client_secrets.json")

flow = Flow.from_client_secrets_file(
    client_secrets_file=client_secret_file,
    scopes=[
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/userinfo.email",
        "openid",
    ],
    redirect_uri="https://www.sd3siot.online/callback",
)


def login_is_required(function):
    def wrapper(*args, **kwargs):
        if "google_id" not in session:
            return abort(401)  # Authorization required
        else:
            return function()

    return wrapper


@app.route("/login")
def login():
    authorization_url, state = flow.authorization_url()
    session["state"] = state
    return redirect(authorization_url)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/callback")
def callback():
    flow.fetch_token(authorization_response=request.url)

    if not session["state"] == request.args["state"]:
        abort(500)

    credentials = flow.credentials
    request_session = requests.Session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)

    id_info = id_token.verify_oauth2_token(
        id_token=credentials._id_token,
        request=token_request,
        audience=GOOGLE_CLIENT_ID,
    )

    session["google_id"] = id_info.get("sub")
    session["name"] = id_info.get("name")
    session["google_avatar"] = id_info["picture"]

    # Add user to the database
    my_db.add_user_and_login(session["name"], session["google_id"])
    print(f"Logged in user ID: {session['google_id']}")
    print(f"Admin ID: {config.get('GOOGLE_ADMIN_ID')}")
    return redirect("/news")


# Homepage route
@app.route("/", methods=["GET"])
def index():
    google_avatar = session.get("google_avatar")
    return render_template("index.html", avatar_url=google_avatar)


# for admin globally accessible across templates
@app.context_processor
def inject_globals():
    return {"google_admin_id": config.get("GOOGLE_ADMIN_ID")}


# News page route
@app.route("/news", methods=["GET"], endpoint="news")
@login_is_required
def news():
    query = request.args.get("query", "latest")
    # URL for fetching the latest news
    url = f"https://newsapi.org/v2/everything?q={query}&sortBy=publishedAt&apiKey={config.get('NEWS_API_KEY')}"

    response = requests.get(url)
    # print(f"API Response Code: {response.status_code}")  # Log response code
    # print(response.text)  # Log the full response for debugging

    if response.status_code != 200:
        return render_template("error.html", message="Failed to fetch news.")

    news_data = response.json()
    articles = news_data.get("articles", [])

    google_avatar = session.get("google_avatar")
    print(f"Total articles fetched: {len(articles)}")
    filter_articles = [
        article
        for article in articles
        if "Yahoo" not in article.get("source", {}).get("name", "")
        and "removed" not in article.get("title", "").lower()
        and article.get("urlToImage")
    ]

    return render_template(
        "news.html", articles=filter_articles, query=query, avatar_url=google_avatar
    )


# dashboard page Route
@app.route("/dashboard", endpoint="dashboard")
@login_is_required
def dashboard():
    try:
        user_id = session["google_id"]
        user_name = session.get("name")
        google_admin_id = config.get("GOOGLE_ADMIN_ID")
        google_avatar = session.get("google_avatar")

        if not user_id or not user_name or user_id != google_admin_id:
            return redirect(url_for("signin"))

        online_users = my_db.get_all_logged_in_users()
        print(f"Online users: {online_users}")
        # google_admin_id = config.get("GOOGLE_ADMIN_ID")

        return render_template(
            "dashboard.html",
            user_id=user_id,
            google_admin_id=google_admin_id,
            avatar_url=google_avatar,
            online_users=online_users,
        )
    except Exception as e:
        print(f"Error in dashboard: {e}")
        return "An error occurred while loading the dashboard.", 500


# delete user route
@app.route("/delete_user/<int:id>", methods=["POST"], endpoint="delete_user")
def delete_user(id):
    try:
        user = my_db.User.query.get(id)  # Use the passed ID
        if user:
            db.session.delete(user)
            db.session.commit()
            flash("User deleted successfully!", "admin")
        else:
            flash("User not found.", "admin")
        return redirect(url_for("dashboard"))
    except Exception as e:
        return f"Error: {e}"


# Add car route
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


UPLOAD_FOLDER = "var/www/FlaskApp/FlaskApp/static/uploads/cars"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


@app.route("/addcar", methods=["GET", "POST"], endpoint="addcar")
@login_is_required
def addcar():
    google_avatar = session.get("google_avatar")
    if request.method == "POST":
        try:
            # Get form data
            make = request.form.get("make")
            year = request.form.get("year")
            car_type = request.form.get("type")
            engine_type = request.form.get("engine_type")
            transmission = request.form.get("transmission")
            color = request.form.get("color")
            picture = request.files.get("picture_url")  # For file uploads
            # Validate required fields
            if not all([make, year, car_type, engine_type, transmission, color]):
                flash("All fields are required except the picture.", "danger")
                return redirect(url_for("addcar"))

            # Validate file and save it
            carpicture_path = None
            if picture and allowed_file(picture.filename):
                filename = secure_filename(picture.filename)
                upload_folder = app.config["UPLOAD_FOLDER"]
                os.makedirs(upload_folder, exist_ok=True)  # Ensure directory exists
                filepath = os.path.join(upload_folder, filename)
                picture.save(filepath)  # Save the file
                carpicture_path = f"uploads/cars/{filename}"  # Store relative path
            elif picture:
                flash(
                    "Invalid file type. Allowed types are PNG, JPG, JPEG, GIF.",
                    "danger",
                )
                return redirect(url_for("addcar"))

            # Create a new Car object
            new_car = Car(
                make=make,
                year=int(year),
                type=car_type,
                engine_type=engine_type,
                transmission=transmission,
                color=color,
                picture_url=carpicture_path,  # Add the picture path
                user_id=session["google_id"],
            )

            # Add and commit to the database
            db.session.add(new_car)
            db.session.commit()
            flash("Car added successfully!", "success")
            return redirect(
                url_for("addcar")
            )  # Redirect to a success page or back to form
        except Exception as e:
            app.logger.error(f"Error adding car: {e}")
            flash("An error occurred while adding the car. Please try again.", "danger")
            return redirect(url_for("addcar"))
    else:
        return render_template("addcar.html", avatar_url=google_avatar)


# car detail route
@app.route("/cars", methods=["GET"], endpoint="cars")
@login_is_required
def cars():
    try:
        user_id = session["google_id"]
        google_admin_id = config.get("GOOGLE_ADMIN_ID")
        google_avatar = session.get("google_avatar")
        # Fetch all plants from the database
        if user_id == google_admin_id:
            # Admin can see all plants
            all_cars = Car.query.all()
        else:
            # Normal users can only see their own plants
            all_cars = Car.query.filter_by(user_id=user_id).all()

        return render_template(
            "cars.html", cars=all_cars, user_id=user_id, avatar_url=google_avatar
        )

    except Exception as e:
        print(f"Error fetching cars: {e}")
        return "An error occurred while fetching the cars.", 500


@app.route("/delete_car/<int:id>", methods=["POST"], endpoint="delete_car")
def delete_car(id):
    try:
        user = my_db.User.query.get(id)
        car = my_db.Car.query.get(id)  # Use the passed ID
        if car:
            db.session.delete(car)
            db.session.commit()
            flash("Car deleted successfully!", "success")
        else:
            flash("car not found.", "success")
        return redirect(url_for("cars"))
    except Exception as e:
        return f"Error: {e}"


# Car feature route
@app.route("/car_feature", methods=["GET"], endpoint="car_feature")
@login_is_required
def car_feature():
    picture = request.args.get("picture_url")  # This should match the template variable
    make = request.args.get("make")
    id = request.args.get("id")  # Assuming car_id is passed to identify the car
    google_avatar = session.get("google_avatar")
    print(f"Picture: {picture}, Make: {make}")
    return render_template(
        "car_feature.html",
        id=id,
        picture=picture,
        make=make,
        avatar_url=google_avatar,
    )


@app.route("/api/store_distance_data", methods=["POST"])
def store_distance_data():
    try:
        data = request.get_json()
        print("Received data:", data)

        if "distance" not in data:
            return jsonify({"error": "Missing distance data"}), 400

        new_data = Distance(distance=data["distance"])
        db.session.add(new_data)
        db.session.commit()

        print("Data stored successfully")
        return jsonify({"message": "TSL2561 data stored successfully"}), 201
    except Exception as e:
        print("Error storing data:", str(e))
        return jsonify({"error": "Failed to store data"}), 500


# distance Previous data route
@app.route(
    "/distance_previous_data", methods=["GET"], endpoint="distance_previous_data"
)
@login_is_required
def distance_previous_data():
    google_avatar = session.get("google_avatar")
    try:
        # Get optional filter parameters from the request
        start_time = request.args.get("start_time")  # Format: YYYY-MM-DD HH:MM:SS
        end_time = request.args.get("end_time")  # Format: YYYY-MM-DD HH:MM:SS

        # Build the query
        query = Distance.query
        if start_time:
            query = query.filter(Distance.timestamp >= start_time)
        if end_time:
            query = query.filter(Distance.timestamp <= end_time)

        # Execute the query
        distances = query.order_by(Distance.timestamp).all()

        # Render the template with data
        return render_template(
            "distance_previous_data.html",
            distances=distances,
            avatar_url=google_avatar,
        )
    except Exception as e:
        print("Error fetching distance data:", str(e))
        return "Failed to fetch distance data", 500


if __name__ == "__main__":
    app.run()
