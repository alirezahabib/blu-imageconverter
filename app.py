import io
import zipfile
from os.path import splitext
from pathlib import Path

import streamlit as st
import streamlit_authenticator as stauth
import yaml
from PIL import Image, ImageEnhance
from pillow_heif import register_heif_opener
from yaml.loader import SafeLoader

from admin_page import admin_page

from presets import presets

register_heif_opener()

# Set the assets directory path
assets_dir = Path('./assets')


# Get the list of assets (presets)
def get_asset_list():
    asset_list = [d.name for d in assets_dir.iterdir() if d.is_dir()]
    asset_list.sort()  # Sort inplace (better performance than sorted())
    return asset_list


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


def add_on_top(base_image, watermark, transparency, size_ratio, position, padding=0, fill=False):
    # Maintain aspect ratio and fit watermark within the base image
    base_width, base_height = base_image.size
    watermark_width, watermark_height = watermark.size

    max_width = int(base_width * size_ratio)
    max_height = int(base_height * size_ratio)

    if fill:
        ratio = max(max_width / watermark_width, max_height / watermark_height)
    else:
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
        "↘️ bottom right": (
            base_image.width - watermark.width - padding_x, base_image.height - watermark.height - padding_y),
        "↙️ bottom left️": (padding_x, base_image.height - watermark.height - padding_y),
        "↗️ top right": (base_image.width - watermark.width - padding_x, padding_y),
        "↖️ top left": (padding_x, padding_y),
        "⏺️ center": ((base_image.width - watermark.width) // 2, (base_image.height - watermark.height) // 2)
    }

    watermark_position = watermark_positions.get(position, "↖️ top left")

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
    asset_select = ['Custom'] + get_asset_list()
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

    watermark_option = st.checkbox("Add Watermark")

    image_formats = ["heic", "heif", "png", "jpg", "jpeg", "ico", "tif", "tiff", "jp2", "bmp", "webp"]
    selected_preset = 'Custom'

    if watermark_option:
        with st.expander("Watermark Options", expanded=True, icon='📌'):
            selected_preset = st.selectbox("Set Watermark Preset", asset_select)
            watermark_file = st.file_uploader("Upload Watermark", type=image_formats,
                                              disabled=selected_preset != "Custom")
            if selected_preset != 'Custom':
                watermark_file = f'./assets/{selected_preset}/logo/logo.png'
            if watermark_file:
                watermark = Image.open(watermark_file)
            if selected_preset != 'Custom':
                st.image(watermark_file, use_column_width=True)

            transparency = st.slider('Set Watermark Transparency', 0.0, 1.0,
                                     presets.get(selected_preset, {}).get('transparency', 0.5))
            size_ratio = st.slider('Set Watermark Size Ratio', 0.0, 1.0,
                                   presets.get(selected_preset, {}).get('size_ratio', 0.20))
            position = st.selectbox('Select Watermark Position',
                                    ['↘️ bottom right', '↙️ bottom left️', '↗️ top right', '↖️ top left', '⏺️ center'],
                                    index=presets.get(selected_preset, {}).get('position', 0))
            if position == "⏺️ center":
                padding = 0
            else:
                padding = st.slider('Set Watermark Padding', 0.0, 0.5, 0.05)

    pattern_option = st.checkbox('Add Pattern')

    if pattern_option:
        with st.expander('Pattern Options', expanded=True, icon='🎨'):
            selected_pattern = st.selectbox('Set Pattern Preset', asset_select,
                                            index=asset_select.index(selected_preset))
            pattern_file = st.file_uploader('Upload Pattern', type=image_formats,
                                            disabled=selected_pattern != 'Custom')
            if selected_pattern != 'Custom':
                pattern_file = f'./assets/{selected_pattern}/pattern/pattern.png'
            if pattern_file:
                pattern = Image.open(pattern_file)
            if selected_preset != 'Custom':
                st.image(pattern_file, use_column_width=True)

            pattern_transparency = st.slider('Set Pattern Transparency', 0.0, 1.0,
                                             presets.get(selected_pattern, {}).get('transparency', 0.5))

    uploaded_files = st.file_uploader('Choose images...', type=image_formats, accept_multiple_files=True)

    images = []
    filenames = {}

    if uploaded_files:
        try:
            img = Image.open(uploaded_files[0])
            cropped_img = crop_image(img, ratio_width, ratio_height)

            if pattern_option and pattern_file:
                cropped_img = add_on_top(cropped_img, pattern, pattern_transparency, 1.0, '↖️ top left', fill=True)

            if watermark_option and watermark_file:
                cropped_img = add_on_top(cropped_img, watermark, transparency, size_ratio, position, padding)

            img_byte_arr = io.BytesIO()
            cropped_img.save(img_byte_arr, format='WEBP', quality=quality)
            img_byte_arr.seek(0)

            st.image(cropped_img, caption=f'Result of: {uploaded_files[0].name}', use_column_width=True)

            original_name = splitext(uploaded_files[0].name)[0]
            name = original_name
            duplicate_name_num = 1
            while name in filenames:
                name = f'{original_name} ({duplicate_name_num})'
                duplicate_name_num += 1

            images.append(img_byte_arr)
            filenames[name] = None

        except Exception as e:
            st.error(f'Error processing {uploaded_files[0].name}: {e}')

        if len(uploaded_files) > 1 and st.button('Export All'):
            st.info('Exporting all images...')

            for uploaded_file in uploaded_files[1:]:
                try:
                    img = Image.open(uploaded_file)
                    cropped_img = crop_image(img, ratio_width, ratio_height)

                    if pattern_option and pattern_file:
                        cropped_img = add_on_top(cropped_img, pattern, pattern_transparency, 1.0, '↖️ top left',
                                                 fill=True)

                    if watermark_option and watermark_file:
                        cropped_img = add_on_top(cropped_img, watermark, transparency, size_ratio, position, padding)

                    img_byte_arr = io.BytesIO()
                    cropped_img.save(img_byte_arr, format='WEBP', quality=quality)
                    img_byte_arr.seek(0)

                    original_name = splitext(uploaded_file.name)[0]
                    name = original_name
                    duplicate_name_num = 1
                    while name in filenames:
                        name = f"{original_name} ({duplicate_name_num})"
                        duplicate_name_num += 1

                    images.append(img_byte_arr)
                    filenames[name] = None
                except Exception as e:
                    st.error(f'Error processing {uploaded_file.name}: {e}')

            zip_buffer = create_zip(images, filenames)
            st.download_button(
                label='Download exported_images.zip',
                data=zip_buffer,
                file_name='exported_images.zip',
                mime='application/zip'
            )

        if len(uploaded_files) == 1:
            first_name = next(iter(filenames))
            st.download_button(
                label=f"Download {first_name}.webp",
                data=images[0],
                file_name=f"{first_name}.webp",
                mime="image/webp"
            )


if __name__ == "__main__":
    st.set_page_config(
        page_title="Bluprint Webp Crop and Convert",
        page_icon="sunrise_over_mountains",
        # layout="wide",
    )
    st.title("Bluprint Webp Crop and Convert")

    with open('./users.yaml') as file:
        config = yaml.load(file, Loader=SafeLoader)

    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days'],
        config['preauthorized']
    )

    name, authentication_status, username = authenticator.login('main')

    if authentication_status:
        if username == 'admin':
            admin_page()
        else:
            main()

        st.divider()
        st.write(f'Logged in as *{name}*')
        authenticator.logout('Logout', 'main')
    elif authentication_status is None:
        st.info('Please enter your username and password')
    elif not authentication_status:
        st.error('Username/password is incorrect')

    st.write("Made with ❤️ at [Bluprint](https://bluprint.ir)")
