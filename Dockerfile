FROM python:3.12-slim
LABEL org.opencontainers.image.source="https://github.com/HypeTek/hypetek-gamevault"
LABEL org.opencontainers.image.title="HypeTek Mission Control"
LABEL org.opencontainers.image.description="Self-hosted game archive and secure Windows launcher for TrueNAS"
LABEL org.opencontainers.image.version="0.2.6"
WORKDIR /app
COPY server/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY server/ ./
COPY VERSION ./VERSION
COPY windows-agent/ /app/windows-agent/
RUN groupadd --gid 568 gamevault \
    && useradd --system --uid 568 --gid 568 --no-create-home gamevault
USER 568
EXPOSE 8080
CMD ["waitress-serve", "--host=0.0.0.0", "--port=8080", "app:app"]
