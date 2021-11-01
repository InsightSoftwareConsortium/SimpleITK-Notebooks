import numpy as np
import matplotlib.pyplot as plt
import SimpleITK as sitk

from IPython.display import clear_output
from scipy import linalg
from registration_utilities import registration_errors


# Callback we associate with the StartEvent, sets up our new data.
def metric_start_plot():
    global metric_values, multires_iterations
    global current_iteration_number

    metric_values = []
    multires_iterations = []
    current_iteration_number = -1


# Callback we associate with the EndEvent, do cleanup of data and figure.
def metric_end_plot():
    global metric_values, multires_iterations
    global current_iteration_number

    del metric_values
    del multires_iterations
    del current_iteration_number
    # Close figure, we don't want to get a duplicate of the plot latter on
    plt.close()


# Callback we associate with the IterationEvent, update our data and display
# new figure.
def metric_plot_values(registration_method):
    global metric_values, multires_iterations
    global current_iteration_number

    # Some optimizers report an iteration event for function evaluations and not
    # a complete iteration, we only want to update every iteration.
    if registration_method.GetOptimizerIteration() == current_iteration_number:
        return

    current_iteration_number = registration_method.GetOptimizerIteration()
    metric_values.append(registration_method.GetMetricValue())
    # Clear the output area (wait=True, to reduce flickering), and plot
    # current data.
    clear_output(wait=True)
    # Plot the similarity metric values.
    plt.plot(metric_values, "r")
    plt.plot(
        multires_iterations,
        [metric_values[index] for index in multires_iterations],
        "b*",
    )
    plt.xlabel("Iteration Number", fontsize=12)
    plt.ylabel("Metric Value", fontsize=12)
    plt.show()


# Callback we associate with the MultiResolutionIterationEvent, update the
# index into the metric_values list.
def metric_update_multires_iterations():
    global metric_values, multires_iterations
    multires_iterations.append(len(metric_values))


# Callback we associate with the StartEvent, sets up our new data.
def metric_and_reference_start_plot():
    global metric_values, multires_iterations, reference_mean_values
    global reference_min_values, reference_max_values
    global current_iteration_number

    metric_values = []
    multires_iterations = []
    reference_mean_values = []
    reference_min_values = []
    reference_max_values = []
    current_iteration_number = -1


# Callback we associate with the EndEvent, do cleanup of data and figure.
def metric_and_reference_end_plot():
    global metric_values, multires_iterations, reference_mean_values
    global reference_min_values, reference_max_values
    global current_iteration_number

    del metric_values
    del multires_iterations
    del reference_mean_values
    del reference_min_values
    del reference_max_values
    del current_iteration_number
    # Close figure, we don't want to get a duplicate of the plot latter on.
    plt.close()


# Callback we associate with the IterationEvent, update our data and display
# new figure.
def metric_and_reference_plot_values(registration_method, fixed_points, moving_points):
    global metric_values, multires_iterations, reference_mean_values
    global reference_min_values, reference_max_values
    global current_iteration_number

    # Some optimizers report an iteration event for function evaluations and not
    # a complete iteration, we only want to update every iteration.
    if registration_method.GetOptimizerIteration() == current_iteration_number:
        return

    current_iteration_number = registration_method.GetOptimizerIteration()
    metric_values.append(registration_method.GetMetricValue())
    # Compute and store TRE statistics (mean, min, max).
    current_transform = sitk.CompositeTransform(
        registration_method.GetInitialTransform()
    )
    current_transform.SetParameters(registration_method.GetOptimizerPosition())
    current_transform.AddTransform(registration_method.GetMovingInitialTransform())
    current_transform.AddTransform(
        registration_method.GetFixedInitialTransform().GetInverse()
    )
    mean_error, _, min_error, max_error, _ = registration_errors(
        current_transform, fixed_points, moving_points
    )
    reference_mean_values.append(mean_error)
    reference_min_values.append(min_error)
    reference_max_values.append(max_error)

    # Clear the output area (wait=True, to reduce flickering), and plot current data.
    clear_output(wait=True)
    # Plot the similarity metric values.
    plt.subplot(1, 2, 1)
    plt.plot(metric_values, "r")
    plt.plot(
        multires_iterations,
        [metric_values[index] for index in multires_iterations],
        "b*",
    )
    plt.xlabel("Iteration Number", fontsize=12)
    plt.ylabel("Metric Value", fontsize=12)
    # Plot the TRE mean value and the [min-max] range.
    plt.subplot(1, 2, 2)
    plt.plot(reference_mean_values, color="black", label="mean")
    plt.fill_between(
        range(len(reference_mean_values)),
        reference_min_values,
        reference_max_values,
        facecolor="red",
        alpha=0.5,
    )
    plt.xlabel("Iteration Number", fontsize=12)
    plt.ylabel("TRE [mm]", fontsize=12)
    plt.legend()

    # Adjust the spacing between subplots so that the axis labels don't overlap.
    plt.tight_layout()
    plt.show()
