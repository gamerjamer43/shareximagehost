# shareximagehost

A simple, self‑hosted ShareX‑compatible image (and video) hosting service with user accounts, 2‑step email verification, per‑user storage quotas, and a web UI.

## Features

- **ShareX API endpoint** (`/upload`)
  - Upload files programmatically by sending a `multipart/form-data` POST with your API key in the `key` header; returns a JSON response with a permanent link.

- **Secure user accounts**
  - Signup/Login with email and username
  - Passwords hashed via PBKDF2
  - Email‑based 2‑step verification (2SV) on signup and login
  - Admin approval required before first login

- **Per‑user web dashboard**
  - View and copy your API key (with show/hide)
  - Reset API key on demand
  - Storage‑use progress bar (2 GB default for users; 25 GB for admin. You can change this to your liking)
  - Grid display of uploaded images/videos with thumbnails and file info
  - Delete files via the UI

- **File preview page**
  - Automatic in‑browser preview of images (JPG/PNG/GIF) and videos (MP4/WebM/OGG)
- **Rate limiting**
  - 5 API uploads per minute; fallback to 100 per hour and 1 000 per day overall
- **Admin CLI script** (`approve.py`)
  - List pending users and approve or delete accounts from the command line
- **Extensible**
  - Add features like paid storage, custom embeds, user profiles, theming, etc.

## Tech Stack

- **Back end**: Flask, Flask‑Login, Flask‑Limiter, SQLAlchemy (SQLite)
- **Email**: SMTP via Gmail SSL for sending 2SV codes
- **File processing**: Pillow for images; MoviePy for video metadata
- **Front end**: Plain HTML/CSS with a dark “Impact”‑style theme

## Installation

1. **Clone the repo**
   ```bash
   git clone https://github.com/gamerjamer43/shareximagehost.git
   cd shareximagehost
   ```
2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure sensitive settings**
   - Create `sensitivedetails.py` in the project root with:
     ```python
     EMAIL_ADDRESS = "your@gmail.com"
     EMAIL_PASSWORD = "your-app-password"
     ```
   - (Optional) Update `app.config['SECRET_KEY']` in `app.py` to a secure random string.
4. **Initialize the database**
   ```bash
   python app.py
   ```
   The first run will create `users.db` and an **admin user** with `id=1`.
5. **Run the server**
   ```bash
   python app.py
   ```
   By default it listens on port 5000 in debug mode.

## Configuration

- **Upload limits**
  - Global per‑file limit: 16 MB (configured via `MAX_CONTENT_LENGTH`)
  - Per‑user total storage: 2 GB (users) / 25 GB (admin)
- **Rate limits** in `app.py` via Flask‑Limiter:
  ```python
  default_limits=["1000 per day", "100 per hour"]
  @limiter.limit("5 per minute")  # on /upload
  ```
- **Static assets** served from `static/` (logos, CSS, etc.)

## Usage

### Web UI

- **Visit** `http://<host>:5000/signup` to create an account
- After signup, admin must run `approve.py` to approve you
- **Login** at `/login`; after entering credentials you’ll get a 2SV code via email
- In your dashboard you can upload via the form (or copy your API key)

### ShareX API

- **Endpoint**:
  ```
  POST http://<host>:5000/upload
  Headers:
    key: <your_api_key>
  Form Data:
    file: <your_file>
  ```
- **Successful response** (`201`):
  ```json
  {
    "success": "File uploaded successfully",
    "file_url": "https://<host>/file/123/your_image.png"
  }
  ```
- **Errors** include missing/invalid key, file too large, upload limit exceeded, etc.

## Admin CLI (`approve.py`)

1. Run:
   ```bash
   python approve.py
   ```
2. It lists all unapproved users, then prompts:
   ```
   Enter ID to approve or delete: 5
   Do you want to approve (a) or delete (d) user alice? (a/d):
   ```
3. Approved users can then complete signup 2SV to log in.

## Project Structure

```
├── app.py             # Main Flask application
├── approve.py         # Admin user‑approval CLI
├── sensitivedetails.py# (gitignored) email creds
├── requirements.txt   # Python dependencies
├── templates/         # HTML templates (UI)
│   ├── index.html
│   ├── signup.html
│   ├── login.html
│   ├── 2sv.html
│   ├── file.html
│   └── test.html
├── static/
│   └── images/        # icons, logo, favicon
├── uploads/           # User file storage (created at runtime)
└── users.db           # SQLite database (created on first run)
```

## Contributing

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/awesome`
3. Commit your changes and push: `git push origin feature/awesome`
4. Open a Pull Request—happy to review and merge!

## License

This project is licensed under the GNU General Public License v3.0. See the [LICENSE](LICENSE) file for details.
=======
adding this later. i'm fat and lazy
