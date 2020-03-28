# -*- coding: utf-8 -*-

import sys
import os
import argparse

import asyncio

from lin.arbiter import Arbiter
from lin.config import Config
from lin.logger import logger_setup
from lin.utils import load_config
from lin.version import __SERVER_NAME__

class CommandInterface:
    def __init__(self):
        self.parser = argparse.ArgumentParser()
      
        self.parser.add_argument(
                '-v', 
                '--version', 
                dest = 'version', 
                action='store_true', 
                help='Print version information'
                )
        self.parser.add_argument(
                '-V', 
                '--verbose', 
                dest = 'verbose', 
                action='store_true', 
                help='Print verbose information'
                )
        self.parser.add_argument(
                '-t', 
                '--test', 
                dest = 'test', 
                help='Just test the configuration file'
                )
        self.parser.add_argument(
                '-c', 
                '--config', 
                dest = 'config', 
                help='Specify which configuration file for Lin'
                )

    @classmethod
    def entrypoint(cls):
        """
        Main entrypoint for external starts.
        """
        cls().run(sys.argv[1:])

    def print_version(self):
        sys.stdout.write(__SERVER_NAME__)
        sys.exit(0)

    def print_verbose(self):
        sys.stdout.write('{}\nPython {}'.format(__SERVER_NAME__, sys.version))
        sys.exit(0)

    def test_config(self, config):
        try:
            cfg = load_config(config)
            Config.parse(cfg)
        except Exception as e:
            sys.stdout.write('Configuratin file exception {}'.format(str(e)))
            sys.exit(-1)
        else:
            sys.stdout.write('Configuration file test succeeded')
            sys.exit(0)

    def start(self, args):
        cfg = load_config(args.config)
        config = Config.parse(cfg)
        logger_setup(*config.error_log)
        arbiter = Arbiter(config)
        arbiter.run()

    def run(self, args):
        args = self.parser.parse_args(args)

        if args.version:
            self.print_version()
        elif args.verbose:
            self.print_verbose()
        elif args.test:
            self.test_config(args.test)
        elif args.config:
            self.start(args)
        else:
            self.parser.print_help()
            sys.exit(0)
