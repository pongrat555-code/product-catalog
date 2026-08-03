import io
import json
import math
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
ITEMS_PER_PAGE = 30  # 30 รายการต่อหน้า

st.set_page_config(
    page_title="Product Catalog System",
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
    """ปรับขนาดรูปภาพให้มีความสูง 1,920px และ 96 DPI"""
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
            dpi=target_dpi
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
            target_dpi=TARGET_DPI
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

# 🔴 ตรวจสอบ URL Query Parameters ว่ามีคำสั่งเปิดโหมดแสดงดัชนีหรือไม่ (?view=index)
query_params = st.query_params
is_index_view = query_params.get("view") == "index"

# ------------------------------------------
# Mode 1: หน้าแสดงดัชนี (เมื่อเปิดผ่านแท็บใหม่) -> ซ่อน Sidebar
# ------------------------------------------
if is_index_view:
    # 🔴 CSS บังคับซ่อน Sidebar Menu และปุ่มพับเก็บ Sidebar ทั้งหมด
    st.markdown(
        """
        <style>
            [data-testid="stSidebar"] {display: none !important;}
            [data-testid="collapsedControl"] {display: none !important;}
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title("📖 ดัชนีแคตตาล็อกสินค้า (Index Book)")

    if not products_data:
        st.info("ยังไม่มีข้อมูลสินค้าในระบบ")
    else:
        # เรียงลำดับตามชื่อสินค้า (ก-ฮ / A-Z)
        sorted_products = sorted(products_data, key=lambda x: x["name"])
        total_items = len(sorted_products)
        total_pages = math.ceil(total_items / ITEMS_PER_PAGE)

        if "current_page" not in st.session_state:
            st.session_state.current_page = 1

        if st.session_state.current_page > total_pages:
            st.session_state.current_page = max(1, total_pages)

        # แถบควบคุมการเปลี่ยนหน้าด้านบน
        ctrl_col1, ctrl_col2, ctrl_col3 = st.columns([1, 2, 1])

        with ctrl_col1:
            if st.button("◄ หน้าก่อนหน้า", disabled=(st.session_state.current_page <= 1), key="top_prev"):
                st.session_state.current_page -= 1
                st.rerun()

        with ctrl_col2:
            st.markdown(
                f"<h4 style='text-align: center; margin: 0;'>หน้า {st.session_state.current_page} / {total_pages} (รวมทั้งหมด {total_items} รายการ)</h4>",
                unsafe_allow_html=True,
            )

        with ctrl_col3:
            if st.button("หน้าถัดไป ►", disabled=(st.session_state.current_page >= total_pages), key="top_next"):
                st.session_state.current_page += 1
                st.rerun()

        st.markdown("---")

        # แสดงรายการสินค้าในหน้านั้น (30 รายการ/หน้า)
        start_idx = (st.session_state.current_page - 1) * ITEMS_PER_PAGE
        end_idx = start_idx + ITEMS_PER_PAGE
        page_products = sorted_products[start_idx:end_idx]

        num_columns = 4
        cols = st.columns(num_columns)

        for i, prod in enumerate(page_products):
            col = cols[i % num_columns]
            with col:
                front_img_url = prod["images"][0] if prod.get("images") and prod["images"][0] else None

                img_html = (
                    f'<a href="{front_img_url}" target="_blank">'
                    f'<img src="{front_img_url}" style="width:300px; max-width:100%; height:auto; border-radius:8px; display:block; margin:0 auto 10px auto;">'
                    f'</a>'
                    if front_img_url
                    else '<div style="width:100%; height:200px; background-color:#E5E7EB; display:flex; align-items:center; justify-content:center; border-radius:8px; margin-bottom:10px; color:#9CA3AF;">ไม่มีรูปภาพด้านหน้า</div>'
                )

                card_html = f"""
                <div style="
                    border: 1px solid #E5E7EB;
                    border-radius: 10px;
                    padding: 12px;
                    margin-bottom: 20px;
                    background-color: #FFFFFF;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                    text-align: center;
                ">
                    {img_html}
                    <div style="font-weight: bold; font-size: 16px; margin-bottom: 6px; color: #1F2937; line-height: 1.3; height: 42px; overflow: hidden; text-overflow: ellipsis;">
                        {prod['name']}
                    </div>
                    <div style="font-size: 16px; color: #059669; font-weight: bold;">
                        ฿{prod['selling_price']:,.2f} บาท
                    </div>
                </div>
                """
                st.markdown(card_html, unsafe_allow_html=True)

        st.markdown("---")

        # แถบควบคุมการเปลี่ยนหน้าด้านล่าง
        b_ctrl1, b_ctrl2, b_ctrl3 = st.columns([1, 2, 1])

        with b_ctrl1:
            if st.button("◄ หน้าก่อนหน้า ", disabled=(st.session_state.current_page <= 1), key="bottom_prev"):
                st.session_state.current_page -= 1
                st.rerun()

        with b_ctrl2:
            selected_p = st.selectbox(
                "กระโดดไปยังหน้า:",
                options=list(range(1, total_pages + 1)),
                index=st.session_state.current_page - 1,
                key="jump_page_select"
            )
            if selected_p != st.session_state.current_page:
                st.session_state.current_page = selected_p
                st.rerun()

        with b_ctrl3:
            if st.button("หน้าถัดไป ► ", disabled=(st.session_state.current_page >= total_pages), key="bottom_next"):
                st.session_state.current_page += 1
                st.rerun()

# ------------------------------------------
# Mode 2: หน้าหลักปกติ (มี Sidebar Menu)
# ------------------------------------------
else:
    st.title("📦 ระบบแคตตาล็อกสินค้า (Cloudinary Only)")
    st.caption("จัดเก็บรูปภาพความละเอียดสูง (Height: 1,920px | Resolution: 96 DPI) บน **Cloudinary**")

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

    # 🔴 แสดงปุ่ม/ลิงก์สำหรับคลิกเปิดเมนู "สร้างดัชนี" ในแท็บใหม่
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        """
        <a href="?view=index" target="_blank" style="
            display: block;
            width: 100%;
            background-color: #2563EB;
            color: white;
            text-align: center;
            padding: 10px 0px;
            border-radius: 8px;
            font-weight: bold;
            text-decoration: none;
            margin-bottom: 15px;
        ">📖 เปิดหน้าสร้างดัชนี (แท็บใหม่) ↗</a>
        """,
        unsafe_allow_html=True,
    )
    st.sidebar.caption("📱 รองรับการถ่ายภาพสินค้า 3 มุมมองด้วยกล้องโทรศัพท์มือถือ")

    # ------------------------------------------
    # 1. MENU: แสดงสินค้าทั้งหมด / ค้นหา
    # ------------------------------------------
    if menu == "🔍 แสดงสินค้า / ค้นหา":
        st.header("📋 รายการสินค้าในระบบ")

        search_term = st.text_input("🔍 ค้นหา (ระบุชื่อ, รายละเอียด หรือแหล่งที่มา):", "")

        filtered_products = [
            p for p in products_data
            if search_term.lower() in p["name"].lower()
            or search_term.lower() in p["detail"].lower()
            or search_term.lower() in p["source"].lower()
        ]

        if not filtered_products:
            st.info("ไม่พบรายการสินค้าที่ตรงกับคำค้นหา")
        else:
            st.write(f"พบทั้งหมด **{len(filtered_products)}** รายการ")
            for prod in filtered_products:
                with st.expander(f"🔹 **{prod['name']}** | ราคาขาย: ฿{prod['selling_price']:,.2f}", expanded=True):
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
                        st.write("**📷 รูปภาพสินค้า (คลิกที่รูปเพื่อขยายแบบ HD 96 DPI ในหน้าต่างใหม่):**")
                        img_cols = st.columns(3)
                        labels = ["ด้านหน้า", "ด้านหลัง", "ด้านข้าง"]

                        for idx, img_url in enumerate(prod.get("images", [])):
                            with img_cols[idx]:
                                if img_url:
                                    st.markdown(
                                        f'<a href="{img_url}" target="_blank">'
                                        f'<img src="{img_url}" style="width:100%; border-radius:5px; margin-bottom:5px;">'
                                        f'</a>',
                                        unsafe_allow_html=True,
                                    )
                                    st.caption(f"🔍 {labels[idx]} (คลิกเพื่อขยาย)")
                                else:
                                    st.caption(f"ไม่มีรูป {labels[idx]}")

    # ------------------------------------------
    # 2. MENU: เพิ่มสินค้าใหม่
    # ------------------------------------------
    elif menu == "➕ เพิ่มสินค้าใหม่":
        st.header("➕ เพิ่มรายการสินค้าใหม่")
        st.info("💡 ภาพถ่ายจะถูกปรับความสูงที่ 1,920px และความละเอียดที่ 96 DPI โดยอัตโนมัติ")

        with st.form("add_product_form", clear_on_submit=True):
            name = st.text_input("ชื่อสินค้า *", placeholder="เช่น เสื้อยืด Oversize สีดำ")

            col_c, col_s = st.columns(2)
            with col_c:
                cost_price = st.number_input("ราคาต้นทุน (บาท) *", min_value=0.0, step=10.0, format="%.2f")
            with col_s:
                selling_price = st.number_input("ราคาขาย (บาท) *", min_value=0.0, step=10.0, format="%.2f")

            source = st.text_input("แหล่งที่มาของสินค้า", placeholder="เช่น โรงงานประตูน้ำ / Supplier A")
            detail = st.text_area("รายละเอียดสินค้า", placeholder="ระบุขนาด สเปก สี หรือข้อมูลเพิ่มเติม...")

            st.subheader("📷 ถ่ายรูปสินค้า 3 รูป")
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

            submitted = st.form_submit_button("💾 บันทึกสินค้า")

            if submitted:
                if not name:
                    st.error("❌ กรุณากรอกชื่อสินค้า")
                else:
                    prod_id = f"PROD-{len(products_data) + 1:04d}"
                    image_urls = []

                    with st.spinner("กำลังปรับขนาดเป็น 1,920px (96 DPI) และอัปโหลดไปยัง Cloudinary..."):
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
                        st.success(f"✅ บันทึกสินค้า '{name}' เรียบร้อยแล้ว (รหัสสินค้า: {prod_id})")

    # ------------------------------------------
    # 3. MENU: แก้ไขข้อมูลสินค้า
    # ------------------------------------------
    elif menu == "✏️ แก้ไขข้อมูลสินค้า":
        st.header("✏️ แก้ไขข้อมูลสินค้า")

        if not products_data:
            st.info("ยังไม่มีข้อมูลสินค้าในระบบ")
        else:
            prod_options = {f"{p['id']} - {p['name']}": p for p in products_data}
            selected_option = st.selectbox("เลือกสินค้าที่ต้องการแก้ไข:", list(prod_options.keys()))
            selected_prod = prod_options[selected_option]

            with st.form("edit_product_form"):
                st.write(f"กำลังแก้ไขรหัสสินค้า: **{selected_prod['id']}**")

                new_name = st.text_input("ชื่อสินค้า", value=selected_prod["name"])
                col_c, col_s = st.columns(2)
                with col_c:
                    new_cost = st.number_input("ราคาต้นทุน (บาท)", value=float(selected_prod["cost_price"]), min_value=0.0)
                with col_s:
                    new_selling = st.number_input("ราคาขาย (บาท)", value=float(selected_prod["selling_price"]), min_value=0.0)

                new_source = st.text_input("แหล่งที่มาของสินค้า", value=selected_prod["source"])
                new_detail = st.text_area("รายละเอียดสินค้า", value=selected_prod["detail"])

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

                    with st.spinner("กำลังประมวลผลรูปถ่าย (96 DPI) และอัปเดตข้อมูล..."):
                        for idx, cam in enumerate([cam1, cam2, cam3]):
                            if cam:
                                old_url = selected_prod["images"][idx]
                                delete_image_from_cloudinary(old_url)

                                new_url = upload_image_to_cloudinary(cam.getvalue(), f"{selected_prod['id']}_img{idx+1}")
                                selected_prod["images"][idx] = new_url

                        if save_catalog_data(products_data):
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
            selected_option = st.selectbox("เลือกสินค้าที่ต้องการลบ:", list(prod_options.keys()))
            selected_prod = prod_options[selected_option]

            st.warning(f"⚠️ คุณกำลังจะลบรายการ: **{selected_prod['name']}** (รหัสสินค้า: {selected_prod['id']})")

            confirm = st.checkbox("ยืนยันการลบรายการนี้ออกจากระบบถาวร")
            if st.button("❌ ยืนยันลบสินค้า", disabled=not confirm):
                with st.spinner("กำลังลบรูปภาพและข้อมูลบน Cloudinary..."):
                    for img_url in selected_prod.get("images", []):
                        if img_url:
                            delete_image_from_cloudinary(img_url)

                    products_data = [p for p in products_data if p["id"] != selected_prod["id"]]
                    if save_catalog_data(products_data):
                        st.success("✅ ลบสินค้าเรียบร้อยแล้ว!")
                        st.rerun()
