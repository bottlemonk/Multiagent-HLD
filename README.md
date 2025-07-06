Power Apps Code Reviewer and HLD Generator
This project analyzes Microsoft Power Apps code files (JSON or YAML format) and generates structured summaries of individual files, which are then used to create a comprehensive High-Level Design (HLD) document for the entire application.

🧠 Overview
The solution uses a multi-stage pipeline built using langgraph, langchain, and an LLM backend (e.g., LM Studio) to:

Read Power App source files from a directory.
Generate per-file summaries highlighting key features like screens, components, data sources, logic, and navigation.
Aggregate all summaries into a single HLD document that describes the overall architecture, data model, user flow, and business rules.
This tool is ideal for documenting or reverse-engineering Power Apps applications programmatically.

📁 Project Structure


1
2
3
4
5
6
project-root/
├── src/                    # Folder containing Power App JSON/YAML files
│   ├── controls/             # Optional: Folder for JSON screen/component files
│   └── *.fx.yaml             # Optional: YAML configuration files
├── Pasted_Text_1751811826366.txt  # Original script (renamed as needed)
└── README.md                 # This file
🛠️ Dependencies
Ensure you have the following installed before running this script:

Python 3.9+
Required libraries:
langgraph
langchain
IPython (for image display)
pyyaml (if handling YAML files)
A compatible LLM backend (e.g., LM Studio ) serving a model like Qwen at http://192.168.0.110:1234/v1.
Install dependencies via:

bash


1
pip install langgraph langchain ipython pyyaml openai
Note: The OpenAI package is used here due to compatibility with ChatOpenAI, even though it connects to a local server. 

⚙️ Configuration
Update the following in the script if needed:

python


1
2
3
4
5
6
llm = ChatOpenAI(
    openai_api_base="http://localhost:1234/v1",  # Your local LLM server
    openai_api_key="lmstudio",
    model="qwen/qwen3-4b",  # Model name
    temperature=0.1
)
Place your Power Apps files under the src/ directory. The script will prioritize .fx.yaml files first; otherwise, it will read .json files from the controls/ folder.

🚀 How to Run
Place your Power Apps JSON or YAML files in the src/ folder.
Run the script:
bash


1
python app_reviewer.py
The output will be printed to the console, including:
File summaries
Final HLD document
Optionally, uncomment the file-saving block to write the final HLD to a Markdown file. 

📊 Output Example
Per-File Summary


1
2
3
4
5
6
- **File Name:** DetailScreen.json
- **Screen:** DetailScreen (type: Screen) – displays a single customer record.
- **Data sources:** Customers (SharePoint list).
- **Variables:** varSelectedCustomer (stores selected customer ID).
- **Key logic:** OnVisible loads selected customer; OnSelect for Save button triggers patch to Customers.
- **Navigation:** On back button, navigates to HomeScreen.
High-Level Design Document Snippet


1
2
3
4
5
6
7
8
9
10
# High-Level Design Document

## Executive Summary
This Power App serves as a customer management system allowing users to view, edit, and submit customer records...

## Application Architecture Overview
The app consists of the following main screens:
- HomeScreen – lists all customers
- DetailScreen – shows and edits customer details
...
📌 Future Enhancements
Add support for additional file formats (e.g., XML, CSV).
Integrate with UML generation tools to produce diagrams automatically.
Store results in a database or export to PDF/Word.
Add command-line arguments for input/output paths.
✅ License
MIT License – see LICENSE for details.
