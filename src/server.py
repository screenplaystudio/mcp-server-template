#!/usr/bin/env python3
import os
import requests
from dotenv import load_dotenv
load_dotenv()
from fastmcp import FastMCP

mcp = FastMCP("Nexudus MCP Server")

NEXUDUS_BASE_URL = "https://spaces.nexudus.com/api"
NEXUDUS_USERNAME = os.environ.get("NEXUDUS_USERNAME")
NEXUDUS_PASSWORD = os.environ.get("NEXUDUS_PASSWORD")
print(f"Username: {NEXUDUS_USERNAME}")
print(f"Password set: {NEXUDUS_PASSWORD is not None}")

def get_auth():
    return (NEXUDUS_USERNAME, NEXUDUS_PASSWORD)

def fetch_all(endpoint, params=None):
    if params is None:
        params = {}
    params["size"] = 25
    params["page"] = 1
    all_records = []
    while True:
        r = requests.get(f"{NEXUDUS_BASE_URL}/{endpoint}", auth=get_auth(), params=params, timeout=30)
        print(f"Status: {r.status_code}")
        print(f"Response: {r.text[:500]}")
        data = r.json()
        records = data.get("Records", [])
        all_records.extend(records)
        if not data.get("HasNextPage", False):
            break
        params["page"] += 1
    return {"Records": all_records, "TotalItems": len(all_records)}

# BOOKINGS

@mcp.tool(description="List bookings with optional filters. Pass date as YYYY-MM-DD.")
def list_bookings(date: str = None) -> dict:
    params = {}
    if date:
        params["BookingStartTime"] = date
    return fetch_all("spaces/bookings", params)

@mcp.tool(description="Create a new booking. ResourceId, CoworkerId, StartTime and EndTime required. Times as ISO 8601.")
def create_booking(resource_id: int, coworker_id: int, start_time: str, end_time: str) -> dict:
    data = {"ResourceId": resource_id, "CoworkerId": coworker_id, "FromTime": start_time, "ToTime": end_time}
    r = requests.post(f"{NEXUDUS_BASE_URL}/spaces/bookings", auth=get_auth(), json=data)
    return r.json()

@mcp.tool(description="Update an existing booking by ID.")
def update_booking(booking_id: int, start_time: str = None, end_time: str = None) -> dict:
    r = requests.get(f"{NEXUDUS_BASE_URL}/spaces/bookings/{booking_id}", auth=get_auth())
    booking = r.json()
    if start_time:
        booking["FromTime"] = start_time
    if end_time:
        booking["ToTime"] = end_time
    r = requests.put(f"{NEXUDUS_BASE_URL}/spaces/bookings/{booking_id}", auth=get_auth(), json=booking)
    return r.json()

@mcp.tool(description="Cancel/delete a booking by ID.")
def cancel_booking(booking_id: int) -> dict:
    r = requests.delete(f"{NEXUDUS_BASE_URL}/spaces/bookings/{booking_id}", auth=get_auth())
    return {"status": r.status_code}

# HELP DESK

@mcp.tool(description="List all help desk messages. Pass open_only=True to see only open tickets.")
def list_helpdesk_messages(open_only: bool = False) -> dict:
    params = {}
    if open_only:
        params["Status"] = "Open"
    return fetch_all("support/helpdeskMessages", params)

@mcp.tool(description="Create a new help desk message.")
def create_helpdesk_message(subject: str, message: str, coworker_id: int) -> dict:
    data = {"Subject": subject, "Message": message, "CoworkerId": coworker_id}
    r = requests.post(f"{NEXUDUS_BASE_URL}/support/helpdeskMessages", auth=get_auth(), json=data)
    return r.json()

@mcp.tool(description="Reply to a help desk message by ID.")
def reply_to_helpdesk_message(message_id: int, reply: str) -> dict:
    data = {"HelpDeskMessageId": message_id, "Message": reply}
    r = requests.post(f"{NEXUDUS_BASE_URL}/support/helpdeskComments", auth=get_auth(), json=data)
    return r.json()

@mcp.tool(description="Close a help desk message by ID.")
def close_helpdesk_message(message_id: int) -> dict:
    r = requests.get(f"{NEXUDUS_BASE_URL}/support/helpdeskMessages/{message_id}", auth=get_auth())
    msg = r.json()
    msg["Status"] = "Closed"
    r = requests.put(f"{NEXUDUS_BASE_URL}/support/helpdeskMessages/{message_id}", auth=get_auth(), json=msg)
    return r.json()

# MEMBERS

@mcp.tool(description="Search for a member by name or email address.")
def search_member(query: str) -> dict:
    params = {"Coworker_FullName": query}
    r = requests.get(f"{NEXUDUS_BASE_URL}/spaces/coworkers", auth=get_auth(), params=params, timeout=30)
    return r.json()

@mcp.tool(description="List all members/coworkers. Pass created_after as YYYY-MM-DD to filter new signups.")
def list_members(created_after: str = None) -> dict:
    params = {}
    if created_after:
        params["from_Coworker_CreatedOn"] = created_after
    return fetch_all("spaces/coworkers", params)

@mcp.tool(description="Get the total count of active members.")
def get_member_count() -> dict:
    params = {"Coworker_Active": True, "size": 1}
    r = requests.get(f"{NEXUDUS_BASE_URL}/spaces/coworkers", auth=get_auth(), params=params, timeout=30)
    data = r.json()
    return {"total_active_members": data.get("TotalItems", 0)}

@mcp.tool(description="Get a single member by ID.")
def get_member(coworker_id: int) -> dict:
    r = requests.get(f"{NEXUDUS_BASE_URL}/spaces/coworkers/{coworker_id}", auth=get_auth())
    return r.json()

@mcp.tool(description="Update a member's details by ID.")
def update_member(coworker_id: int, updates: dict) -> dict:
    r = requests.get(f"{NEXUDUS_BASE_URL}/spaces/coworkers/{coworker_id}", auth=get_auth())
    member = r.json()
    member.update(updates)
    r = requests.put(f"{NEXUDUS_BASE_URL}/spaces/coworkers/{coworker_id}", auth=get_auth(), json=member)
    return r.json()

# CONTRACTS

@mcp.tool(description="List all member contracts. Pass coworker_id to filter by member.")
def list_contracts(coworker_id: int = None) -> dict:
    params = {}
    if coworker_id:
        params["CoworkerId"] = coworker_id
    return fetch_all("billing/coworkercontracts", params)

@mcp.tool(description="Cancel a contract by ID.")
def cancel_contract(contract_id: int) -> dict:
    r = requests.get(f"{NEXUDUS_BASE_URL}/billing/coworkercontracts/{contract_id}", auth=get_auth())
    contract = r.json()
    contract["CancellationDate"] = "today"
    r = requests.put(f"{NEXUDUS_BASE_URL}/billing/coworkercontracts/{contract_id}", auth=get_auth(), json=contract)
    return r.json()

# INVOICES

@mcp.tool(description="List invoices. Pass unpaid_only=True for overdue invoices.")
def list_invoices(unpaid_only: bool = False, coworker_id: int = None) -> dict:
    params = {}
    if unpaid_only:
        params["Paid"] = False
    if coworker_id:
        params["CoworkerId"] = coworker_id
    return fetch_all("billing/coworkerinvoices", params)

@mcp.tool(description="Get a single invoice by ID.")
def get_invoice(invoice_id: int) -> dict:
    r = requests.get(f"{NEXUDUS_BASE_URL}/billing/coworkerinvoices/{invoice_id}", auth=get_auth())
    return r.json()

@mcp.tool(description="Create a new invoice for a member.")
def create_invoice(coworker_id: int, amount: float, description: str) -> dict:
    data = {"CoworkerId": coworker_id, "Amount": amount, "Notes": description}
    r = requests.post(f"{NEXUDUS_BASE_URL}/billing/coworkerinvoices", auth=get_auth(), json=data)
    return r.json()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0"
    print(f"Starting Nexudus MCP server on {host}:{port}")
    mcp.run(
        transport="http",
        host=host,
        port=port,
        stateless_http=False
    )
