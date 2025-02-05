#!/usr/bin/env python

import os
import sys
import argparse
import subprocess
import shutil
from pathlib import Path
from typing import Dict


class ConfigManager:
    def __init__(self, config_dir: str = "~/.config/config-aider"):
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

    def _get_config_to_aliases(self) -> Dict[str, list]:
        """Get mapping of config names to their aliases"""
        aliases = self._get_aliases()
        config_to_aliases = {}
        for alias, target in aliases.items():
            if target not in config_to_aliases:
                config_to_aliases[target] = []
            config_to_aliases[target].append(alias)
        return config_to_aliases

    def list_configs(self) -> Dict[str, str]:
        """List all available configurations and their file paths"""
        configs = {}
        config_to_aliases = self._get_config_to_aliases()
        
        # List all config files with their aliases
        for config_file in Path(self.config_dir).glob("*.yml"):
            config_name = config_file.stem
            alias_list = config_to_aliases.get(config_name, [])
            alias_str = f" (aliases: {', '.join(alias_list)})" if alias_list else ""
            configs[config_name] = f"{str(config_file)}{alias_str}"
                
        return configs

    def show_config(self, config_name: str) -> None:
        """Show the contents of a configuration file with its aliases"""
        # First check if it's an alias
        aliases = self._get_aliases()
        if config_name in aliases:
            config_name = aliases[config_name]
            
        config_path = os.path.join(self.config_dir, f"{config_name}.yml")

        if not os.path.exists(config_path):
            print(f"Error: No configuration found for '{config_name}'")
            print(f"Expected to find config file at: {config_path}")
            sys.exit(1)

        # Get aliases for this config
        config_to_aliases = self._get_config_to_aliases()
        alias_list = config_to_aliases.get(config_name, [])
        alias_str = f" (aliases: {', '.join(alias_list)})" if alias_list else ""

        print(f"=== {config_name}{alias_str} ===")
        print(f"File: {config_path}\n")
        with open(config_path) as f:
            print(f.read())

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


def _get_sample_config_dir() -> str:
    """Get the path to the sample config directory"""
    try:
        # Get the path to this script via the symlink
        script_path = os.path.realpath(__file__)
        # Go up one directory to find the source directory
        src_dir = os.path.dirname(script_path)
        sample_dir = os.path.join(src_dir, "sample_config")
        if os.path.isdir(sample_dir):
            return sample_dir
    except Exception:
        pass
    return None

def create_example_configs(config_manager: ConfigManager) -> None:
    """Create example configurations by copying from sample_config directory"""
    sample_dir = _get_sample_config_dir()
    if not sample_dir:
        print("Error: Could not locate sample configurations directory")
        sys.exit(1)

    # Copy all .yml files from sample_config
    for config_file in Path(sample_dir).glob("*.yml"):
        dest_path = os.path.join(config_manager.config_dir, config_file.name)
        shutil.copy(config_file, dest_path)
        print(f"Created {dest_path}")

    # Copy aliases.txt if it exists
    aliases_src = os.path.join(sample_dir, "aliases.txt")
    aliases_dest = os.path.join(config_manager.config_dir, "aliases.txt")
    if os.path.exists(aliases_src):
        shutil.copy(aliases_src, aliases_dest)
        print(f"Created {aliases_dest}")


def main():
    parser = argparse.ArgumentParser(
        description="Aider configuration manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --init                 # Create example configurations
  %(prog)s --list                 # List available configurations
  %(prog)s --alias l llama3b      # Add 'myalias' for 'g' configuration
  %(prog)s l                      # Run aider with 'llama3b' config via the alias just added
  %(prog)s c3 file1.py file2.py   # Run with 'c3' config and additional files. Any additional args are passed through to aider.
        """,
    )
    parser.add_argument(
        "--alias", "-a", 
        nargs=2,
        metavar=("ALIAS", "TARGET"),
        help="Add a new alias for a configuration"
    )
    parser.add_argument("run_alias", nargs="?", help="Configuration alias to use")
    parser.add_argument(
        "--list", "-l", action="store_true", help="List available configurations"
    )
    parser.add_argument(
        "--init", "-i", action="store_true", help="Create example configurations"
    )
    parser.add_argument(
        "--show", "-s",
        metavar="CONFIG",
        help="Show the contents of a configuration file"
    )
    parser.add_argument(
        "extra_args",
        nargs=argparse.REMAINDER,
        help="Additional arguments to pass to aider",
    )
    parser.add_argument(
        "--uninstall-ca",
        action="store_true",
        help="Uninstall config-aider and remove all related files",
    )
    parser.add_argument(
        "--update-ca",
        action="store_true",
        help="Update config-aider by pulling latest changes from git",
    )
    args, unknown_args = parser.parse_known_args()
    if unknown_args and not args.run_alias:
        # If there are unknown args and no run_alias specified, show help
        parser.print_help()
        print(f"\nError: Unrecognized arguments: {' '.join(unknown_args)}")
        sys.exit(1)
    
    # Add unknown args to extra_args if we have a run_alias
    if args.run_alias:
        args.extra_args = unknown_args + args.extra_args

    config_manager = ConfigManager()

    if args.init:
        create_example_configs(config_manager)
        print("Created example configurations in ~/.config/config-aider/. Add your own yml files there.")
        return
        
    if args.alias:
        alias, target = args.alias
        aliases_path = os.path.join(config_manager.config_dir, "aliases.txt")
        
        # Check if alias already exists
        existing_aliases = config_manager._get_aliases()
        if alias in existing_aliases:
            print(f"Error: Alias '{alias}' already exists")
            sys.exit(1)
            
        # Check if target config exists
        target_path = os.path.join(config_manager.config_dir, f"{target}.yml")
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

    if args.update_ca:
        # Get the path to this script via the symlink
        script_path = os.path.realpath(__file__)
        # Get the source directory
        src_dir = os.path.dirname(script_path)
        
        # Check if this is a git repository
        if not os.path.exists(os.path.join(src_dir, ".git")):
            print("Error: Not a git repository - cannot update")
            sys.exit(1)
            
        # Run git pull
        try:
            print(f"Updating config-aider in {src_dir}")
            subprocess.run(["git", "-C", src_dir, "pull"], check=True)
            print("Update complete")
        except subprocess.CalledProcessError as e:
            print(f"Error: Failed to update: {e}")
            sys.exit(1)
        return

    if args.show:
        config_manager.show_config(args.show)
        return
        
    if args.uninstall_ca:
        # Remove ~/.local/share/config-aider
        share_dir = os.path.expanduser("~/.local/share/config-aider")
        if os.path.exists(share_dir):
            print(f"Removing {share_dir}")
            shutil.rmtree(share_dir)
        
        # Move ~/.config/config-aider to /tmp
        config_dir = os.path.expanduser("~/.config/config-aider")
        if os.path.exists(config_dir):
            tmp_dir = f"/tmp/config-aider-{os.getpid()}"
            print(f"Moving {config_dir} to {tmp_dir}")
            shutil.move(config_dir, tmp_dir)
        
        # Remove the ca symlink
        ca_path = shutil.which("ca")
        if ca_path:
            print(f"Removing {ca_path}")
            os.unlink(ca_path)
        
        print("Uninstall complete")
        return

    if args.run_alias:
        config_manager.run_with_config(args.run_alias, args.extra_args)
    elif not any([args.alias, args.list, args.init, args.uninstall_ca]):
        parser.print_help()


if __name__ == "__main__":
    main()
