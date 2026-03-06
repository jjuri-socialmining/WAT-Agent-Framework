"""
analyze_competitors.py
----------------------
Uses Google Gemini to analyze the scraped data for each competitor
against the saved business profile.

Reads:  tmp/all_scraped.json
        data/business_profile.json
Writes: tmp/analysis_results.json
"""

import os
import json
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

# Setup Gemini
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_key_here":
    raise ValueError("Missing valid GEMINI_API_KEY in .env file")

genai.configure(api_key=GEMINI_API_KEY)
# Use the model specified in .env, fallback to gemini-1.5-pro
MODEL_NAME = os.environ.get("GEMINI_MODEL", "gemini-1.5-pro")

generation_config = {
  "temperature": 0.2,
  "top_p": 0.95,
  "top_k": 40,
  "max_output_tokens": 8192,
  "response_mime_type": "application/json",
}

def analyze_all():
    print(f"🤖 Loading data for Gemini ({MODEL_NAME}) analysis...\n")
    
    with open("data/business_profile.json", "r") as f:
        my_business = json.load(f)
        
    try:
        with open("tmp/all_scraped.json", "r") as f:
            competitors_data = json.load(f)
    except FileNotFoundError:
        print("❌ Error: tmp/all_scraped.json not found. Run scrape_competitor.py first.")
        return

    model = genai.GenerativeModel(
        model_name=MODEL_NAME,
        generation_config=generation_config,
        system_instruction="You are an expert business strategist and competitive intelligence analyst. Always output strictly valid JSON."
    )

    analysis_results = {
        "market_summary": "",
        "my_business_opportunities": [],
        "competitors": []
    }

    print(f"  Analyzing {len(competitors_data)} competitors...")

    for comp in competitors_data:
        comp_name = comp["name"]
        print(f"    Analyzing {comp_name}...")
        
        # Prepare the prompt for this specific competitor
        prompt = f"""
        Here is the profile for my business:
        {json.dumps(my_business, indent=2)}
        
        Here is the scraped website data and reviews for a competitor named '{comp_name}':
        {json.dumps(comp, indent=2)}
        
        Please analyze this competitor. Return a JSON object with EXACTLY the following structure:
        {{
            "name": "{comp_name}",
            "summary": "1-2 sentences summarizing what they do",
            "strengths": ["strength 1", "strength 2", "strength 3"],
            "weaknesses": ["weakness 1", "weakness 2", "weakness 3"],
            "pricing_strategy": "Summary of how they price (if found, else 'Not public')",
            "key_features": ["feature 1", "feature 2"],
            "threat_level": "Low|Medium|High",
            "ideas_to_beat_them": ["idea 1", "idea 2"]
        }}
        """
        
        try:
            response = model.generate_content(prompt)
            result_json = json.loads(response.text)
            analysis_results["competitors"].append(result_json)
        except Exception as e:
            print(f"      ❌ Error analyzing {comp_name}: {e}")

    # Now do a macro analysis of the market
    print("\n  Generating final market summary and global opportunities...")
    macro_prompt = f"""
    My business:
    {json.dumps(my_business, indent=2)}
    
    My competitors' individual analyses:
    {json.dumps(analysis_results["competitors"], indent=2)}
    
    Based on the above, provide a macro market summary and identify the top 3-5 opportunities for my business to dominate this space.
    Return a JSON object with EXACTLY this structure:
    {{
        "market_summary": "A 2-3 paragraph summary of the current market landscape.",
        "my_business_opportunities": ["opportunity 1", "opportunity 2", "opportunity 3", "opportunity 4"]
    }}
    """
    
    try:
        response = model.generate_content(macro_prompt)
        macro_json = json.loads(response.text)
        analysis_results["market_summary"] = macro_json.get("market_summary", "")
        analysis_results["my_business_opportunities"] = macro_json.get("my_business_opportunities", [])
    except Exception as e:
        print(f"      ❌ Error generating macro analysis: {e}")

    # Save results
    with open("tmp/analysis_results.json", "w") as f:
        json.dump(analysis_results, f, indent=2)

    print("\n✅ Analysis complete! Saved to tmp/analysis_results.json")

if __name__ == "__main__":
    analyze_all()
