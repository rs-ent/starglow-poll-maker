
import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def append_new_poll(new_poll_data):
    google_service_account_str = os.environ.get("GOOGLE_SERVICE_ACCOUNT")
    if not google_service_account_str:
        raise ValueError("GOOGLE_SERVICE_ACCOUNT 환경 변수가 설정되어 있지 않습니다.")
    google_service_account_info = json.loads(google_service_account_str)
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(google_service_account_info, scope)
    gc = gspread.authorize(creds)

    sheet = gc.open_by_url("https://docs.google.com/spreadsheets/d/1ZRL_ifqMs35BHOgYMxY59xUTb-l5r2HdCnI1GTneni4").worksheet("Poll List")
    header = sheet.row_values(1)
    header_map = {col: idx + 1 for idx, col in enumerate(header)}
    
    # new_poll_data의 poll_id를 기준으로 해당 행 찾기
    poll_id = new_poll_data.get("poll_id", "")
    try:
        cell = sheet.find(poll_id)
        target_row = cell.row
    except Exception:
        target_row = len(sheet.col_values(1)) + 1

    for key, value in new_poll_data.items():
        if key in header_map:
            # 만약 value가 리스트라면, 문자열로 변환
            if isinstance(value, list):
                value = ";".join(value)
            col_index = header_map[key]
            sheet.update_cell(target_row, col_index, value)
    
    return target_row
