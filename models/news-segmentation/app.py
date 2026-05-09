from flask import Flask, render_template, request
import joblib
import yfinance as yf
from nlp_preprocess import pre_process

app = Flask(__name__)

MODEL_PATHS = {
    'model': 'sentiment_model.pkl',
    'vectorizer': 'tfidf_vectorizer.pkl',
}

LABEL_MAP = {
    0: 'Negative',
    1: 'Neutral',
    2: 'Positive',
}

TOPICS = {
    'bitcoin': 'BTC-USD',
    'tesla': 'TSLA',
    'apple': 'AAPL',
    'amazon': 'AMZN',
    'nvidia': 'NVDA',
    'microsoft': 'MSFT',
    'google': 'GOOGL',
}


def load_model_artifacts():
    sentiment_model = joblib.load(MODEL_PATHS['model'])
    tfidf_vectorizer = joblib.load(MODEL_PATHS['vectorizer'])

    classes = getattr(sentiment_model, 'classes_', None)
    if classes is not None:
        try:
            mapped = {cls: LABEL_MAP[int(cls)] for cls in classes if int(cls) in LABEL_MAP}
            if mapped:
                label_map = mapped
            else:
                label_map = {cls: str(cls).title() for cls in classes}
        except Exception:
            label_map = {cls: str(cls).title() for cls in classes}
    else:
        label_map = LABEL_MAP

    return sentiment_model, tfidf_vectorizer, label_map


model, vectorizer, label_map = load_model_artifacts()


def classify_sentiment(text):
    cleaned = pre_process(text)
    if not cleaned:
        return 'Neutral'

    try:
        vector = vectorizer.transform([cleaned])
        prediction = model.predict(vector)[0]
        return label_map.get(prediction, str(prediction).title())
    except Exception:
        return 'Neutral'


def _normalize_text(value):
    if value is None:
        return ''
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        for key in ('text', 'raw', 'title', 'headline', 'summary', 'description', 'content'):
            nested = value.get(key)
            if isinstance(nested, str) and nested.strip():
                return nested.strip()
        for nested in value.values():
            normalized = _normalize_text(nested)
            if normalized:
                return normalized
        return ''
    if isinstance(value, (list, tuple)):
        parts = [ _normalize_text(item) for item in value ]
        return ' '.join([part for part in parts if part]).strip()
    return str(value).strip()


def _normalize_link(value):
    if value is None:
        return '#'
    if isinstance(value, str):
        return value.strip() or '#'
    if isinstance(value, dict):
        for key in ('link', 'url', 'link_url', 'content_url', 'clickUrl', 'href'):
            nested = value.get(key)
            if isinstance(nested, str) and nested.strip():
                return nested.strip()
        return '#'
    return str(value).strip() or '#'


def get_news_for_ticker(ticker_symbol):
    news_items = []
    try:
        ticker = yf.Ticker(ticker_symbol)
        raw_news = ticker.news or []
    except Exception:
        raw_news = []

    for item in raw_news[:8]:
        title = _normalize_text(
            item.get('title') or item.get('headline') or item.get('content') or item.get('summary') or item.get('publisher') or item.get('source')
        )
        summary = _normalize_text(
            item.get('summary') or item.get('description') or item.get('headline') or item.get('content') or item.get('publisher') or item.get('source')
        )
        link = _normalize_link(
            item.get('link') or item.get('url') or item.get('link_url') or item.get('content_url') or item.get('clickUrl')
        )
        provider = _normalize_text(item.get('publisher') or item.get('source') or 'Yahoo Finance')

        if not title and summary:
            title = summary
            summary = ''

        content = ' '.join([part for part in [title, summary] if part]).strip()

        news_items.append({
            'title': title or 'Headline unavailable',
            'summary': summary or 'No summary available.',
            'link': link,
            'provider': provider or 'Yahoo Finance',
            'sentiment': classify_sentiment(content),
        })

    return news_items


@app.route('/', methods=['GET', 'POST'])
def index():
    selected_topic = 'bitcoin'
    topic_name = 'Bitcoin'
    news_items = []
    summary_text = 'Choose a topic to load the latest Yahoo Finance headlines and sentiment.'

    if request.method == 'POST':
        selected_topic = request.form.get('topic', 'bitcoin')
        topic_name = selected_topic.capitalize()
        ticker_symbol = TOPICS.get(selected_topic, 'BTC-USD')
        news_items = get_news_for_ticker(ticker_symbol)
        positive = sum(1 for item in news_items if item['sentiment'] == 'Positive')
        neutral = sum(1 for item in news_items if item['sentiment'] == 'Neutral')
        negative = sum(1 for item in news_items if item['sentiment'] == 'Negative')
        summary_text = f"Found {len(news_items)} articles: {positive} positive, {neutral} neutral, {negative} negative"

    return render_template(
        'index.html',
        selected_topic=selected_topic,
        topic_name=topic_name,
        news_items=news_items,
        summary_text=summary_text,
        topics=TOPICS,
    )


if __name__ == '__main__':
    app.run(debug=False)
