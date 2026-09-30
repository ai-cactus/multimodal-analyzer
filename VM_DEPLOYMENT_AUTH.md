# VM Deployment & Authentication Guide

## Overview

This guide explains how to properly authenticate the Multimodal Analyzer application when deploying to Google Compute Engine (VM) or GKE.

## Option 1: Service Account Key (Portable Way)

This method works exactly like your local development environment.

### Steps:

1.  **Copy the JSON Key**: Copy `/home/oluwaseyi/doc-analyzer-key.json` to a secure location on your VM (e.g., `/opt/app/config/gcp-key.json`).
2.  **Update `.env`**: Point to this file on the VM.
    ```env
    GOOGLE_APPLICATION_CREDENTIALS=/opt/app/config/gcp-key.json
    ```
3.  **Security Note**: Ensure this JSON file is **never** committed to version control and that its permissions are restricted (e.g., `chmod 600`).

---

## Option 2: Attached Service Account (Cloud-Native Best Practice)

This is the recommended approach for GCP infrastructure. It is more secure and requires zero key management.

### Steps:

1.  **Stop the Instance**: If the VM is already running, you must stop it (or set it during creation).
2.  **Edit Instance**: Go to the **"Compute Engine"** Console -> **"VM instances"** -> Click on your instance name -> Click **"Edit"**.
3.  **Set Service Account**:
    - Scroll to **"API and identity"**.
    - Under **"Service account"**, select: `doc-analyzer@multimodal-analyzer.iam.gserviceaccount.com`.
    - Click **"Save"**.
4.  **Zero-Config on VM**:
    - The application will automatically detect the VM's identity.
    - **Remove** `GOOGLE_APPLICATION_CREDENTIALS` from your `.env` on the VM.
    - The app will use the Google SDK's built-in "Application Default Credentials" (ADC) to authenticate seamlessly.

### Benefits:

- **No Secret Management**: No JSON files to copy, leak, or rotate.
- **Least Privilege**: The VM only has the permissions granted to that specific service account.
- **Easy Scaling**: Works identically across 1 or 1,000 instances.

---

## Troubleshooting

If you see "Reauthentication is needed" or "Permission Denied" on the VM:

1.  Verify the VM has the correct service account attached (Step 3 above).
2.  Ensure you have NOT set `GOOGLE_APPLICATION_CREDENTIALS` to a non-existent path on the VM.
3.  Check if the service account has both `roles/aiplatform.user` and `roles/documentai.apiUser` roles in the IAM console.
