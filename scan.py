#!/usr/bin/env python3

import click


### Logic Classes ###

class scanner():

    def __init__(self, base_path):

        self._base = base_path
        self._failed = set()

    def scan(self):
        pass


### CLI Commands ###

@click.group()
def cli():
    pass

@cli.command()
def scan():
    '''Scan a directory for flac file corruption'''

    click.echo("Not yet implemented")

### Entry Point ###
if __name__ == "__main__":
    cli()
