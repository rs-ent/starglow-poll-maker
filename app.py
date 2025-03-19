##### app.py #####

import streamlit as st
from crawler.make_csv import get_groups, get_youtube
from quest.make_quest import load_data, select_two_groups_random, count_groups_with_min_subscribers, select_groups_with_min_subscribers, search_groups, select_groups_by_search, reselect_group, build_prompt, generate_poll_title, generate_poll_options
from image.combine import make_image
from image.upload import upload_image
from sns.link import link_picker
from sns.youtube import get_playlist, get_random_track_from_playlist
from sheets.append_poll import append_new_poll
from sheets.finder import find_latest_poll_id
from sheets.append_quest import append_new_quests
import requests
from PIL import Image
from io import BytesIO
import base64
import sys
import time
import altair as alt
import pandas as pd
import datetime
import glob
import re

log_placeholder = st.sidebar.empty()

class StreamlitLogger:
    def __init__(self):
        self.log_buffer = ""
        
    def write(self, message):
        # message가 공백이 아닌 경우에만 추가
        if message.strip():
            self.log_buffer += message + "\n"
            log_placeholder.markdown(f"""
            <div style="height:200px; overflow-y: scroll; border:1px solid #ccc; padding: 10px;">
                <pre style="margin: 0;">{self.log_buffer}</pre>
            </div>
            """, unsafe_allow_html=True)
    
    def flush(self):
        pass

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
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("로그")
    
    # 버퍼 초기화 버튼
    if st.sidebar.button("버퍼 초기화"):
        sys.stdout.log_buffer = ""
        log_placeholder.empty()
        print("로그 버퍼가 초기화되었습니다.")

def group_listup():
    st.subheader("Step 0: 그룹 데이터 업데이트")
    
    if st.button("그룹 데이터 업데이트 실행"):
        date = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        groups_file_name = f"groups_data_{date}.csv"
        
        with st.spinner("그룹 리스트 초기화 중 (groups_data.csv 업데이트)..."):
            get_groups(output_file=groups_file_name)
        st.success("그룹 리스트 초기화 완료.")
        
        groups_data_df = pd.read_csv(groups_file_name)
        groups_data_csv = groups_data_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="그룹 리스트",
            data=groups_data_csv,
            file_name=groups_file_name,
            mime="text/csv"
        )

    st.divider()
    csv_files = glob.glob("groups_data*.csv")
    if csv_files:
        selected_input_file = st.selectbox("입력 파일 선택", sorted(csv_files, reverse=True))
        st.session_state.selected_input_file = selected_input_file
        

    if st.button("그룹 데이터 유튜브 구독자 업데이트 실행"):
        input_file = st.session_state.selected_input_file
        with st.spinner("유튜브 구독자 정보 업데이트 중 (groups_data_updated.csv 업데이트)..."):
            updated_date = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            updated_file_name = f"groups_data_updated_{updated_date}.csv"
            get_youtube(input_file=input_file, output_file=updated_file_name)
        st.success("유튜브 구독자 정보 업데이트 완료.")
        groups_data_updated_df = pd.read_csv(updated_file_name)
        groups_data_updated_csv = groups_data_updated_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="그룹 리스트",
            data=groups_data_updated_csv,
            file_name=updated_file_name,
            mime="text/csv"
        )
        
        st.success("Step 0 완료.")

def group_selection():
    st.subheader("Step 1: 그룹 선택 방법")
    csv_files = glob.glob("groups_data_updated*.csv")
    if csv_files:
        selected_data = st.selectbox("Data 선택", sorted(csv_files, reverse=True))
        data = load_data(selected_data)
        st.session_state.data = data

        st.divider()

        # 세션 상태 초기화 (기존 그룹 선택 변수 대신 개별 변수 사용)
        if 'group_A' not in st.session_state:
            st.session_state.group_A = None
        if 'group_B' not in st.session_state:
            st.session_state.group_B = None

        ####################################
        # 공통 선택 유틸리티 함수 정의
        ####################################
        def select_random_group(df, exclude_group=None):
            available = df.copy()
            if exclude_group is not None:
                available = available[available['group_name'] != exclude_group['group_name']]
            return available.sample(n=1).iloc[0]

        def select_by_min_sub(df, min_sub, exclude_group=None):
            available = df[df['youtube_subscribers'] >= min_sub]
            if exclude_group is not None:
                available = available[available['group_name'] != exclude_group['group_name']]
            if available.empty:
                return None
            return available.sample(n=1).iloc[0]

        def select_by_search(df, keyword, selected_name, exclude_group=None):
            available = df[df['group_name'].str.contains(keyword, case=False, na=False)]
            if exclude_group is not None:
                available = available[available['group_name'] != exclude_group['group_name']]
            if available.empty or selected_name not in available['group_name'].values:
                return None
            return available[available['group_name'] == selected_name].iloc[0]

        def select_by_playlist(df, tracks, exclude_group=None):
            available_data = df.copy()
            if exclude_group is not None:
                available_data = available_data[available_data['group_name'] != exclude_group['group_name']]

            matched_info = get_random_track_from_playlist(available_data, tracks)
            if matched_info is None:
                raise ValueError("일치하는 그룹을 찾을 수 없습니다.")
            
            return matched_info
        

        # 비슷한 그룹 선택 함수
        def select_similar_group(df, group, threshold=0.5):
            subscribers = group['youtube_subscribers']
            range_min = subscribers * (1 - threshold)
            range_max = subscribers * (1 + threshold)
            similar_df = df[
                (df['youtube_subscribers'] >= range_min) &
                (df['youtube_subscribers'] <= range_max) &
                (df['group_name'] != group['group_name'])
            ]
            if similar_df.empty:
                df_no_group = df[df['group_name'] != group['group_name']].copy()
                df_no_group['diff'] = (df_no_group['youtube_subscribers'] - subscribers).abs()
                similar_df = df_no_group.sort_values(by='diff').head(5)
            return similar_df.sample(n=1).iloc[0]
        
        threshold_val = st.slider("유사 그룹 선택 임계값 (0.0 ~ 1.0)", 0.0, 1.0, 0.5, step=0.05)
        min_sub = st.slider("최소 구독자 수", 0, int(data['youtube_subscribers'].max()), key="min_sub")
        playlist_id = st.text_input("유튜브 플레이리스트 ID", key="playlist_id", value="https://music.youtube.com/playlist?list=PL4fGSI1pDJn5S09aId3dUGp40ygUqmPGc")
        tracks = get_playlist(playlist_id)
        
        st.divider()

        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Group A 선택")
            # 1. 랜덤 선택 (Group A)
            
            if st.button("Group A - 랜덤 선택"):
                if(st.session_state.group_B is not None):
                    st.session_state.group_A = select_similar_group(data, st.session_state.group_B, threshold_val)
                else:
                    st.session_state.group_A = data.sample(n=1).iloc[0]
                st.success(f"Group A 선택됨: {st.session_state.group_A['group_name']}")

            # 2. 최소 구독자 조건 선택 (Group A)
            if st.button("Group A - 최소 구독자 조건 선택"):
                result = select_by_min_sub(data, min_sub)
                if result is not None:
                    st.session_state.group_A = result
                    st.success(f"Group A 선택됨: {st.session_state.group_A['group_name']}")
                else:
                    st.error("조건을 만족하는 그룹이 없습니다.")

            # 3. 그룹 이름 검색 선택 (Group A)
            keyword_A = st.text_input("Group A - 그룹 검색 키워드", key="keyword_A")
            if keyword_A:
                search_results_A = data[data['group_name'].str.contains(keyword_A, case=False, na=False)]
                if not search_results_A.empty:
                    selected_name_A = st.selectbox("검색 결과에서 Group A 선택", search_results_A['group_name'].tolist(), key="selected_name_A")
                    if st.button("Group A - 검색 선택"):
                        result = select_by_search(data, keyword_A, selected_name_A)
                        if result is not None:
                            st.session_state.group_A = result
                            st.success(f"Group A 선택됨: {st.session_state.group_A['group_name']}")
                        else:
                            st.error("검색 결과에서 선택할 수 없습니다.")
                else:
                    st.write("검색 결과가 없습니다.")

            # 4. 유튜브 플레이리스트 선택 (Group A)
            if st.button("Group A - 플레이리스트에서 선택"):
                st.session_state.group_A = select_by_playlist(data, tracks)
                st.success(f"Group A 선택됨: {st.session_state.group_A['group_name']}")

            if st.session_state.group_A is not None:        
                current_image_A = st.session_state.group_A["image"]
                response_A = requests.get(current_image_A.split("/scale-to-width-down")[0])
                if response_A.status_code == 200:
                    img_A = Image.open(BytesIO(response_A.content))
                    st.image(img_A, width=350)
                else:
                    st.error("Failed to load image for Group A.")

                new_image_A = st.text_input("Replace Group A Image", key="replace_image_A", value=current_image_A)
                if st.button("Replace Group A Image"):
                    st.session_state.group_A["image"] = new_image_A

                st.write(f"**Group A:** {st.session_state.group_A['group_name']}")
                st.write(f"**Subscribers:** {st.session_state.group_A['youtube_subscribers']:,}")

                if st.session_state.group_A is not None and st.session_state.group_B is not None:
                    st.session_state.groups_selected = True
            

        with col2:
            st.markdown("#### Group B 선택")
            # Group B 선택 시 Group A와 중복되지 않도록 available 데이터 필터링
            exclude = st.session_state.group_A

            # 1. 랜덤 선택 (Group B)
            if st.button("Group B - 랜덤 선택"):
                if(st.session_state.group_A is not None):
                    st.session_state.group_B = select_similar_group(data, st.session_state.group_A, threshold_val)
                else:
                    st.session_state.group_B = data.sample(n=1).iloc[0]
                st.success(f"Group B 선택됨: {st.session_state.group_B['group_name']}")

            # 2. 최소 구독자 조건 선택 (Group B)
            if st.button("Group B - 최소 구독자 조건 선택"):
                result = select_by_min_sub(data, min_sub, exclude_group=exclude)
                if result is not None:
                    st.session_state.group_B = result
                    st.success(f"Group B 선택됨: {st.session_state.group_B['group_name']}")
                else:
                    st.error("조건을 만족하는 그룹이 없습니다.")

            # 3. 그룹 이름 검색 선택 (Group B)
            keyword_B = st.text_input("Group B - 그룹 검색 키워드", key="keyword_B")
            if keyword_B:
                search_results_B = data[data['group_name'].str.contains(keyword_B, case=False, na=False)]
                if not search_results_B.empty:
                    selected_name_B = st.selectbox("검색 결과에서 Group B 선택", search_results_B['group_name'].tolist(), key="selected_name_B")
                    if st.button("Group B - 검색 선택"):
                        result = select_by_search(data, keyword_B, selected_name_B, exclude_group=exclude)
                        if result is not None:
                            st.session_state.group_B = result
                            st.success(f"Group B 선택됨: {st.session_state.group_B['group_name']}")
                        else:
                            st.error("검색 결과에서 선택할 수 없습니다.")
                else:
                    st.write("검색 결과가 없습니다.")

            # 4. 유튜브 플레이리스트 선택 (Group B)
            if st.button("Group B - 플레이리스트에서 선택"):
                st.session_state.group_B = select_by_playlist(data, tracks, exclude_group=exclude)
                st.success(f"Group B 선택됨: {st.session_state.group_B['group_name']}")

            if st.session_state.group_B is not None:
                current_image_B = st.session_state.group_B["image"]
                response_B = requests.get(current_image_B.split("/scale-to-width-down")[0])
                if response_B.status_code == 200:
                    img_B = Image.open(BytesIO(response_B.content))
                    st.image(img_B, width=350)
                else:
                    st.error("Failed to load image for Group B.")
                
                new_image_B = st.text_input("Replace Group B Image", key="replace_image_B", value=current_image_B)
                if st.button("Replace Group B Image"):
                    st.session_state.group_B["image"] = new_image_B
                    

                st.write(f"**Group B:** {st.session_state.group_B['group_name']}")
                st.write(f"**Subscribers:** {st.session_state.group_B['youtube_subscribers']:,}")
            
                if st.session_state.group_A is not None and st.session_state.group_B is not None:
                    st.session_state.groups_selected = True

def display_groups():
    if st.session_state.groups_selected:
        
        if not st.session_state.confirmed and st.button("Confirm Selection"):
            st.session_state.confirmed = True
            st.session_state.groups = (st.session_state.group_A, st.session_state.group_B)
            st.success("Groups confirmed!")


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

        group_A = st.session_state.groups[0]
        group_B = st.session_state.groups[1]

        def parse_youtube_id(url):
            pattern = r'(?:v=|\/)([0-9A-Za-z_-]{11})'
            match = re.search(pattern, url)
            return match.group(1) if match else None

        with st.form("append_data_form"):
            col1, col2 = st.columns(2)
            artist_A = st.session_state.poll_options[0]
            artist_B = st.session_state.poll_options[1]

            with col1:
                song_title_for_A = st.text_input(f"Song Title for {artist_A}", value=f"{group_A.get('song_title', '')}")
                song_img_for_A = st.text_input(f"Song Image for {artist_A}", value=f"{group_A.get('song_thumbnail', '')}")
                song_link_for_A = st.text_input(f"Song Link for {artist_A}", value="")
                if song_link_for_A:
                    youtube_id_A = parse_youtube_id(song_link_for_A)
                    if youtube_id_A:
                        st.success(f"YouTube Video ID for {artist_A}: {youtube_id_A}")
                        maxres_url_A = f"https://i.ytimg.com/vi/{youtube_id_A}/maxresdefault.jpg"
                        hq_url_A = f"https://i.ytimg.com/vi/{youtube_id_A}/hqdefault.jpg"
                        st.markdown(f"""
                                    <div style="display:flex; gap:20px;">
                                        <div style="text-align:center;">
                                            <p style="font-weight:bold;">MAX</p>
                                            <a href="{maxres_url_A}" target="_blank">
                                                <img src="{maxres_url_A}" alt="Max Resolution Thumbnail"
                                                style="width:100%; max-width:300px; border-radius:10px;"/>
                                            </a>
                                        </div>
                                        <div style="text-align:center;">
                                            <p style="font-weight:bold;">HQ</p>
                                            <a href="{hq_url_A}" target="_blank">
                                                <img src="{hq_url_A}" alt="HQ Thumbnail"
                                                style="width:100%; max-width:300px; border-radius:10px;"/>
                                            </a>
                                        </div>
                                    </div>
                                """, unsafe_allow_html=True)

                    else:
                        st.error("Invalid YouTube URL.")
            with col2:
                song_title_for_B = st.text_input(f"Song Title for {artist_B}", value=f"{group_B.get('song_title', '')}")
                song_img_for_B = st.text_input(f"Song Image for {artist_B}", value=f"{group_B.get('song_thumbnail', '')}")
                song_link_for_B = st.text_input(f"Song Link for {artist_B}", value="")
                if song_link_for_B:
                    youtube_id_B = parse_youtube_id(song_link_for_B)
                    if youtube_id_B:
                        st.success(f"YouTube Video ID for {artist_B}: {youtube_id_B}")
                        maxres_url_B = f"https://i.ytimg.com/vi/{youtube_id_B}/maxresdefault.jpg"
                        hq_url_B = f"https://i.ytimg.com/vi/{youtube_id_B}/hqdefault.jpg"
                        st.markdown(f"""
                                    <div style="display:flex; gap:20px;">
                                        <div style="text-align:center;">
                                            <p style="font-weight:bold;">MAX</p>
                                            <a href="{maxres_url_B}" target="_blank">
                                                <img src="{maxres_url_B}" alt="Max Resolution Thumbnail"
                                                style="width:100%; max-width:300px; border-radius:10px;"/>
                                            </a>
                                        </div>
                                        <div style="text-align:center;">
                                            <p style="font-weight:bold;">HQ</p>
                                            <a href="{hq_url_B}" target="_blank">
                                                <img src="{hq_url_B}" alt="HQ Thumbnail"
                                                style="width:100%; max-width:300px; border-radius:10px;"/>
                                            </a>
                                        </div>
                                    </div>
                                """, unsafe_allow_html=True)
            
            st.divider()
            poll_id = st.text_input("Poll ID", value=default_poll_id)
            title = st.text_input("Title", value=st.session_state.poll_title.replace('"', ''))
            title_shorten = st.text_input("Title Shorten", value="")
            options_str = st.text_input("Options", value=";".join(st.session_state.poll_options))
            options_shorten = st.text_input("Options Shorten", value="")
            img = st.text_input("Image URL", value=st.session_state.image_url)
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
                        "URL or Condition": f"https://starglow.io/polls/{poll_id}",
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

sys.stdout = StreamlitLogger()

# 메인 함수: 각 단계별 함수들을 순차적으로 호출
def main():
    st.title("Starglow Poll Maker")
    initialize_session_state()
    display_sidebar()  # 사이드바에 진행 단계 표시 및 리셋 버튼

    group_listup()
    group_selection()
    display_groups()
    build_prompt_step()
    ask_to_gpt_step()
    manual_input_step()
    append_data_modify_step()
    quest_entries_section()

if __name__ == "__main__":
    main()
