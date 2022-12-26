import pdb # pdb.set_trace()
import os, sys
import subprocess as sp
import shutil
import glob
import tarfile

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
    print(':: Using data transfer node.')
    _a = [f"'&& {x}'" for x in cmds]
    command_string = " ".join(_a)
    cwd = os.getcwd()
    sp.call(f"ssh filexfer 'cd {cwd}' {command_string} '&& exit'", shell=True)

def make_dir(dir_path_to_make):
    cmd = f'mkdir -p {dir_path_to_make}'
    sp.call(cmd, shell=True)

def get_filenames_in_dir_from_cyverse(irods_dir_path):
    cyverse_ls = sp.run(["ils", irods_dir_path], stdout=sp.PIPE).stdout
    dir_files = [x.strip() for x in cyverse_ls.decode('utf-8').splitlines()][1:]
    return dir_files

def download_file_from_cyverse(irods_path):
    """
    Download the single file given by irods_path to the current working directory.
    """
    # check if the file exists on cyverse
    if not check_if_file_exists_on_cyverse(irods_path):
        raise Exception(f"File not found on cyverse: {irods_path}")
    else:
        print(f"Successfully downloaded file from cyverse: {irods_path}")

def download_files_from_cyverse(files, experiment, force_overwrite=False):
    """
    files: a list of files with full paths to their location on cyverse

    Download everything in files if it isn't found locally*

    * unless force_overwrite is True, in which case download everything
    no matter what.
    """

    for file_path in files:
        print(file_path)
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
    Check if the file exists on cyverse. Return True if it does, False if it doesn't.
    """
    global hpc
    cmd = f'iget -KPVT {os.path.join(irods_path)}'

    if hpc:
        print(f"Using filexfer node to download file")
        print(':: Using data transfer node.')
        _a = [f"'&& {x}'" for x in [cmd]]
        command_string = " ".join(_a)
        cwd = os.getcwd()
        result = sp.run(f"ssh filexfer 'cd {cwd}' {command_string} '&& exit'", capture_output=True, text=True, shell=True)
    
    else:
        print(f"Using current node/system to download file")
        result = sp.run(cmd, capture_output=True, text=True, shell=True)

    if "does not exist" in result.stderr:
        return False
    else:
        return True

   

