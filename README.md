# Semiconductor News AI Agent

반도체 산업 뉴스를 자동으로 수집하고 AI로 분석하기 위해 개발한
Python 기반 뉴스 분석 Agent입니다.

## 개발 목적
반도체 산업의 기술 변화를 지속적으로 파악하는 과정에서
반복적으로 발생하는 뉴스 수집과 분석 업무를 자동화하고자 개발했습니다.

## 주요 기능
- 공개 RSS 기반 반도체 뉴스 자동 수집
- HBM, DRAM, EUV, Foundry, Packaging 등 주요 키워드 필터링
- Gemini API 기반 핵심 내용 및 산업적 의미 분석
- 분석 결과 이메일 자동 발송
- GitHub Actions 기반 정기 실행

## Process
RSS 뉴스 수집
→ 키워드 기반 뉴스 선별
→ Gemini API 분석
→ 핵심 내용 및 산업적 의미 요약
→ 이메일 자동 발송

## Tech Stack
- Python
- Gemini API
- Feedparser
- GitHub Actions
- Gmail SMTP

## 데이터 활용 기준
기사 전문을 저장하거나 재배포하지 않고,
공개 RSS에서 제공되는 제목·요약·출처·원문 링크를 활용했습니다.
