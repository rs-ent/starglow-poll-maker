import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def append_new_poll(new_poll_data):
    # poll_id 검증
    poll_id = new_poll_data.get("poll_id", "")
    if not poll_id:
        raise ValueError("poll_id는 필수 값입니다.")

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
    try:
        cell = sheet.find(poll_id)
        target_row = cell.row
    except gspread.exceptions.CellNotFound:
        # poll_id를 찾지 못한 경우 마지막 행 다음에 추가
        target_row = len(sheet.col_values(1)) + 1

    # 배치 업데이트를 위한 데이터 준비
    batch_data = []
    for key, value in new_poll_data.items():
        if key in header_map:
            if isinstance(value, list):
                value = ";".join(value)
            col_idx = header_map[key]
            cell = gspread.utils.rowcol_to_a1(target_row, col_idx)
            batch_data.append({
                'range': cell,
                'values': [[value]]
            })
    
    # 한 번의 요청으로 모든 데이터 업데이트
    if batch_data:
        sheet.batch_update(batch_data)
    
    return target_row
