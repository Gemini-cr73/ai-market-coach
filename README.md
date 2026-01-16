# 📈 AI Market Coach

<p align="center">
  <img src="https://img.shields.io/badge/Status-Live-brightgreen?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Cloud-Azure_App_Service-0078D4?style=for-the-badge&logo=microsoftazure" />
  <img src="https://img.shields.io/badge/API-FastAPI-009688?style=for-the-badge&logo=fastapi" />
  <img src="https://img.shields.io/badge/UI-Streamlit-FF4B4B?style=for-the-badge&logo=streamlit" />
  <img src="https://img.shields.io/badge/Containers-Docker-2496ED?style=for-the-badge&logo=docker" />
  <img src="https://img.shields.io/badge/LLM-Ollama_(Optional)-000000?style=for-the-badge&logo=ollama" />
</p>

**Educational-only stock learning and analytics assistant.**  
AI Market Coach helps users learn market concepts by turning raw market data into clear metrics + plain-English explanations + practice prompts.

> ⚠️ **Disclaimer:** This project is for educational purposes only and does not provide financial, trading, or investment advice.

## 🌐 Live Links (Production)
- **UI:** `https://<ui-domain>`
- **API Docs (Swagger):** `https://<api-domain>/docs`
- **Health Check:** `https://<api-domain>/health`

> Replace the placeholders with your real domains.

## 🎯 Purpose of the Project
Most beginners can look up a stock price — but struggle to understand what returns, volatility, and drawdown *mean*.  
AI Market Coach bridges that gap by combining:
- market data retrieval,
- analytics,
- and AI-powered teaching explanations (Ollama optional).

## ✅ Application Features

| Category | Feature | Description |
|---|---|---|
| Market Data | Historical price pull | Fetches OHLC/time-series data (ex: via `yfinance`) |
| Analytics | Core metrics | Returns %, volatility, max drawdown, trend summary |
| Learning | “Market Coach” explanations | Plain-English educational explanation for metrics |
| Learning | Practice prompts / quiz mode | Reinforces learning with questions & flashcards |
| Platform | UI + API separation | Streamlit UI calls FastAPI backend over HTTPS |
| Deployment | Production-ready | Dockerized and deployed to Azure App Service |

## 🧠 System Architecture

### Architecture Overview (Production)
You have **two Azure App Services** (two containers):
- **UI Web App**: Streamlit (public website)
- **API Web App**: FastAPI (public API, called by UI)

Cloudflare provides DNS (CNAME), and Azure provides **custom domain + SSL** on App Service.

### 🏗️ SYSTEM ARCHITECTURE (Diagram)

> ✅ Copy/paste this Mermaid diagram into GitHub README (it will render automatically if Mermaid is enabled).
> If you prefer an image diagram, export it later as `docs/architecture.png`.

```mermaid
flowchart LR
  U[User Browser] -->|HTTPS| UI[Streamlit UI Web App]
  CF[Cloudflare DNS (CNAME)] --> UI

  UI -->|HTTPS JSON| API[FastAPI API Web App]
  API --> MD[Market Data: yfinance / provider]
  API --> AE[Analytics Engine: returns / volatility / drawdown]
  API --> LLM[LLM Coach (optional): Ollama]

  API --> HC[/health endpoint/]
