import csv
import os
import datetime
import functools

def log_function(filename="execution_logs.csv"):
    """
    Decorator that logs function execution to a CSV file.
    Logs function name, execution time, return value, and errors.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            function_name = func.__name__

            try:
                result = func(*args, **kwargs)
                log_message = f"✅ {function_name} executed successfully." if result else f"❌ {function_name} returned None."
            except Exception as e:
                log_message = f"🚨 {function_name} failed: {str(e)}"
                result = None

            file_exists = os.path.isfile(filename)
            
            with open(filename, mode="a", newline="", encoding="utf-8") as log_file:
                csv_writer = csv.writer(log_file)
                
                if not file_exists:
                    csv_writer.writerow(["Timestamp", "Function", "Log Message"])
                
                csv_writer.writerow([timestamp, function_name, log_message])

            return result

        return wrapper
    return decorator
