# <p align="center"><b>PhytoOracle | Modular, Scalable Phenomic Data Processing Pipeline</b></p>
<p align="center"><img src="docs/IMG_0102.PNG" height="200"></p>
PhytoOracle Automation (POA) is general-use, distributed computing pipeline for phenomic data. POA can be run on local or HPC resources and is capable of processing large phenomic datasets such as those collected by the Field Scanner at the University of Arizona's Maricopa Agricultural Center (pictured below, Photo: Jesse Rieser for The Wall Street Journal).

<p align="center"><img src="docs/gantry_wsj.jpg" height="300"></p>

POA's distributed framework, leveraging [CCTools' Makeflow and Workqueue](https://cctools.readthedocs.io/en/stable/), allows users to leverage hundreds to thousands of computing cores for parallel processing of large data processing tasks. The pipeline is run using a YAML file, which specifies processing steps run by the pipeline wrapper script (```distributed_pipeline_wrapper.py```).

## Required Dependencies
  * Linux-based computer, cluster, or server
  * [Singularity](https://github.com/apptainer/singularity/blob/master/INSTALL.md)
  * [iRODS](https://emmanuelgonz.github.io/posts/2022/01/irods-setup/)
  * [Python](https://www.python.org/downloads/)

## YAML File
For more information on YAML file key/value pairs, [click here](https://github.com/phytooracle/automation/blob/main/docs/yaml.md).

## Arguments/Flags
For more information on arguments/flags, [click here](https://github.com/phytooracle/automation/blob/main/docs/arguments.md).

## Required setup

### iRODS 

The POA Automation workflow requires iRODS. Follow the documentation [here](https://emmanuelgonz.github.io/posts/2022/01/irods-setup/) to install iRODS. 

### Data transfer node

If you are running POA on the UA HPC, you will need to set up SSH keys to gain access to data transfer nodes (DTNs). To get SSH keys set up, follow the steps below [here](https://github.com/phytooracle/automation/blob/main/docs/dtn.md)

## Running POA
The script ```distributed_pipeline_wrapper.py``` is used to run the pipeline. This script downloads and extracts bundled test data, runs containers, and bundles output data.

### Running on local computers/servers
On your computer/server, run the following command:
```
./distributed_pipeline_wrapper.py -d 2020-02-14 -y yaml_files/example_machinelearning_workflow.yaml
```

### Running on HPC clusters
There are three options when running POA on HPC clusters: interactive, non-interactice, and Cron.

#### Interactive
The pipeline can use a data transfer node to download data, which speeds up processing. You must first launch an interactive node using the following command on UA HPC Puma: 
```
./shell_scripts/interactive_node.sh
```

Once the resources are allocated, run the following command to process data:
```
./distributed_pipeline_wrapper.py -hpc -d 2020-02-14 -y yaml_files/example_machinelearning_workflow.yaml
```

Data will be downloaded and workflows will be launched. You view progress information for a specific workflow using the ```mf_monitor.sh``` script. For example, to view progress information for the first workflow, run:
```
./shell_scripts/mf_monitor.sh 1
```

#### Non-interactive 
To submit a date for processing in a non-interactive node, run:
```shell
sbatch shell_scripts/slurm_submission.sh <yaml_file>
```

For example: 
```shell
sbatch shell_scripts/slurm_submission.sh yaml_files/example_machinelearning_workflow.yaml
```

Make sure to change the `account` and `partition` values as needed in the YAML file. 

#### Cron
To schedule Cron jobs, follow the directions [here](https://github.com/phytooracle/automation/blob/main/docs/cron.md).