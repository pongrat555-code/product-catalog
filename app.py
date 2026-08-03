import io
import json
import os
import streamlit as st
from PIL import Image
import cloudinary
import cloudinary.uploader
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload

# ==========================================
# Google Drive & Cloudinary Configurations
# ==========================================
SCOPES = ["https://www.googleapis.com/auth/drive"]
SHARED_FOLDER_ID = "18T7pXN-N8I7f4-x1A1B2C3D4E5F6G7H"  # 🔴 ใส่ Folder ID Google Drive ของคุณ
DATA_FILE_NAME = "catalog_data.json"

st.set_page_config(
    page_title="Product Catalog System",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ------------------------------------------
# Cloudinary Configuration
# ------------------------------------------
def init_cloudinary():
    """ตั้งค่าเชื่อมต่อ Cloudinary"""
    if "cloudinary" in st.secrets:
        cloudinary.config(
            cloud_name=st.secrets["cloudinary"]["cloud_name"],
            api_key=st.secrets["cloudinary"]["api_key"],
            api_secret=st.secrets["cloudinary"]["api_secret"],
            secure=True,
        )
    else:
        st.error("❌ ไม่พบข้อมูลการตั้งค่า Cloudinary ใน Secrets")
        st.stop()


def upload_image_to_cloudinary(file_bytes, public_id):
    """อัปโหลดรูปภาพไปยัง Cloudinary และส่งกลับเป็น Image URL"""
    try:
        response = cloudinary.uploader.upload(
            file_bytes,
            public_id=public_id,
            folder="product_catalog",
            overwrite=True,
            resource_type="image",
        )
        return response.get("secure_url")
    except Exception as e:
        st.error(f"❌ เกิดข้อผิดพลาดขณะอัปโหลดรูปภาพไป Cloudinary: {e}")
        return None


def delete_image_from_cloudinary(image_url):
    """ลบรูปภาพออกจาก Cloudinary โดยดึง public_id จาก URL"""
    try:
        if image_url and "product_catalog" in image_url:
            # สกัดหา public_id จาก URL
            filename = image_url.split("/")[-1].split(".")[0]
            public_id = f"product_catalog/{filename}"
            cloudinary.uploader.destroy(public_id)
    except Exception:
        pass


# ------------------------------------------
# Google Drive Helper Functions
# ------------------------------------------
def get_drive_service():
    """เชื่อมต่อกับ Google Drive API"""
    if "gcp_service_account" in st.secrets:
        creds = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"], scopes=SCOPES
        )
    elif os.path.exists("service_account.json"):
        creds = service_account.Credentials.from_service_account_file(
            "service_account.json", scopes=SCOPES
        )
    else:
        st.error("❌ ไม่พบข้อมูลการยืนยันตัวตน Google Drive (service_account.json หรือ Secrets)")
        st.stop()

    return build("drive", "v3", credentials=creds)


def download_file_from_drive(service, file_id):
    """ดาวน์โหลดไฟล์ JSON จาก Google Drive"""
    request = service.files().get_media(fileId=file_id)
    file_stream = io.BytesIO()
    downloader = MediaIoBaseDownload(file_stream, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    file_stream.seek(0)
    return file_stream


def load_catalog_data(service, folder_id):
    """โหลดข้อมูลแคตตาล็อก (JSON) จาก Google Drive"""
    try:
        query = f"'{folder_id}' in parents and name = '{DATA_FILE_NAME}' and trashed = false"
        results = (
            service.files()
            .list(
                q=query,
                fields="files(id, name)",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
            )
            .execute()
        )
        items = results.get("files", [])

        if items:
            file_id = items[0]["id"]
            stream = download_file_from_drive(service, file_id)
            return json.loads(stream.read().decode("utf-8")), file_id
        else:
            return [], None
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการโหลดข้อมูลแคตตาล็อก: {e}")
        return [], None


def save_catalog_data(service, folder_id, data, existing_file_id=None):
    """บันทึกข้อมูลแคตตาล็อกลงไฟล์ JSON ใน Google Drive"""
    json_bytes = json.dumps(data, ensure_ascii=False, indent=4).encode("utf-8")

    if existing_file_id:
        media = MediaIoBaseUpload(
            io.BytesIO(json_bytes), mimetype="application/json", resumable=True
        )
        service.files().update(
            fileId=existing_file_id, media_body=media, supportsAllDrives=True
        ).execute()
        return existing_file_id
    else:
        file_metadata = {"name": DATA_FILE_NAME, "parents": [folder_id]}
        media = MediaIoBaseUpload(
            io.BytesIO(json_bytes), mimetype="application/json", resumable=True
        )
        file = (
            service.files()
            .create(
                body=file_metadata,
                media_body=media,
                fields="id",
                supportsAllDrives=True,
            )
            .execute()
        )
        return file.get("id")


# ==========================================
# Main Application Layout
# ==========================================
st.title("📦 ระบบแคตตาล็อกสินค้า (Cloudinary + Google Drive)")
st.caption("จัดเก็บรูปภาพบน Cloudinary | บันทึกข้อมูลแคตตาล็อกบน Google Drive: **pongrat555@gmail.com**")

# ตั้งค่า Cloudinary และ Google Drive
init_cloudinary()

try:
    drive_service = get_drive_service()
    products_data, json_file_id = load_catalog_data(
        drive_service, SHARED_FOLDER_ID
    )
except Exception as e:
    st.error(f"เกิดข้อผิดพลาดในการเชื่อมต่อระบบ: {e}")
    st.stop()

# Sidebar Navigation
st.sidebar.title("📌 เมนูหลัก")
menu = st.sidebar.radio(
    "เลือกรายการทำรายการ:",
    [
        "🔍 แสดงสินค้า / ค้นหา",
        "➕ เพิ่มสินค้าใหม่",
        "✏️ แก้ไขข้อมูลสินค้า",
        "🗑️ ลบสินค้า",
    ],
)

st.sidebar.markdown("---")
st.sidebar.caption("📱 รองรับการถ่ายภาพสินค้า 3 มุมมองด้วยกล้องโทรศัพท์มือถือ")

# ------------------------------------------
# 1. MENU: แสดงสินค้าทั้งหมด / ค้นหา
# ------------------------------------------
if menu == "🔍 แสดงสินค้า / ค้นหา":
    st.header("📋 รายการสินค้าในระบบ")

    search_term = st.text_input(
        "🔍 ค้นหา (ระบุชื่อ, รายละเอียด หรือแหล่งที่มา):", ""
    )

    filtered_products = [
        p
        for p in products_data
        if search_term.lower() in p["name"].lower()
        or search_term.lower() in p["detail"].lower()
        or search_term.lower() in p["source"].lower()
    ]

    if not filtered_products:
        st.info("ไม่พบรายการสินค้าที่ตรงกับคำค้นหา")
    else:
        st.write(f"พบทั้งหมด **{len(filtered_products)}** รายการ")
        for prod in filtered_products:
            with st.expander(
                f"🔹 **{prod['name']}** | ราคาขาย: ฿{prod['selling_price']:,.2f}",
                expanded=True,
            ):
                col_text, col_img = st.columns([1, 1])

                with col_text:
                    st.write(f"**รหัสสินค้า:** `{prod['id']}`")
                    st.write(f"**ราคาต้นทุน:** ฿{prod['cost_price']:,.2f}")
                    st.write(f"**ราคาขาย:** ฿{prod['selling_price']:,.2f}")
                    profit = prod["selling_price"] - prod["cost_price"]
                    st.write(f"**กำไรคาดการณ์:** :green[฿{profit:,.2f}]")
                    st.write(f"**แหล่งที่มา:** {prod['source']}")
                    st.write(f"**รายละเอียด:**\n{prod['detail']}")

                with col_img:
                    st.write("**📷 รูปภาพสินค้า (3 มุมมอง):**")
                    img_cols = st.columns(3)
                    labels = ["ด้านหน้า", "ด้านข้าง/หลัง", "ป้าย/รายละเอียด"]

                    for idx, img_url in enumerate(prod.get("images", [])):
                        with img_cols[idx]:
                            if img_url:
                                st.image(
                                    img_url,
                                    caption=labels[idx],
                                    use_container_width=True,
                                )
                            else:
                                st.caption(f"ไม่มีรูป {labels[idx]}")

# ------------------------------------------
# 2. MENU: เพิ่มสินค้าใหม่
# ------------------------------------------
elif menu == "➕ เพิ่มสินค้าใหม่":
    st.header("➕ เพิ่มรายการสินค้าใหม่")
    st.info("💡 สามารถกดถ่ายรูปสินค้า 3 มุมมองผ่านกล้องโทรศัพท์มือถือได้โดยตรง")

    with st.form("add_product_form", clear_on_submit=True):
        name = st.text_input("ชื่อสินค้า *", placeholder="เช่น เสื้อยืด Oversize สีดำ")

        col_c, col_s = st.columns(2)
        with col_c:
            cost_price = st.number_input(
                "ราคาต้นทุน (บาท) *", min_value=0.0, step=10.0, format="%.2f"
            )
        with col_s:
            selling_price = st.number_input(
                "ราคาขาย (บาท) *", min_value=0.0, step=10.0, format="%.2f"
            )

        source = st.text_input("แหล่งที่มาของสินค้า", placeholder="เช่น โรงงานประตูน้ำ / Supplier A")
        detail = st.text_area("รายละเอียดสินค้า", placeholder="ระบุขนาด สเปก สี หรือข้อมูลเพิ่มเติม...")

        st.subheader("📷 ถ่ายรูปสินค้า 3 รูป")
        col_i1, col_i2, col_i3 = st.columns(3)

        with col_i1:
            st.markdown("**รูปที่ 1: ด้านหน้า**")
            cam1 = st.camera_input("ถ่ายรูปที่ 1", key="add_cam1")
        with col_i2:
            st.markdown("**รูปที่ 2: ด้านข้าง/หลัง**")
            cam2 = st.camera_input("ถ่ายรูปที่ 2", key="add_cam2")
        with col_i3:
            st.markdown("**รูปที่ 3: ป้าย/รายละเอียด**")
            cam3 = st.camera_input("ถ่ายรูปที่ 3", key="add_cam3")

        submitted = st.form_submit_button("💾 บันทึกสินค้า")

        if submitted:
            if not name:
                st.error("❌ กรุณากรอกชื่อสินค้า")
            else:
                prod_id = f"PROD-{len(products_data) + 1:04d}"
                image_urls = []

                with st.spinner("กำลังอัปโหลดรูปภาพไปยัง Cloudinary..."):
                    for idx, cam in enumerate([cam1, cam2, cam3], 1):
                        if cam:
                            file_bytes = cam.getvalue()
                            url = upload_image_to_cloudinary(
                                file_bytes, f"{prod_id}_img{idx}"
                            )
                            image_urls.append(url)
                        else:
                            image_urls.append(None)

                new_product = {
                    "id": prod_id,
                    "name": name,
                    "cost_price": cost_price,
                    "selling_price": selling_price,
                    "source": source,
                    "detail": detail,
                    "images": image_urls,
                }

                products_data.append(new_product)
                json_file_id = save_catalog_data(
                    drive_service, SHARED_FOLDER_ID, products_data, json_file_id
                )
                st.success(
                    f"✅ บันทึกสินค้า '{name}' เรียบร้อยแล้ว (รหัสสินค้า: {prod_id})"
                )

# ------------------------------------------
# 3. MENU: แก้ไขข้อมูลสินค้า
# ------------------------------------------
elif menu == "✏️ แก้ไขข้อมูลสินค้า":
    st.header("✏️ แก้ไขข้อมูลสินค้า")

    if not products_data:
        st.info("ยังไม่มีข้อมูลสินค้าในระบบ")
    else:
        prod_options = {f"{p['id']} - {p['name']}": p for p in products_data}
        selected_option = st.selectbox(
            "เลือกสินค้าที่ต้องการแก้ไข:", list(prod_options.keys())
        )
        selected_prod = prod_options[selected_option]

        with st.form("edit_product_form"):
            st.write(f"กำลังแก้ไขรหัสสินค้า: **{selected_prod['id']}**")

            new_name = st.text_input("ชื่อสินค้า", value=selected_prod["name"])
            col_c, col_s = st.columns(2)
            with col_c:
                new_cost = st.number_input(
                    "ราคาต้นทุน (บาท)",
                    value=float(selected_prod["cost_price"]),
                    min_value=0.0,
                )
            with col_s:
                new_selling = st.number_input(
                    "ราคาขาย (บาท)",
                    value=float(selected_prod["selling_price"]),
                    min_value=0.0,
                )

            new_source = st.text_input(
                "แหล่งที่มาของสินค้า", value=selected_prod["source"]
            )
            new_detail = st.text_area(
                "รายละเอียดสินค้า", value=selected_prod["detail"]
            )

            st.subheader("📷 ถ่ายรูปใหม่เพื่อเปลี่ยนรูปเดิม")
            col_i1, col_i2, col_i3 = st.columns(3)

            with col_i1:
                cam1 = st.camera_input("ถ่ายใหม่ รูปที่ 1", key="edit_cam1")
            with col_i2:
                cam2 = st.camera_input("ถ่ายใหม่ รูปที่ 2", key="edit_cam2")
            with col_i3:
                cam3 = st.camera_input("ถ่ายใหม่ รูปที่ 3", key="edit_cam3")

            update_submitted = st.form_submit_button("🔄 อัปเดตข้อมูล")

            if update_submitted:
                selected_prod["name"] = new_name
                selected_prod["cost_price"] = new_cost
                selected_prod["selling_price"] = new_selling
                selected_prod["source"] = new_source
                selected_prod["detail"] = new_detail

                with st.spinner("กำลังอัปเดตข้อมูลรูปภาพ..."):
                    for idx, cam in enumerate([cam1, cam2, cam3]):
                        if cam:
                            # ลบรูปเดิมบน Cloudinary
                            old_url = selected_prod["images"][idx]
                            delete_image_from_cloudinary(old_url)

                            # อัปโหลดรูปใหม่
                            new_url = upload_image_to_cloudinary(
                                cam.getvalue(),
                                f"{selected_prod['id']}_img{idx+1}",
                            )
                            selected_prod["images"][idx] = new_url

                    json_file_id = save_catalog_data(
                        drive_service,
                        SHARED_FOLDER_ID,
                        products_data,
                        json_file_id,
                    )

                st.success("✅ อัปเดตข้อมูลสินค้าสำเร็จ!")
                st.rerun()

# ------------------------------------------
# 4. MENU: ลบสินค้า
# ------------------------------------------
elif menu == "🗑️ ลบสินค้า":
    st.header("🗑️ ลบรายการสินค้า")

    if not products_data:
        st.info("ยังไม่มีข้อมูลสินค้าในระบบ")
    else:
        prod_options = {f"{p['id']} - {p['name']}": p for p in products_data}
        selected_option = st.selectbox(
            "เลือกสินค้าที่ต้องการลบ:", list(prod_options.keys())
        )
        selected_prod = prod_options[selected_option]

        st.warning(
            f"⚠️ คุณกำลังจะลบรายการ: **{selected_prod['name']}** (รหัสสินค้า: {selected_prod['id']})"
        )

        confirm = st.checkbox("ยืนยันการลบรายการนี้ออกจากระบบถาวร")
        if st.button("❌ ยืนยันลบสินค้า", disabled=not confirm):
            with st.spinner("กำลังลบรูปภาพบน Cloudinary และข้อมูลบน Google Drive..."):
                # ลบรูปภาพทั้งหมดบน Cloudinary
                for img_url in selected_prod.get("images", []):
                    if img_url:
                        delete_image_from_cloudinary(img_url)

                # ลบรายการใน JSON
                products_data = [
                    p for p in products_data if p["id"] != selected_prod["id"]
                ]
                json_file_id = save_catalog_data(
                    drive_service, SHARED_FOLDER_ID, products_data, json_file_id
                )

            st.success("✅ ลบสินค้าเรียบร้อยแล้ว!")
            st.rerun()
