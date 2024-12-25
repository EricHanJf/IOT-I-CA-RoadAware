from flask import Flask, render_template, request, redirect, session, abort
import requests
from config import NEWS_API_KEY
import os
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol
import google.auth.transport.requests
import pathlib
from datetime import datetime

app = Flask(__name__)

app.secret_key = "My_Secret_Key_123!"
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
GOOGLE_CLIENT_ID = (
    "788082330888-3uijks9jcned5u2vemc1mttc68q3hahq.apps.googleusercontent.com"
)
client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "client_secret.json")

flow = Flow.from_client_secrets_file(
    client_secrets_file=client_secrets_file,
    scopes=[
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/userinfo.email",
        "openid",
    ],
    redirect_uri="http://127.0.0.1:5000/callback",
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


@app.route("/callback")
def callback():
    flow.fetch_token(authorization_response=request.url)

    if not session["state"] == request.args["state"]:
        abort(500)

    credentials = flow.credentials
    # request_session = request.session()
    request_session = requests.Session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)

    id_info = id_token.verify_oauth2_token(
        id_token=credentials._id_token,
        request=token_request,
        audience=GOOGLE_CLIENT_ID,
    )

    session["google_id"] = id_info.get("sub")
    print(session["google_id"])
    session["name"] = id_info.get("name")
    return redirect("/news")


# Homepage route
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


# News page
@app.route("/news", methods=["GET"], endpoint="news")
@login_is_required
def news():
    query = request.args.get("query", "latest")
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    url = f"https://newsapi.org/v2/everything?q={query}&apiKey={NEWS_API_KEY}&timestamp={timestamp}"
    response = requests.get(url)
    news_data = response.json()
    articles = news_data.get("articles", [])
    # app.logger.debug(f"Total articles fetched: {len(articles)}")
    print(f"Total articles fetched: {len(articles)}")
    # print(news_data)
    filter_articles = [
        article
        for article in articles
        if "Yahoo" not in article.get("source", {}).get("name", "")
        and "removed" not in article.get("title", "").lower()
    ]
    return render_template("news.html", articles=filter_articles, query=query)


if __name__ == "__main__":
    app.run(debug=True)
