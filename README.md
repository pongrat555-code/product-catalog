# 📦 การตั้งค่าสิทธิ์ Google Drive สำหรับบัญชี `pongrat555@gmail.com`

## 1. สร้าง Service Account บน Google Cloud Console
1. ล็อกอินเข้า [Google Cloud Console](https://console.cloud.google.com/) ด้วยบัญชี `pongrat555@gmail.com`
2. สร้าง Project ใหม่ (เช่น ชื่อ `product-catalog-system`)
3. ไปที่เมนู **APIs & Services > Library** ค้นหา **Google Drive API** แล้วกด **Enable**
4. ไปที่เมนู **APIs & Services > Credentials**
   - กด **+ CREATE CREDENTIALS** -> เลือก **Service Account**
   - กรอกชื่อ Service Account แล้วกด **Create and Continue** -> **Done**
5. คลิกที่ Service Account ที่สร้างขึ้นมา -> ไปที่แถบ **KEYS**
   - กด **ADD KEY** -> เลือก **Create new key** -> เลือกประเภท **JSON**
   - ระบบจะดาวน์โหลดไฟล์ `.json` มายังเครื่องของคุณ

## 2. แชร์โฟลเดอร์ Google Drive ให้ Service Account
1. เปิดไฟล์ JSON ที่ดาวน์โหลดมา คัดลอกอีเมลในช่อง `"client_email"` (จะมีรูปแบบเป็น `xxxx@xxxx.iam.gserviceaccount.com`)
2. เปิด [Google Drive](https://drive.google.com/) ด้วยบัญชี `pongrat555@gmail.com`
3. สร้างโฟลเดอร์ใหม่ชื่อว่า `Product_Catalog_Storage`
4. คลิกขวาที่โฟลเดอร์ -> เลือก **Share (แชร์)**
5. วางอีเมล Service Account จากข้อ 1 ลงไป และกำหนดสิทธิ์เป็น **Editor (ผู้แก้ไข)** แล้วกดส่ง

## 3. Deploy บน Streamlit Community Cloud
1. Push โค้ดทั้งหมดขึ้น **GitHub Repository**
2. ไปที่ [Streamlit Community Cloud](https://share.streamlit.io/) ล็อกอินด้วย GitHub
3. เลือก **New app** -> เลือก Repository, Branch (`main`), และ Main file path (`app.py`)
4. ก่อนกด Deploy ให้ไปที่ **Advanced settings... > Secrets** 
5. เปิดไฟล์ JSON Key ที่ดาวน์โหลดมา นำเนื้อหาทั้งหมดมาแปะลงในช่อง Secrets ในรูปแบบ TOML ดังนี้:

```toml
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
