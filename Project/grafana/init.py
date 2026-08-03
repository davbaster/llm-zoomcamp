import os
import json
from pathlib import Path
import requests

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    def load_dotenv(dotenv_path):
        """Load simple KEY=VALUE entries without requiring python-dotenv."""
        path = Path(dotenv_path)
        if not path.exists():
            return False

        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            value = value.strip().strip("\"'")
            os.environ.setdefault(key.strip(), value)
        return True


load_dotenv(Path(__file__).with_name(".env"))


GRAFANA_URL = os.getenv("GRAFANA_URL", "http://localhost:3000").rstrip("/")

GRAFANA_USER = os.getenv("GRAFANA_ADMIN_USER", "admin")
GRAFANA_PASSWORD = os.getenv("GRAFANA_ADMIN_PASSWORD", "admin")
SERVICE_ACCOUNT_NAME = os.getenv("GRAFANA_SERVICE_ACCOUNT_NAME", "ProgrammaticAccount")
SERVICE_ACCOUNT_TOKEN_NAME = os.getenv(
    "GRAFANA_SERVICE_ACCOUNT_TOKEN_NAME", "ProgrammaticToken"
)

PG_HOST = os.getenv("POSTGRES_HOST")
PG_DB = os.getenv("POSTGRES_DB")
PG_USER = os.getenv("POSTGRES_USER")
PG_PASSWORD = os.getenv("POSTGRES_PASSWORD")
PG_PORT = os.getenv("POSTGRES_PORT")


def grafana_error(response):
    """Return a useful error without hiding Grafana's response body."""
    return f"HTTP {response.status_code}: {response.text or response.reason}"


def create_service_account_token():
    """Create or reuse a service account, then rotate its token."""
    auth = (GRAFANA_USER, GRAFANA_PASSWORD)
    headers = {"Content-Type": "application/json"}

    account_response = requests.post(
        f"{GRAFANA_URL}/api/serviceaccounts",
        auth=auth,
        headers=headers,
        json={"name": SERVICE_ACCOUNT_NAME, "role": "Admin"},
        timeout=10,
    )

    if account_response.status_code in (200, 201):
        service_account_id = account_response.json()["id"]
    elif account_response.status_code in (400, 409) and "already exists" in account_response.text.lower():
        search_response = requests.get(
            f"{GRAFANA_URL}/api/serviceaccounts/search",
            auth=auth,
            params={"query": SERVICE_ACCOUNT_NAME},
            timeout=10,
        )
        if search_response.status_code != 200:
            print(f"Failed to find existing service account: {grafana_error(search_response)}")
            return None

        accounts = search_response.json().get("serviceAccounts", [])
        matching_accounts = [
            account for account in accounts if account["name"] == SERVICE_ACCOUNT_NAME
        ]
        if not matching_accounts:
            print(f"Service account '{SERVICE_ACCOUNT_NAME}' was not found")
            return None
        service_account_id = matching_accounts[0]["id"]
    else:
        print(f"Failed to create service account: {grafana_error(account_response)}")
        return None

    # Tokens are only returned once. Remove the old token with this name so
    # rerunning the script rotates it without accumulating duplicate tokens.
    tokens_response = requests.get(
        f"{GRAFANA_URL}/api/serviceaccounts/{service_account_id}/tokens",
        auth=auth,
        timeout=10,
    )
    if tokens_response.status_code != 200:
        print(f"Failed to list service-account tokens: {grafana_error(tokens_response)}")
        return None

    for token in tokens_response.json():
        if token["name"] == SERVICE_ACCOUNT_TOKEN_NAME:
            delete_response = requests.delete(
                f"{GRAFANA_URL}/api/serviceaccounts/{service_account_id}/tokens/{token['id']}",
                auth=auth,
                timeout=10,
            )
            if delete_response.status_code != 200:
                print(f"Failed to rotate service-account token: {grafana_error(delete_response)}")
                return None

    response = requests.post(
        f"{GRAFANA_URL}/api/serviceaccounts/{service_account_id}/tokens",
        auth=auth,
        headers=headers,
        json={"name": SERVICE_ACCOUNT_TOKEN_NAME},
        timeout=10,
    )

    if response.status_code in (200, 201):
        print("Grafana service-account token created successfully")
        return response.json()["key"]
    else:
        print(f"Failed to create service-account token: {grafana_error(response)}")
        return None


def create_or_update_datasource(api_key):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    datasource_payload = {
        "name": "PostgreSQL",
        "type": "postgres",
        "url": f"{PG_HOST}:{PG_PORT}",
        "access": "proxy",
        "user": PG_USER,
        "database": PG_DB,
        "basicAuth": False,
        "isDefault": True,
        "jsonData": {"sslmode": "disable", "postgresVersion": 1300},
        "secureJsonData": {"password": PG_PASSWORD},
    }

    print("Datasource payload:")
    safe_datasource_payload = {
        **datasource_payload,
        "secureJsonData": {"password": "<redacted>"},
    }
    print(json.dumps(safe_datasource_payload, indent=2))

    # First, try to get the existing datasource
    response = requests.get(
        f"{GRAFANA_URL}/api/datasources/name/{datasource_payload['name']}",
        headers=headers,
        timeout=10,
    )

    if response.status_code == 200:
        # Datasource exists, let's update it
        existing_datasource = response.json()
        datasource_uid = existing_datasource["uid"]
        print(f"Updating existing datasource with uid: {datasource_uid}")
        response = requests.put(
            f"{GRAFANA_URL}/api/datasources/uid/{datasource_uid}",
            headers=headers,
            json=datasource_payload,
            timeout=10,
        )
    elif response.status_code == 404:
        # Datasource doesn't exist, create a new one
        print("Creating new datasource")
        response = requests.post(
            f"{GRAFANA_URL}/api/datasources",
            headers=headers,
            json=datasource_payload,
            timeout=10,
        )
    else:
        print(f"Failed to find existing datasource: {grafana_error(response)}")
        return None

    print(f"Response status code: {response.status_code}")
    print(f"Response headers: {response.headers}")
    print(f"Response content: {response.text}")

    if response.status_code in [200, 201]:
        print("Datasource created or updated successfully")
        return response.json().get("datasource", {}).get("uid") or response.json().get(
            "uid"
        )
    else:
        print(f"Failed to create or update datasource: {grafana_error(response)}")
        return None


def create_dashboard(api_key, datasource_uid):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    dashboard_file = Path(__file__).with_name("dashboard.json")

    try:
        with dashboard_file.open("r", encoding="utf-8") as f:
            dashboard_json = json.load(f)
    except FileNotFoundError:
        print(f"Error: {dashboard_file} not found.")
        return
    except json.JSONDecodeError as e:
        print(f"Error decoding {dashboard_file}: {str(e)}")
        return

    print("Dashboard JSON loaded successfully.")

    # Update datasource UID in the dashboard JSON
    panels_updated = 0
    for panel in dashboard_json.get("panels", []):
        if isinstance(panel.get("datasource"), dict):
            panel["datasource"]["uid"] = datasource_uid
            panels_updated += 1
        elif isinstance(panel.get("targets"), list):
            for target in panel["targets"]:
                if isinstance(target.get("datasource"), dict):
                    target["datasource"]["uid"] = datasource_uid
                    panels_updated += 1

    print(f"Updated datasource UID for {panels_updated} panels/targets.")

    # Remove server-managed fields, but keep the UID so reruns overwrite the
    # same dashboard instead of creating duplicates.
    dashboard_json.pop("id", None)
    dashboard_json.pop("version", None)

    # Prepare the payload
    dashboard_payload = {
        "dashboard": dashboard_json,
        "overwrite": True,
        "message": "Updated by Python script",
    }

    print("Sending dashboard creation request...")

    response = requests.post(
        f"{GRAFANA_URL}/api/dashboards/db",
        headers=headers,
        json=dashboard_payload,
        timeout=10,
    )

    print(f"Response status code: {response.status_code}")
    print(f"Response content: {response.text}")

    if response.status_code == 200:
        print("Dashboard created successfully")
        return response.json().get("uid")
    else:
        print(f"Failed to create dashboard: {grafana_error(response)}")
        return None


def main():
    api_key = create_service_account_token()
    if not api_key:
        print("Grafana token creation failed")
        return

    datasource_uid = create_or_update_datasource(api_key)
    if not datasource_uid:
        print("Datasource creation failed")
        return

    create_dashboard(api_key, datasource_uid)


if __name__ == "__main__":
    main()
