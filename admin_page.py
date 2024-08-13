import shutil
from pathlib import Path

import streamlit as st

assets_dir = Path('./assets')


def get_asset_list():
    asset_list = [d.name for d in assets_dir.iterdir() if d.is_dir()]
    asset_list.sort()  # Sort inplace (better performance than sorted())
    return asset_list


# Upload and save a new file to a preset directory
def upload_file(directory, file_type):
    # Ensure directory exists, if not, create it
    file_type_dir = directory / file_type
    file_type_dir.mkdir(parents=True, exist_ok=True)

    # File upload logic
    file = st.file_uploader(f"Upload {file_type}", type=["png"], key=file_type)
    if file:
        file_path = file_type_dir / f"{file_type}.png"
        with open(file_path, "wb") as f:
            f.write(file.read())
        st.success(f"{file_type}.png updated successfully!")


# Delete a preset
def delete_preset(preset_name):
    preset_dir = assets_dir / preset_name
    if preset_dir.exists():
        shutil.rmtree(preset_dir)
        st.success(f"Preset '{preset_name}' deleted successfully!")
    else:
        st.error(f"Preset '{preset_name}' does not exist!")


# Add a new preset
def add_preset(new_preset_name):
    new_preset_dir = assets_dir / new_preset_name
    if new_preset_dir.exists():
        st.error(f"Preset '{new_preset_name}' already exists!")
    else:
        # Create the preset directory structure
        (new_preset_dir / "logo").mkdir(parents=True, exist_ok=True)
        (new_preset_dir / "pattern").mkdir(parents=True, exist_ok=True)
        st.success(f"Preset '{new_preset_name}' created successfully!")
        return new_preset_name
    return None


# Rename a preset
def rename_preset(old_name, new_name):
    old_preset_dir = assets_dir / old_name
    new_preset_dir = assets_dir / new_name
    if new_preset_dir.exists():
        st.error(f"Preset '{new_name}' already exists! Choose a different name.")
        return True
    else:
        old_preset_dir.rename(new_preset_dir)
        st.success(f"Preset renamed from '{old_name}' to '{new_name}' successfully!")
        return False


def admin_page():
    st.sidebar.title("Preset Manager")
    asset_list = get_asset_list()
    # Add a new preset
    st.sidebar.subheader("Add New Preset")
    new_preset_name = st.sidebar.text_input("New Preset Name")
    if st.sidebar.button("Add Preset"):
        if new_preset_name:
            created_preset = add_preset(new_preset_name)
            if created_preset:
                asset_list = get_asset_list()  # Refresh the preset list

    # Select a preset from the list
    if asset_list:
        st.sidebar.subheader("Modify Preset")
        selected_preset = st.sidebar.selectbox("Choose a preset", asset_list)
        preset_dir = assets_dir / selected_preset

        # new_name = st.text_input("Preset Name", value=selected_preset, key="rename")
        # if st.button("Rename Preset"):
        #     if new_name and new_name != selected_preset:
        #         if rename_preset(selected_preset, new_name):
        #             selected_preset = new_name

        # Show existing logo and pattern
        st.subheader(f"Preset: {selected_preset}")
        logo_path = preset_dir / "logo/logo.png"
        pattern_path = preset_dir / "pattern/pattern.png"

        if logo_path.exists():
            st.image(str(logo_path), caption="Logo", use_column_width=True)
            with open(logo_path, "rb") as file:
                st.download_button(
                    label="Download Logo",
                    data=file,
                    file_name="logo.png",
                    mime="image/png"
                )

        if pattern_path.exists():
            st.image(str(pattern_path), caption="Pattern", use_column_width=True)
            with open(pattern_path, "rb") as file:
                st.download_button(
                    label="Download Pattern",
                    data=file,
                    file_name="pattern.png",
                    mime="image/png"
                )

        # Upload new files to modify preset
        st.subheader("Modify Preset")
        upload_file(preset_dir, "logo")
        upload_file(preset_dir, "pattern")

        # Delete preset with confirmation
        st.subheader("Delete Preset")
        if st.button(f"Delete {selected_preset}"):
            st.warning(f"Do you really want to delete {selected_preset} and all its data?")
            if st.button(f"Yes delete {selected_preset} and all its data."):
                st.warning("OK deleted")
                st.write("Preset deleted")
                # delete_preset(selected_preset)
    else:
        st.write("No presets available. Add a new preset from the sidebar.")
