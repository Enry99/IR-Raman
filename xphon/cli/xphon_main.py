#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys

from xphon import __version__
from xphon.cli.xphon_parser import build_xphon_parser

def main():
    '''
    Main entry point for the xphon command line interface.
    '''

    print(f'xphon version {__version__}')

    if len(sys.argv) == 1:
        print("No command provided. The program will now terminate.")
        return 1

    #parse the command line arguments
    parser = build_xphon_parser()
    args = parser.parse_args()

    #run the command
    try:
        args.func(args)
    except Exception as e:
        if args.traceback:
            raise
        else:
            print(f'Error: {e}')
            return 1

if __name__ == '__main__':
    sys.exit(main())
