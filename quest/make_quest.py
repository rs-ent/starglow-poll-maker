
import os
from openai import OpenAI
import pandas as pd
from dotenv import load_dotenv
load_dotenv()
client = OpenAI(api_key=os.environ['OPENAI'])

def load_data(csv_path='groups_data_updated.csv'):
    df = pd.read_csv(csv_path)
    df = df.dropna(subset=['youtube_subscribers'])
    df['youtube_subscribers'] = df['youtube_subscribers'].astype(int)
    df = df[df['youtube_subscribers'] > 0]
    df = df[df['image'].notna() & (df['image'] != '')]
    for col in ['genres', 'debut', 'disbanded']:
        df[col] = df[col].fillna('Not available')
    return df

def select_two_groups(df):
    """
    그룹 A를 무작위로 선택한 후,c
    그룹 A의 youtube_subscribers 값과 ±10% 범위 내에서 그룹 B를 선택합니다.
    조건에 맞는 그룹이 없으면, 구독자 차이가 가장 적은 상위 5개 중 랜덤 선택합니다.
    """
    group_A = df.sample(n=1).iloc[0]
    subscribers_A = group_A['youtube_subscribers']
    threshold = 0.1 * subscribers_A
    similar_df = df[(df['youtube_subscribers'] >= subscribers_A - threshold) & (df['youtube_subscribers'] <= subscribers_A + threshold) & (df['group_name'] != group_A['group_name'])]
    if similar_df.empty:
        df_noA = df[df['group_name'] != group_A['group_name']].copy()
        df_noA['diff'] = (df_noA['youtube_subscribers'] - subscribers_A).abs()
        similar_df = df_noA.sort_values(by='diff').head(5)
    group_B = similar_df.sample(n=1).iloc[0]
    return (group_A, group_B)

def row_to_dict(row):
    dict_full = row.to_dict()
    return {k: v for k, v in dict_full.items() if pd.notnull(v) and v != ''}

def build_prompt(group_A, group_B):
    """
    두 그룹의 주요 정보를 포함하는 영어 프롬프트를 생성하여,
    LLM에게 창의적이고 다채로운 투표 제목 생성을 요청합니다.
    """
    members_A = group_A.get('members_current', [])
    if isinstance(members_A, list):
        members_A_str = ', '.join(members_A) if members_A else 'Not available'
    else:
        members_A_str = members_A
    members_B = group_B.get('members_current', [])
    if isinstance(members_B, list):
        members_B_str = ', '.join(members_B) if members_B else 'Not available'
    else:
        members_B_str = members_B
    prompt = f"""Use the following Group A and Group B data. \nPlease create a catchy and exciting poll title in English that captures the dynamic showdown between these two K-pop groups.\nThe title should highlight each group's unique characteristics and debut era, while presenting both their similarities and differences.\nAdjust the intensity of expressions based on their YouTube subscribers count.\nAvoid using terms like "newbies" unless both groups debuted in 2024 or later.\nThe title must be provocative yet respectful to the fandom, and no more than 50 characters.\nProvide only the title, with no additional explanation or commentary.\n\nGroup A:\n- Name: {group_A['group_name']}\n- Genre: {group_A.get('genres', 'Not available')}\n- Debut: {group_A.get('debut', 'Not available')}\n- Disbanded: {group_A.get('disbanded', 'Currently active. Not disbanded.')}\n- Members: {members_A_str}\n- Gender: {group_A.get('gender', 'Not available')}\n- YouTube Subscribers: {group_A['youtube_subscribers']}\n\nGroup B:\n- Name: {group_B['group_name']}\n- Genre: {group_B.get('genres', 'Not available')}\n- Members: {members_B_str}\n- Gender: {group_B.get('gender', 'Not available')}\n- YouTube Subscribers: {group_B['youtube_subscribers']}"""
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

def main():
    df = load_data('groups_data_updated.csv')
    group_A, group_B = select_two_groups(df)
    prompt = build_prompt(group_A, group_B)
    print('=== Prompt ===')
    print(prompt)
    poll_title = generate_poll_title(prompt)
    print('\n=== Generated Poll Title ===')
    print(poll_title)
    poll_options = generate_poll_options(group_A, group_B)
    print('\n=== Generated Poll Options ===')
    print(poll_options)
if __name__ == '__main__':
    main()