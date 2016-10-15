StaticGuru

This utility is used to link together commitguru, maven and TOIF in a 
pipeline that allows commits that have previously been statistically 
analysed.

*Note: This is experimental tool which is still under development*


# Prerequisites

This project makes use of data and calls on other tools to be able to 
generate it's data and present it. Please have these other applications
up and running before attempting to run staticguru

## Commit Guru

Commitguru is composed of two parts. The code analyser and the web view 
components. Each one of these components need to be installed individually.
Follow their respective documentations:

The following snapshots should be used with staticguru to ensure the 
proper functioning of the components


https://github.com/louisq/CAS_Web/releases/tag/sg_web161003
https://github.com/louisq/CAS_CodeRepoAnalyzer/releases/tag/sg_cra161003


# Configuration

The following fields need to be updated

 - [ ] REPOSITORY_PATH : Set the path to the directory where commitguru
 stores it's repositories
 - [ ] DATABASE_SETTINGS : Configure DATABASE_HOST, DATABASE_NAME,
 DATABASE_USERNAME and DATABASE_PASSWORD as presented in the example
 configuration. The name of the directory shall be your local username
 where the script is being executed from
 - [ ] TOIF_EXECUTABLE : Full path to the TOIF instance

# Explanation of run

When static guru will start up it will validate the version of the 
database. If it is determined that staticguru is not currently running
on the latest version it will be updated

TODO need to write the remainder of the explanation

# Run

Run the following command to start the process. Upon execution it will 
initiate the build and analysis of the commits that have previously been
analysed by commitguru

    python toif_service.py
