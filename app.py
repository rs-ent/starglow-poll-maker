import streamlit as st
from quest.make_quest import load_data, select_two_groups, reselect_group, build_prompt, generate_poll_title, generate_poll_options
from image.combine import make_image
from image.upload import upload_image
from sns.link import link_picker
from sheets.append_poll import append_new_poll
from sheets.finder import find_latest_poll_id
from sheets.append_quest import append_new_quests
import requests
from PIL import Image
from io import BytesIO
import base64

# 이미지 PIL 객체를 base64 문자열로 변환
def pil_to_base64(img):
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

# SNS 링크에 따른 타입 결정
def select_sns_type(sns_link):
    if "x.com" in sns_link or "twitter" in sns_link:
        return "X"
    elif "instagram" in sns_link:
        return "Instagram"
    elif "facebook" in sns_link:
        return "Facebook"
    elif "youtube" in sns_link:
        return "Youtube"
    else:
        return "SNS"

# 초기 세션 상태 설정
def initialize_session_state():
    keys_defaults = {
        "groups_selected": False,
        "groups": None,
        "confirmed": False,
        "prompted": False,
        "prompt": None,
        "poll_title": None,
        "poll_options": None,
        "image_url": None,
        "manual_input": False,
        "data": None,
        "sns_A": None,
        "sns_B": None,
        "quest_entries": None,
        "new_poll_data": None,
        "latest_row": {}
    }
    for key, default in keys_defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default

# 사이드바에 진행 단계와 전체 리셋 버튼 표시 (편의성 강화)
def display_sidebar():
    st.sidebar.title("진행 단계")
    steps = [
        ("그룹 선택", st.session_state.groups_selected),
        ("그룹 확인 및 확정", st.session_state.confirmed),
        ("프롬프트 생성", st.session_state.prompted),
        ("자동/수동 입력 완료", st.session_state.poll_title is not None and st.session_state.poll_options is not None and st.session_state.image_url is not None),
        ("데이터 추가 완료", st.session_state.new_poll_data is not None),
        ("Quest 항목 생성", st.session_state.quest_entries is not None)
    ]
    for step, completed in steps:
        if completed:
            st.sidebar.success(step)
        else:
            st.sidebar.info(step)
    if st.sidebar.button("전체 리셋"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.experimental_rerun()

# Step 1: 그룹 선택
def group_selection():
    if st.button("Select Two Groups"):
        st.session_state.confirmed = False
        data = load_data("groups_data_updated.csv")
        st.session_state.data = data
        group_A, group_B = select_two_groups(data)
        st.session_state.groups = (group_A, group_B)
        st.session_state.groups_selected = True

# Step 2: 선택된 그룹 표시 및 변경
def display_groups():
    if st.session_state.groups_selected and st.session_state.groups:
        group_A, group_B = st.session_state.groups
        st.subheader("Selected Groups")
        col1, col2 = st.columns(2)
        data = st.session_state.data

        with col1:
            response_A = requests.get(group_A["image"].split("/scale-to-width-down")[0])
            if response_A.status_code == 200:
                img_A = Image.open(BytesIO(response_A.content))
                img_A_base64 = pil_to_base64(img_A)
                container_html_A = f"""
                    <div style="width:350px; height:350px; overflow:hidden;">
                        <img src="data:image/png;base64,{img_A_base64}" style="width:100%; height:100%; object-fit:cover;">
                    </div>
                    """
                st.markdown(container_html_A, unsafe_allow_html=True)
            else:
                st.write("Failed to load image for Group A.")
            st.write("**Group A:**", {k: str(v) for k, v in group_A.items()})
            if st.button("Change Group A"):
                fixed_group = st.session_state.groups[1]
                new_group_A = reselect_group(data, fixed_group)
                st.session_state.groups = (new_group_A, fixed_group)

        with col2:
            response_B = requests.get(group_B["image"].split("/scale-to-width-down")[0])
            if response_B.status_code == 200:
                img_B = Image.open(BytesIO(response_B.content))
                img_B_base64 = pil_to_base64(img_B)
                container_html_B = f"""
                    <div style="width:350px; height:350px; overflow:hidden;">
                        <img src="data:image/png;base64,{img_B_base64}" style="width:100%; height:100%; object-fit:cover;">
                    </div>
                    """
                st.markdown(container_html_B, unsafe_allow_html=True)
            else:
                st.write("Failed to load image for Group B.")
            st.write("**Group B:**", {k: str(v) for k, v in group_B.items()})
            if st.button("Change Group B"):
                fixed_group = st.session_state.groups[0]
                new_group_B = reselect_group(data, fixed_group)
                st.session_state.groups = (fixed_group, new_group_B)

        # 그룹 선택 후 확정 버튼
        if not st.session_state.confirmed and st.button("Confirm"):
            st.session_state.confirmed = True

# Step 3: 프롬프트 생성
def build_prompt_step():
    if st.session_state.confirmed:
        group_A, group_B = st.session_state.groups
        if st.button("Build Prompt"):
            prompt = build_prompt(group_A, group_B)
            st.session_state.prompt = prompt
            st.subheader("Prompt")
            st.write(prompt)
            st.session_state.prompted = True

# Step 4: GPT 요청 및 자동 입력 처리
def ask_to_gpt_step():
    if st.session_state.prompted:
        group_A, group_B = st.session_state.groups
        if st.button("Ask to GPT"):
            prompt = st.session_state.prompt
            st.subheader("Prompt")
            st.write(prompt)
            st.write("Prompt sent to GPT-3 for completion.")
            poll_title = generate_poll_title(prompt)
            poll_options = generate_poll_options(group_A, group_B)
            st.session_state.poll_title = poll_title
            st.session_state.poll_options = poll_options

            st.subheader("Generated Poll")
            st.subheader("**Title:**")
            st.write(poll_title)
            st.write("**Options:**", poll_options)

            # 이미지 생성 및 SNS 링크 처리
            image_path = make_image(group_A["image"], group_B["image"])
            image_url = upload_image(image_path, "blended_image.png")
            st.session_state.image_url = image_url
            sns_A = link_picker(group_A)
            sns_B = link_picker(group_B)
            st.session_state.sns_A = sns_A
            st.session_state.sns_B = sns_B

            response_blend = requests.get(image_url)
            if response_blend.status_code == 200:
                img_blend = Image.open(BytesIO(response_blend.content))
                st.image(img_blend, width=500)
            st.write(image_url)

            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**SNS Link for {poll_options[0]}:**", sns_A)
            with col2:
                st.write(f"**SNS Link for {poll_options[1]}:**", sns_B)

# Step 5: 수동 입력 처리 (Skip 버튼 선택 시 manual_input 플래그를 사용)
def manual_input_step():
    group_A, group_B = st.session_state.groups if st.session_state.groups else (None, None)
    if st.button("Skip and Manually Input"):
        st.session_state.manual_input = True

    if st.session_state.manual_input:
        st.subheader("Prompt")
        st.write(st.session_state.prompt)
        with st.form("manual_poll_form"):
            poll_title_input = st.text_input("Poll Title", value=st.session_state.poll_title or "")
            poll_options = generate_poll_options(group_A, group_B)  # 옵션은 자동 생성
            poll_title_submitted = st.form_submit_button("Submit Poll Title")
            if poll_title_submitted:
                st.session_state.poll_title = poll_title_input
                st.session_state.poll_options = poll_options
                st.success("Poll Title and Options saved")
                st.subheader("Generated Poll")
                st.subheader("**Title:**")
                st.write(poll_title_input)
                st.write("**Options:**", poll_options)

                # 이미지 생성 및 SNS 링크 처리
                image_path = make_image(group_A["image"], group_B["image"])
                image_url = upload_image(image_path, "blended_image.png")
                st.session_state.image_url = image_url
                sns_A = link_picker(group_A)
                sns_B = link_picker(group_B)
                st.session_state.sns_A = sns_A
                st.session_state.sns_B = sns_B

                response_blend = requests.get(image_url)
                if response_blend.status_code == 200:
                    img_blend = Image.open(BytesIO(response_blend.content))
                    st.image(img_blend, width=500)
                st.write(image_url)
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**SNS Link for {poll_options[0]}:**", sns_A)
                with col2:
                    st.write(f"**SNS Link for {poll_options[1]}:**", sns_B)
            else:
                st.error("Please input Poll Title")

# Step 6: 데이터 추가 및 수정 (구글 시트 업데이트)
def append_data_modify_step():
    if st.session_state.poll_title and st.session_state.poll_options and st.session_state.image_url:
        st.subheader("Append Data Modify")
        if st.button("Find Latest Row"):
            latest_row = find_latest_poll_id()
            st.session_state.latest_row = latest_row

        default_poll_id = st.session_state.latest_row.get("poll_id", "")
        default_start = st.session_state.latest_row.get("start", "")
        default_end = st.session_state.latest_row.get("end", "")

        with st.form("append_data_form"):
            artist_A = st.session_state.poll_options[0]
            artist_B = st.session_state.poll_options[1]
            poll_id = st.text_input("Poll ID", value=default_poll_id)
            title = st.text_input("Title", value=st.session_state.poll_title.replace('"', ''))
            title_shorten = st.text_input("Title Shorten", value="")
            options_str = st.text_input("Options", value=";".join(st.session_state.poll_options))
            options_shorten = st.text_input("Options Shorten", value="")
            img = st.text_input("Image URL", value=st.session_state.image_url)
            song_title_for_A = st.text_input(f"Song Title for {artist_A}", value="")
            song_img_for_A = st.text_input(f"Song Image for {artist_A}", value="")
            song_link_for_A = st.text_input(f"Song Link for {artist_A}", value="")
            song_title_for_B = st.text_input(f"Song Title for {artist_B}", value="")
            song_img_for_B = st.text_input(f"Song Image for {artist_B}", value="")
            song_link_for_B = st.text_input(f"Song Link for {artist_B}", value="")
            start = st.text_input("Start", value=default_start)
            end = st.text_input("End", value=default_end)
            announce_today = st.text_input("Announce Today", value="")
            announce_result = st.text_input("Announce Result", value="")
            show_scheduled = st.text_input("Show Scheduled", value="")
            song_announce_img = st.text_input("Song Announce Image", value="")
            poll_announce_img = st.text_input("Poll Announce Image", value="")
            result_img = st.text_input("Result Image", value="")
            reopen = st.text_input("Reopen", value="")
            group_a_str = st.text_input("Group A", value="")
            group_b_str = st.text_input("Group B", value="")
            memo = st.text_area("Memo", value="")

            submitted = st.form_submit_button("Append Data Modify")
            if submitted:
                song_title = f"{st.session_state.poll_options[0]} - {song_title_for_A};{st.session_state.poll_options[1]} - {song_title_for_B}"
                song_img = f"{song_img_for_A};{song_img_for_B}"
                new_poll_data = {
                    "poll_id": poll_id,
                    "title": title,
                    "title_shorten": title_shorten,
                    "options": options_str.split(";"),
                    "options_shorten": options_shorten.split(";"),
                    "img": img,
                    "song_title": song_title,
                    "song_img": song_img,
                    "start": start,
                    "end": end,
                    "announce_today": announce_today,
                    "announce_result": announce_result,
                    "show_scheduled": show_scheduled,
                    "song_announce_img": song_announce_img,
                    "poll_announce_img": poll_announce_img,
                    "result_img": result_img,
                    "reopen": reopen,
                    "group_a": group_a_str,
                    "group_b": group_b_str,
                    "memo": memo
                }
                appended_row = append_new_poll(new_poll_data)
                st.write(f"Data appended to row {appended_row}.")
                st.session_state.new_poll_data = new_poll_data

                # Quest 항목 준비
                poll_number = poll_id.replace("p", "")
                date_start = start.split()[0] if start else ""
                song_titles = [s.strip() for s in song_title.split(";")]
                first_song_title = song_titles[0] if len(song_titles) > 0 else ""
                second_song_title = song_titles[1] if len(song_titles) > 1 else ""

                sns_A = st.session_state.sns_A
                sns_B = st.session_state.sns_B
                sns_A_type = select_sns_type(sns_A)
                sns_B_type = select_sns_type(sns_B)

                st.session_state.quest_entries = [
                    {
                        "Date": date_start,
                        "no": "",
                        "Quest Type": "Youtube",
                        "Tags": "",
                        "Quest Title": first_song_title,
                        "Description": "곡 정보",
                        "URL or Condition": song_link_for_A,
                        "Reward": "",
                        "Amount": ""
                    },
                    {
                        "Date": "",
                        "no": "",
                        "Quest Type": "Youtube",
                        "Tags": "",
                        "Quest Title": second_song_title,
                        "Description": "곡 정보",
                        "URL or Condition": song_link_for_B,
                        "Reward": "",
                        "Amount": ""
                    },
                    {
                        "Date": "",
                        "no": "",
                        "Quest Type": "Website",
                        "Tags": "",
                        "Quest Title": f"[POLL#{poll_number}] {title}",
                        "Description": "폴 참여 링크",
                        "URL or Condition": f"https://starglow-protocol.vercel.app/polls/{poll_id}",
                        "Reward": "Point",
                        "Amount": "800"
                    },
                    {
                        "Date": "",
                        "no": "",
                        "Quest Type": sns_A_type,
                        "Tags": "",
                        "Quest Title": f"Follow {artist_A} on {sns_A_type}",
                        "Description": "아티스트 팔로우",
                        "URL or Condition": sns_A,
                        "Reward": "Point",
                        "Amount": "800"
                    },
                    {
                        "Date": "",
                        "no": "",
                        "Quest Type": sns_B_type,
                        "Tags": "",
                        "Quest Title": f"Follow {artist_B} on {sns_B_type}",
                        "Description": "아티스트 팔로우",
                        "URL or Condition": sns_B,
                        "Reward": "Point",
                        "Amount": "800"
                    }
                ]

# Step 7: Quest 항목 확인 및 수정
def quest_entries_section():
    if st.session_state.new_poll_data and st.session_state.quest_entries:
        st.subheader("Quest Entries")
        for idx, quest in enumerate(st.session_state.quest_entries):
            with st.expander(f"Quest {idx+1}", expanded=True):
                quest["Date"] = st.text_input("Date", value=quest.get("Date", ""), key=f"date_{idx}")
                quest["no"] = st.text_input("No", value=quest.get("no", ""), key=f"no_{idx}")
                quest["Quest Type"] = st.text_input("Quest Type", value=quest.get("Quest Type", ""), key=f"quest_type_{idx}")
                quest["Tags"] = st.text_input("Tags", value=quest.get("Tags", ""), key=f"tags_{idx}")
                quest["Quest Title"] = st.text_input("Quest Title", value=quest.get("Quest Title", ""), key=f"quest_title_{idx}")
                quest["Description"] = st.text_area("Description", value=quest.get("Description", ""), key=f"description_{idx}")
                quest["URL or Condition"] = st.text_input("URL or Condition", value=quest.get("URL or Condition", ""), key=f"url_{idx}")
                quest["Reward"] = st.text_input("Reward", value=quest.get("Reward", ""), key=f"reward_{idx}")
                quest["Amount"] = st.text_input("Amount", value=quest.get("Amount", ""), key=f"amount_{idx}")
                if st.button(f"Remove Quest {idx+1}", key=f"remove_{idx}"):
                    st.session_state.quest_entries.pop(idx)
                    st.experimental_rerun()
        if st.button("Add Quest"):
            st.session_state.quest_entries.append({
                "Date": "",
                "no": "",
                "Quest Type": "",
                "Tags": "",
                "Quest Title": "",
                "Description": "",
                "URL or Condition": "",
                "Reward": "",
                "Amount": ""
            })
            st.experimental_rerun()
        with st.form("append_quest_form"):
            submitted = st.form_submit_button("Submit Quests")
            if submitted:
                quests_data = st.session_state.quest_entries
                appended_rows = append_new_quests(quests_data)
                st.success(f"Quests appended at rows: {appended_rows}")

# 메인 함수: 각 단계별 함수들을 순차적으로 호출
def main():
    st.title("Starglow Poll Maker")
    initialize_session_state()
    display_sidebar()  # 사이드바에 진행 단계 표시 및 리셋 버튼

    group_selection()
    display_groups()
    build_prompt_step()
    ask_to_gpt_step()
    manual_input_step()
    append_data_modify_step()
    quest_entries_section()

if __name__ == "__main__":
    main()
