library(SimpleITK)

if("" != Sys.getenv("SIMPLE_ITK_MEMORY_CONSTRAINED_ENVIRONMENT")) { 
  ReadImage <- function(...) {
    shrink_filter <- ShrinkImageFilter()
    shrink_filter$SetShrinkFactor(2)
    return(shrink_filter$Execute(SimpleITK::ReadImage(...)))
  }
}

