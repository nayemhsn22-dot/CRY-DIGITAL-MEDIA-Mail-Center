import json, os, re, time
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import streamlit as st

APP_NAME = "CRY DIGITAL MEDIA"
MAX_RECIPIENTS = 100
st.set_page_config(page_title="CRY DIGITAL MEDIA | Mail Center", page_icon="✉️", layout="wide")
st.markdown("""
<style>
.stApp { background: linear-gradient(135deg, #020024 0%, #08133d 45%, #071b2d 100%); color: #f5f8ff; }
[data-testid="stSidebar"] { background: rgba(2, 8, 30, .96); }
.stTextInput input, .stTextArea textarea { background: rgba(0,0,0,.35) !important; color: #eaf7ff !important; border: 1px solid #00d9ff !important; }
.stButton > button, .stFormSubmitButton > button { background: linear-gradient(90deg, #075bff, #00cfff); color: white; font-weight: 700; border: 0; border-radius: 14px; min-height: 44px; width: 100%; }
.hero { padding: 18px 22px; border: 1px solid rgba(0,217,255,.65); border-radius: 18px; background: rgba(3,10,35,.72); }
.metric { padding: 16px; border-radius: 14px; border: 1px solid rgba(0,217,255,.5); background: rgba(0,15,45,.75); text-align: center; }
.small-note { color: #a9c5dc; font-size: .9rem; }
</style>
""", unsafe_allow_html=True)

logo_path = os.path.join(os.path.dirname(__file__), "assets", "cry-digital-media-logo.png")
ceo_path = os.path.join(os.path.dirname(__file__), "assets", "ceo-md-maruf-hussain.png")
with st.sidebar:
    if os.path.exists(logo_path): st.image(logo_path, use_container_width=True)
    st.markdown("### ⚙️ Mail settings")
    method = st.radio("Sending method", ["Gmail SMTP", "Email API"])
    delay = st.slider("Delay between messages (seconds)", 1, 30, 3)
    st.caption("Batch limit: up to 100 recipients per run.")
    st.divider()
    st.markdown("**CRY DIGITAL MEDIA**")
    st.caption("CEO: MD MARUF HUSSAIN")

col_logo, col_head = st.columns([1, 3], vertical_alignment="center")
with col_logo:
    if os.path.exists(logo_path): st.image(logo_path, use_container_width=True)
with col_head:
    st.markdown('<div class="hero">', unsafe_allow_html=True)
    st.title("CRY DIGITAL MEDIA")
    st.subheader("Mail Center")
    st.write("Gmail SMTP ও configured email API—এক জায়গা থেকে পরিচালনা করুন।")
    st.markdown('<p class="small-note">Developed by MD MARUF HUSSAIN · CEO, CRY DIGITAL MEDIA</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with st.expander("CEO profile", expanded=False):
    c1, c2 = st.columns([1, 3])
    with c1:
        if os.path.exists(ceo_path): st.image(ceo_path, use_container_width=True)
    with c2:
        st.markdown("### MD MARUF HUSSAIN")
        st.write("Chief Executive Officer (CEO)")
        st.write("CRY DIGITAL MEDIA")

st.info("শুধু অনুমতি পাওয়া প্রাপকদের মেইল পাঠান। Gmail ও API provider-এর sending limits মেনে চলুন; bulk unsolicited mail বা limit bypass করার জন্য এই টুল ব্যবহার করবেন না.")

with st.form("compose_form"):
    st.markdown("### ✉️ Compose message")
    recipients_text = st.text_area("Recipient email addresses (one per line or comma-separated)", placeholder="recipient@example.com\nanother@example.com", height=120)
    subject = st.text_input("Subject", placeholder="Your email subject")
    body = st.text_area("Message", height=180, placeholder="Write your message here...")
    html_mode = st.checkbox("Send message body as HTML", value=False)
    send_clicked = st.form_submit_button("Send email batch")

def parse_recipients(raw):
    parts = re.split(r"[\s,;]+", raw.strip())
    valid, invalid = [], []
    for item in parts:
        if not item: continue
        if re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", item):
            if item.lower() not in {x.lower() for x in valid}: valid.append(item)
        else: invalid.append(item)
    return valid, invalid

def send_smtp(recipients, subject, body, html_mode, user, password, delay_seconds):
    sent, failures = [], []
    server = smtplib.SMTP("smtp.gmail.com", 587, timeout=30)
    try:
        server.ehlo(); server.starttls(); server.ehlo()
        server.login(user, password.replace(" ", ""))
        for index, recipient in enumerate(recipients):
            msg = MIMEMultipart("alternative")
            msg["From"], msg["To"], msg["Subject"] = user, recipient, subject
            msg.attach(MIMEText(body, "html" if html_mode else "plain", "utf-8"))
            try:
                server.sendmail(user, [recipient], msg.as_string()); sent.append(recipient)
            except Exception as exc: failures.append((recipient, str(exc)))
            if index < len(recipients)-1: time.sleep(delay_seconds)
    finally:
        try: server.quit()
        except Exception: pass
    return sent, failures

def send_api(recipients, subject, body, html_mode, endpoint, token, from_email, delay_seconds):
    sent, failures = [], []
    for index, recipient in enumerate(recipients):
        payload = {"from": from_email, "to": recipient, "subject": subject,
                   "text": "" if html_mode else body, "html": body if html_mode else None}
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if token: headers["Authorization"] = "Bearer " + token
        req = Request(endpoint, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
        try:
            with urlopen(req, timeout=30) as response:
                if 200 <= response.status < 300: sent.append(recipient)
                else: failures.append((recipient, f"HTTP {response.status}"))
        except HTTPError as exc: failures.append((recipient, f"HTTP {exc.code}: {exc.reason}"))
        except (URLError, TimeoutError, ValueError) as exc: failures.append((recipient, str(exc)))
        except Exception as exc: failures.append((recipient, str(exc)))
        if index < len(recipients)-1: time.sleep(delay_seconds)
    return sent, failures

if method == "Gmail SMTP":
    st.markdown("### 🔐 Gmail SMTP credentials")
    st.caption("Use a Google App Password, not your regular Gmail password. Credentials are used for this run only and are not written to a file.")
    smtp_col1, smtp_col2 = st.columns(2)
    with smtp_col1: smtp_user = st.text_input("Gmail address", key="smtp_user", placeholder="you@gmail.com")
    with smtp_col2: smtp_pass = st.text_input("Gmail App Password", type="password", key="smtp_pass")
else:
    st.markdown("### 🔌 Email API configuration")
    st.caption("The endpoint must accept the JSON format shown below. Provider-specific APIs may need an adapter.")
    api_col1, api_col2 = st.columns(2)
    with api_col1:
        api_endpoint = st.text_input("API endpoint URL", key="api_endpoint", placeholder="https://api.example.com/send")
        api_from = st.text_input("Verified sender email", key="api_from", placeholder="mail@yourdomain.com")
    with api_col2: api_token = st.text_input("Bearer API token (optional)", type="password", key="api_token")
    with st.expander("Expected API request format"):
        st.code("""POST /send
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

{
  "from": "mail@yourdomain.com",
  "to": "recipient@example.com",
  "subject": "Subject",
  "text": "Plain text body",
  "html": null
}""", language="json")

if send_clicked:
    recipients, invalid = parse_recipients(recipients_text)
    if not recipients: st.error("একটি বৈধ recipient email address দিন।")
    elif len(recipients) > MAX_RECIPIENTS: st.error(f"একটি batch-এ সর্বোচ্চ {MAX_RECIPIENTS} জন recipient রাখা যাবে।")
    elif not subject.strip() or not body.strip(): st.error("Subject এবং message body পূরণ করুন।")
    elif method == "Gmail SMTP" and (not st.session_state.get("smtp_user") or not st.session_state.get("smtp_pass")): st.error("Gmail address ও App Password দিন।")
    elif method == "Email API" and (not st.session_state.get("api_endpoint") or not st.session_state.get("api_from")): st.error("API endpoint এবং verified sender email দিন।")
    else:
        if invalid: st.warning("Invalid entries বাদ দেওয়া হয়েছে: " + ", ".join(invalid[:10]))
        st.write(f"Starting batch for **{len(recipients)}** valid recipient(s)…")
        try:
            if method == "Gmail SMTP":
                sent, failures = send_smtp(recipients, subject.strip(), body, html_mode, st.session_state["smtp_user"].strip(), st.session_state["smtp_pass"], delay)
            else:
                sent, failures = send_api(recipients, subject.strip(), body, html_mode, st.session_state["api_endpoint"].strip(), st.session_state.get("api_token", ""), st.session_state["api_from"].strip(), delay)
            st.success(f"Batch finished at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            m1, m2, m3 = st.columns(3)
            with m1: st.markdown(f'<div class="metric"><h2>{len(sent)}</h2>Sent</div>', unsafe_allow_html=True)
            with m2: st.markdown(f'<div class="metric"><h2>{len(failures)}</h2>Failed</div>', unsafe_allow_html=True)
            with m3: st.markdown(f'<div class="metric"><h2>{len(recipients)}</h2>Total</div>', unsafe_allow_html=True)
            if sent:
                with st.expander("Successful recipients"): st.write("\n".join(sent))
            if failures:
                with st.expander("Failed recipients and reasons", expanded=True):
                    for recipient, reason in failures: st.write(f"- {recipient}: {reason}")
        except Exception as exc: st.error(f"Sending failed: {exc}")

st.divider()
st.caption("CRY DIGITAL MEDIA · CEO: MD MARUF HUSSAIN · Protect API tokens and App Passwords. Never commit credentials to source control.")
