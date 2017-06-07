library(SimpleITK)

v1 <- function(object, Dwidth=grid::unit(5, "cm"))
{
  ncomp <- object$GetNumberOfComponents()
  if (ncomp == 3) {
      ## colour
      a <- as.array(object)
      a <- aperm(a, c(2,1,3))
  } else if (ncomp == 1) {
      a <- t(as.array(object))
  } else {
      stop("Only deals with 1 or 3 component images")
  }
  rg <- range(a)
  A <- (a-rg[1])/(rg[2]-rg[1])
  dd <- dim(a)
  sp <- object$GetSpacing()
  sz <- object$GetSize()
  worlddim <- sp*sz
  worlddim <- worlddim/worlddim[1]
  W <- Dwidth
  H <- Dwidth * worlddim[2]
  grid::grid.raster(A,default.units="mm", width=W, height=H)
}

# display 2D images inside the notebook (colour and greyscale)
show_inline <- function(object, Dwidth=grid::unit(5, "cm"), pad=FALSE)
{
  ncomp <- object$GetNumberOfComponents()
  if (ncomp == 3) {
      ## colour
      a <- as.array(object)
      a <- aperm(a, c(2, 1, 3))
  } else if (ncomp == 1) {
      if (pad) {
          object <- ConstantPad(object, c(1, 1), c(1, 1), 0)
      }
      a <- t(as.array(object))
  } else {
      stop("Only deals with 1 or 3 component images")
  }
  rg <- range(a)
  A <- (a - rg[1]) / (rg[2] - rg[1])
  dd <- dim(a)
  sp <- object$GetSpacing()
  sz <- object$GetSize()
  worlddim <- sp * sz
  worlddim <- worlddim / worlddim[1]
  W <- Dwidth
  H <- Dwidth * worlddim[2]
  WW <- grid::convertX(W*1.1, "inches", valueOnly=TRUE)
  HH <- grid::convertY(H*1.1, "inches", valueOnly=TRUE)
  ## here we set the display size
  ## Jupyter only honours the last setting for a cell, so
  ## we can't reset the original options. That needs to
  ## be done manually, using the "default.options" stored above
  ## Obvious point to do this is before plotting graphs
  options(repr.plot.width = WW, repr.plot.height = HH)
  grid::grid.raster(A, default.units="mm", width=W, height=H)
}

