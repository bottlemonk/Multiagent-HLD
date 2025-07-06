import os
from typing import TypedDict, Dict, Any, List, Optional
from IPython.display import Image, display
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import SystemMessage, HumanMessage
from langchain.chat_models import ChatOpenAI

# Define State
class FileData(TypedDict):
    file_path: str
    content: str

class FileSummary(TypedDict):
    file_name: str  # Use file_path or file_name depending on actual keys
    summary: str  # The output from the LLM for this file

class State(TypedDict):
    files: Dict[str, Any]  # Should still contain 'app_files': List[FileData], possibly errors too
    file_summaries: List[FileSummary]  # <--- List of per-file summaries, added for this agent step
    usecase_prompt: Optional[str]  # For later agent steps – can be optional/None here
    use_case: Optional[str]  # For later agent steps – can be optional/None here


# Initialise the Large Language Model
llm = ChatOpenAI(
    openai_api_base="http://localhost:1234/v1",
    openai_api_key="lmstudio",
    model="qwen/qwen3-4b",
    temperature=0.1
)

# System Prompts
node1_prompt = """
You are a Microsoft Power Apps code reviewer.

Your task is to **analyze the following single Power App code file** (in JSON or YAML) and generate a structured, concise summary of its key features and logic. This summary will be used later to construct a full application UML diagram and documentation.

------------------------------------------------------------------------------
For this ONE file, identify:
------------------------------------------------------------------------------

1. **File name** (if available).
2. **Screens, Components, or Entities** defined or referenced within this file.
   - For each: **Name**, **Type** (e.g., Screen, Component), **Purpose**.
3. **Data sources, variables, collections** referenced or defined.
   - For each: Name, type (variable, collection, etc.), and any field/type info.
4. **Key logic or navigation**
   - User actions, triggers, OnSelect/OnStart, important formulas or rules.
5. **Interactions or relationships**
   - Interactions with other files/components (if discernible).
6. **Any business rules or special processing**.

------------------------------------------------------------------------------
Required Output
------------------------------------------------------------------------------

Produce a clear, **structured summary** (bullet points or short paragraphs) of the above for this specific file. **Do not attempt to summarize the entire app or reference other files.**

This summary will be saved for later aggregation.

------------------------------------------------------------------------------
Example output:
------------------------------------------------------------------------------

- **File Name:** DetailScreen.json
- **Screen:** DetailScreen (type: Screen) – displays a single customer record.
- **Data sources:** Customers (SharePoint list).
- **Variables:** varSelectedCustomer (stores selected customer ID).
- **Key logic:** OnVisible loads selected customer; OnSelect for Save button triggers patch to Customers.
- **Navigation:** On back button, navigates to HomeScreen.

*Only output a summary for this one file.*
/nothink
/no_think
"""
system_prompt_hld = """
You are an expert Power Apps architect.

You are given a set of individual file summaries, each describing one part of a Microsoft Power App project. These summaries include screens, components, data sources, variables, logic, navigation, and relationships.

Your task is to **analyze, consolidate, and synthesize** these per-file summaries into a single, detailed, and coherent High-Level Design (HLD) document for the entire application.

-------------------------------------------------------------------------------
Your HLD document must include:
-------------------------------------------------------------------------------
1. **Executive Summary** – High-level purpose and business context of the app.
2. **Application Architecture Overview** – Key modules, screens, components, and how they fit together.
3. **Data Model** – All entities, data sources, collections, and relationships (tables, lists, variables, etc.).
4. **Navigation and User Flow** – Major navigation paths and typical user journeys.
5. **Custom Logic and Key Interactions** – Important formulas, triggers, and business rules.
6. **Integration Points** – Any connections to external services, APIs, or data sources.
7. **Special Features or Business Rules** – Notable behaviors or requirements.
8. **Component Summary Table** – (Optional) List of screens/components and their responsibilities.

-------------------------------------------------------------------------------
Guidance:
-------------------------------------------------------------------------------
- Remove duplicates and inconsistencies as you merge.
- Infer overall structure, even if some files describe only a small part.
- Write clearly and in full sentences for architects and developers.
- DO NOT just copy the input summaries—synthesize them into a holistic document.
- You may use bullet points, tables, or diagrams for clarity.

-------------------------------------------------------------------------------
The input summaries:
-------------------------------------------------------------------------------
{file_summaries_text}
-------------------------------------------------------------------------------

Now generate the **High-Level Design document**.
/nothink
/no_think
"""


# Node 0: Read the files
def read_files(state: State) -> State:
    src_path = "src"
    print(f"Scanning directory: {src_path}")
    files_data: List[FileData] = []
    errors = []
    total_files = 0
    matched_files = 0

    # First, search for .fx.yaml files
    fx_yaml_found = False
    for root, _, files in os.walk(src_path):
        files = sorted(files)
        for file in files:
            total_files += 1
            if file.endswith('.fx.yaml'):
                fx_yaml_found = True
                matched_files += 1
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, src_path)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                except UnicodeDecodeError:
                    try:
                        with open(file_path, 'rb') as f:
                            content = f.read().decode('utf-8', errors='replace')
                    except Exception as e:
                        errors.append({'file_path': relative_path, 'error': str(e)})
                        print(f"Failed to read {relative_path}: {e}")
                        continue
                except Exception as e:
                    errors.append({'file_path': relative_path, 'error': str(e)})
                    print(f"Failed to read {relative_path}: {e}")
                    continue

                files_data.append({
                    'file_path': relative_path,
                    'content': content
                })

    # If no .fx.yaml files found, look for JSON files in "controls" folder
    if not fx_yaml_found:
        print("No .fx.yaml files found. Searching for JSON files in 'controls' folder...")
        controls_path = os.path.join(src_path, "controls")

        if os.path.exists(controls_path) and os.path.isdir(controls_path):
            for root, _, files in os.walk(controls_path):
                files = sorted(files)
                for file in files:
                    total_files += 1
                    if file.endswith('.json'):
                        matched_files += 1
                        file_path = os.path.join(root, file)
                        relative_path = os.path.relpath(file_path, src_path)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                        except UnicodeDecodeError:
                            try:
                                with open(file_path, 'rb') as f:
                                    content = f.read().decode('utf-8', errors='replace')
                            except Exception as e:
                                errors.append({'file_path': relative_path, 'error': str(e)})
                                print(f"Failed to read {relative_path}: {e}")
                                continue
                        except Exception as e:
                            errors.append({'file_path': relative_path, 'error': str(e)})
                            print(f"Failed to read {relative_path}: {e}")
                            continue

                        files_data.append({
                            'file_path': relative_path,
                            'content': content
                        })
        else:
            print(f"Controls folder not found at: {controls_path}")

    print(f"Total files found: {total_files}")
    print(f"Files matching suffix: {matched_files}")
    print(f"Files processed: {len(files_data)}")
    if errors:
        print(f"Errors: {len(errors)}")
        for error in errors:
            print(f"  - {error['file_path']}: {error['error']}")

    results: Dict[str, Any] = {"app_files": files_data}
    if errors:
        results["errors"] = errors

    return {**state, "files": results}


# Node 1: File Review
def node_1(state: State) -> State:
    print("---Node 1 is GO---")

    file_summaries = []
    app_files = state["files"].get("app_files", [])

    for file in app_files:
        file_content = file["content"]
        file_name = file.get("file_path", "Unknown filename")

        # Prepare prompt with individual file content
        system_prompt = node1_prompt + f"\n---\nFile name: {file_name}\n---\n{file_content}\n---\n"

        messages = [SystemMessage(content=system_prompt)]
        response = llm.invoke(messages)
        summary = response.content
        file_summaries.append({
            "file_name": file_name,
            "summary": summary
        })

        print(f"Summary generated for {file_name} (length: {len(summary)} chars)")

    print(f"Generated summaries for {len(file_summaries)} files.")

    # Store individual summaries to state
    return {**state, "file_summaries": file_summaries}


# Node 2: Report Generation
def node_2(state: State) -> State:
    print("---Node 2 is GO---")

    # Prepare summaries as input for the LLM
    file_summaries = state.get("file_summaries", [])
    # Format as human-readable for the LLM
    file_summaries_text = "\n\n".join(
        [f"---\nSummary for {fs['file_name']}:\n{fs['summary']}" for fs in file_summaries]
    )

    # Insert into the system prompt
    system_prompt = system_prompt_hld.format(file_summaries_text=file_summaries_text)

    print("---Calling LLM to synthesize the HLD document---")
    messages = [SystemMessage(content=system_prompt)]
    response = llm.invoke(messages)
    hld_document = response.content

    print("High-Level Design document generated successfully")
    print(f"Document length: {len(hld_document)} characters")

    # Optionally save as use_case or usecase_prompt for downstream usage - Need to change this to reflect the pivot away from use cases
    return {**state, "use_case": hld_document}


# Build Graph
builder = StateGraph(State)
builder.add_node("read_files", read_files)
builder.add_node("node_1", node_1)
builder.add_node("node_2", node_2)

# Edges
builder.add_edge(START, "read_files")
builder.add_edge("read_files", "node_1")
builder.add_edge("node_1", "node_2")
builder.add_edge("node_2", END)

graph = builder.compile()

# Display Graph
display(Image(graph.get_graph().draw_mermaid_png()))
# Invoke Graph
initial_input = {}  # No initial state needed unless you want to inject something specific
result = graph.invoke(initial_input)

# Save the file as a markdown file locally
#with open("example.md", "w") as file:
#   file.write(result["use_case"])

print(result["use_case"])
