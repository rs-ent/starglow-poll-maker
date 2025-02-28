
import os
from openai import OpenAI
import pandas as pd
from dotenv import load_dotenv
load_dotenv()
client = OpenAI(api_key=os.environ['OPENAI'])

def select_similar_group(df, group, threshold=0.1):
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

def load_data(csv_path='groups_data_updated.csv'):
    df = pd.read_csv(csv_path)
    df = df.dropna(subset=['youtube_subscribers'])
    df['youtube_subscribers'] = df['youtube_subscribers'].astype(int)
    df = df[df['youtube_subscribers'] > 0]
    df = df[df['image'].notna() & (df['image'] != '')]
    df = df[df['disbanded'].isna() == True]
    for col in ['genres', 'debut']:
        df[col] = df[col].fillna('Not available')
    return df

def select_two_groups_random(df):
    group_A = df.sample(n=1).iloc[0]
    group_B = select_similar_group(df, group_A)
    return group_A, group_B

def select_groups_with_min_subscribers(df, min_subscribers, threshold=0.1):
    df_filtered = df[df['youtube_subscribers'] >= min_subscribers]
    if df_filtered.empty:
        raise ValueError("No groups meet the minimum subscriber requirement.")

    group_A = df_filtered.sample(n=1).iloc[0]
    group_B = select_similar_group(df_filtered, group_A, threshold)
    return group_A, group_B

def count_groups_with_min_subscribers(df, min_subscribers):
    return len(df[df['youtube_subscribers'] >= min_subscribers])

def search_groups(df, keyword):
    return df[df['group_name'].str.contains(keyword, case=False, na=False)]

def select_groups_by_search(df, selected_group_name, threshold=0.1):
    matched_groups = df[df['group_name'] == selected_group_name]
    if matched_groups.empty:
        raise ValueError("Selected group not found.")
    
    group_A = matched_groups.iloc[0]
    group_B = select_similar_group(df, group_A, threshold)
    return group_A, group_B

def reselect_group(df, fixed_group):
    """
    fixed_group의 youtube_subscribers를 기준으로 ±10% 범위 내에서
    새로운 그룹을 선택합니다.
    만약 해당 범위 내 후보가 없다면, 구독자 차이가 가장 적은 상위 5개 후보 중 랜덤 선택합니다.
    """
    target_subscribers = fixed_group['youtube_subscribers']
    threshold = 0.1 * target_subscribers
    # 고정 그룹과 다른 그룹들만 후보로 선정
    candidates = df[df['group_name'] != fixed_group['group_name']]
    similar_candidates = candidates[
        (candidates['youtube_subscribers'] >= target_subscribers - threshold) &
        (candidates['youtube_subscribers'] <= target_subscribers + threshold)
    ]
    if similar_candidates.empty:
        candidates = candidates.copy()
        candidates['diff'] = (candidates['youtube_subscribers'] - target_subscribers).abs()
        similar_candidates = candidates.sort_values('diff').head(5)
    return similar_candidates.sample(n=1).iloc[0]

def row_to_dict(row):
    dict_full = row.to_dict()
    return {k: v for k, v in dict_full.items() if pd.notnull(v) and v != ''}

def build_prompt(group_A, group_B):
    """
    두 그룹의 모든 정보를 포함하는 영어 프롬프트를 생성하여,
    LLM에게 창의적이고 다채로운 투표 제목 생성을 요청합니다.
    """
    def format_group_info(group, group_label):
        info = []
        for key, value in group.items():
            if isinstance(value, list):
                value_str = ', '.join(value) if value else "Not available"
            else:
                value_str = value if value else "Not available"
            info.append(f"- {key.replace('_', ' ').title()}: {value_str}")
        return f"{group_label}:\n" + "\n".join(info)

    group_A_info = format_group_info(group_A, "Group A")
    group_B_info = format_group_info(group_B, "Group B")

    prompt = f"""Use the following detailed information about Group A and Group B.

{group_A_info}

{group_B_info}

Please create a catchy and exciting poll title in English that captures the dynamic showdown between these two K-pop groups.

The title should:
- Highlight each group's unique characteristics and debut era.
- Reflect both similarities and differences between the groups.
- Adjust intensity based on their YouTube subscribers count.
- Avoid terms like "newbies" unless both groups debuted in 2024 or later.
- Be provocative yet respectful to the fandom.
- Not exceed 50 characters.

Provide only the title without any additional explanation."""
    
    return prompt

def generate_poll_title(prompt):
    completion = client.completions.create(model='gpt-3.5-turbo-instruct', prompt=prompt, max_tokens=60, temperature=0.7)
    return completion.choices[0].text.strip()

def generate_poll_options(group_A, group_B):
    """
    두 그룹의 'group_name'에서 괄호 이전의 부분만 추출하여,
    투표 옵션 리스트를 생성합니다.
    예를 들어, 그룹명이 "A'ST1 (Special Edition)"인 경우 "A'ST1"만 추출합니다.
    """
    options = []
    a_name = group_A.get('group_name', '')
    if a_name:
        a_option = a_name.split(' (')[0]
        options.append(a_option)
    b_name = group_B.get('group_name', '')
    if b_name:
        b_option = b_name.split(' (')[0]
        options.append(b_option)
    return options