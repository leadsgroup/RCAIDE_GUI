# Minimal production image for the central API; PyQt remains on the desktop.
FROM python:3.12-slim

WORKDIR /service
COPY agent_server ./agent_server
# Install only the dependencies required by the hosted request boundary.
RUN pip install --no-cache-dir "fastapi>=0.115" "pydantic>=2.7" "uvicorn[standard]>=0.30"

# The API only needs network access, so it runs as an unprivileged user.
USER 65532:65532
EXPOSE 8000
CMD ["uvicorn", "agent_server.app:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
