# 🍳 Recipe Cost Wizard — **[Click Here!](https://recipe-cost-finder.streamlit.app/)**

Recipe Cost Wizard is a fun and interactive Streamlit web app that helps you explore recipes scraped from **Kosher.com**, calculate ingredient costs using the **Kroger API**, and learn interesting food facts scraped from **Wikipedia**. It also includes a built‑in AI cooking assistant powered by Azure OpenAI to answer your kitchen questions, suggest substitutions, and explain recipe steps.

Tests coverage: **✔ 60%+**  
Fully deployable on Streamlit Cloud.

---

# 📦 Features

### 📖 Recipe Scraping (Kosher.com)
- Scrapes real recipes from **Kosher.com**
- Extracts ingredients, quantities, instructions, and tags
- Stores everything in a local SQLite database

### 🛒 Kroger API Price Lookup
- Retrieves real ingredient prices from the **Kroger Developer API**
- Updates your SQLite database with fresh pricing
- Fully mocked in tests — no real API calls required

### 🌐 Wikipedia Food Facts
- Scrapes the **first real paragraph** from Wikipedia ingredient pages
- Removes pronunciation lines and irrelevant text
- Adds a “featured ingredient” description to each recipe

### 🧮 Cost Engine
- Converts recipe quantities into estimated cost
- Handles fractions, units, missing quantities, and fallback rules
- Computes total recipe cost and cost per serving
- Generates a full ingredient cost breakdown

### 🧠 AI Cooking Assistant
- Suggests cheaper substitutions
- Explains recipe steps
- Answers cooking questions
- Uses Azure OpenAI (mocked in tests)

### 🗃️ SQLite Database
- Stores recipes, ingredients, and nutrition facts
- Automatically updates ingredient prices
- Fully tested CRUD operations

### 📊 Visualizations
- Ingredient cost pie chart
- Interactive Streamlit UI
- Clean, simple layout for recipe exploration

### 🧪 Testing
- Kosher.com scraper
- Kroger API (mocked)
- Wikipedia scraper
- Cost engine
- Database functions
- AI helper
- **60%+ coverage**

---

# 🎯 What You Can Do in the App

### 🍽️ Explore Recipes
- Browse recipes scraped from Kosher.com
- View ingredients, instructions, and tags
- See cost per serving
- Read featured ingredient facts from Wikipedia

### 💰 Update Ingredient Prices
- Refresh prices using the Kroger API
- Store updated values in SQLite

### 📊 Visualize Costs
- Pie chart of ingredient cost distribution
- Breakdown table with quantities + units

### 🤖 Chat With the AI Chef
- Ask for substitutions
- Ask for cheaper alternatives
- Ask for cooking explanations

---

# 🛠️ Installation & Local Setup

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd final_project
```

### 2. Create a virtual environment
```bash
python3 -m venv venv
source venv/bin/activate     # Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Add your secrets
Create `.streamlit/secrets.toml`:

```toml
AZURE_OPENAI_API_KEY="your_key"
AZURE_OPENAI_ENDPOINT="your_endpoint"
AZURE_OPENAI_MODEL="your_model"

KROGER_CLIENT_ID="your_kroger_client_id"
KROGER_CLIENT_SECRET="your_kroger_client_secret"
```

### 5. Run the app
```bash
python3 -m streamlit run app/streamlit_app.py
```

---

# 🤖 ChatGPT Integration

The app uses **Azure OpenAI** to provide:

- Ingredient substitution suggestions  
- Cooking explanations  
- Chat‑style Q&A  
- Recipe insights  

All AI calls are wrapped in `ai_helper.py` and **fully mocked in tests**, so the test suite runs without internet or API keys.

---

# 🧪 Testing

Run the full test suite:

```bash
pytest -q
```

Run with coverage:

```bash
pytest --cov=. --cov-report=term-missing
```

Generate HTML coverage report:

```bash
pytest --cov=. --cov-report=html
```

Tests achieve **60%+ coverage** and cover:

- Kosher.com scraper  
- Kroger API  
- Wikipedia scraper  
- Cost engine  
- Database  
- AI helper  

---

# 🌍 Deployment (Streamlit Cloud)

1. Push your repo to GitHub  
2. Go to https://share.streamlit.io
3. Select your repo  
4. Set the entrypoint to:

```
app/streamlit_app.py
```

5. Add secrets under **Settings → Secrets**  
6. Deploy!

Live App URL (add yours here):

```
https://recipe-cost-finder.streamlit.app/
```

---

# 📦 Dependencies

Main libraries:

- streamlit  
- requests  
- beautifulsoup4  
- pandas  
- openai  
- python-dotenv  
- pytest  

See `requirements.txt` for full list.

---

# 🎉 You're All Set!
