import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def append_new_quests(quests_data=[]):
    google_service_account_str = os.environ.get('GOOGLE_SERVICE_ACCOUNT')
    if not google_service_account_str:
        raise ValueError('GOOGLE_SERVICE_ACCOUNT 환경 변수가 설정되어 있지 않습니다.')
    google_service_account_info = json.loads(google_service_account_str)
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_dict(google_service_account_info, scope)
    gc = gspread.authorize(creds)
    sheet = gc.open_by_url('https://docs.google.com/spreadsheets/d/1ZRL_ifqMs35BHOgYMxY59xUTb-l5r2HdCnI1GTneni4').worksheet('Quest')
    header = sheet.row_values(1)
    header_map = {col: idx + 1 for idx, col in enumerate(header)}
    col_values = sheet.col_values(header_map.get('Quest Title', 1))
    start_row = len(col_values) + 1
    
    # 배치 업데이트를 위한 데이터 준비
    batch_data = []
    appended_rows = []
    
    for row_idx, quest in enumerate(quests_data):
        current_row = start_row + row_idx
        appended_rows.append(current_row)
        
        for key, value in quest.items():
            if key in header_map:
                col_idx = header_map[key]
                if isinstance(value, list):
                    value = ';'.join(value)
                # A1 표기법으로 셀 위치 지정
                cell = gspread.utils.rowcol_to_a1(current_row, col_idx)
                batch_data.append({
                    'range': cell,
                    'values': [[value]]
                })
    
    # 한 번의 요청으로 모든 데이터 업데이트
    if batch_data:
        sheet.batch_update(batch_data)
    
    return appended_rows