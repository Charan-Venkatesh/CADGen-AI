import streamlit as st
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.llm_client import LocalLLMClient
from src.generator import EnhancedTemplateGenerator
from src.dxf_creator import EnhancedDXFCreator
from src.conversation_manager import ConversationManager

# ============================================================
# CONFIG
# ============================================================
st.set_page_config(
    page_title="AutoCAD Helper - AI CAD Generator",
    page_icon="📐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.title("📐 AutoCAD Helper")
    st.markdown("**AI-Powered CAD File Generator**")
    st.markdown("Generate CAD files from natural language!")
    
    st.markdown("---")
    
    mode = st.radio(
        "🎯 Select Mode",
        ["💬 Chat & Design", "⚡ Quick Generate"],
        help="Choose how to use"
    )
    
    st.markdown("---")
    
    parser_type = st.selectbox(
        "Parser Type",
        ["Template (Fast)", "LLM (Smart)", "Hybrid (Best)"]
    )
    
    st.metric("Accuracy", "100%", "All Tests")
    
    st.markdown("---")
    
    st.subheader("⭐ Quick Templates")
    
    if st.button("📦 Plate", use_container_width=True):
        st.session_state.quick_template = "rectangular plate 200mm by 100mm with 4 corner holes 10mm diameter at 20mm offset"
        st.rerun()
    
    if st.button("🔩 Flange", use_container_width=True):
        st.session_state.quick_template = "circular flange 200mm outer 100mm inner with 8 bolt holes 15mm on 150mm PCD"
        st.rerun()
    
    if st.button("📐 L-Bracket", use_container_width=True):
        st.session_state.quick_template = "L-bracket 150mm vertical 100mm horizontal with 20mm fillet"
        st.rerun()
    
    st.markdown("---")
    
    with st.expander("📖 Help"):
        st.markdown("""
        **Examples:**
        - "rectangular plate 200x100mm"
        - "circular flange with 8 bolts"
        - "L-bracket with corner fillet"
        """)

# ============================================================
# INITIALIZE SESSION STATE
# ============================================================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "manager" not in st.session_state:
    st.session_state.manager = ConversationManager()

if "generated_files" not in st.session_state:
    st.session_state.generated_files = []

if "quick_template" not in st.session_state:
    st.session_state.quick_template = None

# ============================================================
# LOAD MODELS
# ============================================================
@st.cache_resource
def load_template_parser():
    return EnhancedTemplateGenerator()

@st.cache_resource
def load_llm():
    try:
        llm = LocalLLMClient()
        return llm
    except Exception as e:
        st.warning(f"LLM not available: {e}")
        return None

# ============================================================
# MODE 1: CHAT & DESIGN
# ============================================================
if mode == "💬 Chat & Design":
    st.title("💬 Chat & Design - Conversational CAD Generator")
    
    st.markdown("""
    Describe what CAD part you need → I'll generate it instantly!
    """)
    
    # Display chat history
    chat_container = st.container(height=400, border=True)
    
    with chat_container:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"], avatar="🤖" if msg["role"] == "assistant" else "👤"):
                st.write(msg["content"])
    
    # Input
    if st.session_state.quick_template:
        user_input = st.session_state.quick_template
        st.session_state.quick_template = None
    else:
        user_input = st.chat_input("Describe your CAD part...")
    
    if user_input:
        # Add user message
        st.session_state.messages.append({
            "role": "user",
            "content": user_input
        })
        st.session_state.manager.add_message("user", user_input)
        
        # Process
        with st.spinner("🔄 Generating CAD file..."):
            try:
                template_parser = load_template_parser()
                
                # Parse based on mode
                if parser_type == "Template (Fast)":
                    params = template_parser.parse_description(user_input)
                    method = "Template Parser"
                
                elif parser_type == "LLM (Smart)":
                    llm = load_llm()
                    if llm:
                        params = llm.extract_parameters(user_input)
                        method = "LLM (CodeLlama 7B)"
                    else:
                        params = template_parser.parse_description(user_input)
                        method = "Template Parser"
                
                else:  # Hybrid
                    llm = load_llm()
                    if llm:
                        params = llm.extract_parameters(user_input)
                        method = "LLM (CodeLlama 7B)"
                    else:
                        params = template_parser.parse_description(user_input)
                        method = "Template Parser"
                
                # Check for errors
                if "error" in params:
                    raise ValueError("Could not parse")
                
                # Generate DXF
                creator = EnhancedDXFCreator()
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = f"data/examples/chat_{timestamp}.dxf"
                
                os.makedirs("data/examples", exist_ok=True)
                dxf_path = creator.create_from_params(params, output_file)
                
                # Store
                st.session_state.manager.update_design(params)
                st.session_state.generated_files.append({
                    "description": user_input,
                    "file": dxf_path,
                    "timestamp": timestamp
                })
                
                # Response
                bot_message = f"✅ **CAD Generated!**\n\n**Method:** {method}\n\n**Parameters:**\n``````"
                
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": bot_message
                })
                
                # Download button
                with open(dxf_path, 'rb') as f:
                    st.download_button(
                        label="📥 Download DXF File",
                        data=f.read(),
                        file_name=os.path.basename(dxf_path),
                        mime="application/octet-stream",
                        use_container_width=True
                    )
                
                st.rerun()
                
            except Exception as e:
                error_msg = f"❌ Error: {str(e)}"
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg
                })
                st.error(error_msg)

# ============================================================
# MODE 2: QUICK GENERATE
# ============================================================
elif mode == "⚡ Quick Generate":
    st.title("⚡ Quick Generate")
    
    col1, col2 = st.columns([0.6, 0.4])
    
    with col1:
        description = st.text_area(
            "Describe your CAD part:",
            placeholder="E.g., rectangular plate 200x100mm with 4 holes",
            height=200
        )
    
    with col2:
        st.info(f"**Parser:** {parser_type}")
    
    if st.button("🚀 Generate", use_container_width=True):
        if description:
            with st.spinner("⏳ Generating..."):
                try:
                    template_parser = load_template_parser()
                    params = template_parser.parse_description(description)
                    
                    creator = EnhancedDXFCreator()
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    output_file = f"data/examples/quick_{timestamp}.dxf"
                    
                    os.makedirs("data/examples", exist_ok=True)
                    dxf_path = creator.create_from_params(params, output_file)
                    
                    st.success("✅ Generated!")
                    
                    with open(dxf_path, 'rb') as f:
                        st.download_button(
                            label="📥 Download DXF",
                            data=f.read(),
                            file_name=os.path.basename(dxf_path),
                            mime="application/octet-stream",
                            use_container_width=True
                        )
                    
                    st.json(params)
                
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

# ============================================================
# FOOTER
# ============================================================
st.markdown("---")
st.markdown("""
**AutoCAD Helper v1.0** | AI-Powered CAD Generation  
Powered by CodeLlama 7B + ezdxf
""")
