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
    * [use] | Use notification system (True/False)
    * [channel] | Slack channel on which to post
    * [container] | Container to use for sending notifications
      * [simg_name] | Singularity image name
      * [dockerhub_path] | DockerHub path to the container
## Modules 
You can specify any number of modules. Each module runs a single container and generates corresponding outputs. 
* [modules]
  * [container] | Container to run the specific module
    * [simg_name] | Singularity image name
    * [dockerhub_path] | Dockerhub path to the container
  * [command] | Command used to run the container
  * [distribution_level] | Whether running pipeline using local or remote workers (options are: local, wq)
  * [file_level] | Experimental, advanced users only
  * [input_dir] | Initial input directory containing raw data (i.e. an input directory of alignment/west_downsampled would be specified as [alignment, west_downsampled])
  * [input_file] | String of characters shared by all input files (i.e. -west_0.ply)
  * [inputs] | List of input files per task (include if files are remote, remove if files are local)
  * [outputs] | List of output files per task. If an output is not included here, it will be deleted after processing.

## Workload manager (SLURM)
* [workload_manager] | Specifications for manager/worker nodes on an HPC system.
  * [account] | Account to use for remote workers on an HPC system 
  * [high_priority_settings]
    * [use] | Use high priority hours (True/False)
    * [qos_group] | QOS group to use for high priority hours (i.e. user_qos_dukepauli)
    * [partition] | Type of compute hours to use (i.e. "high_priority")
  * [standard_settings]
    * [use] | Use standard hours (True/False)
    * [parition] | Type of compute hours to use (i.e. "standard")
  * [job_name] | Name of the worker SLURM array jobs
  * [nodes] | Number of nodes to request in a single job submission (i.e. "1")
  * [number_worker_array] | Number of workers to run in a single job submission (i.e. "100", "300") 
  * [cores_per_worker] | Number of cores to request for each worker (i.e. "1", "5", "10")
  * [alt_cores_per_worker] | Alternate number of cores to request for each worker, this alternate number is used when the level of distribution changes (i.e. when moving from image distribution to plant level)
  * [time_minutes] | Maximum run time (minutes) for the job submission
  * [retries] | Number of times to retry processing of a failed task
  * [port] | Port number to use for the manager-worker framework. Port value of 0 indicates no preference, randomly select a port
  * [mem_per_core] | Amount of memory (GB) to request for each worker (i.e. "5" for Puma, "6" for Ocelote and El Gato)
  * [mananger_name] | Name of the workflow manager
  * [worker_timeout_seconds] | Maxmimum idle run time (seconds) for worker (i.e. "900" seconds)

## Paths 
* [paths]
  * [models] | CyVerse paths to machine learning models used during data processing
    * [detection] | CyVerse path to object detection model
    * [segmentation] | CyVerse path to segmentation model
  * [pipeline_outpath] | List of output directories which you want to save (i.e. [individual_plants_out])
  * [outpath_subdirs] | List of output subdirectories which you want to save (i.e. [segmentation_pointclouds, plant_reports])
  * [cyverse]
    * [upload_directories] | Upload directories to CyVerse (ADVANCED USERS ONLY)
      * [use] | Use upload directories approach
      * [directories_to_move] | List of directories to upload
      * [temp_directory] | Temporary local directory to store data during upload
    * [basename] | Root directory of raw data
    * [input]
      * [necessary_files] | Necessary files for data processing (i.e. [level_3/stereoTop/season_11_clustering.csv, level_0/necessary_files/gcp_season_11.txt])
      * [level] | Level of raw, input data
      * [subdir] | Subdirectory of raw, input data (OPTIONAL)
      * [prefix] | Prefix tag of raw data (OPTIONAL)
      * [suffix] | Suffix tag of raw data (OPTIONAL)
    * [output]
      * [level] | Level for processed data, path to where it will be uploaded onto CyVerse

## Summary of models used in YAML for various species
There are a number of models available on the datastore:
* [Lettuce]
  * /iplant/home/shared/phytooracle/season_10_lettuce_yr_2020/level_0/necessary_files/detecto_heatmap_lettuce_detection_weights.pth
  * /iplant/home/shared/phytooracle/season_10_lettuce_yr_2020/level_0/necessary_files/dgcnn_3d_model.pth
  * /iplant/home/shared/phytooracle/season_10_lettuce_yr_2020/level_0/necessary_files/model_weights_2021-01-14_flir_lid_10e.pth
  * /iplant/home/shared/phytooracle/season_10_lettuce_yr_2020/level_0/necessary_files/model_weights_flir_v3_full.pth
  * /iplant/home/shared/phytooracle/season_10_lettuce_yr_2020/level_0/necessary_files/model_weights.pth
* [Sorghum]
  * /iplant/home/shared/phytooracle/season_11_sorghum_yr_2020/level_0/model_weights_rgb_lid_100epochs.pth
  * /iplant/home/shared/phytooracle/season_11_sorghum_yr_2020/level_0/model_weights_sorghum_flir.pth
  * /iplant/home/shared/phytooracle/season_11_sorghum_yr_2020/level_0/model_weights_sorghum_rgb.pth
For a given season, it is necessary that the appropriate models for the given species (e.g., lettuce, sorghum) be used. For a given pipeline, not all models will be used. 

### RGB
* [Plant Detection]
  * Sorghum: /iplant/home/shared/phytooracle/season_11_sorghum_yr_2020/level_0/model_weights_sorghum_rgb.pth
  * Lettuce: /iplant/home/shared/phytooracle/season_10_lettuce_yr_2020/level_0/necessary_files/model_weights.pth
* [Segmentation]
  * Sorghum: Not used
  * Lettuce: Not used
* [Lid Detection]
  * Sorghum: /iplant/home/shared/phytooracle/season_11_sorghum_yr_2020/level_0/model_weights_rgb_lid_100epochs.pth	
  * Lettuce: /iplant/home/shared/phytooracle/season_11_sorghum_yr_2020/level_0/model_weights_rgb_lid_100epochs.pth

### FLIR
* [Plant Detection]
  * Sorghum: /iplant/home/shared/phytooracle/season_11_sorghum_yr_2020/level_0/model_weights_sorghum_flir.pth	
  * Lettuce: /iplant/home/shared/phytooracle/season_10_lettuce_yr_2020/level_0/necessary_files/model_weights_flir_v3_full.pth	
* [Segmentation]
  * Sorghum: Not used
  * Lettuce: Not used
* [Lid Detection]
  * Sorghum: /iplant/home/shared/phytooracle/season_10_lettuce_yr_2020/level_0/necessary_files/model_weights_2021-01-14_flir_lid_10e.pth	
  * Lettuce: /iplant/home/shared/phytooracle/season_10_lettuce_yr_2020/level_0/necessary_files/model_weights_2021-01-14_flir_lid_10e.pth	

### 3D - Level 1
* [Plant Detection]
  * Sorghum: Not used
  * Lettuce: Not used
* [Segmentation]
  * Sorghum: Not used
  * Lettuce: Not used
* [Lid Detection]
  * Sorghum: Not used
  * Lettuce: Not used

### 3D - Level 2
Prior to Season 12:
* [Plant Detection]
  * Sorghum: Not used
  * Lettuce: Not used
* [Segmentation]
  * Sorghum: Not used
  * Lettuce: Not used
* [Lid Detection]
  * Sorghum: Not used
  * Lettuce: Not used

From Season 12 onwards:
* [Plant Detection]
  * Sorghum: Contained within the Docker container
  * Lettuce: /iplant/home/shared/phytooracle/season_10_lettuce_yr_2020/level_0/necessary_files/detecto_heatmap_lettuce_detection_weights.pth 
* [Segmentation]
  * Sorghum: Contained within the Docker container
  * Lettuce: /iplant/home/shared/phytooracle/season_10_lettuce_yr_2020/level_0/necessary_files/dgcnn_3d_model.pth 
* [Lid Detection]
  * Sorghum: Not used
  * Lettuce: Not used

### 3D - Level 3
This was the final stage for seasons 10 and 11, but was not performed for season 12 onwards.
* [Plant Detection]
  * Sorghum: Not used
  * Lettuce: Not used
* [Segmentation]
  * Sorghum: Not used
  * Lettuce: Not used
* [Lid Detection]
  * Sorghum: Not used
  * Lettuce: Not used

### PSII
* [Plant Detection]
  * Sorghum: Not used
  * Lettuce: Not used
* [Segmentation]
  * Sorghum: Not used
  * Lettuce: Not used
* [Lid Detection]
  * Sorghum: Not used
  * Lettuce: Not used
