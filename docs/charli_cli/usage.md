# CHARLI CLI — Usage Guide

## Commands

### `charli ask <question>`

Send a text question to CHARLI and display the response.

```bash
charli ask "What is a Raspberry Pi?"
charli ask "Explain how API keys work"
charli ask "Write a Python function that checks if a number is prime"
```

The question must be quoted if it contains spaces or special characters.

**Follow-up questions** work because the server tracks conversation history per device:

```bash
charli ask "What is recursion?"
# CHARLI explains recursion...

charli ask "Can you give me an example in Python?"
# CHARLI gives a Python example, knowing you were talking about recursion
```

The CLI device gets **10 turns** of conversation history, so CHARLI remembers a good amount of context.

**Clearing conversation history:**

```bash
# Via the API directly (no CLI command for this yet)
curl -X DELETE http://charli-server:3000/api/conversation \
  -H "X-API-Key: chk_your_key"
```

### `charli status`

Show current configuration and connection status.

```bash
charli status
```

Example output:

```
CHARLI Status

  Config: /Users/you/.charli/config.json
  Server: http://charli-server:3000
  Device: charli-cli
  API Key: chk_abc1...

✔ Tailscale: connected as macbook-pro
    Tailscale IP: 100.64.0.5
✔ Server: ok
```

Checks three things:
1. Config file loaded and values present
2. Tailscale connected (hostname + IP)
3. Server reachable (`GET /health`)

### `charli init`

Interactive setup wizard. See the [Setup Guide](setup.md) for details.

```bash
charli init
```

Safe to re-run — overwrites the existing config.

### `charli --version`

Print the version number.

### `charli --help`

Show all available commands.

## Response Format

Unlike voice devices (which get short, spoken responses), the CLI device type is configured for **detailed, markdown-formatted responses**:

- Headers and bold text
- Bullet points and numbered lists
- Fenced code blocks with language tags
- Longer explanations (up to 1024 tokens)

This makes the CLI great for:
- **Code questions** — CHARLI returns properly formatted code blocks
- **Explanations** — detailed answers with structure
- **Learning** — the educational style of CHARLI works well in text

## Tips

**Use the CLI alongside voice devices.** The server tracks conversations per device, so your CLI chat history is separate from desk hub or glasses conversations.

**Set env vars for scripts.** If you want to use CHARLI in a shell script:

```bash
export CHARLI_SERVER_URL="http://charli-server:3000"
export CHARLI_API_KEY="chk_your_key"

# Now any charli command uses these values
charli ask "What time zone is New York in?"
```

**Check status first** if something seems off:

```bash
charli status
# Shows config, Tailscale, and server health at a glance
```

## What's Next

These features are planned for future versions:

| Feature | Command | Description |
|---------|---------|-------------|
| Interactive REPL | `charli chat` | Persistent chat session with `/clear`, `/exit` |
| Voice | `charli voice` | Record mic → pipeline → play audio |
| Vision | `charli ask --image ./photo.jpg` | Send an image with your question |
| Streaming | (automatic) | SSE streaming for real-time token display |
