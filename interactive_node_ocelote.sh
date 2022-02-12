#!/bin/bash 
salloc --nodes=1 --mem-per-cpu=6gb --ntasks=28 --time=168:00:00 --job-name=phytooracle_manager --account=frost_lab --partition=standard
