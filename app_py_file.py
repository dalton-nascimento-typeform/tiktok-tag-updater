import streamlit as st
import pandas as pd
import re
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import io
from typing import Dict, List, Optional, Tuple

def extract_url_from_quotes(text: str) -> str:
    """Extract URL from quotation marks in impression tracker text."""
    if pd.isna(text) or not isinstance(text, str):
        return ""
    
    # Find content within quotes
    match = re.search(r'"([^"]*)"', text)
    if match:
        return match.group(1)
    return text.strip()

def parse_url_components(url: str) -> Tuple[str, Dict[str, str]]:
    """Parse URL and return base URL and parameters dictionary."""
    if not url or pd.isna(url):
        return "", {}
    
    parsed = urlparse(str(url))
    params = parse_qs(parsed.query, keep_blank_values=True)
    
    # Convert list values to single values
    param_dict = {k: v[0] if v else "" for k, v in params.items()}
    
    # Reconstruct base URL without query parameters
    base_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, '', parsed.fragment))
    
    return base_url, param_dict

def build_url_with_params(base_url: str, params: Dict[str, str]) -> str:
    """Build URL from base URL and parameters dictionary."""
    if not base_url:
        return ""
    
    if not params:
        return base_url
    
    # Convert params dict back to query string
    query_string = urlencode(params, doseq=False)
    
    parsed = urlparse(base_url)
    new_parsed = parsed._replace(query=query_string)
    
    return urlunparse(new_parsed)

def update_click_url(original_url: str, click_tracker: str, campaign_name: str) -> str:
    """Update click URL with tracker and UTM/TF parameters."""
    if pd.isna(original_url) or not original_url:
        return ""
    
    # Start with original URL
    current_url = str(original_url).strip()
    
    # Prepend click tracker if available
    if click_tracker and not pd.isna(click_tracker):
        click_tracker = str(click_tracker).strip()
        if click_tracker:
            current_url = click_tracker + current_url
    
    # Parse the URL to add missing parameters
    base_url, params = parse_url_components(current_url)
    
    # Add missing UTM parameters
    if 'utm_source' not in params:
        params['utm_source'] = 'tiktok'
    if 'utm_medium' not in params:
        params['utm_medium'] = 'paid'
    if 'utm_campaign' not in params:
        params['utm_campaign'] = str(campaign_name) if campaign_name else ''
    
    # Add missing TF parameters
    if 'tf_source' not in params:
        params['tf_source'] = 'tiktok'
    if 'tf_medium' not in params:
        params['tf_medium'] = 'paid_social'
    if 'tf_campaign' not in params:
        params['tf_campaign'] = str(campaign_name) if campaign_name else ''
    
    return build_url_with_params(base_url, params)

def find_matching_tag_row(tiktok_row: pd.Series, tag_df: pd.DataFrame) -> Optional[pd.Series]:
    """Find matching row in tag file based on Campaign Name, Ad Group Name/Placement Name, and Ad Name."""
    campaign_name = tiktok_row.get('Campaign Name', '')
    ad_group_name = tiktok_row.get('Ad Group Name', '')
    ad_name = tiktok_row.get('Ad Name', '')
    
    # Create boolean mask for matching
    mask = (
        (tag_df['Campaign Name'].astype(str).str.strip() == str(campaign_name).strip()) &
        (tag_df['Placement Name'].astype(str).str.strip() == str(ad_group_name).strip()) &
        (tag_df['Ad Name'].astype(str).str.strip() == str(ad_name).strip())
    )
    
    matching_rows = tag_df[mask]
    
    if len(matching_rows) > 0:
        return matching_rows.iloc[0]
    
    return None

def process_tiktok_file(tiktok_df: pd.DataFrame, tag_dfs: List[pd.DataFrame]) -> Tuple[pd.DataFrame, List[str]]:
    """Process TikTok file with tag files and return updated dataframe and log messages."""
    updated_df = tiktok_df.copy()
    log_messages = []
    
    # Track matches and updates
    total_rows = len(updated_df)
    matches_found = 0
    click_url_updates = 0
    impression_url_updates = 0
    
    for idx, row in updated_df.iterrows():
        campaign_name = row.get('Campaign Name', '')
        ad_group_name = row.get('Ad Group Name', '')
        ad_name = row.get('Ad Name', '')
        
        # Try to find match in any of the tag files
        matching_tag_row = None
        source_file_idx = None
        
        for file_idx, tag_df in enumerate(tag_dfs):
            matching_tag_row = find_matching_tag_row(row, tag_df)
            if matching_tag_row is not None:
                source_file_idx = file_idx
                break
        
        if matching_tag_row is not None:
            matches_found += 1
            
            # Update Click URL
            original_click_url = row.get('Click URL', '')
            click_tracker = matching_tag_row.get('Click Tracker', '')
            
            updated_click_url = update_click_url(original_click_url, click_tracker, campaign_name)
            
            if updated_click_url != original_click_url:
                updated_df.at[idx, 'Click URL'] = updated_click_url
                click_url_updates += 1
            
            # Update Impression tracking URL
            impression_tracker = matching_tag_row.get('Impression Tracker', '')
            if impression_tracker and not pd.isna(impression_tracker):
                extracted_impression_url = extract_url_from_quotes(str(impression_tracker))
                if extracted_impression_url:
                    updated_df.at[idx, 'Impression tracking URL'] = extracted_impression_url
                    impression_url_updates += 1
        else:
            log_messages.append(f"No match found for: Campaign='{campaign_name}', Ad Group='{ad_group_name}', Ad='{ad_name}'")
    
    # Summary log messages
    log_messages.insert(0, f"Processing complete:")
    log_messages.insert(1, f"  • Total rows processed: {total_rows}")
    log_messages.insert(2, f"  • Matches found: {matches_found}")
    log_messages.insert(3, f"  • Click URL updates: {click_url_updates}")
    log_messages.insert(4, f"  • Impression URL updates: {impression_url_updates}")
    log_messages.insert(5, "")
    
    return updated_df, log_messages

def main():
    st.set_page_config(
        page_title="TikTok Tracking Tag Updater",
        page_icon="🎯",
        layout="wide"
    )
    
    st.title("🎯 TikTok Tracking Tag Updater")
    st.markdown("Upload your TikTok export file and DCM tag files to automatically update tracking URLs.")
    
    # File upload section
    st.header("📁 File Upload")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("TikTok Export File")
        tiktok_file = st.file_uploader(
            "Upload TikTok export file (Excel)",
            type=['xlsx', 'xls'],
            key="tiktok_file",
            help="Excel file with 'Ads' sheet containing Campaign Name, Ad Group Name, Ad Name, Click URL, and Impression tracking URL columns"
        )
    
    with col2:
        st.subheader("DCM Tag Files")
        tag_files = st.file_uploader(
            "Upload DCM tag files (Excel)",
            type=['xlsx', 'xls'],
            accept_multiple_files=True,
            key="tag_files",
            help="Excel files with headers in row 11, containing Campaign Name, Placement Name, Ad Name, Click Tracker, and Impression Tracker columns"
        )
    
    if tiktok_file and tag_files:
        try:
            # Load TikTok file
            st.header("📊 Processing Files")
            
            with st.spinner("Loading TikTok export file..."):
                tiktok_df = pd.read_excel(tiktok_file, sheet_name='Ads')
                st.success(f"✅ TikTok file loaded: {len(tiktok_df)} rows")
            
            # Load tag files
            tag_dfs = []
            with st.spinner("Loading DCM tag files..."):
                for i, tag_file in enumerate(tag_files):
                    tag_df = pd.read_excel(tag_file, header=10)  # Headers in row 11
                    tag_dfs.append(tag_df)
                    st.success(f"✅ Tag file {i+1} loaded: {len(tag_df)} rows")
            
            # Validate required columns
            required_tiktok_cols = ['Campaign Name', 'Ad Group Name', 'Ad Name', 'Click URL', 'Impression tracking URL']
            required_tag_cols = ['Campaign Name', 'Placement Name', 'Ad Name', 'Click Tracker', 'Impression Tracker']
            
            missing_tiktok_cols = [col for col in required_tiktok_cols if col not in tiktok_df.columns]
            if missing_tiktok_cols:
                st.error(f"❌ Missing columns in TikTok file: {missing_tiktok_cols}")
                return
            
            for i, tag_df in enumerate(tag_dfs):
                missing_tag_cols = [col for col in required_tag_cols if col not in tag_df.columns]
                if missing_tag_cols:
                    st.error(f"❌ Missing columns in tag file {i+1}: {missing_tag_cols}")
                    return
            
            # Process files
            st.header("🔄 Processing")
            
            with st.spinner("Updating tracking URLs..."):
                updated_df, log_messages = process_tiktok_file(tiktok_df, tag_dfs)
            
            # Display results
            st.header("📈 Results")
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.subheader("Processing Log")
                for message in log_messages:
                    if message.startswith("  •"):
                        st.write(message)
                    elif message.strip():
                        st.text(message)
            
            with col2:
                st.subheader("Preview Updated Data")
                st.dataframe(
                    updated_df[['Campaign Name', 'Ad Group Name', 'Ad Name', 'Click URL', 'Impression tracking URL']].head(10),
                    use_container_width=True
                )
            
            # Download section
            st.header("⬇️ Download Updated File")
            
            # Convert to Excel
            output_buffer = io.BytesIO()
            with pd.ExcelWriter(output_buffer, engine='openpyxl') as writer:
                updated_df.to_excel(writer, sheet_name='Ads', index=False)
            
            output_buffer.seek(0)
            
            st.download_button(
                label="📥 Download Updated TikTok File",
                data=output_buffer.getvalue(),
                file_name="updated_tiktok_export.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
            
            # Show detailed log if there are unmatched rows
            unmatched_messages = [msg for msg in log_messages if msg.startswith("No match found")]
            if unmatched_messages:
                with st.expander(f"⚠️ Unmatched Rows ({len(unmatched_messages)})", expanded=False):
                    for message in unmatched_messages:
                        st.text(message)
        
        except Exception as e:
            st.error(f"❌ Error processing files: {str(e)}")
            st.exception(e)
    
    # Instructions
    st.header("📋 Instructions")
    st.markdown("""
    ### How to use this tool:
    
    1. **Upload TikTok Export File**: 
       - Excel file with an 'Ads' sheet
       - Must contain: Campaign Name, Ad Group Name, Ad Name, Click URL, Impression tracking URL
    
    2. **Upload DCM Tag Files**: 
       - One or more Excel files with headers in row 11
       - Must contain: Campaign Name, Placement Name, Ad Name, Click Tracker, Impression Tracker
    
    3. **Matching Logic**:
       - Rows are matched using Campaign Name, Ad Group Name (TikTok) = Placement Name (DCM), and Ad Name
    
    4. **Updates Applied**:
       - **Click URL**: Prepends click tracker and adds missing UTM/TF parameters
       - **Impression URL**: Extracts URL from quotes in impression tracker
    
    5. **Download**: Get your updated TikTok export file with tracking URLs updated
    
    ### UTM/TF Parameters Added (if missing):
    - `utm_source=tiktok`, `utm_medium=paid`, `utm_campaign=<Campaign Name>`
    - `tf_source=tiktok`, `tf_medium=paid_social`, `tf_campaign=<Campaign Name>`
    """)

if __name__ == "__main__":
    main()