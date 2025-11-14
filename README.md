# AI Sales Dashboard Agent (Streamlit + OpenAI)

This app lets you upload a sales dataset (CSV) and automatically:

- Cleans and aggregates the data
- Generates charts (sales trend, category performance, region, etc.)
- Calls an LLM to produce executive summary and business insights

Built with:
- Python, Streamlit, Pandas, Matplotlib/Plotly
- OpenAI (gpt-4o-mini or gpt-realtime-mini)

## Setup

1. Create and activate a virtual env (optional but recommended)

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate
```

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Set up your OpenAI API key

Create a `.streamlit/secrets.toml` file in the project root:

```toml
# .streamlit/secrets.toml
OPENAI_API_KEY = "your-api-key-here"
```

Get your API key from: https://platform.openai.com/api-keys

**Note:** The `secrets.toml` file is already in `.gitignore` to keep your API key secure.

4. Run the app

```bash
streamlit run app.py
```