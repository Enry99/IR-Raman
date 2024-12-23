'''
Argument parser for xphon command line interface.
'''

import argparse
from importlib import import_module

import xphon
from xphon.cli.command import CLICommandBase, CustomFormatter


def build_xphon_parser():
    '''
    Build the parser for the xphon command line interface.
    '''

    # main parser
    parser = argparse.ArgumentParser(
        prog='xphon',
        epilog=xphon.__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        allow_abbrev=False)
    parser.add_argument('-v', '--version',action='version',version=f'%(prog)s-{xphon.__version__}')
    parser.add_argument('-T', '--traceback',action='store_true',help='Print traceback on error')


    # subparsers
    subparsers = parser.add_subparsers(title='commands',dest='command')

    commands = [
        ('ir', 'xphon.cli.ir'),
        ('raman', 'xphon.cli.raman'),
        ('write', 'xphon.cli.write'),
        ('plot', 'xphon.cli.plot'),
        ('scancel', 'xphon.cli.scancel')
    ]

    for command, module_name in commands:
        cmd : CLICommandBase = import_module(module_name).CLICommand

        subparser = subparsers.add_parser(
                    command,
                    formatter_class=CustomFormatter,
                    help=cmd.__doc__.split('\n')[0],
                    description=cmd.__doc__)
        cmd.add_arguments(subparser)
        cmd.bind_function(subparser)

    return parser
