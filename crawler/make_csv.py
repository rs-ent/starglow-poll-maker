##### crawler\make_csv.py #####

import pandas as pd
from crawler.group_crawler import groups_from_urls
from crawler.get_data import get_individual_data
import random
import time

def get_data(groups, output_file="groups_data.csv", batch_size=10):
    results = []
    batch_count = 0
    for group in groups:
        print(f"\n\n========================================\n\n")
        link = group["link"]
        group_name = group["group_name"].split(" (")[0]
        print(f"그룹 '{group_name}'의 데이터를 가져옵니다... \n({link})")
        data = get_individual_data(link)
        if data is None:
            continue
        
        data["name"] = group_name
        print(f"그룹 '{group_name}'의 데이터를 가져왔습니다.")
        data["group_name"] = group_name
        data["link"] = link
        data["type"] = group.get("type", "")
        data["gender"] = group.get("gender", "")
        print(f"\n\n========================================\n\n")
        
        results.append(data)
        time.sleep(random.uniform(0.01, 0.6))
        
        batch_count += 1
        if batch_count == batch_size:
            df_batch = pd.DataFrame(results)
            hashable_cols = ['group_name', 'link', 'gender', 'image']
            df_batch.drop_duplicates(subset=hashable_cols)
            df_batch.to_csv(output_file, index=False, encoding="utf-8-sig")
            batch_count = 0

    return results

def get_groups(output_file="groups_data.csv"):
    print(f"\n\n========================================\n\n")
    print("그룹 목록을 가져옵니다...")
    boys_urls = [
        "https://kpop.fandom.com/wiki/Category:Male_groups",
        "https://kpop.fandom.com/wiki/Category:Male_groups?from=A",
        "https://kpop.fandom.com/wiki/Category:Male_groups?from=B",
        "https://kpop.fandom.com/wiki/Category:Male_groups?from=C",
        "https://kpop.fandom.com/wiki/Category:Male_groups?from=D",
        "https://kpop.fandom.com/wiki/Category:Male_groups?from=E",
        "https://kpop.fandom.com/wiki/Category:Male_groups?from=F",
        "https://kpop.fandom.com/wiki/Category:Male_groups?from=G",
        "https://kpop.fandom.com/wiki/Category:Male_groups?from=H",
        "https://kpop.fandom.com/wiki/Category:Male_groups?from=I",
        "https://kpop.fandom.com/wiki/Category:Male_groups?from=J",
        "https://kpop.fandom.com/wiki/Category:Male_groups?from=K",
        "https://kpop.fandom.com/wiki/Category:Male_groups?from=L",
        "https://kpop.fandom.com/wiki/Category:Male_groups?from=M",
        "https://kpop.fandom.com/wiki/Category:Male_groups?from=N",
        "https://kpop.fandom.com/wiki/Category:Male_groups?from=O",
        "https://kpop.fandom.com/wiki/Category:Male_groups?from=P",
        "https://kpop.fandom.com/wiki/Category:Male_groups?from=Q",
        "https://kpop.fandom.com/wiki/Category:Male_groups?from=R",
        "https://kpop.fandom.com/wiki/Category:Male_groups?from=S",
        "https://kpop.fandom.com/wiki/Category:Male_groups?from=T",
        "https://kpop.fandom.com/wiki/Category:Male_groups?from=U",
        "https://kpop.fandom.com/wiki/Category:Male_groups?from=V",
        "https://kpop.fandom.com/wiki/Category:Male_groups?from=W",
        "https://kpop.fandom.com/wiki/Category:Male_groups?from=X",
        "https://kpop.fandom.com/wiki/Category:Male_groups?from=Y",
        "https://kpop.fandom.com/wiki/Category:Male_groups?from=Z"
    ]
    boygroups = groups_from_urls(boys_urls, "male")
    print(f"총 {len(boygroups)}개의 남자 그룹을 찾았습니다.")
    
    girls_urls = [
        "https://kpop.fandom.com/wiki/Category:Female_groups",
        "https://kpop.fandom.com/wiki/Category:Female_groups?from=A",
        "https://kpop.fandom.com/wiki/Category:Female_groups?from=B",
        "https://kpop.fandom.com/wiki/Category:Female_groups?from=C",
        "https://kpop.fandom.com/wiki/Category:Female_groups?from=D",
        "https://kpop.fandom.com/wiki/Category:Female_groups?from=E",
        "https://kpop.fandom.com/wiki/Category:Female_groups?from=F",
        "https://kpop.fandom.com/wiki/Category:Female_groups?from=G",
        "https://kpop.fandom.com/wiki/Category:Female_groups?from=H",
        "https://kpop.fandom.com/wiki/Category:Female_groups?from=I",
        "https://kpop.fandom.com/wiki/Category:Female_groups?from=J",
        "https://kpop.fandom.com/wiki/Category:Female_groups?from=K",
        "https://kpop.fandom.com/wiki/Category:Female_groups?from=L",
        "https://kpop.fandom.com/wiki/Category:Female_groups?from=M",
        "https://kpop.fandom.com/wiki/Category:Female_groups?from=N",
        "https://kpop.fandom.com/wiki/Category:Female_groups?from=O",
        "https://kpop.fandom.com/wiki/Category:Female_groups?from=P",
        "https://kpop.fandom.com/wiki/Category:Female_groups?from=Q",
        "https://kpop.fandom.com/wiki/Category:Female_groups?from=R",
        "https://kpop.fandom.com/wiki/Category:Female_groups?from=S",
        "https://kpop.fandom.com/wiki/Category:Female_groups?from=T",
        "https://kpop.fandom.com/wiki/Category:Female_groups?from=U",
        "https://kpop.fandom.com/wiki/Category:Female_groups?from=V",
        "https://kpop.fandom.com/wiki/Category:Female_groups?from=W",
        "https://kpop.fandom.com/wiki/Category:Female_groups?from=X",
        "https://kpop.fandom.com/wiki/Category:Female_groups?from=Y",
        "https://kpop.fandom.com/wiki/Category:Female_groups?from=Z"
    ]
    girlgroups = groups_from_urls(girls_urls, "female")
    print(f"총 {len(girlgroups)}개의 여자 그룹을 찾았습니다.")
    
    groups = boygroups + girlgroups
    if not groups:
        print("그룹 목록을 찾지 못했습니다.")
        return

    print(f"\n\n========================================\n\n")
    print(f"총 {len(groups)}개의 그룹을 찾았습니다. 개별 데이터를 추출합니다...")
    data_list = get_data(groups, output_file)
    
    # DataFrame으로 변환
    df = pd.DataFrame(data_list)
    hashable_cols = ['group_name', 'link', 'gender', 'image']
    df = df.drop_duplicates(subset=hashable_cols)
    print("DataFrame 생성 완료. 일부 데이터 미리보기:")
    print(df.head())
    
    # CSV 파일로 저장 (UTF-8 BOM 포함)
    df.to_csv(output_file, index=False, encoding="utf-8-sig")
    print(f"데이터가 {output_file} 파일로 저장되었습니다.")
    
from sns.youtube import get_youtube_channel_ids, get_youtube_stats_batch
import pandas as pd
import ast
from googleapiclient.discovery import build
import os
from dotenv import load_dotenv

load_dotenv()

def get_youtube(input_file="groups_data.csv", output_file="groups_data_updated.csv"):    
    API_KEY = os.getenv("API_KEY")
    youtube = build("youtube", "v3", developerKey=API_KEY)
    
    # 1. CSV 데이터 불러오기
    print("1. CSV 파일을 불러옵니다...")
    df = pd.read_csv(input_file)
    try:
        updated_df = pd.read_csv(output_file)
        if not updated_df.empty:
            df = updated_df
    except Exception:
        pass
    
    print(f"\n\n========================================\n\n")
    print(f"1. 총 {len(df)}개의 행을 불러왔습니다.")
    # 1-1. 필요한 컬럼이 없으면 생성 (이미 처리된 데이터인지 확인하기 위해)
    print("1.1. 필요한 컬럼이 없으면 생성합니다...")
    for col in ["youtube_data", "youtube_subscribers", "youtube_videos"]:
        if col not in df.columns:
            df[col] = None
    print("1.1. 필요한 컬럼이 모두 생성되었습니다.")

    # 2. 'sns' 컬럼에서 리스트 데이터 추출 (문자열이면 ast.literal_eval 사용)
    print(f"\n\n========================================\n\n")
    print("2. sns 컬럼을 파싱합니다...")
    def parse_sns(sns_value):
        try:
            return ast.literal_eval(sns_value) if isinstance(sns_value, str) else sns_value
        except Exception:
            return []
    df["sns_parsed"] = df["sns"].apply(parse_sns)
    print("2. sns 컬럼 파싱이 완료되었습니다.")

    # 3. 각 행의 sns 링크 중 'youtube.com'이 포함된 링크 추출 (여러 개면 첫 번째만)
    print(f"\n\n========================================\n\n")
    print("3. youtube 링크를 추출합니다...\n")
    def extract_youtube_link(sns_list):
        if not isinstance(sns_list, list):
            return None
        for link in sns_list:
            if "youtube.com" in link:
                return link
        return None
    df["youtube_link"] = df["sns_parsed"].apply(extract_youtube_link)
    print("3. youtube 링크 추출이 완료되었습니다.")

    # 4. 처리할 행 필터링 (youtube_subscribers가 비어있거나 0인 경우)
    print(f"\n\n========================================\n\n")
    print("4. 처리할 행을 필터링합니다...")
    df["youtube_subscribers"] = pd.to_numeric(df["youtube_subscribers"], errors='coerce')
    to_process = df[df["youtube_subscribers"].isna() | (df["youtube_subscribers"] == 0)]

    if to_process.empty:
        print("4. 모든 행이 이미 처리되었습니다.")
        return
    print(f"4. 총 {len(to_process)}개의 행을 처리할 예정입니다.")

    # 5. 배치 처리로 채널 ID 조회
    print(f"\n\n========================================\n\n")
    print("5. 채널 ID를 조회합니다...")
    youtube_links = to_process["youtube_link"].tolist()
    channel_ids_mapping = get_youtube_channel_ids(youtube_links)
    print("5. 채널 ID 조회가 완료되었습니다.")

    # 6. 배치 처리로 통계 정보 조회
    print(f"\n\n========================================\n\n")
    print("6. 통계 정보를 조회합니다...")
    # 유효한 채널 ID만 추출
    valid_channel_ids = [cid for cid in channel_ids_mapping.values() if cid]
    stats_mapping = get_youtube_stats_batch(youtube, valid_channel_ids)
    print("6. 통계 정보 조회가 완료되었습니다.")

    # 7. DataFrame 업데이트
    print(f"\n\n========================================\n\n")
    print("7. DataFrame을 업데이트합니다...")
    for idx in to_process.index:
        link = df.at[idx, "youtube_link"]
        if not link:
            data = {"subscribers": 0, "viewCount": 0, "videoCount": 0}
        else:
            channel_id = channel_ids_mapping.get(link)
            # channel_id가 dict라면 문자열 채널 ID로 변환
            if isinstance(channel_id, dict):
                channel_id = channel_id.get("id")
            if not channel_id:
                data = {"subscribers": 0, "viewCount": 0, "videoCount": 0}
            else:
                stats = stats_mapping.get(channel_id, {"subscriberCount": 0, "viewCount": 0, "videoCount": 0})
                data = {
                    "subscribers": stats.get("subscriberCount", 0),
                    "viewCount": stats.get("viewCount", 0),
                    "videoCount": stats.get("videoCount", 0)
                }
        df.at[idx, "youtube_data"] = str(data)
        df.at[idx, "youtube_subscribers"] = data.get("subscribers", 0)


        # 그룹 이름이 "("를 포함하면 split하여 첫 부분만 사용
        group_name = df.at[idx, "group_name"]
        if " (" in group_name:
            processed_name = group_name.split(" (")[0]
            df.at[idx, "group_name"] = processed_name

        # 중간 결과를 CSV에 저장 (실패 시에도 저장)
        df.to_csv(output_file, index=False, encoding="utf-8-sig")
        print(f"Row {idx} processed: {df.at[idx, 'group_name']}")

    print("Processing complete.")

def main():
    get_youtube()

if __name__ == "__main__":
    main()

    