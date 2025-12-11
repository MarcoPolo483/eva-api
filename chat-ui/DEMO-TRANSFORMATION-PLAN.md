# EVA i11y Demo - Three Concepts Transformation Plan

**Status**: 🎯 Ready to Execute  
**Date**: December 9, 2025  
**Owner**: P04-LIB + P15-DVM (POD-F)  
**Duration**: 5-7 days (5 phases)

---

## 🧩 CONTEXT ENGINEERING

### Mission
Transform EVA i11y Demo from mock API integration to production-ready RAG chat interface using real Government of Canada data sources, fully adhering to Three Concepts Pattern (Context Engineering + Housekeeping + Workspace Management).

### Constraints
- **WCAG 2.2 AA**: All UI/UX must maintain accessibility compliance
- **Bilingual EN-CA/FR-CA**: Full bilingual support required
- **GC Design System**: Canada.ca design tokens and patterns
- **Real Data**: Leverage actual Service Canada, Jurisprudence, and Canada Life content
- **No Mock Data**: Remove all hardcoded/fallback demo data
- **Cosmos DB Query Bug**: Must fix cross-partition query issue (CRITICAL BLOCKER)

### Reuses
- **Existing seeded data**: Service Canada Programs, EVA Development Docs (already in Cosmos DB)
- **POD-S Data Sources**: Jurisprudence (500-1000 PDFs), AssistMe (1450+ XML articles), Canada Life (20-30 booklets)
- **Current UI**: Holiday-themed bilingual interface (1712 lines, 57% Three Concepts compliance)
- **Backend**: FastAPI + Cosmos DB + Azure OpenAI + Blob Storage

### Validates
- Database connectivity before data operations
- Data ingestion success with checksums
- UI/UX accessibility with automated WCAG tests
- RAG query responses with citation validation
- Three Concepts compliance at each phase

---

## 📋 TRANSFORMATION PHASES

### **Phase 1: Fix Cosmos DB Query Bug** (Day 1, 4 hours) ⚠️ CRITICAL BLOCKER

**Context Engineering:**
- **Mission**: Enable cross-partition queries in `list_spaces()` method
- **Root Cause**: Async/sync iterator interaction when `enable_cross_partition_query=True`
- **Solution Options**:
  1. Wrap query in `asyncio.to_thread()` for sync iterator in async context
  2. Use `list()` to consume iterator immediately (like test script)
  3. Implement pagination with explicit partition keys

**Implementation:**
```python
# File: src/eva_api/services/cosmos_service.py (lines 186-210)

async def list_spaces(self, cursor: Optional[str] = None, limit: int = 20):
    """
    🧩 CONTEXT_ENGINEERING: List Knowledge Spaces (Cross-Partition)
    
    Mission: Retrieve all spaces from Cosmos DB across partitions
    Constraints: Partition key is /id, requires cross-partition query
    Reuses: Cosmos SDK query_items with asyncio.to_thread wrapper
    Validates: Returns list of spaces, handles empty results gracefully
    
    🧹 HOUSEKEEPING: No cleanup required (read-only operation)
    """
    if self.mock_mode:
        return mock_spaces, None, False
    
    try:
        # Run synchronous Cosmos query in thread pool to avoid async/sync conflict
        def _query_spaces():
            query = "SELECT * FROM c"
            items = list(self.spaces_container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            return items[:limit] if limit else items
        
        # Execute in thread pool (Cosmos SDK is synchronous)
        import asyncio
        items_list = await asyncio.to_thread(_query_spaces)
        
        # No pagination for cross-partition queries (simplicity)
        next_cursor = None
        has_more = len(items_list) == limit
        
        logger.info(f"Retrieved {len(items_list)} spaces from Cosmos DB")
        return items_list, next_cursor, has_more
        
    except Exception as e:
        logger.error(f"Failed to list spaces: {e}", exc_info=True)
        return [], None, False
```

**Validation:**
1. Restart API server: `$env:PYTHONPATH = "$PWD\src"; python -m uvicorn eva_api.main:app --host 127.0.0.1 --port 8000 --reload --env-file .env`
2. Test endpoint: `curl -H "X-API-Key: demo-api-key" http://127.0.0.1:8000/api/v1/spaces`
3. Verify: Returns 10-12 spaces (Service Canada, EVA Docs, etc.)
4. Check UI: Open http://localhost:8080/ and confirm spaces appear in dropdown

**Success Criteria:**
- ✅ API returns 200 OK with array of spaces
- ✅ UI displays spaces in dropdown (not "No Knowledge Spaces Found")
- ✅ Server remains stable (no crashes)
- ✅ Logs show "Retrieved X spaces from Cosmos DB"

**Deliverables:**
- Fixed `cosmos_service.py` with asyncio.to_thread wrapper
- Passing curl tests
- Working UI with loaded spaces

---

### **Phase 2: Remove Mock Data & Enhance UI** (Day 2, 6 hours)

**Context Engineering:**
- **Mission**: Remove all mock/demo data references from UI, enhance Three Concepts compliance to 80%+
- **Constraints**: Preserve bilingual functionality, maintain WCAG 2.2 AA, keep holiday theme
- **Reuses**: Existing Three Concepts headers, GC Design System patterns

**Tasks:**

#### 2.1 Remove Mock Data References
```javascript
// File: chat-ui/index.html

// REMOVE these lines (if present):
// - loadDemoData() function
// - demo-data.json references
// - Fallback mock responses

// ENSURE all data comes from API:
async function fetchSpaces() {
    // Already correct - uses fetch(`${API_BASE}/api/v1/spaces`)
    // No changes needed here
}
```

#### 2.2 Add Health Monitoring (HK Improvement)
```javascript
// File: chat-ui/index.html (add after line 1577)

/**
 * 🧹 HOUSEKEEPING: Active Health Monitoring
 * 
 * Creates: 30s interval health check timer
 * Validates: API availability, Cosmos DB connection
 * Monitors: Response times, error rates
 * Cleans: Clears timer on page unload
 */
let healthCheckTimer = null;

async function checkHealth() {
    try {
        const start = performance.now();
        const response = await fetch(`${API_BASE}/health`, {
            headers: { 'X-API-Key': API_KEY }
        });
        const elapsed = performance.now() - start;
        
        if (response.ok) {
            const data = await response.json();
            console.log(`✅ Health check: ${data.status} (${elapsed.toFixed(0)}ms)`);
        } else {
            console.warn(`⚠️ Health check failed: ${response.status}`);
        }
    } catch (error) {
        console.error('❌ Health check error:', error);
    }
}

// Start monitoring on page load
window.addEventListener('load', () => {
    checkHealth(); // Immediate check
    healthCheckTimer = setInterval(checkHealth, 30000); // Every 30s
});

// Cleanup on unload (already exists, add to existing handler)
window.addEventListener('beforeunload', () => {
    if (healthCheckTimer) {
        clearInterval(healthCheckTimer);
        healthCheckTimer = null;
    }
    // ... existing cleanup code
});
```

#### 2.3 Replace Hardcoded Colors with GC Design Tokens
```css
/* File: chat-ui/gc-design-tokens.css (NEW FILE) */

/**
 * 🧩 CONTEXT_ENGINEERING: GC Design System Tokens
 * 
 * Mission: Official Canada.ca design system colors and spacing
 * Constraints: Must match Treasury Board Secretariat specifications
 * Reuses: canada.ca/en/government/about/design-system
 * Validates: Color contrast ratios meet WCAG 2.2 AA
 */

:root {
    /* GC Official Colors */
    --gc-red: #C8102E;           /* Canada wordmark red */
    --gc-black: #000000;         /* Text primary */
    --gc-grey-dark: #333333;     /* Text secondary */
    --gc-grey-medium: #666666;   /* Text tertiary */
    --gc-grey-light: #E1E4E7;    /* Borders */
    --gc-white: #FFFFFF;         /* Background */
    
    /* Service Canada Brand */
    --gc-blue-dark: #26374A;     /* Service Canada primary */
    --gc-blue-medium: #335075;   /* Links */
    --gc-blue-light: #EAF3F9;    /* Background accent */
    
    /* Seasonal Theme (Holiday) */
    --gc-green-dark: #2E7D32;    /* Success / Winter green */
    --gc-red-dark: #C62828;      /* Error / Holiday red */
    --gc-gold: #FFD700;          /* Stars / Decorations */
    
    /* Spacing (8px base) */
    --gc-space-xs: 4px;
    --gc-space-sm: 8px;
    --gc-space-md: 16px;
    --gc-space-lg: 24px;
    --gc-space-xl: 32px;
    
    /* Typography */
    --gc-font-family: "Noto Sans", Arial, sans-serif;
    --gc-line-height: 1.5;
}
```

**Update index.html** to use tokens:
```html
<!-- Add to <head> section -->
<link rel="stylesheet" href="gc-design-tokens.css">

<!-- Replace hardcoded colors in <style> section with CSS variables -->
<style>
    /* Example replacements: */
    .success-color { color: var(--gc-green-dark); }  /* was #2E7D32 */
    .error-color { color: var(--gc-red-dark); }      /* was #C62828 */
    .star { color: var(--gc-gold); }                 /* was #FFD700 */
</style>
```

#### 2.4 Enhance ARIA Labels (WCAG Improvement)
```html
<!-- File: chat-ui/index.html -->

<!-- Add ARIA labels to key interactive elements: -->
<select id="spaceSelect" 
        aria-label="Select knowledge space for questions (Sélectionner l'espace de connaissances)">
    <!-- options -->
</select>

<input type="text" 
       id="messageInput" 
       aria-label="Type your question here (Écrivez votre question ici)"
       aria-required="true">

<button id="sendButton" 
        aria-label="Send message (Envoyer le message)">
    📤 Send / Envoyer
</button>

<button id="langToggle" 
        aria-label="Toggle language between English and French (Basculer entre anglais et français)"
        aria-pressed="false">
    🌐 EN
</button>
```

**Validation:**
1. Run WCAG audit: `npm install -g pa11y; pa11y http://localhost:8080/`
2. Check color contrast: All ratios ≥ 4.5:1 (AA level)
3. Test keyboard navigation: Tab through all controls
4. Test screen reader: Use NVDA/JAWS to verify ARIA labels

**Success Criteria:**
- ✅ No mock data references in code
- ✅ Health checks run every 30s, logged to console
- ✅ All colors use GC Design System tokens
- ✅ WCAG 2.2 AA compliance ≥ 90% (pa11y score)
- ✅ Three Concepts compliance ≥ 80% (CE: 9/10, HK: 7/10, WM: 7/10)

**Deliverables:**
- Updated `index.html` (mock data removed, health monitoring added, ARIA enhanced)
- New `gc-design-tokens.css` file
- WCAG audit report showing ≥90% compliance

---

### **Phase 3: Ingest Real Government Data** (Days 3-4, 12 hours)

**Context Engineering:**
- **Mission**: Populate Cosmos DB with actual GC content from POD-S data sources
- **Constraints**: Data must be Protected B compliant, bilingual where applicable
- **Reuses**: POD-S pipeline architecture, existing ingestion patterns

**Data Sources (Actual Availability):**

#### 3.1 Service Canada Programs ✅ COMPLETE
- **Status**: ✅ INGESTED
- **Content**: EI, CPP, OAS program information
- **Location**: Already in Cosmos DB via `seed-demo-data.ps1`
- **Documents**: Employment Insurance, Canada Pension Plan, Old Age Security
- **Languages**: EN-CA, FR-CA (bilingual)
- **Action**: ✅ No action needed

#### 3.2 Employment Act ✅ COMPLETE
- **Status**: ✅ INGESTED
- **Content**: Employment-related legislation and regulations
- **Location**: Already in Cosmos DB
- **Action**: ✅ No action needed

#### 3.3 Jurisprudence (Legal/Case Law) 🔄 PARTIAL
- **Source**: TBD (provide path to PDF repository)
- **Available**: 100 EN documents + 100 FR documents (200 total)
- **Domain**: Legal / Jurisprudence research
- **Content**: Case law, legal decisions
- **Format**: PDF files
- **Bilingual**: Yes (100 EN, 100 FR - separate files)
- **Status**: 🟡 READY TO INGEST (not yet loaded)

**Ingestion Script:**
```powershell
# File: ingest-jurisprudence.ps1 (NEW)

<#
🧩 CONTEXT_ENGINEERING:
    Mission: Ingest jurisprudence PDFs into EVA API for legal research assistant
    Constraints: Protected B data, citation accuracy critical, bilingual EN/FR
    Reuses: EVA API document upload endpoint, Azure Blob Storage
    Validates: PDF file integrity, metadata extraction, successful upload

🧹 HOUSEKEEPING:
    Creates: Knowledge space "Jurisprudence Research", document records
    Modifies: Cosmos DB spaces/documents containers, Blob Storage
    Validates: File checksums, API response codes, citation metadata
    Cleans: Temporary extraction files
    Monitors: Upload progress, error rates, processing time
#>

Param(
    [string]$SourcePath = "c:\path\to\POD-S-Juris\",
    [string]$ApiBase = "http://127.0.0.1:8000",
    [string]$ApiKey = "demo-api-key"
)

$ErrorActionPreference = "Stop"

# 1. Create Jurisprudence space
$spacePayload = @{
    name = "Jurisprudence Research Assistant / Assistant de recherche en jurisprudence"
    description = "Case law and legal decisions for CPP-D and related matters / Jurisprudence et décisions juridiques pour RPC-I"
    language = "bilingual"
    owner_id = [guid]::NewGuid().ToString()
} | ConvertTo-Json

$space = Invoke-RestMethod -Uri "$ApiBase/api/v1/spaces" -Method POST `
    -Headers @{"X-API-Key"=$ApiKey; "Content-Type"="application/json"} `
    -Body $spacePayload

$spaceId = $space.id
Write-Host "✅ Created space: $spaceId"

# 2. Upload PDFs
$pdfs = Get-ChildItem -Path $SourcePath -Filter "*.pdf" -Recurse
Write-Host "📄 Found $($pdfs.Count) PDF files"

$uploaded = 0
foreach ($pdf in $pdfs) {
    try {
        # Extract language from filename (e.g., "case-123-EN.pdf")
        $lang = if ($pdf.Name -match "-FR\.pdf$") { "fr-CA" } else { "en-CA" }
        
        # Upload document
        $form = @{
            file = Get-Item $pdf.FullName
            title = $pdf.BaseName
            language = $lang
        }
        
        Invoke-RestMethod -Uri "$ApiBase/api/v1/spaces/$spaceId/documents" `
            -Method POST -Headers @{"X-API-Key"=$ApiKey} -Form $form
        
        $uploaded++
        Write-Host "  ✅ Uploaded: $($pdf.Name) ($uploaded/$($pdfs.Count))"
        
    } catch {
        Write-Host "  ❌ Failed: $($pdf.Name) - $_" -ForegroundColor Red
    }
}

Write-Host "`n🎉 Ingestion complete: $uploaded/$($pdfs.Count) documents uploaded"
```

#### 3.4 AssistMe Knowledge Articles ✅ COMPLETE
- **Status**: ✅ INGESTED (1 XML file already loaded)
- **Source**: `knowledge_articles_r2r3_en.xml`
- **Domain**: HR / Productivity / Workplace Assistance
- **Content**: Internal assistance articles (exact count TBD)
- **Format**: XML structured data
- **Languages**: EN primary (FR coverage status unknown - needs verification)
- **Action**: ✅ Already ingested, verify bilingual coverage

**Ingestion Script:**
```powershell
# File: ingest-assistme.ps1 (NEW)

<#
🧩 CONTEXT_ENGINEERING:
    Mission: Ingest AssistMe XML articles into EVA API for productivity assistant
    Constraints: XML parsing, article metadata extraction, bilingual support
    Reuses: EVA API document upload, XML parsing libraries
    Validates: XML schema compliance, article completeness, upload success
#>

Param(
    [string]$XmlPath = "c:\path\to\knowledge_articles_r2r3_en.xml",
    [string]$ApiBase = "http://127.0.0.1:8000",
    [string]$ApiKey = "demo-api-key"
)

# Parse XML and upload articles
[xml]$xml = Get-Content $XmlPath

# Create AssistMe space
$spacePayload = @{
    name = "AssistMe Productivity Assistant / Assistant de productivité AssistMe"
    description = "Internal knowledge articles for workplace assistance / Articles de connaissances pour l'assistance au travail"
    language = "bilingual"
    owner_id = [guid]::NewGuid().ToString()
} | ConvertTo-Json

$space = Invoke-RestMethod -Uri "$ApiBase/api/v1/spaces" -Method POST `
    -Headers @{"X-API-Key"=$ApiKey; "Content-Type"="application/json"} `
    -Body $spacePayload

# Iterate articles and upload (logic similar to jurisprudence)
# ... (XML parsing and document upload)
```

#### 3.5 Canada Life Insurance Documents ✅ COMPLETE
- **Status**: ✅ INGESTED (4 documents loaded)
- **Source**: Canada Life policy documentation
- **Domain**: Benefits & Insurance
- **Content**: 4 Canada Life documents (insurance policies, benefits information)
- **Format**: Documents (format TBD)
- **Languages**: EN-CA only (no FR available)
- **Limitation**: ⚠️ Not bilingual - EN only
- **Action**: ✅ Already ingested, FR translation needed for full compliance

#### 3.6 Statistics Canada Data 🆕 PENDING
- **Status**: 🔴 NOT STARTED
- **Source**: TBD (provide Stats Canada data source)
- **Domain**: Statistical data and analysis
- **Content**: Government statistics, census data, economic indicators
- **Format**: TBD (CSV, JSON, or other structured format)
- **Languages**: EN-CA, FR-CA (Stats Canada is bilingual)
- **Action**: 🔴 To be ingested - awaiting data source location

**Ingestion Script:**
```powershell
# File: ingest-canada-life.ps1 (NEW)
# Similar structure to jurisprudence, adapted for text files
```

**Validation:**
1. Check space creation: `curl -H "X-API-Key: demo-api-key" http://127.0.0.1:8000/api/v1/spaces`
2. Verify document counts:
   - Service Canada: Already verified ✅
   - Employment Act: Already verified ✅
   - Jurisprudence: Should show 200 documents (100 EN + 100 FR)
   - AssistMe: Run `verify-assistme-bilingual.ps1` to check language coverage
   - Canada Life: Already verified ✅ (4 documents, EN only)
   - Stats Canada: Not yet ingested 🔴
3. Test RAG queries in each space with sample questions
4. Check bilingual coverage in each space

**Updated Success Criteria:**
- ✅ **Service Canada**: COMPLETE (2 spaces, bilingual EN/FR)
- ✅ **Employment Act**: COMPLETE (ingested)
- 🟡 **Jurisprudence**: READY TO INGEST (200 PDFs: 100 EN + 100 FR)
- ✅ **AssistMe**: COMPLETE (1 XML ingested, verify FR coverage)
- ✅ **Canada Life**: COMPLETE (4 documents, EN only - ⚠️ not bilingual)
- 🔴 **Stats Canada**: NOT STARTED (awaiting data source)

**Total Knowledge Spaces**: 6 (4 complete + 1 ready + 1 pending)
**Total Documents**: ~210+ (existing) + 200 (jurisprudence) + TBD (Stats Canada)

**Bilingual Compliance Status:**
- ✅ Service Canada: Fully bilingual
- ✅ Employment Act: TBD (verify language)
- ✅ Jurisprudence: Fully bilingual (100 EN + 100 FR)
- ⚠️ AssistMe: Unknown (needs verification)
- ❌ Canada Life: EN only (FR translation needed)
- ❓ Stats Canada: TBD (Stats Canada is officially bilingual)

**Deliverables:**
- 1 new ingestion script (jurisprudence with 200 PDFs)
- 1 verification script (AssistMe bilingual check)
- 1 placeholder script (Stats Canada ingestion - awaiting data)
- Data ingestion report (JSON: space, documents count, languages, bilingual status)

---

### **Phase 4: Enhance RAG Query Flow** (Day 5, 6 hours)

**Context Engineering:**
- **Mission**: Improve end-to-end RAG query experience with citations, confidence scores, bilingual responses
- **Constraints**: Response time <5s, citation accuracy, source attribution
- **Reuses**: Azure OpenAI GPT-4, Azure AI Search (if available), existing query service

**Enhancements:**

#### 4.1 Add Citation Display
```javascript
// File: chat-ui/index.html

/**
 * 🧩 CONTEXT_ENGINEERING: Display RAG Response with Citations
 * 
 * Mission: Render AI response with inline citations and source links
 * Constraints: Citations must be clickable, sources must be verifiable
 * Reuses: Markdown parsing, citation formatting patterns
 * Validates: Citation indices exist in sources array
 */
function displayResponseWithCitations(response) {
    const { answer, citations, confidence } = response;
    
    // Replace citation markers [1], [2] with clickable links
    let formattedAnswer = answer;
    if (citations && citations.length > 0) {
        citations.forEach((citation, index) => {
            const marker = `[${index + 1}]`;
            const link = `<a href="#citation-${index}" class="citation-link" 
                           aria-label="Jump to source ${index + 1}">${marker}</a>`;
            formattedAnswer = formattedAnswer.replace(marker, link);
        });
    }
    
    // Add confidence indicator
    const confidenceIcon = confidence >= 0.8 ? '✅' : confidence >= 0.5 ? '⚠️' : '❓';
    const confidenceText = `${confidenceIcon} Confidence: ${(confidence * 100).toFixed(0)}%`;
    
    // Build message HTML
    const messageHtml = `
        <div class="eva-response">
            <div class="response-content">${formattedAnswer}</div>
            <div class="response-metadata">${confidenceText}</div>
            ${renderCitations(citations)}
        </div>
    `;
    
    addMessage('eva', messageHtml, true);
}

function renderCitations(citations) {
    if (!citations || citations.length === 0) return '';
    
    const citationsList = citations.map((citation, index) => `
        <li id="citation-${index}">
            <strong>[${index + 1}]</strong> 
            ${citation.title} 
            <span class="citation-source">(${citation.source})</span>
        </li>
    `).join('');
    
    return `
        <div class="citations-section">
            <h4>📚 Sources / Sources</h4>
            <ol class="citations-list">${citationsList}</ol>
        </div>
    `;
}
```

#### 4.2 Add Suggested Follow-Up Questions
```javascript
// File: chat-ui/index.html

/**
 * 🧩 CONTEXT_ENGINEERING: Generate Contextual Follow-Up Questions
 * 
 * Mission: Suggest relevant follow-up questions based on conversation context
 * Constraints: Max 3 suggestions, bilingual, topic-relevant
 * Reuses: Space metadata, conversation history, domain patterns
 */
function generateFollowUpQuestions(spaceId, lastQuery, lastAnswer) {
    const followUps = [];
    const lang = currentLang; // 'en' or 'fr'
    
    // Example patterns (enhance with AI-generated suggestions in future)
    const patterns = {
        en: [
            `Can you provide more details about this?`,
            `What are the eligibility criteria?`,
            `Are there any recent changes to this policy?`
        ],
        fr: [
            `Pouvez-vous fournir plus de détails à ce sujet?`,
            `Quels sont les critères d'admissibilité?`,
            `Y a-t-il eu des changements récents à cette politique?`
        ]
    };
    
    // Return up to 3 contextual suggestions
    return patterns[lang].slice(0, 3);
}

function displayFollowUpQuestions(questions) {
    const questionsHtml = questions.map(q => `
        <button class="follow-up-btn" onclick="askFollowUp('${q}')">
            ${q}
        </button>
    `).join('');
    
    const followUpHtml = `
        <div class="follow-up-section">
            <p><em>Suggested questions / Questions suggérées:</em></p>
            ${questionsHtml}
        </div>
    `;
    
    // Append to last message
    const lastMessage = messagesContainer.lastElementChild;
    lastMessage.querySelector('.message-content').insertAdjacentHTML('beforeend', followUpHtml);
}

function askFollowUp(question) {
    messageInput.value = question;
    sendMessage();
}
```

#### 4.3 Add Query History Persistence
```javascript
// File: chat-ui/index.html

/**
 * 🧹 HOUSEKEEPING: Query History with LocalStorage
 * 
 * Creates: LocalStorage entry for query history (max 50 queries)
 * Validates: Storage quota, entry expiry (30 days)
 * Cleans: Removes entries older than 30 days
 * Monitors: Storage size, entry count
 */
function saveQueryToHistory(spaceId, query, timestamp) {
    try {
        const history = JSON.parse(localStorage.getItem('eva_query_history') || '[]');
        
        // Add new entry
        history.unshift({ spaceId, query, timestamp });
        
        // Keep max 50 entries
        const trimmed = history.slice(0, 50);
        
        // Remove entries older than 30 days
        const thirtyDaysAgo = Date.now() - (30 * 24 * 60 * 60 * 1000);
        const filtered = trimmed.filter(entry => entry.timestamp > thirtyDaysAgo);
        
        localStorage.setItem('eva_query_history', JSON.stringify(filtered));
        
    } catch (error) {
        console.warn('Failed to save query history:', error);
    }
}

function loadQueryHistory() {
    try {
        const history = JSON.parse(localStorage.getItem('eva_query_history') || '[]');
        console.log(`📜 Loaded ${history.length} queries from history`);
        return history;
    } catch (error) {
        console.warn('Failed to load query history:', error);
        return [];
    }
}

// Update sendMessage() to save history
async function sendMessage() {
    // ... existing code
    
    // Save to history after successful query
    saveQueryToHistory(selectedSpace, messageText, Date.now());
    
    // ... rest of function
}
```

**Validation:**
1. Test citation display: Ask question, verify citations appear with links
2. Test confidence scores: Check scores display correctly (0-100%)
3. Test follow-up questions: Verify 3 contextual suggestions appear
4. Test query history: Submit 5 queries, reload page, check history persists
5. Test bilingual: Switch language, verify all UI text updates

**Success Criteria:**
- ✅ Citations displayed with clickable source links
- ✅ Confidence scores shown for all responses
- ✅ 3 contextual follow-up questions generated
- ✅ Query history persists across sessions (max 50, 30-day expiry)
- ✅ All features work in both EN and FR

**Deliverables:**
- Enhanced `index.html` with citation display, follow-ups, history
- Updated CSS for citation styling
- Query history management with cleanup

---

### **Phase 5: Final Three Concepts Compliance Audit** (Day 6-7, 4 hours)

**Context Engineering:**
- **Mission**: Achieve 95%+ Three Concepts Pattern compliance across UI and backend
- **Constraints**: All files must have proper headers, documentation must be complete
- **Reuses**: THREE-CONCEPTS-COMPLIANCE.md checklist, audit scripts

**Audit Checklist:**

#### 5.1 Context Engineering (CE) - Target: 10/10
- [x] Mission documented in header (lines 2-107)
- [x] Constraints explicitly listed (WCAG, bilingual, GC DS)
- [x] Reuses documented (eva-api, Cosmos DB, Azure OpenAI)
- [x] Validates documented (message length, API responses)
- [ ] JSDoc added to ALL functions (currently 4/20)
- [ ] Input validation enhanced (check space selection before query)
- [ ] Error messages bilingual (currently EN-only in some places)
- [ ] Self-check criteria documented in comments
- [ ] Pre-flight checks added (API connectivity, space availability)
- [ ] Spec alignment verified (WCAG 2.2 AA audit passed)

#### 5.2 Housekeeping (HK) - Target: 9/10
- [x] Resource cleanup on beforeunload (snowflakes, stars, timers)
- [ ] Health monitoring active (30s interval, added in Phase 2)
- [ ] Error recovery patterns (retry logic for failed queries)
- [ ] Logging comprehensive (console.log for all operations)
- [ ] Monitoring telemetry (track response times, error rates)
- [ ] Pre-flight validation (check API health before first query)
- [ ] Graceful degradation (fallback when API unavailable)
- [ ] Memory leak prevention (event listener cleanup)
- [ ] Storage quota management (check before localStorage writes)
- [ ] Connection pool health (track API request success rate)

#### 5.3 Workspace Management (WM) - Target: 9/10
- [x] File organization documented (chat-ui/ structure)
- [x] Dependencies listed (eva-api backend)
- [ ] Caching strategy implemented (LocalStorage for spaces, queries)
- [ ] Directory tree updated (.eva-cache/component-tree.txt)
- [ ] Navigation shortcuts (keyboard shortcuts for space selection)
- [ ] Shared utilities extracted (formatTime, translation helpers)
- [ ] Import paths documented (API_BASE, API_KEY constants)
- [ ] Performance monitoring (track render times)
- [ ] Asset optimization (minify CSS/JS for production)
- [ ] Documentation complete (README with setup instructions)

**Compliance Script:**
```powershell
# File: audit-three-concepts-compliance.ps1 (NEW)

<#
🧩 CONTEXT_ENGINEERING:
    Mission: Audit Three Concepts Pattern compliance across chat-ui
    Constraints: Must score 95%+ overall (CE: 10/10, HK: 9/10, WM: 9/10)
    Reuses: THREE-CONCEPTS-COMPLIANCE.md checklist
    Validates: All criteria met, documentation complete
#>

Write-Host "`n🔍 EVA i11y Demo - Three Concepts Compliance Audit`n" -ForegroundColor Cyan

# Check CE compliance
$ceChecks = @(
    @{ Name="Mission documented"; File="index.html"; Pattern="Mission:" }
    @{ Name="Constraints listed"; File="index.html"; Pattern="Constraints:" }
    @{ Name="Reuses documented"; File="index.html"; Pattern="Reuses:" }
    @{ Name="Validates documented"; File="index.html"; Pattern="Validates:" }
    @{ Name="JSDoc on all functions"; File="index.html"; Pattern="/\*\* \* 🧩 CONTEXT_ENGINEERING:" }
    # ... more checks
)

$ceScore = 0
foreach ($check in $ceChecks) {
    $found = Select-String -Path $check.File -Pattern $check.Pattern -Quiet
    if ($found) {
        Write-Host "  ✅ $($check.Name)" -ForegroundColor Green
        $ceScore++
    } else {
        Write-Host "  ❌ $($check.Name)" -ForegroundColor Red
    }
}

Write-Host "`n📊 Context Engineering: $ceScore/$($ceChecks.Count) ($([math]::Round($ceScore/$ceChecks.Count*100,0))%)`n"

# Check HK compliance (similar)
# Check WM compliance (similar)

# Overall score
$totalScore = $ceScore + $hkScore + $wmScore
$totalChecks = $ceChecks.Count + $hkChecks.Count + $wmChecks.Count
$overallPct = [math]::Round($totalScore/$totalChecks*100, 0)

Write-Host "`n🎯 Overall Compliance: $overallPct% ($totalScore/$totalChecks)`n" -ForegroundColor $(
    if ($overallPct -ge 95) { "Green" } elseif ($overallPct -ge 80) { "Yellow" } else { "Red" }
)

if ($overallPct -lt 95) {
    Write-Host "⚠️ Target not met. Review checklist and address failing items.`n" -ForegroundColor Yellow
} else {
    Write-Host "🎉 Three Concepts Pattern compliance achieved!`n" -ForegroundColor Green
}
```

**Validation:**
1. Run compliance audit: `.\audit-three-concepts-compliance.ps1`
2. Address all failing checks
3. Re-run audit until 95%+ achieved
4. Generate compliance report (HTML/PDF)

**Success Criteria:**
- ✅ Context Engineering: 10/10 (100%)
- ✅ Housekeeping: 9/10 (90%)
- ✅ Workspace Management: 9/10 (90%)
- ✅ Overall: ≥95% compliance
- ✅ Documentation complete (README, COMPLIANCE.md updated)

**Deliverables:**
- Final `index.html` with 95%+ compliance
- Updated `THREE-CONCEPTS-COMPLIANCE.md` with final scores
- Compliance audit script (`audit-three-concepts-compliance.ps1`)
- Executive summary report (DEMO-TRANSFORMATION-COMPLETE.md)

---

## 📦 CURRENT DATA INVENTORY & INGESTION STATUS

### **✅ COMPLETED (Already Ingested)**

#### 1. Service Canada Programs
- **Status**: ✅ INGESTED
- **Documents**: Employment Insurance (EI), Canada Pension Plan (CPP), Old Age Security (OAS)
- **Languages**: EN-CA, FR-CA (fully bilingual)
- **Space Count**: 2 (bilingual spaces)
- **Action**: None required

#### 2. Employment Act
- **Status**: ✅ INGESTED
- **Content**: Employment-related legislation
- **Languages**: TBD (verify EN/FR coverage)
- **Action**: Verify bilingual status with API query

#### 3. AssistMe Knowledge Articles
- **Status**: ✅ INGESTED (1 XML file)
- **Content**: Workplace assistance articles
- **Languages**: Primarily EN (FR coverage unknown)
- **Action**: Run `verify-assistme-bilingual.ps1` to check FR availability

#### 4. Canada Life Insurance
- **Status**: ✅ INGESTED (4 documents)
- **Content**: Insurance policies, benefits information
- **Languages**: ⚠️ EN-CA ONLY (no FR available)
- **Limitation**: Not bilingual - violates GC policy
- **Action**: Request FR translations or mark as EN-only pilot

---

### **🟡 READY TO INGEST (Data Available)**

#### 5. Jurisprudence / Case Law
- **Status**: 🟡 READY (200 PDFs available)
- **Location**: TBD (provide path to PDF folders)
- **Documents**: 100 EN + 100 FR = 200 total
- **Languages**: EN-CA, FR-CA (fully bilingual)
- **Script**: `ingest-jurisprudence.ps1` (included in Phase 3)
- **Action**: Run ingestion script with correct source paths

---

### **🔴 PENDING (Not Yet Available)**

#### 6. Statistics Canada Data
- **Status**: 🔴 NOT STARTED
- **Location**: TBD (awaiting data source from Marco)
- **Content**: Statistical data, census information, economic indicators
- **Languages**: EN-CA, FR-CA (Stats Canada is officially bilingual)
- **Format**: TBD (likely CSV, JSON, or structured data)
- **Action**: Provide data source location to create ingestion script

---

### **📊 CURRENT TOTALS**

| Knowledge Space | Status | Documents | EN | FR | Bilingual? |
|----------------|--------|-----------|----|----|------------|
| Service Canada Programs | ✅ Complete | ~10 | ✅ | ✅ | ✅ YES |
| Employment Act | ✅ Complete | ~5 | ✅ | ❓ | ❓ TBD |
| AssistMe | ✅ Complete | TBD | ✅ | ❓ | ❓ TBD |
| Canada Life | ✅ Complete | 4 | ✅ | ❌ | ❌ NO |
| Jurisprudence | 🟡 Ready | 200 | 100 | 100 | ✅ YES |
| Stats Canada | 🔴 Pending | 0 | - | - | ❓ TBD |
| **TOTAL** | **4 of 6** | **~219+** | **~119+** | **~100+** | **3 YES, 1 NO, 2 TBD** |

---

### **⚠️ BILINGUAL COMPLIANCE RISKS**

1. **Canada Life (4 docs)**: EN only - violates GC bilingual policy
   - **Mitigation**: Mark as EN-only pilot OR request FR translations
   
2. **AssistMe (1 XML)**: Unknown FR coverage - needs verification
   - **Mitigation**: Run `verify-assistme-bilingual.ps1` script
   
3. **Employment Act**: Unknown FR coverage - needs verification
   - **Mitigation**: Query API to check language distribution

---

### **🚀 RECOMMENDED INGESTION ORDER**

**Phase 3A: Immediate (Day 3, 4 hours)**
1. ✅ Verify existing spaces (Service Canada, Employment Act, AssistMe, Canada Life)
2. 🔍 Run bilingual verification on AssistMe and Employment Act
3. 📋 Document bilingual gaps (Canada Life EN-only)

**Phase 3B: Jurisprudence Ingestion (Day 3, 4 hours)**
4. 📄 Run `ingest-jurisprudence.ps1` (200 PDFs: 100 EN + 100 FR)
5. ✅ Verify all 200 documents uploaded successfully
6. 🧪 Test RAG queries in jurisprudence space

**Phase 3C: Stats Canada (Day 4, 4 hours - when data available)**
7. 🔴 Awaiting data source location from Marco
8. 📝 Create `ingest-stats-canada.ps1` script once source provided
9. 📊 Ingest Stats Canada data (bilingual EN/FR)

**Total Phase 3 Duration**: 8-12 hours (depends on Stats Canada data availability)

---

## 🎯 SUCCESS CRITERIA SUMMARY

### Technical Requirements
- ✅ Cosmos DB cross-partition query working (list_spaces returns data)
- ✅ No mock/demo data in production code
- ✅ Real Government of Canada data ingested (5 spaces, 2000+ documents)
- ✅ RAG query flow complete with citations and confidence scores
- ✅ Bilingual support (EN-CA, FR-CA) throughout
- ✅ WCAG 2.2 AA compliance ≥90%
- ✅ GC Design System tokens used (no hardcoded colors)

### Three Concepts Pattern
- ✅ Context Engineering: 10/10 (100%)
- ✅ Housekeeping: 9/10 (90%)
- ✅ Workspace Management: 9/10 (90%)
- ✅ Overall Compliance: ≥95%

### User Experience
- ✅ Spaces load in <1s (no "No Knowledge Spaces Found")
- ✅ Queries respond in <5s with citations
- ✅ Health monitoring active (30s intervals)
- ✅ Query history persists across sessions
- ✅ Follow-up questions suggested
- ✅ Keyboard navigation working
- ✅ Screen reader compatible

### Business Value
- ✅ Executive-ready demo for CIO Sandbox Initiative
- ✅ Reference implementation for GC department pilots
- ✅ Real data sources prove production readiness
- ✅ Bilingual accessibility showcases compliance
- ✅ Template for future EVA Domain Assistant instances

---

## 📅 EXECUTION TIMELINE

| Phase | Duration | Dependencies | Risk | Notes |
|-------|----------|--------------|------|-------|
| **Phase 1**: Fix Cosmos DB Query | 4 hours | None (CRITICAL BLOCKER) | 🔴 HIGH | Must complete first |
| **Phase 2**: Remove Mock Data | 6 hours | Phase 1 complete | 🟡 MEDIUM | UI enhancements |
| **Phase 3A**: Verify Existing Data | 4 hours | Phase 1 complete | 🟢 LOW | Check 4 ingested spaces |
| **Phase 3B**: Ingest Jurisprudence | 4 hours | Phase 3A complete, PDF paths provided | 🟡 MEDIUM | 200 PDFs (100 EN + 100 FR) |
| **Phase 3C**: Ingest Stats Canada | 4 hours | Data source provided by Marco | 🔴 HIGH | ⚠️ BLOCKED - awaiting data |
| **Phase 4**: Enhance RAG Flow | 6 hours | Phase 3A-B complete | 🟢 LOW | Citations, history, follow-ups |
| **Phase 5**: Compliance Audit | 4 hours | Phases 2-4 complete | 🟢 LOW | Three Concepts 95%+ |
| **TOTAL** | **32 hours** (~5-7 days) | - | - | Phase 3C optional if data unavailable |

**Critical Path**: Phase 1 (Cosmos DB fix) blocks all other work. Must complete first.

---

## 🚀 NEXT STEPS

1. **Approve this plan** - Review scope, timeline, and deliverables
2. **Execute Phase 1** - Fix Cosmos DB query (CRITICAL BLOCKER)
3. **Validate Phase 1** - Confirm spaces load in UI before proceeding
4. **Parallel execution** - Phases 2-3 can run concurrently once Phase 1 completes
5. **Final review** - Phase 5 compliance audit and executive demo

---

## 📚 REFERENCES

- **Three Concepts Pattern**: `eva-orchestrator/docs/THREE-CONCEPTS-QUICK-START.md`
- **POD-S Architecture**: `eva-orchestrator/docs/POD-S-PIPELINE-ARCHITECTURE.md`
- **GC Design System**: https://design.canada.ca/
- **WCAG 2.2**: https://www.w3.org/WAI/WCAG22/quickref/
- **EVA API Specification**: `eva-api/docs/SPECIFICATION.md`
- **Current Compliance**: `eva-api/chat-ui/THREE-CONCEPTS-COMPLIANCE.md`

---

**Status**: ✅ Ready to Execute  
**Owner**: P04-LIB + P15-DVM (POD-F)  
**Priority**: HIGH (CIO Sandbox Initiative)  
**Risk**: MEDIUM (Phase 1 critical, Phases 2-5 low-risk)
