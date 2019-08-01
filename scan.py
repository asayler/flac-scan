#!/usr/bin/env python3

import concurrent.futures
import logging
import os
import subprocess
import time

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
        self._flac_exe = [flac_exe]
        self._files = []
        self._failed = []
        self._passed = []
        self._total_cnt = 0

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

    def _preload(self):

        for root, dirs, files in os.walk(self._base):
            logger.info("Traversing '%s'", root)
            for f in files:
                self._total_cnt += 1
                if os.path.splitext(f)[1][1:].lower() in FLAC_EXTS:
                    logger.info("Adding '%s'", f)
                    file_path = os.path.join(root, f)
                    self._files.append(file_path)
                else:
                    logger.debug("Ignoring '%s'", f)

    def scan(self, workers=None):

        self._preload()

        if not workers:
            workers=os.cpu_count()

        logger.info(f"Scanning with {workers} workers")
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            start = time.perf_counter()
            for path, test in zip(self._files, executor.map(self._check_file, self._files)):
                if test:
                    self._passed.append(path)
                else:
                    self._failed.append(path)
        logger.info(f"Completed run in {time.perf_counter()-start:.2f} seconds")


### CLI Commands ###

@click.group()
@click.option('--quiet', is_flag=True)
def cli(quiet):

    if not quiet:
        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
    else:
        logger.addHandler(logging.NullHandler())

@cli.command()
@click.argument('base_path', type=click.Path(exists=True, readable=True, resolve_path=True))
@click.option('--output', default=None, type=click.Path(writable=True, resolve_path=True))
@click.option('--workers', default=os.cpu_count(), type=click.INT)
def scan(base_path, output, workers):
    '''Scan a directory for flac file corruption'''

    click.echo(f"Scanning {base_path}...")
    scanner = Scanner(base_path)

    scanner.scan(workers=workers)

    click.echo(f"Traversed {scanner._total_cnt} total files")
    click.echo(f"Scanned {len(scanner._files)} flac files")
    click.echo(f"Passed {len(scanner._passed)} flac files")
    click.echo(f"Failed {len(scanner._failed)} flac files")

    if not output:
        click.echo("Failed files:")
        for path in scanner._failed:
            click.echo(path)
    else:
        click.echo(f"Writing failed file list to {output}")
        with open(output, 'w') as out:
            for path in scanner._failed:
                out.write(f"{path}\n")


### Entry Point ###
if __name__ == "__main__":
    cli()
