import pandas as pd
import random
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import os
os.environ["HF_HOME"] = r"G:\Cache"
os.environ["TRANSFORMERS_CACHE"] = r"G:\Cache\transformers"
os.environ["TMP"] = r"G:\Temp"
os.environ["TEMP"] = r"G:\Temp"
os.environ[".cacheggg"] = r"G:\Cache"


def load_data(csv_path="groups_data_updated.csv"):
    # CSV 데이터 불러오기 및 전처리: youtube_subscribers가 0보다 큰 그룹만 사용
    df = pd.read_csv(csv_path)
    df = df.dropna(subset=["youtube_subscribers"])
    df["youtube_subscribers"] = df["youtube_subscribers"].astype(int)
    df = df[df["youtube_subscribers"] > 0]
    return df

def select_two_groups(df):
    """
    그룹 A를 무작위로 선택한 후,
    그룹 A의 youtube_subscribers 값과 ±10% 범위 내에서 그룹 B를 선택합니다.
    조건에 맞는 그룹이 없으면, 구독자 차이가 가장 적은 상위 5개 중 랜덤 선택합니다.
    """
    group_A = df.sample(n=1).iloc[0]
    subscribers_A = group_A["youtube_subscribers"]
    threshold = 0.1 * subscribers_A
    similar_df = df[
        (df["youtube_subscribers"] >= subscribers_A - threshold) &
        (df["youtube_subscribers"] <= subscribers_A + threshold) &
        (df["group_name"] != group_A["group_name"])
    ]
    if similar_df.empty:
        df_noA = df[df["group_name"] != group_A["group_name"]].copy()
        df_noA["diff"] = (df_noA["youtube_subscribers"] - subscribers_A).abs()
        similar_df = df_noA.sort_values(by="diff").head(5)
    group_B = similar_df.sample(n=1).iloc[0]
    return group_A, group_B

def row_to_dict(row):
    # NaN 또는 빈 문자열이 아닌 데이터만 딕셔너리로 반환
    dict_full = row.to_dict()
    return {k: v for k, v in dict_full.items() if pd.notnull(v) and v != ""}

def build_prompt(group_A, group_B):
    """
    두 그룹의 주요 정보를 포함하는 영어 프롬프트를 생성하여,
    LLM에게 창의적이고 다채로운 투표 제목 생성을 요청합니다.
    """
    
    members_A = group_A.get('members_current', [])
    if isinstance(members_A, list):
        members_A_str = ", ".join(members_A) if members_A else "Not available"
    else:
        members_A_str = members_A  # 이미 문자열인 경우
    
    # 그룹 B의 멤버 정보 처리
    members_B = group_B.get('members_current', [])
    if isinstance(members_B, list):
        members_B_str = ", ".join(members_B) if members_B else "Not available"
    else:
        members_B_str = members_B
        
        
    prompt = f"""Use the following Group A and Group B data. Please create an catchy and exciting poll title in English that captures the dynamic showdown between these two K-pop groups. The title should highlight each group's unique style, debut era, and competitive spirit. Provide only the title, with no additional explanation or commentary.


Group A:
- Name: {group_A['group_name']}
- Genre: {group_A.get('genres', 'Not available')}
- Debut: {group_A.get('debut', 'Not available')}
- Disbanded: {group_A.get('disbanded', 'Currently active. Not disbanded.')}
- Members: {members_A_str}
- Gender: {group_A.get('gender', 'Not available')}
- YouTube Subscribers: {group_A['youtube_subscribers']}

Group B:
- Name: {group_B['group_name']}
- Genre: {group_B.get('genres', 'Not available')}
- Debut: {group_B.get('debut', 'Not available')}
- Disbanded: {group_B.get('disbanded', 'Currently active. Not disbanded.')}
- Members: {members_B_str}
- Gender: {group_B.get('gender', 'Not available')}
- YouTube Subscribers: {group_B['youtube_subscribers']}

For example, your output could be:
"Rising Queens vs. Future Icons: K-pop Showdown!"""
    return prompt

def generate_poll_title(prompt, model_name="EleutherAI/gpt-j-6B", max_new_tokens=60, num_return_sequences=1):
    """
    Hugging Face의 text-generation 파이프라인을 사용하여,
    프롬프트 기반의 Poll 제목을 생성합니다.
    EleutherAI/gpt-j-6B 사용합니다.
    """
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name)
    text_generator = pipeline("text-generation", model=model, tokenizer=tokenizer)
    results = text_generator(prompt, max_new_tokens=max_new_tokens, num_return_sequences=num_return_sequences, do_sample=True)
    print("=========================RESULT=========================")
    print(results)
    return results[0]["generated_text"]
  
def generate_poll_options(group_A, group_B):
    """
    두 그룹의 'group_name'에서 괄호 이전의 부분만 추출하여,
    투표 옵션 리스트를 생성합니다.
    예를 들어, 그룹명이 "A'ST1 (Special Edition)"인 경우 "A'ST1"만 추출합니다.
    """
    options = []
    
    # 그룹 A의 이름 처리
    a_name = group_A.get('group_name', '')
    if a_name:
        a_option = a_name.split(" (")[0]
        options.append(a_option)
    
    # 그룹 B의 이름 처리
    b_name = group_B.get('group_name', '')
    if b_name:
        b_option = b_name.split(" (")[0]
        options.append(b_option)
    
    return options

def main():
    # 1. CSV 파일에서 데이터 불러오기
    df = load_data("groups_data_updated.csv")
    
    # 2. 조건에 맞는 두 그룹 선택
    group_A, group_B = select_two_groups(df)
    
    # 3. 프롬프트 생성 (두 그룹의 모든 유효 데이터를 포함)
    prompt = build_prompt(group_A, group_B)
    print("=== Prompt ===")
    print(prompt)
    
    # 4. GPT-2를 사용하여 Poll 제목 생성
    poll_title = generate_poll_title(prompt)
    print("\n=== Generated Poll Title ===")
    print(poll_title)
    
    poll_options = generate_poll_options(group_A, group_B)
    print("\n=== Generated Poll Options ===")
    print(poll_options)
    

if __name__ == "__main__":
    main()
