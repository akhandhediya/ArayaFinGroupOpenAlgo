# GitHub Copilot Instructions for OpenAlgo

## Before Starting Any Task

**ALWAYS** refer to `.github/COPILOT_KNOWLEDGE.md` for:
- Architecture patterns and design principles
- Standard workflows and code patterns
- Module structure and key functions
- Error handling conventions
- Security considerations

## Code Style & Patterns

1. **Service Layer**: All business logic returns `Tuple[bool, Dict, int]`
2. **Error Responses**: Use standard format `{'status': 'error', 'message': '...'}`
3. **Session Validation**: Use `@check_session_validity` decorator for protected routes
4. **Logging**: Always use `from utils.logging import get_logger`
5. **Database**: Always call `db_session.remove()` in finally blocks

## When Adding Features

1. Check `.github/COPILOT_KNOWLEDGE.md` for relevant workflow sections
2. Follow established patterns in existing similar modules
3. Maintain consistency with project conventions
4. Add appropriate error handling and logging

## When Debugging

1. Reference common issues section in knowledge base
2. Check environment variables in `.env`
3. Review relevant module documentation in knowledge base
4. Verify session and authentication patterns

## Priority Files to Reference

- `.github/COPILOT_KNOWLEDGE.md` - Primary knowledge base
- `design/*.md` - Detailed architecture documentation
- `README.md` - Project overview and features
