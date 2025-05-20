# Sample Aider Configurations

This directory contains example configuration files for [Aider](https://aider.chat). These files demonstrate different model configurations and settings.

## Configuration File Format

Configuration files are normal Aider config files in aider's YAML format.
They support all options documented in the [Aider configuration reference](https://github.com/Aider-AI/aider/blob/main/aider/website/assets/sample.aider.conf.yml).

## Using These Configurations

These configurations are automatically copied to `~/.config/config-aider/` when you run `ca --init`. You can:

1. Use them as-is with their default aliases:

   - `g` for Gemini
   - `clause` for Claude 3 Sonnet
   - `d` for Deepseek Chat V3

2. Copy and modify them to create your own configurations

3. Use them as templates for new configurations with different models or settings
