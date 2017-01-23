#
# If we are in a continous testing environment that is memory constrained,
# for instance CircleCI which limits memory to 4Gb. We override the ReadImage
# function using a decorator that also resamples the image.
#

import os
import SimpleITK as sitk

def ReadImageDecorator(original_read_image):
    def read_and_resize(*args, **kwargs):
        shrink_filter = sitk.ShrinkImageFilter()
        shrink_filter.SetShrinkFactor(4)
        return shrink_filter.Execute(original_read_image(*args, **kwargs))
    return read_and_resize

if os.environ.get('SIMPLE_ITK_MEMORY_CONSTRAINED_ENVIRONMENT'):
    sitk.ReadImage = ReadImageDecorator(sitk.ReadImage)

