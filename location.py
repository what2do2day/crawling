import requests
import pandas as pd
import time
import json

# Kakao API 호출 함수
def get_location(address):
    url = f"https://dapi.kakao.com/v2/local/search/address.json?query={address}"
    headers = {"Authorization": "KakaoAK ??????????????"}  
    response = requests.get(url, headers=headers)

    print(f"[요청 주소] {address}")
    print(f"[응답 코드] {response.status_code}")

    try:
        data = response.json()
        print(f"[응답 내용] {json.dumps(data, ensure_ascii=False)}")
        return data
    except Exception as e:
        print(f"[JSON 파싱 실패] {e}")
        return {}

# 위경도 추출 함수
def result_location(i):
    try:
        address = df.loc[i, '주소']
        api_json = get_location(address)
        documents = api_json.get('documents', [])

        if documents:
            df.loc[i, 'x'] = documents[0]['x']  # 경도
            df.loc[i, 'y'] = documents[0]['y']  # 위도
            print(f"[{i}] 변환 완료: x={df.loc[i, 'x']}, y={df.loc[i, 'y']}")
        else:
            df.loc[i, 'x'] = None
            df.loc[i, 'y'] = None
            print(f"[{i}] 좌표 없음 - 주소: {address}")
    except Exception as e:
        print(f"[{i}] 예외 발생: {e}")

# 1. CSV 파일 로드
df = pd.read_csv('detail_final.csv', encoding='utf-8')

# 2. 좌표 컬럼 초기화
df['x'] = None
df['y'] = None

# 3. 주소 → 좌표 변환 루프
i = 0
while i < len(df):
    try:
        result_location(i)
        i += 1
    except Exception as e:
        print(f"[{i}] 오류 발생: {e}")
        print("0.5초 후 재시도...")
        time.sleep(0.5)

# 4. 결과 저장
df.to_csv('include_xy.csv', encoding='utf-8-sig', index=False)
print("CSV 저장 완료: include_xy.csv")
