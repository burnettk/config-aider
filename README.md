# Config Aider (ca)

The `ca` command is a helper utility for running [Aider](https://aider.chat) with your favorite configurations.

## Install

`curl -sSf https://raw.githubusercontent.com/burnettk/config-aider/main/install.sh | bash`

Or see [install docs](doc/install.md) if you like safety.

## Quick Start

1. First initialize the config directory with example configurations:
```bash
ca --init
```

2. Copy your favorite configuration files into the config directory (~/.config/config-aider/). For example, if you have a configuration file called sota.yml:
```bash
cp sota.yml ~/.config/config-aider/
```

3. Create an alias for your configuration. For example, to create an alias 's' for 'sota':
```bash
ca --alias s sota
```

4. Run aider using your alias:
```bash
ca s file1.py file2.py
```

## Basic Usage

Run Aider with a specific configuration alias:

```bash
ca <alias> [files...]
```

Common commands:

- `ca --init` - Create example configurations. Start here.
- `ca --list` - List available configurations
- `ca --alias <new-alias> <config-name>` - Create a new alias for a configuration
- `ca <alias> file1.py file2.py` - Run Aider with specified config alias and files

## Configuration Management

Configurations are stored in `~/.config/config-aider/`. You can:

- Add your own `.yml` configuration files
- Create aliases in `aliases.txt`
- Use the sample configurations as templates

For all configuration options, see the [Aider documentation](https://github.com/Aider-AI/aider/blob/main/aider/website/assets/sample.aider.conf.yml).
These are simply aider configuration files that you can pass to aider with the `--config` flag, which is exactly with `ca` does.
