# Deployment

This guide deploys the AI Test Platform to a VPS with Docker Compose, Caddy HTTPS, the React frontend, the FastAPI backend, and Postgres with pgvector.

## VPS Prerequisites

- A Linux VPS with a public IPv4 address.
- Docker Engine installed.
- Docker Compose plugin installed (`docker compose version` should work).
- Git installed.
- Ports `80` and `443` open in the VPS firewall and cloud firewall.
- Outbound HTTPS access from the VPS for Caddy certificates and NVIDIA API calls.

## DNS And Domain Setup

Create a DNS `A` record for the deployment domain and point it to the VPS public IP.

Example:

```bash
ai.example.com.  A  203.0.113.10
```

Wait for DNS propagation before starting Caddy. You can check the record from your workstation:

```bash
dig +short ai.example.com
```

The value must match the VPS public IP. Set the same domain in `.env` as `APP_DOMAIN`.

## Environment Setup

Clone the repository on the VPS, then create the runtime environment file:

```bash
cp .env.example .env
nano .env
```

Do this before running `docker compose up`. Compose reads `.env` for variable substitution in `docker-compose.yml`; without it, required variables such as `POSTGRES_PASSWORD` are not available and Postgres cannot initialize.

Update every placeholder value before deployment:

- `APP_DOMAIN` must be the public domain that points to the VPS.
- `LETSENCRYPT_EMAIL` should be an email address used for certificate notices.
- `POSTGRES_DB`, `POSTGRES_USER`, and `POSTGRES_PASSWORD` configure the database container.
- `DATABASE_URL` must use the Compose service host `postgres`, for example `postgresql+psycopg://USER:PASSWORD@postgres:5432/DB`.
- `JWT_SECRET`, `INITIAL_USER_PASSWORD`, and `NVIDIA_API_KEY` must be replaced with real private values.
- `UPLOAD_MAX_MB` controls both backend upload validation and Caddy's request body limit before API traffic reaches the backend.
- `BACKEND_CORS_ORIGINS` should include the public HTTPS origin, for example `https://ai.example.com`.

Docker Compose automatically reads `.env` for variable substitution in `docker-compose.yml`. The backend, Caddy, and Postgres services receive their required runtime settings from those Compose variables. The Compose file uses required-variable checks so missing `.env` values fail fast with a clear message instead of starting partially configured containers.

## First Deploy

Validate the rendered Compose configuration:

```bash
docker compose config
```

Start the stack:

```bash
docker compose up -d --build
docker compose ps
```

Check the public site after all services are running:

```bash
curl -I "https://$APP_DOMAIN"
curl "https://$APP_DOMAIN/api/health"
```

If those commands are run from a shell that has not loaded `.env`, replace `$APP_DOMAIN` with the real domain.

## Update

Pull the latest code and recreate changed containers:

```bash
git pull
docker compose up -d --build
docker compose ps
```

Review logs after an update:

```bash
docker compose logs --tail=100 caddy
docker compose logs --tail=100 backend
```

## Logs

Follow service logs:

```bash
docker compose logs -f caddy
docker compose logs -f frontend
docker compose logs -f backend
docker compose logs -f postgres
```

Check container health and restart state:

```bash
docker compose ps
```

## Backups

Back up the database and uploaded files together so document metadata and files stay in sync.

Create a timestamped database backup from the running Postgres container:

```bash
mkdir -p backups
docker compose exec postgres sh -c 'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"' > "backups/postgres-$(date +%Y%m%d-%H%M%S).sql"
```

Set the Compose project name used in Docker volume names. If you set `COMPOSE_PROJECT_NAME` in your shell, reuse that value here:

```bash
PROJECT_NAME="${COMPOSE_PROJECT_NAME:-$(basename "$PWD")}"
```

Create a timestamped archive of the `uploaded_files` volume:

```bash
docker run --rm -v "${PROJECT_NAME}_uploaded_files:/data:ro" -v "$PWD/backups:/backup" alpine sh -c 'cd /data && tar czf "/backup/uploaded-files-$(date +%Y%m%d-%H%M%S).tar.gz" .'
```

Caddy stores ACME account and certificate state in `caddy_data` and runtime config in `caddy_config`. These volumes can be backed up with the same pattern if you want faster recovery:

```bash
docker run --rm -v "${PROJECT_NAME}_caddy_data:/data:ro" -v "$PWD/backups:/backup" alpine sh -c 'cd /data && tar czf "/backup/caddy-data-$(date +%Y%m%d-%H%M%S).tar.gz" .'
docker run --rm -v "${PROJECT_NAME}_caddy_config:/data:ro" -v "$PWD/backups:/backup" alpine sh -c 'cd /data && tar czf "/backup/caddy-config-$(date +%Y%m%d-%H%M%S).tar.gz" .'
```

If Caddy volumes are lost, Caddy can reissue certificates and recreate account state as long as DNS still points to the VPS and ports `80` and `443` are reachable. Expect a short HTTPS outage during reissuance, and avoid repeated failed restarts because Let's Encrypt rate limits failed validation attempts.

Copy backups off the VPS regularly. Docker named volumes keep live data, but they are not a substitute for external backups.

## Restore

Stop application traffic before restoring when possible:

```bash
docker compose stop backend caddy
```

Restore a SQL backup into the running Postgres container:

```bash
docker compose exec -T postgres sh -c 'psql -U "$POSTGRES_USER" "$POSTGRES_DB"' < backups/postgres-YYYYMMDD-HHMMSS.sql
```

Restore uploaded files into the `uploaded_files` volume:

```bash
PROJECT_NAME="${COMPOSE_PROJECT_NAME:-$(basename "$PWD")}"
docker run --rm -v "${PROJECT_NAME}_uploaded_files:/data" -v "$PWD/backups:/backup:ro" alpine sh -c 'cd /data && tar xzf /backup/uploaded-files-YYYYMMDD-HHMMSS.tar.gz'
```

If you backed up Caddy volumes and want to restore the previous ACME state, restore them before starting Caddy:

```bash
docker run --rm -v "${PROJECT_NAME}_caddy_data:/data" -v "$PWD/backups:/backup:ro" alpine sh -c 'cd /data && tar xzf /backup/caddy-data-YYYYMMDD-HHMMSS.tar.gz'
docker run --rm -v "${PROJECT_NAME}_caddy_config:/data" -v "$PWD/backups:/backup:ro" alpine sh -c 'cd /data && tar xzf /backup/caddy-config-YYYYMMDD-HHMMSS.tar.gz'
```

Start services again:

```bash
docker compose up -d backend caddy
docker compose ps
```

## Troubleshooting

### Caddy Certificates

If HTTPS certificates are not issued:

- Confirm `APP_DOMAIN` in `.env` exactly matches the DNS name.
- Confirm the domain resolves to the VPS public IP.
- Confirm ports `80` and `443` are reachable from the internet.
- Check Caddy logs with `docker compose logs -f caddy`.
- Avoid repeated failed restarts while DNS is wrong, because Let's Encrypt rate limits failed validation attempts.

After fixing DNS or firewall issues, restart Caddy:

```bash
docker compose restart caddy
```

### Backend Cannot Reach Postgres

Check the Postgres healthcheck and backend logs:

```bash
docker compose ps postgres
docker compose logs --tail=100 postgres
docker compose logs --tail=100 backend
```

Confirm `DATABASE_URL` uses `postgres` as the host and matches the database name, user, and password in `.env`.

If Postgres logs show `Database is uninitialized and superuser password is not specified`, `.env` was missing or `POSTGRES_PASSWORD` was empty when the stack was started. Create `.env`, set `POSTGRES_PASSWORD`, and restart the stack:

```bash
cp .env.example .env
nano .env
docker compose down
docker compose up -d --build
docker compose ps
```

If the failed first start created an empty `postgres_data` volume and Postgres still refuses to initialize after `.env` is fixed, remove only the failed local database volume before starting again. Do not do this on a real deployment with data you need to keep:

```bash
docker compose down
PROJECT_NAME="${COMPOSE_PROJECT_NAME:-$(basename "$PWD")}"
docker volume rm "${PROJECT_NAME}_postgres_data"
docker compose up -d --build
```

### NVIDIA API Failures

If normal or RAG chat requests fail with NVIDIA errors:

- Confirm `NVIDIA_API_KEY` is set to a valid key in `.env`.
- Confirm `NVIDIA_EMBEDDING_MODEL` and `NVIDIA_LLM_MODEL` are available to the key.
- Confirm the VPS can make outbound HTTPS requests.
- Check backend logs for the exact upstream status and message.

```bash
docker compose logs -f backend
```

After changing NVIDIA settings, recreate the backend container:

```bash
docker compose up -d --force-recreate backend
```

