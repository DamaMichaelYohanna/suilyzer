# Suilyzer 🔍

A complete MVP web application that analyzes Sui blockchain transactions and explains them in plain, human-readable language using Google Gemini AI.

## 🌟 Features

- **Plain English Explanations**: Converts complex blockchain transactions into easy-to-understand summaries
- **Visual Transaction Flow**: Interactive diagrams showing how assets and objects move
- **Object Tracking**: Displays created, mutated, and deleted objects
- **Package Information**: Shows involved Move packages, modules, and functions
- **Gas Monitoring**: Clear display of transaction costs
- **Smart Caching**: Prevents repeated API calls for the same transaction
- **Modern UI**: Clean, responsive interface with dark theme

## 📁 Project Structure

```
suilyzer/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py           # FastAPI application
│   │   ├── config.py         # Configuration management
│   │   ├── cache.py          # In-memory caching
│   │   ├── sui_rpc.py        # Sui RPC client
│   │   ├── parser.py         # Transaction parser
│   │   ├── gemini_client.py  # Google Gemini integration
│   │   ├── diagram.py        # Diagram generation
│   │   ├── schemas.py        # Pydantic models
│   │   └── utils.py          # Helper functions
│   ├── requirements.txt      # Python dependencies
│   └── README.md            # Backend documentation
│
├── frontend/
│   ├── index.html           # Main HTML page
│   ├── main.js              # Core JavaScript logic
│   ├── styles.css           # Styling
│   └── diagram.js           # Diagram rendering
│
└── README.md                # This file
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+**
- **Google Gemini API Key** - Get one at [Google AI Studio](https://makersuite.google.com/app/apikey)

### Setup & Run (Easiest Method)

1. **Run setup script** (first time only):
```powershell
.\setup.ps1
```

2. **Add your Gemini API key** to `backend\.env`:
```env
GEMINI_API_KEY=your_api_key_here
```

3. **Start the application**:
```powershell
.\start.ps1
```

4. **Access the app** at: **http://localhost:8001/app**

That's it! The frontend is served by the backend, so you only need one server running.

---

### Manual Setup (Alternative)

### 1. Backend Setup

```powershell
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Create .env file
@"
GEMINI_API_KEY=your_api_key_here
SUI_RPC_URL=https://fullnode.mainnet.sui.io:443
"@ | Out-File -FilePath .env -Encoding UTF8
```

### 2. Run Backend

```powershell
# From backend directory with venv activated
python -m app.main
```

The backend will start at `http://localhost:8000`

### 3. Access the Application

The frontend is automatically served by the backend at:
- **Frontend UI**: http://localhost:8001/app
- **API Documentation**: http://localhost:8001/docs
- **Health Check**: http://localhost:8001/health

(For development, you can also open `frontend/index.html` directly in your browser)

## 🎯 Usage

1. **Get a Transaction Digest**: Find a transaction on [Sui Explorer](https://suiexplorer.com/)
2. **Paste the Digest**: Enter it into the input field
3. **Analyze**: Click "Analyze Transaction"
4. **Review Results**:
   - Read the plain English summary
   - Explore the visual transaction flow
   - Check object changes
   - View involved packages

## 🔧 Configuration

Create a `.env` file in the `backend` directory:

```env
# Required
GEMINI_API_KEY=your_gemini_api_key_here

# Optional (with defaults)
SUI_RPC_URL=https://fullnode.mainnet.sui.io:443
GEMINI_MODEL=gemini-1.5-flash
CACHE_TTL_SECONDS=3600
HOST=0.0.0.0
PORT=8000
```

## 📡 API Endpoints

### `POST /analyze`

Analyze a transaction.

**Request:**
```json
{
  "digest": "transaction_digest_here"
}
```

**Response:**
```json
{
  "summary": "Human-readable explanation...",
  "diagram": {
    "nodes": [...],
    "edges": [...]
  },
  "objects": {
    "created": [...],
    "mutated": [...],
    "deleted": [...]
  },
  "packages": [...],
  "gas_used": "0.002 SUI"
}
```

### Other Endpoints

- `GET /` - API information
- `GET /health` - Health check
- `GET /app` - Serve frontend
- `DELETE /cache` - Clear cache
- `DELETE /cache/{digest}` - Clear specific transaction

## 🏗️ Architecture

### Backend (FastAPI)

1. **Request Handler** (`main.py`) - Receives transaction digest
2. **Cache Check** (`cache.py`) - Returns cached result if available
3. **Sui RPC Client** (`sui_rpc.py`) - Fetches transaction data
4. **Parser** (`parser.py`) - Extracts structured information
5. **Diagram Generator** (`diagram.py`) - Creates visual representation
6. **Gemini Client** (`gemini_client.py`) - Generates explanation
7. **Response** - Returns complete analysis

### Frontend (Vanilla JS)

1. **User Input** - Transaction digest entry
2. **API Call** - POST request to backend
3. **Results Display**:
   - Summary text
   - Cytoscape.js diagram
   - Object lists
   - Package information

## 🎨 Features in Detail

### Transaction Parsing

- Extracts sender and recipients
- Identifies object changes (created/mutated/deleted)
- Tracks coin transfers and amounts
- Calculates gas costs
- Identifies involved packages and modules

### AI Explanation

Uses Google Gemini to:
- Convert technical data to plain English
- Explain what happened in the transaction
- Describe object changes in simple terms
- Present information clearly

### Visual Diagram

Interactive graph showing:
- **Nodes**: Addresses (blue), Objects (purple), Packages (green)
- **Edges**: Transfers, mutations, creations, deletions
- **Interactions**: Hover to highlight, click for details

### Caching

- Results cached by transaction digest
- Default TTL: 1 hour
- Prevents repeated RPC and AI API calls
- Significantly improves performance

## 🛠️ Development

### Backend Development

```powershell
cd backend

# Install dev dependencies
pip install pytest pytest-asyncio black

# Run tests
pytest

# Format code
black app/
```

### Frontend Development

The frontend uses vanilla JavaScript with no build step. Simply edit the files and refresh your browser.

## 🚀 Deployment

### Single Server Deployment

Since the frontend is served by FastAPI, you only need to deploy the backend:

**Railway / Render / Fly.io:**
1. Set environment variable: `GEMINI_API_KEY=your_key`
2. Set start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
3. Deploy from repository root
4. Access at: `https://your-domain.com/app`

**Environment Variables for Production:**
```env
GEMINI_API_KEY=your_key_here
SUI_RPC_URL=https://fullnode.mainnet.sui.io:443
PORT=8001
HOST=0.0.0.0
```

## 🐛 Troubleshooting

### "GEMINI_API_KEY is required"
- Add the key to `backend\.env` file
- Restart the backend server with `.\start.ps1`

### "Transaction not found"
- Verify the transaction digest is correct
- Check you're using the correct network (testnet/mainnet)
- Update `SUI_RPC_URL` in `backend\.env`

### Port already in use
- Change `PORT=8002` in `backend\.env`
- Restart with `.\start.ps1`

### Frontend not loading at /app
- Ensure backend is running: http://localhost:8001/health
- Check that `frontend/` folder exists at project root
- Restart server to mount static files

### Diagram not rendering
- Check browser console for errors
- Ensure Cytoscape.js CDN is accessible
- Verify transaction has diagram data

## 📝 Example Transaction

Try analyzing this mainnet transaction:
```
Enter any recent transaction digest from https://suiexplorer.com/
```

## 🔒 Security Notes

- Never commit API keys to version control
- Use environment variables for sensitive data
- API keys stored in `.env` file (not tracked by git)
- Consider rate limiting for production use

## 📄 License

MIT License - Feel free to use this project for learning or commercial purposes.

## 🤝 Contributing

Contributions welcome! Areas for improvement:
- Additional blockchain networks
- More visualization options
- Transaction comparison features
- Historical analysis
- Export functionality

## 📚 Resources

- [Sui Documentation](https://docs.sui.io/)
- [Sui Explorer](https://suiexplorer.com/)
- [Google Gemini API](https://ai.google.dev/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Cytoscape.js](https://js.cytoscape.org/)

## 👥 Support

For issues or questions:
1. Check the backend README.md for detailed configuration
2. Review console logs for errors
3. Verify all prerequisites are installed
4. Ensure API keys are correctly configured

---

**Built with ❤️ for the Sui blockchain community**
