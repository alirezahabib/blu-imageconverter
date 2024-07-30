import io

import streamlit as st
from PIL import Image, ImageEnhance


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


def add_watermark(base_image, watermark, transparency, size_ratio):
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

    # Position watermark at the bottom right corner
    watermark_position = (base_width - watermark.width, base_height - watermark.height)

    # Create a new image for the result
    watermarked_image = base_image.copy()
    watermarked_image.paste(watermark, watermark_position, watermark)

    return watermarked_image


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

    watermark_option = st.checkbox("Add Watermark")

    if watermark_option:
        with st.expander("Watermark Options", expanded=True, icon='📌'):
            watermark_file = st.file_uploader("Upload Watermark", type=["png", "jpg", "jpeg"])
            transparency = st.slider("Set Watermark Transparency", 0.0, 1.0, 0.5)
            size_ratio = st.slider("Set Watermark Size Ratio", 0.0, 1.0, 0.20)

    uploaded_files = st.file_uploader("Choose images...", type=["png", "jpg", "jpeg"], accept_multiple_files=True)

    if uploaded_files:
        for uploaded_file in uploaded_files:
            img = Image.open(uploaded_file)
            # st.image(img, caption=f'Uploaded Image: {uploaded_file.name}', use_column_width=True)

            cropped_img = crop_image(img, ratio_width, ratio_height)

            if watermark_option and watermark_file:
                watermark = Image.open(watermark_file)
                cropped_img = add_watermark(cropped_img, watermark, transparency, size_ratio)

            # Convert to WebP
            img_byte_arr = io.BytesIO()
            cropped_img.save(img_byte_arr, format='WEBP')
            img_byte_arr.seek(0)

            st.image(cropped_img, caption=f'Cropped Image: {uploaded_file.name}', use_column_width=True)

            st.download_button(
                label=f"Download {uploaded_file.name}_cropped.webp",
                data=img_byte_arr,
                file_name=f"{uploaded_file.name}_cropped.webp",
                mime="image/webp"
            )


if __name__ == "__main__":
    main()
