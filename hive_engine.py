# TIMESTAMP: 2026-02-23 15:30:00
import urllib.request
import json
import os
import time
import re

# v74.5 - API Driven Master (No Docker dependency)
BASE_API = os.getenv('RAE_API_URL', 'http://rae-api-dev:8000')
if not BASE_API.endswith('/'): BASE_API += '/'
API_URL = BASE_API + "v2/memories" 
OUT_DIR = '/app/work_dir/components/'
HEADERS = {'X-API-Key': 'test-key', 'X-Tenant-Id': '00000000-0000-0000-0000-000000000000'}

def log_msg(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

def is_processed(filename):
    if not filename: return True
    # Check for folder (giant) or file (standard)
    folder_name = filename.replace('.js', '').replace('.html', '')
    if os.path.exists(os.path.join(OUT_DIR, folder_name)): return True
    target_file = filename.replace('.js', '.tsx').replace('.html', '.tsx')
    return os.path.exists(os.path.join(OUT_DIR, target_file))

def http_req(url, data=None, method='GET'):
    body = json.dumps(data).encode('utf-8') if data else None
    headers = {'Content-Type': 'application/json', **HEADERS} if data else HEADERS
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=120) as f:
            return json.loads(f.read().decode('utf-8'))
    except: return {}

def ask_saas(model, prompt, system=""):
    try:
        payload = {"content": "SYSTEM: " + system + "\nUSER: " + prompt[:30000], "layer": "reflective", "tags": ["hive_call", model]}
        res = http_req(API_URL + "/", payload, 'POST')
        return res.get('message', '')
    except: return ""

def get_full_source(filename):
    # Fetch through API search
    try:
        url = f"{API_URL}/?q={filename}&limit=200"
        res = http_req(url)
        results = res.get('results', [])
        # Sort and assemble
        file_chunks = [r for r in results if r.get('metadata', {}).get('file') == filename]
        file_chunks.sort(key=lambda x: int(x.get('metadata', {}).get('chunk_index', 0)))
        return "".join([c['content'] for c in file_chunks])
    except: return ""

def process_one(mem):
    filename = mem.get('metadata', {}).get('file')
    if not filename or is_processed(filename): return
    
    log_msg(f"🔥 Processing: {filename}")
    source = get_full_source(filename)
    if not source: return

    # Giant vs Standard
    total_chunks = mem.get('metadata', {}).get('total_chunks', 1)
    
    if total_chunks > 20:
        # Giant strategy: Simple decomposition
        log_msg(f"🏗️  Decomposing Giant: {filename}")
        # Implementation of decomposition logic here...
    else:
        # Standard strategy
        target_name = filename.replace('.js', '.tsx').replace('.html', '.tsx')
        code = ask_saas("gemini-2.5-pro", f"Modernize to Next.js/TSX:\n{source}", "Senior Dev")
        if len(code) > 100:
            if '```' in code:
                try: code = re.search(r'```(?:tsx|ts)?\n(.*?)\n```', code, re.DOTALL).group(1).strip()
                except: pass
            with open(os.path.join(OUT_DIR, target_name), 'w') as f: f.write(code)
            log_msg(f"✅ SUCCESS: {target_name}")

if __name__ == '__main__':
    if not os.path.exists(OUT_DIR): os.makedirs(OUT_DIR)
    log_msg("🚀 STARTING API-DRIVEN v74.5...")
    while True:
        try:
            # Fetch work through API
            data = http_req(API_URL + "/?tag=modernization_v3&limit=50")
            mems = data.get('results', [])
            for m in mems:
                process_one(m)
            time.sleep(30)
        except Exception as e:
            log_msg(f"💥 Error: {e}")
            time.sleep(30)
