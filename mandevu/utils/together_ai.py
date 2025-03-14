import together
from dotenv import load_dotenv
import os

load_dotenv()

def get_recommendations(issues):
    api_key = os.getenv("TOGETHER_AI_API_KEY")
    together.initialize(api_key)
    recommendations = together.get_recommendations(issues)
    return recommendations