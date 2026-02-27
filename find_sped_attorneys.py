import vertexai
import json
import csv
import time
from vertexai.generative_models import GenerativeModel, Tool, GenerationConfig
from google.api_core.exceptions import GoogleAPIError

# =========================
# CONFIGURE THIS
# =========================
PROJECT_ID = "ny-build-487810"
LOCATION = "us-central1"

# =========================
# INIT VERTEX
# =========================
vertexai.init(project=PROJECT_ID, location=LOCATION)

model = GenerativeModel(
    model_name="gemini-2.0-flash",
    tools=[Tool.from_dict({"google_search": {}})]
)

generation_config = GenerationConfig(
    temperature=0.2,
    max_output_tokens=2048
)

# =========================
# ALL DISTRICTS FROM HTML
# =========================
DISTRICTS = [
    "Albany City SD", "Brentwood UFSD", "Buffalo City SD", "Central Islip UFSD", 
    "District 1", "District 10", "District 11", "District 12", "District 13", 
    "District 14", "District 15", "District 16", "District 17", "District 18", 
    "District 19", "District 2", "District 20", "District 21", "District 22", 
    "District 23", "District 24", "District 25", "District 26", "District 27", 
    "District 28", "District 29", "District 3", "District 30", "District 31", 
    "District 32", "District 4", "District 5", "District 6", "District 7", 
    "District 75", "District 79", "District 8", "District 9", "Freeport UFSD", 
    "Hempstead UFSD", "Mount Vernon City SD", "New Rochelle City SD", 
    "Newburgh Enlarged City SD", "Niagara Falls City SD", "Poughkeepsie City SD", 
    "Rochester City SD", "Schenectady City SD", "Syracuse City SD", "Utica City SD", 
    "White Plains City SD", "William Floyd UFSD", "Yonkers City SD"
]

# =========================
# FUNCTION
# =========================
def search_sped_attorneys(district_name, csv_filename="sped_attorneys.csv"):
    # Optimize search query for NYC districts so the search tool doesn't get confused
    search_term = f"NYC {district_name}" if district_name.startswith("District") else f"{district_name} New York"
    
    prompt = f"""
    Find 3 to 5 special education attorneys or law firms serving {search_term}.
    Respond ONLY with a valid JSON array of objects. Do not use markdown blocks (no ```json). 
    Do not include any other text. Each object must have these exact keys:
    "attorney_name", "law_firm", "website", "phone_number", "city".
    If no results are found, return an empty array [].
    """

    try:
        print(f"Searching for: {search_term}...")
        response = model.generate_content(prompt, generation_config=generation_config)

        if response.candidates:
            raw_text = response.candidates[0].content.parts[0].text
            
            # Clean up potential markdown formatting the model might try to sneak in
            clean_text = raw_text.replace('```json', '').replace('```', '').strip()
            
            try:
                data = json.loads(clean_text)
                
                if not data:
                    print(f"  ⚠ Model returned empty array for {district_name}")
                    return

                # Append to CSV
                with open(csv_filename, "a", newline="", encoding="utf-8") as file:
                    writer = csv.writer(file)
                    for item in data:
                        writer.writerow([
                            district_name,
                            item.get("attorney_name", "N/A"),
                            item.get("law_firm", "N/A"),
                            item.get("website", "N/A"),
                            item.get("phone_number", "N/A"),
                            item.get("city", "N/A")
                        ])
                print(f"  ✅ Saved {len(data)} results for {district_name}")
                
            except json.JSONDecodeError:
                print(f"  ❌ Failed to parse JSON for {district_name}. Raw output: {raw_text[:100]}...")
                
        else:
            print(f"  ⚠ No candidates returned for {district_name}")

    except GoogleAPIError as e:
        print(f"  ❌ Vertex API Error for {district_name}: {e}")
    except Exception as e:
        print(f"  ❌ Unexpected error for {district_name}: {e}")

# =========================
# EXECUTION
# =========================
if __name__ == "__main__":
    output_csv = "sped_attorneys.csv"
    
    # 1. Initialize CSV with headers
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["District", "Attorney Name", "Law Firm", "Website", "Phone Number", "City"])
    
    print(f"Starting search for {len(DISTRICTS)} districts. This may take a few minutes...\n")
    
    # 2. Loop through all districts
    for district in DISTRICTS:
        search_sped_attorneys(district, csv_filename=output_csv)
        # Adding a short delay to avoid hitting rate limits too quickly
        time.sleep(2) 
        
    print(f"\n🎉 All done! Data is ready in {output_csv}")