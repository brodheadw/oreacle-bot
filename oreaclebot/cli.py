"""
Command-line interface for Oreacle Bot.

This module provides CLI entry points for running the bot in different modes.
"""

import os
import sys
import argparse
import logging
from typing import Optional

from .monitor import main as monitor_main, run_once


def monitor():
    """Run the continuous monitoring loop."""
    # Set up logging
    log_level = os.environ.get("OREACLE_LOG", "INFO").upper()
    logging.basicConfig(level=log_level, format="[%(asctime)s] %(levelname)s: %(message)s")
    
    # Check required environment variables
    required_vars = ["MANIFOLD_API_KEY", "MARKET_SLUG"]
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        logging.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logging.error("Please set these variables before running the bot.")
        sys.exit(1)
    
    try:
        monitor_main()
    except KeyboardInterrupt:
        logging.info("Monitoring stopped by user")
    except Exception as e:
        logging.exception(f"Error in monitoring loop: {e}")
        sys.exit(1)


def single_cycle():
    """Run a single monitoring cycle (useful for GitHub Actions)."""
    # Set up logging
    log_level = os.environ.get("OREACLE_LOG", "INFO").upper()
    logging.basicConfig(level=log_level, format="[%(asctime)s] %(levelname)s: %(message)s")
    
    # Check required environment variables
    required_vars = ["MANIFOLD_API_KEY", "MARKET_SLUG"]
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        logging.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logging.error("Please set these variables before running the bot.")
        sys.exit(1)
    
    logging.info("🤖 Oreacle Bot - Single Cycle Mode (GitHub Actions)")
    
    try:
        run_once()
        logging.info("✅ Single cycle complete.")
    except Exception as e:
        logging.exception(f"Error in single cycle: {e}")
        sys.exit(1)


def ladder_check():
    """Run ladder monotonicity check."""
    log_level = os.environ.get("OREACLE_LOG", "INFO").upper()
    logging.basicConfig(level=log_level, format="[%(asctime)s] %(levelname)s: %(message)s")
    
    # Import here to avoid circular imports
    from .ladder import main as ladder_main
    
    try:
        return ladder_main()
    except Exception as e:
        logging.exception(f"Error in ladder check: {e}")
        sys.exit(1)


def sentinel_byd():
    """Run BYD monthly sentinel."""
    log_level = os.environ.get("OREACLE_LOG", "INFO").upper()
    logging.basicConfig(level=log_level, format="[%(asctime)s] %(levelname)s: %(message)s")
    
    # Import here to avoid circular imports
    from .sentinels.byd_monthly import main as byd_main
    
    try:
        return byd_main()
    except Exception as e:
        logging.exception(f"Error in BYD sentinel: {e}")
        sys.exit(1)


def main():
    """Main CLI entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Oreacle Bot - Monitor Chinese regulatory sources for CATL lithium mine updates"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Monitor command
    monitor_parser = subparsers.add_parser(
        "monitor", 
        help="Run continuous monitoring (default behavior)"
    )
    
    # Single cycle command
    single_parser = subparsers.add_parser(
        "single", 
        help="Run a single monitoring cycle"
    )
    
    # Ladder monotonicity check
    ladder_parser = subparsers.add_parser(
        "ladder-check",
        help="Check market ladder monotonicity"
    )
    
    # Sentinel commands
    sentinel_parser = subparsers.add_parser(
        "sentinel",
        help="Run specialized monitoring sentinels"
    )
    sentinel_subparsers = sentinel_parser.add_subparsers(dest="sentinel_type", help="Sentinel types")
    
    byd_parser = sentinel_subparsers.add_parser(
        "byd-monthly",
        help="Monitor BYD monthly sales/production reports"
    )
    
    args = parser.parse_args()
    
    # Default to monitor if no command specified
    if args.command is None:
        args.command = "monitor"
    
    if args.command == "monitor":
        monitor()
    elif args.command == "single":
        single_cycle()
    elif args.command == "ladder-check":
        ladder_check()
    elif args.command == "sentinel":
        if args.sentinel_type == "byd-monthly":
            sentinel_byd()
        else:
            sentinel_parser.print_help()
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
