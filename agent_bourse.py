"""
Agent d'analyse financiere - version de depart
================================================
Un agent Claude qui peut :
  1. Analyser une action (fondamentaux + prix)
  2. Suivre un portefeuille (positions, gains/pertes)
  3. Screener / comparer plusieurs titres

Il fonctionne sur la boucle : Claude reflechit -> appelle un outil ->
lit le resultat -> recommence -> repond.

--------------------------------------------------------------------
INSTALLATION (une seule fois, dans un terminal) :
    pip install anthropic yfinance

CLE API (a recuperer sur https://console.anthropic.com) :
    export ANTHROPIC_API_KEY="sk-ant-..."      # Mac / Linux
    setx ANTHROPIC_API_KEY "sk-ant-..."        # Windows

LANCER :
    python agent_bourse.py
--------------------------------------------------------------------

AVERTISSEMENT : ceci est un outil pedagogique. Ce n'est pas un conseil
en investissement. Les donnees peuvent etre incompletes ou en retard.
"""

import json
import yfinance as yf
from anthropic import Anthropic

client = Anthropic()  # lit automatiquement ANTHROPIC_API_KEY
MODEL = "claude-sonnet-5"

# Ton portefeuille : ticker -> (quantite, prix d'achat moyen)
# A adapter avec tes vraies positions.
PORTEFEUILLE = {
    "AAPL": (10, 150.0),
    "MSFT": (5, 300.0),
}


# ====================================================================
# 1) LES OUTILS  (des fonctions Python que Claude peut appeler)
# ====================================================================

def get_stock_info(ticker: str) -> dict:
    """Fondamentaux + dernier prix d'une action."""
    t = yf.Ticker(ticker)
    info = t.info
    return {
        "ticker": ticker,
        "nom": info.get("longName"),
        "prix": info.get("currentPrice"),
        "devise": info.get("currency"),
        "capitalisation": info.get("marketCap"),
        "PER": info.get("trailingPE"),
        "PER_futur": info.get("forwardPE"),
        "rendement_dividende": info.get("dividendYield"),
        "marge_nette": info.get("profitMargins"),
        "croissance_CA": info.get("revenueGrowth"),
        "dette_sur_capitaux": info.get("debtToEquity"),
        "beta": info.get("beta"),
        "recommandation_analystes": info.get("recommendationKey"),
        "objectif_moyen": info.get("targetMeanPrice"),
        "secteur": info.get("sector"),
        "resume": info.get("longBusinessSummary"),
    }


def get_price_history(ticker: str, periode: str = "6mo") -> dict:
    """Historique de prix resume (perf + volatilite)."""
    hist = yf.Ticker(ticker).history(period=periode)
    if hist.empty:
        return {"erreur": f"Aucune donnee pour {ticker}"}
    debut = float(hist["Close"].iloc[0])
    fin = float(hist["Close"].iloc[-1])
    return {
        "ticker": ticker,
        "periode": periode,
        "prix_debut": round(debut, 2),
        "prix_fin": round(fin, 2),
        "performance_pct": round((fin - debut) / debut * 100, 2),
        "plus_haut": round(float(hist["High"].max()), 2),
        "plus_bas": round(float(hist["Low"].min()), 2),
        "volatilite_pct": round(float(hist["Close"].pct_change().std() * 100), 2),
    }


def analyser_portefeuille() -> dict:
    """Valeur actuelle et plus/moins-values du portefeuille."""
    lignes = []
    valeur_totale = 0.0
    cout_total = 0.0
    for ticker, (qte, prix_achat) in PORTEFEUILLE.items():
        prix = yf.Ticker(ticker).info.get("currentPrice")
        if prix is None:
            continue
        valeur = prix * qte
        cout = prix_achat * qte
        valeur_totale += valeur
        cout_total += cout
        lignes.append({
            "ticker": ticker,
            "quantite": qte,
            "prix_achat": prix_achat,
            "prix_actuel": round(prix, 2),
            "valeur": round(valeur, 2),
            "gain_perte": round(valeur - cout, 2),
            "gain_perte_pct": round((prix - prix_achat) / prix_achat * 100, 2),
        })
    return {
        "positions": lignes,
        "valeur_totale": round(valeur_totale, 2),
        "gain_perte_total": round(valeur_totale - cout_total, 2),
        "gain_perte_total_pct": round((valeur_totale - cout_total) / cout_total * 100, 2)
        if cout_total else 0,
    }


# Table de correspondance nom d'outil -> fonction
FONCTIONS = {
    "get_stock_info": get_stock_info,
    "get_price_history": get_price_history,
    "analyser_portefeuille": analyser_portefeuille,
}

# Description des outils au format attendu par l'API Claude
OUTILS = [
    {
        "name": "get_stock_info",
        "description": "Recupere les fondamentaux et le prix actuel d'une action a partir de son ticker (ex: AAPL, MC.PA).",
        "input_schema": {
            "type": "object",
            "properties": {"ticker": {"type": "string", "description": "Le symbole boursier"}},
            "required": ["ticker"],
        },
    },
    {
        "name": "get_price_history",
        "description": "Historique de prix resume : performance, plus haut/bas, volatilite.",
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string"},
                "periode": {"type": "string", "description": "1mo, 3mo, 6mo, 1y, 5y..."},
            },
            "required": ["ticker"],
        },
    },
    {
        "name": "analyser_portefeuille",
        "description": "Analyse le portefeuille de l'utilisateur : valeur actuelle et plus/moins-values.",
        "input_schema": {"type": "object", "properties": {}},
    },
]

SYSTEME = """Tu es un analyste financier rigoureux et pedagogue.
Utilise TOUJOURS les outils pour obtenir des chiffres reels avant de conclure.
Structure tes analyses : contexte, fondamentaux, valorisation, risques, synthese.
Explique les ratios en clair. Chiffre tes arguments.
Rappelle que ce n'est pas un conseil en investissement personnalise et que
l'utilisateur reste seul responsable de ses decisions."""


# ====================================================================
# 2) LA BOUCLE DE L'AGENT
# ====================================================================

def agent(question: str) -> str:
    messages = [{"role": "user", "content": question}]
    while True:
        reponse = client.messages.create(
            model=MODEL,
            max_tokens=2000,
            system=SYSTEME,
            tools=OUTILS,
            messages=messages,
        )
        messages.append({"role": "assistant", "content": reponse.content})

        if reponse.stop_reason != "tool_use":
            # Plus d'outil a appeler : on renvoie le texte final
            return "".join(b.text for b in reponse.content if b.type == "text")

        # Claude demande un ou plusieurs outils : on les execute
        resultats = []
        for bloc in reponse.content:
            if bloc.type == "tool_use":
                fn = FONCTIONS[bloc.name]
                try:
                    sortie = fn(**bloc.input)
                except Exception as e:
                    sortie = {"erreur": str(e)}
                resultats.append({
                    "type": "tool_result",
                    "tool_use_id": bloc.id,
                    "content": json.dumps(sortie, ensure_ascii=False),
                })
        messages.append({"role": "user", "content": resultats})


if __name__ == "__main__":
    print("Agent d'analyse financiere. Tape 'quit' pour sortir.\n")
    print("Exemples :")
    print("  - Analyse l'action LVMH (MC.PA)")
    print("  - Comment se porte mon portefeuille ?")
    print("  - Compare Apple, Microsoft et Nvidia sur 1 an\n")
    while True:
        q = input("> ")
        if q.strip().lower() in {"quit", "exit"}:
            break
        print("\n" + agent(q) + "\n")
