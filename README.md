# Aider Configuration Manager (ca)

The `ca` command is a helper utility for managing and running [Aider](https://aider.chat) with different configurations.

## Installation

1. Clone this repository
2. Make `config_aider.py` executable:

   ```bash
   chmod +x config_aider.py
   ```

3. Create a symlink to make it available as `ca`:

   ```bash
   ln -s $(pwd)/config_aider.py /usr/local/bin/ca # might require sudo
   ```

## Basic Usage

Run Aider with a specific configuration:

```bash
ca <alias> [files...]
```

Common commands:

- `ca --init` - Create example configurations
- `ca --list` - List available configurations
- `ca --alias <new-alias> <config>` - Create a new alias for a configuration
- `ca <alias> file1.py file2.py` - Run Aider with specified config and files

## Configuration Management

Configurations are stored in `~/.config/config-aider/`. You can:

- Add your own `.yml` configuration files
- Create aliases in `aliases.txt`
- Use the sample configurations as templates

For all configuration options, see the [Aider documentation](https://github.com/Aider-AI/aider/blob/main/aider/website/assets/sample.aider.conf.yml).
These are simply aider configuration files that you can pass to aider with the `--config` flag, which is exactly with `ca` does.
