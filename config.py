"""
Configuration file for Malaysian Legal Assistant
Centralizes all file paths to make the project portable
"""

import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LAWS_FOLDER = os.path.join(BASE_DIR, "laws")

CONTRACTS_OUTPUT_FOLDER = os.path.join(BASE_DIR, "contracts_output")
UPLOADED_DOCS_FOLDER = os.path.join(BASE_DIR, "uploaded_docs")
UPLOADED_CONTRACTS_FOLDER = os.path.join(BASE_DIR, "uploaded_contracts")
LAWS_DELETED_FOLDER = os.path.join(BASE_DIR, "laws_deleted")
LAWS_BACKUP_FOLDER = os.path.join(BASE_DIR, "laws_backup")

for folder in [LAWS_FOLDER, CONTRACTS_OUTPUT_FOLDER, LAWS_DELETED_FOLDER]:
    os.makedirs(folder, exist_ok=True)
if __name__ == "__main__":
    print("Base Directory:", BASE_DIR)
    print("Laws Folder:", LAWS_FOLDER)
    print("Contracts Output:", CONTRACTS_OUTPUT_FOLDER)
    print("Laws Deleted:", LAWS_DELETED_FOLDER)