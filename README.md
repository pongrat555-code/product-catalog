# ⚙️ การตั้งค่า Streamlit Secrets (Cloudinary + Google Drive)

สมัครใช้งาน Cloudinary ฟรีที่ [cloudinary.com](https://cloudinary.com/) เพื่อดึงค่า `Cloud Name`, `API Key`, และ `API Secret`

จากนั้นนำไปใส่ในเมนู **App Settings > Secrets** บน [Streamlit Community Cloud](https://share.streamlit.io/) ดังนี้:

```toml
[cloudinary]
cloud_name = "ใส่_cloud_name_จาก_cloudinary"
api_key = "ใส่_api_key_จาก_cloudinary"
api_secret = "ใส่_api_secret_จาก_cloudinary"

[gcp_service_account]
type = "service_account"
project_id = "your-project-id"
private_key_id = "xxxxxx"
private_key = "-----BEGIN PRIVATE KEY-----\n..."
client_email = "your-service-account@...iam.gserviceaccount.com"
client_id = "xxxxxx"
auth_uri = "[https://accounts.google.com/o/oauth2/auth](https://accounts.google.com/o/oauth2/auth)"
token_uri = "[https://oauth2.googleapis.com/token](https://oauth2.googleapis.com/token)"
auth_provider_x509_cert_url = "[https://www.googleapis.com/oauth2/v1/certs](https://www.googleapis.com/oauth2/v1/certs)"
client_x509_cert_url = "[https://www.googleapis.com/robot/v1/metadata/x509/](https://www.googleapis.com/robot/v1/metadata/x509/)..."
