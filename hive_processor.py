import httpx
import json
import time
import os
import re

API_URL = 'http://localhost:8001/v2/memories'
OLLAMA_URL = 'http://localhost:11434/api/generate'
TARGET_DIR = '/home/operator/dreamsoft_factory/next-frontend/src/services/'

# ULTRA SIMPLE PROMPT
PROMPT = "Convert this legacy JS code to a PLAIN TypeScript class for Next.js. Use axios. NO Angular decorators. NO RxJS. Output ONLY code."

def ask_ollama(model, prompt):
    try:
        payload = {'model': model, 'prompt': prompt, 'stream': False}
        resp = httpx.post(OLLAMA_URL, json=payload, timeout=600.0)
        return resp.json().get('response', '')
    except Exception:
        return ''

def process_hive():
    try:
        url = API_URL + '/?tag=modernization_v3&tag=pending&limit=1'
        response = httpx.get(url)
        memories = response.json().get('results', [])
        if not memories: 
            print('No pending tasks.')
            return

        for mem in memories:
            mid = mem['id']
            source = mem['content']
            s_name = 'service_' + mid[:8]
            print('Working on ' + s_name)
            
            full_prompt = PROMPT + chr(10) + chr(10) + source
            final = ask_ollama('qwen2.5-coder:14b', full_prompt)
            
            # Clean up markdown
            if '```' in final:
                try:
                    final = final.split('```')[1]
                    if final.startswith('typescript'): final = final[10:]
                    if final.startswith('ts'): final = final[2:]
                except: pass

            if len(final) > 10:
                target_file = os.path.join(TARGET_DIR, s_name + '.ts')
                with open(target_file, 'w') as f:
                    f.write(final)
                
                # Mark as completed regardless of content quality to prevent loops
                patch_url = API_URL + '/' + mid
                httpx.patch(patch_url, json={'tags': ['modernization_v3', 'completed']})
                print('Saved ' + target_file)
            else:
                print('Empty response from model')
    except Exception as e:
        print('Error in loop')

if __name__ == "__main__":
    if not os.path.exists(TARGET_DIR): os.makedirs(TARGET_DIR)
    print('HIVE V4.4 (FINAL) START')
    while True:
        process_hive()
        time.sleep(2)
