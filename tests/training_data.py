import csv
import requests
from pathlib import Path
import random
import string

def generate_training_data(csv_file):
    training_data = []

    with open(csv_file, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            master_name = row['name'].strip()
            master_code = ''.join(random.choices(string.ascii_uppercase, k=6))
            training_data.append({"vendor_name": master_name, "master_code": master_code})
            training_data.append({"vendor_name": master_name[:-1], "master_code": master_code})
            training_data.append({"vendor_name": master_name[:-2], "master_code": master_code})
            training_data.append({"vendor_name": master_name[:-3], "master_code": master_code})
            training_data.append({"vendor_name": master_name[:-4], "master_code": master_code})
            training_data.append({"vendor_name": master_name[:-5], "master_code": master_code})
            training_data.append({"vendor_name": master_name[:-6], "master_code": master_code})
            training_data.append({"vendor_name": master_name[:-7], "master_code": master_code})
            training_data.append({"vendor_name": master_name[:-8], "master_code": master_code})
            training_data.append({"vendor_name": master_name[:-9], "master_code": master_code})
            training_data.append({"vendor_name": master_name[:-10], "master_code": master_code})

    return training_data

def chunked(iterable, size):
    for i in range(0, len(iterable), size):
        yield iterable[i:i + size]

# Usage
csv_file = Path(__file__).parent / 'medicines_dataset.csv'
training_data = generate_training_data(csv_file)

# Print first 10 examples
for item in training_data[:10]:
    print(item)

# Send to FastAPI /train endpoint in batches
url = "http://127.0.0.1:8001/train"
batch_size = 50
for idx, batch in enumerate(chunked(training_data, batch_size)):
    response = requests.post(url, json=batch)
    print(f"Batch {idx+1}: POST /train status: {response.status_code}")
    try:
        print("Response:", response.json())
    except Exception:
        print("Response content:", response.content)