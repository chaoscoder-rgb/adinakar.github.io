import pandas as pd
import ast
import datetime # Added for timestamp

# --- Excel Writing with Styling (and openpyxl imports moved here) ---
from openpyxl import Workbook
from openpyxl.styles import PatternFill
from openpyxl.utils.dataframe import dataframe_to_rows


def load_and_preprocess_data():
    """
    Loads data from CSV files into pandas DataFrames and performs initial preprocessing.
    Expected files:
    - 'files/AD-TransactionAnalysis-Fields.csv'
    - 'files/splunk_log_data_pre.csv'
    - 'files/splunk_log_data_post.csv'
    """
    try:
        df_analysis_fields = pd.read_csv('files/AD-TransactionAnalysis-Fields.csv')
        df_analysis_fields['Weight_Num'] = df_analysis_fields['Weight'].str.rstrip('%').astype('float') / 100.0
        df_analysis_fields.columns = df_analysis_fields.columns.str.strip()
        for col in df_analysis_fields.columns:
            if df_analysis_fields[col].dtype == 'object':
                df_analysis_fields[col] = df_analysis_fields[col].str.strip()

        df_pre_logs = pd.read_csv('files/splunk_log_data_pre.csv')
        df_post_logs = pd.read_csv('files/splunk_log_data_post.csv')

        df_pre_logs.columns = df_pre_logs.columns.str.strip()
        df_post_logs.columns = df_post_logs.columns.str.strip()

        df_pre_logs.insert(0, 'Unique ID', [f"PRE_{i}" for i in range(len(df_pre_logs))])
        df_post_logs.insert(0, 'Unique ID', [f"POST_{i}" for i in range(len(df_post_logs))])

        dict_like_params = []
        if 'Example' in df_analysis_fields.columns:
            for _, row in df_analysis_fields.iterrows():
                example_val = str(row['Example'])
                if example_val.startswith('{') and example_val.endswith('}'):
                    dict_like_params.append(row['Parameter'])

        cols_to_parse_pre = [col for col in dict_like_params if col in df_pre_logs.columns]
        cols_to_parse_post = [col for col in dict_like_params if col in df_post_logs.columns]

        def parse_string_dict(s):
            if pd.isna(s) or s == "" or not isinstance(s, str): return None
            try: return ast.literal_eval(s)
            except (ValueError, SyntaxError): return s

        for col in cols_to_parse_pre: df_pre_logs[col] = df_pre_logs[col].apply(parse_string_dict)
        for col in cols_to_parse_post: df_post_logs[col] = df_post_logs[col].apply(parse_string_dict)

        string_cols = ['User ID', 'Requesting Service', 'Error Code', 'HTTP Method',
                       'Responding Service', 'Release Version', 'Location', 'Device/OS', 'Session ID',
                       'Error Description'] # Added Error Description here

        for df in [df_pre_logs, df_post_logs]:
            for col in string_cols:
                if col in df.columns:
                    df[col] = df[col].astype(str).fillna('')

        print("Data loaded and preprocessed successfully.")
        return df_analysis_fields, df_pre_logs, df_post_logs
    except Exception as e:
        print(f"An error occurred during data loading and preprocessing: {e}")
        return None, None, None

def compare_transactions(df_post_logs, df_pre_logs, df_analysis_fields):
    """
    Compares transactions, handling multiple matches by creating separate rows.
    Returns a list of dictionaries, each representing a row for the final report.
    """
    baseline_fields = df_analysis_fields[df_analysis_fields['Match Group'] == 'Baseline']['Parameter'].tolist()
    all_matchable_fields = df_analysis_fields['Parameter'].tolist() # All fields defined in analysis file

    weights_map = df_analysis_fields.set_index('Parameter')['Weight_Num'].to_dict()
    output_rows_list = []

    for _, post_row in df_post_logs.iterrows():
        found_at_least_one_match_for_this_post_row = False

        for _, pre_row in df_pre_logs.iterrows():
            baseline_fields_all_match = True
            # Check baseline fields for this pre_row
            for field in baseline_fields:
                post_val = post_row.get(field, float('nan')) # Use .get for safety, though columns should exist
                pre_val = pre_row.get(field, float('nan'))

                is_field_match = False
                if pd.isna(post_val) and pd.isna(pre_val): is_field_match = True
                elif not pd.isna(post_val) and not pd.isna(pre_val) and post_val == pre_val: is_field_match = True

                if not is_field_match:
                    baseline_fields_all_match = False
                    break

            if baseline_fields_all_match:
                found_at_least_one_match_for_this_post_row = True
                current_total_weight_percentage = 0.0
                field_comparison_details = {}

                # Calculate percentage and gather field match details for ALL relevant fields
                for field in all_matchable_fields:
                    # This field contributes to styling and percentage calculation if it exists in post_row
                    if field not in post_row:
                        field_comparison_details[field] = False # Cannot match if not in post_row
                        continue

                    post_val = post_row[field]
                    pre_val = pre_row.get(field, float('nan')) # Get from pre_row, default if missing

                    is_field_match_for_styling_and_weight = False
                    if pd.isna(post_val) and pd.isna(pre_val):
                        is_field_match_for_styling_and_weight = True
                    elif not pd.isna(post_val) and not pd.isna(pre_val) and post_val == pre_val:
                        is_field_match_for_styling_and_weight = True

                    field_comparison_details[field] = is_field_match_for_styling_and_weight
                    if is_field_match_for_styling_and_weight:
                        current_total_weight_percentage += weights_map.get(field, 0)

                # Construct output row for this specific post-pre match
                output_row_data = post_row.to_dict() # Start with all data from post_row
                output_row_data['Matched Pre Unique ID'] = pre_row['Unique ID']
                output_row_data['Match Result'] = 'Yes'
                output_row_data['Total Matched Percentage'] = round(current_total_weight_percentage * 100, 2)
                output_row_data['__Field_Matches__'] = field_comparison_details # For styling
                output_rows_list.append(output_row_data)

        if not found_at_least_one_match_for_this_post_row:
            # If no pre_row matched this post_row on baseline criteria
            output_row_data = post_row.to_dict()
            output_row_data['Matched Pre Unique ID'] = None
            output_row_data['Match Result'] = 'No'
            output_row_data['Total Matched Percentage'] = 'Not Applicable'
            output_row_data['__Field_Matches__'] = {} # No fields to style as 'matched' or 'mismatched'
            output_rows_list.append(output_row_data)

    return output_rows_list


def write_excel_output_with_styling(output_df, df_pre_logs, df_post_logs, # Added raw dfs for new sheets
                                   df_analysis_fields,
                                   pre_file_name, post_file_name, num_pre_rows, num_post_rows,
                                   filename="files/comparison_output.xlsx"):
    wb = Workbook()

    # --- Main Comparison Sheet (Styled) ---
    ws_main = wb.active
    ws_main.title = "Transaction Comparison"
    green_fill = PatternFill(start_color="CCFFCC", end_color="CCFFCC", fill_type="solid")
    red_fill = PatternFill(start_color="FFCCCC", end_color="FFCCCC", fill_type="solid")

    df_for_excel_main = output_df.copy()
    # The __Field_Matches__ column is already dicts of booleans, not for direct display.
    # It will be dropped before saving if it's still there, or handled by dataframe_to_rows if it errors.
    # Let's ensure complex objects are stringified for the main data part.
    columns_to_stringify = [col for col in df_analysis_fields['Parameter'].tolist() if col in df_for_excel_main.columns]
    columns_to_stringify.append('Unique ID') # Ensure Unique IDs are strings if not already
    columns_to_stringify.append('Matched Pre Unique ID')

    for col in df_for_excel_main.columns:
        if df_for_excel_main[col].dtype == 'object':
            # Check if first non-NaN is dict or list
            first_valid = df_for_excel_main[col].dropna().iloc[0] if not df_for_excel_main[col].dropna().empty else None
            if isinstance(first_valid, (dict, list)):
                 df_for_excel_main[col] = df_for_excel_main[col].apply(lambda x: str(x) if isinstance(x, (dict, list)) else x)

    # Add headers for main sheet
    main_sheet_headers = [col for col in df_for_excel_main.columns if col not in ['__Field_Matches__']]
    ws_main.append(main_sheet_headers)

    # Add data rows and apply styling
    header_list_main = main_sheet_headers # Use the ordered list
    col_name_to_idx_main = {name: i + 1 for i, name in enumerate(header_list_main)}

    for row_dict in output_df.to_dict('records'): # output_df still has __Field_Matches__ here
        # Prepare row for appending (without special columns)
        row_to_append = [str(row_dict.get(col)) if isinstance(row_dict.get(col), (dict,list)) else row_dict.get(col) for col in main_sheet_headers]
        ws_main.append(row_to_append)

        current_ws_row = ws_main.max_row # Get current row index in worksheet
        if row_dict.get('Match Result') == 'Yes':
            field_matches = row_dict.get('__Field_Matches__', {})
            for field_name, is_match in field_matches.items():
                if field_name in col_name_to_idx_main:
                    col_idx = col_name_to_idx_main[field_name]
                    cell = ws_main.cell(row=current_ws_row, column=col_idx)
                    if is_match: cell.fill = green_fill
                    else: cell.fill = red_fill

    # --- Pre-Log Data Sheet ---
    ws_pre = wb.create_sheet("Pre-Log Data")
    df_pre_excel = df_pre_logs.copy()
    for col in df_pre_excel.columns: # Stringify dicts/lists if any
        if df_pre_excel[col].dtype == 'object':
            first_valid = df_pre_excel[col].dropna().iloc[0] if not df_pre_excel[col].dropna().empty else None
            if isinstance(first_valid, (dict, list)):
                 df_pre_excel[col] = df_pre_excel[col].apply(lambda x: str(x) if isinstance(x, (dict, list)) else x)
    for r in dataframe_to_rows(df_pre_excel, index=False, header=True): ws_pre.append(r)

    # --- Post-Log Data Sheet ---
    ws_post = wb.create_sheet("Post-Log Data")
    df_post_excel = df_post_logs.copy()
    for col in df_post_excel.columns: # Stringify dicts/lists if any
        if df_post_excel[col].dtype == 'object':
            first_valid = df_post_excel[col].dropna().iloc[0] if not df_post_excel[col].dropna().empty else None
            if isinstance(first_valid, (dict, list)):
                 df_post_excel[col] = df_post_excel[col].apply(lambda x: str(x) if isinstance(x, (dict, list)) else x)
    for r in dataframe_to_rows(df_post_excel, index=False, header=True): ws_post.append(r)

    # --- Summary Sheet Creation ---
    ws_summary = wb.create_sheet("Comparison Summary")
    summary_data = [
        ("Pre-File Name:", pre_file_name),
        ("Post-File Name:", post_file_name),
        ("Number of Rows in Pre-File:", num_pre_rows),
        ("Number of Rows in Post-File:", num_post_rows),
        # Count of 'Yes' Match Result rows in the main comparison output
        ("Count of Matched Pairs (Post-Pre):", output_df[output_df['Match Result'] == 'Yes'].shape[0]),
        # Count of unique Post 'Unique ID's that are in the 'No' match group
        ("Count of Unmatched Post Transactions:", output_df[output_df['Match Result'] == 'No']['Unique ID'].nunique()),
    ]
    for r_idx, (label, value) in enumerate(summary_data, 1):
        ws_summary.cell(row=r_idx, column=1, value=label)
        ws_summary.cell(row=r_idx, column=2, value=value)

    current_row_in_summary = len(summary_data) + 2
    ws_summary.cell(row=current_row_in_summary, column=1, value="Matches Grouped by User ID, Error Code, Requesting Service:")
    current_row_in_summary += 1

    if not output_df[output_df['Match Result'] == 'Yes'].empty:
        matched_pairs_df = output_df[output_df['Match Result'] == 'Yes']
        try:
            pivot_table = pd.pivot_table(
                matched_pairs_df,
                index=['User ID', 'Error Code', 'Requesting Service'],
                aggfunc='size',
                fill_value=0
            ).reset_index(name='Match Count')
            for c_idx, value in enumerate(pivot_table.columns, 1):
                ws_summary.cell(row=current_row_in_summary, column=c_idx, value=value)
            current_row_in_summary +=1
            for _, pivot_row in pivot_table.iterrows():
                for c_idx, value in enumerate(pivot_row, 1):
                    ws_summary.cell(row=current_row_in_summary, column=c_idx, value=value)
                current_row_in_summary += 1
        except Exception as e:
            ws_summary.cell(row=current_row_in_summary, column=1, value=f"Error generating pivot table: {e}")
    else:
        ws_summary.cell(row=current_row_in_summary, column=1, value="No 'Yes' matches to generate pivot table.")

    try:
        wb.save(filename)
        print(f"\nStyled comparison output with summary sheet saved to {filename}")
    except Exception as e:
        print(f"Error saving styled Excel output: {e}")


if __name__ == '__main__':
    df_analysis, df_pre, df_post = load_and_preprocess_data()

    if df_analysis is None or df_pre is None or df_post is None:
        print("Data loading failed. Exiting.")
    else:
        print("\nRunning transaction comparison (overhauled)...")
        output_list_of_dicts = compare_transactions(df_post, df_pre, df_analysis)
        comparison_output_df = pd.DataFrame(output_list_of_dicts)

        # Prepare detailed_results for styling function (list of dicts with 'Match Result' and 'Field Matches')
        # This is now directly embedded in comparison_output_df as '__Field_Matches__'
        # The styling function will use the comparison_output_df directly.

        # For console output and clarity, keep a separate detailed_results structure if needed for debugging
        # but for styling, the comparison_output_df (before dropping __Field_Matches__) is key.

        # Make a copy for printing before dropping helper columns
        printable_df = comparison_output_df.copy()
        if '__Field_Matches__' in printable_df.columns:
            printable_df = printable_df.drop(columns=['__Field_Matches__'])

        print("\nComparison Output DF Head (Post Overhaul):")
        print(printable_df.head())
        print(f"\nTotal rows in output: {len(comparison_output_df)}")

        print("\nValue counts for 'Match Result':")
        print(comparison_output_df['Match Result'].value_counts())

        print("\nSample of 'Total Matched Percentage' for 'Yes' matches:")
        print(comparison_output_df[comparison_output_df['Match Result'] == 'Yes']['Total Matched Percentage'].head())

        print("\nSample of 'Matched Pre Unique ID' for 'Yes' matches:")
        print(comparison_output_df[comparison_output_df['Match Result'] == 'Yes']['Matched Pre Unique ID'].head())

        # Example: Print details for the first 'Yes' match found in the new structure
        first_yes_match_dict = next((item for item in output_list_of_dicts if item['Match Result'] == 'Yes'), None)
        if first_yes_match_dict:
            print(f"\nDetails for first 'Yes' match (Post Unique ID: {first_yes_match_dict.get('Unique ID')}):")
            print(f"  Matched Pre Unique ID: {first_yes_match_dict.get('Matched Pre Unique ID')}")
            field_matches_sample = dict(list(first_yes_match_dict.get('__Field_Matches__', {}).items())[:5])
            print(f"  Field Matches (sample): {field_matches_sample}")

        pre_file_name = "splunk_log_data_pre.csv"
        post_file_name = "splunk_log_data_post.csv"
        num_pre_rows = len(df_pre)
        num_post_rows = len(df_post)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"files/comparison_output_{timestamp}.xlsx"

        write_excel_output_with_styling(
            comparison_output_df, # This now contains __Field_Matches__
            df_pre, df_post, # Pass raw dataframes for new sheets
            df_analysis,
            pre_file_name, post_file_name, num_pre_rows, num_post_rows,
            filename=output_filename
        )
        print(f"Test run with styled Excel output finished. File saved as {output_filename}")
