import requests
import json 
API_URL = "http://localhost:8000/process"


def fetch_bin_data(file_path: str, api_url: str = API_URL):
    try:
        with open(file_path, "rb") as f:
            files = {
                "file": (file_path, f, "application/octet-stream")
            }

            response = requests.post(
                api_url,
                files=files,   # 👈 IMPORTANT
                timeout=120
            )

        response.raise_for_status()

        content = response.content.decode("utf-8")
        
        return [
            json.loads(line)
            for line in content.splitlines()
            if line.strip()
        ]

    except Exception as e:
        raise RuntimeError(f"Request failed: {e}")