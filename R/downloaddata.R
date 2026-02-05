#
# This script utilizes the existing Python download script via the R reticulate package. To install the package, from the R prompt:
# install.packages("reticulate") and then select the mirror from which to download it.
# Note that all of the feedback with regard to download progress goes to the console and is not visible in the notebook as is
# the case with the Python notebooks. 
#
if (!require(reticulate)) {
    stop("reticulate library not installed - run install.packages('reticulate')\n")
}

# Find the python script directory, under the Utilities directory in the repository. We are assuming here that this file
# is sourced with chdir equals true [source('ddata.R', chdir=T)]
python_script_dir <- normalizePath("../Utilities")

# Import Python's sys module and add the Utilities directory to the path
sys <- import("sys", convert = FALSE)

# The Python method returns None, suppress output using invisible() in R
invisible(sys$path$insert(0L, python_script_dir))

# Import the downloaddata module
downloaddata <- import("downloaddata")

fetch_data <- function(cache_file_name, verify=FALSE, cache_directory_name="../Data") {
    # Call Python's fetch_data function directly
    # reticulate automatically converts R logical to Python bool
    result <- downloaddata$fetch_data(
        cache_file_name = cache_file_name,
        verify = verify,
        cache_directory_name = normalizePath(cache_directory_name)
    )
    return(result)
}

fetch_data_all <- function(output_directory, manifest_file, verify=TRUE) {
    # Call Python's fetch_data_all function directly
    downloaddata$fetch_data_all(
        output_directory = output_directory,
        manifest_file = manifest_file,
        verify = verify
    )
}
