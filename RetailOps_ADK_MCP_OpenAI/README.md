# RetailOps AI – Google ADK + MCP + OpenAI GPT-4o mini

A fresh retail-domain agent project using only the requested stack:
1. Google ADK – agent orchestration
2. MCP – enterprise tool integration
3. OpenAI GPT-4o mini – LLM
4. Python – business logic
5. FastAPI – REST API
6. SQL – relational data
7. Docker – containerization

## Database choice

SQL is a query language, not a database product. This starter uses **SQLite**, a local SQL database included with Python, so no database server needs to be installed. The schema and queries can later be adapted to SQL Server or PostgreSQL if that is what your environment provides.

## Architecture

- Google ADK root agent uses `LiteLlm(model="openai/gpt-4o-mini")`.
- ADK connects to three independent MCP servers over local STDIO.
- Procurement MCP exposes PO search, PO details and PO/ASN/GRN quantity calculations.
- Inventory MCP exposes stock lookup, low-stock identification and pending-GRN summary.
- Vendor MCP exposes vendor lookup and vendor performance aggregation.
- All MCP servers and FastAPI use the same SQLite database.
- This first version is read-only and uses synthetic retail records.

## Requirements

- Python 3.12 recommended
- OpenAI API key with API access/available billing
- Docker Desktop (optional for container milestone)

## 1. Setup on Windows PowerShell

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks activation:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
```

## 2. Configure OpenAI

```powershell
Copy-Item .env.example .env
```

Edit `.env`:

```env
OPENAI_API_KEY=your_actual_key
ADK_MODEL=openai/gpt-4o-mini
```

Never commit `.env` or expose your API key.

On Windows, if LiteLLM encounters an encoding issue, set:

```powershell
$env:PYTHONUTF8 = "1"
```

## 3. Run FastAPI

From the project root:

```powershell
uvicorn api.main:app --reload --port 8080
```

Open:
- API health: http://127.0.0.1:8080/health
- Swagger docs: http://127.0.0.1:8080/docs
- Purchase orders: http://127.0.0.1:8080/purchase-orders
- Low stock: http://127.0.0.1:8080/inventory/low-stock

## 4. Run Google ADK

Open a second PowerShell window, activate the same virtual environment, and run from the project root:

```powershell
$env:PYTHONUTF8 = "1"
adk web --port 8000 .
```

Open the local URL printed by ADK and select `retailops_agent`.

Try:
1. `Show all purchase orders for ABC Textiles.`
2. `For PO1001, compare PO, ASN and GRN quantities.`
3. `Find all low-stock SKUs.`
4. `Summarize PO, ASN and GRN performance for V001.`
5. `Give me a combined procurement and inventory exception summary.`

## 5. Inspect MCP tools

Run the Procurement MCP server through MCP Inspector:

```powershell
npx -y @modelcontextprotocol/inspector python -m retailops_mcp.servers.procurement_server
```

The server exposes tools, a resource and a prompt. The Inventory and Vendor servers can be inspected similarly by changing the module name.

## 6. Docker

Create `.env` first, then:

```powershell
docker compose up --build
```

- FastAPI: http://localhost:8080/docs
- ADK web: http://localhost:8000

Stop:

```powershell
docker compose down
```

The named Docker volume retains the demo SQL database.

## SQL definitions

- Pending ASN = `MAX(PO_Qty - ASN_Qty, 0)`
- Pending GRN against ASN = `MAX(ASN_Qty - GRN_Qty, 0)`
- Unreceived against PO = `MAX(PO_Qty - GRN_Qty, 0)`

Do not mix these three measures.

## Important production gaps

This is a learning/portfolio starter, not production-ready software. Before customer deployment add:
- Identity authentication and role/site/tenant authorization
- Input validation and database migration management
- Audit logs and structured application logs
- Timeouts, retries, rate limiting and error handling
- Human approval before any side-effecting operation
- Tests for business calculations and MCP integration
- Secret management and network security
- Monitoring, evaluation and deployment controls

No email sending, PO updates or inventory adjustments are enabled in this version.
