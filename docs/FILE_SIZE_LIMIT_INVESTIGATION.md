# File Size Limit Investigation: 100 MB Maximum

## Executive Summary

**Question**: Is there a technical limitation requiring the 100 MB file size limit on ingestion?

**Answer**: Yes and No.
- **No**: The specific value of 100 MB is arbitrary with no documented justification
- **Yes**: Legitimate technical constraints require SOME upper limit due to memory-intensive architecture

## Current State

### Where the 100 MB Limit is Defined

1. **Backend Configuration** (`backend/app/config.py:57`)
   - Defined: `MAX_UPLOAD_SIZE_MB: int = 100`
   - **Critical Issue**: Never enforced server-side

2. **Frontend** (`frontend/src/components/ingestion/FileUploader.tsx:43`)
   - Hardcoded: `maxSize: 100 * 1024 * 1024`
   - **Only actual enforcement point** (client-side only, easily bypassed)

3. **Environment Template** (`.env.example:36`)
   - Default value: `MAX_UPLOAD_SIZE_MB=100`

## Technical Constraints Justifying a File Size Limit

### 1. Memory Safety (Critical) ⚠️
- **Location**: `backend/app/api/routes/ingestion.py:50`
- **Issue**: `content = await file.read()` loads entire file into RAM
- **Impact**: FastAPI worker must hold complete file in memory
- **Risk**: Multiple concurrent uploads can exhaust memory and crash the service

### 2. Parser Memory Amplification
- **Location**: `backend/app/utils/parsers.py`
- **Issue**: Parsers create 2-4x copies in memory
  - Markdown: raw text → HTML → DOM → extracted text (3-4x)
  - JSON: recursive flattening for nested structures
  - PDF/DOCX: full document loaded, then concatenated
- **Impact**: 100 MB file consumes 300-400 MB during parsing

### 3. Chunk Materialization
- **Location**: `backend/app/workers/tasks.py:70`
- **Issue**: All chunks materialized as `list[str]` in memory
- **Impact**: 100 MB file → ~222,000 chunks (at 500 chars) all in memory

### 4. Worker Starvation
- **Location**: `backend/app/workers/celery_app.py:18`
- **Issue**: `worker_prefetch_multiplier=1` (one task per worker)
- **Impact**: Large files monopolize Celery workers for extended periods

### 5. Database Stress
- **Locations**: `database/init.sql:64-66` (indexes), `init.sql:168-170` (trigger)
- **Issues**:
  - Three IVFFlat vector indexes updated on every batch
  - Per-row trigger fires for each INSERT
  - 222,000 insertions creates significant database load

### 6. External API Constraints
- **Location**: `backend/app/core/embeddings.py:54-64`
- **OpenAI API Limits**:
  - Max 8,191 tokens per input
  - Batch limit ~2,048 inputs per call
  - Rate limits (3,000-10,000 RPM)
- **Impact**: 100 MB file → 222,000 API calls = hundreds of dollars + hours of processing

### 7. Missing Server-Side Enforcement 🔴
- Backend config exists but is never checked
- No nginx `client_max_body_size` limit
- No FastAPI middleware validation
- Direct API calls bypass frontend limit

## Key Findings

### Security Gap
The backend doesn't enforce `MAX_UPLOAD_SIZE_MB` - only the client-side React component does. This means:
1. Direct API calls can bypass the limit
2. Backend could crash if fed files larger than available RAM
3. Memory exhaustion attacks are possible

### Architectural Bottleneck
The most critical constraint is **synchronous file loading**: `await file.read()` makes it impossible to process files larger than available RAM without architectural changes.

## Recommendations

### Priority 1: Critical Fixes (Security & Stability)
**Implementation Time**: 1-2 hours

1. **Add Server-Side File Size Validation**
   - File: `backend/app/api/routes/ingestion.py` (before line 50)
   - Prevents memory exhaustion via direct API calls
   ```python
   if file.size > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
       raise HTTPException(status_code=413, detail=f"File exceeds {settings.MAX_UPLOAD_SIZE_MB}MB limit")
   ```

2. **Implement Streaming File Upload**
   - File: `backend/app/api/routes/ingestion.py` (line 50)
   - Reduces memory from full file size to 8KB constant
   ```python
   CHUNK_SIZE = 8192
   with open(file_path, "wb") as f:
       while chunk := await file.read(CHUNK_SIZE):
           f.write(chunk)
   ```

3. **Document the Rationale**
   - File: `backend/app/config.py` (line 57)
   - Explain why limit exists and how to adjust it

### Priority 2: Scalability Improvements
**Implementation Time**: 1-2 days

1. **Generator-Based Chunking**
   - Files: `backend/app/utils/chunking.py`, `backend/app/workers/tasks.py`
   - Enables processing files of any size with constant memory

2. **Streaming Embedding & Insertion**
   - File: `backend/app/workers/tasks.py`
   - Pipeline: parse → chunk → embed → insert (no full materialization)

3. **OpenAI API Resilience**
   - File: `backend/app/core/embeddings.py`
   - Add retry logic with exponential backoff
   - Respect batch limits (sub-batch into 2048 groups)

### Priority 3: Full Architecture Refactor
**Implementation Time**: 1-2 weeks

1. **Streaming/Generator-Based Parsers**
2. **Database Bulk Operation Optimizations**
   - Disable triggers during bulk inserts
   - Defer index updates for large ingestions
3. **Frontend Config Synchronization**
   - Read limit from backend API instead of hardcoding

## Conclusion

The 100 MB limit is a **reasonable defensive default** but lacks:
- ✗ Server-side enforcement (only client-side)
- ✗ Documentation explaining the rationale
- ✗ Configurability tied to available resources

**To support significantly larger files**, architectural changes are required:
- Streaming at every layer (upload → parse → chunk → embed → store)
- Generator-based processing (no list materialization)
- Database bulk operation optimizations
- External API resilience (retry, batching)

## Files Involved

### Critical Files
- `backend/app/config.py` - Config definition (line 57)
- `backend/app/api/routes/ingestion.py` - Upload endpoint (line 50)
- `frontend/src/components/ingestion/FileUploader.tsx` - Only enforcement (line 43)
- `backend/app/utils/parsers.py` - Memory-intensive parsing
- `backend/app/workers/tasks.py` - Chunk processing (lines 70-116)
- `backend/app/core/embeddings.py` - OpenAI integration
- `database/init.sql` - Indexes and triggers

## Related Documentation
- Full investigation plan: `/root/.claude/plans/snug-rolling-rainbow.md`
- Architecture overview: `docs/ARCHITECTURE.md`
- API documentation: `docs/API.md`
