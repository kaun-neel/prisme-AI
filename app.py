import streamlit as st
import time
from agent_brain import analyze_code
from splunk_connect import push_dashboard_via_mcp

st.set_page_config(page_title="Prism | Code-to-Splunk", layout="wide", initial_sidebar_state="collapsed")

if 'current_page' not in st.session_state: st.session_state.current_page = 'input'
if 'code_input' not in st.session_state: st.session_state.code_input = ""
if 'analysis' not in st.session_state: st.session_state.analysis = None
if 'success_msg' not in st.session_state: st.session_state.success_msg = ""

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&family=DM+Serif+Display&display=swap');

    /* Pitch Black Enterprise Background */
    .stApp { background-color: #09090b; color: #fafafa; font-family: 'Inter', sans-serif; }

    /* Hide Streamlit chrome that causes jitter */
    header[data-testid="stHeader"], footer, [data-testid="collapsedControl"] {display: none !important;}
    [data-testid="stStatusWidget"], [data-testid="stDecoration"], .stDeployButton { display: none !important; }
    div[data-testid="stToolbar"] { display: none !important; }

    /* Prevent layout shift */
    [data-testid="stAppViewContainer"] { min-height: 100vh; }
    html { scroll-behavior: auto !important; overflow-anchor: none !important; }

    h1, h2, h3, p { font-family: 'Inter', sans-serif; margin: 0; padding: 0; }
    
    /* THE PRISME LOGO */
    .prisme-logo-container { position: relative; display: flex; align-items: center; width: 300px; height: 60px; margin-bottom: 20px;}
    .prisme-glow {
        position: absolute; top: 50%; left: 40px; transform: translate(-50%, -50%);
        width: 120px; height: 60px;
        background: radial-gradient(circle at center, rgba(217, 70, 239, 0.8) 0%, rgba(59, 130, 246, 0.6) 45%, transparent 70%);
        filter: blur(20px); z-index: 0;
    }
    .prisme-text { position: relative; z-index: 1; font-family: 'DM Serif Display', serif; font-size: 42px; color: #ffffff; letter-spacing: -1px; }

    /* MAC WINDOW STYLE CODE EDITOR */
    .mac-window-header { background: #111113; border: 1px solid #27272a; border-bottom: none; border-radius: 8px 8px 0 0; padding: 12px 16px; display: flex; align-items: center; gap: 8px; }
    .mac-dot { width: 10px; height: 10px; border-radius: 50%; }
    .mac-dot.red { background: #ff5f56; } .mac-dot.yellow { background: #ffbd2e; } .mac-dot.green { background: #27c93f; }
    .mac-title { color: #71717a; font-family: 'JetBrains Mono', monospace; font-size: 12px; margin-left: 8px; }

    div[data-testid="stTextArea"] > div { background: #111113 !important; border: 1px solid #27272a !important; border-top: none !important; border-radius: 0 0 8px 8px !important; }
    div[data-testid="stTextArea"] textarea { color: #a1a1aa !important; font-family: 'JetBrains Mono', monospace !important; font-size: 14px !important; padding: 16px !important; line-height: 1.5 !important; }
    div[data-testid="stTextArea"] textarea:focus { border-color: #6366f1 !important; color: #ffffff !important; }

    /* BUTTONS */
    .btn-primary > button { background: #6366f1 !important; color: white !important; border: none !important; border-radius: 6px !important; font-size: 14px !important; font-weight: 500 !important; padding: 12px 24px !important; width: 100% !important; transition: all 0.2s; }
    .btn-primary > button:hover { background: #4f46e5 !important; box-shadow: 0 0 15px rgba(99, 102, 241, 0.4); }
    
    .btn-mcp > button { background: linear-gradient(135deg, #b45309, #7c2d12) !important; color: white !important; border: none !important; border-radius: 6px !important; font-size: 14px !important; font-weight: 600 !important; padding: 12px 24px !important; width: 100% !important; transition: all 0.2s; margin-top: 20px !important;}
    .btn-mcp > button:hover { background: linear-gradient(135deg, #d97706, #9a3412) !important; box-shadow: 0 0 15px rgba(180, 83, 9, 0.4); }

    .btn-back > button { background: transparent !important; color: #71717a !important; border: none !important; padding: 0 !important; font-size: 13px !important; margin-bottom: 20px !important;}
    .btn-back > button:hover { color: #ffffff !important; }

    /* ANALYSIS CARDS */
    .analysis-card { background: #09090b; border: 1px solid #27272a; border-radius: 8px; padding: 20px; margin-bottom: 16px; }
    .card-title { color: #fafafa; font-size: 16px; font-weight: 600; display: flex; align-items: center; gap: 8px; margin-bottom: 16px; }
    
    /* RISKS */
    .risk-item { padding: 12px; border-radius: 6px; margin-bottom: 8px; font-size: 13px; display: flex; gap: 12px; align-items: center;}
    .risk-critical { background: rgba(220, 38, 38, 0.1); border: 1px solid rgba(220, 38, 38, 0.2); color: #fca5a5; }
    .risk-high { background: rgba(234, 88, 12, 0.1); border: 1px solid rgba(234, 88, 12, 0.2); color: #fdba74; }
    .risk-medium { background: rgba(202, 138, 4, 0.1); border: 1px solid rgba(202, 138, 4, 0.2); color: #fde047; }
    .badge { padding: 2px 8px; border-radius: 12px; font-size: 10px; font-weight: 700; text-transform: uppercase; }
    .badge-critical { background: #dc2626; color: white; }
    .badge-high { background: #ea580c; color: white; }
    .badge-medium { background: #ca8a04; color: white; }

    /* SPL QUERIES & ALERTS */
    .spl-box { background: #111113; border: 1px solid #27272a; border-radius: 6px; padding: 12px; font-family: 'JetBrains Mono', monospace; font-size: 12px; color: #a78bfa; margin-top: 8px; margin-bottom: 16px;}
    .spl-title { color: #e4e4e7; font-size: 14px; font-weight: 500; }
    .viz-tag { background: #27272a; color: #a1a1aa; padding: 2px 8px; border-radius: 4px; font-size: 11px; margin-left: 10px; }

    /* TABS */
    div[data-testid="stTabs"] button { color: #a1a1aa !important; font-family: 'Inter', sans-serif !important; font-weight: 500 !important; }
    div[data-testid="stTabs"] button[aria-selected="true"] { color: #ffffff !important; border-bottom-color: #6366f1 !important; }
    
    /* Process Info Vertical Line */
    .process-line { border-left: 2px solid #27272a; padding-left: 20px; margin-top: 30px; margin-left: 10px; }
    </style>
""", unsafe_allow_html=True)

st.html("""
<script>
    const app = window.parent.document.querySelector('[data-testid="stAppViewContainer"]');
    if (app) {
        app.style.opacity = '0';
        app.style.transform = 'translateY(6px)';
        app.style.transition = 'none';
        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                app.style.transition = 'opacity 0.35s ease, transform 0.35s ease';
                app.style.opacity = '1';
                app.style.transform = 'translateY(0)';
            });
        });
    }
    window.parent.scrollTo({ top: 0, behavior: 'instant' });
</script>
""")

def render_header():
    st.markdown('''
        <div class="prisme-logo-container"><div class="prisme-glow"></div><div class="prisme-text">Prism</div></div>
        <div style="color: #a1a1aa; font-size: 16px; margin-top: -10px; margin-bottom: 30px;">AI Code-to-Splunk Bridge</div>
    ''', unsafe_allow_html=True)

def page_input():
    _, col, _ = st.columns([1, 2, 1])
    with col:
        render_header()
        st.markdown('<p style="color: #d1d5db; font-size: 15px; margin-bottom: 20px;">Paste your application code. Prism will analyze it and auto-generate a complete Splunk instrumentation plan.</p>', unsafe_allow_html=True)
        
        st.markdown('<div class="mac-window-header"><div class="mac-dot red"></div><div class="mac-dot yellow"></div><div class="mac-dot green"></div><span class="mac-title">application_code.py</span></div>', unsafe_allow_html=True)
        
        code = st.text_area(
            "Code Input Area", 
            height=400, 
            label_visibility="collapsed",
            placeholder="# Paste Python, Node.js, Go, or Java code here...\n\ndef process_checkout():\n    ...",
            value=st.session_state.code_input
        )
        
        st.markdown('<div class="btn-primary" style="margin-top: 20px;">', unsafe_allow_html=True)
        analyze_btn = st.button("Analyze with Splunk Hosted Model →")
        st.markdown('</div>', unsafe_allow_html=True)
        
        if analyze_btn and code.strip():
            st.session_state.code_input = code
            st.session_state.current_page = 'processing'
            st.rerun()

def page_processing():
    _, col, _ = st.columns([1, 2, 1])
    with col:
        render_header()
        st.markdown('<div class="process-line">', unsafe_allow_html=True)
        st.markdown('<span style="color: #fafafa; font-size: 16px; font-weight: 500;">Analyzing Codebase...</span><br><br>', unsafe_allow_html=True)
        
        terminal = st.empty()
        phases = [
            "> Connecting to Splunk Hosted Model Endpoint...",
            "> Parsing Abstract Syntax Tree...",
            "> Identifying unhandled exceptions and latency bottlenecks...",
            "> Generating SPL queries and Alerts...",
            "> Compiling Dashboard JSON for MCP Server..."
        ]
        for phase in phases:
            terminal.markdown(f'<span style="font-family: \'JetBrains Mono\', monospace; color: #a1a1aa; font-size: 14px;">{phase}</span>', unsafe_allow_html=True)
            time.sleep(0.7)
            
        st.session_state.analysis = analyze_code(st.session_state.code_input)
        st.session_state.current_page = 'analysis'
        st.rerun()

def page_analysis():
    col1, col2 = st.columns([1, 4])
    with col1:
        st.markdown('<div class="btn-back">', unsafe_allow_html=True)
        back_btn = st.button("‹ Back to Input")
        st.markdown('</div>', unsafe_allow_html=True)
        
        if back_btn:
            st.session_state.current_page = 'input'
            st.rerun()
    
    render_header()
    
    data = st.session_state.analysis
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["⚠️ Risk Areas", "🔍 SPL Queries", "🚨 Alerts", "📊 Dashboard Panels", "📝 Logging Recs"])
    
    with tab1:
        st.markdown('<div class="analysis-card"><div class="card-title">Code-Level Risks Detected</div>', unsafe_allow_html=True)
        for risk in data['risks']:
            level = risk['level']
            st.markdown(f'''
                <div class="risk-item risk-{level}">
                    <span class="badge badge-{level}">{level}</span>
                    <span>{risk['message']}</span>
                </div>
            ''', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        st.markdown('<div class="analysis-card"><div class="card-title">Ready-to-run SPL Queries</div>', unsafe_allow_html=True)
        for spl in data['spl_queries']:
            st.markdown(f'''
                <div>
                    <span class="spl-title">{spl['name']}</span>
                    <span class="viz-tag">{spl['viz']}</span>
                    <div class="spl-box">{spl['spl']}</div>
                </div>
            ''', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with tab3:
        st.markdown('<div class="analysis-card"><div class="card-title">Recommended Alerts</div>', unsafe_allow_html=True)
        for alert in data['alerts']:
            level = alert['severity']
            st.markdown(f'''
                <div style="margin-bottom: 20px;">
                    <div style="display:flex; align-items:center; gap: 10px; margin-bottom: 8px;">
                        <span class="badge badge-{level}">{level}</span>
                        <span class="spl-title">{alert['name']}</span>
                        <span style="color: #71717a; font-size: 13px;">Trigger: {alert['condition']}</span>
                    </div>
                    <div class="spl-box" style="margin-top: 0;">{alert['spl']}</div>
                </div>
            ''', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
    with tab4:
        st.markdown('<div class="analysis-card"><div class="card-title">Generated Dashboard Configuration</div>', unsafe_allow_html=True)
        cols = st.columns(2)
        for i, panel in enumerate(data['dashboard_panels']):
            with cols[i%2]:
                st.markdown(f'''
                    <div style="background: #18181b; border: 1px solid #27272a; padding: 16px; border-radius: 8px; margin-bottom: 16px;">
                        <div style="color: #fafafa; font-weight: 500; font-size: 14px; margin-bottom: 4px;">{panel['title']}</div>
                        <div style="color: #a1a1aa; font-size: 12px;">{panel['desc']}</div>
                    </div>
                ''', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with tab5:
        st.markdown('<div class="analysis-card"><div class="card-title">Instrumentation Recommendations</div>', unsafe_allow_html=True)
        for rec in data['logging_recs']:
            st.markdown(f'<div style="background: #111113; border-left: 3px solid #6366f1; padding: 12px 16px; margin-bottom: 12px; color: #d1d5db; font-size: 13px; font-family: \'JetBrains Mono\', monospace;">{rec}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    _, center, _ = st.columns([1, 2, 1])
    with center:
        st.markdown('<div class="btn-mcp">', unsafe_allow_html=True)
        push_btn = st.button("Push Dashboard via Splunk MCP Server")
        st.markdown('</div>', unsafe_allow_html=True)
        
        if push_btn:
            st.session_state.current_page = 'pushing'
            st.rerun()

def page_pushing():
    _, col, _ = st.columns([1, 2, 1])
    with col:
        render_header()
        st.markdown('<div class="process-line">', unsafe_allow_html=True)
        
        terminal = st.empty()
        phases = [
            "> Establishing connection to Splunk MCP Server...",
            "> Formatting JSON dashboard config...",
            "> Validating SPL queries via MCP...",
            "> Deploying to Splunk Enterprise..."
        ]
        for phase in phases:
            terminal.markdown(f'<span style="font-family: \'JetBrains Mono\', monospace; color: #a1a1aa; font-size: 14px;">{phase}</span>', unsafe_allow_html=True)
            time.sleep(0.8)
            
        success, msg = push_dashboard_via_mcp(st.session_state.analysis)
        if success:
            st.session_state.success_msg = msg
            st.session_state.current_page = 'success'
            st.rerun()
        else:
            st.error(f"Deployment Failed: {msg}")
            if st.button("‹ Back to Analysis"):
                st.session_state.current_page = 'analysis'
                st.rerun()

def page_success():
    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.markdown(f'''
            <div style="text-align: center; padding: 60px 0;">
                <div style="width:64px;height:64px;border-radius:50%;background:rgba(16,185,129,0.1);border:1px solid rgba(16,185,129,0.3);display:inline-flex;align-items:center;justify-content:center;margin-bottom:24px;">
                    <svg style="width:32px;height:32px;stroke:#34d399;fill:none;stroke-width:2" viewBox="0 0 24 24"><path d="M20 6 9 17l-5-5"/></svg>
                </div>
                <h1 style="color: #fafafa; font-weight: 700; font-size: 32px; letter-spacing:-1px; margin-bottom: 12px;">Deployment Successful</h1>
                <p style="color: #a1a1aa; font-size: 16px;">{st.session_state.success_msg}</p>
            </div>
        ''', unsafe_allow_html=True)
        
        st.markdown('<div class="btn-primary" style="margin-top: 20px;">', unsafe_allow_html=True)
        restart_btn = st.button("Start New Analysis")
        st.markdown('</div>', unsafe_allow_html=True)
        
        if restart_btn:
            st.session_state.current_page = 'input'
            st.session_state.code_input = ""
            st.rerun()

placeholder = st.empty()
with placeholder.container():
    if st.session_state.current_page == 'input': page_input()
    elif st.session_state.current_page == 'processing': page_processing()
    elif st.session_state.current_page == 'analysis': page_analysis()
    elif st.session_state.current_page == 'pushing': page_pushing()
    elif st.session_state.current_page == 'success': page_success()