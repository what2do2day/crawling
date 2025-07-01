import pandas as pd
import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class KakaoMapCrawler:
    def __init__(self):
        self.driver = None
        self.wait = None

    def setup_driver(self):
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.maximize_window()
        self.wait = WebDriverWait(self.driver, 15)
        logger.info("Chrome 드라이버 설정 완료")

    def remove_dimmed_layer(self):
        try:
            self.driver.execute_script("document.getElementById('dimmedLayer')?.remove();")
            logger.info("dimmedLayer 제거 완료")
        except:
            pass

    def search_store(self, store_name):
        try:
            logger.info("카카오맵 접속 중...")
            self.driver.get("https://map.kakao.com")
            time.sleep(1)

            search_input = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "input#search\\.keyword\\.query"))
            )
            search_input.clear()
            search_input.send_keys(store_name)
            search_input.send_keys(Keys.ENTER)
            time.sleep(1.5)

            logger.info(f"'{store_name}' 검색 완료")
            return True
        except Exception as e:
            logger.error(f"'{store_name}' 검색 실패: {e}")
            return False

    def click_detail_view(self):
        try:
            time.sleep(1)
            self.remove_dimmed_layer()
            detail_selector = "#info\\.search\\.place\\.list > li > div.info_item > div.contact.clickArea > a.moreview"
            logger.info(f"상세보기 버튼 탐색 시도: {detail_selector}")

            link = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, detail_selector))
            )
            original_window = self.driver.current_window_handle
            link.click()
            logger.info("상세보기 클릭 완료, 새 탭 열림 대기")

            WebDriverWait(self.driver, 10).until(lambda d: len(d.window_handles) > 1)

            for handle in self.driver.window_handles:
                if handle != original_window:
                    self.driver.switch_to.window(handle)
                    logger.info("새 탭(상세 페이지)로 전환 완료")
                    break

            time.sleep(2)
            return True

        except Exception as e:
            logger.error(f"상세보기 클릭 실패: {e}")
            return False

    def extract_place_info(self, store_name):
        try:
            logger.info("상세보기 페이지 진입 완료 — 정보 추출 시작")

            current_url = self.driver.current_url
            logger.info(f"현재 URL: {current_url}")

            place_id = current_url.split("/")[-1].split("#")[0]
            logger.info(f"추출한 placeId: {place_id}")

            spans = self.driver.find_elements(By.CSS_SELECTOR, "span.txt_detail")
            logger.info(f"발견된 span.txt_detail 요소 개수: {len(spans)}")

            address = "주소 정보 없음"
            for i, span in enumerate(spans, 1):
                text = span.text.strip()
                logger.info(f"[{i}] span 내용: {text}")
                if "서울" in text:
                    address = text
                    logger.info(f"선택된 주소: {address}")
                    break

            logger.info(f"장소 정보 추출 완료 — 이름: {store_name}, 주소: {address}, placeId: {place_id}")

            return {
                'store_name': store_name,
                'address': address,
                'place_id': place_id
            }

        except Exception as e:
            logger.error(f"장소 정보 추출 실패: {e}")
            return None

    def click_more_button_if_exists(self, review_item):
        """
        개별 리뷰 아이템에서 더보기 버튼이 있는지 확인하고 클릭
        """
        try:
            # 리뷰 텍스트에 '...'이 있는지 먼저 확인
            review_text_element = review_item.find_element(By.CSS_SELECTOR, "div.review_detail div.wrap_review a p")
            review_text = review_text_element.text.strip()
            
            if '...' not in review_text:
                logger.debug("더보기가 필요없는 리뷰입니다.")
                return False
            
            # 더보기 버튼 찾기 (여러 가능한 셀렉터 시도)
            more_button_selectors = [
                "span.btn_more",  # 기본 더보기 버튼
                "div.review_detail div.wrap_review a p span.btn_more",  # 상세 경로
                ".btn_more"  # 간단한 클래스 셀렉터
            ]
            
            more_button = None
            for selector in more_button_selectors:
                try:
                    more_button = review_item.find_element(By.CSS_SELECTOR, selector)
                    if more_button and more_button.text.strip() == "더보기":
                        logger.info(f"더보기 버튼 발견: {selector}")
                        break
                except:
                    continue
            
            if more_button:
                # 더보기 버튼이 클릭 가능한 상태인지 확인
                if more_button.is_displayed() and more_button.is_enabled():
                    # 스크롤하여 버튼이 보이도록 조정
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", more_button)
                    time.sleep(0.5)
                    
                    # 더보기 버튼 클릭
                    more_button.click()
                    logger.info("더보기 버튼 클릭 완료")
                    time.sleep(0.5)  # 텍스트 로딩 대기
                    return True
                else:
                    logger.debug("더보기 버튼이 클릭 가능한 상태가 아닙니다.")
                    return False
            else:
                logger.debug("더보기 버튼을 찾을 수 없습니다.")
                return False
                
        except Exception as e:
            logger.debug(f"더보기 버튼 처리 중 오류: {e}")
            return False

    def extract_reviews(self, store_name):
        reviews = []
        try:
            logger.info("후기 탭 클릭 시도")
            
            # 여러 가능한 후기 탭 셀렉터들을 시도
            review_tab_selectors = [
                "/html/body/div[2]/main/article/div[2]/div[1]/div/ul/li[4]/a",  # li[4] 시도
                "//a[contains(text(), '후기')]",  # 텍스트로 찾기
                "//li/a[contains(text(), '후기')]",  # li 안의 후기 링크
                "ul.list_menu li:nth-child(4) a",  # CSS 셀렉터로 4번째
                "ul.list_menu li:nth-child(5) a"   # CSS 셀렉터로 5번째 (혹시 순서가 다를 경우)
            ]
            
            review_tab_clicked = False
            for i, selector in enumerate(review_tab_selectors, 1):
                try:
                    logger.info(f"후기 탭 시도 {i}: {selector}")
                    
                    if selector.startswith("//") or selector.startswith("/html"):
                        # XPath 사용
                        element = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                    else:
                        # CSS 셀렉터 사용
                        element = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                    
                    element.click()
                    logger.info(f"후기 탭 클릭 완료 (방법 {i})")
                    review_tab_clicked = True
                    break
                    
                except Exception as e:
                    logger.debug(f"후기 탭 시도 {i} 실패: {e}")
                    continue
            
            if not review_tab_clicked:
                logger.error("모든 후기 탭 셀렉터 시도 실패")
                return []
                
            time.sleep(2)  # 후기 탭 로딩 대기

            # 스크롤하여 더 많은 리뷰 로드
            for scroll_round in range(3):
                self.driver.execute_script("window.scrollBy(0, 1000)")
                logger.info(f"스크롤 다운 {scroll_round + 1}회 완료")
                time.sleep(1)

            # 리뷰 컨테이너 찾기
            review_container_xpath = "/html/body/div[2]/main/article/div[2]/div[2]/div[2]/div[3]/ul"
            try:
                review_container = self.driver.find_element(By.XPATH, review_container_xpath)
                review_items = review_container.find_elements(By.TAG_NAME, "li")
                logger.info(f"리뷰 컨테이너에서 {len(review_items)}개 리뷰 아이템 발견")
            except:
                logger.warning("리뷰 컨테이너를 찾을 수 없어 대체 방법 사용")
                review_items = self.driver.find_elements(By.CSS_SELECTOR, "div.group_review ul li")
                logger.info(f"대체 방법으로 {len(review_items)}개 리뷰 아이템 발견")

            processed_reviews = 0
            for i, review_item in enumerate(review_items, 1):
                try:
                    logger.info(f"리뷰 {i} 처리 중...")
                    
                    # 더보기 버튼이 있는지 확인하고 클릭
                    more_clicked = self.click_more_button_if_exists(review_item)
                    if more_clicked:
                        logger.info(f"리뷰 {i}: 더보기 버튼 클릭 완료")
                        time.sleep(0.5)  # 텍스트 확장 대기
                    
                    # 리뷰 텍스트 추출 (여러 가능한 셀렉터 시도)
                    review_text_selectors = [
                        "div.review_detail div.wrap_review a p",
                        "div.area_review div.review_detail div.wrap_review a p",
                        ".wrap_review a p"
                    ]
                    
                    review_text = None
                    for selector in review_text_selectors:
                        try:
                            review_element = review_item.find_element(By.CSS_SELECTOR, selector)
                            review_text = review_element.text.strip()
                            if review_text:
                                break
                        except:
                            continue
                    
                    if review_text and len(review_text) > 3:
                        # 더보기 버튼 텍스트 제거 (혹시 포함되어 있을 경우)
                        review_text = review_text.replace("더보기", "").strip()
                        
                        reviews.append({
                            'store_name': store_name,
                            'review_text': review_text
                        })
                        processed_reviews += 1
                        logger.info(f"리뷰 {i} 추출 완료: {review_text[:50]}...")
                    else:
                        logger.warning(f"리뷰 {i}: 유효한 텍스트를 찾을 수 없음")
                        
                except Exception as e:
                    logger.error(f"리뷰 {i} 처리 중 오류: {e}")
                    continue

            logger.info(f"총 {processed_reviews}개 리뷰 추출 완료")
            return reviews

        except Exception as e:
            logger.error(f"리뷰 추출 실패: {e}")
            return []

    def crawl_from_csv(self, input_csv_path, detail_path="output/detail.csv", review_path="output/review.csv"):
        try:
            df = pd.read_csv(input_csv_path)

            if 'store_name' not in df.columns:
                logger.error("CSV 파일에 'store_name' 컬럼이 없습니다.")
                return

            store_names = df['store_name'].tolist()
            logger.info(f"총 {len(store_names)}개 가게 크롤링 시작")

            os.makedirs("output", exist_ok=True)
            self.setup_driver()

            detail_list = []
            review_list = []

            for i, store_name in enumerate(store_names, 1):
                logger.info(f"[{i}/{len(store_names)}] '{store_name}' 처리 중...")

                if not self.search_store(store_name):
                    continue

                if not self.click_detail_view():
                    continue

                place_info = self.extract_place_info(store_name)
                if place_info:
                    detail_list.append(place_info)

                    reviews = self.extract_reviews(store_name)
                    review_list.extend(reviews)

                # 상세 페이지 닫고 원래 창으로 복귀
                if len(self.driver.window_handles) > 1:
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[0])
                    logger.info("상세 페이지 탭 닫고 원래 창으로 복귀")

                time.sleep(1)

            pd.DataFrame(detail_list).to_csv(detail_path, index=False, encoding='utf-8-sig')
            pd.DataFrame(review_list).to_csv(review_path, index=False, encoding='utf-8-sig')

            logger.info(f"가게 정보 {len(detail_list)}개를 '{detail_path}'에 저장 완료")
            logger.info(f"리뷰 {len(review_list)}개를 '{review_path}'에 저장 완료")

        except Exception as e:
            logger.error(f"크롤링 실패: {e}")
            raise
        finally:
            if self.driver:
                self.driver.quit()

def main():
    input_file = "stores.csv"
    detail_file = "output/detail.csv"
    review_file = "output/review.csv"

    if not os.path.exists(input_file):
        logger.error(f"입력 파일 '{input_file}'이 존재하지 않습니다.")

    crawler = KakaoMapCrawler()

    try:
        crawler.crawl_from_csv(input_file, detail_file, review_file)
        print("\n크롤링 완료!")
        print(f"가게 정보: {detail_file}")
        print(f"리뷰: {review_file}")

    except Exception as e:
        logger.error(f"실행 중 오류 발생: {e}")

if __name__ == "__main__":
    main()