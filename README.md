# Config Aider (ca)

The `ca` command is a helper utility for running [Aider](https://aider.chat) with your favorite configurations.

## Install

`curl -sSf https://raw.githubusercontent.com/burnettk/config-aider/main/install.sh | bash`

Or see [install docs](doc/install.md) if you like safety.

## Quick Start

1. First, initialize the config directory with example configurations:
```bash
ca --init
```

2. Copy your favorite aider configuration files into `~/.config/config-aider/`. For example, if you have a configuration file called sota.yml:
```bash
cp sota.yml ~/.config/config-aider/
```

3. Create an alias for your configuration. For example, to create an alias `s` for `sota`:
```bash
ca --alias s sota
```

4. Run aider using your `s` config alias:
```bash
ca s file1.py file2.py
```

## Usage

```text
usage: config_aider.py [-h] [--alias ALIAS TARGET] [--list] [--init] [run_alias] ...

Aider configuration manager

positional arguments:
  run_alias             Configuration alias to use
  extra_args            Additional arguments to pass to aider

options:
  -h, --help            show this help message and exit
  --alias ALIAS TARGET, -a ALIAS TARGET
                        Add a new alias for a configuration
  --list, -l            List available configurations
  --init, -i            Create example configurations
```

## Configuration Management

Configurations are stored in `~/.config/config-aider/`. You can:

- Add your own `.yml` configuration files
- Create aliases in `aliases.txt`, either manually, or using `ca --alias ALIAS TARGET`
- Use the sample configurations as templates

For all configuration options, see the [Aider documentation](https://github.com/Aider-AI/aider/blob/main/aider/website/assets/sample.aider.conf.yml).
The YAML files are simply aider configuration files that you can pass to aider with the `--config` flag, which is exactly what `ca` does.
