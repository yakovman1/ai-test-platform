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

Update every placeholder value before deployment:

- `APP_DOMAIN` must be the public domain that points to the VPS.
- `LETSENCRYPT_EMAIL` should be an email address used for certificate notices.
- `POSTGRES_DB`, `POSTGRES_USER`, and `POSTGRES_PASSWORD` configure the database container.
- `DATABASE_URL` must use the Compose service host `postgres`, for example `postgresql+psycopg://USER:PASSWORD@postgres:5432/DB`.
- `JWT_SECRET`, `INITIAL_USER_PASSWORD`, and `NVIDIA_API_KEY` must be replaced with real private values.
- `BACKEND_CORS_ORIGINS` should include the public HTTPS origin, for example `https://ai.example.com`.

Docker Compose automatically reads `.env` for variable substitution in `docker-compose.yml`. The backend service also receives `.env` through `env_file` when the file is present, while Caddy receives the domain and Let's Encrypt email through its container environment.

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

## Postgres Backup

Create a timestamped database backup from the running Postgres container:

```bash
mkdir -p backups
docker compose exec postgres sh -c 'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"' > "backups/postgres-$(date +%Y%m%d-%H%M%S).sql"
```

Copy backups off the VPS regularly. The Postgres data volume keeps live data, but it is not a substitute for external backups.

## Postgres Restore

Stop application traffic before restoring when possible:

```bash
docker compose stop backend
```

Restore a SQL backup into the running Postgres container:

```bash
docker compose exec -T postgres sh -c 'psql -U "$POSTGRES_USER" "$POSTGRES_DB"' < backups/postgres-YYYYMMDD-HHMMSS.sql
```

Start the backend again:

```bash
docker compose up -d backend
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
