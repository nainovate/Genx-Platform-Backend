import pandas as pd
import os
from datetime import datetime
from fastapi import HTTPException
from openpyxl import load_workbook

class ExcelHandler:
    def __init__(self, excel_file_name):
        self.excel_file_name = excel_file_name

    def json_to_excel(self, json_data):
        try:
            # Validate the provided JSON data
            if not json_data:
                raise HTTPException(status_code=400, detail="The provided JSON data is empty or invalid. Cannot convert to Excel.")
            
            all_data = []
             # Iterate through each model in the list (since json_data is a list)
            for model_data in json_data:
                if not isinstance(model_data, dict):
                    raise HTTPException(status_code=400, detail="Invalid data format. Each entry must be a dictionary.")

                timestamp_value = model_data.get("results", {}).get("timestamp", None)  # Extract timestamp from each model
                for payload_key, payloads in model_data["results"].items():
                    if payload_key == "timestamp":
                        continue
                    if not isinstance(payloads, list):
                        raise HTTPException(status_code=400, detail="Invalid payload format. Each payload must be a list.")

                    # Process each item in the payloads
                    for payload in payloads:
                        # Add the timestamp to each row of data
                        payload["Timestamp"] = timestamp_value
                        all_data.append(payload)

            # If no valid data is found, raise an exception
            if not all_data:
                raise HTTPException(status_code=400, detail="No valid data found to convert to Excel.")
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.excel_file_name), exist_ok=True)

            # Generate timestamp for file naming
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            # Create a new file name with the timestamp
            file_name = f"output_{timestamp}.xlsx"

            # Combine the file name with the directory path
            file_path = os.path.join(self.excel_file_name, file_name)
            print("Excel file path:", file_path)

            # Create DataFrame from the collected data
            df = pd.DataFrame(all_data)

            # Add the timestamp column to the entire DataFrame
            df["Timestamp"] = timestamp_value

            # Sheet 1: Input Details
            df1 = df[["Timestamp", "Test ID", "Input", "Question Number", "distributor(%)", "prompt_count"]].drop_duplicates().sort_values(by=["Test ID", "Question Number"])

            # Sheet 2: Request Response Details
            df2 = df[["Test ID", "User ID", "Session ID", "Question Number", "request_id", "Response", "Status Code", "Latency (seconds)"]].sort_values(by=["Test ID", "User ID"])

            # Sheet 3: Performance Data
            df3 = df[["Test ID", "Percentile Latency (seconds)", "Throughput (requests/second)"]].drop_duplicates()

            # Write data to Excel using xlsxwriter
            with pd.ExcelWriter(file_path, engine='xlsxwriter') as writer:
                workbook = writer.book

                # Write first sheet with merged cells for 'Test ID' and 'Timestamp'
                df1.to_excel(writer, sheet_name='Input Details', startrow=0, index=False)
                worksheet1 = writer.sheets['Input Details']
                merge_format = workbook.add_format({
                    'align': 'center',
                    'valign': 'vcenter',
                    'border': 1
                })

                # Merge 'Test ID' cells in Input Details sheet
                test_id_groups = df1.groupby('Test ID')
                for idx, (test_id, group) in enumerate(test_id_groups):
                    first_row = 1 + sum(len(g) for _, g in list(test_id_groups)[:idx])
                    last_row = first_row + len(group) - 1
                    worksheet1.merge_range(first_row, 1, last_row, 1, test_id, merge_format)

                # Merge 'Timestamp' cells in Input Details sheet
                timestamp_groups = df1.groupby('Timestamp')
                for idx, (timestamp, group) in enumerate(timestamp_groups):
                    first_row = 1 + sum(len(g) for _, g in list(timestamp_groups)[:idx])
                    last_row = first_row + len(group) - 1
                    worksheet1.merge_range(first_row, 0, last_row, 0, timestamp, merge_format)

                # Write second sheet with merged 'Test ID' cells
                df2.to_excel(writer, sheet_name='Request Response Details', index=False)
                worksheet2 = writer.sheets['Request Response Details']
                
                # Merge 'Test ID' cells in Request Response Details sheet
                test_id_groups = df2.groupby('Test ID')
                for idx, (test_id, group) in enumerate(test_id_groups):
                    first_row = 1 + sum(len(g) for _, g in list(test_id_groups)[:idx])
                    last_row = first_row + len(group) - 1
                    worksheet2.merge_range(first_row, 0, last_row, 0, test_id, merge_format)

                # Write third sheet
                df3.to_excel(writer, sheet_name='Performance', index=False)

            print(f"Excel file saved successfully as {file_path}")
            return file_path
        except OSError as e:
            error_message = f"OS error occurred while creating directory or file: {e}"
            print(error_message)
            raise HTTPException(status_code=500, detail=error_message)

        except Exception as e:
            error_message = f"Error converting JSON to Excel: {e}"
            print(error_message)
            raise HTTPException(status_code=500, detail=error_message)
