
"""
QueryForge - Streamlit UI interface.
"""

import streamlit as st
import asyncio
from datetime import datetime
from typing import Optional

from core.config import Config, write_env
from core.models import Schema
from core.storage import SchemaStorage
from core.generator import generator
from core.safety import validate_query_safety

# Page configuration
st.set_page_config(
    page_title="QueryForge",
    layout="wide",
    page_icon="🔧"
)

# Initialize storage
storage = SchemaStorage()

def sidebar_navigation():
    """Simple sidebar navigation."""
    st.sidebar.title("🔧 QueryForge")
    
    page = st.sidebar.selectbox(
        "Navigate to:",
        ["Generate", "Schemas", "Settings"]
    )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**Provider:** {Config.PROVIDER}")
    
    if Config.is_api_key_configured():
        st.sidebar.success("✅ API Key: Configured")
    else:
        st.sidebar.error("❌ API Key: Not configured")
    
    return page

def generate_page():
    """Query generation page."""
    st.title("🚀 Generate Query")
    st.markdown("Convert natural language to SQL/NoSQL queries")
    
    # Check configuration first
    is_valid, issues = Config.validate_config()
    if not is_valid:
        st.error("⚠️ Configuration Issues:")
        for issue in issues:
            st.error(f"• {issue}")
        st.info("Please configure your settings before generating queries.")
        return
    
    with st.form("query_form"):
        # Question input
        question = st.text_area(
            "Question",
            placeholder="Find all users who registered in the last 30 days",
            height=100
        )
        
        # Configuration row
        col1, col2, col3 = st.columns(3)
        
        with col1:
            database_type = st.selectbox(
                "Database Type",
                Config.SUPPORTED_DATABASES
            )
        
        with col2:
            model = st.selectbox(
                "Model",
                Config.OPENAI_MODELS,
                index=0
            )
        
        with col3:
            strict = st.checkbox(
                "Strict Mode (SELECT-only)",
                value=True
            )
        
        # Row limit
        row_limit = st.number_input(
            "Row Limit",
            min_value=1,
            max_value=Config.ROW_LIMIT_MAX,
            value=Config.ROW_LIMIT_DEFAULT,
            step=100
        )
        
        # Schema source
        st.markdown("**Schema Source**")
        schema_option = st.radio(
            "Choose schema source:",
            ["None", "Select saved schema", "Paste schema text"],
            horizontal=True
        )
        
        schema_text = None
        schema_id = None
        
        if schema_option == "Select saved schema":
            schemas = storage.list_schemas()
            if schemas:
                schema_names = [f"{s.name} ({s.database_type})" for s in schemas]
                selected = st.selectbox("Select schema:", schema_names)
                if selected:
                    schema_id = schemas[schema_names.index(selected)].id
            else:
                st.info("No saved schemas found. Create one in the Schemas page.")
        
        elif schema_option == "Paste schema text":
            schema_text = st.text_area(
                "Schema",
                placeholder="CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(100));",
                height=100
            )
        
        # Generate button
        generate_clicked = st.form_submit_button("🔮 Generate Query", type="primary")
    
    # Generate query
    if generate_clicked:
        if not question.strip():
            st.error("Please enter a question.")
            return
        
        with st.spinner("Generating query..."):
            try:
                # Run async function in sync context
                query, error = asyncio.run(generator.generate_query(
                    question=question,
                    database_type=database_type,
                    model=model,
                    schema_text=schema_text,
                    schema_id=schema_id,
                    strict=strict,
                    row_limit=row_limit
                ))
                
                if error:
                    st.error(f"❌ Generation failed: {error}")
                else:
                    st.success("✅ Query generated successfully!")
                    
                    # Display result
                    st.markdown("**Generated Query:**")
                    if database_type.lower() == "mongodb":
                        st.code(query, language="json")
                    else:
                        st.code(query, language="sql")
                    
                    # Copy to clipboard helper
                    st.info("💡 Tip: Click inside the code block and use Ctrl+A, Ctrl+C to copy")
                    
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

def schemas_page():
    """Schema management page."""
    st.title("📋 Schemas")
    
    tab1, tab2 = st.tabs(["➕ Add Schema", "📚 Saved Schemas"])
    
    with tab1:
        st.markdown("**Add New Schema**")
        
        with st.form("add_schema"):
            name = st.text_input("Name", placeholder="My Database Schema")
            database_type = st.selectbox("Database Type", Config.SUPPORTED_DATABASES)
            content = st.text_area(
                "Content",
                placeholder="CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(100));",
                height=200
            )
            
            if st.form_submit_button("💾 Save Schema", type="primary"):
                if not name.strip():
                    st.error("Please enter a schema name.")
                elif not content.strip():
                    st.error("Please enter schema content.")
                else:
                    try:
                        schema = Schema(
                            name=name.strip(),
                            database_type=database_type,
                            content=content.strip()
                        )
                        storage.save_schema(schema)
                        st.success(f"✅ Schema '{name}' saved successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error saving schema: {str(e)}")
    
    with tab2:
        st.markdown("**Saved Schemas**")
        
        schemas = storage.list_schemas()
        
        if not schemas:
            st.info("No schemas saved yet.")
        else:
            for schema in schemas:
                with st.expander(f"📄 {schema.name} ({schema.database_type})"):
                    st.markdown(f"**Created:** {schema.created_at}")
                    st.markdown(f"**Updated:** {schema.updated_at}")
                    st.code(schema.content, language="sql")
                    
                    if st.button(f"🗑️ Delete {schema.name}", key=f"delete_{schema.id}"):
                        storage.delete_schema(schema.id)
                        st.success(f"✅ Schema '{schema.name}' deleted")
                        st.rerun()

def settings_page():
    """Settings and configuration page."""
    st.title("⚙️ Settings")
    
    # Current configuration
    st.markdown("**Current Configuration**")
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Provider", Config.PROVIDER)
        st.metric("Model", Config.MODEL_CHAT)
    
    with col2:
        st.metric("Storage Path", str(Config.STORAGE_DIR))
        st.metric("Row Limit Default", f"{Config.ROW_LIMIT_DEFAULT:,}")
    
    st.markdown("---")
    
    # API Key Settings
    st.markdown("**🔑 OpenAI API Key**")
    
    with st.form("api_key_form"):
        current_key = "✅ Configured" if Config.is_api_key_configured() else "❌ Not configured"
        st.info(f"Current status: {current_key}")
        
        api_key = st.text_input(
            "API Key",
            type="password",
            placeholder="sk-..."
        )
        
        if st.form_submit_button("💾 Save API Key", type="primary"):
            if api_key.strip():
                try:
                    write_env("OPENAI_API_KEY", api_key.strip())
                    Config.reload_config()
                    st.success("✅ API key saved successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error saving API key: {str(e)}")
            else:
                st.error("Please enter an API key")
    
    st.markdown("---")
    
    # Row Limit Settings
    st.markdown("**📊 Default Row Limit**")
    
    with st.form("row_limit_form"):
        new_row_limit = st.number_input(
            "Default Row Limit",
            min_value=1,
            max_value=Config.ROW_LIMIT_MAX,
            value=Config.ROW_LIMIT_DEFAULT,
            step=100
        )
        
        if st.form_submit_button("💾 Save Row Limit", type="primary"):
            try:
                write_env("ROW_LIMIT_DEFAULT", str(new_row_limit))
                Config.reload_config()
                st.success("✅ Row limit saved successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error saving row limit: {str(e)}")
    
    st.markdown("---")
    
    # Help section
    st.markdown("**❓ Help**")
    
    with st.expander("How to get an OpenAI API key"):
        st.markdown("""
        1. Go to https://platform.openai.com/api-keys
        2. Sign in to your OpenAI account
        3. Click "Create new secret key"
        4. Copy the key and paste it above
        5. Make sure you have credits in your OpenAI account
        """)
    
    with st.expander("Schema format examples"):
        st.markdown("**SQL Schema:**")
        st.code("""CREATE TABLE users (
    id INT PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100),
    created_at TIMESTAMP
);""", language="sql")
        
        st.markdown("**MongoDB Schema:**")
        st.code("""{
  "users": {
    "_id": "ObjectId",
    "name": "string",
    "email": "string",
    "created_at": "Date"
  }
}""", language="json")

def main():
    """Main application."""
    try:
        page = sidebar_navigation()
        
        if page == "Generate":
            generate_page()
        elif page == "Schemas":
            schemas_page()
        elif page == "Settings":
            settings_page()
            
    except Exception as e:
        st.error(f"❌ Application Error: {str(e)}")
        st.info("Please refresh the page or check your configuration.")

if __name__ == "__main__":
    main()
