import streamlit as st
from PIL import Image
import io


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


def main():
    st.title("Bluprint Webp Crop and Convert")

    ratio_options = ["1:1", "3:4", "4:3", "16:9", "9:16", "Custom"]
    selected_ratio = st.selectbox("Select Aspect Ratio (width:height)", ratio_options)

    if selected_ratio == "Custom":
        ratio_width = st.number_input("Width Ratio", min_value=1, value=1)
        ratio_height = st.number_input("Height Ratio", min_value=1, value=1)
    else:
        ratio_map = {
            "1:1": (1, 1),
            "3:4": (3, 4),
            "4:3": (4, 3),
            "16:9": (16, 9),
            "9:16": (9, 16)
        }
        ratio_width, ratio_height = ratio_map[selected_ratio]

    uploaded_files = st.file_uploader("Choose images...", type=["png", "jpg", "jpeg"], accept_multiple_files=True)

    if uploaded_files:
        for uploaded_file in uploaded_files:
            img = Image.open(uploaded_file)
            st.image(img, caption=f'Uploaded Image: {uploaded_file.name}', use_column_width=True)

            cropped_img = crop_image(img, ratio_width, ratio_height)

            # Convert to WebP
            img_byte_arr = io.BytesIO()
            cropped_img.save(img_byte_arr, format='WEBP')
            img_byte_arr.seek(0)

            st.image(cropped_img, caption=f'Cropped Image: {uploaded_file.name}', use_column_width=True)

            st.download_button(
                label=f"Download {uploaded_file.name.split('.')[0]}_cropped.webp",
                data=img_byte_arr,
                file_name=f"{uploaded_file.name.split('.')[0]}_cropped.webp",
                mime="image/webp"
            )


if __name__ == "__main__":
    main()
