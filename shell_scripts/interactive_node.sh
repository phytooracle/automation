#!/bin/bash 
salloc --nodes=1 --mem-per-cpu=5GB --ntasks=94 --time=168:00:00 --job-name=phytooracle_manager --account=frost_lab --partition=standard
