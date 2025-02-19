import pandas as pd
import numpy as np

# Function to calculate the error between the original curve and the approximation
def calculate_error(x, y, x_res, y_res):
    error = 0
    for i in range(len(x_res) - 1):
        # Find all points in the original slice_data between x_res[i] and x_res[i+1]
        mask = (x >= x_res[i]) & (x <= x_res[i + 1])
        x_segment = x[mask]
        y_segment = y[mask]
        
        # Linear interpolation for the resampled segment
        y_interp = np.interp(x_segment, [x_res[i], x_res[i + 1]], [y_res[i], y_res[i + 1]])
        
        # Calculate the maximum error in this segment
        segment_error = np.max(np.abs(y_segment - y_interp))
        if segment_error > error:
            error = segment_error
    return error

# Function to resample based on maximum error
def resample_based_on_error(x, y, max_error):
    resampled_indices = [0]  # Start with the first point
    i = 0
    while i < len(x) - 1:
        j = i + 1
        while j < len(x):
            # Check the error for the segment from x[i] to x[j]
            x_segment = x[i:j + 1]
            y_segment = y[i:j + 1]
            error = calculate_error(x, y, [x[i], x[j]], [y[i], y[j]])
            if error > max_error:
                # If error exceeds the threshold, add the previous point
                resampled_indices.append(j - 1)
                i = j - 1
                break
            j += 1
        if j >= len(x):
            break
    # Always include the last point
    if resampled_indices[-1] != len(x) - 1:
        resampled_indices.append(len(x) - 1)
    return x[resampled_indices], y[resampled_indices]