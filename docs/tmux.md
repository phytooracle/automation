# Background
PhytoOracle Automation (POA) fully automates phenomics data processing by handling raw data download, parallel data processing, and output data upload. To further facilitate automated data processing, an interactive node can be used to develop or test issues that arise. Interactive nodes must be run on tmux to enable persistent connection to the interactive node. 

# Install tmux

Connect to the UA HPC and access a file transfer node:

```bash
ssh filexfer
```

Download the installation script:

```bash
iget -KPVT /iplant/home/shared/phytooracle/software_installation/install_tmux.sh
```

Go back to the head node: 

```bash
exit
```

Change the file permissions and run the installation script:

```bash
chmod 755 install_tmux.sh && ./install_tmux.sh
```

Open your ~/.bashrc file: 

```bash
vim ~/.bashrc
```

Add the following file to your ~/.bashrc file:

```bash
alias tmux="$HOME/local/bin/tmux"
```

Save your changes, close the file, and source changes:

```bash
source ~/.bashrc
```

At this point, tmux should be installed. You can now run it:

```bash
tmux
```

For more information about tmux, [click here](https://tmuxcheatsheet.com/).