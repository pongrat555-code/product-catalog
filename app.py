import io
import json
import requests
import streamlit as st
from PIL import Image
import cloudinary
import cloudinary.uploader
import cloudinary.api

# ==========================================
# Cloudinary Configurations & Constants
# ==========================================
JSON_PUBLIC_ID = "product_catalog/catalog_data"
TARGET_HEIGHT = 1920
TARGET_DPI = (96, 96)

st.set_page_config(
    page_title="ระบบแคตตาล็อกพระเครื่อง",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)


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


def process_image_resolution(file_bytes, target_height=1920, target_dpi=(96, 96)):
    """ปรับขนาดรูปภาพให้มีความสูง 1,920px และความละเอียด 96 DPI"""
    try:
        img = Image.open(io.BytesIO(file_bytes))
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        orig_width, orig_height = img.size
        aspect_ratio = orig_width / orig_height
        target_width = int(target_height * aspect_ratio)

        resized_img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)

        buffer = io.BytesIO()
        resized_img.save(
            buffer,
            format="JPEG",
            quality=98,
            subsampling=0,
            dpi=target_dpi,
        )
        return buffer.getvalue()
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการปรับขนาดและกำหนด DPI รูปภาพ: {e}")
        return file_bytes


def upload_image_to_cloudinary(file_bytes, public_id):
    """อัปโหลดรูปภาพไปยัง Cloudinary"""
    try:
        processed_bytes = process_image_resolution(
            file_bytes,
            target_height=TARGET_HEIGHT,
            target_dpi=TARGET_DPI,
        )

        response = cloudinary.uploader.upload(
            processed_bytes,
            public_id=public_id,
            folder="product_catalog/images",
            overwrite=True,
            resource_type="image",
        )
        return response.get("secure_url")
    except Exception as e:
        st.error(f"❌ เกิดข้อผิดพลาดขณะอัปโหลดรูปภาพไป Cloudinary: {e}")
        return None


def delete_image_from_cloudinary(image_url):
    """ลบรูปภาพออกจาก Cloudinary"""
    try:
        if image_url and "product_catalog/images" in image_url:
            filename = image_url.split("/")[-1].split(".")[0]
            public_id = f"product_catalog/images/{filename}"
            cloudinary.uploader.destroy(public_id, resource_type="image")
    except Exception:
        pass


def load_catalog_data():
    """โหลดข้อมูลแคตตาล็อก (JSON) จาก Cloudinary"""
    try:
        resource = cloudinary.api.resource(JSON_PUBLIC_ID, resource_type="raw")
        url = resource.get("secure_url")
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        return []
    except cloudinary.exceptions.NotFound:
        return []
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการโหลดข้อมูลแคตตาล็อก: {e}")
        return []


def save_catalog_data(data):
    """บันทึกข้อมูลแคตตาล็อกลงไฟล์ JSON ใน Cloudinary"""
    try:
        json_bytes = json.dumps(data, ensure_ascii=False, indent=4).encode("utf-8")

        cloudinary.uploader.upload(
            json_bytes,
            public_id=JSON_PUBLIC_ID,
            overwrite=True,
            resource_type="raw",
            invalidate=True,
        )
        return True
    except Exception as e:
        st.error(f"❌ เกิดข้อผิดพลาดขณะบันทึกข้อมูลแคตตาล็อก: {e}")
        return False


# ==========================================
# Main Application Setup
# ==========================================
init_cloudinary()
products_data = load_catalog_data()

st.title("📦 ระบบแคตตาล็อกพระเครื่อง")

# Sidebar Navigation
st.sidebar.title("📌 เมนูหลัก")
menu = st.sidebar.radio(
    "เลือกรายการทำรายการ:",
    [
        "🔍 แสดงพระเครื่อง / ค้นหา",
        "➕ เพิ่มพระเครื่องใหม่",
        "✏️ แก้ไขข้อมูลพระเครื่อง",
        "🗑️ ลบพระเครื่อง",
    ],
)

# ------------------------------------------
# 1. MENU: แสดงพระเครื่องทั้งหมด / ค้นหา
# ------------------------------------------
if menu == "🔍 แสดงพระเครื่อง / ค้นหา":
    st.header("📋 รายการพระเครื่องในระบบ")

    search_term = st.text_input("🔍 ค้นหา (ระบุชื่อ, รายละเอียด หรือแหล่งที่มา):", "")

    filtered_products = [
        p
        for p in products_data
        if search_term.lower() in p["name"].lower()
        or search_term.lower() in p["detail"].lower()
        or search_term.lower() in p["source"].lower()
    ]

    if not filtered_products:
        st.info("ไม่พบรายการพระเครื่องที่ตรงกับคำค้นหา")
    else:
        st.write(f"พบทั้งหมด **{len(filtered_products)}** รายการ")
        for prod in filtered_products:
            with st.expander(
                f"🔹 **{prod['name']}**",
                expanded=True,
            ):
                col_text, col_img = st.columns([1, 1])

                with col_text:
                    st.write(f"**รหัสพระเครื่อง:** `{prod['id']}`")
                    st.write(f"**ราคาต้นทุน:** ฿{prod['cost_price']:,.2f}")
                    st.write(f"**ราคาขาย:** ฿{prod['selling_price']:,.2f}")
                    profit = prod["selling_price"] - prod["cost_price"]
                    st.write(f"**กำไรคาดการณ์:** :green[฿{profit:,.2f}]")
                    st.write(f"**แหล่งที่มา:** {prod['source']}")
                    st.write(f"**รายละเอียด:**\n{prod['detail']}")

                with col_img:
                    st.write("**📷 รูปภาพพระเครื่อง:**")
                    img_cols = st.columns(3)
                    labels = ["ด้านหน้า", "ด้านหลัง", "ด้านข้าง"]

                    for idx, img_url in enumerate(prod.get("images", [])):
                        with img_cols[idx]:
                            if img_url:
                                st.markdown(
                                    f'<a href="{img_url}" target="_blank">'
                                    f'<img src="{img_url}" style="width:100%; border-radius:5px; margin-bottom:5px;">'
                                    f"</a>",
                                    unsafe_allow_html=True,
                                )
                                st.markdown(
                                    f"<div style='text-align: center; font-size: 14px; color: #6B7280;'>{labels[idx]}</div>",
                                    unsafe_allow_html=True,
                                )
                            else:
                                st.markdown(
                                    f"<div style='text-align: center; font-size: 14px; color: #9CA3AF;'>ไม่มีรูป {labels[idx]}</div>",
                                    unsafe_allow_html=True,
                                )

# ------------------------------------------
# 2. MENU: เพิ่มพระเครื่องใหม่
# ------------------------------------------
elif menu == "➕ เพิ่มพระเครื่องใหม่":
    st.header("➕ เพิ่มรายการพระเครื่องใหม่")

    with st.form("add_product_form", clear_on_submit=True):
        name = st.text_input("ชื่อพระเครื่อง *", placeholder="เช่น พระสมเด็จวัดระฆัง พิมพ์ใหญ่")

        col_c, col_s = st.columns(2)
        with col_c:
            cost_price = st.number_input(
                "ราคาต้นทุน (บาท) *", min_value=0.0, step=10.0, format="%.2f"
            )
        with col_s:
            selling_price = st.number_input(
                "ราคาขาย (บาท) *", min_value=0.0, step=10.0, format="%.2f"
            )

        source = st.text_input("แหล่งที่มาของพระเครื่อง", placeholder="เช่น รังพระท่าพระจันทร์ / สายตรง")
        detail = st.text_area("รายละเอียดพระเครื่อง", placeholder="ระบุพิมพ์ทรง เนื้อหา สภาพพระ หรือข้อมูลเพิ่มเติม...")

        st.subheader("📷 ถ่ายรูปพระเครื่อง 3 รูป")
        col_i1, col_i2, col_i3 = st.columns(3)

        with col_i1:
            st.markdown("**รูปที่ 1: ด้านหน้า**")
            cam1 = st.camera_input("ถ่ายรูปด้านหน้า", key="add_cam1")
        with col_i2:
            st.markdown("**รูปที่ 2: ด้านหลัง**")
            cam2 = st.camera_input("ถ่ายรูปด้านหลัง", key="add_cam2")
        with col_i3:
            st.markdown("**รูปที่ 3: ด้านข้าง**")
            cam3 = st.camera_input("ถ่ายรูปด้านข้าง", key="add_cam3")

        submitted = st.form_submit_button("💾 บันทึกพระเครื่อง")

        if submitted:
            if not name:
                st.error("❌ กรุณากรอกชื่อพระเครื่อง")
            else:
                prod_id = f"PROD-{len(products_data) + 1:04d}"
                image_urls = []

                with st.spinner("กำลังประมวลผลและอัปโหลดรูปภาพ..."):
                    for idx, cam in enumerate([cam1, cam2, cam3], 1):
                        if cam:
                            file_bytes = cam.getvalue()
                            url = upload_image_to_cloudinary(file_bytes, f"{prod_id}_img{idx}")
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
                if save_catalog_data(products_data):
                    st.success(f"✅ บันทึกพระเครื่อง '{name}' เรียบร้อยแล้ว (รหัสพระเครื่อง: {prod_id})")

# ------------------------------------------
# 3. MENU: แก้ไขข้อมูลพระเครื่อง
# ------------------------------------------
elif menu == "✏️ แก้ไขข้อมูลพระเครื่อง":
    st.header("✏️ แก้ไขข้อมูลพระเครื่อง")

    if not products_data:
        st.info("ยังไม่มีข้อมูลพระเครื่องในระบบ")
    else:
        prod_options = {f"{p['id']} - {p['name']}": p for p in products_data}
        selected_option = st.selectbox("เลือกพระเครื่องที่ต้องการแก้ไข:", list(prod_options.keys()))
        selected_prod = prod_options[selected_option]

        with st.form("edit_product_form"):
            st.write(f"กำลังแก้ไขรหัสพระเครื่อง: **{selected_prod['id']}**")

            new_name = st.text_input("ชื่อพระเครื่อง", value=selected_prod["name"])
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

            new_source = st.text_input("แหล่งที่มาของพระเครื่อง", value=selected_prod["source"])
            new_detail = st.text_area("รายละเอียดพระเครื่อง", value=selected_prod["detail"])

            st.subheader("📷 ถ่ายรูปใหม่เพื่อเปลี่ยนรูปเดิม")
            col_i1, col_i2, col_i3 = st.columns(3)

            with col_i1:
                cam1 = st.camera_input("ถ่ายใหม่ รูปด้านหน้า", key="edit_cam1")
            with col_i2:
                cam2 = st.camera_input("ถ่ายใหม่ รูปด้านหลัง", key="edit_cam2")
            with col_i3:
                cam3 = st.camera_input("ถ่ายใหม่ รูปด้านข้าง", key="edit_cam3")

            update_submitted = st.form_submit_button("🔄 อัปเดตข้อมูล")

            if update_submitted:
                selected_prod["name"] = new_name
                selected_prod["cost_price"] = new_cost
                selected_prod["selling_price"] = new_selling
                selected_prod["source"] = new_source
                selected_prod["detail"] = new_detail

                with st.spinner("กำลังประมวลผลรูปถ่ายและอัปเดตข้อมูล..."):
                    for idx, cam in enumerate([cam1, cam2, cam3]):
                        if cam:
                            old_url = selected_prod["images"][idx]
                            delete_image_from_cloudinary(old_url)

                            new_url = upload_image_to_cloudinary(
                                cam.getvalue(), f"{selected_prod['id']}_img{idx+1}"
                            )
                            selected_prod["images"][idx] = new_url

                    if save_catalog_data(products_data):
                        st.success("✅ อัปเดตข้อมูลพระเครื่องสำเร็จ!")
                        st.rerun()

# ------------------------------------------
# 4. MENU: ลบพระเครื่อง
# ------------------------------------------
elif menu == "🗑️ ลบพระเครื่อง":
    st.header("🗑️ ลบรายการพระเครื่อง")

    if not products_data:
        st.info("ยังไม่มีข้อมูลพระเครื่องในระบบ")
    else:
        prod_options = {f"{p['id']} - {p['name']}": p for p in products_data}
        selected_option = st.selectbox("เลือกพระเครื่องที่ต้องการแก้ไข/ลบ:", list(prod_options.keys()))
        selected_prod = prod_options[selected_option]

        st.warning(
            f"⚠️ คุณกำลังจะลบรายการ: **{selected_prod['name']}** (รหัสพระเครื่อง: {selected_prod['id']})"
        )

        confirm = st.checkbox("ยืนยันการลบรายการนี้ออกจากระบบถาวร")
        if st.button("❌ ยืนยันลบพระเครื่อง", disabled=not confirm):
            with st.spinner("กำลังลบรูปภาพและข้อมูล..."):
                for img_url in selected_prod.get("images", []):
                    if img_url:
                        delete_image_from_cloudinary(img_url)

                products_data = [p for p in products_data if p["id"] != selected_prod["id"]]
                if save_catalog_data(products_data):
                    st.success("✅ ลบพระเครื่องเรียบร้อยแล้ว!")
                    st.rerun()
