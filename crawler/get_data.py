##### crawler\get_data.py #####

import requests
from bs4 import BeautifulSoup
import re

def extract_value(container):
    """
    주어진 컨테이너에서 값을 추출합니다.
    - <ul> 태그가 있으면, 각 <li>의 텍스트를 리스트로 반환
    - 없으면, 컨테이너의 텍스트(공백 제거)를 반환
    """
    if container is None:
        return ""
    ul = container.find("ul")
    if ul:
        return [li.get_text(strip=True) for li in ul.find_all("li")]
    return container.get_text(separator=" ", strip=True)

def extract_links(container):
    """
    컨테이너 내의 모든 링크 href를 리스트로 반환합니다.
    """
    if container is None:
        return []
    return [a.get("href") for a in container.find_all("a") if a.get("href")]

def get_individual_data(link):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    try:
        response = requests.get(link, headers=headers)
    except Exception as e:
        print(f"Error fetching {link}: {e}")
        return None

    if response.status_code != 200:
        print(f"Failed to fetch {link}: status {response.status_code}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 데이터 기본값 설정 (찾지 못하는 경우 빈 값으로 남김)
    data = {
        "name": "",
        "image": "",
        "hangul": "",
        "romanization": "",
        "katakana": "",
        "origin": "",
        "genres": "",
        "debut": "",
        "disbanded": "",
        "years_active": "",
        "label": "",
        "associated": "",
        "members_current": [],
        "members_former": [],
        "website": [],
        "sns": [],
        "fandom": "",
        "colors": "",
        "related": "",
        "other_names": ""
    }
    
    # infobox 찾기
    infobox = soup.find("aside", class_="portable-infobox")
    if not infobox:
        print("Infobox not found")
        return data

    # 그룹명: infobox 상단의 h2[data-source="name"]
    name_tag = infobox.find("h2", {"data-source": "name"})
    if name_tag:
        data["name"] = name_tag.get_text(strip=True)
    
    # 대표 이미지: figure[data-source="image"] 내부의 img 태그
    image_container = infobox.find("figure", {"data-source": "image"})
    if image_container:
        img_tag = image_container.find("img")
        if img_tag:
            data["image"] = img_tag.get("src", "")
    
    # infobox 내부의 모든 data-source 요소 순회
    for element in infobox.find_all(attrs={"data-source": True}):
        source = element.get("data-source").strip().lower()
        # 이미 처리한 name, image는 건너뜁니다.
        if source in ["name", "image"]:
            continue

        # 기본 텍스트 데이터 추출: hangul, origin, genres, debut, disbanded, years, label, associated,
        # roman/romanization, katakana, fandom, colors, 기타(other, formerly)
        if source in ["hangul", "origin", "genres", "debut", "disbanded", "years", "label", "associated", "roman", "romanization", "katakana", "fandom", "colors", "other", "formerly"]:
            value_container = element.find("div", class_="pi-data-value")
            value = extract_value(value_container) if value_container else ""
            if source == "years":
                data["years_active"] = value
            elif source in ["roman", "romanization"]:
                data["romanization"] = value
            elif source in ["other", "formerly"]:
                data["other_names"] = value
            else:
                # key 이름과 data 딕셔너리의 키가 일치하는 경우에만 저장(예: hangul, origin, genres, etc.)
                data[source] = value

        # Members: current, former
        elif source in ["current", "former"]:
            value_container = element.find("div", class_="pi-data-value")
            value = extract_value(value_container) if value_container else ""
            if source == "current":
                if isinstance(value, list):
                    data["members_current"] = value
                else:
                    data["members_current"] = [value] if value else []
            else:
                if isinstance(value, list):
                    data["members_former"] = value
                else:
                    data["members_former"] = [value] if value else []

        # Website: 링크 추출
        elif source == "website":
            links = extract_links(element)
            data["website"] = links

        # SNS: 링크 추출
        elif source == "sns":
            links = extract_links(element)
            data["sns"] = links

        # Related Wikis: p 태그의 텍스트
        elif source == "related":
            p_tag = element.find("p")
            data["related"] = p_tag.get_text(separator=" ", strip=True) if p_tag else ""
    
    return data