"""FinGuard Phase 2 analyst UI — single-user educational prototype."""
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'src'))

import streamlit as st
from finguard.service import process_file
from finguard.storage import connect, list_cases, review_case, get_case_transactions
from finguard.reports import make_docx, make_pdf

st.set_page_config(page_title='FinGuard | AML Screening', page_icon='🛡️', layout='wide', initial_sidebar_state='expanded')
st.markdown('''<style>
.block-container {max-width: 1250px; padding-top: 2rem}
h1, h2, h3 {letter-spacing: -.025em}
[data-testid="stMetric"] {background: #f2f5fa; padding: 15px; border-radius: 10px}
@media (prefers-color-scheme: dark) {[data-testid="stMetric"] {background: #1c2634}}
</style>''', unsafe_allow_html=True)

DB = os.getenv('FINGUARD_DB_PATH', str(ROOT / 'runtime' / 'finguard.db'))
SAMPLE = ROOT / 'data' / 'development_first_50000.csv'

st.title('🛡️ FinGuard Orchestrator')
st.caption('AML transaction screening • AI-assisted investigation • Analyst review')
st.info('Educational prototype using synthetic data. Not a production compliance system or an official SAR filing tool.', icon='ℹ️')

with st.sidebar:
    st.header('Screening setup')
    st.caption('Step 1 — Select transaction data')
    source = st.radio('Data source', ['Upload CSV', 'Use included sample'], horizontal=False)
    uploaded = st.file_uploader('Choose a transaction CSV', type=['csv']) if source == 'Upload CSV' else None
    if source == 'Use included sample':
        st.caption('Included synthetic SAML-D sample (up to 50,000 rows).')
    limit = st.number_input('Maximum transactions to process', min_value=100, max_value=15000, value=150, step=50)
    st.caption('Start with 150 transactions for a quick demonstration. Larger batches can take longer and may incur API charges.')
    st.divider()
    st.caption('Step 2 — Run screening')
    ai_enabled = bool(os.getenv('OPENAI_API_KEY')) and os.getenv('FINGUARD_ENABLE_OPENAI', '1') != '0'
    st.write('AI assessment:', '**Enabled**' if ai_enabled else '**Offline fallback**')
    st.caption('Set OPENAI_API_KEY in your environment to enable AI. Without it, rule-based summaries are used.')
    ready = (source == 'Use included sample' and SAMPLE.exists()) or (source == 'Upload CSV' and uploaded is not None)
    run = st.button('▶ Process transactions', type='primary', disabled=not ready, use_container_width=True)

if run:
    temp_path = None
    try:
        if source == 'Use included sample':
            file_path = SAMPLE
        else:
            with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as temp:
                temp.write(uploaded.getvalue())
                temp_path = Path(temp.name)
            file_path = temp_path
        with st.spinner('Processing transactions, detecting patterns, and preparing assessments…'):
            result = process_file(file_path, db_path=DB, limit=int(limit))
        st.session_state['last_batch'] = result
        st.success('Screening completed. Open the Investigation Queue to review flagged cases.')
    except Exception as exc:
        st.error(f'Processing failed: {exc}')
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)

con = connect(DB)
try:
    cases = list_cases(con)
    counts = {status: sum(c['status'] == status for c in cases) for status in ('pending_review', 'approved', 'rejected', 'needs_revision')}
    cols = st.columns(4)
    for col, (label, value) in zip(cols, [('Total cases', len(cases)), ('Pending review', counts['pending_review']), ('Approved (demo)', counts['approved']), ('Needs revision', counts['needs_revision'])]):
        col.metric(label, value)

    tab_queue, tab_activity, tab_about = st.tabs(['📋 Investigation Queue', '📈 Batch Activity', 'ℹ️ About FinGuard'])
    with tab_activity:
        st.subheader('Most recent screening')
        last = st.session_state.get('last_batch')
        if last:
            st.json(last)
            if last.get('already_processed'):
                st.caption('This file and row limit were previously processed; existing cases were reused.')
        else:
            st.info('Process a file to see its batch summary here.')
        st.caption('All cases and review decisions are saved to the local demonstration SQLite database.')

    with tab_queue:
        if not cases:
            st.info('No cases yet. Select the included sample in the sidebar and click Process transactions.')
        else:
            filter_cols = st.columns([1, 2])
            with filter_cols[0]:
                status_filter = st.selectbox('Status', ['All', 'pending_review', 'approved', 'rejected', 'needs_revision'])
            with filter_cols[1]:
                batch_filter = st.selectbox('Batch', ['All batches'] + list(dict.fromkeys(c['batch_id'] for c in cases)))
            visible = [c for c in cases if (status_filter == 'All' or c['status'] == status_filter) and (batch_filter == 'All batches' or c['batch_id'] == batch_filter)]
            if not visible:
                st.info('No cases match these filters.')
            else:
                st.dataframe([{
                    'Case ID': c['case_id'], 'Pattern': c['typology'].replace('_', ' ').title(),
                    'Risk': (c['assessment'] or {}).get('risk_level', 'Not assessed'),
                    'Status': c['status'], 'Transactions': len(c['payload'].get('transaction_ids', []))
                } for c in visible], use_container_width=True, hide_index=True)
                selected = st.selectbox('Select a case to investigate', [c['case_id'] for c in visible], key='selected_case')
                case = next(c for c in visible if c['case_id'] == selected)
                assessment = case.get('assessment') or {}
                st.divider()
                st.subheader('Case details')
                detail_cols = st.columns(3)
                detail_cols[0].metric('Pattern', case['typology'].replace('_', ' ').title())
                detail_cols[1].metric('Risk level', str(assessment.get('risk_level', 'Unknown')).replace('_', ' ').title())
                detail_cols[2].metric('Status', case['status'].replace('_', ' ').title())
                st.markdown('**Assessment summary**')
                st.write(assessment.get('summary') or 'No assessment available.')
                st.markdown('**Transaction evidence**')
                tx = get_case_transactions(con, selected)
                if tx:
                    st.dataframe(tx, use_container_width=True, hide_index=True)
                else:
                    st.caption('No transaction evidence found for this case.')
                with st.expander('Detection evidence and case details'):
                    st.json(case['payload'].get('details', {}))
                with st.expander('Regulatory references (project summaries)'):
                    citations = assessment.get('regulatory_citations', [])
                    if not citations:
                        st.write('No regulatory references attached to this assessment.')
                    for citation in citations:
                        if isinstance(citation, dict):
                            st.markdown('**' + str(citation.get('title') or citation.get('source_id') or 'Reference') + '**')
                            st.write(citation.get('text_excerpt', ''))
                            url = citation.get('url', '')
                            if url:
                                st.caption(str(url))
                        else:
                            st.write(str(citation))
                    st.caption('These are project-authored summaries, not independently verified legal guidance.')
                with st.expander('Assessment limitations'):
                    limitations = assessment.get('limitations') or []
                    if isinstance(limitations, str):
                        limitations = [limitations]
                    for item in limitations:
                        st.write('• ' + str(item))
                st.warning('A pattern match or AI risk level is not evidence of wrongdoing. Human review is required.')
                st.subheader('Analyst decision — training demonstration')
                if case['status'] == 'approved':
                    st.success('This case is approved for training demonstration. Reports are available below.')
                with st.form('review_form_' + selected):
                    reviewer = st.text_input('Reviewer name (required)')
                    decision = st.selectbox('Decision', ['pending_review', 'approved', 'needs_revision', 'rejected'], index=0)
                    notes = st.text_area('Review notes')
                    confirm = st.checkbox('I understand this is a simulated class-project decision, not a real compliance approval.')
                    save = st.form_submit_button('Save review decision', type='primary')
                if save:
                    if decision == 'pending_review':
                        st.error('Select an actual review decision before saving.')
                    elif not reviewer.strip():
                        st.error('Enter a reviewer name.')
                    elif not confirm:
                        st.error('Confirm the training-only disclaimer.')
                    else:
                        try:
                            review_case(con, selected, decision, reviewer, notes)
                            st.success('Decision saved.')
                            st.rerun()
                        except ValueError as exc:
                            st.error(str(exc))
                if case['status'] == 'approved':
                    st.subheader('Download investigation draft')
                    try:
                        dl1, dl2 = st.columns(2)
                        with dl1:
                            st.download_button('⬇ Download PDF report', make_pdf(con, selected), file_name=f'{selected}.pdf', mime='application/pdf', use_container_width=True)
                        with dl2:
                            st.download_button('⬇ Download Word report', make_docx(con, selected), file_name=f'{selected}.docx', mime='application/vnd.openxmlformats-officedocument.wordprocessingml.document', use_container_width=True)
                    except Exception as exc:
                        st.error(f'Unable to generate report: {exc}')
    with tab_about:
        st.subheader('What this prototype does')
        st.write('Upload a synthetic transaction CSV, identify candidate AML patterns, retrieve curated regulatory reference summaries, generate optional AI-assisted assessments, review evidence, and export approved training investigation drafts.')
        st.write('**Phase 1:** requirements and design documents (PRD, HLD, LLD, evaluation plan).')
        st.write('**Phase 2:** implemented and tested screening engine, analyst interface, and reports.')
        st.caption('Current limits: CSV ingestion, heuristic detection, demo SQLite database, no authentication, and no real SAR filing.')
finally:
    con.close()
