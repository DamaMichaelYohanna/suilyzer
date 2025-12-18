# Suilyzer Backend

A FastAPI backend that analyzes Sui blockchain transactions and provides human-readable explanations using Google Gemini AI. **This backend also serves the frontend static files**, providing a complete single-server deployment solution.

## Features

- **Transaction Analysis**: Fetch and parse Sui transaction data
- **AI-Powered Explanations**: Generate plain English summaries using Google Gemini
- **Visual Diagrams**: Create graph representations of transaction flows
- **Smart Caching**: Cache results to avoid repeated API calls
- **Object Tracking**: Track created, mutated, and deleted objects
- **Gas Monitoring**: Display gas costs in user-friendly format
- **Integrated Frontend**: Serves the web UI at `/app` endpoint

## Prerequisites

- Python 3.11 or higher
- Google Gemini API key (get one at https://makersuite.google.com/app/apikey)

## Installation

1. Navigate to the backend directory:
```powershell
cd backend
```

2. Create a virtual environment:
```powershell
python -m venv venv
```

3. Activate the virtual environment:
```powershell
.\venv\Scripts\Activate.ps1
```

4. Install dependencies:
```powershell
pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the backend directory with the following variables:

```env
# Required
GEMINI_API_KEY=your_gemini_api_key_here

# Optional (defaults shown)
SUI_RPC_URL=https://fullnode.mainnet.sui.io:443
GEMINI_MODEL=gemini-1.5-flash
CACHE_TTL_SECONDS=3600
HOST=0.0.0.0
PORT=8000
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Google Gemini API key (required) | None |
| `SUI_RPC_URL` | Sui RPC endpoint URL | `https://fullnode.mainnet.sui.io:443` |
| `GEMINI_MODEL` | Gemini model to use | `gemini-2.5-flash` |
| `CACHE_TTL_SECONDS` | Cache time-to-live in seconds | `3600` (1 hour) |
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `8000` |

## Running the Server

From the backend directory with your virtual environment activated:

```powershell
python -m app.main
```

Or using uvicorn directly:

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The server will start at `http://localhost:8000`

### Accessing the Application

Once the server is running:
- **Frontend UI**: http://localhost:8001/app (or http://localhost:8000/app)
- **API Documentation**: http://localhost:8001/docs
- **Health Check**: http://localhost:8001/health

The backend automatically serves the frontend from the `../frontend` directory.

## API Endpoints

### POST /analyze

Analyze a Sui transaction and return human-readable explanation.

**Request:**
```json
{
  "digest": "transaction_digest_here"
}
```

**Response:**
```json
{
  "summary": "This transaction sent 0.5 SUI from address 0x1234... to address 0x5678....",
  "diagram": {
    "nodes": [
      {
        "id": "addr_0x1234...",
        "label": "0x1234...5678",
        "type": "address"
      }
    ],
    "edges": [
      {
        "source": "addr_0x1234...",
        "target": "addr_0x5678...",
        "label": "+0.5 SUI",
        "type": "transfer"
      }
    ]
  },
  "objects": {
    "created": [],
    "mutated": [],
    "deleted": []
  },
  "packages": [
    {
      "package_id": "0x2",
      "module": "transfer",
      "function": "public_transfer"
    }
  ],
  "gas_used": "0.002 SUI"
}
```

**Status Codes:**
- `200`: Success
- `400`: Invalid request (bad digest format)
- `404`: Transaction not found
- `500`: Internal server error

### GET /

Get API information and available endpoints. Redirects to `/app` if frontend is available.

### GET /app

Serves the frontend web application UI.

### GET /health

Health check endpoint showing cache size and configuration.

### GET /static/*

Serves frontend static files (CSS, JavaScript, images).

### DELETE /cache/{digest}

Clear a specific transaction from cache.

### DELETE /cache

Clear all cached transactions.

## Project Structure

```
suilyzer/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py           # FastAPI application and endpoints
│   │   ├── config.py         # Configuration management
│   │   ├── cache.py          # In-memory caching
│   │   ├── sui_rpc.py        # Sui RPC client
│   │   ├── parser.py         # Transaction parser
│   │   ├── gemini_client.py  # Google Gemini integration
│   │   ├── diagram.py        # Diagram generation
│   │   ├── schemas.py        # Pydantic models
│   │   └── utils.py          # Helper functions
│   ├── requirements.txt      # Python dependencies
│   ├── .env                  # Environment configuration
│   └── README.md            # This file
│
├── frontend/                 # Served by backend at /app
│   ├── index.html           # Main UI
│   ├── main.js              # Application logic
│   ├── diagram.js           # Cytoscape visualization
│   └── styles.css           # Styling
│
├
└── README.md                # Main project documentation
```

## Module Responsibilities

### main.py
- FastAPI application initialization
- CORS configuration
- API endpoints
- Request/response handling
- Frontend static file serving
- Root redirect to /app

### config.py
- Environment variable management
- Configuration validation
- Default values

### cache.py
- In-memory cache with TTL
- Cache operations (get, set, delete, clear)
- Automatic expiration

### sui_rpc.py
- Sui RPC communication
- Transaction data fetching
- Error handling

### parser.py
- Parse raw Sui transaction data
- Extract object changes
- Extract package information
- Format gas costs
- Structure data for Gemini

### gemini_client.py
- Google Gemini API integration
- Generate human-readable explanations
- System prompt management

### diagram.py
- Generate graph representation
- Create nodes (addresses, objects, packages)
- Create edges (transfers, mutations, creations)

### schemas.py
- Pydantic models for validation
- Request/response types
- Data structures

### utils.py
- Helper functions
- Format SUI amounts
- Truncate addresses
- Parse object types

## Frontend Integration

### Built-in Frontend Serving

The backend automatically serves the frontend application from the `../frontend` directory:

- **Frontend files location**: `../frontend/` (relative to backend directory)
- **Frontend URL**: `http://localhost:8001/app`
- **Static assets**: Served at `/static/` endpoint
- **Auto-redirect**: Root `/` redirects to `/app`

This means you only need to deploy the backend - the frontend is included automatically!

### Frontend Structure

```
frontend/
├── index.html    # Main UI (served at /app)
├── main.js       # Application logic (served at /static/main.js)
├── diagram.js    # Cytoscape visualization (served at /static/diagram.js)
└── styles.css    # Styling (served at /static/styles.css)
```

### How Frontend Connects to Backend

The frontend automatically detects the API URL:

```javascript
// From frontend/main.js
const API_BASE_URL = window.location.hostname === 'localhost' && window.location.port === '' 
    ? 'http://localhost:8001'
    : window.location.origin;

// Makes requests to /analyze endpoint
const response = await fetch(`${API_BASE_URL}/analyze`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    digest: 'transaction_digest_here'
  })
});

const data = await response.json();
console.log(data.summary);
```

### Standalone Frontend Development

You can also develop the frontend separately by opening `frontend/index.html` directly in a browser. It will connect to `http://localhost:8001` for API calls.

## Caching Behavior

- Results are cached by transaction digest
- Cache TTL is configurable (default: 1 hour)
- Cached responses include Gemini explanations and parsed data
- Cache prevents repeated expensive API calls
- Cache automatically expires based on TTL
- Manual cache clearing available via DELETE endpoints

## Error Handling

The backend handles various error scenarios:

- **Invalid digest format**: 400 Bad Request
- **Transaction not found**: 404 Not Found
- **Sui RPC errors**: 500 with error details
- **Gemini API failures**: 500 with error details
- **Missing API key**: Startup failure with clear message

All errors return JSON with `error` and optional `detail` fields.

## Development

### Running Tests

```powershell
# Install dev dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest
```

### Code Style

The project follows PEP 8 style guidelines. Format code with:

```powershell
pip install black
black app/
```

## Deployment

### Single Server Deployment

Since the backend serves the frontend, you only need to deploy one application:

**Railway / Render / Fly.io:**
```bash
# Set environment variables
GEMINI_API_KEY=your_key_here
PORT=8001

# Start command
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

**Access points:**
- Frontend: `https://your-domain.com/app`
- API: `https://your-domain.com/docs`
- Health: `https://your-domain.com/health`

**Important:** Deploy from the project root (parent of backend/), not from the backend directory, so that the frontend folder is accessible.

## Troubleshooting

### "GEMINI_API_KEY is required"
Set the `GEMINI_API_KEY` environment variable in your `.env` file.

### "Connection refused" errors
Ensure the Sui RPC URL is accessible and correct.

### Slow responses
First request for a transaction is slow due to RPC + Gemini calls. Subsequent requests use cache.

### Import errors
Ensure you're in the backend directory and virtual environment is activated.

### Frontend not loading (404 on /app)
- Ensure the `frontend/` directory exists at the project root (parent of backend/)
- Check that `index.html` exists in the frontend directory
- Restart the server to reload static file mounts

### CSS/JS not loading
- Verify paths in `index.html` use `/static/` prefix
- Check browser console for 404 errors
- Ensure frontend files exist: `styles.css`, `main.js`, `diagram.js`

## License

MIT License

## Support

For issues and questions, please open an issue on the project repository.
