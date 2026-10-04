import json
import os
from pathlib import Path


ASSISTANT_CONFIG_FILE = Path(__file__).with_name("assistant.json")
REFERENCE_FILE = Path(__file__).with_name("Tomcat_HTTPD_Error_reference.docx")

MODEL = os.getenv("OPENAI_MODEL", "gpt-5-mini")

INSTRUCTIONS = """You are a Tomcat and Apache HTTPD Application Support Assistant.

Use the uploaded Tomcat_HTTPD_Error_reference.docx as the primary reference for troubleshooting.

When the user provides an error, HTTP status code, exception, Apache AHxxxxx error, or log:
1. Identify the relevant error from the reference document.
2. Explain its meaning and possible causes.
3. Provide troubleshooting steps and commands supported by the reference.
4. If logs are provided, analyze them and identify the deepest meaningful "Caused by" exception.
5. Clearly distinguish confirmed evidence from possible causes.
6. Recommend the least disruptive corrective action supported by the reference.
7. Explain how to verify the issue after the fix.
8. If the reference does not contain enough information, ask for the required logs or configuration details instead of guessing.

Follow this troubleshooting approach:
Symptom -> Error -> Logs -> Root Cause -> Fix -> Validation

Important:
- Do not invent information that is not supported by the reference.
- Prefer log evidence over assumptions.
- Do not claim a root cause unless the available evidence supports it.
- Keep responses practical and suitable for an Application Support Engineer.
"""


def _load_config():
    if not ASSISTANT_CONFIG_FILE.exists():
        return None

    try:
        with ASSISTANT_CONFIG_FILE.open("r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError):
        return None


def _save_config(config):
    with ASSISTANT_CONFIG_FILE.open("w", encoding="utf-8") as file:
        json.dump(config, file, indent=2)


def create_assistant(client):
    """
    Creates/reuses the Responses API configuration and the vector store
    containing the Tomcat/HTTPD reference document.

    The function name is kept as create_assistant() so existing main_flask.py
    imports do not need to change, although the old Assistants API is no
    longer used.
    """
    if not REFERENCE_FILE.exists():
        raise FileNotFoundError(
            "Reference document not found: {}".format(REFERENCE_FILE)
        )

    reference_mtime = REFERENCE_FILE.stat().st_mtime
    config = _load_config()

    # Reuse the existing vector store when it was created from the same
    # local reference document.
    if (
        config
        and config.get("vector_store_id")
        and config.get("reference_file_mtime") == reference_mtime
    ):
        print("Loaded existing vector store configuration...")
        return config

    print("Creating a new vector store for the reference document...")

    vector_store = client.vector_stores.create(
        name="Tomcat_HTTPD_Error_Reference"
    )

    with REFERENCE_FILE.open("rb") as file:
        vector_store_file = client.vector_stores.files.upload_and_poll(
            vector_store_id=vector_store.id,
            file=file,
            max_wait_seconds=300
        )

    if vector_store_file.status != "completed":
        error_details = getattr(vector_store_file, "last_error", None)
        raise RuntimeError(
            "Reference document processing failed. Status: {}. Error: {}".format(
                vector_store_file.status,
                error_details
            )
        )

    config = {
        "vector_store_id": vector_store.id,
        "reference_file_id": getattr(vector_store_file, "id", None),
        "reference_file_mtime": reference_mtime,
        "model": MODEL
    }

    _save_config(config)
    print("Reference document uploaded and processed successfully.")

    return config
