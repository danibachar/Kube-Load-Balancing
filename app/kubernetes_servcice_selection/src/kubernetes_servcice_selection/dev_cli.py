"""Click command line script for running the development webserver."""

import click
import os

from .app import app


@click.command()
@click.option(
    "-p",
    "--port",
    default=8050,
    metavar="PORT",
    type=int,
    help="Port to run the development webserver on. Defaults to 8050.",
)
@click.option(
    "-h",
    "--host",
    default="0.0.0.0",
    metavar="HOST",
    help=(
        "The hostname to listen on. Set this to '0.0.0.0' to have the server "
        "available externally as well. Defaults to '127.0.0.1'."
    ),
)
@click.option(
    "--debug/--no-debug",
    default=True,
    help="Toggles whether the Dash app is run in debug mode. Defaults to True",
)
def main(port, host, debug):
    overrided_port = os.environ.get('PORT', port)
    print("###overrided_port###\n{}".format(overrided_port))
    app.run_server(port=overrided_port, debug=debug, host=host)
