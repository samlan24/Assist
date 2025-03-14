import spacy

nlp = spacy.load("en_core_web_sm")

def analyze_content(content):
    doc = nlp(content)
    keywords = [token.text for token in doc if token.is_alpha and not token.is_stop]
    keyword_freq = {keyword: keywords.count(keyword) for keyword in set(keywords)}
    return keyword_freq