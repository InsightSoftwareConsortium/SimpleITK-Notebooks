#
# This script utilizes the existing Python download script via the R rPython package. To install the package, from the R prompt:
# install.packages("rPython") and then select the mirror from which to download it.
# Note that all of the feedback with regard to download progress goes to the console and is not visible in the notebook as is
# the case with the Python notebooks. 
#
if (!require(rPython)) {
    stop("rPython library not installed - run install.packages('rPython')\n")
}

# Find the python script directory, under the Utilities directory in the repository. We are assuming here that this file
# is sourced with chdir equals true [source('ddata.R', chdir=T)]
python_script_dir <- normalizePath("../Utilities")

python.exec("import os")
python.exec("import sys")
python.exec(paste("sys.path.append('", python_script_dir,"')",sep=""))
python.exec("from downloaddata import fetch_data, fetch_data_all")

fetch_data<-function(cache_file_name, verify=FALSE, cache_directory_name="../Data"){
    v<- if(verify) 'True' else 'False'
    python.exec(  paste("filename = fetch_data(cache_file_name='",cache_file_name,"',verify=",v,", cache_directory_name='",normalizePath(cache_directory_name),"')", sep=""))
    python.get("filename")
}

fetch_data_all<-function(output_directory, manifest_file, verify=TRUE){
    v<- if(verify) 'True' else 'False'
    python.exec(paste("fetch_data_all(output_directory='",output_directory,"',manifest_file='", manifest_file,"', verify=",v,")", sep=""))
}
