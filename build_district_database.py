import json
import time
import vertexai
from vertexai.generative_models import GenerativeModel

# --- Configuration ---
PROJECT_ID = "ny-build-487810"  # Replace with your actual project ID
LOCATION = "us-central1"

# Initialize Vertex AI
vertexai.init(project=PROJECT_ID, location=LOCATION)

# Gemini 1.5 Pro is ideal for heavy research and complex extraction
model = GenerativeModel("gemini-2.0-flash")

# The Top 20 NY Districts (by enrollment/prominence)
ny_districts = [
    "New York City Geographic District #2 (Manhattan)",
    "New York City Geographic District #15 (Brooklyn)",
    "New York City Geographic District #31 (Staten Island)",
    "Buffalo City School District",
    "Rochester City School District",
    "Yonkers City School District",
    "Syracuse City School District",
    "Brentwood Union Free School District",
    "Sachem Central School District",
    "Newburgh Enlarged City School District",
    "East Ramapo Central School District",
    "Wappingers Central School District",
    "Mount Vernon City School District",
    "New Rochelle City School District",
    "Freeport Union Free School District",
    "Central Islip Union Free School District",
    "Utica City School District",
    "Niagara Falls City School District",
    "William Floyd Union Free School District",
    "Hempstead Union Free School District"
]

database = []

print("Starting Vertex AI District Research Engine...")

for district in ny_districts:
    print(f"\nResearching: {district}...")
    
    # The Prompt: Forcing the model to act as a structured data extractor
    prompt = f"""
    You are an expert researcher specializing in New York State public education and Special Education regulations (Part 200).
    Please research the following school district: {district}.
    
    Extract the following data specifically related to their Special Education department and Committee on Special Education (CSE). 
    If a specific phone number or director name cannot be verified, output "Needs Verification".
    
    1. Superintendent Name
    2. Director of Special Education (or Head of Pupil Personnel Services)
    3. Main Special Education Office Phone Number
    4. URL to the District's Special Education/CSE web page
    5. Verify 2-3 standard Special Education forms or packets available on their site (e.g., Initial Referral Form, CPSE to CSE Transition Packet, Procedural Safeguards). Provide the form name and its likely purpose.

    Return the result STRICTLY as a valid JSON object with the following keys:
    "district_name", "superintendent", "special_ed_director", "special_ed_phone", "special_ed_url", "verified_forms".
    
    "verified_forms" should be a list of dictionaries with "form_name" and "purpose".
    Do not include markdown formatting like ```json.
    """

    try:
        # Call Vertex AI
        response = model.generate_content(prompt)
        raw_text = response.text.strip()
        
        # Clean markdown if the model accidentally includes it
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:-3]
        elif raw_text.startswith("```"):
            raw_text = raw_text[3:-3]
            
        # Parse and append to our database
        district_data = json.loads(raw_text)
        database.append(district_data)
        print(f"✓ Data extracted for {district_data.get('district_name', district)}")
        print(f"  Director: {district_data.get('special_ed_director')}")
        print(f"  Phone: {district_data.get('special_ed_phone')}")
        
        # Pause to avoid rate limits
        time.sleep(3)
        
    except json.JSONDecodeError:
        print(f"  [ERROR] Model did not return valid JSON for {district}. Raw output: {raw_text}")
    except Exception as e:
        print(f"  [ERROR] Failed to research {district}: {str(e)}")

# Save to a master JSON file
output_file = "ny_special_ed_directory.json"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(database, f, indent=4)

print(f"\nDatabase generation complete! Saved to {output_file}")