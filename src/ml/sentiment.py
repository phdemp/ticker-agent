from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

class SentimentAnalyzer:
    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()

    def analyze(self, text: str) -> float:
        """
        Returns the compound sentiment score (-1.0 to 1.0).
        """
        if not text:
            return 0.0
        scores = self.analyzer.polarity_scores(text)
        return scores['compound']
