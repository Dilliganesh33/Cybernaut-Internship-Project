import requests
import pandas as pd
from bs4 import BeautifulSoup
import time
import os
from dotenv import load_dotenv

# load API keys from .env file (keeps secrets safe)
load_dotenv()
APIFY_TOKEN = os.getenv("APIFY_TOKEN")
ACTOR_ID = os.getenv("ACTOR_ID")

# ask user for the job they want to search
job_title = input("Enter job title: ")

# trigger the Apify actor run (starts a new scraper job)
url = f"https://api.apify.com/v2/acts/{ACTOR_ID}/runs?token={APIFY_TOKEN}"
payload = {
    "startUrls": [{"url": f"https://www.indeed.com/jobs?q={job_title}"}],
    "maxResults": 100
}
response = requests.post(url, json=payload)
run_data = response.json()
run_id = run_data["data"]["id"]   # unique ID for this scraper run

# check status of the scraping job until it's done
status_url = f"https://api.apify.com/v2/acts/{ACTOR_ID}/runs/{run_id}?token={APIFY_TOKEN}"

print("\n⏳ Fetching jobs... Please wait, it may take up to a minute.\n")

while True:
    status_response = requests.get(status_url).json()
    status = status_response["data"]["status"]
    if status in ["SUCCEEDED", "FAILED", "ABORTED"]:
        break   # stop waiting once job finishes
    print("...still fetching, please wait...")
    time.sleep(5)  # wait before checking again

# once finished, grab the dataset ID (where results are stored)
dataset_id = status_response["data"]["defaultDatasetId"]
dataset_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?format=json&token={APIFY_TOKEN}"
data = requests.get(dataset_url).json()

cleaned = []
for job in data:
    # job descriptions come as HTML, so convert to plain text
    desc_html = job.get("descriptionHTML", "")
    soup = BeautifulSoup(desc_html, "html.parser")
    desc_text = soup.get_text(" ", strip=True)

    # collect only useful fields into a clean dict
    cleaned.append({
        "Job Title": job.get("positionName"),
        "Company": job.get("company"),
        "Location": job.get("location"),
        "Salary": job.get("salary"),
        "Job Type": ", ".join(job.get("jobType", [])) if job.get("jobType") else "",
        "Rating": job.get("rating"),
        "Reviews": job.get("reviewsCount"),
        "Posted": job.get("postedAt"),
        "Apply Link": job.get("externalApplyLink") or job.get("url"),
        "Description": desc_text
    })

# convert list of jobs into a DataFrame and save to Excel
df = pd.DataFrame(cleaned)
df.to_excel(f"{job_title}_cleaned_jobs.xlsx", index=False)
print(f"\nSaved cleaned jobs to {job_title}_cleaned_jobs.xlsx")
