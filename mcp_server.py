import os
import json
import httpx

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP


# Load environment variables
load_dotenv()


# Create MCP server
mcp = FastMCP("JouleOps MCP Server")


# FastAPI base URL
BASE_URL = "http://localhost:8000/api"


# --------------------------------------------------
# Get Material Details
# --------------------------------------------------

@mcp.tool()
def get_material_details(
    material_id: str,
    plant_code: str
) -> str:

    try:
        response = httpx.post(
            f"{BASE_URL}/material/details",
            json={
                "material_id": material_id,
                "plant_code": plant_code
            },
            timeout=30.0
        )

        result = response.json()

        return json.dumps(
            result,
            indent=2
        )

    except Exception as e:
        return f"Error: {str(e)}"


# --------------------------------------------------
# Get Open Sales Orders
# --------------------------------------------------

@mcp.tool()
def get_open_sales_orders(
    region: str,
    date_from: str,
    date_to: str
) -> str:

    try:
        response = httpx.post(
            f"{BASE_URL}/sales/orders",
            json={
                "region": region,
                "date_from": date_from,
                "date_to": date_to
            },
            timeout=30.0
        )

        result = response.json()

        return json.dumps(
            result,
            indent=2
        )

    except Exception as e:
        return f"Error: {str(e)}"


# --------------------------------------------------
# Get Customer Summary
# --------------------------------------------------

@mcp.tool()
def get_customer_summary(
    customer_id: str
) -> str:

    try:
        response = httpx.post(
            f"{BASE_URL}/customer/summary",
            json={
                "customer_id": customer_id
            },
            timeout=30.0
        )

        result = response.json()

        return json.dumps(
            result,
            indent=2
        )

    except Exception as e:
        return f"Error: {str(e)}"


# --------------------------------------------------
# Create Ticket
# --------------------------------------------------

@mcp.tool()
def create_ticket(
    material_id: str,
    plant_code: str,
    priority: str,
    assigned_team: str,
    description: str,
    created_by_role: str,
    x_user_role: str = "PLANT_SUPERVISOR"
) -> str:

    try:

        headers = {
            "X-User-Role": x_user_role
        }

        response = httpx.post(
            f"{BASE_URL}/ticket/create",
            json={
                "material_id": material_id,
                "plant_code": plant_code,
                "priority": priority,
                "assigned_team": assigned_team,
                "description": description,
                "created_by_role": created_by_role
            },
            headers=headers,
            timeout=30.0
        )

        result = response.json()

        return json.dumps(
            result,
            indent=2
        )

    except Exception as e:
        return f"Error: {str(e)}"


# --------------------------------------------------
# Summarize Overdue Invoices
# --------------------------------------------------

@mcp.tool()
def summarize_overdue_invoices(
    customer_id: str
) -> str:

    try:
        response = httpx.post(
            f"{BASE_URL}/invoices/overdue",
            json={
                "customer_id": customer_id
            },
            timeout=30.0
        )

        result = response.json()

        return json.dumps(
            result,
            indent=2
        )

    except Exception as e:
        return f"Error: {str(e)}"


# --------------------------------------------------
# Main
# --------------------------------------------------

if __name__ == "__main__":

    print("=" * 50)
    print("Starting JouleOps MCP Server...")
    print("=" * 50)

    print("Tools available:")
    print(" - get_material_details")
    print(" - get_open_sales_orders")
    print(" - get_customer_summary")
    print(" - create_ticket")
    print(" - summarize_overdue_invoices")

    print("=" * 50)
    print("MCP Server is running!")
    print("Press Ctrl+C to stop")
    print("=" * 50)

    mcp.run()
    











