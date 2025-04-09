import requests
import json
import os


TOGETHER_AI_API_KEY = os.getenv("TOGETHER_AI_API_KEY")

def get_recommendations(issues_detected):
    """
    Generates SEO recommendations based on detected issues using Together AI.

    Args:
        issues_detected (list): List of detected SEO issues.

    Returns:
        dict: AI-generated SEO recommendations in JSON format.
    """
    if not TOGETHER_AI_API_KEY:
        raise ValueError("Missing Together AI API key. Set TOGETHER_AI_API_KEY in environment variables.")

    api_url = "https://api.together.ai/v1/chat/completions"


    prompt = f"""
    Here are the SEO issues detected on a webpage:
    {json.dumps(issues_detected, indent=2)}

    Provide SEO recommendations, in **structured JSON format**.

    ONLY return a JSON response, in this exact format:
    {{
        "ai_recommendations": [
            "Recommendation 1",
            "Recommendation 2",
            "Recommendation 3"
        ]
    }}
    """

    headers = {
        "Authorization": f"Bearer {TOGETHER_AI_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
        "messages": [
            {"role": "system", "content": "You are an expert SEO assistant."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }

    response = requests.post(api_url, headers=headers, json=payload)

    if response.status_code == 200:
        try:
            ai_response = response.json().get("choices", [{}])[0].get("message", {}).get("content", "{}")
            return json.loads(ai_response)
        except json.JSONDecodeError:
            return {"Recommendations": ["Error: AI response is not valid JSON."]}
    else:
        return {"Recommendations": [f"Error: {response.status_code}, {response.text}"]}

