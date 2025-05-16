from flask import Blueprint, jsonify, current_app, request, render_template
import requests
import os
from datetime import datetime
import logging
from functools import wraps
import re

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Blueprint
api = Blueprint('api', __name__)

# Error handling decorator
def handle_api_errors(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except requests.exceptions.RequestException as e:
            logger.error(f"API request error: {e}")
            return jsonify({"error": "External API request failed", "details": str(e)}), 503
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500
    return decorated_function

# Authentication middleware
def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key or api_key != os.environ.get('API_KEY'):
            return jsonify({"error": "Unauthorized access"}), 401
        return f(*args, **kwargs)
    return decorated_function

# Routes for economic data
@api.route('/interest-rates', methods=['GET'])
@require_api_key
@handle_api_errors
def get_interest_rates():
    series_id = request.args.get('series', 'FEDFUNDS')
    url = f"https://api.stlouisfed.org/fred/series/observations"
    params = {
        'series_id': series_id,
        'api_key': os.environ.get('FRED_API_KEY'),
        'file_type': 'json',
        'sort_order': 'desc',
        'limit': 10
    }
    response = requests.get(url, params=params)
    if response.status_code != 200:
        logger.warning(f"FRED API returned status code {response.status_code}")
        return jsonify({"error": "Could not retrieve interest rate data"}), response.status_code
    data = response.json()
    rate_data = [{
        "date": item["date"],
        "value": float(item["value"]) if item["value"] != "." else None,
        "series": series_id
    } for item in data.get("observations", [])]
    return jsonify({
        "interest_rates": rate_data,
        "last_updated": datetime.now().isoformat()
    })

@api.route('/jobs-report', methods=['GET'])
@require_api_key
@handle_api_errors
def get_jobs_report():
    series_ids = request.args.get('series', 'PAYEMS').split(',')
    url = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
    headers = {"Content-Type": "application/json"}
    data = {
        "seriesid": series_ids,
        "startyear": str(datetime.now().year - 1),
        "endyear": str(datetime.now().year),
        "registrationkey": os.environ.get('BLS_API_KEY')
    }
    response = requests.post(url, json=data, headers=headers)
    if response.status_code != 200:
        logger.warning(f"BLS API returned status code {response.status_code}")
        return jsonify({"error": "Could not retrieve jobs report data"}), response.status_code
    data = response.json()
    if data.get("status") != "REQUEST_SUCCEEDED":
        logger.warning(f"BLS API request failed: {data.get('message')}")
        return jsonify({"error": data.get("message")}), 400
    jobs_data = []
    for series in data.get("Results", {}).get("series", []):
        series_id = series.get("seriesID")
        for item in series.get("data", []):
            jobs_data.append({
                "series": series_id,
                "year": item.get("year"),
                "period": item.get("period").replace("M", ""),
                "value": float(item.get("value")),
                "footnotes": [note.get("text") for note in item.get("footnotes", [])]
            })
    jobs_data.sort(key=lambda x: (int(x["year"]), int(x["period"])), reverse=True)
    return jsonify({
        "jobs_data": jobs_data,
        "last_updated": datetime.now().isoformat()
    })

@api.route('/inflation', methods=['GET'])
@require_api_key
@handle_api_errors
def get_inflation_data():
    series_id = request.args.get('series', 'CPIAUCSL')
    url = f"https://api.stlouisfed.org/fred/series/observations"
    params = {
        'series_id': series_id,
        'api_key': os.environ.get('FRED_API_KEY'),
        'file_type': 'json',
        'sort_order': 'desc',
        'limit': 24
    }
    response = requests.get(url, params=params)
    if response.status_code != 200:
        logger.warning(f"FRED API returned status code {response.status_code}")
        return jsonify({"error": "Could not retrieve inflation data"}), response.status_code
    data = response.json()
    observations = data.get("observations", [])
    inflation_data = []
    for i in range(len(observations) - 12):
        current = observations[i]
        year_ago = observations[i + 12]
        if current["value"] != "." and year_ago["value"] != ".":
            current_value = float(current["value"])
            year_ago_value = float(year_ago["value"])
            yoy_rate = ((current_value - year_ago_value) / year_ago_value) * 100
            inflation_data.append({
                "date": current["date"],
                "value": round(yoy_rate, 2),
                "index": current_value,
                "series": series_id
            })
    return jsonify({
        "inflation_data": inflation_data,
        "last_updated": datetime.now().isoformat()
    })

@api.route('/economic-news', methods=['GET'])
@require_api_key
@handle_api_errors
def get_economic_news():
    query = request.args.get('query', 'economy OR inflation OR "interest rates" OR "federal reserve"')
    days = int(request.args.get('days', 3))
    from_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    from_date = from_date.replace(day=from_date.day - days).isoformat()
    url = "https://newsapi.org/v2/everything"
    params = {
        'q': query,
        'from': from_date,
        'sortBy': 'popularity',
        'language': 'en',
        'apiKey': os.environ.get('NEWS_API_KEY')
    }
    response = requests.get(url, params=params)
    if response.status_code != 200:
        logger.warning(f"News API returned status code {response.status_code}")
        return jsonify({"error": "Could not retrieve economic news"}), response.status_code
    data = response.json()
    news_data = []
    for article in data.get("articles", []):
        if article.get("title") and article.get("url"):
            news_data.append({
                "title": article.get("title"),
                "source": article.get("source", {}).get("name"),
                "author": article.get("author"),
                "description": article.get("description"),
                "url": article.get("url"),
                "published_at": article.get("publishedAt"),
                "content_snippet": article.get("content", "").split("[+")[0],
                "image_url": article.get("urlToImage")
            })
    return jsonify({
        "economic_news": news_data,
        "count": len(news_data),
        "query": query,
        "last_updated": datetime.now().isoformat()
    })

def clean_article_content(content):
    """Clean and sanitize article content."""
    if not content:
        return ""
    # Remove any script-like content
    if isinstance(content, str):
        content = content.replace('window.open', '')
        content = content.replace('javascript:', '')
        # Remove HTML tags
        content = re.sub(r'<[^>]+>', '', content)
        # Remove special characters
        content = content.replace('&gt;', '>').replace('&lt;', '<').replace('&amp;', '&')
        # Truncate if too long
        return content[:200] + '...' if len(content) > 200 else content
    return ""

@api.route('/', methods=['GET'])
def render_news_page():
    try:
        query = 'economy OR inflation OR "interest rates" OR "federal reserve"'
        days = 1
        from_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        from_date = from_date.replace(day=from_date.day - days).isoformat()
        
        url = "https://newsapi.org/v2/everything"
        params = {
            'q': query,
            'from': from_date,
            'sortBy': 'popularity',
            'language': 'en',
            'apiKey': os.environ.get('NEWS_API_KEY')
        }
        
        response = requests.get(url, params=params)
        if response.status_code != 200:
            logger.warning(f"News API returned status code {response.status_code}")
            return render_template('index.html', articles=[])
            
        data = response.json()
        news_data = []
        for article in data.get("articles", []):
            if article.get("title") and article.get("url"):
                news_data.append({
                    "title": clean_article_content(article.get("title")),
                    "source": article.get("source", {}).get("name"),
                    "author": article.get("author"),
                    "description": clean_article_content(article.get("description")),
                    "url": article.get("url"),
                    "published_at": article.get("publishedAt"),
                    "content_snippet": clean_article_content(article.get("content")),
                    "image_url": article.get("urlToImage")
                })
        return render_template('index.html', articles=news_data)
    except Exception as e:
        logger.error(f"Failed to render homepage: {e}")
        return render_template('index.html', articles=[])

@api.route('/markets', methods=['GET'])
def markets_page():
    try:
        query = 'stock market OR financial markets OR trading OR market analysis'
        days = 2
        from_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        from_date = from_date.replace(day=from_date.day - days).isoformat()
        
        url = "https://newsapi.org/v2/everything"
        params = {
            'q': query,
            'from': from_date,
            'sortBy': 'popularity',
            'language': 'en',
            'apiKey': os.environ.get('NEWS_API_KEY')
        }
        
        response = requests.get(url, params=params)
        news_data = []
        if response.status_code == 200:
            data = response.json()
            for article in data.get("articles", []):
                if article.get("title") and article.get("url"):
                    news_data.append({
                        "title": article.get("title"),
                        "source": article.get("source", {}).get("name"),
                        "author": article.get("author"),
                        "description": article.get("description"),
                        "url": article.get("url"),
                        "published_at": article.get("publishedAt"),
                        "content_snippet": article.get("content", "").split("[+")[0],
                        "image_url": article.get("urlToImage")
                    })
        return render_template('category.html', 
                             articles=news_data, 
                             category="Markets",
                             description="Latest updates from global financial markets")
    except Exception as e:
        logger.error(f"Failed to render markets page: {e}")
        return render_template('category.html', articles=[], category="Markets")

@api.route('/stocks', methods=['GET'])
def stocks_page():
    try:
        query = 'stocks OR stock trading OR NYSE OR NASDAQ OR company earnings'
        days = 2
        from_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        from_date = from_date.replace(day=from_date.day - days).isoformat()
        
        url = "https://newsapi.org/v2/everything"
        params = {
            'q': query,
            'from': from_date,
            'sortBy': 'popularity',
            'language': 'en',
            'apiKey': os.environ.get('NEWS_API_KEY')
        }
        
        response = requests.get(url, params=params)
        news_data = []
        if response.status_code == 200:
            data = response.json()
            for article in data.get("articles", []):
                if article.get("title") and article.get("url"):
                    news_data.append({
                        "title": article.get("title"),
                        "source": article.get("source", {}).get("name"),
                        "author": article.get("author"),
                        "description": article.get("description"),
                        "url": article.get("url"),
                        "published_at": article.get("publishedAt"),
                        "content_snippet": article.get("content", "").split("[+")[0],
                        "image_url": article.get("urlToImage")
                    })
        return render_template('category.html', 
                             articles=news_data, 
                             category="Stocks",
                             description="Latest stock market news and analysis")
    except Exception as e:
        logger.error(f"Failed to render stocks page: {e}")
        return render_template('category.html', articles=[], category="Stocks")

@api.route('/crypto', methods=['GET'])
def crypto_page():
    try:
        query = 'cryptocurrency OR bitcoin OR ethereum OR blockchain OR crypto market'
        days = 2
        from_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        from_date = from_date.replace(day=from_date.day - days).isoformat()
        
        url = "https://newsapi.org/v2/everything"
        params = {
            'q': query,
            'from': from_date,
            'sortBy': 'popularity',
            'language': 'en',
            'apiKey': os.environ.get('NEWS_API_KEY')
        }
        
        response = requests.get(url, params=params)
        news_data = []
        if response.status_code == 200:
            data = response.json()
            for article in data.get("articles", []):
                if article.get("title") and article.get("url"):
                    news_data.append({
                        "title": article.get("title"),
                        "source": article.get("source", {}).get("name"),
                        "author": article.get("author"),
                        "description": article.get("description"),
                        "url": article.get("url"),
                        "published_at": article.get("publishedAt"),
                        "content_snippet": article.get("content", "").split("[+")[0],
                        "image_url": article.get("urlToImage")
                    })
        return render_template('category.html', 
                             articles=news_data, 
                             category="Cryptocurrency",
                             description="Latest cryptocurrency news and market updates")
    except Exception as e:
        logger.error(f"Failed to render crypto page: {e}")
        return render_template('category.html', articles=[], category="Cryptocurrency")

@api.route('/real-estate', methods=['GET'])
def real_estate_page():
    try:
        query = 'real estate market OR housing market OR property investment OR mortgage rates'
        days = 2
        from_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        from_date = from_date.replace(day=from_date.day - days).isoformat()
        
        url = "https://newsapi.org/v2/everything"
        params = {
            'q': query,
            'from': from_date,
            'sortBy': 'popularity',
            'language': 'en',
            'apiKey': os.environ.get('NEWS_API_KEY')
        }
        
        response = requests.get(url, params=params)
        news_data = []
        if response.status_code == 200:
            data = response.json()
            for article in data.get("articles", []):
                if article.get("title") and article.get("url"):
                    news_data.append({
                        "title": article.get("title"),
                        "source": article.get("source", {}).get("name"),
                        "author": article.get("author"),
                        "description": article.get("description"),
                        "url": article.get("url"),
                        "published_at": article.get("publishedAt"),
                        "content_snippet": article.get("content", "").split("[+")[0],
                        "image_url": article.get("urlToImage")
                    })
        return render_template('category.html', 
                             articles=news_data, 
                             category="Real Estate",
                             description="Latest real estate market news and trends")
    except Exception as e:
        logger.error(f"Failed to render real estate page: {e}")
        return render_template('category.html', articles=[], category="Real Estate")

@api.route('/tech', methods=['GET'])
def tech_page():
    try:
        query = 'technology industry OR tech companies OR innovation OR artificial intelligence OR startups'
        days = 2
        from_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        from_date = from_date.replace(day=from_date.day - days).isoformat()
        
        url = "https://newsapi.org/v2/everything"
        params = {
            'q': query,
            'from': from_date,
            'sortBy': 'popularity',
            'language': 'en',
            'apiKey': os.environ.get('NEWS_API_KEY')
        }
        
        response = requests.get(url, params=params)
        news_data = []
        if response.status_code == 200:
            data = response.json()
            for article in data.get("articles", []):
                if article.get("title") and article.get("url"):
                    news_data.append({
                        "title": article.get("title"),
                        "source": article.get("source", {}).get("name"),
                        "author": article.get("author"),
                        "description": article.get("description"),
                        "url": article.get("url"),
                        "published_at": article.get("publishedAt"),
                        "content_snippet": article.get("content", "").split("[+")[0],
                        "image_url": article.get("urlToImage")
                    })
        return render_template('category.html', 
                             articles=news_data, 
                             category="Technology",
                             description="Latest technology news and innovations")
    except Exception as e:
        logger.error(f"Failed to render tech page: {e}")
        return render_template('category.html', articles=[], category="Technology")

def register_routes(app):
    app.register_blueprint(api)
