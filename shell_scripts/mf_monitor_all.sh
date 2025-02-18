#!/bin/bash
export CCTOOLS_HOME=${HOME}/cctools-7.4.2-x86_64-centos7
export PATH=${CCTOOLS_HOME}/bin:$PATH
makeflow_monitor -H *.makeflowlog
