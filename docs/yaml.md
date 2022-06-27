# YAML file 
The YAML file can be edited to run any container. Below is a list of important keys to ensure the pipeline runs correctly:
## Tags 
Tags which will are used for documentation purposes. They include descriptions of the processing pipeline.
* [tags]
  * [pipeline] | Name of test
  * [description] | Version of test
  * [notes] | General notes of test
  * [rubby] | Name of user running pipeline
  * [sensor] | Name of sensor being processed
  * [season] | Season number (i.e. 10, 11, 12, etc)
  * [season_name] | Season name as found on CyVerse (i.e. season_11_sorghum_yr_2020)
  * [slack_notifications] | Send out Slack notifications
## Modules 
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

## Workload manager (SLURM)
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

## Paths 
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
