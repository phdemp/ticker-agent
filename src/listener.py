import re
import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from snscrape.modules.twitter import TwitterSearchScraper

CASHTAG_RE = re.compile(r'\$([A-Z]{2,6})\b')
analyzer = SentimentIntensityAnalyzer()

def extract_cashtags(text):
    return CASHTAG_RE.findall(text)

def fetch_tweets(query, limit=2_000):
    """Yield raw tweets from snscrape."""
    for i, tweet in enumerate(TwitterSearchScraper(query).get_items()):
        if i >= limit:
            break
        yield tweet

def parse_tweet(tweet):
    cashtags = extract_cashtags(tweet.content)
    sentiment = analyzer.polarity_scores(tweet.content)['compound']
    return {
        'id': tweet.id,
        'created': tweet.date,
        'user': tweet.user.username,
        'text': tweet.content,
        'cashtags': cashtags,
        'sentiment': sentiment,
    }

def rank_new_tickers(days=7, limit=2_000):
    since = (pd.Timestamp.utcnow() - pd.Timedelta(days=days)).strftime('%Y-%m-%d')
    query = f'"$" since:{since}'
    records = []
    for tw in fetch_tweets(query, limit):
        records.append(parse_tweet(tw))
    df = pd.DataFrame(records).explode('cashtags').dropna(subset=['cashtags'])
    if df.empty:
        return pd.DataFrame()

    # volume + mean sentiment per ticker
    summary = (df.groupby('cashtags')
                 .agg(count=('id', 'size'),
                      avg_sent=('sentiment', 'mean'),
                      first_tweet=('created', 'min'))
                 .reset_index())
    # keep tickers with ≥ 5 mentions
    summary = summary[summary['count'] >= 5].sort_values('count', ascending=False)
    return summary.head(3)

if __name__ == '__main__':
    top = rank_new_tickers()
    print(top.to_string(index=False))