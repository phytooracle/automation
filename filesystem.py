import pdb # pdb.set_trace()
import os, sys
import subprocess as sp
import shutil
import glob

def run_filexfer_node_commands(cmds, cwd)
    print(':: Using data transfer node.')
    _a = [f"'&& {x}'" for x in cmds
    command_string = " ".join(_b)
    breakpoint()
    sp.call(f"ssh filexfer 'cd {cwd}' '&& {cmd}' '&& exit'", shell=True)

def make_dir(dir_path_to_make, hpc=True):
    global args
    cmd = f'imkdir -p {dir_path_to_make}'
    if args.hpc: 

    else:
        
        cmd1 = f'imkdir -p {irods_output_path}'
        sp.call(cmd1, shell=True)

