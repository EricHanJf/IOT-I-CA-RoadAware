from flask import Flask, render_template, request
import requests
from config import NEWS_API_KEY

app = Flask(__name__)


# homepage
@app.route("/")
def news():
    query = request.args.get("query", "latest")
    # url = f"https://newsapi.org/v2/top-headlines?country={query}&apiKey={NEWS_API_KEY}"
    url = f"https://newsapi.org/v2/everything?q={query}&apiKey={NEWS_API_KEY}"
    response = requests.get(url)
    news_data = response.json()
    articles = news_data.get("articles", [])
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
