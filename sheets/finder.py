import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta

def find_latest_poll_id():
    # 환경 변수에서 서비스 계정 정보를 JSON 문자열로 가져와 딕셔너리로 변환
    google_service_account_str = os.environ.get("GOOGLE_SERVICE_ACCOUNT")
    if not google_service_account_str:
        raise ValueError("GOOGLE_SERVICE_ACCOUNT 환경 변수가 설정되어 있지 않습니다.")
    google_service_account_info = json.loads(google_service_account_str)
    
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(google_service_account_info, scope)
    gc = gspread.authorize(creds)

    # 지정된 구글 스프레드시트와 워크시트 열기
    sheet = gc.open_by_url("https://docs.google.com/spreadsheets/d/1ZRL_ifqMs35BHOgYMxY59xUTb-l5r2HdCnI1GTneni4").worksheet("Poll List")
    
    # 헤더 읽기 및 각 열의 인덱스(1-indexed) 매핑 생성
    header = sheet.row_values(1)
    header_map = {col: idx + 1 for idx, col in enumerate(header)}

    # 'title' 열의 인덱스 확인
    title_col_index = header_map.get('title')
    if not title_col_index:
        raise ValueError("헤더에 'title' 열이 없습니다.")

    # 'title' 값이 비어있는 첫 번째 행 찾기 (헤더 이후 행부터 검색)
    col_values = sheet.col_values(title_col_index)
    target_row = None
    for i in range(2, len(col_values) + 1):
        if not col_values[i - 1]:
            target_row = i
            break

    if target_row is not None:
        # 빈 행이 있는 경우 해당 행의 데이터를 반환
        row_values = sheet.row_values(target_row)
        row_obj = {header[i]: row_values[i] if i < len(row_values) else "" for i in range(len(header))}
        return row_obj
    else:
        # 빈 행이 없으면, 새 행 번호를 할당하고 직전 행의 데이터를 참고하여 새 poll_id, start, end 계산
        target_row = len(col_values) + 1
        previous_row_index = len(col_values)  # 마지막 데이터 행
        previous_row_values = sheet.row_values(previous_row_index)
        row_obj_prev = {header[i]: previous_row_values[i] if i < len(previous_row_values) else "" for i in range(len(header))}

        # poll_id: 'p'를 제외한 숫자에 +1
        previous_poll_id = row_obj_prev.get("poll_id", "")
        if previous_poll_id and previous_poll_id.startswith("p"):
            try:
                num = int(previous_poll_id[1:])
                new_poll_id = "p" + str(num + 1)
            except ValueError:
                new_poll_id = "p1"
        else:
            new_poll_id = "p1"

        # start와 end: 직전 행의 start, end에 +1일 (날짜 형식: "YYYY-MM-DD HH:MM")
        date_format = "%Y-%m-%d %H:%M"
        previous_start = row_obj_prev.get("start", "")
        previous_end = row_obj_prev.get("end", "")
        new_start = ""
        new_end = ""
        if previous_start:
            try:
                dt_start = datetime.strptime(previous_start, date_format)
                new_start = (dt_start + timedelta(days=1)).strftime(date_format)
            except Exception:
                new_start = previous_start
        if previous_end:
            try:
                dt_end = datetime.strptime(previous_end, date_format)
                new_end = (dt_end + timedelta(days=1)).strftime(date_format)
            except Exception:
                new_end = previous_end

        # 새 행의 기본 row object 구성 (나머지 필드는 빈 문자열)
        row_obj = {col: "" for col in header}
        row_obj["poll_id"] = new_poll_id
        row_obj["start"] = new_start
        row_obj["end"] = new_end

        return row_obj