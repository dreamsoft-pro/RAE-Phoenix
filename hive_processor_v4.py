import httpx
import json
import time
import os
import re

API_URL = 'http://localhost:8001/v2/memories'
OLLAMA_URL = 'http://localhost:11434/api/generate'
TARGET_DIR = '/home/operator/dreamsoft_factory/next-frontend/src/services/'

# Use string concatenation to avoid escape issues
WRITER_PROMPT = "You are a Next.js Expert. Your task is to convert legacy JavaScript services to modern TypeScript classes for Next.js."
WRITER_PROMPT += chr(10) + "STRICT RULES:"
WRITER_PROMPT += chr(10) + "- Use standard classes: export class Name"
WRITER_PROMPT += chr(10) + "- NO Angular decorators, NO RxJS, NO HttpClient"
WRITER_PROMPT += chr(10) + "- Use axios with async/await"
WRITER_PROMPT += chr(10) + "RETURN ONLY CODE."

def ask_ollama(model, prompt):
    try:
        payload = {'model': model, 'prompt': prompt, 'stream': False}
        resp = httpx.post(OLLAMA_URL, json=payload, timeout=600.0)
        return resp.json().get('response', '')
    except Exception as e:
        return 'ERROR'

def process_hive():
    try:
        url = API_URL + '/?tag=modernization_v3&tag=pending&limit=1'
        response = httpx.get(url)
        memories = response.json().get('results', [])
        if not memories: return

        for mem in memories:
            mid = mem['id']
            source = mem['content']
            s_name = 'service_' + mid[:8]
            print('Processing ' + s_name)
            
            full_prompt = WRITER_PROMPT + chr(10) + chr(10) + source
            final = ask_ollama('deepseek-coder-v2:16b', full_prompt)
            
            if 'class' in final or 'export' in final:
                target_file = os.path.join(TARGET_DIR, s_name + '.ts')
                with open(target_file, 'w') as f:
                    f.write(final)
                
                patch_url = API_URL + '/' + mid
                httpx.patch(patch_url, json={'tags': ['modernization_v3', 'completed']})
                print('Success: ' + target_file)
    except Exception as e:
        print('Error')

if __name__ == "__main__":
    if not os.path.exists(TARGET_DIR): os.makedirs(TARGET_DIR)
    print('HIVE V4.3 START')
    while True:
        process_hive()
        time.sleep(5)
