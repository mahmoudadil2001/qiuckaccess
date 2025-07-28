import streamlit as st
import requests
import time
import subprocess

token = st.secrets["GITHUB_TOKEN"]
headers = {"Authorization": f"token {token}"} if token else {}

def get_user_repos(username):
    url = f"https://api.github.com/users/{username}/repos?_={int(time.time())}"
    r = requests.get(url, headers=headers)
    return r.json() if r.status_code == 200 else []

def get_github_contents(owner, repo, path=""):
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}?_={int(time.time())}"
    r = requests.get(url, headers=headers)
    return r.json() if r.status_code == 200 else None

def get_file_content(download_url):
    r = requests.get(f"{download_url}?_={int(time.time())}", headers=headers)
    return r.text if r.status_code == 200 else "⚠️ خطأ في جلب المحتوى"

def copy_button(text, key, label):
    escaped = (
        text.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$")
        .replace("\n", "\\n").replace('"', '\\"').replace("'", "\\'")
    )
    js = f"""
    <script>
    function copy_{key}(){{
        navigator.clipboard.writeText("{escaped}").then(() => {{
            var msg = document.getElementById("msg_{key}");
            msg.style.display = "block";
            setTimeout(() => {{
                msg.style.display = "none";
            }}, 1500);
        }}).catch(err => {{
            alert("حدث خطأ أثناء النسخ: " + err);
        }});
    }}
    </script>
    <button onclick="copy_{key}()" style="
        background:#2196F3;color:white;padding:6px 12px;
        border:none;border-radius:5px;cursor:pointer;margin-top:10px;
    ">📋 {label}</button>
    <div id="msg_{key}" style="display:none;color:green;font-weight:bold;margin-top:5px;">✅ تم النسخ</div>
    """
    st.components.v1.html(js, height=70)

def update_repo():
    try:
        subprocess.run(["git", "fetch"], check=True)
        subprocess.run(["git", "reset", "--hard", "origin/main"], check=True)
        st.success("✅ تم تحديث المشروع من GitHub بنجاح")
        st.rerun()
    except Exception as e:
        st.error(f"⚠️ حدث خطأ أثناء تحديث المشروع: {e}")

def main():
    st.title("📂 مستعرض ملفات GitHub")

    if st.button("🔄 تحديث المشروع من GitHub"):
        update_repo()

    username = "mahmoudadil2001"
    repos = get_user_repos(username)

    if repos:
        repo_names = [r["name"] for r in repos]
        repo_choice = st.selectbox("اختر المستودع", repo_names)

        if repo_choice:
            contents = get_github_contents(username, repo_choice)
            if contents:
                files = [c for c in contents if c["type"] == "file"]
                folders = [c for c in contents if c["type"] == "dir"]

                st.write("### اختر الملفات:")
                if "selected_files" not in st.session_state:
                    st.session_state.selected_files = set()

                selected_files_local = set()

                for file in files:
                    checked = file["path"] in st.session_state.selected_files
                    new_val = st.checkbox(file["name"], value=checked, key=file["path"])
                    if new_val:
                        selected_files_local.add(file["path"])
                    else:
                        selected_files_local.discard(file["path"])

                if "show_folders" not in st.session_state:
                    st.session_state.show_folders = False

                if st.button("📁 Show Folders"):
                    st.session_state.show_folders = not st.session_state.show_folders

                if st.session_state.show_folders:
                    for folder in folders:
                        with st.expander(folder["name"]):
                            folder_contents = get_github_contents(username, repo_choice, folder["path"])
                            if folder_contents:
                                for f in folder_contents:
                                    if f["type"] == "file":
                                        checked = f["path"] in st.session_state.selected_files
                                        new_val = st.checkbox(f"{folder['name']}/{f['name']}", value=checked, key=f["path"])
                                        if new_val:
                                            selected_files_local.add(f["path"])
                                        else:
                                            selected_files_local.discard(f["path"])

                st.session_state.selected_files = selected_files_local

                if "show_selected_files_content" not in st.session_state:
                    st.session_state.show_selected_files_content = False

                if st.button("📜 إظهار/إخفاء محتويات الملفات المحددة"):
                    st.session_state.show_selected_files_content = not st.session_state.show_selected_files_content

                if st.session_state.show_selected_files_content:
                    if not st.session_state.selected_files:
                        st.warning("⚠️ حدد ملف واحد أو أكثر أولاً!")
                    else:
                        combined_text = ""
                        for fpath in st.session_state.selected_files:
                            file_data = next((f for f in files if f["path"] == fpath), None)
                            if not file_data:
                                for folder in folders:
                                    folder_contents = get_github_contents(username, repo_choice, folder["path"])
                                    if folder_contents:
                                        for ff in folder_contents:
                                            if ff["path"] == fpath:
                                                file_data = ff
                                                file_data["folder_name"] = folder["name"]
                                                break
                            if file_data:
                                content = get_file_content(file_data["download_url"])
                                prefix = f"{file_data.get('folder_name', '')}/" if "folder_name" in file_data else ""
                                combined_text += f"===== {prefix}{file_data['name']} =====\n{content}\n\n"

                        st.text_area("📄 محتويات الملفات المحددة", combined_text, height=300)
                        copy_button(combined_text, key="combined", label="نسخ كل المحتويات")

if __name__ == "__main__":
    main()
