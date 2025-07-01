import time
import pandas as pd
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# 1. 셀레니움 드라이버 설정
options = Options()
options.add_argument('--headless')  # 창 숨김
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-blink-features=AutomationControlled')
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# 2. 검색어 목록 불러오기
df = pd.read_csv("detail_final.csv")
store_names = df['store_name'].tolist()

# 3. 결과 저장 리스트
results = []
now = datetime.now().strftime("%Y%m%d_%H%M")

for i, keyword in enumerate(store_names):
    try:
        # 카카오맵 접속 및 검색
        driver.get("https://map.kakao.com")
        time.sleep(0.5)
        search_input = driver.find_element(By.ID, "search.keyword.query")
        search_input.clear()
        search_input.send_keys(keyword)
        
        # dimmedLayer 제거 (검색 버튼 클릭 전)
        try:
            driver.execute_script("document.getElementById('dimmedLayer')?.remove();")
        except:
            pass
        
        driver.find_element(By.ID, "search.keyword.submit").click()
        time.sleep(0.5)

        # 검색 결과 목록 가져오기
        place_items = driver.find_elements(By.CSS_SELECTOR, "#info\\.search\\.place\\.list li.PlaceItem")
        
        # 정확한 제목 매칭을 위한 변수
        matched_item = None
        exact_match_found = False
        
        # 목록을 순회하면서 정확한 제목 찾기
        for item in place_items:
            try:
                title_element = item.find_element(By.CSS_SELECTOR, "a.link_name")
                title = title_element.get_attribute("title")
                
                # 정확한 제목 매칭 확인
                if title.strip() == keyword.strip():
                    matched_item = item
                    exact_match_found = True
                    print(f" 정확한 매칭 발견: {keyword} → {title}")
                    break
                    
            except Exception as e:
                continue
        
        # 정확한 매칭이 없으면 첫 번째 결과 사용
        if not exact_match_found:
            if place_items:
                matched_item = place_items[0]
                title = matched_item.find_element(By.CSS_SELECTOR, "a.link_name").get_attribute("title")
                print(f" 정확한 매칭 없음, 첫 번째 결과 사용: {keyword} → {title}")
            else:
                raise Exception("검색 결과가 없습니다")

        # 매칭된 아이템에서 정보 수집 (matched_item이 None이 아닌 경우에만)
        if matched_item is not None:
            title = matched_item.find_element(By.CSS_SELECTOR, "a.link_name").get_attribute("title")
            address = matched_item.find_element(By.CSS_SELECTOR, "div.addr p").get_attribute("title")
            subcategory = matched_item.find_element(By.CSS_SELECTOR, "span.subcategory").text

            try:
                rating = matched_item.find_element(By.CSS_SELECTOR, "em.num").text
            except:
                rating = ""

            try:
                moreview_link = matched_item.find_element(By.CSS_SELECTOR, "a.moreview").get_attribute("href")
                place_id = moreview_link.strip().split('/')[-1]
            except:
                place_id = ""
        else:
            # matched_item이 None인 경우 빈 값으로 설정
            title = ""
            address = ""
            subcategory = ""
            rating = ""
            place_id = ""

        # 검색어 column 추가
        results.append([keyword, place_id, title, address, rating, subcategory])
        print(f" {keyword} → {title}")
            
    except Exception as e:
        print(f" {keyword} → Error: {e}")
        results.append([keyword, "", "", "", "", ""])

# 4. 모든 결과 저장
if results:
    output_df = pd.DataFrame(results, columns=["검색어", "ID", "상점명", "주소", "별점", "업종"])
    output_filename = f"{now}.csv"
    output_df.to_csv(output_filename, index=False, encoding="utf-8-sig")
    print(f"\n 저장 완료: {output_filename} (총 {len(results)}개)")

driver.quit()
