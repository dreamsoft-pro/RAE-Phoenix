import os, json, psycopg2

COMP_DIR = '/home/operator/RAE-Suite-Modular/packages/rae-hive/work_dir/components/'
DREAMSOFT_TENANT = 'd7ea3501-de04-4e11-894a-d80ca08de7e8'

def run_ingest():
    conn = psycopg2.connect("host=localhost dbname=rae user=rae password=rae_password")
    conn.autocommit = True
    cur = conn.cursor()

    # Clear previous corrupted data for this project
    cur.execute("DELETE FROM memories WHERE tenant_id = %s", (DREAMSOFT_TENANT,))
    print("Cleaned previous memories.")

    count = 0
    for comp in os.listdir(COMP_DIR):
        base_path = os.path.join(COMP_DIR, comp)
        if not os.path.isdir(base_path): continue
        
        content_file = None
        for target in ['_integrated.tsx', 'code']:
            if os.path.exists(os.path.join(base_path, target)):
                content_file = os.path.join(base_path, target)
                break
                
        if content_file:
            try:
                with open(content_file, 'r', encoding='utf-8') as f: content = f.read()
                metadata = {
                    "project": "dreamsoft-pro", 
                    "service": comp, 
                    "source_file": os.path.basename(content_file),
                    "tech_stack": "NextJS" if content_file.endswith('.tsx') else "AngularJS"
                }
                
                cur.execute("INSERT INTO memories (content, layer, metadata, importance, tenant_id) VALUES (%s, %s, %s, %s, %s)", 
                            (content, 'semantic', json.dumps(metadata), 0.8, DREAMSOFT_TENANT))
                count += 1
                if count % 50 == 0: print(f"PROGRESS: {count} atoms ingested...")
            except Exception as e:
                print(f"Error in {comp}: {e}")

    cur.close()
    conn.close()
    print(f"✅ SUCCESS: {count} components ingested into RAE tenant dreamsoft.")

if __name__ == "__main__":
    run_ingest()
