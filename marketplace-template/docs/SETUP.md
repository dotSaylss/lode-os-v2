# Setup Guide — get the marketplace running on your computer

Welcome! This guide walks you through running this app on your own computer,
step by step. **You do not need to be a programmer.** If you can copy and paste,
you can do this. Every command is explained in plain English first, and we cover
both **Mac** and **Windows**.

Take your time. There is nothing here you can break.

---

## 1. What you're setting up

This is a **marketplace with an AI matchmaker**. Someone types what they need in
plain language (for example, *"I need my single mixed and mastered"*), and an AI
assembles a best-fit team from a list of vetted service providers, explains *why*
each one fits, suggests how to split the money and rights, and shows exactly
which providers it looked at — so the answer is trustworthy, not made up.

It ships looking like a **music-services marketplace**, but the same code works
for any kind of marketplace. When it's running, it looks like this:

![The running marketplace](img/marketplace-verified.png)

The app has two halves that run at the same time:

- A **backend** — the "engine" that holds the list of providers and runs the AI.
- A **frontend** — the web page you actually look at and click on.

You'll start both. Don't worry about what those words mean yet — we'll get there.

> **The good news:** out of the box, this app runs with **zero setup keys and no
> AI account**. It uses a built-in "mock" (practice) matchmaker so you can see
> the whole experience immediately, for free. Turning on the *real* AI is an
> optional extra at the end.

---

## 2. What you need first

You need to install two free tools, plus have a way to type commands. Let's get
those ready.

### A code editor / terminal — what is a "terminal"?

A **terminal** is just a text window where you type commands instead of clicking
buttons. It comes free with your computer — you don't install anything.

- **On a Mac:** Press `Cmd (⌘) + Space`, type `Terminal`, and press `Enter`.
  A window called **Terminal** opens.
- **On Windows:** Click the Start menu, type `PowerShell`, and click
  **Windows PowerShell**. A blue window opens.

Keep that window open — you'll paste commands into it throughout this guide.
When we show a command in a box, copy it, click into the terminal, paste, and
press `Enter`.

### Tool 1 — Python

**Python** is the programming language the backend engine is written in. You
need version **3.11 or newer**.

1. Download it from **https://www.python.org/downloads/** and run the installer.
2. **On Windows, important:** on the first screen of the installer, tick the box
   that says **"Add Python to PATH"** before clicking Install. This lets the
   terminal find Python later.

**Check it worked.** This command asks Python to tell you its version:

**Mac:**
```bash
python3 --version
```

**Windows:**
```powershell
python --version
```

You should see something like `Python 3.11.5` (any 3.11 or higher is great). If
you instead see an error like "command not found," see the Troubleshooting table
at the end.

### Tool 2 — Node.js

**Node.js** is what runs the frontend (the web page). You need version **18 or
newer**.

1. Download it from **https://nodejs.org/** — click the button labelled **LTS**
   (that's the stable version). Run the installer and click through with the
   default options.

**Check it worked.** This command asks Node to tell you its version:

```bash
node --version
```

You should see something like `v18.17.0` or higher (for example `v24.x` — that's
fine).

> Installing Node also installs **npm** for free. `npm` ("Node Package Manager")
> is a helper that downloads the building blocks the frontend needs. You'll use
> it in a moment.

Once both `--version` checks print a number, you're ready. 🎉

---

## 3. The fast path (one command)

If you're on a **Mac** (or Linux), there's a helper script that installs
everything and starts both halves for you with a single command.

First, go into the project folder. `cd` means "change directory" — it moves your
terminal into a folder. Replace the path if you saved the project somewhere else:

```bash
cd marketplace-template
```

Then run the helper script:

```bash
./run.sh
```

This installs the backend, installs the frontend, and starts both. When it's
done you'll see a message pointing you to **http://localhost:5173** — open that
in your web browser (see Section 5).

> **On Windows,** the one-command script isn't available — but the step-by-step
> path below takes only a few minutes. Follow Section 4 instead.

To stop everything later, click the terminal and press **`Ctrl + C`**.

---

## 4. The step-by-step path (works everywhere)

Prefer to do it yourself, or on Windows? Follow these. You'll use **two terminal
windows** — one for the backend, one for the frontend — because both need to keep
running at the same time.

### Part A — Start the backend (the engine)

**Step 1 — Open the backend folder.** In your first terminal window:

```bash
cd marketplace-template/backend
```

**Step 2 — Create a "virtual environment."** A **venv** (short for *virtual
environment*) is a private, self-contained box for this project's Python parts,
so they never clash with anything else on your computer. This command creates one
in a hidden folder called `.venv`:

**Mac:**
```bash
python3 -m venv .venv
```

**Windows:**
```powershell
python -m venv .venv
```

Nothing dramatic happens — that's normal. It just quietly creates the box.

**Step 3 — Turn the venv on ("activate" it).** This tells your terminal to use
that private box. **The command is different on each system:**

**Mac:**
```bash
source .venv/bin/activate
```

**Windows:**
```powershell
.venv\Scripts\activate
```

You'll know it worked because `(.venv)` now appears at the start of your terminal
line. Keep this terminal open — the venv stays on until you close it.

> **Windows note:** if you see a red error about "running scripts is disabled,"
> run this once, then try the activate command again:
> ```powershell
> Set-ExecutionPolicy -Scope Process Bypass
> ```

**Step 4 — Install the backend's parts.** `requirements.txt` is a shopping list
of the pieces the backend needs. `pip` is Python's installer; this reads the list
and downloads everything:

```bash
pip install -r requirements.txt
```

You'll see several lines scroll by, ending in something like
`Successfully installed fastapi ... uvicorn ...`. This takes under a minute.

**Step 5 — Start the backend.** This launches the engine. **localhost** means
"this very computer," and a **port** is like a numbered door on it — the backend
answers on door **8000**:

```bash
uvicorn main:app --reload
```

You should see a line that includes `Uvicorn running on http://127.0.0.1:8000`.
**Leave this terminal running** — the backend is now live. (Closing it, or
pressing `Ctrl + C`, stops the engine.)

**Step 6 — Confirm it's healthy (optional).** Open a **new** terminal window and
run this. It asks the backend "are you okay?" and reads the answer:

```bash
curl http://localhost:8000/api/health
```

You should see:

```
{"status":"ok","matchmaker":"mock"}
```

`"mock"` confirms it's running in the free, no-key practice mode. Perfect.

### Part B — Start the frontend (the web page)

Open a **second** terminal window (leave the backend one running).

**Step 1 — Open the frontend folder.**

```bash
cd marketplace-template/frontend
```

**Step 2 — Install the frontend's parts.** This uses `npm` to download the web
page's building blocks. It can take a couple of minutes the first time:

```bash
npm install
```

You'll see a progress bar and finally a summary like `added 200 packages`. A few
yellow "warning" lines are normal and safe to ignore.

**Step 3 — Start the frontend.** This launches the web page on port **5173**:

```bash
npm run dev
```

You should see something like:

```
  VITE ready in 400 ms
  ➜  Local:   http://localhost:5173/
```

**Leave this terminal running too.** Both halves are now live.

---

## 5. Using it

1. Open your web browser (Chrome, Safari, Edge — any works).
2. Go to **http://localhost:5173** — type that into the address bar and press
   Enter.
3. The marketplace page loads. You should see a grid of **19 providers** (mixing
   engineers, mastering studios, cover-art designers, and more). If the grid is
   full of cards, the frontend and backend are talking to each other correctly.
4. Find the text box near the top and describe a project in plain language. Try:

   > **I need my lo-fi hip-hop single mixed, mastered, and cover art**

5. Click the **"Find my team"** button.
6. In a moment, the matchmaker replies with a **recommended team** — one provider
   per role — explains **why** each was chosen, suggests a **money/rights split**,
   and shows the **evidence** (the exact providers it considered) so you can see
   the answer is grounded in the real marketplace, not invented.

That's the whole experience. Change the brief and try again — experiment freely.

---

## 6. Optional: turn on the real AI

By default the app uses the free built-in "mock" matchmaker, which is great for
demos. If you want the **real** Google Gemini AI agent to do the matching, here's
how. This is entirely optional.

**Step 1 — Get a free API key.** An **API key** is a secret password that lets
your app use Google's AI. Get one at **https://aistudio.google.com/apikey** —
sign in with a Google account and click to create a key. Copy the long string it
gives you.

**Step 2 — Enable the AI parts in the shopping list.** Open
`backend/requirements.txt` in any text editor and **remove the `#` and the space**
at the start of these two lines, so they read:

```
google-adk
google-genai
```

**Step 3 — Install those new parts.** Back in your backend terminal (with the
`(.venv)` shown), re-run the installer:

```bash
pip install -r requirements.txt
```

**Step 4 — Give the app your key.** In the `backend` folder, make a copy of the
example settings file and name it `.env` (a file that holds private settings):

**Mac:**
```bash
cp .env.example .env
```

**Windows:**
```powershell
copy .env.example .env
```

Open the new `.env` file in a text editor and add this line (paste your real key
in place of the placeholder):

```
GOOGLE_API_KEY=paste-your-key-here
```

Save the file.

**Step 5 — Restart the backend.** In the backend terminal, press `Ctrl + C` to
stop it, then start it again:

```bash
uvicorn main:app --reload
```

The app is set to `auto` mode by default, so now that a key is present it will
use the **real** Gemini agent automatically. Confirm with the health check:

```bash
curl http://localhost:8000/api/health
```

It should now say `"matchmaker":"real"` instead of `"mock"`. Your matches are now
being generated by live AI. 🎉

---

## 7. Troubleshooting

Something not working? It's almost always one of these. Find your symptom:

| What you see | What it means | How to fix it |
|---|---|---|
| **`command not found: python` / `python3`** (Mac) or **`'python' is not recognized`** (Windows) | The terminal can't find Python. | Reinstall from python.org. On Windows, tick **"Add Python to PATH"** during install, then close and reopen the terminal. On Mac, try `python3` instead of `python`. |
| **`command not found: node` / `npm`** | Node.js isn't installed or the terminal needs a restart. | Install the **LTS** version from nodejs.org, then close and reopen your terminal window. |
| **`Address already in use` / `port 8000 (or 5173) already in use`** | Something is already running on that door — often an old copy of this app. | Go to the earlier terminal running it and press `Ctrl + C` to free the port, then start again. If unsure, closing all terminal windows and reopening resets everything. |
| **`npm install` shows errors and stops** | The download got interrupted, or a partial install is confusing it. | Run `npm install` again (it resumes). Still stuck? Delete the `node_modules` folder in `frontend` and the `package-lock.json` file, then run `npm install` once more. |
| **The page loads but the provider grid is blank** | The web page can't reach the backend engine. | Make sure the **backend terminal is still running** (Section 4, Part A). Confirm `curl http://localhost:8000/api/health` returns `{"status":"ok",...}`. Both halves must be running at once. |
| **`(.venv)` disappeared from my terminal** | You closed the terminal or opened a new one; the venv only stays on in the window where you activated it. | Re-run the activate command from Section 4, Part A, Step 3, in the backend folder. |
| **Windows: "running scripts is disabled on this system"** | Windows blocks scripts by default. | Run `Set-ExecutionPolicy -Scope Process Bypass` once, then re-run the activate command. |
| **How do I stop everything?** | — | Click each running terminal and press **`Ctrl + C`**. That stops that half. Do it in both the backend and frontend terminals. |

Still stuck? Close every terminal window, reopen fresh ones, and start again from
Section 4. A clean restart fixes most mysteries.

---

## 8. Where to go next

You've got the whole thing running — nicely done. When you're ready to make it
your own:

- **`../README.md`** — the project overview, and the **"Make it yours"** section,
  which shows the handful of files to edit to re-brand the marketplace, swap in
  your own list of providers, or change the categories. Re-theming to a
  completely different (non-music) marketplace is mostly rewriting one data file.
- **`ARCHITECTURE.md`** — a deeper tour of how the pieces fit together. This is
  also the ideal file to hand to an AI coding assistant (like Lovable or Claude)
  when you want it to help you customize the app — it gives the AI the full map
  in one place.

Have fun building. You're no longer just running someone else's app — you're
ready to shape it into yours.
