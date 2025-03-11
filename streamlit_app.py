import streamlit as st
import pandas as pd
from url_processor import validate_excel_file, process_url
from st_aggrid import AgGrid, GridOptionsBuilder
import concurrent.futures
import os
from io import BytesIO

# Page configuration
st.set_page_config(
    page_title="Dlr URL Processor",
    page_icon="🌐",
    layout="wide"
)

# Initialize session state
if 'processing_results' not in st.session_state:
    st.session_state.processing_results = []
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

# Load custom CSS
with open('assets/custom.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def check_password():
    """Returns `True` if the user had the correct password."""
    if st.session_state.get('authenticated'):
        return True

    # Show login form
    st.title("🔐 Login required for intuitive-URL Processor")
    username = st.text_input("Username", key="username_input")
    password = st.text_input("Password", type="password", key="password_input")

    if st.button("Login"):
        if username == "intuitive-data" and password == "Z7A3Id9FjPcf":
            st.session_state.authenticated = True
            st.success("Logged in successfully!")
            st.rerun()
        else:
            st.error("Invalid username or password")
            return False
    return False

# Main application
if check_password():
    # Header
    st.title("🌐 URL Processor")
    st.markdown("""
    Process multiple URLs from an Excel file and analyze their content.
    Upload an Excel file containing URLs and their categories to begin.
    """)

    # File upload section
    uploaded_file = st.file_uploader("Upload Excel File", type=['xlsx'])

    if uploaded_file:
        is_valid, error_message, df = validate_excel_file(uploaded_file)

        if not is_valid:
            st.error(error_message)
        else:
            st.success("File uploaded successfully!")

            # Display input data
            st.subheader("Input Data Preview")
            grid_options = GridOptionsBuilder.from_dataframe(df)
            grid_options.configure_default_column(editable=False, groupable=True)
            AgGrid(df, gridOptions=grid_options.build(), height=300)

            # Process button
            if st.button("Process URLs"):
                # Reset results
                st.session_state.processing_results = []

                # Setup progress tracking
                total_urls = len(df)
                progress_bar = st.progress(0)
                status_text = st.empty()

                # Process URLs in parallel without callbacks
                with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                    # Submit all jobs
                    future_to_url = {
                        executor.submit(
                            process_url,
                            url=row['URL'],
                            category=row['Category']
                        ): idx for idx, row in df.iterrows()
                    }

                    # Track completed URLs
                    completed = 0

                    # Process results as they complete
                    for future in concurrent.futures.as_completed(future_to_url):
                        url_idx = future_to_url[future]
                        try:
                            result = future.result()
                            st.session_state.processing_results.append(result)
                        except Exception as e:
                            st.error(f"Error processing URL {df.iloc[url_idx]['URL']}: {str(e)}")

                        # Update progress
                        completed += 1
                        progress = completed / total_urls
                        progress_bar.progress(progress)
                        status_text.text(f"Processing: {completed}/{total_urls} URLs")

                # Display results
                if st.session_state.processing_results:
                    st.subheader("Processing Results")

                    results_df = pd.DataFrame(st.session_state.processing_results)

                    # Success/Error statistics
                    success_count = len(results_df[results_df['status'] == 'success'])
                    error_count = len(results_df[results_df['status'] == 'error'])

                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Successfully Processed", success_count)
                    with col2:
                        st.metric("Errors", error_count)

                    # Display results table
                    grid_options = GridOptionsBuilder.from_dataframe(results_df)
                    grid_options.configure_default_column(editable=False, groupable=True)
                    grid_options.configure_column("full_text", maxWidth=300)
                    AgGrid(results_df, gridOptions=grid_options.build(), height=500)

                    # Export results button with download functionality
                    buffer = BytesIO()
                    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                        results_df.to_excel(writer, index=False)

                    # Generate filename with timestamp
                    timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"processed_urls_{timestamp}.xlsx"

                    st.download_button(
                        label="📥 Download Results",
                        data=buffer.getvalue(),
                        file_name=filename,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

    # Add logout button in sidebar
    with st.sidebar:
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.rerun()

# Footer
st.markdown("---")
st.markdown("Made with ❤️ using Streamlit")
