##### crawler\boy_group_crawler.py #####
import requests
from bs4 import BeautifulSoup

def groups_from_urls(urls, gender = "male"):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }
    all_groups = []
    
    for url in urls:
        print("Processing URL:", url)
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print("페이지를 불러오지 못했습니다. 상태 코드:", response.status_code)
            continue
        
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.find("title").text
        print("페이지 제목:", title)
        
        members_div = soup.find("div", class_="category-page__members")
        if not members_div:
            print("멤버 목록을 찾지 못했습니다.")
            continue
        
        wrappers = members_div.find_all("div", class_="category-page__members-wrapper")
        for wrapper in wrappers:
            ul = wrapper.find("ul", class_="category-page__members-for-char")
            if not ul:
                continue
            lis = ul.find_all("li", class_="category-page__member")
            for li in lis:
                a_tag = li.find("a", class_="category-page__member-link")
                if a_tag:
                    group_name = a_tag.get_text(strip=True)
                    link = a_tag.get("href")
                    if link.startswith("/"):
                        link = "https://kpop.fandom.com" + link
                    all_groups.append({
                        "group_name": group_name, 
                        "link": link, 
                        "type": "group", 
                        "gender": gender
                    })
    return all_groups