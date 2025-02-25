
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
    target_row = len(col_values) + 2
    appended_rows = []
    for quest in quests_data:
        for key, value in quest.items():
            if key in header_map:
                if isinstance(value, list):
                    value = ';'.join(value)
                sheet.update_cell(target_row, header_map[key], value)
        appended_rows.append(target_row)
        target_row += 1
    return appended_rows