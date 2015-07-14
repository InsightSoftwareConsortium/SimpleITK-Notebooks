import numpy as np
from scipy import linalg
import matplotlib.pyplot as plt
import SimpleITK as sitk

def load_RIRE_ground_truth(file_name):
    """
    Load the point sets defining the ground truth transformations for the RIRE 
    training dataset.

    Args: 
        file_name (str): RIRE ground truth file name. File format is specific to 
                         the RIRE training data, with the actual data expectd to 
                         be in lines 15-23.
    Returns:
    Two lists of tuples representing the points in the "left" and "right" 
    coordinate systems.
    """
    with open(file_name, 'r') as fp:
        lines = fp.readlines()
        l = []
        r = []
        # Fiducial information is in lines 15-22, starting with the second entry.
        for line in lines[15:23]:
            coordinates = line.split()
            l.append((float(coordinates[1]), float(coordinates[2]), float(coordinates[3])))
            r.append((float(coordinates[4]), float(coordinates[5]), float(coordinates[6])))
    return (l, r)


def absolute_orientation_m(points_in_left, points_in_right):
    """
    Absolute orientation using a matrix to represent the rotation. Solution is 
    due to S. Umeyama, "Least-Squares Estimation of Transformation Parameters 
    Between Two Point Patterns", IEEE Trans. Pattern Anal. Machine Intell., 
    vol. 13(4): 376-380.
    
    This is a refinement of the method proposed by Arun, Huang and Blostein, 
    ensuring that the rotation matrix is indeed a rotation and not a reflection. 
    
    Args:
        points_in_left (list(tuple)): Set of points corresponding to 
                                      points_in_right in a different coordinate system.
        points_in_right (list(tuple)): Set of points corresponding to 
                                       points_in_left in a different coordinate system.
        
    Returns:
        R,t (numpy.ndarray, numpy.array): Rigid transformation that maps points_in_left 
                                          onto points_in_right.
                                          R*points_in_left + t = points_in_right
    """
    num_points = len(points_in_left)
    dim_points = len(points_in_left[0])
    # Cursory check that the number of points is sufficient.
    if num_points<dim_points:      
        raise ValueError('Number of points must be greater/equal {0}.'.format(dim_points))

    # Construct matrices out of the two point sets for easy manipulation.
    left_mat = np.array(points_in_left).T
    right_mat = np.array(points_in_right).T
     
    # Center both data sets on the mean.
    left_mean = left_mat.mean(1)
    right_mean = right_mat.mean(1)
    left_M = left_mat - np.tile(left_mean, (num_points, 1)).T     
    right_M = right_mat - np.tile(right_mean, (num_points, 1)).T     
    
    M = left_M.dot(right_M.T)               
    U,S,Vt = linalg.svd(M)
    V=Vt.T
    # V * diag(1,1,det(U*V)) * U' - diagonal matrix ensures that we have a 
    # rotation and not a reflection.
    R = V.dot(np.diag((1,1,linalg.det(U.dot(V))))).dot(U.T) 
    t = right_mean - R.dot(left_mean) 
    return R,t


def generate_random_pointset(image, num_points):
    """
    Generate a random set (uniform sample) of points in the given image's domain.
    
    Args:
        image (SimpleITK.Image): Domain in which points are created.
        num_points (int): Number of points to generate.
        
    Returns:
        A list of points (tuples).
    """
    # Continous random uniform point indexes inside the image bounds.
    point_indexes = np.multiply(np.tile(image.GetSize(), (num_points, 1)), 
                                np.random.random((num_points, image.GetDimension())))
    pointset_list = point_indexes.tolist()
    # Get the list of physical points corresponding to the indexes.
    return [image.TransformContinuousIndexToPhysicalPoint(point_index) \
            for point_index in pointset_list]


def registration_errors(tx, reference_fixed_point_list, reference_moving_point_list, 
                        display_points = False):
  """
  Distances between points transformed by the given transformation and their
  location in another coordinate system. When the points are only used to 
  evaluate registration accuracy (not used in the registration) this is the 
  Target Registration Error (TRE).
  
  Args:
      tx (SimpleITK.Transform): The transform we want to evaluate.
      reference_fixed_point_list (list(tuple-like)): Points in fixed image 
                                                     cooredinate system.
      reference_moving_point_list (list(tuple-like)): Points in moving image 
                                                      cooredinate system.
      display_points (boolean): Display a 3D figure with lines connecting 
                                corresponding points.

  Returns:
   (mean, std, min, max, errors) (float, float, float, float, [float]): 
    TRE statistics and original TREs.
  """
  transformed_fixed_point_list = [tx.TransformPoint(p) for p in reference_fixed_point_list]

  errors = [linalg.norm(np.array(p_fixed) -  np.array(p_moving))
            for p_fixed,p_moving in zip(transformed_fixed_point_list, reference_moving_point_list)]
  if display_points:
      from mpl_toolkits.mplot3d import Axes3D
      import matplotlib.pyplot as plt
      fig = plt.figure()
      ax = fig.add_subplot(111, projection='3d')
   
      ax.scatter(list(np.array(transformed_fixed_point_list).T)[0],
                 list(np.array(transformed_fixed_point_list).T)[1],
                 list(np.array(transformed_fixed_point_list).T)[2],  
                 marker = 'o',
                 color = 'blue',
                 label = 'transformed fixed points')
                 
      ax.scatter(list(np.array(reference_moving_point_list).T)[0],
                 list(np.array(reference_moving_point_list).T)[1],
                 list(np.array(reference_moving_point_list).T)[2],  
                 marker = '^',
                 color = 'blue',
                 label = 'moving points')
      # Connect corresponding points with red line. 
      for points in zip(transformed_fixed_point_list, reference_moving_point_list):
        x,y,z = zip(*points)
        ax.plot(x,y,z, color='red')            
      
      ax.legend(bbox_to_anchor = [0.5,1.0], loc='center') 

  return (np.mean(errors), np.std(errors), np.min(errors), np.max(errors), errors) 

def display_scalar_images(image1_z_index, image2_z_index, image1, image2, 
                          min_max_image1= (), min_max_image2 = (), title1="", title2="", figure_size=(10,8)):
    """
    Display a plot with two slices from 3D images. Display of the specific z slices is side by side.

    Note: When using this function as a callback for interact in IPython notebooks it is recommended to 
          provide the min_max_image1 and min_max_image2 variables for intensity scaling. Otherwise we
          compute them internally every time this function is invoked (scrolling events).
    Args:
        image1_z_index (int): index of the slice we display for the first image.
        image2_z_index (int): index of the slice we display for the second image.
        image1 (SimpleITK.Image): first image.
        image2 (SimpleITK.Image): second image.
        min_max_image1 (Tuple(float, float)): image intensity values are linearly scaled to be in the given range. if
                                              the range is not provided by the caller, then we use the image's minimum 
                                              and maximum intensities.
        min_max_image2 (Tuple(float, float)): image intensity values are linearly scaled to be in the given range. if
                                              the range is not provided by the caller, then we use the image's minimum 
                                              and maximum intensities.
       title1 (string): title for first image plot.
       title2 (string): title for second image plot.
       figure_size (Tuple(float,float)): width and height of figure in inches.                               
    """

    intensity_statistics_filter = sitk.StatisticsImageFilter()
    if min_max_image1:
        vmin1 = min(min_max_image1)
        vmax1 = max(min_max_image1)
    else:
        intensity_statistics_filter.Execute(image1)
        vmin1 = intensity_statistics_filter.GetMinimum()
        vmax1 = intensity_statistics_filter.GetMaximum()
    if min_max_image2:
        vmin2 = min(min_max_image2)
        vmax2 = max(min_max_image2)
    else:
        intensity_statistics_filter.Execute(image2)
        vmin2 = intensity_statistics_filter.GetMinimum()
        vmax2 = intensity_statistics_filter.GetMaximum()
    
    plt.subplots(1,2,figsize=figure_size)
    
    plt.subplot(1,2,1)
    plt.imshow(sitk.GetArrayFromImage(image1[:,:,image1_z_index]),cmap=plt.cm.Greys_r, vmin=vmin1, vmax=vmax1)
    plt.title(title1)
    plt.axis('off')
    
    plt.subplot(1,2,2)
    plt.imshow(sitk.GetArrayFromImage(image2[:,:,image2_z_index]),cmap=plt.cm.Greys_r, vmin=vmin2, vmax=vmax2)
    plt.title(title2)
    plt.axis('off')


def display_images_with_alpha(image_z, alpha, image1, image2):
    """
    Display a plot with a slice from the 3D images that is alpha blended.
    It is assumed that the two images have the same physical charecteristics (origin,
    spacing, direction, size), if they do not, an exception is thrown.
    """
    img = (1.0 - alpha)*image1[:,:,image_z] + alpha*image2[:,:,image_z] 
    plt.imshow(sitk.GetArrayFromImage(img),cmap=plt.cm.Greys_r);
    plt.axis('off')
