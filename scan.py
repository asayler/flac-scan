#!/usr/bin/env python3

import logging
import os
import subprocess

import click



FLAC_EXTS = ["flac"]
FLAC_CMD = "flac"
FLAC_VERSION = ["--version"]
FLAC_TEST = ["-s", "--test"]

logger = logging.getLogger("flac_scan")


### Logic Classes ###

class Scanner():

    def __init__(self, base_path, flac_exe=FLAC_CMD):

        # Setup Class
        self._base = base_path
        self._failed = set()
        self._flac_exe = [flac_exe]

        # Test flac install
        cmd = self._flac_exe + FLAC_VERSION
        try:
            cp = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if cp.returncode == 0:
                logger.info("Using %s", cp.stdout.decode().strip())
            else:
                raise OSError(f"Faild to run '{cmd}': {cp.stderr.decode()}")
        except FileNotFoundError:
            raise OSError(f"Could not find '{self._flac_exe[0]}'. Is it installed?")

    def _check_file(self, file_path):

        cmd = self._flac_exe + FLAC_TEST + [file_path]
        try:
            logger.debug("Running %s", cmd)
            cp = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if cp.returncode == 0:
                return True
            else:
                logger.debug("Failed to verify %s: %s", file_path, cp.stderr.decode())
                return False
        except FileNotFoundError:
            raise OSError(f"Could not find '{self._flac_exe[0]}'. Is it installed?")

    def scan(self):

        for root, dirs, files in os.walk(self._base):
            logger.info("Traversing '%s'", root)
            for f in files:
                if os.path.splitext(f)[1][1:].lower() in FLAC_EXTS:
                    logger.info("Scanning '%s'", f)
                    file_path = os.path.join(root, f)
                    if not self._check_file(file_path):
                        logger.warning("Failed to verify '%s'", f)
                else:
                    logger.debug("Skipping '%s'", f)


### CLI Commands ###

@click.group()
def cli():

    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

@cli.command()
@click.argument('base_path', type=click.Path(exists=True, readable=True, resolve_path=True))
def scan(base_path):
    '''Scan a directory for flac file corruption'''

    click.echo(f"Scanning {base_path}...")
    scanner = Scanner(base_path)
    scanner.scan()

### Entry Point ###
if __name__ == "__main__":
    cli()
