##### main.py #####

import pandas as pd
from crawler.group_crawler import groups_from_urls
from crawler.get_data import get_individual_data

def get_data(groups):
    results = []
    for group in groups:
        link = group["link"]
        group_name = group["group_name"]
        print(f"Processing {group_name} - {link}")
        data = get_individual_data(link)
        if data is None:
            continue  # 개별 데이터를 가져오지 못하면 건너뜁니다.
        # 원래 크롤링한 그룹 기본정보를 추가
        data["group_name"] = group_name
        data["link"] = link
        data["type"] = group.get("type", "")
        data["gender"] = group.get("gender", "")
        results.append(data)
    return results

def get_groups():
    boys_urls = [
      "https://kpop.fandom.com/wiki/Category:Male_groups",
      "https://kpop.fandom.com/wiki/Category:Male_groups?from=Forestella",
      "https://kpop.fandom.com/wiki/Category:Male_groups?from=SHINHWA+%28group%29"
    ]
    boygroups = groups_from_urls(boys_urls, "male")
    
    girls_urls = [
      "https://kpop.fandom.com/wiki/Category:Female_groups",
      "https://kpop.fandom.com/wiki/Category:Female_groups?from=CLEO+%28group%29",
      "https://kpop.fandom.com/wiki/Category:Female_groups?from=IITERNITI",
      "https://kpop.fandom.com/wiki/Category:Female_groups?from=Perfume+de+Ange",
      "https://kpop.fandom.com/wiki/Category:Female_groups?from=UNICODE"
    ]
    girlgroups = groups_from_urls(girls_urls, "female")
    
    groups = boygroups + girlgroups
    if not groups:
        print("그룹 목록을 찾지 못했습니다.")
        return

    print(f"총 {len(groups)}개의 그룹을 찾았습니다. 개별 데이터를 추출합니다...")
    data_list = get_data(groups)
    
    # DataFrame으로 변환
    df = pd.DataFrame(data_list)
    print("DataFrame 생성 완료. 일부 데이터 미리보기:")
    print(df.head())
    
    # CSV 파일로 저장 (UTF-8 BOM 포함)
    output_file = "groups_data.csv"
    df.to_csv(output_file, index=False, encoding="utf-8-sig")
    print(f"데이터가 {output_file} 파일로 저장되었습니다.")
    
from sns.youtube import get_youtube_channel_id, get_youtube_stats, get_top_videos
import pandas as pd
import ast
from googleapiclient.discovery import build
import os
from dotenv import load_dotenv

load_dotenv()

def get_youtube():    
    API_KEY = os.getenv("API_KEY")
    youtube = build("youtube", "v3", developerKey=API_KEY)
    
    # 1. CSV 데이터 불러오기
    df = pd.read_csv("groups_data.csv")
    updated_df = pd.read_csv("groups_data_updated.csv")
    if not updated_df.empty:
        df = updated_df
    
    # 1-1. 필요한 컬럼이 없으면 생성 (이미 처리된 데이터인지 확인하기 위해)
    if "youtube_data" not in df.columns:
        df["youtube_data"] = None
    if "youtube_subscribers" not in df.columns:
        df["youtube_subscribers"] = None
    if "youtube_videos" not in df.columns:
        df["youtube_videos"] = None

    # 2. 'sns' 컬럼에서 리스트 데이터 추출 (문자열 형태이면 ast.literal_eval 사용)
    def parse_sns(sns_value):
        try:
            # 예: "['https://www.instagram.com/andteam_official/', ...]"
            return ast.literal_eval(sns_value) if isinstance(sns_value, str) else sns_value
        except Exception:
            return []
    df["sns_parsed"] = df["sns"].apply(parse_sns)

    # 3. 각 행의 sns 링크 중 'youtube.com'이 포함된 링크 추출 (여러 개면 첫 번째만)
    def extract_youtube_link(sns_list):
        if not isinstance(sns_list, list):
            return None
        for link in sns_list:
            if "youtube.com" in link:
                return link
        return None
    df["youtube_link"] = df["sns_parsed"].apply(extract_youtube_link)

    # 4. YouTube 링크로부터 구독자 수와 상위 10개 동영상 정보 가져오기
    def get_youtube_data(youtube_link):
        if not youtube_link:
            return {"subscribers": 0, "top_videos": []}
        channel_id = get_youtube_channel_id(youtube, youtube_link)
        if not channel_id:
            return {"subscribers": 0, "top_videos": []}
        subscribers = get_youtube_stats(youtube, channel_id)
        top_videos = []
        #top_videos = get_top_videos(youtube, channel_id, top_n=10)
        return {"subscribers": subscribers, "top_videos": top_videos}

    # 5. 각 행을 순차적으로 처리하고, 처리한 후 CSV 업데이트 (이미 처리된 행은 건너뜁니다)
    for idx, row in df.iterrows():
        # youtube_subscribers 값이 비어있거나 0인 경우에만 처리 (이미 업데이트된 행은 건너뛰기)
        if pd.isna(row["youtube_subscribers"]) or row["youtube_subscribers"] == 0:
            print(f"Processing row {idx}: {row['group_name']}")
            data = get_youtube_data(row["youtube_link"])
            df.at[idx, "youtube_data"] = data
            df.at[idx, "youtube_subscribers"] = data.get("subscribers", 0)
            df.at[idx, "youtube_videos"] = data.get("top_videos", [])
            # 처리한 후 CSV 파일 업데이트 (중간에 중단되어도 처리된 내용은 저장됨)
            df.to_csv("groups_data_updated.csv", index=False, encoding="utf-8-sig")
        else:
            print(f"Skipping row {idx}: {row['group_name']} already processed")
    
    print("Processing complete.")

def main():
    get_youtube()

if __name__ == "__main__":
    main()