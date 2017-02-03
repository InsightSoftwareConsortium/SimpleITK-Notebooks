#
# If we are in a continous testing environment that is memory constrained,
# for instance CircleCI which limits memory to 4Gb. We override the ReadImage
# function using a decorator that also resamples the image.
#

import os
import SimpleITK as sitk

#
# A decorator which receives the size to shrink as a parameter.
#
def shrink_decorator(size):
    def inner_decorator(func):
        def func_and_resize(*args, **kwargs):
            shrink_filter = sitk.ShrinkImageFilter()
            shrink_filter.SetShrinkFactor(size)
            return shrink_filter.Execute(func(*args, **kwargs))
        return func_and_resize
    return inner_decorator

if os.environ.get('SIMPLE_ITK_MEMORY_CONSTRAINED_ENVIRONMENT'):
    sitk.ReadImage = shrink_decorator(4)(sitk.ReadImage)


