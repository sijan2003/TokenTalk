# 🧠 DocuMind: The Ultimate Code-Level Technical Manual

This manual provides an exhaustive, code-inclusive breakdown of the **DocuMind** application. It explains exactly *what* the code is doing and *why* it was written that way.

---

## 🏗️ 1. Project Architecture

DocuMind uses a **Decoupled Architecture**:
- **Backend (FastAPI):** High-performance REST API.
- **Frontend (Vanilla JS):** Client-side interactivity.
- **AI Core (LangChain + FAISS):** The heavy lifting of text processing and context retrieval.

---

## 🐍 2. Backend: Service-Level Code Breakdown

### A. The RAG Core (`rag_service.py`)
This is the heart of the AI. We use **LCEL (LangChain Expression Language)** to build a pipeline.

```python
# The Chain Logic
rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | PROMPT
    | llm
    | StrOutputParser()
)
```
- **`retriever | format_docs`**: This piped operation first finds segments using FAISS and then concatenates them into a single block of text (string).
- **`RunnablePassthrough()`**: This simply takes the user's question and hands it over to the next step without changing it.
- **`PROMPT`**: The template that instructs the AI how to behave.
- **`llm`**: Our connection to Google Gemini Flash.
- **`StrOutputParser()`**: Ensures the final output is just a clean string, not a complex AI object.

### B. YouTube Processing (`youtube_service.py`)
We handle YouTube transcripts differently because they aren't static files.

```python
# Fixed logic for specific library versions
yt = YouTubeTranscriptApi() # 1. Instantiate class
transcript = yt.fetch(video_id, languages=['en', 'en-US', 'en-GB']) # 2. Fetch list

# Reconstructing dialogue from objects
return " ".join(getattr(item, "text", str(item)) for item in transcript)
```
- **Why `getattr`?**: The transcripts are returned as `FetchedTranscriptSnippet` objects. If we tried `item['text']`, it would crash with a "not subscriptable" error. `getattr` safely gets the `.text` attribute.

### C. Web Scraping (`webpage_service.py`)
We "clean" the web to save AI costs and improve accuracy.

```python
soup = BeautifulSoup(response.content, 'html.parser')

# Noise removal logic
for script in soup(["script", "style", "nav", "footer"]):
    script.decompose() # This deletes them from the page memory!
```
- **Decompose**: We destroy headers, footers, and scripts so the AI doesn't get confused by "Login to your account" or "Click here to buy" buttons nearby.

---

## 🗄️ 3. Database & Security

### A. Password Hashing (`security.py`)
We use **PBKDF2-SHA256**.

```python
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def get_password_hash(password: str):
    return pwd_context.hash(password)
```
- **Salting**: PBKDF2 automatically adds a unique "salt" to every password so that even two identical passwords look completely different in the database.

### B. JWT Authentication (`deps.py`)
Every protected endpoint uses this "Gatekeeper":

```python
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = decode_access_token(token) # Check if token hasn't expired
    email = payload.get("sub")
    user = db.query(User).filter(User.email == email).first()
    return user # Injects the actual User object into your function!
```

---

## 🎨 4. Frontend: The Connectivity Layer

### A. Standardized API Client (`api.js`)
We built a single `API` class to avoid repeating code.

```javascript
async request(endpoint, options = {}) {
    // Automatically adds the Token to every request!
    const token = localStorage.getItem('token');
    const headers = { ...options.headers };
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const res = await fetch(`${this.baseUrl}${endpoint}`, { ...options, headers });
    // Global Error Handling
    if (res.status === 401) window.location.href = 'index.html'; 
    return res.json();
}
```

### B. Chat Auto-Scroll (`chat.js`)
To make it feel professional, we force the window to scroll as messages arrive.

```javascript
function scrollToBottom() {
    const chatMessages = document.getElementById('chatMessages');
    chatMessages.scrollTop = chatMessages.scrollHeight;
}
```

---

## 🛠️ 5. Technical "Minute Details" Summary

| Component | Minute Detail | Why it matters? |
| :--- | :--- | :--- |
| **FAISS** | `allow_dangerous_deserialization=True` | Required to reload our locally saved AI index files. |
| **CORS** | `allow_credentials=False` | Allows the "*" wildcard so you don't get 400 errors from Chrome/Edge. |
| **Embeddings** | `all-MiniLM-L6-v2` | A 384-dimension model. Smaller and faster than OpenAI's models, perfect for local run. |
| **CSS** | `min-height: 0` on flex items | Fixes the bug where the message area pushes the input bar off-screen. |

---

## 📖 6. Final Note: Inline Documentation

Beyond this manual, I have added **comprehensive inline comments** to every source file in the project. 

### Where to Look:
- **Backend Services**: `backend/app/services/` for the deep "Why" behind the AI logic.
- **Frontend State**: `frontend/js/` for explanations on how the UI reacts to your actions.
- **Models/Auth**: `backend/app/models/` and `deps.py` for database and security rules.

**The code is now as much a learning tool as it is a working application. Happy exploring!** 🚀
