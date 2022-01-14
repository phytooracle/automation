#!/bin/bash 

export CCTOOLS_HOME=${HOME}/cctools-7.1.12-x86_64-centos7
export PATH=${CCTOOLS_HOME}/bin:$PATH
makeflow_monitor wf_file_${1}.json.makeflowlog
