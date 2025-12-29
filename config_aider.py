#!/usr/bin/env python

import os
import sys
import argparse
import subprocess
import shutil
import shlex
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import tempfile
import json


class ConfigManager:
    def __init__(self, config_dir: str = "~/.config/config-aider"):
        self.config_dir = Path(os.path.expanduser(config_dir))
        self.global_defaults_path = self.config_dir / "GLOBAL_DEFAULTS.yml"
        self._ensure_config_dir()

    def _ensure_config_dir(self) -> None:
        """Create config directory if it doesn't exist"""
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def _get_aliases(self) -> Dict[str, str]:
        """Read aliases from aliases.txt file"""
        aliases_path = self.config_dir / "aliases.txt"
        if not aliases_path.is_file():
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
        for config_file in self.config_dir.glob("*.yml"):
            if config_file.name == "GLOBAL_DEFAULTS.yml":
                continue
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

        config_path = self.config_dir / f"{config_name}.yml"

        if not config_path.is_file():
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

    def _substitute_bedrock_arn_placeholders(self, content: str) -> str:
        """Substitute <region> and <account> placeholders in Bedrock ARNs"""
        bedrock_region = os.environ.get("BEDROCK_REGION")
        bedrock_account = os.environ.get("BEDROCK_ACCOUNT")
        
        if "<region>" in content or "<account>" in content:
            if not bedrock_region:
                print("Error: Configuration contains <region> placeholder but BEDROCK_REGION environment variable is not set")
                sys.exit(1)
            if not bedrock_account:
                print("Error: Configuration contains <account> placeholder but BEDROCK_ACCOUNT environment variable is not set")
                sys.exit(1)
            
            content = content.replace("<region>", bedrock_region)
            content = content.replace("<account>", bedrock_account)
            
            if os.environ.get("CA_DEBUG") == "true":
                print(f"Substituted Bedrock ARN placeholders: region={bedrock_region}, account={bedrock_account}")
        
        return content

    def _extract_bedrock_model_name(self, config_path: Path) -> Optional[str]:
        """Extract the Bedrock model name from the config file"""
        try:
            with open(config_path, 'r') as f:
                for line in f:
                    stripped_line = line.strip()
                    if stripped_line.startswith('model:'):
                        model_value = stripped_line.split(':', 1)[1].strip()
                        # Remove quotes if present
                        if model_value.startswith(('"', "'")) and model_value.endswith(('"', "'")):
                            model_value = model_value[1:-1]
                        # Check if it's a Bedrock converse model
                        if model_value.startswith('bedrock/converse/'):
                            return model_value
        except Exception as e:
            if os.environ.get("CA_DEBUG") == "true":
                print(f"Warning: Could not extract model name from {config_path}: {e}")
        return None

    def _create_bedrock_model_profile(self, model_name: str, bedrock_region: str, bedrock_account: str) -> dict:
        """Create a single Bedrock model profile with the appropriate settings"""
        # Extract the model ID from the full model name
        # e.g., "bedrock/converse/anthropic.claude-sonnet-4-5-20250929-v1:0" -> "anthropic.claude-sonnet-4-5-20250929-v1:0"
        model_id = model_name.replace('bedrock/converse/', '')
        
        # Determine if this is a global inference profile or a direct model
        if model_id.startswith('global.'):
            # It's already a global inference profile
            arn = f"arn:aws:bedrock:{bedrock_region}:{bedrock_account}:inference-profile/{model_id}"
        else:
            # Convert to global inference profile format
            arn = f"arn:aws:bedrock:{bedrock_region}:{bedrock_account}:inference-profile/global.{model_id}"
        
        profile = {
            "name": model_name,
            "extra_params": {
                "model_id": arn,
                "max_tokens": 64000
            },
            "cache_control": True,
            "accepts_settings": ["thinking_tokens"]
        }
        
        return profile

    def _generate_bedrock_inference_profiles(self, config_path: Path) -> str:
        """Generate Bedrock inference profiles JSON with substituted ARN values"""
        bedrock_region = os.environ.get("BEDROCK_REGION")
        bedrock_account = os.environ.get("BEDROCK_ACCOUNT")
        
        if not bedrock_region or not bedrock_account:
            print("Error: BEDROCK_REGION and BEDROCK_ACCOUNT environment variables must be set for Bedrock inference profiles")
            sys.exit(1)
        
        # Extract the model name from the config
        model_name = self._extract_bedrock_model_name(config_path)
        if not model_name:
            print(f"Error: Could not extract Bedrock model name from config file {config_path}")
            sys.exit(1)
        
        # Create a single profile for this model
        profile = self._create_bedrock_model_profile(model_name, bedrock_region, bedrock_account)
        profiles = [profile]
        
        try:
            tmp_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json")
            tmp_file_path = tmp_file.name
            json.dump(profiles, tmp_file, indent=2)
            tmp_file.close()
            
            if os.environ.get("CA_DEBUG") == "true":
                print(f"Generated Bedrock inference profile for {model_name} at {tmp_file_path}")
            
            return tmp_file_path
        except Exception as e:
            print(f"Error creating Bedrock inference profiles file: {e}")
            sys.exit(1)

    def _get_model_settings(self, config_path: str, only_provider: str = None) -> str:
        """Generate model settings JSON for OpenRouter models"""
        if not only_provider:
            return None

        models = []
        with open(config_path) as f:
            for line in f:
                line = line.strip()
                if "openrouter/" in line.lower():
                    # Handle both quoted and unquoted values
                    if ":" in line:
                        key, value = line.split(":", 1)
                        value = value.strip()
                        # Remove quotes if present
                        if value.startswith(('"', "'")) and value.endswith(('"', "'")):
                            value = value[1:-1]
                        if value.startswith("openrouter/"):
                            models.append(value)

        if not models:
            return None

        # Create model settings JSON
        settings = []
        for model in models:
            settings.append({
                "name": model,
                "extra_params": {
                    "extra_body": {
                        "provider": {
                            "order": [only_provider],
                            "allow_fallbacks": False,
                            "data_collection": "deny",
                            "require_parameters": True
                        }
                    }
                }
            })

        # Write to temp file
        tmp_file_path = None
        try:
            tmp_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json")
            tmp_file_path = tmp_file.name
            json.dump(settings, tmp_file)
            tmp_file.close()
            return tmp_file_path
        except Exception as e:
            print(f"Error creating model settings temp file: {e}")
            if tmp_file_path and os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
            sys.exit(1)

    def _resolve_config_path(self, alias: str) -> Path:
        """Resolve alias to config path and check existence."""
        aliases = self._get_aliases()
        config_name = alias
        if alias in aliases:
            config_name = aliases[alias]

        specific_config_path = self.config_dir / f"{config_name}.yml"

        if not specific_config_path.is_file():
            print(f"Error: No configuration found for '{config_name}'")
            print(f"Expected to find config file at: {specific_config_path}")
            sys.exit(1)
        return specific_config_path

    def _get_api_key_value(self, api_key_env_var: Optional[str]) -> Optional[str]:
        """Get API key value from environment variable."""
        if not api_key_env_var:
            return None
        api_key = os.environ.get(api_key_env_var)
        if not api_key:
            print(f"Error: Environment variable '{api_key_env_var}' specified in config but not set.")
            sys.exit(1)
        return api_key

    def _get_api_key_info(self, config_path: Path) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract API key env var name and provider from config file.
        Returns (api_key_env_var, api_key_provider). Provider defaults to 'openai'.
        """
        api_key_env_var = None
        api_key_provider = "openai"

        if not config_path.is_file():
            return None, api_key_provider

        try:
            with open(config_path, 'r') as f:
                for line in f:
                    stripped_line = line.strip()
                    if stripped_line.startswith('api-key-env:'):
                        api_key_env_var = stripped_line.split(':', 1)[1].strip()
                    elif stripped_line.startswith('api-key-provider:'):
                        api_key_provider = stripped_line.split(':', 1)[1].strip()
        except Exception as e:
            print(f"Warning: Could not read API key info from {config_path}: {e}")

        return api_key_env_var, api_key_provider

    def _parse_only_provider(self, extra_args: List[str]) -> Tuple[Optional[str], List[str]]:
        """Handles the --only argument, returning the provider and updated args."""
        only_provider = None
        if "--only" in extra_args:
            try:
                only_idx = extra_args.index("--only")
                only_provider = extra_args[only_idx + 1]
                extra_args = extra_args[:only_idx] + extra_args[only_idx + 2:]
            except IndexError:
                print("Error: --only requires a provider argument")
                sys.exit(1)
        return only_provider, extra_args

    def _check_for_bedrock_inference_profiles(self, config_path: Path) -> bool:
        """Check if config references .bedrock-inference-profiles.json"""
        try:
            with open(config_path, 'r') as f:
                content = f.read()
                return '.bedrock-inference-profiles.json' in content
        except Exception:
            return False

    def _create_temporary_config(self, specific_config_path: Path, global_defaults_exist: bool, bedrock_profiles_path: Optional[str] = None) -> Optional[str]:
        """Combines global defaults and specific config into a temporary file if needed."""
        temp_config_path = None
        try:
            temp_config_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".yml", encoding='utf-8')
            temp_config_path = temp_config_file.name

            if global_defaults_exist:
                if os.environ.get("CA_DEBUG") == "true":
                    print(f"Prepending global defaults from {self.global_defaults_path}")
                with open(self.global_defaults_path, "r") as f_global:
                    global_content = f_global.read()
                    global_content = self._substitute_bedrock_arn_placeholders(global_content)
                    temp_config_file.write(global_content)
                temp_config_file.write("\n")

            if os.environ.get("CA_DEBUG") == "true":
                print(f"Appending specific config from {specific_config_path} (filtering API keys)")
            with open(specific_config_path, "r") as f_specific:
                specific_content = []
                for line in f_specific:
                    stripped_line = line.strip()
                    if not stripped_line.startswith("api-key-env:") and not stripped_line.startswith("api-key-provider:"):
                        # Replace .bedrock-inference-profiles.json reference with generated file
                        if bedrock_profiles_path and '.bedrock-inference-profiles.json' in line:
                            line = line.replace('.bedrock-inference-profiles.json', bedrock_profiles_path)
                        specific_content.append(line)
                specific_content_str = ''.join(specific_content)
                specific_content_str = self._substitute_bedrock_arn_placeholders(specific_content_str)
                temp_config_file.write(specific_content_str)

            temp_config_file.close()
            if os.environ.get("CA_DEBUG") == "true":
                print(f"Using combined temporary config path: {temp_config_path}")
            return temp_config_path
        except Exception as e:
            print(f"Error creating temporary config file: {e}")
            if temp_config_path and os.path.exists(temp_config_path):
                os.unlink(temp_config_path) # Clean up if creation failed mid-way
            sys.exit(1)

    def _read_standard_repo_args(self) -> List[str]:
        """Reads arguments from .aider-standard-repo-args file."""
        standard_args_file = Path(".aider-standard-repo-args")
        standard_args = []
        if standard_args_file.is_file():
            with open(standard_args_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        try:
                            args_from_line = shlex.split(line)
                            standard_args.extend(args_from_line)
                        except ValueError as e:
                            print(f"Warning: Skipping invalid line in {standard_args_file}: {line} ({e})")
            if standard_args and os.environ.get("CA_DEBUG") != "true": # Only print if not in debug, debug prints later
                 print(f"Adding standard repo args from {standard_args_file}: {shlex.join(standard_args)}")
        return standard_args

    def _build_aider_command(self, effective_config_path: str, api_key_provider: Optional[str], api_key: Optional[str], model_settings_file: Optional[str], standard_args: List[str], extra_args: List[str]) -> List[str]:
        """Builds the command list to execute aider."""
        cmd = ["aider-ce", "--tui", "--config", effective_config_path]
        if api_key:
            cmd.extend(["--api-key", f"{api_key_provider}={api_key}"])
        if model_settings_file:
            cmd.extend(["--model-settings-file", model_settings_file])
        cmd.extend(standard_args)
        cmd.extend(extra_args)
        return cmd

    def _execute_aider(self, cmd: List[str]) -> None:
        """Execute the aider command."""
        try:
            if os.environ.get("CA_DEBUG") == "true":
                print(f"Executing command: {shlex.join(cmd)}")
            os.execvpe(cmd[0], cmd, os.environ)
        except FileNotFoundError:
            print(f"Error: Command '{cmd[0]}' not found")
            sys.exit(1) # Exit here, cleanup happens in the caller's finally

    def run_with_config(self, alias: str, extra_args: List[str]) -> None:
        """Run aider with the specified configuration file or alias"""
        specific_config_path = self._resolve_config_path(alias)
        only_provider, extra_args = self._parse_only_provider(extra_args)

        model_settings_file = None
        temp_config_path = None
        bedrock_profiles_path = None
        cmd = [] # Initialize cmd here to ensure it's defined for the finally block if errors occur early

        try:
            # Check if config needs Bedrock inference profiles
            needs_bedrock_profiles = self._check_for_bedrock_inference_profiles(specific_config_path)
            if needs_bedrock_profiles:
                bedrock_profiles_path = self._generate_bedrock_inference_profiles(specific_config_path)

            model_settings_file = self._get_model_settings(str(specific_config_path), only_provider)
            api_key_env_var, api_key_provider = self._get_api_key_info(specific_config_path)
            api_key = self._get_api_key_value(api_key_env_var)

            global_defaults_exist = self.global_defaults_path.is_file()
            needs_temp_config = global_defaults_exist or (api_key is not None) or needs_bedrock_profiles
            effective_config_path = str(specific_config_path)

            if needs_temp_config:
                # _create_temporary_config handles its own errors and cleanup on failure
                temp_config_path = self._create_temporary_config(specific_config_path, global_defaults_exist, bedrock_profiles_path)
                effective_config_path = temp_config_path

            standard_args = self._read_standard_repo_args()

            cmd = self._build_aider_command(
                effective_config_path,
                api_key_provider,
                api_key,
                model_settings_file,
                standard_args,
                extra_args
            )

            self._execute_aider(cmd)

        # Outer except blocks start here
        except KeyboardInterrupt:
            print("\nOperation cancelled by user")
            # Cleanup is handled in finally block
            sys.exit(1)
        except Exception as e:
            print(f"An unexpected error occurred before executing aider: {e}")
            # Cleanup is handled in finally block
            sys.exit(1)
        finally:
            # Ensure temporary files are cleaned up
            if temp_config_path and os.path.exists(temp_config_path):
                if os.environ.get("CA_DEBUG") == "true":
                    print(f"Cleaning up temporary config file: {temp_config_path}")
                os.unlink(temp_config_path)
            if model_settings_file and os.path.exists(model_settings_file):
                if os.environ.get("CA_DEBUG") == "true":
                    print(f"Cleaning up temporary model settings file: {model_settings_file}")
                os.unlink(model_settings_file)
            if bedrock_profiles_path and os.path.exists(bedrock_profiles_path):
                if os.environ.get("CA_DEBUG") == "true":
                    print(f"Cleaning up temporary Bedrock profiles file: {bedrock_profiles_path}")
                os.unlink(bedrock_profiles_path)


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
    for config_file_path in Path(sample_dir).glob("*.yml"):
        dest_path = config_manager.config_dir / config_file_path.name
        shutil.copy(config_file_path, dest_path)
        print(f"Created {dest_path}")

    # Copy aliases.txt if it exists
    aliases_src_path = Path(sample_dir) / "aliases.txt"
    aliases_dest_path = config_manager.config_dir / "aliases.txt"
    if aliases_src_path.exists():
        shutil.copy(aliases_src_path, aliases_dest_path)
        print(f"Created {aliases_dest_path}")

def _handle_add_alias(config_manager: ConfigManager, alias: str, target: str) -> None:
    """Adds a new alias."""
    aliases_path = config_manager.config_dir / "aliases.txt"
    existing_aliases = config_manager._get_aliases()
    if alias in existing_aliases:
        print(f"Error: Alias '{alias}' already exists")
        sys.exit(1)

    target_path = config_manager.config_dir / f"{target}.yml"
    if not target_path.is_file():
        print(f"Error: Target configuration '{target}' does not exist at {target_path}")
        sys.exit(1)

    with open(aliases_path, "a") as f:
        f.write(f"{alias}:{target}\n")
    print(f"Added alias: {alias} -> {target}")

def _handle_update() -> None:
    """Updates config-aider by pulling latest changes from git."""
    try:
        script_path = os.path.realpath(__file__)
        src_dir = os.path.dirname(script_path)
    except NameError: # __file__ might not be defined (e.g. interactive)
         print("Error: Could not determine script path.")
         sys.exit(1)

    if not os.path.exists(os.path.join(src_dir, ".git")):
        print(f"Error: Not a git repository ({src_dir}) - cannot update")
        sys.exit(1)

    try:
        print(f"Updating config-aider in {src_dir}")
        # Use absolute path for git -C
        subprocess.run(["git", "-C", src_dir, "pull"], check=True)
        print("Update complete")
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to update: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("Error: 'git' command not found. Is git installed and in your PATH?")
        sys.exit(1)

def _handle_uninstall() -> None:
    """Uninstalls config-aider."""
    share_dir = os.path.expanduser("~/.local/share/config-aider")
    if os.path.exists(share_dir):
        print(f"Removing {share_dir}")
        shutil.rmtree(share_dir)

    config_dir = os.path.expanduser("~/.config/config-aider")
    if os.path.exists(config_dir):
        tmp_dir = f"/tmp/config-aider-{os.getpid()}"
        print(f"Moving {config_dir} to {tmp_dir}")
        try:
            shutil.move(config_dir, tmp_dir)
        except Exception as e:
            print(f"Error moving config directory: {e}")
            # Continue to attempt removing symlink

    ca_path = shutil.which("ca")
    if ca_path and os.path.islink(ca_path): # Check if it's a symlink before removing
        try:
            # Check if the symlink points to this script before removing
            target_path = os.path.realpath(ca_path)
            script_path = os.path.realpath(__file__)
            if target_path == script_path:
                print(f"Removing symlink {ca_path}")
                os.unlink(ca_path)
            else:
                print(f"Skipping removal of {ca_path} as it does not point to this script ({target_path})")
        except Exception as e:
            print(f"Error removing symlink {ca_path}: {e}")
    elif ca_path:
        print(f"Skipping removal of {ca_path} as it is not a symlink.")


    print("Uninstall complete. You may need to manually remove other related files if installed differently.")


def _parse_arguments() -> Tuple[argparse.ArgumentParser, argparse.Namespace]:
    """Parse command line arguments."""
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
  %(prog)s or --only DeepSeek     # Run with 'or' config, which must map to an openrouter/ model, and instruct openrouter to use only the DeepSeek provider
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
        "--only",
        metavar="PROVIDER",
        help="For OpenRouter models, only use the specified provider (e.g. 'Azure', 'Anthropic')",
    )
    parser.add_argument(
        "--update-ca",
        action="store_true",
        help="Update config-aider by pulling latest changes from git",
    )
    args, unknown_args = parser.parse_known_args()

    # Handle unknown args specifically for the run_alias case
    if args.run_alias:
        args.extra_args = unknown_args + args.extra_args
    elif unknown_args:
        # If there are unknown args and no run_alias specified, it's an error
        parser.print_help()
        print(f"\nError: Unrecognized arguments: {' '.join(unknown_args)}")
        sys.exit(1)

    return parser, args


def main():
    parser, args = _parse_arguments()
    config_manager = ConfigManager()

    # Handle actions that don't involve running aider first
    if args.init:
        create_example_configs(config_manager)
        print("Created example configurations in ~/.config/config-aider/. Add your own yml files there.")
        return

    if args.alias:
        _handle_add_alias(config_manager, args.alias[0], args.alias[1])
        return

    if args.list:
        configs = config_manager.list_configs()
        for config_name, config_info in configs.items():
            print(f"{config_name}: {config_info}")
        return

    if args.update_ca:
        _handle_update()
        return

    if args.show:
        config_manager.show_config(args.show)
        return

    if args.uninstall_ca:
        _handle_uninstall()
        return

    if args.run_alias:
        # Add it back to extra_args if it was passed as a top-level arg
        if args.only:
            args.extra_args = ["--only", args.only] + args.extra_args
        config_manager.run_with_config(args.run_alias, args.extra_args)
    elif not any([args.alias, args.list, args.init, args.uninstall_ca, args.update_ca, args.show]):
        # If no action was taken and no run_alias provided, show help
        parser.print_help()


if __name__ == "__main__":
    main()
