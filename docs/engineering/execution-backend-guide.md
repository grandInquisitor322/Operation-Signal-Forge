# Execution Backend Guide (Daytona)

- API key via DAYTONA_API_KEY (env or .env) — never commit keys
- Upload module with sandbox.fs.upload_file
- Run tests with sandbox.process.code_run
- Always daytona.delete(sandbox) in a finally block