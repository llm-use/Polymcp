#!/usr/bin/env python3
"""
PolyMCP CLI - Main Entry Point
Complete command-line interface for PolyMCP management.
"""

import click
from pathlib import Path
import sys

from . import __version__
from .commands import init, server, agent, test, config


@click.group()
@click.version_option(version=__version__, prog_name="polymcp")
@click.pass_context
def cli(ctx):
    """
    PolyMCP CLI - Universal MCP Agent & Toolkit
    
    Manage MCP servers, agents, and projects from the command line.
    
    Examples:
      polymcp init my-project          # Create new project
      polymcp server add http://...    # Add MCP server
      polymcp server list              # List configured servers
      polymcp agent run                # Run agent interactively
      polymcp test server http://...   # Test MCP server
    """
    ctx.ensure_object(dict)
    ctx.obj['config_dir'] = Path.home() / '.polymcp'
    ctx.obj['config_dir'].mkdir(exist_ok=True)


# Register command groups
cli.add_command(init.init_cmd, name='init')
cli.add_command(server.server, name='server')
cli.add_command(agent.agent, name='agent')
cli.add_command(test.test, name='test')
cli.add_command(config.config, name='config')


def main():
    """Entry point for CLI."""
    try:
        cli(obj={})
    except KeyboardInterrupt:
        click.echo("\n\nInterrupted by user", err=True)
        sys.exit(130)
    except Exception as e:
        click.echo(f"\nError: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
