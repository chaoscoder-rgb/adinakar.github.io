import pandas as pd
import ast

def load_and_preprocess_data():
    """
    Loads data from CSV files into pandas DataFrames and performs initial preprocessing.
    Expected files:
    - 'files/AD-TransactionAnalysis-Fields.csv'
    - 'files/splunk_log_data_pre.csv'
    - 'files/splunk_log_data_post.csv'
    """
    try:
        # Load the analysis fields mapping
        df_analysis_fields = pd.read_csv('files/AD-TransactionAnalysis-Fields.csv')

        # Preprocess df_analysis_fields
        # Convert 'Weight' from "10%" string to float 0.10
        df_analysis_fields['Weight_Num'] = df_analysis_fields['Weight'].str.rstrip('%').astype('float') / 100.0
        # Strip potential leading/trailing whitespace from column names and values
        df_analysis_fields.columns = df_analysis_fields.columns.str.strip()
        for col in df_analysis_fields.columns:
            if df_analysis_fields[col].dtype == 'object':
                df_analysis_fields[col] = df_analysis_fields[col].str.strip()

        # Load the pre and post log data
        df_pre_logs = pd.read_csv('files/splunk_log_data_pre.csv')
        df_post_logs = pd.read_csv('files/splunk_log_data_post.csv')

        # Strip potential leading/trailing whitespace from column names
        df_pre_logs.columns = df_pre_logs.columns.str.strip()
        df_post_logs.columns = df_post_logs.columns.str.strip()

        # Identify columns that need to be parsed from string-formatted dicts
        # Based on AD-TransactionAnalysis-Fields.csv, these are typically:
        # Request Headers, Request Payload, Response Body
        # However, it's safer to check which parameters have examples suggesting dict structures.
        dict_like_params = []
        if 'Example' in df_analysis_fields.columns:
            for _, row in df_analysis_fields.iterrows():
                example_val = str(row['Example'])
                if example_val.startswith('{') and example_val.endswith('}'):
                    dict_like_params.append(row['Parameter'])

        # Ensure we only try to parse columns that actually exist in the log DataFrames
        cols_to_parse_pre = [col for col in dict_like_params if col in df_pre_logs.columns]
        cols_to_parse_post = [col for col in dict_like_params if col in df_post_logs.columns]

        # Helper function to safely parse string-formatted dictionaries
        def parse_string_dict(s):
            if pd.isna(s) or s == "" or not isinstance(s, str):
                return None # Or {} if an empty dict is preferred for missing values
            try:
                return ast.literal_eval(s)
            except (ValueError, SyntaxError):
                # Handle cases where parsing fails, e.g., malformed string
                # print(f"Warning: Could not parse string: {s}")
                return s # Keep original if parsing fails, or return a specific error marker

        for col in cols_to_parse_pre:
            df_pre_logs[col] = df_pre_logs[col].apply(parse_string_dict)

        for col in cols_to_parse_post:
            df_post_logs[col] = df_post_logs[col].apply(parse_string_dict)

        # Convert relevant columns to string to ensure consistent comparisons,
        # especially for numerical-looking codes that should be treated as strings.
        # This should be done after parsing for dict-like columns.
        string_cols = ['User ID', 'Requesting Service', 'Error Code', 'HTTP Method',
                       'Responding Service', 'Release Version', 'Location', 'Device/OS', 'Session ID']

        for df in [df_pre_logs, df_post_logs]:
            for col in string_cols:
                if col in df.columns:
                    df[col] = df[col].astype(str).fillna('') # Convert to string and fill NaN with empty string

        # Error Description might also need to be string, but it's handled by default read_csv as object/string
        if 'Error Description' in df_pre_logs.columns:
             df_pre_logs['Error Description'] = df_pre_logs['Error Description'].astype(str).fillna('')
        if 'Error Description' in df_post_logs.columns:
             df_post_logs['Error Description'] = df_post_logs['Error Description'].astype(str).fillna('')


        print("Data loaded and preprocessed successfully.")
        print("\nAnalysis Fields Head:")
        print(df_analysis_fields.head())
        print(f"\nAnalysis Fields Columns: {df_analysis_fields.columns.tolist()}")
        print(f"Identified dict-like parameters for parsing: {dict_like_params}")


        print("\nPre-Logs Head:")
        print(df_pre_logs.head())
        print(f"\nPre-Logs Columns: {df_pre_logs.columns.tolist()}")
        if cols_to_parse_pre:
            print(f"\nSample of parsed '{cols_to_parse_pre[0]}' in Pre-Logs:")
            print(df_pre_logs[cols_to_parse_pre[0]].head())


        print("\nPost-Logs Head:")
        print(df_post_logs.head())
        print(f"\nPost-Logs Columns: {df_post_logs.columns.tolist()}")
        if cols_to_parse_post:
            print(f"\nSample of parsed '{cols_to_parse_post[0]}' in Post-Logs:")
            print(df_post_logs[cols_to_parse_post[0]].head())

        return df_analysis_fields, df_pre_logs, df_post_logs
    except Exception as e:
        print(f"An error occurred during data loading and preprocessing: {e}")
        # Optionally re-raise the exception if you want the program to stop
        # raise
        # Or return None or empty DataFrames to indicate failure
        return None, None, None

if __name__ == '__main__':
    # This is for testing the function directly
    df_analysis, df_pre, df_post = load_and_preprocess_data()

    if df_analysis is None or df_pre is None or df_post is None:
        print("Data loading failed. Exiting.")
    else:
        # Further checks can be added here, e.g.
        print("\nData types in df_analysis_fields:")
    print(df_analysis.dtypes)
    print("\nData types in df_pre_logs:")
    print(df_pre.dtypes)
    print("\nData types in df_post_logs:")
    print(df_post.dtypes)

    # Example: Check one of the parsed columns
    if 'Request Headers' in df_post.columns:
        print("\nExample of a parsed Request Header entry in df_post_logs:")
        print(df_post['Request Headers'].iloc[0])
        print(type(df_post['Request Headers'].iloc[0]))

    if 'Weight_Num' in df_analysis.columns:
        print("\nNumeric weights in df_analysis_fields:")
        print(df_analysis[['Parameter', 'Weight', 'Weight_Num']].head())

    # Check for NaNs in key fields after processing
    baseline_fields = df_analysis[df_analysis['Match Group'] == 'Baseline']['Parameter'].tolist()
    print(f"\nBaseline fields: {baseline_fields}")

    print("\nNaN counts in baseline fields of Pre-Logs:")
    for col in baseline_fields:
        if col in df_pre.columns:
            print(f"{col}: {df_pre[col].isna().sum()}")
        else:
            print(f"{col}: Not found in Pre-Logs")

    print("\nNaN counts in baseline fields of Post-Logs:")
    for col in baseline_fields:
        if col in df_post.columns:
            print(f"{col}: {df_post[col].isna().sum()}")
        else:
            print(f"{col}: Not found in Post-Logs")

    # Check Requesting Service example from AD-TransactionAnalysis-Fields.csv
    # "payment-service (From headers)", Service name in X-Service-Name
    # The current logic directly uses the "Requesting Service" column.
    # If X-Service-Name is a header in 'Request Headers', that would require different logic.
    # For now, assuming direct match on 'Requesting Service' column.
    if 'Requesting Service' in df_post.columns:
        print("\nSample 'Requesting Service' data from post_logs:")
        print(df_post['Requesting Service'].head())

    if 'Error Description' in df_post.columns:
        print("\nSample 'Error Description' data from post_logs:")
        print(df_post['Error Description'].head())
        print(type(df_post['Error Description'].iloc[0]))


    # Check if 'Error Code' is string
    if 'Error Code' in df_post.columns:
        print("\nType of 'Error Code' in post_logs")
        print(df_post['Error Code'].dtype)
        print(df_post['Error Code'].head())

    # Check a string-parsed dict column to ensure it's dict
    if 'Request Payload' in df_post and not df_post['Request Payload'].empty:
        first_payload_item = df_post['Request Payload'].iloc[0]
        print(f"\nFirst item in 'Request Payload' (post_logs): {first_payload_item}")
        print(f"Type of first item in 'Request Payload' (post_logs): {type(first_payload_item)}")

    if 'Response Body' in df_post and not df_post['Response Body'].empty:
        first_response_body_item = df_post['Response Body'].iloc[0]
        print(f"\nFirst item in 'Response Body' (post_logs): {first_response_body_item}")
        print(f"Type of first item in 'Response Body' (post_logs): {type(first_response_body_item)}")

    print("Test run of load_and_preprocess_data finished.")


def compare_transactions(df_post_logs, df_pre_logs, df_analysis_fields):
    """
    Compares transactions from df_post_logs with df_pre_logs based on df_analysis_fields.

    Args:
        df_post_logs (pd.DataFrame): DataFrame of current logs.
        df_pre_logs (pd.DataFrame): DataFrame of historical/baseline logs.
        df_analysis_fields (pd.DataFrame): DataFrame with matching rules and weights.

    Returns:
        pd.DataFrame: df_post_logs with added 'Match Result' and 'Total Matched Percentage' columns.
    """
    baseline_fields = df_analysis_fields[df_analysis_fields['Match Group'] == 'Baseline']['Parameter'].tolist()
    comprehensive_fields = df_analysis_fields[df_analysis_fields['Match Group'] == 'Comprehensive']['Parameter'].tolist()

    all_matchable_fields = baseline_fields + comprehensive_fields

    # Create a dictionary for quick weight lookup
    # Ensure 'Parameter' is the index for quick lookup
    if 'Parameter' not in df_analysis_fields.columns:
        raise ValueError("Critical column 'Parameter' not found in df_analysis_fields.")
    if 'Weight_Num' not in df_analysis_fields.columns:
        # Attempt to create it if 'Weight' exists
        if 'Weight' in df_analysis_fields.columns:
            print("Warning: 'Weight_Num' not found, attempting to create from 'Weight'.")
            df_analysis_fields['Weight_Num'] = df_analysis_fields['Weight'].str.rstrip('%').astype('float') / 100.0
        else:
            raise ValueError("Critical column 'Weight_Num' (and 'Weight') not found in df_analysis_fields.")

    weights_map = df_analysis_fields.set_index('Parameter')['Weight_Num'].to_dict()

    results = []

    for index, post_row in df_post_logs.iterrows():
        match_found_for_post_row = False
        best_match_percentage = 0.0  # In case multiple pre_rows match baseline, not strictly needed by current logic

        for _, pre_row in df_pre_logs.iterrows():
            baseline_match = True
            # Check baseline fields
            for field in baseline_fields:
                if field not in post_row or field not in pre_row:
                    # print(f"Warning: Baseline field '{field}' not found in a row. Post: {field in post_row}, Pre: {field in pre_row}")
                    baseline_match = False
                    break

                post_val = post_row[field]
                pre_val = pre_row[field]

                # Handle NaN explicitly if not already handled by fillna('') during preprocessing
                # If they were filled with '', then pd.NA comparison might be tricky, direct equality is fine
                if pd.isna(post_val) and pd.isna(pre_val):
                    continue # Both are NaN, consider it a match for this field
                if pd.isna(post_val) or pd.isna(pre_val):
                    baseline_match = False # One is NaN, the other is not
                    break

                # For dicts, direct comparison works. For other types, direct.
                if post_val != pre_val:
                    baseline_match = False
                    break

            if baseline_match:
                match_found_for_post_row = True
                current_transaction_match_percentage = 0.0

                # Calculate comprehensive match percentage (Baseline + Comprehensive fields)
                for field in all_matchable_fields: # Iterate over all fields defined for matching
                    if field not in post_row or field not in pre_row:
                        # print(f"Warning: Field '{field}' for percentage calculation not found. Post: {field in post_row}, Pre: {field in pre_row}")
                        continue

                    post_val = post_row[field]
                    pre_val = pre_row[field]

                    if pd.isna(post_val) and pd.isna(pre_val):
                        # If both are NaN, and field has weight, count it.
                        # Or decide if NaNs matching contribute to percentage. Assuming they do if values are identical (both NaN).
                        current_transaction_match_percentage += weights_map.get(field, 0)
                        continue
                    if pd.isna(post_val) or pd.isna(pre_val):
                        continue # Field mismatch if one is NaN

                    if post_val == pre_val:
                        current_transaction_match_percentage += weights_map.get(field, 0)

                # Store this percentage. If there could be multiple pre_row matches,
                # you might want the highest, but current logic implies one match is enough.
                best_match_percentage = current_transaction_match_percentage * 100 # Convert to percentage
                break # Found a baseline match, move to the next post_row

        if match_found_for_post_row:
            results.append({'Match Result': 'Yes', 'Total Matched Percentage': round(best_match_percentage, 2)})
        else:
            results.append({'Match Result': 'No', 'Total Matched Percentage': 'Not Applicable'})

    output_df = df_post_logs.copy()
    result_df_part = pd.DataFrame(results, index=output_df.index)

    output_df['Match Result'] = result_df_part['Match Result']
    output_df['Total Matched Percentage'] = result_df_part['Total Matched Percentage']

    return output_df

if __name__ == '__main__':
    # This is for testing the function directly
    df_analysis, df_pre, df_post = load_and_preprocess_data()

    # Further checks can be added here, e.g.
    print("\nData types in df_analysis_fields:")
    print(df_analysis.dtypes)
    # print("\nData types in df_pre_logs:")
    # print(df_pre.dtypes)
    # print("\nData types in df_post_logs:")
    # print(df_post.dtypes)

    if 'Weight_Num' in df_analysis.columns:
        print("\nNumeric weights in df_analysis_fields:")
        print(df_analysis[['Parameter', 'Weight', 'Weight_Num']].head())

    print("\nRunning transaction comparison...")
    comparison_output = compare_transactions(df_post, df_pre, df_analysis)
    print("\nComparison Output Head:")
    print(comparison_output.head())

    print("\nValue counts for 'Match Result':")
    print(comparison_output['Match Result'].value_counts())

    print("\nSample of 'Total Matched Percentage' for 'Yes' matches:")
    print(comparison_output[comparison_output['Match Result'] == 'Yes']['Total Matched Percentage'].head())

    print("\nSample of 'Total Matched Percentage' for 'No' matches:")
    print(comparison_output[comparison_output['Match Result'] == 'No']['Total Matched Percentage'].head())

    # Save the output to an Excel file for inspection
    try:
        output_file_path_excel = 'files/comparison_output.xlsx'
        # Using openpyxl engine, which should be installed. index=False to not write pandas index to file.
        comparison_output.to_excel(output_file_path_excel, index=False, engine='openpyxl')
        print(f"\nComparison output saved to {output_file_path_excel}")
    except Exception as e:
        print(f"Error saving output to Excel: {e}")

    print("Test run of compare_transactions finished.")
