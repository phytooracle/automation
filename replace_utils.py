#!/usr/bin/env python3
"""
Author : eg
Date   : 2021-10-19
Purpose: Rock the Casbah
"""

import argparse
import os
import sys

# --------------------------------------------------
def replace_file_one(line2replace, date):
    f = open("process_one_set.sh", 'r')
    fdata = f.read()
    f.close()

    nline = fdata.replace(line2replace, date)
    f = open("process_one_set.sh", 'w')
    f.write(nline)
    f.close()

# --------------------------------------------------
def replace_file_two(line2replace, date):
    f = open("process_one_set2.sh", 'r')
    fdata = f.read()
    f.close()

    nline = fdata.replace(line2replace, date)
    f = open("process_one_set2.sh", 'w')
    f.write(nline)
    f.close()


# --------------------------------------------------
def replace_file_three(line2replace, date):
    f = open("process_one_set3.sh", 'r')
    fdata = f.read()
    f.close()

    nline = fdata.replace(line2replace, date)
    f = open("process_one_set3.sh", 'w')
    f.write(nline)
    f.close()