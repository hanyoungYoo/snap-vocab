# snap-vocab

Self-hosted English vocabulary tool that captures expressions from LLM conversations and delivers spaced-repetition review questions via Telegram.

## Quick Start

```bash
# 1. Install Python 3.13 + uv (if not already installed)
brew install uv  # or https://docs.astral.sh/uv/

# 2. Install dependencies
uv sync

# 3. Set up environment variables
cp .env.example .env
# Fill in API_SECRET_KEY, LLM_API_KEY, and other required values

# 4. Start the database
docker-compose up -d db
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[LICENSE](LICENSE)
