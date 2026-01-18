# Emoji library https://emojidb.org/openai-emojis
"""
general
☰ list
⚖️ scale
📘📕📓 book
📖 book open
📚 book stack
📥 📩book with arrow (use this for download)
📄 paper written
📝 ✒ paper written pencil
🔍 mag glass (search)
🗒️ list

📊📂database main
📋➕✏️✔️


⚠️ error
⚙️ ⚒ settings
🗑️ delete
💡bulb idea
❌✅🚫

📌pin

💻🗝️🔐🛍️login
🏣🏛️👩🏻‍💼🏫institution
👨‍👨‍👦‍👦 user select

🧮💭process loop

others maybe useful
📈🔄🔔⌨

"""
import re
import streamlit as st
import pandas as pd

from core.qa_engine import (
    get_answer_for_app,
    generate_starter_questions,
    generate_followup_questions,
    laws
)

from contract_generation.generator import generate_contract_for_app
from uploaded_docs.doc_ingest import extract_text_from_pdf, extract_text_from_docx, split_into_sections
from uploaded_docs.doc_qa import ask_uploaded_doc, summarize_uploaded_doc, extract_key_clauses
from uploaded_contracts.contract_ingest import extract_text_from_pdf as extract_contract_pdf, extract_text_from_docx as extract_contract_docx, split_into_clauses
from uploaded_contracts.contract_analysis import analyze_risks, validate_contract, extract_obligations_rights

# first do the main page 
# then add the sessions and replace and add the api key bar instead of hard code
st.set_page_config(
    page_title="Malaysian Legal Assistant",
    page_icon="⚖️",
    layout="wide"
)

for key in ["chat_history", "starter_questions", "followups", "current_input", "api_key",
            "uploaded_sections", "uploaded_doc_name",
            "uploaded_contract_sections", "uploaded_contract_name"]:
    if key not in st.session_state:
        st.session_state[key] = None if "sections" in key or "name" in key else [] if "questions" in key or "chat" in key else ""

st.sidebar.subheader("OpenAI API Key")
api_key_input = st.sidebar.text_input(
    "Enter your OpenAI API Key:",
    type="password",
    value=st.session_state.api_key if st.session_state.api_key else ""
)

if api_key_input and api_key_input.startswith("sk-"):
    st.session_state.api_key = api_key_input
elif api_key_input and not api_key_input.startswith("sk-"):
    st.sidebar.error("⚠️ OpenAI API keys should start with 'sk-'")
    st.session_state.api_key = ""
else:
    st.session_state.api_key = ""

st.sidebar.title("Mode")
mode = st.sidebar.radio(
    "Choose function:",
    ["📘 Legal Q&A", "📄 Contract Generator", "🔍 Uploaded Contract Analyzer", "⚙️ Law Database Manager"]
)


# LEGAL Q&A MODE
if mode == "📘 Legal Q&A":
    st.title("⚖️ Malaysian Law Q&A Assistant")

    source = st.radio(
        "Select knowledge source:",
        ["Malaysian Law Database", "Uploaded Document"]
    )

    if source == "Malaysian Law Database":
        # Check API key 
        if not st.session_state.api_key or st.session_state.api_key.strip() == "":
            st.warning("⚠️ Please enter your OpenAI API Key in the sidebar to continue.")
            st.stop()
        
        # Generate question
        if not st.session_state.starter_questions:
            try:
                with st.spinner("Generating starter questions..."):
                    st.session_state.starter_questions = generate_starter_questions(laws, st.session_state.api_key)
            except Exception as e:
                st.error(f"Error generating starter questions: {str(e)}")
                st.info("You can still ask questions directly below.")
                st.session_state.starter_questions = []

        # Chat history
        for chat in st.session_state.chat_history:
            st.markdown(f"**You:** {chat['question']}")
            
            if chat.get('selected_acts'):
                with st.expander("📚 Acts Consulted", expanded=False):
                    for act in chat['selected_acts']:
                        st.markdown(f"- {act}")
            
            st.markdown(f"**Assistant:**")
            st.markdown(chat['answer'])
            
            # references
            if chat.get('references'):
                with st.expander("📖 Legal References Used", expanded=False):
                    for ref in chat['references']:
                        matched_kw = ", ".join(ref['matched_keywords'][:5]) if ref['matched_keywords'] else "N/A"
                        st.markdown(f"""
                        **{ref['act']}** - Section {ref['section']}
                        - Matched keywords: `{matched_kw}`
                        """)
            
            st.markdown("---")

        # Suggestions
        if not st.session_state.chat_history:
            st.subheader("Suggested starter questions")
            for q in st.session_state.starter_questions:
                if st.button(q, key=f"starter_{q}"):
                    st.session_state.current_input = q
                    st.rerun()
        elif st.session_state.followups:
            st.subheader("Suggested follow-up questions")
            for q in st.session_state.followups:
                if st.button(q, key=f"followup_{q}"):
                    st.session_state.current_input = q
                    st.rerun()

        st.divider()
        with st.form("chat_input", clear_on_submit=True):
            user_question = st.text_input(
                "Ask a question about Malaysian law:",
                value=st.session_state.current_input
            )
            submitted = st.form_submit_button("Ask")

        if submitted and user_question.strip() and st.session_state.api_key:
            st.session_state.followups = []
            st.session_state.current_input = ""

            with st.spinner("🔍 Analyzing Malaysian law..."):
                # Get enhanced response
                result = get_answer_for_app(user_question, st.session_state.api_key)

            st.session_state.chat_history.append({
                "question": user_question,
                "answer": result['answer'],
                "references": result['references'],
                "selected_acts": result['selected_acts'],
                "selected_sections": result.get('selected_sections', [])
            })
            st.session_state.followups = result['followups']
            st.rerun()

    else: 
        st.subheader("Upload PDF or Word Document for Q&A")
        uploaded_file = st.file_uploader(
            "Upload PDF or Word document",
            type=["pdf", "docx"]
        )

        if uploaded_file:
            if uploaded_file.type == "application/pdf":
                text = extract_text_from_pdf(uploaded_file)
            else:
                text = extract_text_from_docx(uploaded_file)

            st.session_state.uploaded_sections = split_into_sections(
                text,
                act_name=uploaded_file.name
            )
            st.session_state.uploaded_doc_name = uploaded_file.name
            st.success(f"Loaded: {uploaded_file.name}")

        if st.session_state.uploaded_sections:
            action = st.selectbox(
                "Choose action",
                ["Ask a Question", "Summarize Document", "Extract Important Clauses"]
            )

            if action == "Ask a Question":
                q = st.text_input("Enter your question")
                if st.button("Ask") and q:
                    answer = ask_uploaded_doc(
                        q,
                        st.session_state.uploaded_sections,
                        st.session_state.api_key
                    )
                    st.markdown(answer)

            elif action == "Summarize Document":
                if st.button("Generate Summary"):
                    summary = summarize_uploaded_doc(
                        st.session_state.uploaded_sections,
                        st.session_state.api_key
                    )
                    st.markdown(summary)

            elif action == "Extract Important Clauses":
                if st.button("Extract"):
                    clauses = extract_key_clauses(
                        st.session_state.uploaded_sections,
                        st.session_state.api_key
                    )
                    st.markdown(clauses)

            if st.button("Remove Document"):
                st.session_state.uploaded_sections = None
                st.session_state.uploaded_doc_name = ""
                st.rerun()

# CONTRACT GENERATOR
elif mode == "📄 Contract Generator":
    st.title("📄 Malaysian Contract Generator")

    contract_type = st.selectbox(
        "Select contract type",
        [
            "Employment Contract",
            "Tenancy Agreement",
            "Non-Disclosure Agreement (NDA)",
            "Intellectual Property Agreement",
            "General Contract under Contracts Act 1950"
        ]
    )

    contract_fields = {
        "Employment Contract": ["Employee Name", "Employer Name", "Start Date", "Salary", "Position"],
        "Tenancy Agreement": ["Tenant Name", "Landlord Name", "Property Address", "Rent", "Start Date", "End Date"],
        "Non-Disclosure Agreement (NDA)": ["Party A", "Party B", "Effective Date", "Confidential Information Details", "Term"],
        "Intellectual Property Agreement": ["Owner", "Recipient", "IP Type", "Effective Date", "Term"],
        "General Contract under Contracts Act 1950": ["Party A", "Party B", "Effective Date", "Terms"]
    }

    st.subheader("Enter Contract Details")
    user_input = {}
    for field in contract_fields.get(contract_type, []):
        user_input[field] = st.text_input(field)

    additional_info = st.text_area("Additional Information (optional)")

    if st.button("Generate Contract") and st.session_state.api_key:
        user_input_text = "\n".join(f"{k}: {v}" for k, v in user_input.items())
        if additional_info.strip():
            user_input_text += f"\nAdditional Information: {additional_info}"

        with st.spinner("🔍 Analyzing applicable laws and drafting contract..."):
            result = generate_contract_for_app(
                contract_type,
                user_input_text,
                pdf=True,
                api_key=st.session_state.api_key
            )

        # Display relevant acts 
        st.subheader("📚 Legal Framework")
        with st.expander("Acts Consulted", expanded=True):
            for act in result['relevant_acts']:
                st.markdown(f"- {act}")

        # full response
        st.subheader("Generated Contract with Legal Reasoning")
        st.markdown(result['full_response'])

        # law references 
        if result['law_references']:
            with st.expander("📖 Law Sections Referenced", expanded=False):
                for ref in result['law_references']:
                    st.markdown(f"""
                    **{ref['act']}** - Section {ref['section']}
                    - {ref['title']}
                    """)

        # Download
        if result['pdf_path'] or result['word_path']:
            st.divider()
            st.subheader("📥 Download Contract")
            col1, col2, col3 = st.columns([1, 1, 2])
            
            with col1:
                if result['pdf_path']:
                    with open(result['pdf_path'], "rb") as f:
                        st.download_button(
                            label="📄 Download PDF",
                            data=f,
                            file_name=f"{contract_type.replace(' ', '_')}.pdf",
                            mime="application/pdf"
                        )
            
            with col2:
                if result['word_path']:
                    with open(result['word_path'], "rb") as f:
                        st.download_button(
                            label="📝 Download Word",
                            data=f,
                            file_name=f"{contract_type.replace(' ', '_')}.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        )
            
            with col3:
                st.caption("💡 Both files contain only the contract text (without analysis/reasoning). Word format is editable.")


# UPLOADED CONTRACT ANALYZER
elif mode == "🔍 Uploaded Contract Analyzer":
    st.title("🔍 Uploaded Contract Analyzer")
    uploaded_file = st.file_uploader(
        "Upload PDF or Word Contract",
        type=["pdf", "docx"]
    )

    if uploaded_file:
        if uploaded_file.type == "application/pdf":
            text = extract_contract_pdf(uploaded_file)
        else:
            text = extract_contract_docx(uploaded_file)

        st.session_state.uploaded_contract_sections = split_into_clauses(
            text,
            contract_name=uploaded_file.name
        )
        st.session_state.uploaded_contract_name = uploaded_file.name
        st.success(f"Loaded: {uploaded_file.name}")

    if st.session_state.uploaded_contract_sections:
        action = st.selectbox(
            "Choose action",
            ["Query Contract", "Risk Analysis", "Validate Contract", "Extract Obligations/Rights"]
        )

        if action == "Query Contract":
            st.subheader("Ask Questions About This Contract")
            q = st.text_input("Enter your question about the contract")
            if st.button("Ask") and q and st.session_state.api_key:
                with st.spinner("Analyzing contract..."):
                    from uploaded_contracts.contract_analysis import query_contract
                    answer = query_contract(
                        q,
                        st.session_state.uploaded_contract_sections,
                        st.session_state.api_key
                    )
                st.markdown(answer)

        elif action == "Risk Analysis":
            if st.button("Analyze Risks"):
                report = analyze_risks(
                    st.session_state.uploaded_contract_sections,
                    st.session_state.api_key
                )
                st.markdown(report)

        elif action == "Validate Contract":
            if st.button("Validate"):
                report = validate_contract(
                    st.session_state.uploaded_contract_sections,
                    st.session_state.api_key
                )
                st.markdown(report)

        elif action == "Extract Obligations/Rights":
            if st.button("Extract"):
                report = extract_obligations_rights(
                    st.session_state.uploaded_contract_sections,
                    st.session_state.api_key
                )
                st.markdown(report)

        if st.button("Remove Contract"):
            st.session_state.uploaded_contract_sections = None
            st.session_state.uploaded_contract_name = ""
            st.rerun()

# LAW DATABASE MANAGER
else:
    st.title("⚙️ Law Database Manager")
    
    from law_management.manager import (
        get_all_laws, get_law_by_key, add_law, 
        update_law, delete_law, get_law_stats
    )
    from law_management.validator import validate_law_file
    from law_management.schema import create_law_schema
    import json
    
    # Stats overview
    stats = get_law_stats()
    st.subheader("📊 Database Statistics")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Laws", stats['total_laws'])
    with col2:
        st.metric("Total Sections", stats['total_sections'])
    with col3:
        if stats['oldest_year'] and stats['newest_year']:
            st.metric("Year Range", f"{stats['oldest_year']} - {stats['newest_year']}")
    
    st.divider()
    
    #  tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📋 View All", "➕ Add New", "✏️ Update", "🗑️ Delete"])
    
    # view all laws
    # add new law
    # update existing law
    #delete 
    with tab1:
        st.subheader("All Laws in Database")
        laws = get_all_laws()
        
        if laws:
            import pandas as pd
            df = pd.DataFrame(laws)
            df = df[['act_name', 'file_key', 'year', 'version', 'total_sections', 'last_updated']]
            df.columns = ['Act Name', 'File Key', 'Year', 'Version', 'Sections', 'Last Updated']
            st.dataframe(df, use_container_width=True)
            
            st.subheader("View Law Details")
            selected_key = st.selectbox("Select a law to view:", [law['file_key'] for law in laws])
            
            if selected_key:
                law_data = get_law_by_key(selected_key)
                if law_data:
                    st.json(law_data['metadata'])
                    st.caption(f"Contains {len(law_data['sections'])} sections")
        else:
            st.info("No laws in database")
    

    with tab2:
        st.subheader("Add New Law")
        st.info("Upload a JSON file following the standard schema, or create one from scratch.")
        
        upload_method = st.radio("How would you like to add the law?", 
                                 ["Upload JSON File", "Create from Scratch"])
        
        if upload_method == "Upload JSON File":
            uploaded_file = st.file_uploader("Upload Law JSON", type=['json'])
            
            if uploaded_file:
                try:
                    data = json.load(uploaded_file)
                    
                    is_valid, errors = validate_law_file(data)
                    
                    if is_valid:
                        st.success("✅ File is valid!")
                        st.json(data['metadata'])
                        
                        if st.button("Add to Database"):
                            success, message = add_law(data)
                            if success:
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)
                    else:
                        st.error("❌ Validation failed:")
                        for error in errors:
                            st.write(f"- {error}")
                except Exception as e:
                    st.error(f"Error reading file: {str(e)}")
        
        else: 
            st.write("**Enter Law Metadata:**")
            col1, col2 = st.columns(2)
            with col1:
                act_name = st.text_input("Act Name", placeholder="e.g., Contracts Act 1950")
                file_key = st.text_input("File Key", placeholder="e.g., contracts_act_1950")
                year = st.text_input("Year", placeholder="e.g., 1950")
            with col2:
                version = st.text_input("Version", value="1.0")
                source = st.text_input("Source", value="Official gazette")
            
            sections_json = st.text_area(
                "Sections (JSON array):",
                placeholder='[{"section": "1", "title": "...", "text": "..."}]',
                height=200
            )
            
            if st.button("Create Law"):
                if not all([act_name, file_key, year, sections_json]):
                    st.error("Please fill in all required fields")
                else:
                    try:
                        sections = json.loads(sections_json)
                        data = create_law_schema(
                            act_name=act_name,
                            file_key=file_key,
                            year=year,
                            sections=sections,
                            version=version,
                            source=source
                        )
                        
                        success, message = add_law(data)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                    except json.JSONDecodeError:
                        st.error("Invalid JSON in sections")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
    
    with tab3:
        st.subheader("Update Existing Law")
        
        laws = get_all_laws()
        if laws:
            selected_key = st.selectbox("Select law to update:", [law['file_key'] for law in laws], key="update_select")
            
            if selected_key:
                current_law = get_law_by_key(selected_key)
                st.write("**Current Version:**")
                st.json(current_law['metadata'])
                
                st.write("**Upload New Version:**")
                new_file = st.file_uploader("Upload updated JSON", type=['json'], key="update_upload")
                
                if new_file:
                    try:
                        new_data = json.load(new_file)
                        
                        is_valid, errors = validate_law_file(new_data)
                        
                        if is_valid:
                            st.success("✅ New file is valid!")
                            
                            from law_management.validator import compare_versions
                            comparison = compare_versions(current_law, new_data)
                            
                            st.write("**Changes:**")
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Sections Added", comparison['sections_added'])
                            with col2:
                                st.metric("Sections Modified", comparison['sections_modified'])
                            with col3:
                                st.metric("Sections Removed", comparison['sections_removed'])
                            
                            if comparison['metadata_changes']:
                                st.write("**Metadata Changes:**")
                                for key, change in comparison['metadata_changes'].items():
                                    st.write(f"- {key}: `{change['old']}` → `{change['new']}`")
                            
                            check_version = st.checkbox("Enforce version check", value=True)
                            
                            if st.button("Update Law"):
                                success, message, comp = update_law(selected_key, new_data, check_version)
                                if success:
                                    st.success(message)
                                    st.rerun()
                                else:
                                    st.error(message)
                        else:
                            st.error("❌ Validation failed:")
                            for error in errors:
                                st.write(f"- {error}")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
        else:
            st.info("No laws in database to update")
    
    with tab4:
        st.subheader("Delete Law")
        st.warning("⚠️ This will remove the law from the database. A backup will be created.")
        
        laws = get_all_laws()
        if laws:
            selected_key = st.selectbox("Select law to delete:", [law['file_key'] for law in laws], key="delete_select")
            
            if selected_key:
                law_data = get_law_by_key(selected_key)
                st.write("**Law to Delete:**")
                st.json(law_data['metadata'])
                
                create_backup = st.checkbox("Create backup before deleting", value=True)
                confirm = st.checkbox("I confirm I want to delete this law")
                
                if confirm and st.button("🗑️ Delete Law", type="primary"):
                    success, message = delete_law(selected_key, create_backup)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
        else:
            st.info("No laws in database to delete")