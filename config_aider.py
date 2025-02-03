#!/usr/bin/env python

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
from typing import Dict, Optional


class ConfigManager:
    def __init__(self, config_dir: str = "~/.config/aider-profiles"):
        self.config_dir = os.path.expanduser(config_dir)
        self.config_map: Dict[str, dict] = {}
        self._ensure_config_dir()
        self._load_configs()

    def _ensure_config_dir(self) -> None:
        """Create config directory if it doesn't exist"""
        os.makedirs(self.config_dir, exist_ok=True)

    def _load_configs(self) -> None:
        """Load all JSON configuration files from the config directory"""
        for config_file in Path(self.config_dir).glob("*.json"):
            alias = config_file.stem
            try:
                with open(config_file) as f:
                    config = json.load(f)
                    # Basic validation
                    if not isinstance(config, dict) or "args" not in config:
                        print(
                            f"Warning: Skipping invalid config file {config_file} - missing 'args' dictionary"
                        )
                        continue
                    self.config_map[alias] = config
            except json.JSONDecodeError as e:
                print(f"Warning: Failed to load config file {config_file}: {e}")

    def save_config(self, alias: str, config: dict) -> None:
        """Save a new configuration"""
        config_path = os.path.join(self.config_dir, f"{alias}.json")
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
        self.config_map[alias] = config

    def get_config(self, alias: str) -> Optional[dict]:
        """Retrieve a configuration by alias"""
        config = self.config_map.get(alias)
        if config:
            # Expand any environment variables in string values
            return self._expand_env_vars(config)
        return None

    def _expand_env_vars(self, config: dict) -> dict:
        """Recursively expand environment variables in config values"""
        result = {}
        for key, value in config.items():
            if isinstance(value, str):
                result[key] = os.path.expandvars(value)
            elif isinstance(value, dict):
                result[key] = self._expand_env_vars(value)
            else:
                result[key] = value
        return result

    def list_configs(self) -> Dict[str, dict]:
        """List all available configurations"""
        return self.config_map

    def run_with_config(self, alias: str, extra_args: list = None) -> None:
        """Run aider with the specified configuration"""
        config = self.get_config(alias)
        if not config:
            print(f"Error: No configuration found for alias '{alias}'")
            sys.exit(1)

        cmd = [config.get("base_command", "aider")]

        for key, value in config.get("args", {}).items():
            if isinstance(value, bool):
                if value:
                    cmd.append(f"--{key}")
            else:
                cmd.extend([f"--{key}", str(value)])

        if extra_args:
            cmd.extend(extra_args)

        try:
            subprocess.run(cmd)
        except FileNotFoundError:
            print(f"Error: Command '{cmd[0]}' not found")
            sys.exit(1)
        except KeyboardInterrupt:
            print("\nOperation cancelled by user")
            sys.exit(1)


def create_example_configs(config_manager: ConfigManager) -> None:
    """Create example configurations"""
    examples = {
        "g": {
            "base_command": "aider",
            "args": {
                "model": "gemini-pro",
                "edit-format": "simple",
                "auto-commit": True,
            },
        },
        "c3": {
            "base_command": "aider",
            "args": {
                "model": "claude-3-sonnet-20240229",
                "edit-format": "diff",
                "auto-commit": False,
                "api-key": "${ANTHROPIC_API_KEY}",
            },
        },
    }

    for alias, config in examples.items():
        config_manager.save_config(alias, config)


def main():
    parser = argparse.ArgumentParser(
        description="Aider configuration manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --init                 # Create example configurations
  %(prog)s --list                 # List available configurations
  %(prog)s g                      # Run aider with 'g' configuration
  %(prog)s c3 file1.py file2.py  # Run with 'c3' config and additional files
        """,
    )
    parser.add_argument("alias", nargs="?", help="Configuration alias to use")
    parser.add_argument(
        "--list", action="store_true", help="List available configurations"
    )
    parser.add_argument(
        "--init", action="store_true", help="Create example configurations"
    )
    parser.add_argument(
        "extra_args",
        nargs=argparse.REMAINDER,
        help="Additional arguments to pass to aider",
    )
    args = parser.parse_args()

    config_manager = ConfigManager()

    if args.init:
        create_example_configs(config_manager)
        print("Created example configurations in ~/.config/aider-profiles/")
        return

    if args.list:
        configs = config_manager.list_configs()
        if not configs:
            print("No configurations found")
            return
        print("\nAvailable configurations:")
        for alias, config in configs.items():
            print(f"\n{alias}:")
            print(json.dumps(config, indent=2))
        return

    if not args.alias:
        parser.print_help()
        return

    config_manager.run_with_config(args.alias, args.extra_args)


if __name__ == "__main__":
    main()
