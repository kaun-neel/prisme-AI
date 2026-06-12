import os
import json
import re
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate

load_dotenv()
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "https://ollama.com/v1")
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "dummy-key")

def analyze_code(code_sample):
    print("Waking up Prism Code Analysis Agent...")
    
    llm = ChatOpenAI(
        model="gpt-oss:120b-cloud", 
        temperature=0.1, 
        api_key=OLLAMA_API_KEY,
        base_url=OLLAMA_BASE_URL,
        max_tokens=2000
    ) 
    
    prompt = PromptTemplate(
        input_variables=["code"],
        template="""
        You are an elite Splunk Observability Architect and Code Reviewer.
        Analyze the following application code for observability gaps, latency bottlenecks, and unhandled errors.
        
        CODE TO ANALYZE:
        -----------------------------------
        {code}
        -----------------------------------
        
        Return ONLY a valid JSON object matching this exact schema. Do not include markdown formatting, backticks, or conversational text.
        {{
            "risks": [
                {{"level": "critical", "message": "Describe the code risk (e.g. DB leaks, missing timeouts)"}},
                {{"level": "high", "message": "Describe another risk"}}
            ],
            "spl_queries": [
                {{"name": "Query Name", "viz": "Timechart", "spl": "index=app | timechart avg(duration)"}}
            ],
            "alerts": [
                {{"severity": "critical", "name": "Alert Name", "condition": "Trigger condition", "spl": "index=app status=failed | stats count"}}
            ],
            "dashboard_panels": [
                {{"title": "Panel Title", "desc": "What this panel tracks"}}
            ],
            "logging_recs": [
                "Specific line of logging code to add"
            ]
        }}
        """
    )
    
    chain = prompt | llm
    
    try:
        response = chain.invoke({"code": code_sample})
        raw_text = response.content
        json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        
        if json_match:
            clean_json = json_match.group(0)
        else:
            clean_json = raw_text
            
        data = json.loads(clean_json)
        print("Successfully parsed AI JSON response!")
        return data
        
    except Exception as e:
        print(f"AI Parsing Error: {e}")
        return {
            "risks": [
                {"level": "critical", "message": f"AI Parsing Error: {str(e)[:50]}..."},
            ],
            "spl_queries": [],
            "alerts": [],
            "dashboard_panels": [],
            "logging_recs": ["Could not parse LLM output. Try again."]
        }