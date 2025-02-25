import streamlit as st
from quest.make_quest import load_data, select_two_groups, build_prompt, generate_poll_title, generate_poll_options
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

def pil_to_base64(img):
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

def select_sns_type(sns_link):
    if "x.com" in sns_link:
        return "X"
    elif "twitter" in sns_link:
        return "X"
    elif "instagram" in sns_link:
        return "Instagram"
    elif "facebook" in sns_link:
        return "Facebook"
    elif "youtube" in sns_link:
        return "Youtube"
    else:
        return "SNS"

def main():
    st.title("Starglow Poll Maker")

    # Initialize session state variables if not already present.
    if "groups_selected" not in st.session_state:
        st.session_state.groups_selected = False
    if "groups" not in st.session_state:
        st.session_state.groups = None
    if "confirmed" not in st.session_state:
        st.session_state.confirmed = False
    if "prompted" not in st.session_state:
        st.session_state.prompted = False
    if "prompt" not in st.session_state:
        st.session_state.prompt = None
    if "poll_title" not in st.session_state:
        st.session_state.poll_title = None
    if "poll_options" not in st.session_state:
        st.session_state.poll_options = None
    if "image_url" not in st.session_state:
        st.session_state.image_url = None

    # Step 1: User selects two groups.
    if st.button("Select Two Groups"):
        st.session_state.confirmed = False
        data = load_data("groups_data_updated.csv")
        group_A, group_B = select_two_groups(data)
        st.session_state.groups = (group_A, group_B)
        st.session_state.groups_selected = True

    # 그룹이 선택된 경우 항상 그룹 정보를 표시
    if st.session_state.groups_selected:
        group_A, group_B = st.session_state.groups
        st.subheader("Selected Groups")
        col1, col2 = st.columns(2)

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

        # Step 2: Confirmation 버튼은 그룹 선택 후 항상 표시되도록 분리
        if not st.session_state.confirmed:
            if st.button("Confirm"):
                st.session_state.confirmed = True

    # Step 3: Build prompt.
    if st.session_state.confirmed:
        group_A, group_B = st.session_state.groups        
        if st.button("Build Prompt"):
            prompt = build_prompt(group_A, group_B)
            st.session_state.prompt = prompt
            st.subheader("Prompt")
            st.write(prompt)
            st.session_state.prompted = True

    # Step 4: Ask to GPT.
    if st.session_state.prompted:
        if st.button("Ask to GPT"):
            prompt = st.session_state.prompt
            st.subheader("Prompt")
            st.write(st.session_state.prompt)
            st.write("Prompt sent to GPT-3 for completion.")
            poll_title = generate_poll_title(prompt)
            poll_options = generate_poll_options(group_A, group_B)
            st.session_state.poll_title = poll_title
            st.session_state.poll_options = poll_options

            st.subheader("Generated Poll")
            st.subheader("**Title:**")
            st.subheader(poll_title)
            
            st.write("**Options:**", poll_options)

            col1, col2 = st.columns(2)

            # Further steps: creating blended image, uploading, SNS links, etc.
            image_path = make_image(group_A["image"], group_B["image"])
            image_url = upload_image(image_path, "blended_image.png")
            st.session_state.image_url = image_url
            sns_A = link_picker(group_A)
            st.session_state.sns_A = sns_A
            sns_B = link_picker(group_B)
            st.session_state.sns_B = sns_B

            response_Blend = requests.get(image_url)
            if response_B.status_code == 200:
                img_Blend = Image.open(BytesIO(response_Blend.content))
            st.image(img_Blend, width=500)
            st.write(image_url)
            
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**SNS Link for {poll_options[0]}:**", sns_A)
            with col2:
                st.write(f"**SNS Link for {poll_options[1]}:**", sns_B)

    # Step 5: Append Data Modify
    if st.session_state.poll_title and st.session_state.poll_options and st.session_state.image_url:
        st.subheader("Append Data Modify")
        
        if st.button("Find Latest Row"):
            latest_row = find_latest_poll_id()
            st.session_state.latest_row = latest_row

        # latest_row가 존재하면, 해당 값을 기본값으로 사용
        default_poll_id = st.session_state.latest_row.get("poll_id", "") if "latest_row" in st.session_state else ""
        default_start = st.session_state.latest_row.get("start", "") if "latest_row" in st.session_state else ""
        default_end = st.session_state.latest_row.get("end", "") if "latest_row" in st.session_state else ""


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
                        "URL or Condition": f"{sns_B}",
                        "Reward": "Point",
                        "Amount": "800"
                    }
                ]

    if "new_poll_data" in st.session_state:

        st.subheader("Quest Entries")
        # Quest 항목들을 폼 외부에서 출력하여 수정할 수 있도록 함 (추가/제거 버튼 포함)
        for idx, quest in enumerate(st.session_state.quest_entries):
            with st.expander(f"Quest {idx+1}", expanded=True):
                # 각 필드 입력
                quest["Date"] = st.text_input("Date", value=quest.get("Date", ""), key=f"date_{idx}")
                quest["no"] = st.text_input("No", value=quest.get("no", ""), key=f"no_{idx}")
                quest["Quest Type"] = st.text_input("Quest Type", value=quest.get("Quest Type", ""), key=f"quest_type_{idx}")
                quest["Tags"] = st.text_input("Tags", value=quest.get("Tags", ""), key=f"tags_{idx}")
                quest["Quest Title"] = st.text_input("Quest Title", value=quest.get("Quest Title", ""), key=f"quest_title_{idx}")
                quest["Description"] = st.text_area("Description", value=quest.get("Description", ""), key=f"description_{idx}")
                quest["URL or Condition"] = st.text_input("URL or Condition", value=quest.get("URL or Condition", ""), key=f"url_{idx}")
                quest["Reward"] = st.text_input("Reward", value=quest.get("Reward", ""), key=f"reward_{idx}")
                quest["Amount"] = st.text_input("Amount", value=quest.get("Amount", ""), key=f"amount_{idx}")
                # 개별 항목 제거 버튼 (폼 외부에서 처리)
                if st.button(f"Remove Quest {idx+1}", key=f"remove_{idx}"):
                    st.session_state.quest_entries.pop(idx)
                    st.experimental_rerun()

        # 항목 추가 버튼 (폼 외부에서 처리)
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

        # 이제, Quest 항목들의 입력 필드를 값은 세션 스테이트에 업데이트되어 있으므로, 제출만 처리하는 폼 사용
        with st.form("append_quest_form"):
            submitted = st.form_submit_button("Submit Quests")
            if submitted:
                quests_data = st.session_state.quest_entries
                appended_rows = append_new_quests(quests_data)
                st.success(f"Quests appended at rows: {appended_rows}")


if __name__ == "__main__":
    main()
