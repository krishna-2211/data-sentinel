import pandas as pd
import io

def generate_data_profile(df: pd.DataFrame) -> str:
    """
    Analyzes a DataFrame and returns a text-based Data Quality Report (DQR).
    Includes: Essentials, Outliers, and Correlation Analysis.
    """
    buffer = io.StringIO()
    
    # --- SECTION 1: DATASET OVERVIEW ---
    buffer.write(f"DATA QUALITY REPORT\n")
    buffer.write(f"===================\n")
    buffer.write(f"Total Rows: {len(df)}\n")
    buffer.write(f"Total Columns: {len(df.columns)}\n")
    
    # Check for duplicates
    duplicates = df.duplicated().sum()
    if duplicates > 0:
        buffer.write(f"Duplicate Rows: {duplicates} (Needs Deduplication)\n")
    else:
        buffer.write(f"Duplicate Rows: 0\n")
    
    buffer.write(f"Columns: {list(df.columns)}\n\n")
    
    # --- SECTION 2: COLUMN ANALYSIS ---
    buffer.write(f"--- COLUMN STATISTICS ---\n")
    for col in df.columns:
        buffer.write(f"Column '{col}':\n")
        
        # Type & Missing
        dtype = df[col].dtype
        missing = df[col].isnull().sum()
        missing_pct = (missing / len(df)) * 100
        buffer.write(f"  - Data Type: {dtype}\n")
        buffer.write(f"  - Missing Values: {missing} ({missing_pct:.2f}%)\n")
        
        # Unique Values
        unique_count = df[col].nunique()
        buffer.write(f"  - Unique Values: {unique_count}\n")
        
        # Numeric Stats
        if pd.api.types.is_numeric_dtype(df[col]):
            # Zero count (often a placeholder for missing)
            zeros = (df[col] == 0).sum()
            buffer.write(f"  - Zero Values: {zeros}\n")
            
            # Skew
            try:
                skew = df[col].skew()
                buffer.write(f"  - Skew: {skew:.2f}\n")
            except: pass
            
            # Outliers (IQR)
            try:
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                outliers = df[(df[col] < (Q1 - 1.5 * IQR)) | (df[col] > (Q3 + 1.5 * IQR))].shape[0]
                buffer.write(f"  - Potential Outliers (IQR): {outliers}\n")
            except: pass
            
        # String Stats
        if pd.api.types.is_string_dtype(df[col]):
            # Check for empty strings that aren't NaN
            empty_strings = (df[col] == "").sum()
            if empty_strings > 0:
                buffer.write(f"  - Empty Strings (not NaN): {empty_strings}\n")
        
        # Samples (Crucial for context)
        samples = df[col].dropna().unique()[:5]
        buffer.write(f"  - Sample Values: {list(samples)}\n")
        buffer.write("\n")

    # --- SECTION 3: CORRELATION ANALYSIS (Your Feature!) ---
    # We only check numeric columns to find relationships
    numeric_df = df.select_dtypes(include=['number'])
    if not numeric_df.empty and len(numeric_df.columns) > 1:
        buffer.write("TOP CORRELATIONS (Potential Redundancy):\n")
        try:
            corr_matrix = numeric_df.corr().abs()
            # Select upper triangle of correlation matrix
            import numpy as np
            upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
            
            # Find strong correlations (> 0.8)
            strong_pairs = [
                (column, index, upper.loc[index, column]) 
                for index in upper.index 
                for column in upper.columns 
                if upper.loc[index, column] > 0.8
            ]
            
            if strong_pairs:
                for col1, col2, val in strong_pairs:
                    buffer.write(f"  - '{col1}' vs '{col2}': {val:.2f} (High Correlation)\n")
            else:
                buffer.write("  - No strong correlations detected (> 0.8).\n")
                
        except Exception as e:
            buffer.write(f"  - Could not calculate correlations: {e}\n")
            
    return buffer.getvalue()