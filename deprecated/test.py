#!/usr/bin/env python3
"""
Author : eg
Date   : 2021-10-29
Purpose: Rock the Casbah
"""

import argparse
import os
import sys


# --------------------------------------------------
def get_args():
    """Get command-line arguments"""

    parser = argparse.ArgumentParser(
        description='Rock the Casbah',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('-l',
                        '--list',
                        nargs='+',
                        help='A named string argument',
                        metavar='list',
                        type=str)

    return parser.parse_args()


# --------------------------------------------------
def main():
    """Make a jazz noise here"""

    args = get_args()
    print(type(args.list))
    if set(['1','2']).issubset(args.list):
    # # # if '1' and '2' in args.list:
        print(f'Running workflow {print([i for i in [args.list]])}')

    if set(['3']).issubset(args.list): 
        print('WF3')


# --------------------------------------------------
if __name__ == '__main__':
    main()
