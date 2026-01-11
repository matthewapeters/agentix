# Agentix

Agentix is a CLI tool designed for interacting with large language models (LLMs) via the Ollama API. It provides features for managing prompts, sessions, and model configurations.

## Features

- List available models and their details.
- Manage system and user prompts.
- Handle session history with token-aware context trimming.
- Query the Ollama API for LLM interactions.

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/your-repo/agentix.git
   cd agentix
   ```

2. Set up the environment using `uv`:

   ```bash
   uv setup
   ```

3. Install dependencies:

   ```bash
   uv install
   ```

## Usage

Run the CLI tool with the following command:

```bash
uv run python -m src.agentix.main [OPTIONS]
```

### Options

- `--list-models`: List all available models.
- `--list-prompts`: Display all system prompts.
- `--list-sessions`: Show session history.
- `--session SESSION_NAME`: Specify a session name to continue or create.
- `--temperature VALUE`: Set the temperature for the model (e.g., 0.7).
- `--debug`: Enable debug mode for detailed logs.

### Examples

1. List all models:

   ```bash
   uv run python -m src.agentix.main --list-models
   ```

2. Query the API with a specific session:

   ```bash
   uv run python -m src.agentix.main --session my_session --temperature 0.8
   ```

3. Display available prompts:

   ```bash
   uv run python -m src.agentix.main --list-prompts
   ```

## Testing

Run the test suite with:

```bash
uv run python -m pytest
```

To check test coverage:

```bash
uv run python -m pytest --cov=src/agentix --cov-report=term-missing
```

## Contributing

1. Fork the repository.
2. Create a new branch for your feature:

   ```bash
   git checkout -b feature-name
   ```

3. Commit your changes:

   ```bash
   git commit -m "Add new feature"
   ```

4. Push to your branch:

   ```bash
   git push origin feature-name
   ```

5. Open a pull request.

## License

This project is licensed under the MIT License.
