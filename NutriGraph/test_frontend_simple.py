"""
Simple test to check if file upload is working in Streamlit
Run this instead of the full app to isolate the issue
"""

import streamlit as st
from io import BytesIO
from PIL import Image

st.title("File Upload Test")

uploaded_file = st.file_uploader("Upload Image", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    st.write("### File Info:")
    st.write(f"- Name: {uploaded_file.name}")
    st.write(f"- Type: {uploaded_file.type}")
    st.write(f"- Size: {uploaded_file.size} bytes")
    
    try:
        # Test 1: Read bytes
        st.write("\n### Test 1: Reading bytes...")
        file_bytes = uploaded_file.read()
        st.write(f"✓ Bytes read: {len(file_bytes)}")
        st.write(f"✓ First 20 bytes: {file_bytes[:20]}")
        
        # Test 2: Open as image
        st.write("\n### Test 2: Opening as image...")
        uploaded_file.seek(0)  # Reset pointer
        image = Image.open(uploaded_file)
        st.write(f"✓ Image format: {image.format}")
        st.write(f"✓ Image size: {image.size}")
        
        # Test 3: Display image
        st.write("\n### Test 3: Display image...")
        st.image(image, width=300)
        st.write("✓ Image displayed")
        
        # Test 4: Session state
        st.write("\n### Test 4: Session state...")
        if st.button("Store in Session State"):
            uploaded_file.seek(0)
            st.session_state.test_bytes = uploaded_file.read()
            st.session_state.test_name = uploaded_file.name
            st.write(f"✓ Stored {len(st.session_state.test_bytes)} bytes")
        
        if 'test_bytes' in st.session_state:
            st.write(f"✓ Session state has: {len(st.session_state.test_bytes)} bytes")
            
            # Test 5: Create BytesIO
            st.write("\n### Test 5: BytesIO wrapper...")
            bio = BytesIO(st.session_state.test_bytes)
            st.write(f"✓ BytesIO created")
            st.write(f"✓ BytesIO size: {len(bio.getvalue())} bytes")
        
        st.success("All tests passed! ✓")
        
    except Exception as e:
        st.error(f"ERROR: {type(e).__name__}: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
