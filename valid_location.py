import pandas as pd

# 1. include_xy.csv 불러오기
df = pd.read_csv('먹거리.csv', encoding='utf-8-sig')

# 2. 좌표(x 또는 y)가 없는 행 필터링
failed_rows = df[df['x'].isna() | df['y'].isna()]
valid_rows = df.dropna(subset=['x', 'y'])

# 3. 좌표 못 찾은 행 저장
failed_rows.to_csv('failed_addresses.csv', encoding='utf-8-sig', index=False)
print(f"총 {len(failed_rows)}개 좌표 못 찾은 행 → failed_addresses.csv로 저장 완료.")

# 4. 좌표 있는 데이터만 다시 저장 (덮어쓰기)
valid_rows.to_csv('include_xy.csv', encoding='utf-8-sig', index=False)
print(f"좌표가 있는 {len(valid_rows)}개 행만 include_xy.csv에 저장되었습니다.")