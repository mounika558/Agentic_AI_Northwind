# VIVA PREPARATION: JouleOps - SAP BTP AI Capstone Project

---

## 1. PROJECT OVERVIEW & ARCHITECTURE

### 1.1 Project Name & Objective

**Project Name:** JouleOps - NorthWind Capstone  
**Objective:** Build an enterprise-grade API platform integrated with SAP HANA database for managing operational data in a manufacturing/supply chain environment.

### 1.2 High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│            MCP Server (mcp_server.py)                   │
│  - Tool Wrapper Layer                                   │
│  - FastMCP Server                                       │
│  - Calls FastAPI endpoints                              │
└─────────────────────────────────────────────────────────┘
                        ↓ (HTTP Calls)
┌─────────────────────────────────────────────────────────┐
│            FastAPI Backend (main.py)                    │
│  - RESTful API Endpoints                                │
│  - Business Logic                                       │
│  - Request Validation (Pydantic Models)                │
│  - Role-Based Authorization                            │
│  - Audit Logging                                        │
└─────────────────────────────────────────────────────────┘
                        ↓ (SQL Queries)
┌─────────────────────────────────────────────────────────┐
│         SAP HANA Database (hdbcli)                      │
│  - MATERIALS Table                                      │
│  - CUSTOMERS Table                                      │
│  - SALES_ORDERS Table                                   │
│  - INVOICES Table                                       │
│  - TICKETS Table                                        │
│  - AUDIT_LOG Table                                      │
└─────────────────────────────────────────────────────────┘
                        ↑ (Seed Data)
┌─────────────────────────────────────────────────────────┐
│       Data Generation (generate_seed_data.py)           │
│  - Creates CSV files with test data                     │
│  - 500 Materials, 100 Customers, 800 Orders, etc.       │
└─────────────────────────────────────────────────────────┘
```

### 1.3 Three-Tier Architecture

1. **Presentation Layer:** MCP Server (tool interface for AI assistants)
2. **Business Logic Layer:** FastAPI endpoints with validation & authorization
3. **Data Access Layer:** SAP HANA database connections

---

## 2. TECHNOLOGY STACK

| Component             | Technology       | Purpose                               |
| --------------------- | ---------------- | ------------------------------------- |
| **Backend Framework** | FastAPI (Python) | REST API development                  |
| **Database**          | SAP HANA         | Enterprise data management            |
| **Database Driver**   | hdbcli           | Python-SAP HANA connectivity          |
| **MCP Protocol**      | FastMCP          | Model Context Protocol implementation |
| **HTTP Client**       | httpx            | Making requests to FastAPI            |
| **Data Validation**   | Pydantic         | Request/response model validation     |
| **Data Generation**   | pandas, Faker    | Test data generation                  |
| **Configuration**     | python-dotenv    | Environment variable management       |

---

## 3. CORE COMPONENTS EXPLANATION

### 3.1 MAIN.PY - FastAPI Backend

#### 3.1.1 Database Connection Function

```python
def get_db():
```

**Purpose:** Establish connection to SAP HANA database  
**Parameters:** None (reads from environment variables)  
**Returns:** Connection object  
**Key Details:**

- Uses `dbapi.connect()` from hdbcli library
- Reads credentials from .env file (HANA_HOST, HANA_PORT, HANA_USER, HANA_PASSWORD)
- Enables encrypted connection (encrypt=True)
- Connection is closed after each query execution

**Why This Design:** Stateless connection approach ensures each request gets a fresh connection, preventing connection leaks.

---

#### 3.1.2 REQUEST MODELS (Pydantic Classes)

These define API input validation:

**MaterialRequest**

- `material_id`: Material identifier
- `plant_code`: Manufacturing plant code
- Purpose: Validate material query requests

**SalesRequest**

- `region`: Geographic region
- `date_from`, `date_to`: Date range filters
- Purpose: Filter sales orders by region & date

**CustomerRequest**

- `customer_id`: Customer identifier
- Purpose: Fetch customer-specific data

**TicketRequest**

- `material_id`, `plant_code`: Identifies the asset
- `priority`: Task priority level
- `assigned_team`: Team responsible for ticket
- `description`: Ticket details
- `created_by_role`: Role of ticket creator
- Purpose: Create maintenance/operational tickets

**InvoiceRequest**

- `customer_id`: Target customer
- Purpose: Fetch invoice data for specific customer

**Why Pydantic:** Automatic validation, type checking, and error handling for API inputs.

---

#### 3.1.3 API ENDPOINTS

##### ✓ **GET /health**

```python
@app.get("/health")
def health()
```

**Purpose:** Health check endpoint  
**Returns:** `{"status": "ok"}`  
**Use Case:** Monitor if API is running  
**No Database Call:** Lightweight check

---

##### ✓ **POST /api/material/details**

```python
@app.post("/api/material/details")
def get_material(req: MaterialRequest)
```

**Purpose:** Fetch material master data  
**Input:** MaterialRequest (material_id, plant_code)  
**Database Query:**

```sql
SELECT material_id, description, category, unit_price, stock_qty,
       safety_stock, plant_code
FROM MATERIALS
WHERE material_id = ? AND plant_code = ?
```

**Returns:**

```json
{
  "material_id": "MAT-0001",
  "description": "Product description",
  "category": "Raw Material",
  "unit_price": 1500.5,
  "stock_qty": 250,
  "safety_stock": 50,
  "plant_code": "PLT-PUN",
  "is_below_safety": false,
  "tool": "get_material_details",
  "source_tables": ["MATERIALS"]
}
```



**Key Feature:** `is_below_safety` field calculated by comparing stock_qty vs safety_stock  
**Error Handling:** Returns 404 if material not found  
**Business Logic:** Helps identify low-stock materials for re-ordering

---


##### ✓ **POST /api/sales/orders**

```python
@app.post("/api/sales/orders")
def get_sales(req: SalesRequest)
```

**Purpose:** Retrieve open sales orders by region and date  
**Input:** SalesRequest (region, date_from, date_to)  
**Database Query:**

```sql
SELECT customer_id, COUNT(*) AS orders, SUM(qty) AS total_qty
FROM SALES_ORDERS
WHERE region = ? AND status = 'Open'
      AND created_on BETWEEN ? AND ?
GROUP BY customer_id
```

**Returns:**

```json
{
  "region": "North",
  "orders": [
    {
      "customer_id": "C-001",
      "order_count": 5,
      "total_qty": 150
    }
  ],
  "tool": "get_open_sales_orders",
  "source_tables": ["SALES_ORDERS"]
}
```

**Key Feature:** Aggregates data by customer  
**Business Logic:** Helps sales managers track pending orders by region  
**Date Filtering:** Uses BETWEEN for date range queries

---

##### ✓ **POST /api/customer/summary**

```python
@app.post("/api/customer/summary")
def get_customer(req: CustomerRequest)
```

**Purpose:** Comprehensive customer financial overview  
**Input:** CustomerRequest (customer_id)  
**Database Query:** (Complex JOIN)

```sql
SELECT c.customer_id, c.name, c.region, c.credit_limit,
       c.outstanding_amount,
       COUNT(i.invoice_id) AS inv_count, SUM(i.amount) AS total_amt,
       SUM(CASE WHEN i.status = 'Overdue' THEN i.amount ELSE 0 END) AS overdue_amt
FROM CUSTOMERS c
LEFT JOIN INVOICES i ON c.customer_id = i.customer_id
WHERE c.customer_id = ?
GROUP BY c.customer_id, c.name, c.region, c.credit_limit, c.outstanding_amount
```

**Returns:**

```json
{
  "customer_id": "C-001",
  "name": "Acme Corp",
  "region": "North",
  "credit_limit": 100000,
  "outstanding_amount": 25000,
  "total_invoices": 12,
  "total_amount": 85000,
  "overdue_amount": 5000,
  "tool": "get_customer_summary",
  "source_tables": ["CUSTOMERS", "INVOICES"]
}
```

**Key Features:**

- LEFT JOIN to include customers without invoices
- CASE statement to calculate overdue amounts
- Financial metrics for credit risk assessment

**Business Logic:** Helps finance team assess customer creditworthiness

---

##### ✓ **POST /api/ticket/create**

```python
@app.post("/api/ticket/create")
def create_ticket(req: TicketRequest, x_user_role: str = Header(...))
```

**Purpose:** Create maintenance/operational tickets with authorization  
**Input:** TicketRequest + x_user_role header

**Authorization Logic:**

```python
if x_user_role not in ["PLANT_SUPERVISOR", "SALES_MANAGER", "FINANCE"]:
    raise HTTPException(status_code=403, detail="Insufficient permissions")
```

**Allowed Roles:** Only specific roles can create tickets

**Database Operations (2 inserts):**

1. **Insert into TICKETS table:**

```sql
INSERT INTO TICKETS (ticket_id, material_id, priority, assigned_team,
                     description, status, created_on, created_by_role)
VALUES (?, ?, ?, ?, ?, 'Open', CURRENT_TIMESTAMP, ?)
```

2. **Insert into AUDIT_LOG table:**

```sql
INSERT INTO AUDIT_LOG (ts, user_role, tool_name, params_masked, outcome)
VALUES (CURRENT_TIMESTAMP, ?, 'create_ticket', ?, 'SUCCESS')
```

**Ticket ID Format:** `TKT-{YYYYMMDDHHMMSS}` (timestamp-based unique ID)

**Audit Trail:**

- Description is MASKED as `[MASKED]` in logs for security
- Logs user role, timestamp, tool name, and outcome
- Ensures compliance and traceability

**Returns:**

```json
{
  "ticket_id": "TKT-20240815153045",
  "message": "Ticket TKT-20240815153045 created successfully",
  "assigned_team": "Mechanical",
  "priority": "HIGH",
  "tool": "create_ticket",
  "source_tables": ["TICKETS", "AUDIT_LOG"]
}
```

**Key Security Features:**

- Role-based access control (RBAC)
- Sensitive parameter masking
- Complete audit trail logging

---

##### ✓ **POST /api/invoices/overdue**

```python
@app.post("/api/invoices/overdue")
def overdue_invoices(req: InvoiceRequest)
```

**Purpose:** Identify overdue invoices and recommend actions  
**Input:** InvoiceRequest (customer_id)  
**Database Query:**

```sql
SELECT invoice_id, amount, due_date, days_overdue, status
FROM INVOICES
WHERE customer_id = ? AND status = 'Overdue'
ORDER BY days_overdue DESC
```

**Business Logic - Recommendation Engine:**

```
if max_days_overdue > 90:
    recommendation = "ESCALATE_TO_LEGAL"
elif max_days_overdue > 60:
    recommendation = "HOLD_SHIPMENTS"
else:
    recommendation = "SEND_REMINDER"
```

**Returns (With Invoices):**

```json
{
  "customer_id": "C-001",
  "total_overdue": 15000,
  "max_days_overdue": 75,
  "recommendation": "HOLD_SHIPMENTS",
  "invoices": [
    {
      "invoice_id": "INV-0001",
      "amount": 5000,
      "due_date": "2024-06-01",
      "days_overdue": 75,
      "status": "Overdue"
    }
  ],
  "tool": "summarize_overdue_invoices",
  "source_tables": ["INVOICES"]
}
```

**Returns (No Overdue Invoices):**

```json
{
  "customer_id": "C-001",
  "total_overdue": 0,
  "invoices": [],
  "tool": "summarize_overdue_invoices",
  "source_tables": ["INVOICES"]
}
```

**Business Value:** Helps collection teams prioritize follow-up actions

---

### 3.2 MCP_SERVER.PY - FastMCP Protocol Implementation

#### 3.2.1 Purpose

- Wraps FastAPI endpoints as MCP tools
- Allows AI assistants (Claude, Copilot) to call backend APIs
- Standardized tool interface for LLMs

#### 3.2.2 MCP Server Setup

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("JouleOps MCP Server")
BASE_URL = "http://localhost:8000/api"
```

**Purpose:** Create MCP server pointing to local FastAPI instance

#### 3.2.3 MCP Tool: `get_material_details`

```python
@mcp.tool()
def get_material_details(material_id: str, plant_code: str) -> str:
```

**Purpose:** MCP wrapper for /api/material/details  
**Parameters:** Same as API (material_id, plant_code)  
**Returns:** JSON string  
**Error Handling:** Catches exceptions and returns error message  
**HTTP Call:** POST to `{BASE_URL}/material/details`  
**Timeout:** 30 seconds

**Use Case:** AI can ask "What's the stock level of MAT-0001 at PLT-PUN?"

---

#### 3.2.4 MCP Tool: `get_open_sales_orders`

```python
@mcp.tool()
def get_open_sales_orders(region: str, date_from: str, date_to: str) -> str:
```

**Purpose:** MCP wrapper for /api/sales/orders  
**Use Case:** "Show open orders in North region for last month"  
**Timeout:** 30 seconds

---

#### 3.2.5 MCP Tool: `get_customer_summary`

```python
@mcp.tool()
def get_customer_summary(customer_id: str) -> str:
```

**Purpose:** MCP wrapper for /api/customer/summary  
**Use Case:** "Get financial overview of customer C-001"

---

#### 3.2.6 MCP Tool: `create_ticket`

```python
@mcp.tool()
def create_ticket(material_id: str, plant_code: str, priority: str,
                  assigned_team: str, description: str,
                  created_by_role: str,
                  x_user_role: str = "PLANT_SUPERVISOR") -> str:
```

**Purpose:** MCP wrapper for /api/ticket/create  
**Key Difference:** Role passed as parameter (default: PLANT_SUPERVISOR)  
**HTTP Headers:** Sets `"X-User-Role"` header  
**Use Case:** "Create HIGH priority ticket for Mechanical team"

---

#### 3.2.7 MCP Tool: `summarize_overdue_invoices`

```python
@mcp.tool()
def summarize_overdue_invoices(customer_id: str) -> str:
```

**Purpose:** MCP wrapper for /api/invoices/overdue  
**Use Case:** "What invoices are overdue for customer C-001?"

---

#### 3.2.8 MCP Server Runtime

```python
if __name__ == "__main__":
    print("Tools available:")
    print(" - get_material_details")
    print(" - get_open_sales_orders")
    print(" - get_customer_summary")
    print(" - create_ticket")
    print(" - summarize_overdue_invoices")

    mcp.run()
```

**Startup:** Prints available tools and starts MCP server  
**Execution:** `mcp.run()` listens for tool invocation requests

---

### 3.3 GENERATE_SEED_DATA.PY - Test Data Generator

#### 3.3.1 Master Data Configurations

Defines controlled test data dimensions:

```python
PLANTS = ["PLT-PUN", "PLT-CHE", "PLT-HYD", "PLT-COI"]  # 4 plants
CATEGORIES = ["Raw Material", "Finished Goods", "Packaging", "Spare Parts", "Chemicals"]
ORDER_STATUSES = ["Open", "Closed", "Cancelled"]
INVOICE_STATUSES = ["Paid", "Overdue", "Pending"]
PRIORITIES = ["HIGH", "MEDIUM", "LOW"]
TEAMS = ["Mechanical", "Electrical", "IT", "Production", "Quality"]
REGIONS = ["South", "North", "East", "West", "Central"]
```

#### 3.3.2 Function: `generate_materials()`

**Purpose:** Create 500 test material records  
**Data Generated:**

- material_id: MAT-0001 to MAT-0500
- description: Random catch phrases (Faker)
- category: Randomly selected from CATEGORIES
- unit_price: 100-5000 (random)
- stock_qty: 10-500 units
- safety_stock: 20-100 units
- plant_code: One of 4 plants
- created_on: Date from -1 year to now

**Returns:** Pandas DataFrame with 500 rows

---

#### 3.3.3 Function: `generate_customers()`

**Purpose:** Create 100 test customer records  
**Data Generated:**

- customer_id: C-001 to C-100
- name: Random company names (Faker)
- region: One of 5 regions
- credit_limit: 10,000-200,000
- outstanding_amount: 0-50,000
- created_on: Date from -2 years to now

**Returns:** Pandas DataFrame with 100 rows

---

#### 3.3.4 Function: `generate_sales_orders(materials, customers)`

**Purpose:** Create 800 test sales orders  
**Dependencies:** Needs materials and customers DataFrames  
**Data Generated:**

- order_id: SO-0001 to SO-0800
- customer_id: Random from customers
- material_id: Random from materials
- qty: 1-100 units
- status: Random (Open/Closed/Cancelled)
- region: Random region
- created_on: Date from -3 months to now

**Returns:** Pandas DataFrame with 800 rows

---

#### 3.3.5 Function: `generate_invoices(customers)`

**Purpose:** Create 400 test invoice records  
**Dependencies:** Needs customers DataFrame  
**Data Generated:**

- invoice_id: INV-0001 to INV-0400
- customer_id: Random from customers
- amount: 1,000-50,000
- due_date: -90 to +30 days from now
- status: Random (Paid/Overdue/Pending)
- days_overdue: Calculated based on due_date
- created_on: Date from -6 months to now

**Special Logic:** If due_date < today, calculate days_overdue

**Returns:** Pandas DataFrame with 400 rows

---

#### 3.3.6 Function: `generate_tickets()`

**Purpose:** Create empty tickets table structure  
**Returns:** Empty DataFrame with columns (no data initially)

---

#### 3.3.7 Function: `generate_audit_log()`

**Purpose:** Create empty audit log table structure  
**Returns:** Empty DataFrame with columns (populated during API calls)

---

#### 3.3.8 Function: `main()`

**Purpose:** Orchestrates data generation and CSV export  
**Steps:**

1. Create `data/` directory
2. Call all generate functions
3. Save each DataFrame as CSV file:
   - data_materials.csv (500 rows)
   - data_customers.csv (100 rows)
   - data_sales_orders.csv (800 rows)
   - data_invoices.csv (400 rows)
   - data_tickets.csv (empty)
   - data_audit_log.csv (empty)

**Why CSV Format:** Easy to load into SAP HANA or other databases

---

## 4. DATA FLOW & SEQUENCE DIAGRAMS

### 4.1 Material Details Query Flow

```
User Request (MCP)
    ↓
get_material_details(material_id, plant_code)
    ↓
POST /api/material/details (MCP Server → FastAPI)
    ↓
get_db() [Create connection]
    ↓
Execute SQL: SELECT FROM MATERIALS WHERE...
    ↓
cursor.fetchone() [Fetch single row]
    ↓
conn.close()
    ↓
Return JSON {material_id, description, category, ...is_below_safety}
    ↓
MCP returns formatted result
    ↓
Display to user
```

### 4.2 Create Ticket Flow (With Authorization & Audit)

```
User Request (MCP)
    ↓
create_ticket(..., x_user_role="PLANT_SUPERVISOR")
    ↓
POST /api/ticket/create with X-User-Role header
    ↓
Check: Is role in ["PLANT_SUPERVISOR", "SALES_MANAGER", "FINANCE"]?
    ├─ NO → HTTP 403 Forbidden
    └─ YES ↓
        get_db() [Create connection]
        ↓
        Generate ticket_id = "TKT-{YYYYMMDDHHMMSS}"
        ↓
        INSERT INTO TICKETS (ticket_id, material_id, priority, ...)
        ↓
        Mask sensitive params: description=[MASKED]
        ↓
        INSERT INTO AUDIT_LOG (ts, user_role, tool_name, params_masked, outcome='SUCCESS')
        ↓
        conn.commit()
        ↓
        Return {ticket_id, message, assigned_team, priority}
        ↓
        MCP returns result
        ↓
        Display to user
```

### 4.3 Customer Summary with JOIN

```
User Request (MCP)
    ↓
get_customer_summary(customer_id="C-001")
    ↓
POST /api/customer/summary
    ↓
Execute SQL:
    SELECT c.*, COUNT(i.invoice_id), SUM(i.amount),
           SUM(CASE WHEN i.status='Overdue' THEN i.amount...)
    FROM CUSTOMERS c
    LEFT JOIN INVOICES i
    ↓
cursor.fetchone()
    ↓
Return {customer_id, name, credit_limit, outstanding_amount,
        total_invoices, total_amount, overdue_amount}
    ↓
Display comprehensive financial overview
```

---

## 5. SECURITY & COMPLIANCE

### 5.1 Authentication & Authorization

- **Header-Based Auth:** Uses `x_user_role` header
- **Role-Based Access Control (RBAC):**
  - Only PLANT_SUPERVISOR, SALES_MANAGER, FINANCE can create tickets
  - Other roles get HTTP 403 Forbidden
- **Environment Variables:** Database credentials stored in .env (not hardcoded)

### 5.2 Sensitive Data Protection

- **Parameter Masking in Logs:**
  ```python
  masked_params = f"material={req.material_id}, priority={req.priority}, description=[MASKED]"
  ```
- **Encrypted Database Connection:** `encrypt=True` in SAP HANA connection
- **Audit Trail:** Every ticket creation logged with timestamp, user role, and outcome

### 5.3 Input Validation

- **Pydantic Models:** Automatic type checking and validation
- **SQL Parametrized Queries:** Prevents SQL injection
  ```python
  cursor.execute("SELECT * FROM MATERIALS WHERE material_id = ? AND plant_code = ?",
                 (req.material_id, req.plant_code))
  ```

---

## 6. ERROR HANDLING & EDGE CASES

### 6.1 Material Details (404 Not Found)

```python
if not row:
    raise HTTPException(status_code=404, detail="Material not found")
```

**Scenario:** Requesting non-existent material_id

### 6.2 Customer Summary (No Invoices)

```python
if not row:
    raise HTTPException(status_code=404, detail="Customer not found")
```

**Scenario:** Requesting non-existent customer_id

### 6.3 Overdue Invoices (No Overdue Records)

```python
if not rows:
    return {
        "customer_id": req.customer_id,
        "total_overdue": 0,
        "invoices": [],
        ...
    }
```

**Scenario:** Customer has no overdue invoices → returns empty list

### 6.4 MCP Tool Error Handling

```python
try:
    response = httpx.post(..., timeout=30.0)
    result = response.json()
    return json.dumps(result, indent=2)
except Exception as e:
    return f"Error: {str(e)}"
```

**Catches:**

- Network timeout (30s limit)
- Connection errors
- JSON parsing errors
- Returns formatted error message to user

---

## 7. KEY BUSINESS METRICS & CALCULATIONS

### 7.1 Material Safety Stock Alert

```
is_below_safety = stock_qty < safety_stock
```

**Purpose:** Identifies materials needing re-order  
**Example:** stock_qty=25, safety_stock=50 → is_below_safety=True

### 7.2 Customer Financial Health

```
Metrics Calculated:
- total_invoices: COUNT(*)
- total_amount: SUM(amount)
- overdue_amount: SUM(CASE WHEN status='Overdue' THEN amount ELSE 0)
- credit_utilization: outstanding_amount / credit_limit
```

### 7.3 Overdue Invoice Escalation

```
if days_overdue > 90:
    recommendation = "ESCALATE_TO_LEGAL"     # Legal action
elif days_overdue > 60:
    recommendation = "HOLD_SHIPMENTS"        # Stop deliveries
else:
    recommendation = "SEND_REMINDER"         # Friendly reminder
```

**Purpose:** Automate collection strategy based on severity

### 7.4 Sales Order Aggregation

```
GROUP BY customer_id
  - order_count: Number of open orders
  - total_qty: Total quantity ordered
```

**Purpose:** Identify top customers by order volume

---

## 8. DATABASE SCHEMA OVERVIEW

### 8.1 MATERIALS Table

```
Columns: material_id, description, category, unit_price,
         stock_qty, safety_stock, plant_code, created_on
Relationships: Used in SALES_ORDERS, TICKETS
Indexes: Likely on material_id, plant_code
```

### 8.2 CUSTOMERS Table

```
Columns: customer_id, name, region, credit_limit, outstanding_amount, created_on
Relationships: Used in SALES_ORDERS, INVOICES
Indexes: Likely on customer_id, region
```

### 8.3 SALES_ORDERS Table

```
Columns: order_id, customer_id, material_id, qty, status, region, created_on
Relationships: FK to CUSTOMERS, FK to MATERIALS
Indexes: Likely on customer_id, material_id, status, region
```

### 8.4 INVOICES Table

```
Columns: invoice_id, customer_id, amount, due_date, status, days_overdue, created_on
Relationships: FK to CUSTOMERS
Indexes: Likely on customer_id, status, due_date
```

### 8.5 TICKETS Table

```
Columns: ticket_id, material_id, priority, assigned_team, description,
         status, created_on, created_by_role
Relationships: FK to MATERIALS
Indexes: Likely on ticket_id, material_id, status
```

### 8.6 AUDIT_LOG Table

```
Columns: log_id, ts, user_role, tool_name, params_masked, outcome
Purpose: Compliance & traceability
Retention: All logs kept for audit trail
```

---

## 9. DEPLOYMENT & EXECUTION

### 9.1 Prerequisites

- Python 3.8+
- SAP HANA database with network access
- Environment variables configured (.env file)

### 9.2 Setup Steps

```bash
# Install dependencies
pip install -r requirements.txt

# Generate test data
python generate_seed_data.py
# Creates: data/data_*.csv files

# Start FastAPI backend
python main.py
# Runs on http://localhost:8000

# In separate terminal, start MCP server
python mcp_server.py
# Listens for tool invocation requests
```

### 9.3 Environment Variables (.env)

```
HANA_HOST=<hostname>
HANA_PORT=<port>
HANA_USER=<username>
HANA_PASSWORD=<password>
```

### 9.4 Available APIs (After startup)

- Health: `GET http://localhost:8000/health`
- Material: `POST http://localhost:8000/api/material/details`
- Sales: `POST http://localhost:8000/api/sales/orders`
- Customer: `POST http://localhost:8000/api/customer/summary`
- Ticket: `POST http://localhost:8000/api/ticket/create`
- Invoice: `POST http://localhost:8000/api/invoices/overdue`

---

## 10. VIVA QUESTIONS & ANSWERS

### Q1: What is the architecture of your project?

**A:** Three-tier architecture:

1. **Presentation Layer:** MCP Server (FastMCP) exposing tools for AI assistants
2. **Business Logic Layer:** FastAPI backend with validation, authorization, and business rules
3. **Data Layer:** SAP HANA database

The MCP server wraps FastAPI endpoints and makes them callable as tools for Claude/AI assistants.

---

### Q2: How do you handle authentication and authorization?

**A:**

- **Authentication:** Role-based using HTTP header `x_user_role`
- **Authorization:** In `create_ticket` endpoint, we check if user role is in allowed list:
  ```python
  if x_user_role not in ["PLANT_SUPERVISOR", "SALES_MANAGER", "FINANCE"]:
      raise HTTPException(status_code=403, detail="Insufficient permissions")
  ```
- Prevents unauthorized role escalation

---

### Q3: How does the system handle sensitive data?

**A:**

1. **Parameter Masking:** Sensitive fields (like full descriptions) masked as `[MASKED]` in audit logs
2. **Encrypted Connections:** Database connection uses `encrypt=True`
3. **Environment Variables:** Credentials stored in .env, not hardcoded
4. **Audit Trail:** All ticket creations logged with timestamp and user role for compliance

---

### Q4: Walk us through the `create_ticket` endpoint with authorization and audit logging.

**A:**

1. User sends POST request with TicketRequest data and x_user_role header
2. Endpoint checks if role is authorized (403 if not)
3. Generate unique ticket_id with timestamp: `TKT-20240815153045`
4. Connect to HANA database
5. Execute INSERT into TICKETS table with all ticket details
6. Mask sensitive params: description becomes `[MASKED]`
7. Execute INSERT into AUDIT_LOG table with timestamp, user_role, tool_name, masked_params
8. Commit both inserts (atomic transaction)
9. Return success response with ticket_id

**Why this design:** Ensures every ticket creation is traceable, auditable, and authorized.

---

### Q5: Explain the customer summary calculation with overdue invoices.

**A:** The SQL query uses:

- **LEFT JOIN:** Includes customers even if they have no invoices
- **GROUP BY:** Aggregates multiple invoices per customer
- **CASE Statement:** Conditionally sums only overdue amounts:
  ```sql
  SUM(CASE WHEN i.status = 'Overdue' THEN i.amount ELSE 0 END)
  ```
  This provides:
- total_invoices: Count of all invoices
- total_amount: Sum of all invoice amounts
- overdue_amount: Sum of only overdue amounts

Helps finance assess customer credit risk.

---

### Q6: What is the purpose of the MCP server and how does it differ from FastAPI?

**A:**

- **FastAPI:** Provides REST API endpoints
- **MCP Server:** Wraps FastAPI endpoints as "tools" that AI assistants (Claude, Copilot) can call

**Difference:**

- FastAPI: Client sends HTTP requests, gets HTTP responses
- MCP: AI assistant requests a tool, MCP makes HTTP call to FastAPI, returns result to AI in standardized format

**Benefits:** Allows AI assistants to integrate with backend services seamlessly.

---

### Q7: How does the overdue invoice recommendation engine work?

**A:** Business logic based on days_overdue:

```
if days_overdue > 90 days:
    recommendation = "ESCALATE_TO_LEGAL"  # Too old, legal action
elif days_overdue > 60 days:
    recommendation = "HOLD_SHIPMENTS"     # Moderate, stop orders
else:
    recommendation = "SEND_REMINDER"      # Recent, friendly reminder
```

**Purpose:** Automate collection strategy priority to help finance team

---

### Q8: Explain the data generation strategy. Why generate seed data?

**A:**

- **Strategy:** Use Faker library to generate realistic test data with:
  - 500 Materials
  - 100 Customers
  - 800 Sales Orders
  - 400 Invoices
- **Why:** Testing system without production data, demonstrations, performance testing
- **Reproducibility:** Master data (PLANTS, REGIONS, etc.) are fixed, but details are random
- **Format:** Save as CSV for easy loading into HANA

---

### Q9: How do you prevent SQL injection attacks?

**A:** Use parametrized queries (placeholders):

```python
cursor.execute(
    "SELECT * FROM MATERIALS WHERE material_id = ? AND plant_code = ?",
    (req.material_id, req.plant_code)  # Parameters passed separately
)
```

- Placeholders (`?`) are not string interpolated
- Database driver escapes/sanitizes parameter values
- Even if material_id contains malicious SQL, it's treated as literal value

---

### Q10: What are the key business metrics you calculate?

**A:**

1. **Material Stock Alert:** `is_below_safety = stock_qty < safety_stock`
2. **Sales Aggregation:** Order count & total quantity per customer per region
3. **Customer Financial Health:** Credit utilization, overdue amounts
4. **Overdue Invoice Severity:** Days overdue to prioritize collection
5. **Operational Metrics:** Ticket creation with role tracking and priority levels

---

### Q11: How do you handle database connection management?

**A:**

- **Stateless Connections:** Each request calls `get_db()` to create fresh connection
- **Connection Closure:** After query execution, `conn.close()` releases resources
- **Error Handling:** If query fails, exception is raised and connection should auto-cleanup
- **Benefits:** Prevents connection leaks, works with connection pooling

---

### Q12: Describe the sales orders query optimization.

**A:** The query groups by customer_id with filters:

```sql
SELECT customer_id, COUNT(*) AS orders, SUM(qty) AS total_qty
FROM SALES_ORDERS
WHERE region = ? AND status = 'Open' AND created_on BETWEEN ? AND ?
GROUP BY customer_id
```

**Optimizations:**

- **WHERE clause:** Filters before GROUP BY to reduce rows processed
- **Status='Open':** Only active orders (faster than processing all then filtering)
- **Date range:** Limits time period of data examined
- **Aggregation:** Reduces output size from potentially 1000s to 100s of rows
- **Grouping:** Shows per-customer totals for easier analysis

---

### Q13: What's the significance of Pydantic models in your project?

**A:**

- **Automatic Validation:** Type checking (material_id must be string, etc.)
- **Error Responses:** Returns 422 Unprocessable Entity with validation errors
- **Documentation:** Pydantic models auto-generate API documentation
- **Serialization:** Converts Python objects to JSON automatically
- **Example:** MaterialRequest enforces that material_id and plant_code are both strings

---

### Q14: How do you ensure audit compliance?

**A:**

1. **Audit Log Table:** Every ticket creation logged with:
   - Timestamp
   - User role
   - Tool name (create_ticket)
   - Masked parameters
   - Outcome (SUCCESS/FAILURE)

2. **Non-repudiation:** User role recorded, cannot deny they performed action
3. **Data Protection:** Sensitive details masked, but audit trail preserved
4. **Retention:** Audit logs likely kept indefinitely for compliance
5. **Query:** Finance can query audit_log for compliance reports

---

### Q15: What role does FastMCP play in AI integration?

**A:**

- **Protocol:** Model Context Protocol - standard for AI tool integration
- **Tools:** Exposes 5 business functions as AI-callable tools
- **Format:** Wraps HTTP responses in standardized format for AI understanding
- **Use Case:** Claude asks "Show me overdue invoices for customer C-001", MCP calls the API and returns result
- **Extensibility:** New tools can be added by adding @mcp.tool() functions

---

## 11. TECHNICAL TERMINOLOGIES

| Term                   | Meaning                                                                   |
| ---------------------- | ------------------------------------------------------------------------- |
| **MCP**                | Model Context Protocol - standard for AI assistants to call tools         |
| **Pydantic**           | Python library for data validation using Python type hints                |
| **HANA**               | SAP HANA - in-memory database management system                           |
| **hdbcli**             | Python driver for SAP HANA database connectivity                          |
| **FastAPI**            | Modern Python web framework for building APIs                             |
| **RBAC**               | Role-Based Access Control - authorization based on user roles             |
| **LEFT JOIN**          | SQL join that includes all rows from left table even if no match in right |
| **GROUP BY**           | SQL clause that aggregates rows sharing same values                       |
| **CASE Statement**     | Conditional logic in SQL (IF-THEN-ELSE)                                   |
| **httpx**              | Python HTTP client library (async-capable alternative to requests)        |
| **Faker**              | Python library generating fake/realistic test data                        |
| **Parametrized Query** | SQL query with placeholders to prevent SQL injection                      |
| **Connection Pooling** | Reusing database connections to improve performance                       |
| **Audit Trail**        | Historical record of all system actions for compliance                    |
| **Parameter Masking**  | Hiding sensitive data in logs (e.g., [MASKED])                            |
| **Stateless API**      | API that doesn't store session state, each request is independent         |
| **Timestamp-based ID** | Unique identifier generated from current date/time                        |
| **DAO Pattern**        | Data Access Object - layer between business logic and database            |

---

## 12. QUICK REFERENCE GUIDE

### API Endpoints Summary

| Endpoint                | Method | Purpose           | Key Feature                   |
| ----------------------- | ------ | ----------------- | ----------------------------- |
| `/health`               | GET    | Health check      | No DB call                    |
| `/api/material/details` | POST   | Get material data | Calculates safety stock alert |
| `/api/sales/orders`     | POST   | Get open orders   | Region + date filtering       |
| `/api/customer/summary` | POST   | Customer overview | LEFT JOIN with invoices       |
| `/api/ticket/create`    | POST   | Create ticket     | RBAC + audit logging          |
| `/api/invoices/overdue` | POST   | Overdue analysis  | Recommendation engine         |

### MCP Tools (5 Total)

1. `get_material_details(material_id, plant_code)`
2. `get_open_sales_orders(region, date_from, date_to)`
3. `get_customer_summary(customer_id)`
4. `create_ticket(material_id, plant_code, priority, assigned_team, description, created_by_role, x_user_role)`
5. `summarize_overdue_invoices(customer_id)`

### Data Generation (6 CSV Files)

1. data_materials.csv (500 rows)
2. data_customers.csv (100 rows)
3. data_sales_orders.csv (800 rows)
4. data_invoices.csv (400 rows)
5. data_tickets.csv (empty structure)
6. data_audit_log.csv (empty structure)

---

## 13. REAL-WORLD USE CASES

### Use Case 1: Plant Manager Checking Stock

**Scenario:** Plant manager needs to know if material MAT-0142 at plant PLT-PUN is low stock

**Flow:**

1. Ask MCP: "Is MAT-0142 low stock at PLT-PUN?"
2. MCP calls get_material_details
3. Returns is_below_safety=True if stock_qty < safety_stock
4. Plant manager orders replenishment immediately

---

### Use Case 2: Sales Manager Monitoring Region

**Scenario:** Sales manager wants to see open orders in North region for the last quarter

**Flow:**

1. Ask MCP: "Show open sales orders in North region for Q3"
2. MCP calls get_open_sales_orders(region="North", date_from="2024-07-01", date_to="2024-09-30")
3. Returns orders aggregated by customer
4. Sales manager identifies high-value customers for follow-up

---

### Use Case 3: Finance Team Collection Action

**Scenario:** Finance needs to know action plan for overdue invoices

**Flow:**

1. Ask MCP: "What's the status of customer C-045?"
2. MCP calls get_customer_summary → shows total_overdue=15000, overdue_amount=5000
3. Ask MCP: "Show overdue invoices for C-045"
4. MCP calls summarize_overdue_invoices → recommendation="HOLD_SHIPMENTS"
5. Finance team holds shipments until payment received

---

### Use Case 4: Plant Maintenance Ticket Creation

**Scenario:** Production supervisor needs to create maintenance ticket

**Flow:**

1. Ask MCP (as PLANT_SUPERVISOR): "Create HIGH priority ticket for Mechanical team"
2. MCP calls create_ticket with x_user_role="PLANT_SUPERVISOR"
3. Authorization passes (role is allowed)
4. Ticket created, audit logged
5. Mechanical team receives ticket assignment
6. Finance can audit who created the ticket and when

---

## 14. PERFORMANCE CONSIDERATIONS

### Query Optimization

- **Material Details:** Single row lookup → O(1) with indexed material_id
- **Sales Orders:** WHERE filters before GROUP BY → reduces data scanned
- **Customer Summary:** LEFT JOIN with aggregation → efficient with indexed customer_id
- **Overdue Invoices:** ORDER BY days_overdue DESC → helps identify priority cases

### Scalability

- **Stateless API:** Can be load balanced across multiple instances
- **Parameterized Queries:** Connection pooling friendly
- **MCP Timeout:** 30 seconds prevents hanging requests
- **CSV Generation:** One-time operation, not performance-critical

---

## 15. FUTURE ENHANCEMENTS

1. **API Rate Limiting:** Protect against abuse
2. **Caching:** Cache frequently accessed materials/customers
3. **Pagination:** Handle large result sets in sales orders query
4. **Advanced Filtering:** More flexible date range options
5. **Real-time Notifications:** Alert when stock goes below safety level
6. **Mobile API:** Optimized endpoints for mobile clients
7. **Analytics Dashboard:** Visualize trends in sales/overdue invoices
8. **API Versioning:** Support v1, v2, etc. for backward compatibility
9. **Webhook Support:** Notify external systems on ticket creation
10. **ML Integration:** Predict which customers likely to default on payments

---

**END OF VIVA PREPARATION DOCUMENT**
