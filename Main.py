import os
import time
import fitz  # PyMuPDF for PDF parsing
import matplotlib.pyplot as plt
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def download_pdf(download_dir):
    options = webdriver.ChromeOptions()
    prefs = {"download.default_directory": download_dir}
    options.add_experimental_option("prefs", prefs)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        driver.get("https://sustainability.google/reports/")
        time.sleep(3)  

        pdf_link = driver.find_element(By.XPATH, '/html/body/div/div/div[1]/div/div[2]/ul[1]/li[1]/div[2]/a')
        pdf_link.click()
        time.sleep(5)  
    finally:
        driver.quit()


def extract_data_from_pdf(pdf_path):
    data = {
        "Scope 1 Emissions": None,
        "Scope 2 Emissions": None,
        "Hazardous Waste Produced": None,
        "Primary Energy Sources": {},
        "Water Consumption": None,
        "Decarbonization Plan": None,
        "Biodiversity Impact": None,
    }

    with fitz.open(pdf_path) as pdf:
        for page in pdf:
            text = page.get_text()

            
            if "Scope 1" in text:
                data["Scope 1 Emissions"] = extract_numeric_value(text, "Scope 1 GHG emissions")
            if "Scope 2" in text:
                data["Scope 2 Emissions"] = extract_numeric_value(text, "Scope 2 GHG emissions")

            
            if "Hazardous waste" in text:
                data["Hazardous Waste Produced"] = extract_value_by_context(text, "Hazardous waste produced")

            for source in ["coal", "gas", "diesel", "heating oil", "electricity"]:
                if source in text:
                    data["Primary Energy Sources"][source] = extract_value_by_context(text, source)

            
            if "water consumption" in text:
                data["Water Consumption"] = extract_value_by_context(text, "water consumption")

            
            if "decarbonization" in text or "carbon offset" in text:
                data["Decarbonization Plan"] = extract_value_by_context(text, "decarbonization plan")

            
            if "biodiversity" in text:
                data["Biodiversity Impact"] = text

    return data


def extract_numeric_value(text, keyword):
    try:
        start = text.index(keyword) + len(keyword)
        end = start + 50  # Limit search to a small text segment
        value = ''.join([s for s in text[start:end].split() if s.isdigit() or '.' in s])
        return value
    except ValueError:
        return None

def extract_value_by_context(text, keyword):
    if keyword in text:
        idx = text.index(keyword) + len(keyword)
        return text[idx:idx + 50].split('.')[0]  # Extract short context
    return None


def generate_pivot_charts(data):
    
    ghg_labels = ["Scope 1", "Scope 2"]
    ghg_values = [float(data["Scope 1 Emissions"] or 0), float(data["Scope 2 Emissions"] or 0)]
    plt.figure(figsize=(8, 6))
    plt.pie(ghg_values, labels=ghg_labels, autopct='%1.1f%%', startangle=140)
    plt.title("Scope 1 and Scope 2 GHG Emissions")
    plt.show()

   
    energy_labels = list(data["Primary Energy Sources"].keys())
    energy_values = [float(v) for v in data["Primary Energy Sources"].values()]
    plt.figure(figsize=(8, 6))
    plt.pie(energy_values, labels=energy_labels, autopct='%1.1f%%', startangle=140)
    plt.title("Primary Energy Source Consumption (GWh)")
    plt.show()


if __name__ == "__main__":
    download_directory = "./downloads"
    os.makedirs(download_directory, exist_ok=True)
    
    download_pdf(download_directory)
    pdf_path = os.path.join(download_directory, "google-2024-environmental-report.pdf")
    
    if os.path.exists(pdf_path):
        extracted_data = extract_data_from_pdf(pdf_path)
        generate_pivot_charts(extracted_data)
    else:
        print("PDF file not found.")
