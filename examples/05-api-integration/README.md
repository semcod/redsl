# ReDSL Example 05: REST API Integration

This example demonstrates how to use ReDSL as a microservice via REST API.

## Features

- **Analyze Project** (`POST /analyze`) — Submit toon.yaml content for analysis
- **Refactoring Decisions** (`POST /decide`) — Get DSL-based refactoring decisions
- **Execute Refactoring** (`POST /refactor`) — Run refactoring pipeline
- **Custom Rules** (`POST /rules`) — Add team-specific DSL rules
- **Memory Stats** (`GET /memory/stats`) — View agent memory statistics

## Running the Example

This is a **client-only** example that prints curl commands and Python client code.
It assumes a ReDSL server is running locally.

### Start the Server

```bash
cd redsl/
uvicorn app.api:app --port 8000
```

### Run the Client

```bash
cd examples/05-api-integration
python main.py
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/analyze` | POST | Analyze project from toon.yaml content |
| `/decide` | POST | Get refactoring decisions |
| `/refactor` | POST | Execute refactoring pipeline |
| `/rules` | POST | Add custom DSL rules |
| `/memory/stats` | GET | Get memory statistics |

## Example Output

The script prints:
- curl commands for each endpoint
- Python httpx client code
- WebSocket client example for real-time refactoring

## Prerequisites

- ReDSL server running on `localhost:8000`
- Python 3.10+
- (Optional) `httpx` for Python client examples
- (Optional) `websockets` for WebSocket example
