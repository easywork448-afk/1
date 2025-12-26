Railway deployment

1) Push this repository to GitHub (or connect your Git repository to Railway).

2) Create a new project on Railway and connect the Git repository branch.

3) Set environment variables in Railway project settings:
   - `BOT_TOKEN` — your Telegram bot token
   - `TARGET_GROUP_ID` — target group id (e.g. -1001234567890 or @yourgroup)

4) Railway will detect the `Procfile`. Ensure the service type is `Worker` and it runs the command from `Procfile`.

5) Deploy. The bot will start and run continuously on Railway.

Local testing

- To run locally, create a `.env` with `BOT_TOKEN` and `TARGET_GROUP_ID` then:

```bash
python -m venv .venv
.\.venv\Scripts\activate    # on Windows
pip install -r requirements.txt
python bot.py
```

Optional: Use the included `Dockerfile` to build and run a container locally or on a cloud host.

Notes

- Railway provides automatic restarts and 24/7 uptime depending on plan.
- Keep your `BOT_TOKEN` secret and use Railway environment variables rather than committing `.env` to the repo.
