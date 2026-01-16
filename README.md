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

- **UI:** https://market.ai-coach-lab.com  
- **API Docs (Swagger):** https://market-api.ai-coach-lab.com/docs  
- **Health Check:** https://market-api.ai-coach-lab.com/health  

## 🎯 Purpose of the Project

Most beginners can look up a stock price — but struggle to understand what returns, volatility, and drawdown *mean*.  
AI Market Coach bridges that gap by combining:

- market data retrieval (`yfinance`)
- analytics (returns, volatility, max drawdown)
- optional AI-powered teaching explanations (Ollama)

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

- **UI Web App:** Streamlit (public website) → `market.ai-coach-lab.com`  
- **API Web App:** FastAPI (public API, called by UI) → `market-api.ai-coach-lab.com`

Cloudflare provides DNS (CNAME), and Azure provides **custom domain + SSL** on App Service.

### 🏗️ SYSTEM ARCHITECTURE (Production Diagram)

> ✅ Copy/paste this Mermaid diagram into GitHub README (renders automatically if Mermaid is enabled).  
> 🖼️ If you prefer an image diagram, export it later as `docs/architecture-prod.png`.

```mermaid
flowchart LR
  U["User (Browser)"] --> UI["Streamlit UI<br/>market.ai-coach-lab.com<br/>(Azure App Service: UI)"]
  CF["Cloudflare DNS<br/>(CNAME)"] --> UI
  UI -->|HTTPS JSON| API["FastAPI API<br/>market-api.ai-coach-lab.com<br/>(Azure App Service: API)"]
  API --> YF["Market Data Provider<br/>(yfinance)"]
  API --> AN["Analytics Engine<br/>(returns, volatility, drawdown)"]
  API --> LLM["LLM Coach (optional)<br/>(Ollama)"]
  API --> HC["Health Endpoint<br/>(/health)"]
