"""RCAIDE-hosted assistant API package.

Startup is intentionally side-effect free; Uvicorn imports
``agent_server.app:app`` when the service is launched.
"""
