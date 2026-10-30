# GradMatch

SE 413/513 Software Testing project, Fall 2026
Rajeshwari Galugu and Sai Nishith Jangili

A Streamlit app for students planning grad school. You enter your degree (MS or PhD), field,
GPA, home state, the states you'd like, budget and citizenship. The app shows:

- programs you can afford, cheapest first (PhD: best funded first), with a Safety / Match / Reach chance
- scholarships and fellowships you can apply for
- their deadlines, with a warning when one is less than 2 weeks away

The same search is also available as a small REST API.

Live app: https://gradmatch-rg.streamlit.app

## Features

| Feature | Files | Who |
|---|---|---|
| Program search, yearly cost and PhD funding | `search.py`, `cost.py` | Rajeshwari |
| Admission chance | `fit.py` | Rajeshwari |
| Scholarships | `scholarships.py` | Sai Nishith |
| Deadline tracker | `deadlines.py` | Sai Nishith |

Also: the page `app/streamlit_app.py` and CI (Rajeshwari), and the data loader
`data_loader.py`, the SQLite database `database.py` and the API `api.py` (Sai Nishith). All code is in `src/gradmatch/`.

## Running

Python 3.11 or newer.

```
pip install -r requirements.txt
streamlit run app/streamlit_app.py
uvicorn --app-dir src gradmatch.api:app     # API at http://127.0.0.1:8000/docs
pytest --cov
```

## Data

- `data/programs.csv`: 159 MS and PhD programs in Computer Science, Electrical Engineering,
  Mechanical Engineering and Statistics in IL, IN, MI, OH and WI. Tuition, school names and websites are from
  the 2024 IPEDS data (U.S. Department of Education). The acceptance rate is the school's
  overall rate from IPEDS, not the program's. Living cost is from the MERIC cost of living index.
  The `stipend` column is blank until we check it on the program's website (blank = "Not listed").
- `data/scholarships.csv`: 7 national scholarships and fellowships. The amounts and deadlines
  still need to be checked on each official website.

Results are estimates and do not promise admission.
