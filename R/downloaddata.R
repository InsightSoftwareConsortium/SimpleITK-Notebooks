## R version of the python downloaddata.py functions.

if (!require(jsonlite)){
  stop("Please install jsonlite package - install.packages('jsonlite')")
}

get_midas_servers <- function()
{
  midas_servers <- c(
    # Data published by MIDAS
    "http://midas3.kitware.com/midas/api/rest?method=midas.bitstream.download&checksum=%(hash)&algorithm=%(algo)",
    # Data published by developers using git-gerrit-push.
    "http://www.itk.org/files/ExternalData/%(algo)/%(hash)",
    # Mirror supported by the Slicer community.
    "http://slicer.kitware.com/midas3/api/rest?method=midas.bitstream.download&checksum=%(hash)&algorithm=%(algo)"
  )
  ## fetch relevant environment variables
  EDOSV <- Sys.getenv("ExternalData_OBJECT_STORES")

  if (EDOSV != "") {
    local_object_stores <- strsplit(EDOSV, ";")
    local_object_stores <- paste0("file://", local_object_stores, "/MD5/%(hash)")
    midas_servers <- c(local_object_stores, midas_servers)
  }
  return(midas_servers)
}

fetch_data_one <- function(onefilename, output_directory, manifest_file, verify=TRUE, force=FALSE)
{
  manifest <- fromJSON(manifest_file)
  stopifnot(onefilename %in% names(manifest))

  cat("Fetching ", onefilename, "\n")

  outfile <- file.path(output_directory, onefilename)
  filedetails <- manifest[[onefilename]]
  this.md5sum <- filedetails$md5sum

  all_urls <- filedetails$url
  if (is.null(all_urls)) {
    all_urls <- gsub("%\\(hash\\)", this.md5sum, get_midas_servers())
    all_urls <- gsub("%\\(algo\\)", "md5", all_urls)
  }


  newdownload <- FALSE
  ## might be nicer to do this with RCurl, but lets
  ## avoid extra packages
  for (url in all_urls){
    if (force | (!file.exists(outfile))){
      dir.create(dirname(outfile), recursive = TRUE, showWarnings = FALSE)
      try(
        download.file(url, outfile, method="auto")
      )
      newmd5 <- tools::md5sum(outfile)
      if (is.na(newmd5)) {
        ## for some reason we get NAs for md5sum
        cat("md5sum is missing\n")
        cat(outfile, "\n")
        cat(url, "\n")
      }
      if (!is.na(newmd5) & (newmd5 == this.md5sum)) {
        newdownload=TRUE
        break
      } else {
        ## md5sum is wrong - problem downloading - skip to the next URL
        ## don't quit as the download.file function will save the error
        ## in the output file if there was a problem
        file.remove(outfile)
        warning(paste("Problem downloading", url, "Trying next site"))
      }
    }
  }

  if (!file.exists(outfile)) {
    msg <- paste("File", basename(outfile), "could not be found in any of the following locations\n", paste(all_urls, collapse="\n"))
    stop(msg)
  }

  if (!newdownload & verify){
    ## If the file was part of an archive then we don't verify it. These
    ## files are only verfied on download
    if (is.null(filedetails$archive) & (tools::md5sum(outfile) != this.md5sum)) {
      ## redownload if md5sum is incorrect
      fetch_data_one(onefilename, output_directory, manifest_file, verify, force=TRUE)
    }
  }

  is.tar <- function(fname)
  {
    ut <- function()
    {
      utils::untar(fname, list=TRUE, tar="internal")
      return(TRUE)
    }
    s <- tryCatch(ut(), error=function(e){return(FALSE)})
    return(s)
  }
  is.zip <- function(fname)
  {
    uz <- function()
    {
      utils::unzip(fname, list=TRUE, unzip="internal")
      return(TRUE)
    }
    s <- tryCatch(uz(), error=function(e){return(FALSE)})
    return(s)
  }

  ## unpack if an archive
  if (!is.null(filedetails$archive)) {
    tmpoutfile <- paste0(outfile, ".tmp")
    outdir=dirname(outfile)
    if (is.tar(outfile)) {
      file.rename(outfile, tmpoutfile)
      utils::untar(tmpoutfile, exdir=outdir)
      file.remove(tmpoutfile)
    } else if (is.zip(outfile)) {
      file.rename(outfile, tmpoutfile)
      utils::unzip(tmpoutfile, exdir=outdir)
      file.remove(tmpoutfile)
    }

  }
  return(outfile)
}

fetch_data_all <- function(output_directory, manifest_file, verify=TRUE)
{
  ## seem to be two options for json reading - rjson and jsonlite - randomly choose
  ## jsonlite to start with
  manifest <- fromJSON((manifest_file))

  lapply(names(manifest), fetch_data_one, output_directory=output_directory, manifest_file=manifest_file, verify=verify, force=FALSE)

}

fetch_data <- function(cache_file_name, verify=FALSE, cache_directory_name="../Data")
{
  cache_manifest_file <- file.path(cache_directory_name, "manifest.json")
  fetch_data_one(cache_file_name, cache_directory_name, cache_manifest_file, verify=verify)
}
