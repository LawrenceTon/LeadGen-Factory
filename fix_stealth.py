import gradio as gr
import requests
import json
import os

# ==========================================
# 1. PASTE YOUR KEY HERE
# ==========================================
API_KEY = "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" 

# ==========================================
# 2. MAGIC MODEL SELECTOR
# ==========================================
# We use "openrouter/free" so it AUTOMATICALLY picks a working model.
# You will never get a "Model ID not found" error again.
MODEL = "openrouter/free"

LOREBOOK_FILE = "lorebook.json"

def check_lorebook(user_input):
    if not os.path.exists(LOREBOOK_FILE): return ""
    try:
        with open(LOREBOOK_FILE, 'r', encoding='utf-8') as f:
            lore = json.load(f)
    except:
        return ""
    
    found_lore = []
    for entry in lore:
        for keyword in entry['keywords']:
            if keyword.lower() in user_input.lower():
                print(f"--> Knowledge Activated: {entry['title']}")
                found_lore.append(entry['content'])
                break 
    return "\n".join(found_lore)

def chat_function(message, history):
    active_knowledge = check_lorebook(message)
    formatted_history = []
    for human, assistant in history:
        formatted_history.append({"role": "user", "content": human})
        formatted_history.append({"role": "assistant", "content": assistant})
        
    system_prompt = "You are a helpful AI assistant."
    if active_knowledge:
        system_prompt += f"\n[RELEVANT KNOWLEDGE]: {active_knowledge}"
    
    messages = [{"role": "system", "content": system_prompt}] + formatted_history + [{"role": "user", "content": message}]

    headers = {
        "Authorization": f"Bearer {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}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:7860", 
        "X-Title": "Python Tavern"
    }
    
    # We use the Auto-Router to find the best free model
    payload = {
        "model": MODEL, 
        "messages": messages,
    }
    
    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
        
        if response.status_code != 200:
            return f"Error: {response.text}"
            
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"Connection Error: {e}"

app = gr.ChatInterface(fn=chat_function, title="Fresh Start AI", description="Using Auto-Free Router")

if __name__ == "__main__":
    app.launch()