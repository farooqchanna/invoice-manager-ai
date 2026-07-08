# Invoice Manager

A small Flask web app that lets you upload invoice files (images/PDFs), uses **Google Gemini** to extract structured invoice data from them, stores the data in a CSV file, displays it in a table, and automatically emails a daily reminder for invoices due that day.

## Features

- **Login-gated access** — simple session-based login screen guarding the app.
- **AI-powered invoice ingestion** — upload an invoice file; Gemini (`gemini-2.5-flash`) reads it and returns structured JSON (company name, service, total payment, due date), which is appended to a local CSV.
- **Invoice table view** — view all stored invoices, see the running total, and delete individual rows.
- **Automatic email reminders** — a background scheduler runs daily at 9:00 AM, checks for invoices due that day, and emails a summary via Gmail SMTP.

## Project Structure

```
.
├── app.py            # Main Flask application (this file)
├── api.py            # Must define `api_key` (Gemini/Google API key)
├── prom.py           # Must define `prt()` returning the extraction prompt for Gemini
├── invoice.csv        # Data store (auto-created on first upload)
└── templates/
    ├── login.html
    ├── upload.html
    └── view.html
```

## Requirements

- Python 3.9+
- Packages:
  ```
  flask
  apscheduler
  google-genai
  pandas
  ```
  Install with:
  ```bash
  pip install flask apscheduler google-genai pandas
  ```

## Configuration

Before running, set up the following:

1. **`api.py`** — must define an `api_key` variable containing your Google Gemini API key (used implicitly by `genai.Client()`, typically via the `GOOGLE_API_KEY`/`GEMINI_API_KEY` environment variable — make sure `api.py` exports/sets it appropriately).
2. **`prom.py`** — must define a `prt()` function that returns the prompt instructing Gemini how to extract invoice fields (`company_name`, `service`, `total_payment`, `due_date`) as JSON.
3. **Flask secret key** — replace the placeholder in `app.secret_key` with a real, secret value.
4. **Email credentials** — in `auto_mail()`, replace `"YOUR_APP_PASSWORD"` with a Gmail **App Password** (not your regular password) for the sender account. Consider moving `sender`, `recipient`, and `password` into environment variables instead of hardcoding them.
5. **Login credentials** — the login route currently checks for the hardcoded username `admin` and password `123`. Replace this with a real authentication mechanism before any real-world use.

## Running the App

```bash
python app.py
```

By default this will start the Flask development server. Since the app also uses `BackgroundScheduler`, the scheduled job will start alongside the web server.

> **Note:** `app.run()` is not shown in the current file — add it if missing, e.g.:
> ```python
> if __name__ == "__main__":
>     app.run(debug=True)
> ```

## Routes

| Route | Methods | Description |
|---|---|---|
| `/` | GET, POST | Login page. POST validates credentials and starts a session. |
| `/logout` | GET, POST | Clears the session and redirects to login. |
| `/home` | GET, POST | GET shows the upload form. POST accepts a file, sends it to Gemini for extraction, and appends the parsed invoice to `invoice.csv`. |
| `/view` | GET, POST | Displays all invoices and the total amount. POST with a `number` field deletes that row (by index) from the CSV. |

## Data Format (`invoice.csv`)

| Column | Description |
|---|---|
| `company_name` | Name of the billing company |
| `service` | Service or product billed |
| `total_payment` | Invoice amount |
| `due_date` | Date payment is due (`YYYY-MM-DD`) |

## Known Issues / Suggested Improvements

- **Column name mismatch:** `/view` reads and sums `df.total_amount`, but the CSV is written with a `total_payment` column. This will raise an `AttributeError` unless the column is renamed consistently.
- **Hardcoded secrets:** the Flask `secret_key`, Gmail password, and login credentials are hardcoded in source. Move these to environment variables or a `.env` file (e.g. via `python-dotenv`) and never commit real credentials.
- **No authentication on `/home` or `/view`:** routes aren't currently protected by a login check (e.g. `if "user" not in session: return redirect(url_for("login"))`), so they're accessible without logging in.
- **Row deletion by CSV index** is fragile if the CSV is edited concurrently or externally; consider a proper database (SQLite, etc.) for reliability.
- **Error handling on Gemini response parsing:** if Gemini doesn't return valid JSON, `json.loads(data)` will raise an unhandled exception.

## License

Add a license of your choice here.
