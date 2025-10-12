# Terms & Conditions Analyzer ⚖️

An AI-powered tool to analyze and summarize legal documents like Terms of Service, rental agreements, and insurance policies, highlighting potential risks.

---

## Key Features

* **Multi-Document Analysis:** Supports Software ToS, Leases, Insurance Policies, and Loan Agreements.
* **AI-Powered Summaries:** Uses a powerful AI model to generate clear summaries for each section.
* **Intuitive Risk Gauge:** Displays a single, color-coded risk level (Low, Moderate, High) for an immediate at-a-glance assessment of the document.
* **Interactive Jargon Buster:** Automatically identifies common legal terms and provides definitions in a popover. Also includes a sidebar tool to look up any word using an online dictionary.
* **Editable Configuration:** A dedicated tab allows users to modify the keywords and risk scores for the current session, providing full control over the analysis.
* **Risk Scoring & Highlighting:** Flags clauses as Low, Medium, or High risk and highlights the trigger keywords.
* **PDF Report Export:** Generates a clean, downloadable PDF report of the complete analysis.

---

## Installation and Usage

Follow these steps to set up and run the project on your local machine.

### Dependencies

=======
This project requires the following Python libraries. You can install them using the `requirements.txt` file provided in the next step.

* `streamlit`
* `pdfplumber`
* `reportlab`
* `transformers`
* `torch`
* `nltk`
* `requests`
* `sentencepiece`

### Instructions

1.  **Clone the Repository**
    ```bash
    git clone [https://github.com/YourUsername/your-repo-name.git](https://github.com/YourUsername/your-repo-name.git)
    cd your-repo-name
    ```

2.  **Create a `requirements.txt` File**
    Create a new file named `requirements.txt` in the project folder and paste the following content into it:
    ```text
    streamlit
    pdfplumber
    reportlab
    transformers
    torch
    nltk
    requests
    sentencepiece
    ```

3.  **Set Up a Virtual Environment (Recommended)**
    * **On macOS/Linux:**
        ```bash
        python3 -m venv venv
        source venv/bin/activate
        ```
    * **On Windows:**
        ```bash
        python -m venv venv
        .\venv\Scripts\activate
        ```

4.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

5.  **Run the App**
    ```bash
    streamlit run app.py
    ```
---
## About This Project

This project was developed in collaboration with Google's Gemini. The core logic, code, and debugging were achieved through a process of guided prompting, testing, and refinement.
