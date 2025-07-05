import csv
import json
import requests
import time
import random
import re

# Path to your CSV file
CSV_FILE = 'Promt.csv'
# Workflow file to use as a template
WORKFLOW_FILE = 'Workflowtest.json'
# ComfyUI's prompt endpoint URL
COMFYUI_URL = 'http://192.168.0.204:8188/prompt'
# The column name for positive prompts in your CSV
PROMPT_COLUMN = 'Promt(positive)'
# The column name for character name in your CSV
NAME_COLUMN = 'Tên'

# Helper to sanitize filename
def sanitize_filename(name):
    return re.sub(r'[^a-zA-Z0-9_-]', '_', name)

# Helper to update the positive prompt and filename in the workflow
# (node id 6 for prompt, node id 9 for filename_prefix)
def update_workflow_prompt(workflow, prompt, filename_prefix):
    # For API-style workflow: set the 'text' field in node '6' (CLIPTextEncode)
    if '6' in workflow and workflow['6']['class_type'] == 'CLIPTextEncode':
        workflow['6']['inputs']['text'] = prompt
    # Randomize the seed in node '3' (KSampler)
    if '3' in workflow and workflow['3']['class_type'] == 'KSampler':
        workflow['3']['inputs']['seed'] = random.randint(0, 2**63 - 1)
    # Set the filename_prefix in node '9' (SaveImage)
    if '9' in workflow and workflow['9']['class_type'] == 'SaveImage':
        workflow['9']['inputs']['filename_prefix'] = filename_prefix
    return workflow

def main():
    # Load workflow template
    with open(WORKFLOW_FILE, 'r', encoding='utf-8') as wf:
        workflow_template = json.load(wf)
    
    # Read prompts from CSV
    with open(CSV_FILE, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        rows = [row for row in reader if row.get(PROMPT_COLUMN, '').strip()]
    
    for idx, row in enumerate(rows, 1):
        prompt = row.get(PROMPT_COLUMN, '').strip()
        name = row.get(NAME_COLUMN, f'img_{idx}').strip()
        filename_prefix = sanitize_filename(name)
        # Prepare workflow for this prompt
        workflow = update_workflow_prompt(json.loads(json.dumps(workflow_template)), prompt, filename_prefix)
        # Send to ComfyUI
        try:
            #Reminder: watch for the endpoint URL and payload structure  
            response = requests.post(COMFYUI_URL, json={"prompt": workflow})
            #end of reminder
            response.raise_for_status()
            print(f"[{idx}/{len(rows)}] Sent prompt: {prompt[:60]}... Filename: {filename_prefix} Success!")
        except Exception as e:
            print(f"[{idx}/{len(rows)}] Error sending prompt: {e}")
            print(f"Prompt: {prompt}")
            print(f"Payload: {json.dumps(workflow)[:1000]}...\n")
            continue
        # Optional: wait a bit between requests to avoid overloading
        time.sleep(1)

if __name__ == '__main__':
    main()
