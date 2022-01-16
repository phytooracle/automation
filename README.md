# PhytoOracle | Modular, Scalable Phenomic Data Processing Pipeline
This is our general-use, distributed computing pipeline for phenomic data. The pipeline can be run on local or HPC resources--it is important to note that **Singularity is required** when using this pipeline on HPC systems. 

This distributed framework allows users to leverage hundreds to thousands of computing cores for parallel processing of large data processing tasks. Additionally, this pipeline can be run locally (see Modules section below). The pipeline is run using a YAML file, which specifies processing steps run by the pipeline wrapper script (```distributed_pipeline_wrapper.py```). Below is information regarding the YAML file.

## YAML file 
The YAML file can be edited to run any container. Below is a list of important keys to ensure the pipeline runs correctly:
### Tags 
Tags which will are used for documentation purposes. They include descriptions of the processing pipeline.
* [tags]
  * [pipeline] | Name of test
  * [description] | Version of test
  * [notes] | General notes of test
  * [rubby] | Name of user running pipeline
  * [sensor] | Name of sensor being processed
### Modules 
You can specify any number of modules. Each module runs a single container and generates corresponding outputs. 
* [modules]
  * [container][simg_name] | Singularity image name
  * [container][dockerhub_path] | Dockerhub path to the container
  * [command] | Command used to run the container
  * [distribution_level] | Whether running pipeline using local or remote workers. Options are [local, wq]
  * [file_level] | NA
  * [input_dir] | Initial input directory containing raw data
  * [input_file] | String of characters shared by all input files (i.e., -west_0.ply)
  * [inputs] | List of input files per task
  * [outputs] | List of output files per task. If an output is not included here, it will be deleted after processing

### Workload manager (SLURM)
* [account] | Account to use for remote workers on an HPC system 
* [parition] | Type of compute hours to use (windfall, standard, high_priority)
* [job_name] | Name of the SLURM job
* [nodes] | Number of nodes to request in a single job submission
* [number_tasks] | Number of tasks to run in a single job submission 
* [number_tasks_per_node] | Number of tasks to run on a single node
* [cores_per_worker] | Number of cores to request for each Workqueue worker
* [alt_cores_per_worker] | Alternate number of cores to request for each Workqueue worker, this alternate number is used when the level of distribution changes (i.e. when moving from image distribution to plant level)
* [time_minutes] | Maximum run time (minutes) for the job submission
* [retries] | Number of times to retry processing of a failed task
* [port] | Port number to use for the manager-worker framework. Port value of 0 indicates no preference
* [mem_per_cpu] | Amount of memory (GB) to request for each node (Workqueue worker)
* [mananger_name] | Name of the Makeflow manager
* [worker_timeout_seconds] | Maxmimum idle run time (seconds) for Workqueue worker

### Paths 
* [paths]
  * [pipeline_outpath]
    * [pointclouds] | Output path to point cloud data 
    * [dashboard] | Output path to visualizations (GIFs, etc)
  * [cyverse]
    * [input]
      * [basename] | Root directory of raw data
      * [subdir] | Subdirectory of raw data
      * [suffix] | Suffix tag of raw data
    * [output]
      * [base] | Root directory to upload data
      * [subdir] | Subdirectory in which to upload data

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

### Running on HPC cluster
#### Interactive node
The pipeline can use a data transfer node to download data, which speeds up processing. You must first launch an interactive node using the following command on UA HPC Puma: 
```
./interactive_node.sh
```

Once the resources are allocated, run the following command to process data:
```
./distributed_pipeline_wrapper.py -hpc -d 2020-01-22 -y yaml_files/example_machinelearning_workflow.yaml
```

Data will be downloaded and workflows will be launched. You view progress information for a specific workflow using the ```mf_monitor.sh``` script. For example, to view progress information for the first workflow, run:
```
./mf_monitor.sh 1
```

#### Non-interactive job submission
To submit a date for processing in a non-interactive node, run:
```shell
sbatch slurm_submission.sh "./distributed_pipeline_wrapper.py -hpc -d 2020-01-27 -y yaml_files/example_machinelearning_workflow.yaml" .
```

Make sure to change the account, partition as needed. 