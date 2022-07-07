#!/bin/bash
export CCTOOLS_HOME=${HOME}/cctools/
export PATH=${CCTOOLS_HOME}/bin:$PATH
makeflow_monitor wf_file_${1}.json.makeflowlog