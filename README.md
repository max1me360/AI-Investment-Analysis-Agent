# AI Investment Analysis Agent

A conversational financial analyst powered by Claude that reasons over live market data instead of inventing it. The agent runs an autonomous tool calling loop: it interprets a question posed in plain language, decides what information it actually needs, and reaches for the right function to retrieve fundamentals, price history, or the current portfolio before forming a conclusion. Every figure it cites originates from real market data pulled through yfinance, so the analysis stays grounded rather than fabricated.

Three composable tools give the model its senses. The first inspects a company's fundamentals and valuation, the second characterizes recent price behavior and volatility, and the third evaluates existing holdings to surface gains, losses, and overall exposure. A carefully framed system prompt keeps the reasoning structured and quantified, while the architecture stays deliberately extensible: introducing a screener, a news feed, or scheduled alerts amounts to writing one additional function.

## What it does

Analyzes a single stock across fundamentals, valuation, and recent price action. Tracks a portfolio and computes real time gains, losses, and overall exposure. Compares and screens multiple tickers against your own criteria, all through natural language.

## Tech stack

Python, Anthropic Claude API, yfinance.

## Getting started

Install the dependencies:

```bash
python3 -m pip install anthropic yfinance
```

Set your Anthropic API key (created at https://console.anthropic.com):

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

Edit the `PORTEFEUILLE` dictionary in `agent_bourse.py` with your own positions, then launch the agent:

```bash
python3 agent_bourse.py
```

Ask questions in plain language, for example `Analyse l'action LVMH (MC.PA)`, `Comment se porte mon portefeuille ?`, or `Compare Apple, Microsoft and Nvidia over one year`.

## How it works

The agent loop sends your question to Claude with a set of tool definitions. When the model decides it needs data, it returns a tool call, the corresponding Python function runs and fetches live figures through yfinance, and the result is fed back into the conversation. The loop repeats until the model has enough grounding to answer, then returns a structured analysis.

## Disclaimer

This project is intended for educational purposes and does not constitute financial or investment advice. Market data may be delayed or incomplete, and every decision remains your own.
