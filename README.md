# PhytoOracle Test Pipeline
This is a test pipeline for scanner3DTop (point cloud) data. The pipeline can be run on local or HPC resources-- **Singularity is required**. The pipeline is run using a YAML file, which is outlined below.

## YAML file 
The YAML file can be edited to run any container. Below is a list of important keys to ensure the pipeline runs correctly:
### Tags 
You can specify tags which will are used to identify distinct test outputs. 
* [tags]
  * [pipeline] | Name of test
  * [description] | Version of test
  * [notes] | General notes of test
### Modules 
You can specify any number of modules. Each module runs a single container and generates corresponding outputs. 
* [modules]
  * [container][simg_name] | Singularity image name
  * [container][dockerhub_path] | Dockerhub path to the container
  * [command] | Command used to run the container 

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
The script ```test_pipeline.py``` is used to run the pipeline. This script downloads and extracts bundled test data, runs containers, and bundles output data.

### Flags 
* -hpc --hpc | Download data using UA HPC data transfer node 
* -d --date | Test date to process (see the "Supported test datasets" section below for supported dates)
* -y --yaml | YAML file to use for processing 
  
### Supported test datasets
The following scanner3DTop test datasets are currently supported: 
* 2020-01-22
* 2020-02-16
* 2020-03-02

### Running on HPC cluster
The pipeline can use a data transfer node to download data, which speeds up processing. You must first launch an interactive node using the following command on UA HPC Puma: 
```
./interactive_node.sh
```

Once the resources are allocated, run the following command to process data:
```
./test_pipeline.py -hpc -d 2020-01-22 -y yaml_files/travis_test_polynomial_cropping.yaml
```
### Running on a local computer
The pipeline can run on any Linux environment. Run the following command:
To run the pipeline on a local computer, run the following command:
```
./test_pipeline.py -d 2020-01-22 -y yaml_files/travis_test_polynomial_cropping.yaml
```

## Dashboard generator

### NEW Dasboard (generate_dashboard.py)

This script will will find every pipeline 'run' (date and output_process_tag combinarions) and create pages for everything.  

From the same directory you ran `test_pipeline.py` do something like this...
```
python generate_dashboard.py
```


### DEPRECATED Dashboard (generate_dashboard_for_pipeline_output.py)

From the same directory you ran `test_pipeline.py` do something like this...
```
generate_dashboard_for_pipeline_output.py -d 2020-03-02 -t polynomial_cropping_dev
```

It will output `index_1.html` in the `2020-03-02/polynomial_cropping_dev/plant_reports` directory...

```
firefox 2020-03-02/polynomial_cropping_dev/plant_reports/index_1.html
```
