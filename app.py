import io

import streamlit as st
from PIL import Image, ImageEnhance
import zipfile
from pillow_heif import register_heif_opener
from os.path import splitext

register_heif_opener()


def crop_image(img, ratio_width, ratio_height):
    img_width, img_height = img.size
    target_width = img_width
    target_height = int(img_width * (ratio_height / ratio_width))

    if target_height > img_height:
        target_height = img_height
        target_width = int(img_height * (ratio_width / ratio_height))

    left = (img_width - target_width) / 2
    top = (img_height - target_height) / 2
    right = (img_width + target_width) / 2
    bottom = (img_height + target_height) / 2

    return img.crop((left, top, right, bottom))


def add_watermark(base_image, watermark, transparency, size_ratio, position, padding=0):
    # Maintain aspect ratio and fit watermark within the base image
    base_width, base_height = base_image.size
    watermark_width, watermark_height = watermark.size

    max_width = int(base_width * size_ratio)
    max_height = int(base_height * size_ratio)

    ratio = min(max_width / watermark_width, max_height / watermark_height)
    new_size = (int(watermark_width * ratio), int(watermark_height * ratio))

    watermark = watermark.resize(new_size, Image.Resampling.LANCZOS)
    watermark = watermark.convert("RGBA")

    # Adjust watermark transparency
    alpha = watermark.split()[3]
    alpha = ImageEnhance.Brightness(alpha).enhance(transparency)
    watermark.putalpha(alpha)

    # Calculate padding in pixels
    padding_x = int(base_width * padding)
    padding_y = int(base_height * padding)

    # Position watermark with padding
    watermark_positions = {
        "↘️ bottom right": (base_image.width - watermark.width - padding_x, base_image.height - watermark.height - padding_y),
        "↙️ bottom left️": (padding_x, base_image.height - watermark.height - padding_y),
        "↗️ top right": (base_image.width - watermark.width - padding_x, padding_y),
        "↖️ top left": (padding_x, padding_y),
        "⏺️ center": ((base_image.width - watermark.width) // 2, (base_image.height - watermark.height) // 2)
    }

    watermark_position = watermark_positions.get(position, "↘️ bottom right")

    # Create a new image for the result
    watermarked_image = base_image.copy()
    watermarked_image.paste(watermark, watermark_position, watermark)

    return watermarked_image


def create_zip(images, filenames):
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for img_byte_arr, filename in zip(images, filenames):
            zip_file.writestr(f'{filename}.webp', img_byte_arr.read())
    zip_buffer.seek(0)
    return zip_buffer


def main():
    st.set_page_config(
        page_title="Bluprint Webp Crop and Convert",
        page_icon="sunrise_over_mountains",
        # layout="wide",
    )
    st.title("Bluprint Webp Crop and Convert")

    ratio_options = ["1:1", "4:3", "3:4", "16:9", "9:16", "2:1", "1:2", "Custom"]
    selected_ratio = st.selectbox("Select Aspect Ratio (width:height)", ratio_options)

    if selected_ratio == "Custom":
        ratio_width = st.number_input("Width Ratio", min_value=1, value=1)
        ratio_height = st.number_input("Height Ratio", min_value=1, value=1)
    else:
        ratio_map = {
            "1:1": (1, 1),
            "4:3": (4, 3),
            "3:4": (3, 4),
            "16:9": (16, 9),
            "9:16": (9, 16),
            "2:1": (2, 1),
            "1:2": (1, 2),
        }
        ratio_width, ratio_height = ratio_map[selected_ratio]

    with st.expander("Advanced", icon='🛠'):
        quality = st.slider("Export Quality (default=80)", 0, 100, 80)
        # exact = st.checkbox("Preserve Transparency")
        preview_limit = st.number_input("Preview Limit", min_value=0, value=1)

    watermark_option = st.checkbox("Add Watermark")

    image_formats = ["heic", "heif", "png", "jpg", "jpeg", "ico", "tif", "tiff", "jp2", "bmp", "webp"]

    if watermark_option:
        with st.expander("Watermark Options", expanded=True, icon='📌'):
            watermark_file = st.file_uploader("Upload Watermark", type=image_formats)
            transparency = st.slider("Set Watermark Transparency", 0.0, 1.0, 0.5)
            size_ratio = st.slider("Set Watermark Size Ratio", 0.0, 1.0, 0.20)
            position = st.selectbox("Select Watermark Position",
                                    ["↘️ bottom right", "↙️ bottom left️", "↗️ top right", "↖️ top left", "⏺️ center"])
            if position == "⏺️ center":
                padding = 0
            else:
                padding = st.slider("Set Watermark Padding", 0.0, 0.5, 0.05)

    uploaded_files = st.file_uploader("Choose images...", type=image_formats, accept_multiple_files=True)

    if uploaded_files:
        images = []
        filenames = {}

        for uploaded_file in uploaded_files:
            try:
                img = Image.open(uploaded_file)
                # st.image(img, caption=f'Uploaded Image: {uploaded_file.name}', use_column_width=True)
                cropped_img = crop_image(img, ratio_width, ratio_height)

                if watermark_option and watermark_file:
                    watermark = Image.open(watermark_file)
                    cropped_img = add_watermark(cropped_img, watermark, transparency, size_ratio, position, padding)

                img_byte_arr = io.BytesIO()
                cropped_img.save(img_byte_arr, format='WEBP', quality=quality)
                img_byte_arr.seek(0)

                if preview_limit:
                    st.image(cropped_img, caption=f'Result of: {uploaded_file.name}', use_column_width=True)
                    preview_limit -= 1

                original_name = splitext(uploaded_file.name)[0]
                name = original_name
                duplicate_name_num = 1
                while name in filenames:
                    name = f"{original_name} ({duplicate_name_num})"
                    duplicate_name_num += 1

                images.append(img_byte_arr)
                filenames[name] = None
            except Exception as e:
                st.error(f"Error processing {uploaded_file.name}: {e}")

        if len(images) == 1:
            first_name = next(iter(filenames))
            st.download_button(
                label=f"Download {first_name}.webp",
                data=images[0],
                file_name=f"{first_name}.webp",
                mime="image/webp"
            )
        else:
            # Create zip file
            zip_buffer = create_zip(images, filenames)
            st.download_button(
                label="Download All Exported Images as ZIP",
                data=zip_buffer,
                file_name="exported_images.zip",
                mime="application/zip"
            )


if __name__ == "__main__":
    main()
