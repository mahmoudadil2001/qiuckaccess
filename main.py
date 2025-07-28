import streamlit as st
import requests

token = st.secrets["GITHUB_TOKEN"]
headers = {"Authorization": f"token {token}"} if token else {}


def get_user_repos(username):
    url = f"https://api.github.com/users/{username}/repos"
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        return r.json()
    else:
        st.error(f"خطأ في جلب المستودعات: {r.status_code}")
        return []


def get_github_contents(owner, repo, path=""):
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        return r.json()
    else:
        st.error(f"خطأ في جلب محتويات المستودع: {r.status_code}")
        return None


def get_file_content(download_url):
    r = requests.get(download_url, headers=headers)
    if r.status_code == 200:
        return r.text
    else:
        return "⚠️ خطأ في جلب المحتوى"


def copy_button(text, key, label):
    escaped = (
        text.replace("\\", "\\\\")
        .replace("`", "\\`")
        .replace("$", "\\$")
        .replace("\n", "\\n")
        .replace('"', '\\"')
        .replace("'", "\\'")
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
        background:#2196F3;
        color:white;
        padding:6px 12px;
        border:none;
        border-radius:5px;
        cursor:pointer;
        margin-top:10px;
    ">
        📋 {label}
    </button>
    <div id="msg_{key}" style="display:none;color:green;font-weight:bold;margin-top:5px;">✅ تم النسخ</div>
    """
    st.components.v1.html(js, height=70)


def main():
    st.title("مستعرض ملفات GitHub مع اختيار ونسخ")

    if "show_intro" not in st.session_state:
        st.session_state.show_intro = False

    if st.button("شرح وتعريف"):
        st.session_state.show_intro = not st.session_state.show_intro

    if st.session_state.show_intro:
        intro_text = """مرحبا جات جي بي تي كيف حالك
عندي مشروع معظمه بايثون يعتمد على ستريم لت
سارسل محتوى ملفات المشروع اسم المشروع ومحتواه 
من اطلبه منك ببساطة تنتضر ان ارسل لك المحتويات كاملة ثم تنتضر مني  طلباتي
ما اريده منك بعد تاكيد الطلبات او التغييرات ان تقول لي اسم الملف الذي يجب تغييره وان ترسله كاملا معدلا 
ان كان اكثر من ملف يتيغر عادي ارسله واحد ورا التالي
ان كان هناك ملف اضافي قل اسمه وارسله كاملا
ان كانت هناك اضافة مكتبة او ماشابه نبهني عليها
"""
        st.text_area("المحتوى قابل للنسخ", intro_text, height=200)
        copy_button(intro_text, key="intro_copy", label="نسخ نص التعريف")

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

                if st.button("Show Folders"):
                    st.session_state.show_folders = not st.session_state.show_folders

                if st.session_state.show_folders:
                    st.write("### الفولدرات:")

                    for folder in folders:
                        with st.expander(folder["name"]):
                            folder_contents = get_github_contents(username, repo_choice, folder["path"])
                            if folder_contents:
                                folder_files = [f for f in folder_contents if f["type"] == "file"]
                                for f in folder_files:
                                    checked = f["path"] in st.session_state.selected_files
                                    new_val = st.checkbox(f"{folder['name']}/{f['name']}", value=checked, key=f["path"])
                                    if new_val:
                                        selected_files_local.add(f["path"])
                                    else:
                                        selected_files_local.discard(f["path"])

                st.session_state.selected_files = selected_files_local

                if "show_selected_files_content" not in st.session_state:
                    st.session_state.show_selected_files_content = False

                if st.button("إظهار/إخفاء محتويات الملفات المحددة"):
                    st.session_state.show_selected_files_content = not st.session_state.show_selected_files_content

                if st.session_state.show_selected_files_content:
                    if not st.session_state.selected_files:
                        st.warning("حدد ملف واحد أو أكثر أولاً!")
                    else:
                        combined_text = ""
                        for fpath in st.session_state.selected_files:
                            file_data = None
                            for f in files:
                                if f["path"] == fpath:
                                    file_data = f
                                    break
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

                        st.text_area("محتويات الملفات المحددة", combined_text, height=300)
                        copy_button(combined_text, key="combined", label="نسخ كل المحتويات")


if __name__ == "__main__":
    main()
