import asyncio
from playwright.async_api import async_playwright
import json
import re

# ================= 테스트용 설정 =================
# 현재 돌리고 계신 5600~5800페이지 근처 아무 페이지나 넣어서 테스트해보세요.
TEST_PAGE = 1 
START_DATE = "20260129"
END_DATE = "20260130"
KEYWORD = f"RD=[{START_DATE}~{END_DATE}]"

# 테스트용 파일명 
TEST_DATA_FILE = "test_result.jsonl"
# ===============================================

async def run_test():
    async with async_playwright() as p:
        # 헤드리스 해제 (눈으로 직접 확인)
        browser = await p.chromium.launch(headless=False, args=["--start-maximized"])
        context = await browser.new_context(no_viewport=True)
        page = await context.new_page()
        page.on("dialog", lambda dialog: dialog.accept())

        try:
            print(f"🔬 {TEST_PAGE}페이지 테스트 수집 시작...")
            await page.goto("https://www.kipris.or.kr/khome/search/searchResult.do?tab=trademark", wait_until="networkidle")
            
            # 검색어 입력
            await page.fill("#sd010301_g04_text", KEYWORD)
            await page.keyboard.press("Enter")
            await asyncio.sleep(5)

            # 테스트 페이지로 점프
            await page.fill("#srchRsltPagingNum", str(TEST_PAGE))
            await page.click("button.btn-jump")
            await asyncio.sleep(8)

            print(f"🔎 {TEST_PAGE}페이지 데이터 추출 중...")
            await page.wait_for_selector("article.result_item", timeout=30000)
            
            items = page.locator("article.result_item")
            count = await items.count()
            
            test_results = []
            for i in range(count):
                item = items.nth(i)
                try:
                    title = (await item.locator("h1.title button.link.under").first.inner_text(timeout=3000)).strip()
                    reg_num = (await item.locator(".head-title button.tit").first.inner_text(timeout=3000)).strip()
                    
                    # [핵심 검수 대상] 출원인 & 최종권리자
                    applicant_el = item.locator("li:has-text('출원인') button.link").first
                    applicant = (await applicant_el.inner_text(timeout=2000)).strip() if await applicant_el.count() > 0 else "N/A"
                    
                    owner_el = item.locator("li:has-text('최종권리자') button.link").first
                    owner = (await owner_el.inner_text(timeout=2000)).strip() if await owner_el.count() > 0 else "N/A"

                    res = {"title": title, "reg_num": reg_num, "applicant": applicant, "owner": owner, "page": TEST_PAGE}
                    test_results.append(res)
                    print(f"✅ {i+1}번: {title[:10]}... | 권리자: {owner}")
                except:
                    continue

            # 파일 저장
            with open(TEST_DATA_FILE, "w", encoding="utf-8") as f:
                for r in test_results:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
            
            print(f"\n✨ 테스트 완료! {len(test_results)}건이 '{TEST_DATA_FILE}'에 저장되었습니다.")

        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run_test())