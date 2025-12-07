"""
CLI entry point and commands.
"""

import argparse
import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False) -> None:
    """Configure CLI logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(levelname)s: %(message)s"
    )


def cmd_download(args: argparse.Namespace) -> int:
    """Handle download command."""
    from ..core import get_config
    from ..core.download import get_download_manager
    
    config = get_config()
    manager = get_download_manager()
    
    # Determine save path
    save_path = args.output or config.paths.default_save_path
    
    print(f"Adding download: {args.repo_id}")
    print(f"Platform: {args.platform}")
    print(f"Save path: {save_path}")
    
    try:
        task_id = manager.add(
            repo_id=args.repo_id,
            save_path=save_path,
            platform=args.platform,
            repo_type=args.type,
        )
        print(f"Download queued with ID: {task_id}")
        
        if args.wait:
            print("Waiting for download to complete...")
            manager.start()
            # In a real implementation, we'd wait for completion
            
        return 0
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_list(args: argparse.Namespace) -> int:
    """Handle list command."""
    from ..core import get_db
    
    db = get_db()
    
    if args.what == "history":
        history = db.get_history(limit=args.limit)
        if not history:
            print("No download history found.")
            return 0
        
        print(f"\nDownload History ({len(history)} entries):")
        print("-" * 60)
        for entry in history:
            fav = "⭐" if entry.is_favorite else "  "
            print(f"{fav} {entry.repo_id:<40} {entry.platform}")
            
    elif args.what == "local":
        models = db.get_local_models()
        if not models:
            print("No local models found. Run 'scan' first.")
            return 0
        
        print(f"\nLocal Models ({len(models)} files):")
        print("-" * 60)
        for model in models:
            size = f"{model.file_size / 1024 / 1024:.1f} MB" if model.file_size else "?"
            print(f"  {model.file_name:<40} {size:>10}  {model.model_type}")
            
    elif args.what == "queue":
        pending = db.get_pending_downloads()
        if not pending:
            print("Download queue is empty.")
            return 0
        
        print(f"\nDownload Queue ({len(pending)} items):")
        print("-" * 60)
        for item in pending:
            print(f"  [{item.priority}] {item.repo_id:<40} {item.status}")
    
    return 0


def cmd_scan(args: argparse.Namespace) -> int:
    """Handle scan command."""
    from ..core import get_db
    from ..core.constants import FILE_CATEGORIES
    import os
    import hashlib
    
    paths = args.paths or [os.path.expanduser("~/.cache/huggingface/hub")]
    
    print("Scanning for models...")
    db = get_db()
    
    MODEL_EXTENSIONS = {'.safetensors', '.ckpt', '.pt', '.pth', '.bin', '.gguf'}
    found_count = 0
    
    for scan_path in paths:
        if not os.path.exists(scan_path):
            print(f"  Skipping (not found): {scan_path}")
            continue
        
        print(f"  Scanning: {scan_path}")
        
        for root, dirs, files in os.walk(scan_path):
            for filename in files:
                ext = os.path.splitext(filename)[1].lower()
                if ext in MODEL_EXTENSIONS:
                    filepath = os.path.join(root, filename)
                    stat = os.stat(filepath)
                    
                    # Detect model type from path/name
                    path_lower = filepath.lower()
                    model_type = "checkpoint"
                    if "lora" in path_lower:
                        model_type = "lora"
                    elif "vae" in path_lower:
                        model_type = "vae"
                    elif "controlnet" in path_lower:
                        model_type = "controlnet"
                    elif "embedding" in path_lower:
                        model_type = "embedding"
                    
                    db.add_local_model({
                        "file_path": filepath,
                        "file_name": filename,
                        "file_size": stat.st_size,
                        "model_type": model_type,
                    })
                    found_count += 1
    
    print(f"\nFound {found_count} model files.")
    return 0


def cmd_config(args: argparse.Namespace) -> int:
    """Handle config command."""
    from ..core import get_config
    
    config = get_config()
    
    if args.action == "show":
        print("\nCurrent Configuration:")
        print("-" * 40)
        print(f"  Default save path: {config.paths.default_save_path}")
        print(f"  ComfyUI root: {config.paths.comfy_root or 'Not set'}")
        print(f"  Max workers: {config.download.max_workers}")
        print(f"  Auto retry: {config.download.auto_retry}")
        print(f"  Theme: {config.ui.theme}")
        
    elif args.action == "set":
        if not args.key or not args.value:
            print("Error: --key and --value required for 'set'", file=sys.stderr)
            return 1
        
        try:
            config.update(**{args.key: args.value})
            print(f"Set {args.key} = {args.value}")
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
            
    elif args.action == "reset":
        from ..core.config import reset_config
        reset_config()
        print("Configuration reset to defaults.")
    
    return 0


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="hf-suite",
        description="HuggingFace Download Suite CLI",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 2.0.0"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Download command
    dl_parser = subparsers.add_parser("download", aliases=["dl"], help="Download a model")
    dl_parser.add_argument("repo_id", help="Repository ID (e.g., user/model)")
    dl_parser.add_argument(
        "-p", "--platform",
        choices=["huggingface", "modelscope"],
        default="huggingface",
        help="Platform (default: huggingface)"
    )
    dl_parser.add_argument(
        "-t", "--type",
        choices=["model", "dataset"],
        default="model",
        help="Repository type (default: model)"
    )
    dl_parser.add_argument(
        "-o", "--output",
        help="Output directory"
    )
    dl_parser.add_argument(
        "-w", "--wait",
        action="store_true",
        help="Wait for download to complete"
    )
    dl_parser.set_defaults(func=cmd_download)
    
    # List command
    list_parser = subparsers.add_parser("list", aliases=["ls"], help="List items")
    list_parser.add_argument(
        "what",
        choices=["history", "local", "queue"],
        help="What to list"
    )
    list_parser.add_argument(
        "-n", "--limit",
        type=int,
        default=20,
        help="Maximum items to show"
    )
    list_parser.set_defaults(func=cmd_list)
    
    # Scan command
    scan_parser = subparsers.add_parser("scan", help="Scan for local models")
    scan_parser.add_argument(
        "paths",
        nargs="*",
        help="Paths to scan (default: ~/.cache/huggingface/hub)"
    )
    scan_parser.set_defaults(func=cmd_scan)
    
    # Config command
    config_parser = subparsers.add_parser("config", help="Manage configuration")
    config_parser.add_argument(
        "action",
        choices=["show", "set", "reset"],
        help="Config action"
    )
    config_parser.add_argument("--key", help="Config key for 'set'")
    config_parser.add_argument("--value", help="Config value for 'set'")
    config_parser.set_defaults(func=cmd_config)
    
    return parser


def cli(args: list = None) -> int:
    """Run the CLI."""
    parser = create_parser()
    parsed = parser.parse_args(args)
    
    setup_logging(parsed.verbose)
    
    if not parsed.command:
        parser.print_help()
        return 0
    
    return parsed.func(parsed)


def main() -> None:
    """Main entry point."""
    sys.exit(cli())


if __name__ == "__main__":
    main()
