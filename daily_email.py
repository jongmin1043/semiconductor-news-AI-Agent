import os
import smtplib
import feedparser

from google import genai
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone, timedelta


RSS_FEEDS = [
    {
        "name": "Semiconductor Engineering",
        "url": "https://semiengineering.com/feed/"
    },
    {
        "name": "SemiWiki",
        "url": "https://semiwiki.com/feed/"
    },
    {
        "name": "EE Times",
        "url": "https://www.eetimes.com/feed/"
    }
]


KEYWORDS = [
    "HBM", "DRAM", "NAND",
    "Samsung", "SK hynix", "SK Hynix",
    "TSMC", "NVIDIA", "ASML",
    "EUV", "Packaging", "Foundry",
    "AI", "Memory", "Chiplet",
    "CoWoS", "Wafer", "Fab",
    "Semiconductor", "GPU", "Advanced Packaging"
]


def get_env(name):
    value = os.getenv(name)

    if not value:
        raise ValueError(f"환경변수 {name}이 설정되지 않았습니다.")

    return value


def clean_text(text):
    if not text:
        return ""

    return " ".join(
        str(text)
        .replace("\n", " ")
        .replace("\r", " ")
        .split()
    )


def collect_news(max_items=10):
    collected = []

    for feed_info in RSS_FEEDS:
        source = feed_info["name"]
        url = feed_info["url"]

        print(f"RSS 수집 중: {source}")

        feed = feedparser.parse(url)

        for entry in feed.entries:
            title = clean_text(entry.get("title", ""))

            summary = clean_text(
                entry.get("summary", "")
                or entry.get("description", "")
            )

            link = entry.get("link", "")
            published = entry.get("published", "")

            text = f"{title} {summary}".lower()

            if any(keyword.lower() in text for keyword in KEYWORDS):
                collected.append({
                    "source": source,
                    "title": title,
                    "summary": summary[:500],
                    "link": link,
                    "published": published
                })

    unique_news = []
    seen_links = set()

    for item in collected:
        link = item["link"]

        if link and link not in seen_links:
            unique_news.append(item)
            seen_links.add(link)

    return unique_news[:max_items]


def make_news_text(news_items):
    if not news_items:
        return "오늘 수집된 반도체 관련 RSS 뉴스가 없습니다."

    lines = []

    for idx, item in enumerate(news_items, start=1):
        lines.append(f"{idx}. 제목: {item['title']}")
        lines.append(f"출처: {item['source']}")
        lines.append(f"RSS 요약: {item['summary']}")
        lines.append(f"발행일: {item['published']}")
        lines.append(f"원문 링크: {item['link']}")
        lines.append("")

    return "\n".join(lines)


def summarize_with_gemini(news_text):
    gemini_api_key = get_env("GEMINIAPIKEY")

    client = genai.Client(api_key=gemini_api_key)

    # 너무 긴 입력 방지
    news_text = news_text[:12000]

    prompt = f"""
너는 반도체 산업 분석가다.

아래 RSS 뉴스 정보를 바탕으로 한국어 데일리 반도체 뉴스 요약 메일을 작성해라.

중요 조건:

- 기사 원문 전체를 복사하지 말 것
- RSS에 제공된 제목, 짧은 요약, 출처, 링크만 바탕으로 작성할 것
- 각 뉴스는 2~3문장 이내로 요약할 것
- 출처와 원문 링크를 반드시 포함할 것
- 원문에 없는 내용을 단정하지 말 것
- 과장된 표현을 쓰지 말 것
- 개인 학습용 데일리 브리핑 형식으로 작성할 것
- 마크다운 기호를 사용하지 말 것
- 별표(**), 샵(###), 구분선(---), 코드블록(```)을 사용하지 말 것
- 일반 텍스트 이메일처럼 깔끔하게 작성할 것
- 문장은 너무 길게 쓰지 말고 읽기 쉽게 끊을 것
- HBM, DRAM, NAND, Foundry, EUV, Packaging, NVIDIA, TSMC, Samsung, SK hynix 관련 이슈를 우선적으로 설명할 것

출력 형식:

[오늘의 반도체 뉴스 요약]

오늘의 핵심 흐름:
오늘 수집된 뉴스에서 보이는 반도체 산업 흐름을 2~3문장으로 요약한다.

주요 뉴스

1. 제목:
   출처:
   핵심 요약:
   산업적 의미:
   원문 링크:

2. 제목:
   출처:
   핵심 요약:
   산업적 의미:
   원문 링크:

마무리 코멘트:
오늘 뉴스가 반도체 산업에서 어떤 흐름을 보여주는지 1~2문장으로 정리한다.

뉴스 데이터:
{news_text}
"""

    max_retries = 3

    for attempt in range(max_retries):
        try:
            print(f"Gemini 호출 시도 {attempt + 1}/{max_retries}")

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )

            if response.text:
                return response.text.strip()

            raise ValueError("Gemini 응답이 비어 있습니다.")

        except Exception as e:
            print(f"Gemini 호출 실패: {e}")

            if attempt < max_retries - 1:
                wait_seconds = 5 * (attempt + 1)
                print(f"{wait_seconds}초 후 다시 시도합니다.")
                time.sleep(wait_seconds)

    # Gemini가 끝까지 실패해도 workflow는 죽이지 않음
    return (
        "[오늘의 반도체 뉴스 요약]\n\n"
        "Gemini AI 요약을 일시적으로 생성하지 못했습니다.\n"
        "아래는 오늘 수집된 RSS 뉴스입니다.\n\n"
        + news_text
    )

def send_email(subject, body):
    gmail_address = get_env("GMAILADDRESS")
    gmail_app_password = get_env("GMAILAPPPASSWORD")
    to_email = get_env("TOEMAIL")

    msg = MIMEMultipart()
    msg["From"] = gmail_address
    msg["To"] = to_email
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain", "utf-8"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(gmail_address, gmail_app_password)
        server.send_message(msg)


def main():
    kst = timezone(timedelta(hours=9))
    today = datetime.now(kst).strftime("%Y-%m-%d")

    news_items = collect_news(max_items=10)
    news_text = make_news_text(news_items)

    if not news_items:
        final_body = "[오늘의 반도체 뉴스 요약]\n\n오늘 수집된 반도체 관련 RSS 뉴스가 없습니다."
    else:
        final_body = summarize_with_gemini(news_text)

    subject = f"[반도체 뉴스 요약] {today}"

    send_email(subject, final_body)

    print("메일 발송 완료")


if __name__ == "__main__":
    main()
