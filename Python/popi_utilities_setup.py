"""
Utilities specific to the POPI data: 
* The label values used in the masks that segment the CT into air/body/lung. 
* Function for reading the ground truth point data.
* Function for displaying a spatio-temporal coronal image with segmented label contour overlay.
* Function for displaying a coronal image with a set of segmentations (before and after registration).
"""

import SimpleITK as sitk
import matplotlib.pyplot as plt
import numpy as np

body_label = 0
air_label = 1
lung_label = 2    


def read_POPI_points(file_name):
    with open(file_name,'r') as fp:
        lines = fp.readlines()
        points = []
        # First line in the file is #X Y Z which we ignore.
        for line in lines[1:]:
            coordinates = line.split()
            if coordinates:
                points.append((float(coordinates[0]), float(coordinates[1]), float(coordinates[2])))
        return points
    
    
def overlay_binary_segmentation_contours(image, mask, window_min, window_max):
    """
    Given a 2D image and mask:
       a. resample the image and mask into isotropic grid (required for display).
       b. rescale the image intensities using the given window information.
       c. overlay the contours computed from the mask onto the image.
    """
    # Resample the image (linear interpolation) and mask (nearest neighbor interpolation) into an isotropic grid, 
    # required for display.
    original_spacing = image.GetSpacing()
    original_size = image.GetSize()
    min_spacing = min(original_spacing)
    new_spacing = [min_spacing, min_spacing]
    new_size = [int(round(original_size[0]*(original_spacing[0]/min_spacing))), 
                int(round(original_size[1]*(original_spacing[1]/min_spacing)))]
    resampled_img = sitk.Resample(image, new_size, sitk.Transform(), 
                                  sitk.sitkLinear, image.GetOrigin(),
                                  new_spacing, image.GetDirection(), 0.0, 
                                  image.GetPixelID())
    resampled_msk = sitk.Resample(mask, new_size, sitk.Transform(), 
                                  sitk.sitkNearestNeighbor, mask.GetOrigin(),
                                  new_spacing, mask.GetDirection(), 0.0, 
                                  mask.GetPixelID())

    # Create the overlay: cast the mask to expected label pixel type, and do the same for the image after
    # window-level, accounting for the high dynamic range of the CT.
    return sitk.LabelMapContourOverlay(sitk.Cast(resampled_msk, sitk.sitkLabelUInt8), 
                                       sitk.Cast(sitk.IntensityWindowing(resampled_img,
                                                                         windowMinimum=window_min, 
                                                                         windowMaximum=window_max), 
                                                 sitk.sitkUInt8), 
                                       opacity = 1, 
                                       contourThickness=[2,2])    
    
def display_coronal_with_overlay(temporal_slice, coronal_slice, images, masks, label, window_min, window_max):
    """
    Display a coronal slice from the 4D (3D+time) CT with a contour overlaid onto it. The contour is the edge of 
    the specific label.
    """
    img = images[temporal_slice][:,coronal_slice,:]
    msk = masks[temporal_slice][:,coronal_slice,:]==label

    overlay_img = overlay_binary_segmentation_contours(img, msk, window_min, window_max)    
    # Flip the image so that corresponds to correct radiological view.
    plt.imshow(np.flipud(sitk.GetArrayViewFromImage(overlay_img)))
    plt.axis('off')
    plt.show()

def display_coronal_with_label_maps_overlay(coronal_slice, mask_index, image, masks, label, window_min, window_max):
    """
    Display a coronal slice from a 3D CT with a contour overlaid onto it. The contour is the edge of 
    the specific label from the specific mask. Function is used to display results of transforming a segmentation
    using registration.
    """
    img = image[:,coronal_slice,:]
    msk = masks[mask_index][:,coronal_slice,:]==label

    overlay_img = overlay_binary_segmentation_contours(img, msk, window_min, window_max)
    # Flip the image so that corresponds to correct radiological view.
    plt.imshow(np.flipud(sitk.GetArrayViewFromImage(overlay_img)))
    plt.axis('off')
    plt.show()
