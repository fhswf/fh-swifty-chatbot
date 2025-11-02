"""
Compatibility patch for cognee package.

Fixes the issue where cognee tries to use HTTP_422_UNPROCESSABLE_CONTENT
which doesn't exist in starlette.status. The correct constant is HTTP_422_UNPROCESSABLE_ENTITY.
"""
import starlette.status

# Patch the missing HTTP_422_UNPROCESSABLE_CONTENT constant
# This is a bug in cognee - it should use HTTP_422_UNPROCESSABLE_ENTITY
if not hasattr(starlette.status, 'HTTP_422_UNPROCESSABLE_CONTENT'):
    starlette.status.HTTP_422_UNPROCESSABLE_CONTENT = starlette.status.HTTP_422_UNPROCESSABLE_ENTITY

