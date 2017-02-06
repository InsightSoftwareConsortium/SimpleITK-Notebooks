library(SimpleITK)

shrink_decorator <- function(size) {
    inner_decorator <- function(func) {
        func_and_resize <- function(...) {
            shrink_filter <- ShrinkImageFilter()
            shrink_filter$SetShrinkFactor(size)
            return(shrink_filter$Execute(func(...)))
        }
        return(func_and_resize)
    }
    return(inner_decorator)
}

if("" != Sys.getenv("SIMPLE_ITK_MEMORY_CONSTRAINED_ENVIRONMENT")) { 
  ReadImage <- shrink_decorator(4)(SimpleITK::ReadImage)
}

