import SimpleITK as sitk
import matplotlib.pyplot as plt
import ipywidgets as widgets
from IPython.display import display
import numpy as np

class RegistrationPointDataAquisition(object):
    """
    This class provides a GUI for localizing corresponding points in two images, and for evaluating registration results using a linked cursor 
    approach, user clicks in one image and the corresponding point is added to the other image.
    """

    def __init__(self, fixed_image, moving_image, fixed_window_level= None, moving_window_level= None, figure_size=(10,8), known_transformation=None):
        self.fixed_image = fixed_image
        self.fixed_npa, self.fixed_min_intensity, self.fixed_max_intensity = self.get_window_level_numpy_array(self.fixed_image, fixed_window_level)
        self.moving_image = moving_image
        self.moving_npa, self.moving_min_intensity, self.moving_max_intensity = self.get_window_level_numpy_array(self.moving_image, moving_window_level)
        self.fixed_point_indexes = []
        self.moving_point_indexes = []
        self.click_history = [] # Keep a history of user point localizations, enabling undo of last localization.
        self.known_transformation = known_transformation # If the transformation is valid (not None) then corresponding points are automatically added.
        self.text_and_marker_color = 'red'

        # Create a figure with two axes for the fixed and moving images.        
        self.fig, axes = plt.subplots(1,2,figsize=figure_size)
        #self.fig.canvas.set_window_title('Registration Points Acquisition') 
        self.fixed_axes = axes[0]
        self.moving_axes = axes[1]        
        # Connect the mouse button press to the canvas (__call__ method is the invoked callback).
        self.fig.canvas.mpl_connect('button_press_event', self)

        ui = self.create_ui()
        
        # Display the data and the controls, first time we display the images is outside the "update_display" method
        # as that method relies on the previous zoom factor which doesn't exist yet.
        self.fixed_axes.imshow(self.fixed_npa[self.fixed_slider.value,:,:],
                               cmap=plt.cm.Greys_r,
                               vmin=self.fixed_min_intensity,
                               vmax=self.fixed_max_intensity)
        self.moving_axes.imshow(self.moving_npa[self.moving_slider.value,:,:],
                                cmap=plt.cm.Greys_r,
                                vmin=self.moving_min_intensity,
                                vmax=self.moving_max_intensity)
        self.update_display()
        display(ui)
    
    def create_ui(self):
        # Create the active UI components. Height and width are specified in 'em' units. This is
        # a html size specification, size relative to current font size.
        self.viewing_checkbox = widgets.RadioButtons(description= 'Interaction mode:', 
                                                     options= ['edit', 'view'], 
                                                     value = 'edit')

        self.clearlast_button = widgets.Button(description= 'Clear Last', 
                                               width= '7em', 
                                               height= '3em')
        self.clearlast_button.on_click(self.clear_last)

        self.clearall_button = widgets.Button(description= 'Clear All', 
                                              width= '7em', 
                                              height= '3em') 
        self.clearall_button.on_click(self.clear_all)

        self.fixed_slider = widgets.IntSlider(description='fixed image z slice:',
                                              min=0,
                                              max=self.fixed_npa.shape[0]-1, 
                                              step=1, 
                                              value = int((self.fixed_npa.shape[0]-1)/2),
                                              width='20em')
        self.fixed_slider.on_trait_change(self.update_display,'value')
        
        self.moving_slider = widgets.IntSlider(description='moving image z slice:', 
                                               min=0,
                                               max=self.moving_npa.shape[0]-1, 
                                               step=1, 
                                               value = int((self.moving_npa.shape[0]-1)/2),
                                               width='19em')
        self.moving_slider.on_trait_change(self.update_display,'value')

        # Layout of UI components. This is pure ugliness because we are not using a UI toolkit. Layout is done
        # using the box widget and padding so that the visible UI components are spaced nicely.
        bx0 = widgets.Box(padding=7, children=[self.fixed_slider, self.moving_slider])
        bx1 = widgets.Box(padding=7, children = [self.viewing_checkbox])
        bx2 = widgets.Box(padding = 15, children = [self.clearlast_button])
        bx3 = widgets.Box(padding = 15, children = [self.clearall_button])
        return widgets.HBox(children=[widgets.HBox(children=[bx1, bx2, bx3]),bx0])
        
    def get_window_level_numpy_array(self, image, window_level):
        """
        Get the numpy array representation of the image and the min and max of the intensities
        used for display.
        """
        npa = sitk.GetArrayFromImage(image)
        if not window_level:
            return npa, npa.min(), npa.max()
        else:
            return npa, window_level[1]-window_level[0]/2.0, window_level[1]+window_level[0]/2.0 

    def update_display(self):
        """
        Display the two images based on the slider values and the points which are on the 
        displayed slices.
        """
        # We want to keep the zoom factor which was set prior to display, so we log it before
        # clearing the axes.
        fixed_xlim = self.fixed_axes.get_xlim()
        fixed_ylim = self.fixed_axes.get_ylim()
        moving_xlim = self.moving_axes.get_xlim()
        moving_ylim = self.moving_axes.get_ylim()        
        
        # Draw the fixed image in the first subplot and the localized points.
        self.fixed_axes.clear()
        self.fixed_axes.imshow(self.fixed_npa[self.fixed_slider.value,:,:],
                               cmap=plt.cm.Greys_r, 
                               vmin=self.fixed_min_intensity,
                               vmax=self.fixed_max_intensity)
        # Positioning the text is a bit tricky, we position relative to the data coordinate system, but we
        # want to specify the shift in pixels as we are dealing with display. We therefore (a) get the data 
        # point in the display coordinate system in pixel units (b) modify the point using pixel offset and
        # transform back to the data coordinate system for display.
        text_x_offset = -10
        text_y_offset = -10
        for i, pnt in enumerate(self.fixed_point_indexes):
            if pnt[2] == self.fixed_slider.value:
                self.fixed_axes.scatter(pnt[0], pnt[1], s=90, marker='+', color=self.text_and_marker_color)
                # Get point in pixels.
                text_in_data_coords = self.fixed_axes.transData.transform([pnt[0],pnt[1]]) 
                # Offset in pixels and get in data coordinates.
                text_in_data_coords = self.fixed_axes.transData.inverted().transform((text_in_data_coords[0]+text_x_offset, text_in_data_coords[1]+text_y_offset))
                self.fixed_axes.text(text_in_data_coords[0], text_in_data_coords[1], str(i), color=self.text_and_marker_color)                               
        self.fixed_axes.set_title('fixed image - localized {0} points'.format(len(self.fixed_point_indexes)))   
        self.fixed_axes.set_axis_off()
        
        # Draw the moving image in the second subplot and the localized points.
        self.moving_axes.clear()
        self.moving_axes.imshow(self.moving_npa[self.moving_slider.value,:,:],
                                cmap=plt.cm.Greys_r,
                                vmin=self.moving_min_intensity,
                                vmax=self.moving_max_intensity)        
        for i, pnt in enumerate(self.moving_point_indexes):
            if pnt[2] == self.moving_slider.value:
                self.moving_axes.scatter(pnt[0], pnt[1], s=90, marker='+', color=self.text_and_marker_color)
                text_in_data_coords = self.moving_axes.transData.transform([pnt[0],pnt[1]])
                text_in_data_coords = self.moving_axes.transData.inverted().transform((text_in_data_coords[0]+text_x_offset, text_in_data_coords[1]+text_y_offset))
                self.moving_axes.text(text_in_data_coords[0], text_in_data_coords[1], str(i), color=self.text_and_marker_color)
        self.moving_axes.set_title('moving image - localized {0} points'.format(len(self.moving_point_indexes)))
        self.moving_axes.set_axis_off()

        # Set the zoom factor back to what it was before we cleared the axes, and rendered our data.
        self.fixed_axes.set_xlim(fixed_xlim)
        self.fixed_axes.set_ylim(fixed_ylim)
        self.moving_axes.set_xlim(moving_xlim)
        self.moving_axes.set_ylim(moving_ylim)        

        self.fig.canvas.draw_idle()
    
    def clear_all(self, button):
        """
        Get rid of all the data.
        """
        del self.fixed_point_indexes[:]
        del self.moving_point_indexes[:]
        del self.click_history[:]
        self.update_display()
        
    def clear_last(self, button):
        """
        Remove last point or point-pair addition (depends on whether the interface is used for localizing point pairs or
        evaluation of registration).
        """
        if self.click_history:
            if self.known_transformation:
                self.click_history.pop().pop()
            self.click_history.pop().pop()
            self.update_display()
        
    def get_points(self):
        """
        Get the points in the image coordinate systems.
        """
        if(len(self.fixed_point_indexes) != len(self.moving_point_indexes)):
            raise Exception('Number of localized points in fixed and moving images does not match.') 
        fixed_point_list = [self.fixed_image.TransformContinuousIndexToPhysicalPoint(pnt) for pnt in self.fixed_point_indexes]
        moving_point_list = [self.moving_image.TransformContinuousIndexToPhysicalPoint(pnt) for pnt in self.moving_point_indexes]
        return fixed_point_list, moving_point_list
                    
    def __call__(self, event):
        """
        Callback invoked when the user clicks inside the figure.
        """
        # We add points only in 'edit' mode. If the spatial transformation between the two images is known, self.known_transformation was set,
        # then every button_press_event will generate a point in each of the images. Finally, we enforce that all points have a corresponding
        # point in the other image by not allowing the user to add multiple points in the same image, they have to add points by switching between
        # the two images.
        if self.viewing_checkbox.value == 'edit':
            if event.inaxes==self.fixed_axes:
                if len(self.fixed_point_indexes) - len(self.moving_point_indexes)<=0:                            
                    self.fixed_point_indexes.append((event.xdata, event.ydata, self.fixed_slider.value))
                    self.click_history.append(self.fixed_point_indexes)
                    if self.known_transformation:
                        moving_point_physical = self.known_transformation.TransformPoint(self.fixed_image.TransformContinuousIndexToPhysicalPoint(self.fixed_point_indexes[-1]))
                        moving_point_indexes = self.moving_image.TransformPhysicalPointToIndex(moving_point_physical)
                        self.moving_point_indexes.append(moving_point_indexes)
                        self.click_history.append(self.moving_point_indexes)
                        if self.moving_slider.max>=moving_point_indexes[2] and self.moving_slider.min<=moving_point_indexes[2]:
                            self.moving_slider.value = moving_point_indexes[2]
                    self.update_display()
            if event.inaxes==self.moving_axes:
                if len(self.moving_point_indexes) - len(self.fixed_point_indexes)<=0:
                    self.moving_point_indexes.append((event.xdata, event.ydata, self.moving_slider.value))
                    self.click_history.append(self.moving_point_indexes)
                    if self.known_transformation:
                        inverse_transform = self.known_transformation.GetInverse()
                        fixed_point_physical = inverse_transform.TransformPoint(self.moving_image.TransformContinuousIndexToPhysicalPoint(self.moving_point_indexes[-1]))
                        fixed_point_indexes = self.fixed_image.TransformPhysicalPointToIndex(fixed_point_physical)
                        self.fixed_point_indexes.append(fixed_point_indexes)
                        self.click_history.append(self.fixed_point_indexes)
                        if self.fixed_slider.max>=fixed_point_indexes[2] and self.fixed_slider.min<=fixed_point_indexes[2]:
                            self.fixed_slider.value = fixed_point_indexes[2]
                    self.update_display()                


class PointDataAquisition(object):
    
    def __init__(self, image, window_level= None, figure_size=(10,8)):
        self.image = image
        self.npa, self.min_intensity, self.max_intensity = self.get_window_level_numpy_array(self.image, window_level)
        self.point_indexes = []

        # Create a figure. 
        self.fig, self.axes = plt.subplots(1,1,figsize=figure_size)
        # Connect the mouse button press to the canvas (__call__ method is the invoked callback).
        self.fig.canvas.mpl_connect('button_press_event', self)

        ui = self.create_ui()
        
        # Display the data and the controls, first time we display the image is outside the "update_display" method
        # as that method relies on the previous zoom factor which doesn't exist yet.
        self.axes.imshow(self.npa[self.slice_slider.value,:,:],
                         cmap=plt.cm.Greys_r,
                         vmin=self.min_intensity,
                         vmax=self.max_intensity)
        self.update_display()
        display(ui)
    
    def create_ui(self):
        # Create the active UI components. Height and width are specified in 'em' units. This is
        # a html size specification, size relative to current font size.
        self.viewing_checkbox = widgets.RadioButtons(description= 'Interaction mode:', 
                                                     options= ['edit', 'view'], 
                                                     value = 'edit')

        self.clearlast_button = widgets.Button(description= 'Clear Last', 
                                               width= '7em', 
                                               height= '3em')
        self.clearlast_button.on_click(self.clear_last)

        self.clearall_button = widgets.Button(description= 'Clear All', 
                                              width= '7em', 
                                              height= '3em') 
        self.clearall_button.on_click(self.clear_all)

        self.slice_slider = widgets.IntSlider(description='image z slice:',
                                              min=0,
                                              max=self.npa.shape[0]-1, 
                                              step=1, 
                                              value = int((self.npa.shape[0]-1)/2),
                                              width='20em')
        self.slice_slider.on_trait_change(self.update_display,'value')
        
        # Layout of UI components. This is pure ugliness because we are not using a UI toolkit. Layout is done
        # using the box widget and padding so that the visible UI components are spaced nicely.
        bx0 = widgets.Box(padding=7, children=[self.slice_slider])
        bx1 = widgets.Box(padding=7, children = [self.viewing_checkbox])
        bx2 = widgets.Box(padding = 15, children = [self.clearlast_button])
        bx3 = widgets.Box(padding = 15, children = [self.clearall_button])
        return widgets.HBox(children=[widgets.HBox(children=[bx1, bx2, bx3]),bx0])
        
    def get_window_level_numpy_array(self, image, window_level):
        npa = sitk.GetArrayFromImage(image)
        if not window_level:
            return npa, npa.min(), npa.max()
        else:
            return npa, window_level[1]-window_level[0]/2.0, window_level[1]+window_level[0]/2.0 
    
    def update_display(self):
        # We want to keep the zoom factor which was set prior to display, so we log it before
        # clearing the axes.
        xlim = self.axes.get_xlim()
        ylim = self.axes.get_ylim()
        
        # Draw the image and localized points.
        self.axes.clear()
        self.axes.imshow(self.npa[self.slice_slider.value,:,:],
                         cmap=plt.cm.Greys_r, 
                         vmin=self.min_intensity,
                         vmax=self.max_intensity)
        # Positioning the text is a bit tricky, we position relative to the data coordinate system, but we
        # want to specify the shift in pixels as we are dealing with display. We therefore (a) get the data 
        # point in the display coordinate system in pixel units (b) modify the point using pixel offset and
        # transform back to the data coordinate system for display.
        text_x_offset = -10
        text_y_offset = -10
        for i, pnt in enumerate(self.point_indexes):
            if pnt[2] == self.slice_slider.value:
                self.axes.scatter(pnt[0], pnt[1], s=90, marker='+', color='yellow')
                # Get point in pixels.
                text_in_data_coords = self.axes.transData.transform([pnt[0],pnt[1]]) 
                # Offset in pixels and get in data coordinates.
                text_in_data_coords = self.axes.transData.inverted().transform((text_in_data_coords[0]+text_x_offset, text_in_data_coords[1]+text_y_offset))
                self.axes.text(text_in_data_coords[0], text_in_data_coords[1], str(i), color='yellow')                               
        self.axes.set_title('localized {0} points'.format(len(self.point_indexes)))
        self.axes.set_axis_off()
        

        # Set the zoom factor back to what it was before we cleared the axes, and rendered our data.
        self.axes.set_xlim(xlim)
        self.axes.set_ylim(ylim)

        self.fig.canvas.draw_idle()
    
    def add_point_indexes(self, point_index_data):
        self.validate_points(point_index_data)
        self.point_indexes.append(list(point_index_data))
        self.update_display()

    def set_point_indexes(self, point_index_data):
        self.validate_points(point_index_data)
        del self.point_indexes[:]
        self.point_indexes = list(point_index_data)
        self.update_display()

    def validate_points(self, point_index_data):
        for p in point_index_data:
            if p[0]>=self.npa.shape[2] or p[0]<0 or p[1]>=self.npa.shape[1] or p[1]<0 or p[2]>=self.npa.shape[0] or p[2]<0:
                raise ValueError('Given point (' + ', '.join(map(str,p)) + ') is outside the image bounds.')

    def clear_all(self, button):
        del self.point_indexes[:]
        self.update_display()
        
    def clear_last(self, button):
        if self.point_indexes:
            self.point_indexes.pop()
            self.update_display()
        
    def get_points(self):
        return [self.image.TransformContinuousIndexToPhysicalPoint(pnt) for pnt in self.point_indexes]

    def get_point_indexes(self):
        '''
        Return the point indexes, not the continous index we keep.
        '''
        # Round and then cast to int, just rounding will return a float
        return [tuple(map(lambda x: int(round(x)), pnt)) for pnt in self.point_indexes]


    def __call__(self, event):
        if self.viewing_checkbox.value == 'edit':
            if event.inaxes==self.axes:
                self.point_indexes.append((event.xdata, event.ydata, self.slice_slider.value))
                self.update_display()



class MultiImageDisplay(object):

    def __init__(self, image_list, axis=0, shared_slider=False, title_list=None, window_level_list= None, figure_size=(10,8)):

        self.get_window_level_numpy_array(image_list, window_level_list)
        if title_list:
            if len(image_list)!=len(title_list):
                raise ValueError('Title list and image list lengths do not match')
            self.title_list = list(title_list)

        # Our dynamic slice, based on the axis the user specifies
        self.slc = [slice(None)]*3
        self.axis = axis

        # Create a figure.
        self.fig, self.axes = plt.subplots(1,len(image_list),figsize=figure_size)
        if len(image_list)==1:
            self.axes = [self.axes]

        ui = self.create_ui(shared_slider)

        # Display the data and the controls, first time we display the image is outside the "update_display" method
        # as that method relies on the previous zoom factor which doesn't exist yet.
        for ax, npa, slider, min_intensity, max_intensity in zip(self.axes, self.npa_list, self.slider_list, self.min_intensity_list, self.max_intensity_list):
            self.slc[self.axis] = slice(slider.value, slider.value+1)
            # Need to use squeeze to collapse degenerate dimension (e.g. RGB image size 124 124 1 3)
            ax.imshow(np.squeeze(npa[self.slc]),
                      cmap=plt.cm.Greys_r,
                      vmin=min_intensity,
                      vmax=max_intensity)
        self.update_display()
        display(ui)

    def create_ui(self, shared_slider):
        # Create the active UI components. Height and width are specified in 'em' units. This is
        # a html size specification, size relative to current font size.
        ui = None

        if shared_slider:
            # Validate that all the images have the same size along the axis which we scroll through
            sz = self.npa_list[0].shape[self.axis]
            for npa in self.npa_list:
                       if npa.shape[self.axis]!=sz:
                           raise ValueError('Not all images have the same size along the specified axis, cannot share slider.')

            slider = widgets.IntSlider(description='image slice:',
                                      min=0,
                                      max=sz-1,
                                      step=1,
                                      value = int((sz-1)/2),
                                      width='20em')
            slider.on_trait_change(self.update_display,'value')
            self.slider_list = [slider]*len(self.npa_list)
            ui = widgets.Box(padding=7, children=[slider])
        else:
            self.slider_list = []
            for npa in self.npa_list:
                slider = widgets.IntSlider(description='image slice:',
                                           min=0,
                                           max=npa.shape[self.axis]-1,
                                           step=1,
                                           value = int((npa.shape[self.axis]-1)/2),
                                           width='20em')
                slider.on_trait_change(self.update_display,'value')
                self.slider_list.append(slider)
            ui = widgets.Box(padding=7, children=self.slider_list)
        return ui

    def get_window_level_numpy_array(self, image_list, window_level_list):
        self.npa_list = list(map(sitk.GetArrayFromImage, image_list))
        if not window_level_list:
            self.min_intensity_list = list(map(np.min, self.npa_list))
            self.max_intensity_list = list(map(np.max, self.npa_list))
        else:
            self.min_intensity_list = list(map(lambda x: x[1]-x[0]/2.0, window_level_list))
            self.max_intensity_list = list(map(lambda x: x[1]+x[0]/2.0, window_level_list))

    def update_display(self):

        # Draw the image(s)
        for ax, npa, title, slider, min_intensity, max_intensity in zip(self.axes, self.npa_list, self.title_list, self.slider_list, self.min_intensity_list, self.max_intensity_list):
            # We want to keep the zoom factor which was set prior to display, so we log it before
            # clearing the axes.
            xlim = ax.get_xlim()
            ylim = ax.get_ylim()

            self.slc[self.axis] = slice(slider.value, slider.value+1)
            ax.clear()
            # Need to use squeeze to collapse degenerate dimension (e.g. RGB image size 124 124 1 3)
            ax.imshow(np.squeeze(npa[self.slc]),
                      cmap=plt.cm.Greys_r,
                      vmin=min_intensity,
                      vmax=max_intensity)
            ax.set_title(title)
            ax.set_axis_off()

            # Set the zoom factor back to what it was before we cleared the axes, and rendered our data.
            ax.set_xlim(xlim)
            ax.set_ylim(ylim)

        self.fig.canvas.draw_idle()

