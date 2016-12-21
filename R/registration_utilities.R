#
# Get a coronal slice with overlaid contour of the mask for the specific slice index in all temporal images.
#
temporal_coronal_with_overlay <- function(coronal_slice_index, images, masks, label, window_min, window_max)
{
    # Extract the 2D images and masks.
    slices <- lapply(images, function(img, slc) img[,slc,], slc=coronal_slice_index) 
    slice_masks <- lapply(masks, function(msk, slc, lbl) msk[,slc,]==lbl , slc=coronal_slice_index, lbl=label)   

    # Resample the image (linear interpolation) and mask (nearest neighbor interpolation) into an isotropic grid, 
    # required for display.
    original_spacing <- slices[[1]]$GetSpacing()
    original_size <- slices[[1]]$GetSize()
    min_spacing <- min(original_spacing)
    new_spacing <- c(min_spacing, min_spacing)
    new_size <- c(as.integer(round(original_size[1]*(original_spacing[1]/min_spacing))), 
                  as.integer(round(original_size[2]*(original_spacing[2]/min_spacing))))
    resampled_slices <- lapply(slices, function(slc, sz, spc) Resample(slc, sz, Transform(), 
                                                                       "sitkLinear", slc$GetOrigin(),
                                                                       spc, slc$GetDirection(), 0.0, 
                                                                       slc$GetPixelID()), sz=new_size, spc=new_spacing)
    resampled_slice_masks <- lapply(slice_masks, function(msk, sz, spc) Resample(msk, sz, Transform(), 
                                                                       "sitkNearestNeighbor", msk$GetOrigin(),
                                                                       spc, msk$GetDirection(), 0.0, 
                                                                       msk$GetPixelID()), sz=new_size, spc=new_spacing)

    # Create the overlay: cast the mask to expected label pixel type, and do the same for the image after
    # window-level, accounting for the high dynamic range of the CT.
    overlaid_slices <- mapply( function(slc, msk, win_min, win_max) LabelMapContourOverlay(Cast(msk, "sitkLabelUInt8"), 
                                                                    Cast(IntensityWindowing(slc,
                                                                                            windowMinimum=win_min, 
                                                                                            windowMaximum=win_max), 
                                                                         "sitkUInt8"), 
                                                                     opacity = 1,
                                                                     c(0,0), c(2,2)),
                                resampled_slices,
                                resampled_slice_masks, win_min=window_min, win_max=window_max)
    # Create the temporal slice, 3D volume representing 2D coronal+time    
    temporal_image <- Image(c(overlaid_slices[[1]]$GetSize(), length(overlaid_slices)), overlaid_slices[[1]]$GetPixelID())
    # Two subtle points: (1) to paste the 2D slice into the 3D volume we need to make it a 3D slice (JoinSeries),
    #                    (2) the Paste function uses SimpleITK indexing, requiring the seq()-1.
    invisible(mapply(function(slice, index) temporal_image<<- Paste(temporal_image, JoinSeries(slice), c(slice$GetSize(),1), c(0,0,0), c(0,0,index)),
                     overlaid_slices, seq(length(overlaid_slices))-1))

    return(temporal_image)
}

#
# Evaluate the quality of a registration (resulting transformation), given a set of corrosponding reference 
# points in the fixed and moving coordinate systems. Euclidean distance between T(p_fixed) and p_moving. 
#                    
registration_errors <- function(tx, reference_fixed_points, reference_moving_points)
{
  transformed_fixed_points <- apply(reference_fixed_points, 1, 
                                    function(pnt,transform) transform$TransformPoint(pnt),transform=tx) 
  return(sqrt(colSums((transformed_fixed_points - t(as.matrix(reference_moving_points)))^2)))
}
