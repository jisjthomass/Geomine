with open("api_client.py", "r") as f:
    text = f.read()

text = text.replace('print(f"\\n\\n=== API REQUEST FAILED: {error} ===\\n\\n", flush=True)\\n        fallback_response["error"] = str(error)', 
                    'print(f"\\n\\n=== API REQUEST FAILED: {error} ===\\n\\n", flush=True)\n        fallback_response["error"] = str(error)')

with open("api_client.py", "w") as f:
    f.write(text)
