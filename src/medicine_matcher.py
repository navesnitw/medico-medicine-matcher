from fastapi import FastAPI, HTTPException, Request, Body
import uvicorn
from typing import List, Dict
from pydantic import BaseModel
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import os
from app.mysql_vendor_repository import MySQLVendorRepository
from app.mysql_master_repository import MySQLMasterRepository

class MedicineMapping(BaseModel):
    vendor_name: str 
    master_code: str

class MedicineMatcher:
    def __init__(self, mysql_master_repo : MySQLMasterRepository, mysql_vendor_repo: MySQLVendorRepository):
        self.mysql_master_repo = mysql_master_repo
        self.mysql_vendor_repo = mysql_vendor_repo
        self.vendor_medicine_dict = {}
        self.master_medicines_dict = {}
        self.master_code_dict = {}

    def load_master_data(self):
        master_data = self.mysql_master_repo.get_master_data()
        self.master_medicines_dict = {master_name.lower() : (master_name, master_code, master_id) for (master_name, master_code, master_id) in master_data}
        self.master_code_dict = {master_code: (master_name, master_id) for (master_name, master_code, master_id) in master_data}
        print(f"Loaded {len(self.master_medicines_dict)} medicines from MySQL Master repository.")

    def load_vendor_mappings(self):
        medicines = self.mysql_vendor_repo.get_all_medicines()
        self.vendor_medicine_dict = {name.strip().lower(): master_code for name, master_code in medicines.items()}
        print(f"Loaded {len(self.vendor_medicine_dict)} medicines from MySQL Vendor repository.")

    def train(self, examples: List[MedicineMapping]):
        training_data = {}
        for ex in examples:
            if not ex.vendor_name.strip() or not ex.master_code.strip():
                print(f"Skipping invalid example: {ex}")
                continue
            training_data[ex.vendor_name.strip().lower()] = ex.master_code.strip()
        self.vendor_medicine_dict.update(training_data)
        self.mysql_vendor_repo.save_medicines(training_data)
    
    def find_matches(self, vendor_name: str) -> Dict[str, str]:
        vendor_name_lower = vendor_name.strip().lower()
        if vendor_name_lower in self.master_medicines_dict:
            (master_name, master_code, master_id) = self.master_medicines_dict[vendor_name_lower]
            return {"name": master_name, "code": master_code, "id": str(master_id)}
        if vendor_name_lower in self.vendor_medicine_dict:
            master_code = self.vendor_medicine_dict[vendor_name_lower]
            result = self.master_code_dict.get(master_code)
            if result is not None:
                (master_name, master_id) = result
                return {"name": master_name, "code": master_code, "id": str(master_id)}
        return {}
    
    def delete_mappings(self, vendor_names: List[str]):
        cleaned_names = [name.strip().lower() for name in vendor_names if name and name.strip()]
        for name in cleaned_names:
            self.vendor_medicine_dict.pop(name, None)
        self.mysql_vendor_repo.delete_medicines(cleaned_names)

def get_matcher(request: Request) -> MedicineMatcher:
    return request.app.state.matcher

@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    print("Initializing Medicine Matcher...")

    loaded = load_dotenv()
    if not loaded:
        raise RuntimeError("Failed to load environment variables from .env file")
    
    host = os.getenv("DB_HOST")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    database = os.getenv("DB_NAME")
    port = os.getenv("DB_PORT", 3306)

    mysql_master_repo = MySQLMasterRepository(host, user, password, database, port)

    mysql_repo = MySQLVendorRepository(
        host=host,
        user=user,
        password=password,
        database=database,
        port=port
    )
    matcher = MedicineMatcher(mysql_master_repo=mysql_master_repo, mysql_vendor_repo=mysql_repo)
    matcher.load_master_data()
    matcher.load_vendor_mappings()
    fastapi_app.state.matcher = matcher
    print("Medicine Matcher initialized.")
    yield
    print("Shutting down Medicine Matcher...")
    mysql_repo.close()

app = FastAPI(title="Medicine Name Matcher API", lifespan=lifespan)

@app.post("/train")
async def train(examples: List[MedicineMapping], request: Request):
    if not examples:
        raise HTTPException(status_code=400, detail="No medicine mappings provided")
    matcher = get_matcher(request)
    matcher.train(examples)
    return {"message": f"Medicine mapping data updated. Count : {len(examples)}"}

@app.get("/find_match")
async def find_match_endpoint(vendor_name: str, request: Request) -> Dict[str, str]:
    matcher = get_matcher(request)
    match = matcher.find_matches(vendor_name)
    if not match:
        raise HTTPException(status_code=404, detail="No mappings found for the given vendor name")
    return match

@app.delete("/delete_mappings")
async def delete_mappings(request: Request, vendor_names: List[str] = Body(...)):
    matcher = get_matcher(request)
    matcher.delete_mappings(vendor_names)
    return {"message": f"Deleted {len(vendor_names)} vendor medicine mappings."}

if __name__ == "__main__":
    print("Starting Medicine Matcher API via Uvicorn...")
    uvicorn.run("medicine_matcher:app", host="127.0.0.1", port=8001)
