
import os
import pandas as pd
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.styles import Alignment

def convert_json_to_excel(input_file, output_file):
    df = pd.read_json(input_file)
    wb = Workbook()
    ws = wb.active
    for r in dataframe_to_rows(df, index=False, header=True):
        ws.append(r)
    for row in ws.rows:
        for cell in row:
            cell.alignment = Alignment(wrap_text=True)
    wb.save(output_file)

def traverse_directory(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.json'):
                input_file = os.path.join(root, file)
                output_file = os.path.splitext(input_file)[0] + '.xlsx'
                convert_json_to_excel(input_file, output_file)


if __name__=="__main__":
    traverse_directory('.')



