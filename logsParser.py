# logsParser.py
import os
from io import StringIO
import numpy as np
import pandas as pd
import datetime as dt


def read_and_clean_log(file_path):
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()

        # Define the header
        header = "Time|         N|       LIR|     Table|       ST4|       ST3|       ST5|ST1 (flow T)|ST1 (flow H)|       SO1|       SO2|       SP5|       SP1|       SP4|       SP3|       SF1|       SP2|       SP8|      SP15|"

        # Flag to indicate the first occurrence of the header
        header_found = False
        cleaned_lines = []

        for line in lines:
            if line.strip() == header:
                if not header_found:
                    header_found = True
                    cleaned_lines.append(line.strip())
            else:
                cleaned_lines.append(line.strip())

        # Join the cleaned lines into a single string
        cleaned_data = "\n".join(cleaned_lines)

        # Load the cleaned data into a pandas DataFrame
        df = pd.read_csv(StringIO(cleaned_data), sep="|")

        # Correct any potential unnamed column issues
        df.columns = df.columns.str.strip()
        df.drop(columns=['Unnamed: 19'], errors='ignore', inplace=True)

        return df

    except PermissionError:
        print(f"Permission denied: Unable to access the file at {file_path}.")
    except FileNotFoundError:
        print(f"File not found: The file at {file_path} does not exist.")
    except Exception as e:
        print(f"An error occurred: {e} (empty log file)")
        return None
    
def read_and_clean_sensors(file_path):
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()

        # Define the header
        header = "Time|       LIR|    Raquel|    Bunker|  Filled B|       ST4|       ST3|       ST5|    Flow T|    Flow H|       SO1|       SO2|       SP5|       SP1|       SP4|       SP3|       SF1|       SP2|       SP8|      SP15|"

        # Flag to indicate the first occurrence of the header
        header_found = False
        cleaned_lines = []

        for line in lines:
            if line.strip() == header:
                if not header_found:
                    header_found = True
                    cleaned_lines.append(line.strip())
            else:
                cleaned_lines.append(line.strip())

        # Join the cleaned lines into a single string
        cleaned_data = "\n".join(cleaned_lines)

        # Load the cleaned data into a pandas DataFrame
        df = pd.read_csv(StringIO(cleaned_data), sep="|")

        # Correct any potential unnamed column issues
        df.columns = df.columns.str.strip()
        df.drop(columns=['Unnamed: 20'], errors='ignore', inplace=True)

        return df

    except PermissionError:
        print(f"Permission denied: Unable to access the file at {file_path}.")
    except FileNotFoundError:
        print(f"File not found: The file at {file_path} does not exist.")
    except Exception as e:
        print(f"An error occurred: {e} (empty log file)")
        return None

def process_sensors(logs, reference_date):
    logs.columns = logs.columns.str.strip().str.replace('[^a-zA-Z0-9]', '_', regex=True)

    # Initialize the previous time
    prev_time = None
    
    # Iterate over the rows in the 'Time' column
    for i, time_str in enumerate(logs['Time']):
        # Strip leading/trailing whitespaces
        time_str = time_str.strip()
        
        time = pd.to_datetime(time_str, format='%H:%M:%S')

        # Increment date if time is earlier than previous (crossing midnight)
        if prev_time is None or time < prev_time:
            reference_date += pd.Timedelta(days=1)

        logs.at[i, 'Time'] = pd.to_datetime(f'{reference_date.year}-{reference_date.month}-{reference_date.day} {time.hour}:{time.minute}:{time.second}')
        prev_time = time

    logs[['LIR']] = logs[['LIR']].astype(int)
    logs.loc[:, ~logs.columns.isin(['Time', 'LIR'])] = logs.loc[:, ~logs.columns.isin(['Time', 'LIR'])].astype(float)

    return logs

def process_sensors_optimized(logs, reference_date):
    # Clean column names first
    logs.columns = logs.columns.str.strip().str.replace('[^a-zA-Z0-9]', '_', regex=True)

    # Convert Time column to datetime
    logs['Time'] = pd.to_datetime(logs['Time'], format='%H:%M:%S')

    # Check for midnight crossovers and update the date
    prev_time = logs['Time'].shift(1)
    crossover_mask = (prev_time.notnull()) & (logs['Time'] < prev_time)
    logs['Date'] = reference_date + pd.to_timedelta(crossover_mask.cumsum(), unit='D')

    # Combine Date and Time into a single datetime column
    logs['Datetime'] = logs['Date'].dt.strftime('%Y-%m-%d') + ' ' + logs['Time'].dt.time.astype(str)
    logs['Datetime'] = pd.to_datetime(logs['Datetime'])

    # Drop intermediate columns
    logs.drop(columns=['Time', 'Date'], inplace=True)

    # Safely cast LIR to int and others to float
    logs['LIR'] = pd.to_numeric(logs['LIR'], downcast='integer', errors='coerce')
    non_lir_columns = logs.columns.difference(['Datetime', 'LIR'])
    logs[non_lir_columns] = logs[non_lir_columns].apply(pd.to_numeric, downcast='float', errors='coerce')

    return logs

def process_logs(logs, reference_date):
    logs.columns = logs.columns.str.strip().str.replace('[^a-zA-Z0-9]', '_', regex=True)

    # Initialize the previous time
    prev_time = None
    
    # Iterate over the rows in the 'Time' column
    for i, time_str in enumerate(logs['Time']):
        time = pd.to_datetime(time_str, format='%H:%M:%S')

        # Increment date if time is earlier than previous (crossing midnight)
        if prev_time is None or time < prev_time:
            reference_date += pd.Timedelta(days=1)

        logs.at[i, 'Time'] = pd.to_datetime(f'{reference_date.year}-{reference_date.month}-{reference_date.day} {time.hour}:{time.minute}:{time.second}')
        prev_time = time

    logs[['LIR', 'N']] = logs[['LIR', 'N']].astype(int)
    logs.loc[:, ~logs.columns.isin(['Time', 'LIR', 'N'])] = logs.loc[:, ~logs.columns.isin(['Time', 'LIR', 'N'])].astype(float)
    
    min_difference = 0.02
    # Calculate the difference
    logs['Ag_Cons'] = logs['SP5'].diff()
    # Set the difference to 0 if the absolute difference is less than min_difference
    logs['Ag_Cons'] = logs['Ag_Cons'].apply(lambda x: 0 if x < min_difference else x)
    # Optional: Cumulative sum if needed
    logs['Ag_Cons_cs'] = logs['Ag_Cons'].abs().cumsum()
    
    return logs

def process_slice_data(file_path):
    slice_data = pd.read_csv(file_path, sep=";", decimal=",")

    slice_data = slice_data.rename(columns={
        "Total slice surface (mm2)": "tss",
        "Total slice surface (mm?)": "tss",
        "Part (mm?)": "part",
        "Non solid support (mm?)": "nss",
        "Solid support (mm?)": "ss"
    })

    slice_data = slice_data.dropna(axis=1)
    return slice_data

def merge_logs_with_slice_data(logs, slice_data):
    logs = pd.concat([logs, slice_data[["tss", "part", "nss", "ss"]]], axis=1)
    logs["tss_m2"] = logs["tss"] * 1e-4
    logs = logs.dropna()
    return logs

def to_seconds(time_str):
    """
    Convert MM-SS formatted string to total seconds.
    """
    minutes, seconds = map(int, time_str.split('-'))
    return minutes * 60 + seconds

def calculate_time_differences(row, columns):
    """
    Calculate time differences (in seconds) between consecutive time columns.
    """
    differences = []
    for col1, col2 in zip(columns, columns[1:]):
        t1 = to_seconds(row[col1]) if pd.notna(row[col1]) else None
        t2 = to_seconds(row[col2]) if pd.notna(row[col2]) else None
        if t1 is not None and t2 is not None:
            diff = t2 - t1
            if diff < 0:  # Adjust for crossing from 59 seconds to 00 seconds
                diff += 60
            differences.append(diff)
        else:
            differences.append(None)  # Preserve None for missing values
    return differences