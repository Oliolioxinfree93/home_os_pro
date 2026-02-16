 (cd "$(git rev-parse --show-toplevel)" && git apply --3way <<'EOF' 
diff --git a/styles.py b/styles.py
index 019225d761daab5ed7f6981f06be064b14f222a9..3cb815fa9ef3d342c77b0ffc72fb1bbef2a8fcd2 100644
--- a/styles.py
+++ b/styles.py
@@ -1,326 +1,318 @@
 def get_css():
     return """
 <style>
-@import url('https://fonts.googleapis.com/css2?family=Fraunces:wght@300;400;600&family=DM+Sans:wght@300;400;500;600&display=swap');
+@import url('https://fonts.googleapis.com/css2?family=Fraunces:wght@500;600&family=Manrope:wght@400;500;600;700&display=swap');
 
-/* ── FORCE LIGHT MODE EVERYWHERE ── */
 :root {
     color-scheme: light !important;
-    --cream:      #FAF7F2;
-    --forest:     #2D5016;
-    --sage:       #7A9E5F;
-    --gold:       #C8952A;
-    --gold-light: #F5E6C8;
-    --charcoal:   #2C2C2C;
-    --mid-gray:   #6B6B6B;
-    --light-gray: #E8E4DE;
-    --shadow:     rgba(44,44,44,0.08);
-}
-
-/* ── GLOBAL ── */
-html, body {
-    font-family: 'DM Sans', sans-serif !important;
-    background-color: var(--cream) !important;
-    color: var(--charcoal) !important;
-    color-scheme: light !important;
+    --bg: #f6f2ea;
+    --bg-soft: #fbf8f2;
+    --surface: #ffffff;
+    --surface-soft: #fffdf9;
+    --line: #e7ddcf;
+    --line-strong: #d8c7b2;
+    --text: #2f2a24;
+    --text-muted: #6f675d;
+    --forest: #26481f;
+    --forest-600: #315927;
+    --sage: #7f9f65;
+    --gold: #bb8229;
+    --gold-soft: #f7e7c8;
+    --shadow-sm: 0 2px 8px rgba(39, 30, 21, 0.06);
+    --shadow-md: 0 10px 24px rgba(39, 30, 21, 0.1);
 }
 
-/* Streamlit app container */
+html,
+body,
 .stApp,
 [data-testid="stAppViewContainer"],
 section.main,
 .main .block-container {
-    background-color: var(--cream) !important;
-    color: var(--charcoal) !important;
+    font-family: 'Manrope', sans-serif !important;
+    background-color: var(--bg) !important;
+    color: var(--text) !important;
+}
+
+[data-testid="stAppViewContainer"] {
+    background-image:
+        radial-gradient(circle at 12% -8%, rgba(255, 255, 255, 0.85) 0, rgba(255, 255, 255, 0) 40%),
+        radial-gradient(circle at 95% 4%, rgba(245, 221, 179, 0.28) 0, rgba(245, 221, 179, 0) 33%),
+        linear-gradient(180deg, #f8f3e9 0%, #f6f2ea 100%) !important;
 }
 
-/* ── HIDE STREAMLIT CHROME (safe — does NOT hide sidebar toggle) ── */
 #MainMenu { visibility: hidden; }
 footer { visibility: hidden; }
 .stDeployButton { display: none; }
 
-/* ── SIDEBAR TOGGLE BUTTON — make it visible on mobile ── */
+[data-testid="stHeader"] {
+    background: linear-gradient(180deg, rgba(246, 242, 234, 0.94) 0%, rgba(246, 242, 234, 0.62) 62%, rgba(246, 242, 234, 0.06) 100%) !important;
+    backdrop-filter: blur(8px);
+}
+
+.block-container {
+    max-width: 1120px !important;
+    padding-top: 1.15rem !important;
+    padding-bottom: 2.4rem !important;
+}
+
+h1, h2, h3 {
+    font-family: 'Fraunces', serif !important;
+    color: var(--forest) !important;
+    letter-spacing: -0.01em;
+}
+
+h1 {
+    font-size: clamp(1.8rem, 2.2vw, 2.35rem) !important;
+    line-height: 1.1 !important;
+    margin-bottom: 0.35rem !important;
+}
+
+h2 { font-size: clamp(1.3rem, 1.6vw, 1.7rem) !important; }
+h3 { font-size: clamp(1.12rem, 1.3vw, 1.32rem) !important; }
+
+p, li, label {
+    color: var(--text) !important;
+}
+
+small,
+.stCaption,
+[data-testid="stMarkdownContainer"] small,
+[data-testid="stMarkdownContainer"] p:has(> small) {
+    color: var(--text-muted) !important;
+}
+
 [data-testid="collapsedControl"] {
     visibility: visible !important;
     display: flex !important;
-    background-color: var(--forest) !important;
-    border-radius: 0 8px 8px 0 !important;
-    padding: 8px 6px !important;
+    align-items: center !important;
+    background: linear-gradient(180deg, #2f5525 0%, #25431e 100%) !important;
+    border-radius: 0 10px 10px 0 !important;
+    box-shadow: var(--shadow-sm) !important;
 }
 [data-testid="collapsedControl"] svg,
 [data-testid="collapsedControl"] span {
-    color: white !important;
-    fill: white !important;
+    color: #fff !important;
+    fill: #fff !important;
+}
+
+[data-testid="stSidebar"] {
+    background: linear-gradient(180deg, #f9f3e8 0%, #f2e7d7 100%) !important;
+    border-right: 1px solid var(--line-strong) !important;
+}
+
+[data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
+[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
+[data-testid="stSidebar"] label,
+[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
+[data-testid="stSidebar"] span {
+    color: #2f2a23 !important;
+    -webkit-text-fill-color: #2f2a23 !important;
 }
 
-/* ── INPUT LABELS — the text above form fields ── */
 label,
 [data-testid="stWidgetLabel"],
 [data-testid="stWidgetLabel"] p,
-[data-testid="stWidgetLabel"] span,
-.stTextInput label,
-.stNumberInput label,
-.stSelectbox label,
-.stRadio label,
-.stCheckbox label,
-.stDateInput label,
-.stFileUploader label,
-.stTextArea label {
-    color: var(--charcoal) !important;
+[data-testid="stWidgetLabel"] span {
+    color: var(--text) !important;
+    -webkit-text-fill-color: var(--text) !important;
     font-size: 0.88rem !important;
-    font-weight: 500 !important;
-    opacity: 1 !important;
-    -webkit-text-fill-color: var(--charcoal) !important;
+    font-weight: 600 !important;
+    letter-spacing: 0.01em;
 }
 
-/* ── SIDEBAR ── */
-[data-testid="stSidebar"] {
-    background: #F5F0E8 !important;
-    border-right: 2px solid #E8E0D0 !important;
+input, textarea, select,
+[data-baseweb="select"] > div,
+[data-testid="stDateInputField"] {
+    background: var(--surface) !important;
+    color: var(--text) !important;
+    border-radius: 12px !important;
+    border: 1px solid var(--line) !important;
+    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.95) !important;
 }
-[data-testid="stSidebar"] h1,
-[data-testid="stSidebar"] h2,
-[data-testid="stSidebar"] h3 {
-    color: var(--forest) !important;
+
+input:focus, textarea:focus, select:focus,
+[data-baseweb="select"] > div:focus-within,
+.stTextInput > div > div:focus-within,
+.stNumberInput > div > div:focus-within,
+.stTextArea > div > div:focus-within {
+    border-color: #729958 !important;
+    box-shadow: 0 0 0 4px rgba(129, 161, 104, 0.2) !important;
 }
-[data-testid="stSidebar"] label,
-[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {
-    color: var(--charcoal) !important;
-    -webkit-text-fill-color: var(--charcoal) !important;
-}
-[data-testid="stSidebar"] .stButton > button {
-    background: var(--forest) !important;
-    color: white !important;
-    -webkit-text-fill-color: white !important;
-    border: none !important;
-    border-radius: 8px !important;
-    font-weight: 500 !important;
-    opacity: 1 !important;
-}
-[data-testid="stSidebar"] .stButton > button:hover {
-    background: #3d6b1f !important;
-    opacity: 1 !important;
-}
-[data-testid="stSidebar"] .stFormSubmitButton > button {
-    background: var(--gold) !important;
-    color: white !important;
-    -webkit-text-fill-color: white !important;
-    border: none !important;
-    font-weight: 600 !important;
-    opacity: 1 !important;
+
+.stButton > button,
+.stFormSubmitButton > button {
+    border-radius: 12px !important;
+    font-weight: 700 !important;
+    border: 1px solid transparent !important;
+    transition: transform 150ms ease, box-shadow 150ms ease, background-color 150ms ease !important;
+    box-shadow: var(--shadow-sm) !important;
 }
 
-/* ── TYPOGRAPHY ── */
-h1, h2, h3 {
-    font-family: 'Fraunces', serif !important;
-    color: var(--forest) !important;
-    font-weight: 600 !important;
+.stButton > button[kind="primary"],
+.stFormSubmitButton > button {
+    background: linear-gradient(180deg, var(--forest-600) 0%, var(--forest) 100%) !important;
+    color: #fff !important;
 }
-h1 { font-size: 2.2rem !important; letter-spacing: -0.02em; }
-h2 { font-size: 1.6rem !important; }
-h3 { font-size: 1.2rem !important; }
 
-p, span, div {
-    color: var(--charcoal);
+.stButton > button[kind="primary"]:hover,
+.stFormSubmitButton > button:hover {
+    transform: translateY(-1px) !important;
+    box-shadow: 0 10px 18px rgba(37, 67, 31, 0.28) !important;
 }
 
-/* ── MAIN CONTENT AREA ── */
-.block-container {
-    padding-top: 1.5rem !important;
-    max-width: 1100px !important;
+.stButton > button[kind="secondary"] {
+    background: var(--surface-soft) !important;
+    color: var(--forest) !important;
+    border-color: var(--line-strong) !important;
 }
 
-/* ── INPUTS ── */
-input, textarea, select,
-input[type="text"],
-input[type="number"],
-input[type="search"],
-input[type="email"] {
-    color-scheme: light !important;
-    background-color: white !important;
-    color: var(--charcoal) !important;
-    -webkit-text-fill-color: var(--charcoal) !important;
-    -webkit-box-shadow: 0 0 0px 1000px white inset !important;
-    caret-color: var(--charcoal) !important;
-    border-radius: 8px !important;
-    border: 1.5px solid var(--light-gray) !important;
-    opacity: 1 !important;
+.stButton > button[kind="secondary"]:hover {
+    background: #f8f2e5 !important;
+}
+
+.stButton > button:focus-visible,
+.stFormSubmitButton > button:focus-visible {
+    outline: 3px solid rgba(126, 161, 99, 0.45) !important;
+    outline-offset: 2px !important;
 }
 
-/* ── METRIC CARDS ── */
 [data-testid="stMetric"] {
-    background: white !important;
-    border: 1px solid var(--light-gray) !important;
+    background:
+        radial-gradient(circle at 100% 0%, rgba(245, 228, 197, 0.35) 0, rgba(245, 228, 197, 0) 44%),
+        linear-gradient(180deg, #ffffff 0%, #fffdf8 100%) !important;
+    border: 1px solid var(--line) !important;
     border-radius: 16px !important;
-    padding: 1.2rem 1.4rem !important;
-    box-shadow: 0 2px 12px var(--shadow) !important;
+    padding: 1rem 1.15rem !important;
+    box-shadow: var(--shadow-sm) !important;
 }
+
 [data-testid="stMetricLabel"] p {
-    font-size: 0.78rem !important;
+    color: var(--text-muted) !important;
     text-transform: uppercase !important;
-    letter-spacing: 0.06em !important;
-    color: var(--mid-gray) !important;
-    font-weight: 500 !important;
+    letter-spacing: 0.08em !important;
+    font-size: 0.73rem !important;
+    font-weight: 700 !important;
 }
+
 [data-testid="stMetricValue"] {
     font-family: 'Fraunces', serif !important;
-    font-size: 1.9rem !important;
     color: var(--forest) !important;
-    font-weight: 600 !important;
+    font-size: clamp(1.35rem, 2vw, 2rem) !important;
 }
+
 [data-testid="stMetricDelta"] {
     font-size: 0.8rem !important;
-    color: var(--sage) !important;
+    font-weight: 600 !important;
 }
 
-/* ── TABS ── */
 [data-testid="stTabs"] [role="tablist"] {
-    background: white !important;
-    border-radius: 12px !important;
-    padding: 4px !important;
-    border: 1px solid var(--light-gray) !important;
+    background: rgba(255, 255, 255, 0.74) !important;
+    border: 1px solid var(--line) !important;
+    border-radius: 13px !important;
+    padding: 0.3rem !important;
 }
+
 [data-testid="stTabs"] [role="tab"] {
-    border-radius: 8px !important;
-    font-weight: 500 !important;
-    font-size: 0.85rem !important;
-    color: var(--mid-gray) !important;
-}
-[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
-    background: var(--forest) !important;
-    color: white !important;
+    border-radius: 10px !important;
+    color: var(--text-muted) !important;
     font-weight: 600 !important;
+    padding: 0.45rem 0.9rem !important;
 }
 
-/* ── CARDS ── */
-[data-testid="stVerticalBlockBorderWrapper"] {
-    border-radius: 14px !important;
-    border: 1px solid var(--light-gray) !important;
-    background: white !important;
-    padding: 0.8rem 1rem !important;
-    box-shadow: 0 2px 8px var(--shadow) !important;
-    margin-bottom: 0.5rem !important;
+[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
+    background: linear-gradient(180deg, #37642a 0%, #27491f 100%) !important;
+    color: #fff !important;
+    box-shadow: 0 8px 14px rgba(39, 73, 31, 0.22) !important;
 }
 
-/* ── BUTTONS ── */
-.stButton > button {
-    border-radius: 10px !important;
-    font-weight: 500 !important;
-    transition: all 0.2s ease !important;
-}
-.stButton > button[kind="primary"] {
-    background: var(--forest) !important;
-    color: white !important;
-    border: none !important;
+[data-testid="stVerticalBlockBorderWrapper"] {
+    background: linear-gradient(180deg, rgba(255, 255, 255, 0.97) 0%, rgba(255, 251, 244, 0.99) 100%) !important;
+    border: 1px solid var(--line) !important;
+    border-radius: 16px !important;
+    padding: 0.9rem 1rem !important;
+    box-shadow: var(--shadow-sm) !important;
+    margin-bottom: 0.65rem !important;
 }
 
-/* ── PROGRESS BAR ── */
-.stProgress > div > div {
-    background: var(--sage) !important;
-    border-radius: 99px !important;
+[data-testid="stVerticalBlockBorderWrapper"]:hover {
+    box-shadow: var(--shadow-md) !important;
 }
 
-/* ── SIDEBAR SECONDARY BUTTONS (e.g. inactive language toggle) ── */
-[data-testid="stSidebar"] .stButton > button[kind="secondary"] {
-    background: white !important;
-    color: var(--forest) !important;
-    -webkit-text-fill-color: var(--forest) !important;
-    border: 2px solid var(--forest) !important;
-    font-weight: 500 !important;
-}
-[data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover {
-    background: var(--gold-light) !important;
+[data-testid="stDataFrame"],
+[data-testid="stTable"] {
+    border-radius: 14px !important;
+    border: 1px solid var(--line) !important;
+    overflow: hidden !important;
+    box-shadow: var(--shadow-sm) !important;
+    background: var(--surface) !important;
 }
 
-/* ── EXPANDER ── */
 [data-testid="stExpander"] {
-    border: 1px solid var(--light-gray) !important;
-    border-radius: 12px !important;
-    background: white !important;
+    border: 1px solid var(--line) !important;
+    border-radius: 14px !important;
+    background: linear-gradient(180deg, #fff 0%, #fffcf7 100%) !important;
 }
 
-/* ── OVERRIDE DARK MODE — force light always ── */
-@media (prefers-color-scheme: dark) {
-    html, body, .stApp,
-    [data-testid="stAppViewContainer"],
-    section.main {
-        background-color: var(--cream) !important;
-        color: var(--charcoal) !important;
-    }
-    [data-testid="stSidebar"] {
-        background: #F5F0E8 !important;
-    }
-    [data-testid="stVerticalBlockBorderWrapper"],
-    [data-testid="stMetric"],
-    [data-testid="stExpander"] {
-        background: white !important;
-    }
-    label,
-    [data-testid="stWidgetLabel"] p {
-        color: var(--charcoal) !important;
-        -webkit-text-fill-color: var(--charcoal) !important;
-    }
-    input, textarea, select {
-        background-color: white !important;
-        color: var(--charcoal) !important;
-        -webkit-text-fill-color: var(--charcoal) !important;
-        -webkit-box-shadow: 0 0 0px 1000px white inset !important;
-    }
+[data-testid="stExpander"] details summary p {
+    color: var(--forest) !important;
+    font-weight: 700 !important;
 }
 
-/* ── SELECTED ITEM HIGHLIGHT ── */
-/* Gold border on selected cards */
-[data-testid="stVerticalBlockBorderWrapper"]:has(button[kind="secondary"][title="Tap to select"] ~ *) {
-    border-color: var(--gold) !important;
-    box-shadow: 0 0 0 2px var(--gold-light), 0 2px 8px var(--shadow) !important;
+.stProgress > div {
+    background: #e8eddc !important;
+    border-radius: 999px !important;
 }
 
-/* Tap select button — minimal, emoji only */
-button[title="Tap to select"] {
-    background: transparent !important;
-    border: none !important;
-    padding: 2px 6px !important;
-    min-height: 32px !important;
-    font-size: 1rem !important;
-    box-shadow: none !important;
+.stProgress > div > div {
+    background: linear-gradient(90deg, #7ea35f 0%, #5f8847 100%) !important;
+    border-radius: 999px !important;
 }
 
-/* Category badge inline */
 code {
-    background: var(--gold-light) !important;
-    color: var(--forest) !important;
-    border-radius: 6px !important;
-    padding: 1px 6px !important;
-    font-size: 0.75rem !important;
-    font-family: 'DM Sans', sans-serif !important;
-    font-weight: 500 !important;
+    background: var(--gold-soft) !important;
+    color: #5b4219 !important;
+    border-radius: 7px !important;
+    padding: 0.1rem 0.4rem !important;
+    font-size: 0.76rem !important;
+    border: 1px solid rgba(187, 130, 41, 0.24) !important;
 }
 
-/* Move/action buttons in action bar */
-.action-bar .stButton > button {
-    padding: 4px 8px !important;
-    font-size: 0.8rem !important;
-    min-height: 36px !important;
+div[data-testid="stMarkdownContainer"] hr {
+    border: none !important;
+    border-top: 1px solid var(--line) !important;
+    margin: 1rem 0 !important;
 }
 
-/* ── FOOTER ── */
 .footer-text {
     text-align: center;
-    color: var(--mid-gray);
-    font-size: 0.75rem;
-    padding: 2rem 0 1rem;
-    border-top: 1px solid var(--light-gray);
+    color: var(--text-muted) !important;
+    font-size: 0.74rem;
     margin-top: 2rem;
+    padding-top: 1rem;
+    border-top: 1px solid var(--line);
+}
+
+@media (prefers-reduced-motion: reduce) {
+    *, *::before, *::after {
+        animation: none !important;
+        transition: none !important;
+    }
 }
 
-/* ── MOBILE ── */
 @media (max-width: 768px) {
-    .block-container { padding: 1rem 0.8rem !important; }
-    h1 { font-size: 1.6rem !important; }
-    [data-testid="stMetricValue"] { font-size: 1.4rem !important; }
-    /* Bigger touch targets on mobile */
-    .stButton > button { min-height: 44px !important; }
-    label { font-size: 0.9rem !important; }
+    .block-container {
+        padding-left: 0.8rem !important;
+        padding-right: 0.8rem !important;
+    }
+
+    [data-testid="stMetric"] {
+        min-height: auto !important;
+    }
+
+    .stButton > button,
+    .stFormSubmitButton > button {
+        min-height: 44px !important;
+    }
 }
 </style>
 """
 
EOF
)
