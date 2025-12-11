# EVA Chat UI - Simple Demo Interface

A minimal, single-file chat interface for testing EVA Domain Assistant with your loaded documents.

## ✨ Features

- **Intelligent Greeting**: EVA introduces itself and displays available knowledge spaces
- **Data Source Discovery**: Automatically fetches and displays your Cosmos DB knowledge spaces
- **Contextual Questions**: EVA suggests relevant questions based on your document content
- **Real-time Chat**: Submit questions and get AI-powered answers with source citations
- **Beautiful UI**: Modern, responsive design with smooth animations

## 🚀 Quick Start (Local Testing)

### Option 1: VS Code Live Server (Recommended)

1. **Install Live Server Extension** (if not installed):
   - Open VS Code Extensions (Ctrl+Shift+X)
   - Search for "Live Server" by Ritwick Dey
   - Click Install

2. **Start the Chat UI**:
   ```powershell
   # Navigate to chat UI folder
   cd "c:\Users\marco\Documents\_AI Dev\EVA Suite\eva-api\chat-ui"
   
   # Right-click on index.html in VS Code
   # Select "Open with Live Server"
   ```
   
   **OR use Command Palette**:
   - Press `Ctrl+Shift+P`
   - Type "Live Server: Open with Live Server"
   - Press Enter

3. **Browser will auto-open** at: `http://127.0.0.1:5500/index.html`

### Option 2: Python HTTP Server

```powershell
# Start simple HTTP server
cd "c:\Users\marco\Documents\_AI Dev\EVA Suite\eva-api\chat-ui"
python -m http.server 5500

# Open browser manually
Start-Process "http://127.0.0.1:5500"
```

### Option 3: Direct File Open (Limited Functionality)

```powershell
# Open directly in browser (CORS may block API calls)
Start-Process "c:\Users\marco\Documents\_AI Dev\EVA Suite\eva-api\chat-ui\index.html"
```

⚠️ **Note**: Direct file open may not work due to CORS restrictions. Use Option 1 or 2.

## 🔧 Configuration

### API Connection

The chat UI connects to your EVA API backend. Default configuration:

```javascript
// In index.html (line ~480)
const API_BASE = 'http://127.0.0.1:8000';
const API_KEY = 'demo-api-key'; // Replace with your API key
```

### Get Your API Key

1. **Generate API Key** (if you don't have one):
   ```powershell
   curl -X POST http://127.0.0.1:8000/api/v1/auth/api-keys `
     -H "Authorization: Bearer YOUR_JWT_TOKEN" `
     -H "Content-Type: application/json" `
     -d '{"name": "Demo Chat UI", "scopes": ["read", "write"]}'
   ```

2. **Or use existing key** from your `.env` file:
   ```powershell
   # Check for API_KEY in .env
   Get-Content .env | Select-String "API_KEY"
   ```

3. **Update index.html**:
   - Open `chat-ui/index.html`
   - Find line ~480: `const API_KEY = 'demo-api-key';`
   - Replace with your actual API key

### CORS Configuration

The API is already configured to allow local development:

```python
# src/eva_api/config.py
allowed_origins = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:5500",  # Live Server
    "http://127.0.0.1:5500",  # Live Server
]
```

If using a different port, update `.env.production`:

```env
ALLOWED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000,http://localhost:YOUR_PORT
```

## 🎯 Testing Workflow

### 1. Start EVA API Backend

```powershell
cd "c:\Users\marco\Documents\_AI Dev\EVA Suite\eva-api"
$env:PYTHONPATH='src'
uvicorn eva_api.main:app --host 127.0.0.1 --port 8000
```

**Expected output**:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started webhook delivery service
INFO:     Redis connection established
```

### 2. Verify API Health

```powershell
# Test API is responding
curl http://127.0.0.1:8000/health
```

**Expected response**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-12-08T..."
}
```

### 3. Check Your Knowledge Spaces

```powershell
# List available spaces (requires API key)
curl http://127.0.0.1:8000/api/v1/spaces `
  -H "X-API-Key: YOUR_API_KEY"
```

**Expected response**:
```json
{
  "data": {
    "items": [
      {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "name": "Contract Documents",
        "description": "Legal contracts and agreements",
        "created_at": "2025-12-08T..."
      }
    ]
  }
}
```

### 4. Start Chat UI

```powershell
# Option 1: VS Code Live Server (recommended)
# Right-click index.html → "Open with Live Server"

# Option 2: Python HTTP Server
cd chat-ui
python -m http.server 5500
Start-Process "http://127.0.0.1:5500"
```

### 5. Test the Experience

1. **Open browser** at: `http://127.0.0.1:5500`
2. **EVA greets you**: "Hi! I'm EVA 👋"
3. **Data sources displayed**: Shows your Cosmos DB knowledge spaces
4. **Suggested questions**: Click any question to ask
5. **Chat with EVA**: Type your own questions

**Example interaction**:
```
User: Hi EVA
EVA: Hello again! 👋 I'm here and ready to help...

User: What information is available in Contract Documents?
EVA: [Searches documents and provides answer with citations]
```

## 🐛 Troubleshooting

### Issue: "No Knowledge Spaces Found"

**Problem**: Chat UI shows no data sources.

**Solutions**:
1. **Verify API is running**:
   ```powershell
   curl http://127.0.0.1:8000/health
   ```

2. **Check API key** in `index.html` (line ~480)

3. **Create a knowledge space**:
   ```powershell
   curl -X POST http://127.0.0.1:8000/api/v1/spaces `
     -H "X-API-Key: YOUR_API_KEY" `
     -H "Content-Type: application/json" `
     -d '{"name": "Demo Space", "description": "Test documents"}'
   ```

### Issue: CORS Error in Browser Console

**Problem**: Browser shows "blocked by CORS policy".

**Solutions**:
1. **Don't open file directly** - use Live Server or HTTP server
2. **Verify CORS config** in `.env.production`:
   ```env
   ALLOWED_ORIGINS=http://localhost:5500,http://127.0.0.1:5500
   ```
3. **Restart API** after changing CORS settings

### Issue: "Failed to fetch spaces" Error

**Problem**: API connection fails.

**Solutions**:
1. **Check API URL** in `index.html` (line ~479):
   ```javascript
   const API_BASE = 'http://127.0.0.1:8000'; // Must match API server
   ```

2. **Verify API is accessible**:
   ```powershell
   curl http://127.0.0.1:8000/api/v1/spaces -H "X-API-Key: YOUR_KEY"
   ```

3. **Check browser DevTools** (F12 → Console) for error details

### Issue: Query Times Out

**Problem**: EVA shows "Query timeout" after 2 minutes.

**Solutions**:
1. **Azure OpenAI may be slow** - this is normal for first query
2. **Check API logs** for Azure service errors
3. **Verify Azure OpenAI credentials**:
   ```powershell
   # In .env.production
   AZURE_OPENAI_ENDPOINT=https://...
   AZURE_OPENAI_KEY=...
   ```

## 📊 What EVA Shows

### 1. Greeting Message
```
Hi! I'm EVA 👋

I'm your Intelligent Document Assistant. I can help you find information, 
answer questions, and analyze content from your knowledge spaces.
```

### 2. Data Sources (Knowledge Spaces)
```
Available Knowledge Spaces:

I currently have access to 3 knowledge spaces:

📚 Your Data Sources
┌─────────────────────────────────────────┐
│ 📁 Contract Documents                   │
│ Legal contracts and agreements          │
│ 15 documents • Created Dec 8, 2025      │
└─────────────────────────────────────────┘
```

### 3. Suggested Questions
```
💡 Try asking me:

💡 What information is available in Contract Documents?
💡 Can you summarize the content in Contract Documents?
💡 What are the key terms in the Contract Documents?
```

### 4. Query Responses
```
User: What are the main terms in my contracts?

EVA: Answer:
Based on the contract documents, the main terms include:
1. Payment terms: Net 30 days
2. Termination clause: 60 days notice
3. Confidentiality: 5-year non-disclosure

📎 Sources:
1. Service Agreement (Page 3)
2. Master Contract Template (Page 7)
```

## 🚀 Next Steps

### For 25-User Demo

**Option A: Deploy to Azure Static Web Apps** (Recommended)

```powershell
# 1. Install Azure Static Web Apps CLI
npm install -g @azure/static-web-apps-cli

# 2. Deploy
cd "c:\Users\marco\Documents\_AI Dev\EVA Suite\eva-api\chat-ui"
swa deploy --app-location . --output-location . --app-name eva-chat-demo

# 3. Get public URL (e.g., https://eva-chat-demo.azurestaticapps.net)
```

**Option B: Azure Blob Storage + CDN**

```powershell
# 1. Upload to blob storage
az storage blob upload-batch `
  --account-name evasuitestoragedev `
  --destination '$web' `
  --source chat-ui `
  --pattern "*.html"

# 2. Enable static website hosting
az storage blob service-properties update `
  --account-name evasuitestoragedev `
  --static-website `
  --index-document index.html

# 3. Get public URL
az storage account show `
  --name evasuitestoragedev `
  --query "primaryEndpoints.web" -o tsv
```

### Update API Configuration for Production

```env
# .env.production - Add production chat UI URL
ALLOWED_ORIGINS=http://localhost:8000,https://eva-chat-demo.azurestaticapps.net
```

### Share with 25 Users

1. **Deploy chat UI** to Azure (see above)
2. **Generate 25 API keys**:
   ```powershell
   # Script to create 25 demo keys
   1..25 | ForEach-Object {
     curl -X POST http://127.0.0.1:8000/api/v1/auth/api-keys `
       -H "Authorization: Bearer $JWT" `
       -d "{\"name\": \"Demo User $_\", \"scopes\": [\"read\"]}"
   }
   ```
3. **Share URL + API key** with each user
4. **Users update their API key** in browser console:
   ```javascript
   // Browser console (F12)
   localStorage.setItem('eva_api_key', 'sk_user1_actual_key');
   location.reload();
   ```

## 📝 Customization

### Change EVA's Personality

Edit line ~555 in `index.html`:

```javascript
addMessage('eva', `
    <strong>Hi! I'm EVA 👋</strong><br><br>
    [Customize this greeting message]
`);
```

### Modify Suggested Questions

Edit line ~651 in `index.html`:

```javascript
function generateSuggestedQuestions(space) {
    return [
        "Your custom question 1?",
        "Your custom question 2?",
        "Your custom question 3?"
    ];
}
```

### Update Branding

Edit CSS in `index.html` (lines ~20-400):

```css
:root {
    --primary: #0066CC;        /* Change brand color */
    --primary-dark: #004C99;
    /* ... */
}
```

## 🎨 Features Breakdown

| Feature | Status | Description |
|---------|--------|-------------|
| Greeting | ✅ | EVA introduces itself |
| Data Sources | ✅ | Fetches knowledge spaces from Cosmos DB |
| Suggested Questions | ✅ | Context-aware question generation |
| Real-time Chat | ✅ | Submit queries and get answers |
| Source Citations | ✅ | Shows document references |
| Typing Indicator | ✅ | Visual feedback during processing |
| Error Handling | ✅ | User-friendly error messages |
| Responsive Design | ✅ | Works on desktop and mobile |
| Auto-scroll | ✅ | Keeps latest message visible |
| Enter to Send | ✅ | Press Enter to submit |

## 🔒 Security Notes

⚠️ **This is a demo UI** - production deployment requires:

1. **Secure API keys**: Don't hardcode keys in HTML
2. **JWT authentication**: Implement proper login flow
3. **HTTPS only**: Deploy with SSL certificates
4. **Rate limiting**: Already implemented in backend
5. **Input validation**: Backend validates all queries
6. **CORS restrictions**: Limit to your production domain

## 📚 Related Documentation

- **Backend API**: `docs/SPECIFICATION.md`
- **APIM Setup**: `docs/APIM-DEMO-SANDBOX-SETUP.md`
- **Production Deployment**: `PRODUCTION-DEPLOYMENT-QUICK-START.md`
- **Phase 3 Features**: `PHASE-3-COMPLETION.md`

## 🆘 Support

**Issues?** Check:
1. Browser DevTools Console (F12)
2. API Server Logs (terminal running uvicorn)
3. Network tab in DevTools (check failed requests)

**Still stuck?** Review troubleshooting section above or check API documentation.

---

**🎉 Enjoy testing EVA with your documents!**
