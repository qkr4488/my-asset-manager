# 내 자산 관리자 (My Asset Manager)

가계부 + 적금/예금 복리 계산 + 주식 포트폴리오 + 자산 관리 + 일정/목표를 한 곳에서 관리하는 Windows 프로그램입니다.

## 주요 기능

- **📊 대시보드**: 총 자산, 이번 달 수입/지출, 오늘과 내일의 일정을 한눈에 확인
- **💳 가계부**: 수입/지출을 카테고리별로 기록하고 월별 합계 확인
- **🏦 적금/예금**: 월/분기/반기/연 복리 계산, 세후 만기 금액 자동 산출
- **📈 주식**: 보유 종목 관리, yfinance API로 실시간 가격 업데이트 (수동 입력도 지원)
- **🏠 기타 자산**: 현금, 부동산, 암호화폐 등을 자유롭게 등록
- **📅 일정/목표**: 날짜별 To-Do, 우선순위 관리, 완료 체크

데이터는 사용자 홈 폴더의 `MyAssetManager/asset_manager.db`에 SQLite로 저장됩니다. .exe로 빌드한 뒤에도 데이터가 그대로 유지됩니다.

## 1) 빠르게 실행하기 (Python 설치된 경우)

Python 3.10+ 가 설치되어 있어야 합니다. ([python.org](https://www.python.org/downloads/)에서 설치 시 "Add Python to PATH" 체크 권장)

```cmd
pip install -r requirements.txt
python app.py
```

또는 `run.bat`을 더블클릭하세요.

## 2) Windows .exe 파일로 빌드하기

`build.bat`을 더블클릭하거나 명령 프롬프트에서 실행하세요.

```cmd
build.bat
```

빌드가 끝나면 `dist\MyAssetManager.exe`가 만들어집니다. 이 파일 하나만 있으면 Python 없이도 어디서든 실행할 수 있습니다.

수동으로 빌드하려면:

```cmd
pip install pyinstaller yfinance
pyinstaller --onefile --windowed --name MyAssetManager --hidden-import=yfinance app.py
```

> ⚠️ PyInstaller는 빌드를 **실행한 OS에서 동작하는 실행파일**을 만듭니다. .exe(Windows용)는 반드시 **Windows에서** 빌드해야 합니다.

## 한국 주식 티커 형식

yfinance는 한국 주식의 경우 종목코드 뒤에 거래소 접미사를 붙여야 합니다.

- 코스피: `005930.KS` (삼성전자), `035420.KS` (NAVER)
- 코스닥: `035720.KQ` (카카오게임즈 등)
- 미국 주식: 그대로 사용 - `AAPL`, `TSLA`, `NVDA`

## 복리 계산 방식

### 예금 (거치식)
```
만기금액 = 원금 × (1 + r/n)^(n×t)
```
- r: 연이율, n: 연 복리 횟수, t: 기간(년)

### 적금 (월 납입식)
각 회차 납입금에 남은 기간만큼의 복리를 적용해 합산합니다.

### 이자소득세
기본 15.4% (이자소득세 14% + 지방소득세 1.4%)로 설정되어 있으며, 입력 폼에서 변경할 수 있습니다.

## 파일 구조

```
app.py             - 메인 GUI 애플리케이션
database.py        - SQLite 데이터베이스 모듈
finance.py         - 복리 계산 및 주식 가격 조회
requirements.txt   - 의존성 목록
build.bat          - .exe 빌드 스크립트
run.bat            - 빠른 실행 스크립트
```

## 문제 해결

- **한글이 깨져 보여요**: Windows 기본 폰트인 'Malgun Gothic'을 사용합니다. 시스템에 이 폰트가 없으면 다른 폰트로 자동 대체됩니다.
- **yfinance가 가격을 못 가져와요**: 네트워크 연결을 확인하고, 티커가 정확한지 확인하세요. 그래도 안 되면 "수동 가격 변경" 버튼으로 직접 입력할 수 있습니다.
- **빌드한 .exe에서 yfinance 오류**: `build.bat`은 이미 `--hidden-import=yfinance`를 포함하고 있습니다. 그래도 문제가 있으면 `--collect-all yfinance` 옵션을 추가하세요.
