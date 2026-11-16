# Deployment on operator-prod

Live application: https://resume-reranker.namankundra.com

The full application runs in one Docker container: FastAPI serves the compiled
React frontend and the API. The CPU embedding model is downloaded into the image
at build time, loaded before startup completes, and used offline at runtime.

The deployment directory on the host is `/opt/resume-reranker`. Runtime secrets
are in `deploy/.env` with mode `600`, outside the image. Set `DATABASE_URL` to the
Neon URL; production startup fails if it is missing.

```bash
cd /opt/resume-reranker
sudo docker compose -f deploy/compose.yaml up -d --build
sudo docker compose -f deploy/compose.yaml ps
sudo docker compose -f deploy/compose.yaml logs --tail=50 app
curl --fail http://127.0.0.1:8011/api/health
```

`deploy/compose.yaml` joins the existing `foreman-production_default` proxy network
and exposes port 8011 on loopback only. The existing Caddy container proxies
`resume-reranker.namankundra.com` to `resume-reranker:8000` and manages HTTPS.
The site block is in `deploy/Caddyfile`; merge it into the host Caddyfile, validate
the combined configuration, then reload Caddy. DNS must point the subdomain to
the host. Other applications on the proxy keep their existing routes.

The current proxy container has an older file bind mount. To reload the current
host configuration without restarting other sites, copy it into the container
and validate that copy before reloading:

```bash
sudo docker cp /home/nkundra_be23/Foreman/deploy/Caddyfile foreman-production-caddy-1:/tmp/Caddyfile.reload
sudo docker exec foreman-production-caddy-1 caddy validate --config /tmp/Caddyfile.reload --adapter caddyfile
sudo docker exec foreman-production-caddy-1 caddy reload --config /tmp/Caddyfile.reload --adapter caddyfile
```

The container runs as an unprivileged user, has a 1.5 GB memory limit and 1.5 CPU
limit, restarts automatically, and checks health every 30 seconds. Model startup
has a two-minute health-check grace period. Use synthetic data for this public
assignment demo; all visitors share the same saved-run history.

Run `python deploy/verify.py` from a checkout to verify HTTPS, frontend assets,
ten mixed PDF/DOCX uploads with real embeddings, explanation fields, partial-file
failure and database persistence. It deletes only its own synthetic test run.
The production image also passed all 36 backend tests on Linux. Installed Python
versions are recorded on the server in `deploy/requirements.installed.txt`.


See [the main README](../README.md) for local setup and architecture, and
[the matching methodology](MATCHING.md) for the scoring algorithm.
