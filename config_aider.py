#!/usr/bin/env python

import os
import sys
import argparse
import subprocess
from pathlib import Path
from typing import Dict


class ConfigManager:
    def __init__(self, config_dir: str = "~/.config/aider-profiles"):
        self.config_dir = os.path.expanduser(config_dir)
        self._ensure_config_dir()

    def _ensure_config_dir(self) -> None:
        """Create config directory if it doesn't exist"""
        os.makedirs(self.config_dir, exist_ok=True)

    def _get_aliases(self) -> Dict[str, str]:
        """Read aliases from aliases.txt file"""
        aliases_path = os.path.join(self.config_dir, "aliases.txt")
        if not os.path.exists(aliases_path):
            return {}

        aliases = {}
        with open(aliases_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    parts = line.split(":")
                    if len(parts) == 2:
                        alias, target = parts
                        aliases[alias.strip()] = target.strip()
        return aliases

    def list_configs(self) -> Dict[str, str]:
        """List all available configurations and their file paths"""
        configs = {}
        aliases = self._get_aliases()
        
        # Create a mapping of config names to their aliases
        config_to_aliases = {}
        for alias, target in aliases.items():
            if target not in config_to_aliases:
                config_to_aliases[target] = []
            config_to_aliases[target].append(alias)
        
        # List all config files with their aliases
        for config_file in Path(self.config_dir).glob("*.yml"):
            config_name = config_file.stem
            alias_list = config_to_aliases.get(config_name, [])
            alias_str = f" (aliases: {', '.join(alias_list)})" if alias_list else ""
            configs[config_name] = f"{str(config_file)}{alias_str}"
                
        return configs

    def run_with_config(self, alias: str, extra_args: list) -> None:
        """Run aider with the specified configuration file or alias"""
        # First check if it's an alias
        aliases = self._get_aliases()
        if alias in aliases:
            alias = aliases[alias]
            
        config_path = os.path.join(self.config_dir, f"{alias}.yml")

        if not os.path.exists(config_path):
            print(f"Error: No configuration found for alias '{alias}'")
            print(f"Expected to find config file at: {config_path}")
            sys.exit(1)

        cmd = ["aider", "--config", config_path] + extra_args

        try:
            subprocess.run(cmd)
        except FileNotFoundError:
            print(f"Error: Command '{cmd[0]}' not found")
            sys.exit(1)
        except KeyboardInterrupt:
            print("\nOperation cancelled by user")
            sys.exit(1)


def create_example_configs(config_manager: ConfigManager) -> None:
    """Create example configurations in YAML format"""
    example_configs = [
        {
            "alias": "gemini-experimental",
            "config": """
model: gemini/gemini-exp-1206
auto-commits: false
detect-urls: false
""",
        },
        {
            "alias": "deepseek-deepseek-chat",
            "config": """
model: deepseek/deepseek-chat
auto-commits: false
detect-urls: false
""",
        },
        {
            "alias": "claude-3-sonnet",
            "config": """
model: claude-3-sonnet-20240229
auto-commits: false
""",
        },
    ]

    for example in example_configs:
        filename = example["alias"].replace("/", "-") + ".yml"
        config_path = os.path.join(config_manager.config_dir, filename)
        with open(config_path, "w") as f:
            f.write(example["config"])

    # Create default aliases
    aliases_path = os.path.join(config_manager.config_dir, "aliases.txt")
    if not os.path.exists(aliases_path):
        default_aliases = """\
# Aider configuration aliases
# Format: alias:config-name

g:gemini-experimental
c3:claude-3-sonnet
d:deepseek-deepseek-chat
"""
        with open(aliases_path, "w") as f:
            f.write(default_aliases)


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
    parser.add_argument(
        "--add-alias", "-a", 
        nargs=2,
        metavar=("ALIAS", "TARGET"),
        help="Add a new alias for a configuration"
    )
    parser.add_argument("alias", nargs="?", help="Configuration alias to use")
    parser.add_argument(
        "--list", "-l", action="store_true", help="List available configurations"
    )
    parser.add_argument(
        "--init", "-i", action="store_true", help="Create example configurations"
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
        
    if args.add_alias:
        alias, target = args.add_alias
        aliases_path = os.path.join(config_manager.config_dir, "aliases.txt")
        
        # Check if alias already exists
        existing_aliases = config_manager._get_aliases()
        if alias in existing_aliases:
            print(f"Error: Alias '{alias}' already exists")
            sys.exit(1)
            
        # Check if target config exists
        target_path = os.path.join(config_manager.config_dir, f"{target}.conf.yml")
        if not os.path.exists(target_path):
            print(f"Error: Target configuration '{target}' does not exist")
            sys.exit(1)
            
        # Add the new alias
        with open(aliases_path, "a") as f:
            f.write(f"\n{alias}:{target}\n")
        print(f"Added alias: {alias} -> {target}")
        return

    if args.list:
        configs = config_manager.list_configs()
        for config_name, config_info in configs.items():
            print(f"{config_name}: {config_info}")
        return

    if not args.alias:
        parser.print_help()
        return

    config_manager.run_with_config(args.alias, args.extra_args)


if __name__ == "__main__":
    main()
