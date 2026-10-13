# CRY DIGITAL MEDIA Mail Center

Branded Streamlit web app with Gmail SMTP (Google App Password) and configurable JSON email API support.

## Run locally
1. Install Python 3.10+.
2. `pip install -r requirements.txt`
3. `streamlit run app.py`

## Deploy on Streamlit Community Cloud
1. Upload this project to a GitHub repository you control.
2. Visit https://share.streamlit.io/ and connect your GitHub account.
3. Choose the repository and `app.py`, then deploy.
4. Your app will receive a `*.streamlit.app` URL.

I cannot publish into an external hosting account or generate a live URL without authorized access to that account. Do not add credentials to the repository.

## Sending
- SMTP uses `smtp.gmail.com:587` with STARTTLS. Use a Google App Password.
- API mode sends one JSON POST per recipient. The endpoint must accept `from`, `to`, `subject`, `text`, and `html`, and optional Bearer authorization. Adapt `send_api()` for provider-specific schemas.
- Batch cap is 100 recipients and a delay is applied between messages. Use only for recipients who have agreed to receive mail and follow provider rules.
