# Rate Limiting Configuration

## Overview

VaultMind implements IP-based rate limiting to control costs and ensure system reliability. This protects against:
- **Cost overruns** from excessive OpenAI API calls
- **DDoS attacks** and abuse
- **Resource exhaustion** on the backend server
- **Google Calendar API quota limits**

## Implementation

### Library
- **slowapi** v0.1.9 - FastAPI-compatible rate limiting based on Flask-Limiter
- Built on top of `limits` library for flexible rate limit storage

### Strategy
- **Key Function**: `get_remote_address` - Limits based on client IP address
- **Storage**: In-memory (suitable for single-instance deployments)
- **Response**: HTTP 429 (Too Many Requests) when limit exceeded

## Rate Limits by Endpoint

| Endpoint | Rate Limit | Reason |
|----------|-----------|---------|
| `GET /health` | 100/minute | High-frequency monitoring checks |
| `POST /agent/chat` | **10/minute** | **OpenAI API cost control** |
| `POST /agent/calendar` | 20/minute | Google Calendar API quota management |
| `GET /audit/logs` | 30/minute | Prevent log scraping |

### Critical: Chat Endpoint (10 req/min)

The most restrictive limit is on `/agent/chat` because:
1. **OpenAI Costs**: Each request calls GPT-4o-mini (~$0.15 per 1M tokens)
2. **Abuse Prevention**: Stops automated bots from draining credits
3. **User Experience**: 10 requests/min = 1 request every 6 seconds (reasonable for human interaction)

## Configuration

```python
# In main.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Initialize limiter
limiter = Limiter(key_func=get_remote_address)

# Add to FastAPI app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Apply to endpoints
@app.post("/agent/chat")
@limiter.limit("10/minute")
async def chat_with_agent(request: Request, ...):
    ...
```

## Response Format

When rate limit is exceeded:

```json
{
  "error": "Rate limit exceeded: 10 per 1 minute"
}
```

HTTP Status: **429 Too Many Requests**

Headers:
```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1698765432
Retry-After: 60
```

## Frontend Integration

Add rate limit handling to your Next.js frontend:

```typescript
// In frontend API calls
try {
  const response = await fetch('/api/agent/chat', {
    method: 'POST',
    body: JSON.stringify({ message })
  });

  if (response.status === 429) {
    const retryAfter = response.headers.get('Retry-After');
    toast.error(`Rate limit exceeded. Try again in ${retryAfter} seconds.`);
    return;
  }

  const data = await response.json();
  // ... handle success
} catch (error) {
  // ... handle error
}
```

## Production Recommendations

### 1. Redis Storage (Multi-Instance Deployments)

For multiple backend instances (horizontal scaling), switch to Redis:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address
from limits.storage import RedisStorage

# Redis-backed rate limiting
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=os.getenv("REDIS_URL", "redis://localhost:6379")
)
```

### 2. User-Based Rate Limiting

Instead of IP-based, use authenticated user ID:

```python
def get_user_id(request: Request) -> str:
    """Extract user ID from JWT for per-user rate limiting"""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header:
        return get_remote_address(request)
    
    try:
        token = auth_header.split(" ")[1]
        payload = jwt.decode(token, options={"verify_signature": False})
        return payload.get("sub", get_remote_address(request))
    except:
        return get_remote_address(request)

limiter = Limiter(key_func=get_user_id)
```

### 3. Tiered Limits

Different limits for free vs paid users:

```python
@app.post("/agent/chat")
async def chat_with_agent(request: Request, user_claims: Dict = Depends(verify_jwt)):
    # Check user tier
    user_tier = user_claims.get("tier", "free")
    
    if user_tier == "free":
        await limiter.check(request, "10/minute")
    elif user_tier == "pro":
        await limiter.check(request, "100/minute")
    
    # ... process request
```

### 4. Nginx Rate Limiting (Upstream)

Add another layer at reverse proxy level:

```nginx
http {
  limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
  
  server {
    location /agent/ {
      limit_req zone=api_limit burst=20 nodelay;
      proxy_pass http://backend:8000;
    }
  }
}
```

## Monitoring

Track rate limit hits in your logs:

```python
# Add logging when limit is hit
@app.exception_handler(RateLimitExceeded)
async def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded):
    logger.warning(f"[RATE_LIMIT] IP {get_remote_address(request)} exceeded limit on {request.url.path}")
    return _rate_limit_exceeded_handler(request, exc)
```

## Testing

Test rate limits with curl:

```bash
# Hit /agent/chat 11 times rapidly
for i in {1..11}; do
  curl -X POST http://localhost:8000/agent/chat \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"message": "Test"}' \
    -w "\nStatus: %{http_code}\n"
  sleep 1
done

# Expected: First 10 succeed (200), 11th fails (429)
```

## Cost Savings Calculation

**Without rate limiting:**
- 1000 malicious requests/hour × 24 hours = 24,000 requests/day
- At $0.15 per 1M tokens, ~500 tokens per request
- Cost: 24,000 × 500 × $0.15 / 1,000,000 = **$1.80/day** = **$54/month** (just from abuse)

**With 10 req/min limit:**
- Max: 10 × 60 minutes = 600 requests/hour
- Daily abuse cost: 600 × 24 × 500 × $0.15 / 1,000,000 = **$1.08/day** = **$32.40/month**

**Savings**: 40% reduction in potential abuse costs

## Security Benefits

1. **Brute Force Protection**: Limits JWT token guessing attempts
2. **Enumeration Prevention**: Stops attackers from mapping your API
3. **Resource Protection**: Prevents memory/CPU exhaustion
4. **Fair Usage**: Ensures all users get equal access

## References

- [slowapi Documentation](https://github.com/laurents/slowapi)
- [limits Library](https://github.com/alisaifee/limits)
- [OWASP Rate Limiting](https://owasp.org/www-community/controls/Blocking_Brute_Force_Attacks)
- [FastAPI Best Practices](https://fastapi.tiangolo.com/advanced/middleware/)
