# PhytoOracle | Modular, Scalable Phenomic Data Processing Pipeline
This is our general-use, distributed computing pipeline for phenomic data. The pipeline can be run on local or HPC resources--it is important to note that **Singularity is required** when using this pipeline on HPC systems. 

This distributed framework allows users to leverage hundreds to thousands of computing cores for parallel processing of large data processing tasks. Additionally, this pipeline can be run locally (see Modules section below). The pipeline is run using a YAML file, which specifies processing steps run by the pipeline wrapper script (```distributed_pipeline_wrapper.py```). For more information on YAML key/value pairs, (click here)[]


## Running the pipeline
The script ```distributed_pipeline_wrapper.py``` is used to run the pipeline. This script downloads and extracts bundled test data, runs containers, and bundles output data.

### Flags 
* Required
  * -d, --date | Test date/s to process (in YYYY-MM-DD format, i.e."2020-01-22")
  * -y, --yaml | YAML file to use for processing
* Optional
  * -hpc, --hpc | Download data using UA HPC data transfer node
  * -l, --local_cores | Number of cores to use for local processing 
  * -sm, --seg_model | Segmentation model file path on CyVerse DataStore
  * -dm, --det_model | Detection model file path on CyVerse DataStore

### Running on Cloud cluster
On your Cloud VM, run the following command:
```
./distributed_pipeline_wrapper.py -d 2020-02-14 -y yaml_files/example_machinelearning_workflow.yaml
```

### Running on HPC cluster | interactive job submission
#### Interactive node
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

#### Running on HPC cluster | non-interactive job submission
To submit a date for processing in a non-interactive node, run:
```shell
sbatch shell_scripts/slurm_submission.sh <scan_date> <yaml_file>
```

For example: 
```shell
sbatch shell_scripts/slurm_submission.sh 2020-01-27 yaml_files/example_machinelearning_workflow.yaml
```

Make sure to change the account, partition as needed in the YAML file. 
