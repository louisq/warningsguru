# StaticGuru

This utility is used to link together commitguru, maven and TOIF in a 
pipeline that allows commits that have previously been statistically 
analysed.

*Note: This is experimental tool which is still under development*


## Prerequisites

This project makes use of data and calls on other tools to be able to 
generate it's data and present it. Please have these other applications
up and running before attempting to run staticguru

### Commit Guru

Commitguru is composed of two parts. The code analyser and the web view 
components. Each one of these components need to be installed individually.
Follow their respective documentations:

The following snapshots should be used with staticguru to ensure the 
proper functioning of the components


https://github.com/louisq/CAS_Web/tree/dev

https://github.com/louisq/CAS_CodeRepoAnalyzer/releases/tag/sg_cra161003

### TOIF

StaticGuru uses KDM Analytic's TOIF to run the static analysis tools. 
TOIF is an integration framework for static analysis tools that allow 
for their execution and consolidated reporting.

Install TOIF and follow instructions to install Jlint and Findbugs

Download and documentation: http://www.kdmanalytics.com/toif/download.html

GitHub: https://github.com/KdmAnalytics/toif/

### Python

StaticGuru is a python 2.7 application. Ensure that you have it installed
on your system and install the following libraries:

    pip install psycopg2
    pip install gitpython
    pip install lxml

### Others

You will also need the following on your system:
1. Maven
2. Git

## Setup & Configuration

The following fields need to be updated

 - [ ] COMMITGURU_REPOSITORY_PATH : Set the path to the directory where commitguru
 stores it's repositories
 - [ ] REPOSITORY_CACHE_PATH : Full path where staticguru will be storing 
 copy of repositories
 - [ ] DATABASE_SETTINGS : Configure DATABASE_HOST, DATABASE_NAME,
 DATABASE_USERNAME and DATABASE_PASSWORD as presented in the example
 configuration. The name of the directory shall be your local username
 where the script is being executed from
 - [ ] TOIF_EXECUTABLE : Full path to the TOIF instance
 
 The database will be created on the first run of StaticGuru

## Explanation of run

When StaticGuru will start up it will validate the version of the 
database. If it is determined that staticguru is not currently running
on the latest version it will be updated

It will then check to determine if any commitguru commits have not been 
previously analysed by staticguru. Commits are then checkout and if a pom
file is present staticguru will attempt to have Maven build the commit. 

During the build process TOIF will be called from the staticguru toif runner
which will run the static analysis on the files which have been modified.

The warnings are analysed to detemine which one are new. These result can 
then be presented as part of the modified commitguru CAS Web instance.

## Run

Run the following command to start the process. Upon execution it will 
initiate the build and analysis of the commits that have previously been
analysed by commitguru

    python toif_service.py
