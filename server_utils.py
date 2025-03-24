import pdb # pdb.set_trace()
import os, sys
import subprocess as sp
import shutil
import glob
import tarfile
import requests

hpc = False


def distro_name():
    pairs = {}
    with open("/etc/os-release") as myfile:
        for line in myfile:
            if '=' in line:
                name, var = line.partition("=")[::2]
                pairs[name] = var.strip().replace("\"","")
    if "NAME" in pairs:
        return pairs['NAME']
    else:
        raise Exception(f"Can't determine distro from /etc/os-release")


def run_filexfer_node_commands(cmds):
    global hpc
    print(f':: Using data transfer node to download file.')
    _a = [f"&& {x}" for x in cmds]
    command_string = " ".join(_a)
    cwd = os.getcwd()
    cmd = f"ssh -o 'ServerAliveInterval 30' -o 'ServerAliveCountMax 5760' filexfer 'cd {cwd} {command_string} && exit'"
    sp.run(cmd, shell=True)

def make_dir(dir_path_to_make):
    cmd = f'mkdir -p {dir_path_to_make}'
    sp.call(cmd, shell=True)


def get_filenames_in_dir_from_cyverse(irods_dir_path):
    global hpc
    if hpc:
        cmd = f"ssh filexfer 'ils {irods_dir_path}'"
        cyverse_ls = sp.run(cmd, shell=True, stdout=sp.PIPE).stdout
    else:
        cyverse_ls = sp.run(["ils", irods_dir_path], stdout=sp.PIPE).stdout
    dir_files = [x.strip() for x in cyverse_ls.decode('utf-8').splitlines()][1:]
    return dir_files


def download_file_from_cyverse(irods_path, check_exists=False):
    """
    Download the single file given by irods_path to the current working directory.
    """
    global hpc
    cmd = f'iget -PVT {os.path.join(irods_path)}'

    if check_exists and not check_if_file_exists_on_cyverse(irods_path):
        print(f"ERROR: File doesn't exist on cyverse: {irods_path}")
        raise Exception(f"File doesn't exist on cyverse: {irods_path}")
    
    if hpc: 
        run_filexfer_node_commands([cmd])
    else:
        print(f":: Using current node/system to download file")
        sp.call(cmd, shell=True)
   

def download_files_from_cyverse(files, experiment, force_overwrite=False):
    """
    files: a list of files with full paths to their location on CyVerse.

    Download everything in files if it isn't found locally*
    Note this method assumes the CyVerse paths in files are valid.

    * unless force_overwrite is True, in which case download everything
    no matter what.
    """
    for file_path in files:
        # print(file_path)
        filename = os.path.basename(file_path)

        print(f"Looking for local copy of {filename}...")
        if not os.path.isfile(filename):
            print(f"    We need to get: {file_path}")
            download_file_from_cyverse(file_path)
        else:
            print(f"FOUND")
            if force_overwrite:
                print(f"    ... but we're going to overwrite it: {file_path}")
                download_file_from_cyverse(file_path)


def untar_files(local_files, force_overwrite=False):
    """
    local_files: a mixed list of file types

    If a file in local_files has an extension found in the `extensions` list,
    attempt to uncompress/untar it unless it's already been uncompressed.

    Notes:

    (1) We expect tarballs to contain a single directory full of files.  If
    that's not what we find, this function throws an exception.

    """

    extensions = ['.tar', '.tgz', '.tar.gz']
    
    for filename in local_files:
        if any(x in filename for x in extensions):
            file = tarfile.open(filename)
            print(f"untar_files() is examining {filename} to see if it's been untared before.")
            #if not file.getmembers()[0].isdir():
                #raise Exception(f"   tarball doesn't start with a directory")
            tarball_first_file = file.getmembers()[0].name
            if os.path.isdir(tarball_first_file):
                print(f"   Looks like tarball has been unarchived before.  Skipping")
            else:
                print(f"Unarchiving: {filename}")
                file.extractall(".")
                file.close()


def check_if_file_exists_on_cyverse(irods_path):
    """
    Check if a file was downloaded by checking if it exists in the current
    working directory.
    """
    found = False

    # parse irods path to get directory and filename
    irods_dir = os.path.dirname(irods_path)
    filename = os.path.basename(irods_path)
    cwd = os.getcwd()

    global hpc

    if hpc:
        print(':: Using data transfer node to check if file exists on cyverse.')
        cmd = f"ssh filexfer 'cd {cwd} && icd {irods_dir} && ils > filexfer_output.txt && exit'"
        sp.run(cmd, shell=True)

    else:
        print(':: Using local irods to check if file exists on cyverse.')
        sp.run(f"cd {cwd} && icd {irods_dir} && ils > filexfer_output.txt", shell=True)
    
    # read output file and check if file exists
    with open("filexfer_output.txt", "r") as f:
        for line in f:
            if filename in line:
                found = True
                break
    
    sp.run("rm filexfer_output.txt", shell=True)

    return found
