# OpenAlgo - GitHub Copilot Knowledge Base

> **Purpose**: This document provides GitHub Copilot with the essential knowledge to understand, debug, and extend the OpenAlgo trading platform.

## Project Overview

**OpenAlgo** is a Flask-based algorithmic trading platform providing a unified API interface for 25+ Indian stock brokers. It supports REST APIs, WebSocket streaming, Python strategy hosting, and real-time trading through a modern web interface.

**Tech Stack**: Python 3.8+, Flask 3.0.3, Flask-RESTX, SQLAlchemy 2.0+, Flask-SocketIO, ZeroMQ, TailwindCSS + DaisyUI

**Key Capabilities**:
- Unified trading API across multiple brokers
- Real-time WebSocket market data streaming
- Python strategy hosting with process isolation
- Sandbox mode for risk-free testing
- Telegram bot integration
- Modern responsive UI with dark/light themes

---

## Architecture & Design Patterns

### Application Structure

```
app.py                    # Main Flask app with SocketIO initialization
├── blueprints/          # Flask blueprints (auth, orders, dashboard, etc.)
├── restx_api/           # REST API namespaces (/api/v1/*)
├── services/            # Business logic layer (order, market data, websocket)
├── broker/              # Broker adapters (25+ brokers, plugin architecture)
├── database/            # SQLAlchemy models and DB operations
├── utils/               # Utilities (logging, session, security, etc.)
├── websocket_proxy/     # Standalone WebSocket server with ZMQ
├── sandbox/             # Analyzer mode (simulated trading)
└── extensions.py        # Flask extensions (SocketIO, CSRF, etc.)
```

### Core Design Patterns

1. **Service Layer Pattern**: Business logic in `services/` directory
   - Each service returns `Tuple[bool, Dict, int]` (success, data, status_code)
   - Example: `services/place_order_service.py`, `services/websocket_service.py`

2. **Broker Adapter Pattern**: Each broker implements standardized interface
   - Structure: `broker/<broker_name>/api/` (auth_api.py, order_api.py, data.py, funds.py)
   - Plugin loading via `utils/plugin_loader.py` and `plugin.json`

3. **Blueprint Pattern**: Modular routing with Flask blueprints
   - Each blueprint handles specific domain (auth, orders, dashboard)
   - Session validation with `@check_session_validity` decorator

4. **Factory Pattern**: Dynamic broker adapter creation
   - `websocket_proxy/broker_factory.py` - creates broker-specific WebSocket adapters

---

## Critical Modules & Symbols

### Application Entry Point

**File**: `app.py`
- `create_app()` - Flask app factory, registers blueprints, initializes extensions
- `setup_environment(app)` - Parallel DB initialization, loads broker plugins
- `check_session_expiry()` - Before-request hook for session validation
- Registers 20+ blueprints (auth_bp, orders_bp, api_v1_bp, etc.)

### Extensions & Configuration

**File**: `extensions.py`
- `socketio = SocketIO(async_mode='threading')` - Flask-SocketIO instance
- **Critical**: Uses `threading` mode (not eventlet) to prevent greenlet errors

**Files**: `cors.py`, `csp.py`, `limiter.py`
- CORS, Content Security Policy, and rate limiting configuration
- All configurable via environment variables

### Authentication & Security

**File**: `database/auth_db.py`
- `User` model - username, password (Argon2 hashed)
- `ApiKey` model - API keys with Argon2 hashing + Fernet encryption
- `AuthToken` model - Broker auth tokens (encrypted with Fernet)
- **Caching**: TTL caches for auth tokens, API keys (session-based expiry)
- `verify_api_key(api_key)` - Validates API key, returns username
- `get_auth_token(api_key)` - Gets decrypted broker auth token
- `get_broker_name(api_key)` - Gets broker name for user

**File**: `utils/session.py`
- `check_session_validity()` - Validates session expiry (3:30 AM IST default)
- `is_session_valid()` - Returns bool for session expiry check
- `revoke_user_tokens()` - Clears expired session tokens

**File**: `blueprints/auth.py`
- Routes: `/auth/login`, `/auth/logout`, `/auth/broker`, `/auth/reset-password`
- Uses `@limiter.limit()` for rate limiting on sensitive endpoints

### REST API Layer

**File**: `restx_api/__init__.py`
- `api_v1_bp = Blueprint('api_v1', __name__, url_prefix='/api/v1')`
- 30+ namespaces registered (placeorder, quotes, funds, orderbook, etc.)
- **CSRF Exempt**: API endpoints exempt from CSRF (use API key auth)

**Common API Pattern**:
```python
# All API endpoints follow this pattern:
@api.route('/')
class ResourceName(Resource):
    @api.doc(...)
    @api.expect(...)
    def post(self):
        # 1. Validate API key
        api_key = request.headers.get('X-API-KEY')
        if not verify_api_key(api_key):
            return {'status': 'error', 'message': 'Invalid API key'}, 401
        
        # 2. Call service layer
        success, response, status = service_function(api_key, data)
        
        # 3. Return standardized response
        return response, status
```

**Key Services**:
- `services/place_order_service.py` - `execute_order(data, api_key)`
- `services/place_smart_order_service.py` - Smart orders with SL/Target
- `services/basket_order_service.py` - Multi-order execution
- `services/quotes_service.py` - Real-time market quotes
- `services/websocket_service.py` - WebSocket subscription management

### WebSocket Architecture

**File**: `websocket_proxy/server.py`
- Standalone WebSocket server (port 8765 default)
- Handles client authentication via API key
- Routes market data from broker adapters to clients

**File**: `websocket_proxy/base_adapter.py`
- `BaseWebSocketAdapter` - Abstract base class for broker adapters
- Publishes to ZMQ, proxy server subscribes and routes to clients
- Methods: `connect()`, `disconnect()`, `subscribe()`, `unsubscribe()`

**File**: `services/websocket_service.py`
- `get_websocket_status(username)` - Connection status
- `subscribe_to_symbols(username, broker, symbols, mode)` - Subscribe to market data
- `unsubscribe_from_symbols()`, `unsubscribe_all()` - Unsubscribe operations
- Returns: `Tuple[bool, Dict[str, Any], int]`

**File**: `services/market_data_service.py`
- `MarketDataService` - Singleton for caching market data
- Methods: `get_ltp()`, `get_quote()`, `get_market_depth()`
- Thread-safe caching with cleanup loop

**File**: `blueprints/websocket_example.py`
- Routes: `/api/websocket/status`, `/api/websocket/subscribe`, etc.
- Socket.IO events: `connect`, `subscribe`, `unsubscribe`, `get_ltp`
- Namespace: `/market`

### Database Layer

**Pattern**: All DB modules follow similar structure:
```python
# Example: database/auth_db.py
engine = create_engine(DATABASE_URL, poolclass=NullPool for SQLite)
db_session = scoped_session(sessionmaker(bind=engine))
Base = declarative_base()

class ModelName(Base):
    __tablename__ = 'table_name'
    # columns...

def init_db():
    Base.metadata.create_all(bind=engine)
```

**Key Models**:
- `database/auth_db.py` - User, ApiKey, AuthToken, BrokerSettings
- `database/user_db.py` - UserSettings, MasterSettings
- `database/symbol.py` - MasterContract (symbol mappings)
- `database/strategy_db.py` - ChartinkStrategy, StrategyExecution
- `database/sandbox_db.py` - SandboxOrder, SandboxPosition (analyzer mode)
- `database/telegram_db.py` - TelegramBotConfig, TelegramUser

**Database URLs**: Environment variables
- `DATABASE_URL` - Main database (sqlite:///db/openalgo.db)
- `LATENCY_DATABASE_URL` - Latency monitoring
- `ANALYZER_DATABASE_URL` - Sandbox/analyzer mode

### Logging System

**File**: `utils/logging.py`
- `get_logger(__name__)` - Returns configured logger
- `ColoredFormatter` - Colorama-based colored console output
- `SensitiveDataFilter` - Redacts API keys, tokens, passwords from logs
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- File rotation: `TimedRotatingFileHandler` (daily rotation)

**Usage**:
```python
from utils.logging import get_logger
logger = get_logger(__name__)
logger.info("Message")
logger.error("Error message")
```

### Blueprint Patterns

**File**: `blueprints/orders.py`
- Routes: `/orderbook`, `/tradebook`, `/positions`, `/holdings`
- `/close_position`, `/close_all_positions`, `/cancel_all_orders`
- All protected with `@check_session_validity` decorator

**File**: `blueprints/dashboard.py`
- Route: `/dashboard` - Main trading dashboard
- Session validation, broker token verification

**File**: `blueprints/analyzer.py`
- Routes: `/analyzer/`, `/analyzer/stats`, `/analyzer/requests`
- Sandbox mode UI for risk-free testing

**Common Blueprint Structure**:
```python
from flask import Blueprint, render_template, session, jsonify
from utils.session import check_session_validity

bp_name = Blueprint('name', __name__, url_prefix='/prefix')

@bp_name.route('/path')
@check_session_validity
def route_function():
    username = session.get('user')
    # logic...
    return render_template('template.html', data=data)
```

### Utility Modules

**File**: `utils/session.py`
- `get_session_expiry_time()` - Calculates time until 3:30 AM IST
- `check_session_validity` - Decorator for session validation

**File**: `utils/plugin_loader.py`
- `load_broker_auth_functions()` - Dynamically loads broker plugins
- Reads `broker/*/plugin.json` for broker metadata

**File**: `utils/config.py`
- Environment variable validation and defaults

**File**: `utils/httpx_client.py`
- Reusable httpx client with connection pooling

**File**: `utils/security_middleware.py`
- Security headers, CORS, CSP enforcement

---

## Environment Variables

**Critical Variables**:
```env
# Application
APP_KEY = "secret-key"                      # Flask secret key
HOST_SERVER = "http://127.0.0.1:5000"      # Server URL
DATABASE_URL = "sqlite:///db/openalgo.db"  # Main database

# Security
API_KEY_PEPPER = "change-in-production"    # Pepper for API key hashing
CSRF_ENABLED = "TRUE"                      # Enable CSRF protection
SESSION_EXPIRY_TIME = "03:00"              # Daily session expiry (IST)

# Rate Limiting
API_RATE_LIMIT = "10 per second"
ORDER_RATE_LIMIT = "10 per second"
LOGIN_RATE_LIMIT_MIN = "5 per minute"

# WebSocket
WEBSOCKET_URL = "ws://localhost:8765"      # WebSocket server URL
WEBSOCKET_HOST = "127.0.0.1"
WEBSOCKET_PORT = "8765"

# Flask Settings
FLASK_HOST_IP = "127.0.0.1"
FLASK_PORT = "5000"
FLASK_DEBUG = "False"
```

**Loading**: Use `utils/env_check.py::load_and_check_env_variables()` to validate

---

## Common Workflows & Patterns

### Adding a New REST API Endpoint

1. **Create service function** in `services/`:
   ```python
   # services/new_feature_service.py
   def execute_new_feature(api_key: str, data: dict) -> Tuple[bool, Dict, int]:
       try:
           # Get broker
           broker = get_broker_name(api_key)
           # Get auth token
           auth_token = get_auth_token(api_key)
           # Call broker API
           api_module = importlib.import_module(f'broker.{broker}.api.order_api')
           result = api_module.new_feature_function(auth_token, data)
           return True, result, 200
       except Exception as e:
           return False, {'status': 'error', 'message': str(e)}, 500
   ```

2. **Create API namespace** in `restx_api/`:
   ```python
   # restx_api/new_feature.py
   from flask_restx import Namespace, Resource
   api = Namespace('newfeature', description='New feature operations')
   
   @api.route('/')
   class NewFeature(Resource):
       def post(self):
           api_key = request.headers.get('X-API-KEY')
           # validate and call service...
   ```

3. **Register namespace** in `restx_api/__init__.py`:
   ```python
   from .new_feature import api as new_feature_ns
   api.add_namespace(new_feature_ns, path='/newfeature')
   ```

### Adding a New Blueprint Route

1. **Create/modify blueprint** in `blueprints/`:
   ```python
   # blueprints/new_blueprint.py
   from flask import Blueprint
   new_bp = Blueprint('new', __name__, url_prefix='/new')
   
   @new_bp.route('/path')
   @check_session_validity
   def route_handler():
       # logic...
   ```

2. **Register blueprint** in `app.py`:
   ```python
   from blueprints.new_blueprint import new_bp
   app.register_blueprint(new_bp)
   ```

### Implementing Broker Adapter

**Structure**: Each broker must have:
```
broker/<broker_name>/
├── plugin.json                    # Broker metadata
├── api/
│   ├── auth_api.py               # authenticate(data) -> auth_token
│   ├── order_api.py              # place_order, modify_order, cancel_order
│   ├── data.py                   # get_quotes, get_history, get_depth
│   └── funds.py                  # get_margin, get_funds
├── mapping/
│   └── transform_data.py         # Symbol mapping broker <-> OpenAlgo
└── streaming/                     # Optional WebSocket adapter
    └── broker_adapter.py         # Extends BaseWebSocketAdapter
```

**Key Functions**:
- `authenticate(data)` - Returns `{'status': 'success', 'access_token': '...'}`
- `place_order(auth_token, order_data)` - Standardized order placement
- `get_order_book(auth_token)` - Returns list of orders
- All functions return standardized dict with `'status'` key

### Adding WebSocket Support

1. **Create broker adapter** extending `BaseWebSocketAdapter`:
   ```python
   # broker/<broker>/streaming/broker_adapter.py
   from websocket_proxy.base_adapter import BaseWebSocketAdapter
   
   class BrokerAdapter(BaseWebSocketAdapter):
       def connect(self):
           # Establish WebSocket connection
       
       def subscribe(self, symbols, mode):
           # Subscribe to symbols
       
       def _on_message(self, message):
           # Process incoming data, publish to ZMQ
           self.publish_market_data(processed_data)
   ```

2. **Register in factory** (`websocket_proxy/broker_factory.py`):
   ```python
   def create_broker_adapter(broker_name, ...):
       if broker_name == 'newbroker':
           from broker.newbroker.streaming.broker_adapter import BrokerAdapter
           return BrokerAdapter(...)
   ```

### Session Management Pattern

**All protected routes**:
```python
from utils.session import check_session_validity

@blueprint.route('/path')
@check_session_validity
def protected_route():
    username = session.get('user')  # Available after decorator
    # Session automatically validated
```

**Session data**:
- `session['user']` - Username
- `session['logged_in']` - Boolean
- Expires at 3:30 AM IST daily (configurable)

---

## Error Handling & Debugging

### Standard Error Response Format

```python
{
    'status': 'error',
    'message': 'Human-readable error message',
    'code': 'ERROR_CODE',  # Optional
    'data': {}             # Optional additional context
}
```

### Common Error Patterns

1. **API Key Validation**:
   ```python
   if not verify_api_key(api_key):
       return {'status': 'error', 'message': 'Invalid API key'}, 401
   ```

2. **Session Validation**:
   ```python
   if not session.get('logged_in'):
       return redirect('/auth/login')
   ```

3. **Broker API Errors**:
   ```python
   try:
       result = broker_function()
   except Exception as e:
       logger.error(f"Broker error: {e}")
       return {'status': 'error', 'message': str(e)}, 500
   ```

### Debugging Tips

1. **Check logs**: `log/openalgo.log` (with color codes filtered)
2. **Database inspection**: SQLite browser for `db/openalgo.db`
3. **API testing**: Use Analyzer mode (`/analyzer/`) for dry-run testing
4. **WebSocket debugging**: Check `websocket_proxy/server.py` logs
5. **Session issues**: Check `utils/session.py` expiry logic

### Common Issues & Solutions

**Issue**: Session expires unexpectedly
- **Check**: `SESSION_EXPIRY_TIME` in .env (default 03:00 IST)
- **Fix**: Adjust expiry time or check timezone settings

**Issue**: WebSocket not connecting
- **Check**: `WEBSOCKET_URL` matches server port
- **Check**: WebSocket server started (port 8765)
- **Fix**: Verify broker adapter is registered in factory

**Issue**: Broker API errors
- **Check**: Auth token validity in `database/auth_db.py::AuthToken`
- **Check**: Broker credentials in environment variables
- **Fix**: Re-authenticate via `/auth/broker`

**Issue**: CSRF token errors
- **Check**: `CSRF_ENABLED` in .env
- **Check**: Template includes `{{ csrf_token() }}`
- **Fix**: Exempt API endpoints with `csrf.exempt(blueprint)`

**Issue**: Rate limit exceeded
- **Check**: `*_RATE_LIMIT` variables in .env
- **Fix**: Adjust limits or implement backoff in client

---

## Testing & Development

### Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your settings

# Initialize database
python -c "from app import app, setup_environment; setup_environment(app)"

# Run Flask development server
python app.py
# Or with gunicorn (production)
gunicorn -b 0.0.0.0:5000 -w 4 app:app

# Run WebSocket server separately (if not Docker)
python -m websocket_proxy.server
```

### Testing Endpoints

**REST API**:
```bash
curl -X POST http://localhost:5000/api/v1/placeorder \
  -H "X-API-KEY: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"symbol":"RELIANCE","exchange":"NSE","action":"BUY",...}'
```

**WebSocket**:
- Use `/websocket/test` route for browser-based testing
- Check `templates/websocket/test_market_data.html` for examples

---

## Security Considerations

1. **API Keys**: Never log or expose API keys (filtered by `SensitiveDataFilter`)
2. **CSRF Protection**: Enabled by default for all non-API routes
3. **Session Security**: 
   - HttpOnly cookies
   - Secure flag for HTTPS
   - SameSite=Lax
4. **Password Storage**: Argon2 with pepper (configurable `API_KEY_PEPPER`)
5. **Token Encryption**: Fernet encryption for broker auth tokens
6. **Rate Limiting**: Configurable per endpoint
7. **Input Validation**: All API inputs validated via Flask-RESTX schemas

---

## Performance Optimization

1. **Caching**: TTL caches for auth tokens, API keys (session-based expiry)
2. **Connection Pooling**: 
   - SQLAlchemy pool (50 base, 100 overflow)
   - httpx client with keep-alive
3. **Async Processing**: WebSocket via threading mode (not eventlet)
4. **Database**: Use PostgreSQL for production (better concurrency than SQLite)
5. **Logging**: Minimize DEBUG logs in production
6. **Static Files**: Serve via nginx in production

---

## Quick Reference

### Import Patterns

```python
# Logging
from utils.logging import get_logger
logger = get_logger(__name__)

# Session
from utils.session import check_session_validity, is_session_valid

# Auth
from database.auth_db import verify_api_key, get_auth_token, get_broker_name

# Flask
from flask import Blueprint, render_template, session, jsonify, request

# Service pattern
from services.some_service import execute_function
success, response, status_code = execute_function(api_key, data)
```

### Database Session Pattern

```python
from database.auth_db import db_session  # or relevant db module

try:
    # Query
    result = db_session.query(Model).filter_by(field=value).first()
    # Commit if modifying
    db_session.commit()
except Exception as e:
    db_session.rollback()
    logger.error(f"Database error: {e}")
finally:
    db_session.remove()  # Important: always cleanup
```

### Broker Function Call Pattern

```python
import importlib

# Get broker module dynamically
broker = get_broker_name(api_key)
auth_token = get_auth_token(api_key)

# Import broker module
module = importlib.import_module(f'broker.{broker}.api.order_api')

# Call function
result = module.place_order(auth_token, order_data)
```

---

## Additional Resources

- **Design Docs**: `/design/` directory - comprehensive architecture documentation
- **API Documentation**: Available at `/api/v1/` when Flask-RESTX running
- **WebSocket Protocol**: `websocket_proxy/README.md`

---

**Last Updated**: November 1, 2025  
**Maintainer**: OpenAlgo Core Team  
**License**: AGPL V3.0
