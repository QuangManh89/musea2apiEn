# MUSE2API

中文文档: [README.zh-CN.md](./README.zh-CN.md)

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?logo=python" alt="Python Version" />
  <img src="https://img.shields.io/badge/FastAPI-0.115%2B-009688?logo=fastapi" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker" alt="Docker" />
  <img src="https://img.shields.io/badge/API-OpenAI%20Compatible-green" alt="OpenAI API Compatible" />
  <img src="https://img.shields.io/badge/License-MIT-orange" alt="License" />
  <a href="https://linux.do/" target="_blank"><img src="https://img.shields.io/badge/Community-LINUX%20DO-111827?logo=linux&logoColor=white" alt="LINUX DO" /></a>
</p>

<p align="center">
  🤝 This open-source project links to and endorses <b><a href="https://linux.do/" target="_blank">LINUX DO Community (https://linux.do/)</a></b> — a new ideal community (sincere, friendly, united, professional)
</p>

Reverse-engineers the cutting-edge multimodal capabilities of the **[muse.ai](https://muse.ai/)** web client into a standard **OpenAI-compatible RESTful API**. Via headless-browser CDP passthrough, warm-standby WebSocket tunnel reuse, and dynamic session management, it natively supports text chat (2–3 second streaming first-token latency), text-to-image, image-to-image editing, text-to-video, and first-frame image-to-video, plus a multi-account pool with affinity rotation, fully automatic 48-hour session renewal with cloud VM wake-up keepalive, and a companion Chrome one-click account-import extension.

---

## 🌟 Core Features

- 💬 **Standard chat endpoints (Chat Completions & Responses API)**
  - Fully compatible with the `/v1/chat/completions` protocol and the newer `/v1/responses` protocol used by Codex by default.
  - Native SSE streaming typewriter output (`stream=True`) and synchronous full responses, with warm-tab and Noise WebSocket tunnel affinity reuse — **first-token latency of only 2–3 seconds for back-to-back chats**.
  - Supports multi-turn context and System Prompt configuration.
  - Built-in smart model alias mapping: common names such as `gpt-4o`, `gpt-5`, `claude-sonnet-4`, `deepseek-chat` are routed automatically.
- 🎨 **High-quality image generation & editing (Images Generations & Edits)**
  - Fully compatible with `/v1/images/generations` (text-to-image) and `/v1/images/edits` (image-to-image / reference-image editing).
  - Supports aspect ratios such as `1:1`, `16:9`, `9:16`, `4:3`, `3:4`, direct reference-image upload, and watermark-free clean output.
  - Supports both `url` direct links and `b64_json` return formats, with built-in second-level plain-text refusal detection to prevent queue deadlocks.
  - Image-to-image returns only newly generated media for this run: upload previews and historical attachments are excluded, downloads bind to the selected result; unconfirmed reference uploads or prompt sends produce explicit errors instead of silently returning the original image.
- 🎬 **Text-to-video / image-to-video (Videos)**
  - Natively wired to Muse's top-tier video models. Duration requests of 5 / 6 / 8 / 10 seconds are accepted (final clip length follows Muse upstream output), with `9:16` portrait / `16:9` landscape generation.
  - Supports uploading a first-frame reference image (Data URL / HTTP URL) for strict first-frame image-to-video creation.
  - Async task architecture (`/v1/videos` to create a task + `/v1/videos/{task_id}` status polling).
  - Built-in media serving at `/v1/media/{filename}` with automatic persistent storage of generated MP4 / WebP assets.
- ⚡ **True multi-account parallel execution (Multi-Account Parallel Execution)**
  - Isolated incognito containers via Chromium-native `Target.createBrowserContext`; concurrent tasks run in independent sandboxes.
  - Multiple accounts generate images/videos and stream chats simultaneously with zero mutual blocking; Cookies and Sessions are 100% isolated with no cross-talk.
  - Built-in smart account-conflict scheduler: same-account tasks are mutually exclusive (no trampling), multi-account tasks run fully in parallel.
  - Tune the concurrency cap via `MUSE2API_CONCURRENCY` to match your hardware (default: 2).
- 🔄 **Multi-account pool with warm-connection affinity scheduling**
  - Import an unlimited matrix of Muse accounts.
  - Warm-tab affinity + LRU dispatch balances 2-second-class responsiveness with even consumption across accounts.
  - When one account hits quota exhaustion or a session anomaly, it is flagged automatically with 0-second transparent failover to a healthy standby account.
- 🛡️ **Fully automatic 48-hour session renewal & cloud VM keepalive**
  - Original background heartbeat coroutine talks directly to `/api/session` to renew `hatch_vml` (+48h) and `hatch_sess` (+30d), and calls `/api/hatch/vm/wake` to keep the cloud workspace VM warm.
  - Completely solves the static 48-hour Meta Cookie expiry and VM sleep-disconnect problems — no frequent re-login needed.
- 🧩 **Companion Chrome one-click account-import extension**
  - No manual F12 packet capture: one click on the extension icon extracts the current browser login state (including `HttpOnly` core Cookies with real expiry times) and securely pushes it to the account pool.
- 🖥️ **Modern dark Ops console (Web Console) with live hot upgrade**
  - Built-in ready-to-use Web UI: live service health, account-pool quota & status, one-click whole-pool keepalive, task progress replay, media library management, and online API debugging.
  - **Network-wide live update broadcast & one-click upgrade**: when the official GitHub repo publishes a new release or fix, every deployed node's admin console automatically shows an update banner at the top. Click **"⚡ One-click online upgrade & restart"** to pull the latest code and restart gracefully (local `.env` config and account data are preserved).

---

## 🚀 Quick Deploy

### Option 1: Docker Compose (recommended, one command out of the box)

1. **Clone the repo and enter the directory**:
   ```bash
   git clone https://github.com/czg86389-hub/muse2api.git
   cd muse2api
   ```

2. **Configure environment variables (optional)**:
   ```bash
   cp .env.example .env
   # Edit .env as needed; changing MUSE2API_KEY to your own admin key is recommended
   ```

   Docker Compose reads `MUSE2API_KEY` from `.env` and will no longer be overridden by the sample value in the Compose file.

3. **Start the container**:
   ```bash
   docker compose up -d
   ```

4. **Open the admin panel**:
   Open in your browser: `http://<your-server-IP>:18610/admin?key=<your-MUSE2API_KEY>`

---

### Option 2: Bare metal / VPS (Ubuntu / Debian)

1. **Install system dependencies & Chromium**:
   ```bash
   sudo apt-get update
   sudo apt-get install -y chromium fonts-wqy-zenhei python3 python3-pip python3-venv
   ```

2. **Set up the Python virtual environment**:
   ```bash
   cd /opt/muse2api
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Configure the systemd service**:
   ```bash
   sudo cp deploy/muse2api.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable --now muse2api
   ```

4. **Nginx reverse-proxy config (important: prevents 502 timeouts & streaming stalls)**:
   If you proxy via Nginx / aaPanel / 1Panel, raise `proxy_read_timeout` to `600s` and disable `proxy_buffering` (see `deploy/nginx.example.conf`):
   ```nginx
   location / {
       proxy_pass http://127.0.0.1:18610;
       proxy_read_timeout 600s;      # avoid 502 Bad Gateway on slow image/video jobs
       proxy_send_timeout 600s;
       proxy_buffering off;          # keep SSE chat typewriter output at 0-delay
       client_max_body_size 64M;     # allow large reference-image uploads
       proxy_set_header Host $host;
       proxy_set_header X-Real-IP $remote_addr;
       proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
   }
   ```

---

## 🧩 Account Import (Chrome Extension / Tampermonkey Script)

### Option A: Chrome / Edge extension
The project ships a dedicated Chrome account-import extension (in `extension/`), so no manual F12 Cookie extraction is needed:

1. Open Chrome / Edge, visit `chrome://extensions`, and enable **"Developer mode"** in the top-right corner.
2. Click **"Load unpacked"** and select the `extension` directory from this project.
3. In that browser, log in to [muse.ai](https://muse.ai/) until you reach the main chat UI.
4. Click the extension icon in the toolbar, fill in your service address (e.g. `http://1.2.3.4:18610`) and `MUSE2API_KEY`.
5. Click **"Read & import"** — synced into the pool within seconds!

### Option B: Tampermonkey userscript (no extension install, cross-browser)
For users who prefer not to enable developer mode, or who use Firefox / Safari, a userscript is provided at `tools/muse2api_cookie_importer.user.js`:
1. Install the Tampermonkey extension in your browser.
2. Create a new script and paste the contents of `tools/muse2api_cookie_importer.user.js`, then save.
3. Open the [muse.ai](https://muse.ai/) page — a floating **"⚡ Import to muse2api"** button appears in the bottom-right corner. Right-click to configure the service address and Key; left-click pushes the login state into the pool in one click with automatic clipboard fallback.

---

## 📖 API Examples

All protected endpoints require this header:
```http
Authorization: Bearer <your-MUSE2API_KEY>
```

### 1. Chat Completions

```bash
curl -X POST "http://localhost:18610/v1/chat/completions" \
  -H "Authorization: Bearer m2a_your_secret_key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "muse-spark",
    "messages": [
      {"role": "user", "content": "Write a haiku about neon rain over a cyberpunk city"}
    ],
    "stream": false
  }'
```

### 2. Image Generation

```bash
curl -X POST "http://localhost:18610/v1/images/generations" \
  -H "Authorization: Bearer m2a_your_secret_key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "muse-image",
    "prompt": "A robotic Shiba Inu in an anti-gravity spacesuit, cinematic lighting, 8k",
    "size": "16:9",
    "response_format": "url"
  }'
```

**Sample response**:
```json
{
  "created": 1790148495,
  "data": [
    {
      "revised_prompt": "A robotic Shiba Inu in an anti-gravity spacesuit, cinematic lighting, 8k",
      "url": "http://localhost:18610/v1/media/img_abc123.webp",
      "kind": "image",
      "bytes": 54210
    }
  ]
}
```

### 3. Text-to-Video / Image-to-Video (Videos)

- **Step 1: create the generation task**
  ```bash
  curl -X POST "http://localhost:18610/v1/videos" \
    -H "Authorization: Bearer m2a_your_secret_key" \
    -H "Content-Type: application/json" \
    -d '{
      "model": "muse-video",
      "prompt": "Golden maple leaves drifting lightly in the breeze, sunlight through the treetops",
      "duration": 5,
      "size": "16:9"
    }'
  ```
  Returns a task ID: `{"id": "task_xyz789", "status": "queued"}`

- **Step 2: poll the task status**
  ```bash
  curl "http://localhost:18610/v1/videos/task_xyz789" \
    -H "Authorization: Bearer m2a_your_secret_key"
  ```
  When finished, returns:
  ```json
  {
    "id": "task_xyz789",
    "status": "succeeded",
    "progress": 100,
    "result": {
      "url": "http://localhost:18610/v1/media/vid_xyz789.mp4"
    }
  }
  ```

---

## ⚙️ Environment Variables

| Variable | Default | Description |
|---|---|---|
| `MUSE2API_KEY` | Auto-generated | Admin console + API auth key (starts with `m2a_`) |
| `MUSE2API_LANG` | `en` | UI/backend language: `en` (default) \| `zh`. The admin page has its own toggle |
| `MUSE2API_HOST` | `127.0.0.1` | Listen IP (`0.0.0.0` recommended inside Docker) |
| `MUSE2API_PORT` | `18610` | Service port |
| `MUSE2API_PUBLIC_BASE` | empty | Public base URL prefix; when empty the frontend auto-detects the request origin |
| `MUSE2API_CHROMIUM` | `chromium` | Full path to the browser executable |
| `MUSE2API_CDP_PORT` | `19210` | Internal CDP debugging port |
| `MUSE2API_CONCURRENCY` | `2` | Max concurrent generation tasks (raise freely with server resources, default 2) |
| `MUSE2API_IMAGE_TIMEOUT` | `240` | Image generation timeout (seconds) |
| `MUSE2API_VIDEO_TIMEOUT` | `600` | Video generation timeout (seconds) |
| `MUSE2API_CHAT_TIMEOUT` | `300` | Chat generation timeout (seconds) |
| `MUSE2API_KEEPALIVE_DISABLED_ACCOUNTS` | `0` | Auto-keepalive for disabled accounts (0=off, 1=on; disabled accounts never join rotation) |

---

## ❓ FAQ

- **401 from `/api/session`?** Upstream rejected the credentials. Confirm the account can still log in at muse.ai, then re-import its Cookies.
- **403?** Access denied — possibly account permissions, server egress IP, or region/access restrictions. **Not the same as an expired Cookie.** Check the full error and your deployment network; don't blindly re-import in a loop.
- **429 / 5xx / timeout / non-JSON / no `assigned`?** This keepalive round is unconfirmed: it is no longer reported as success and no longer overwrites the last confirmed account status; the note shows the diagnosis. Accounts previously "unchecked" or "abnormal" are not forcibly rewritten to "healthy".
- **"Healthy" meaning?** It is the most recent confirmed result, not a guarantee that the current network path works. "Remaining validity" is derived from Cookie timestamps/estimates, not proof of a valid server-side session.
- **No muse.ai Cookies found / missing core keys like `hatch_sess`?** The browser isn't fully logged in yet — open https://muse.ai/ until the chat UI is visible, then import again.
- **401 from the extension?** Re-copy the API Key from the admin page (it starts with `m2a_`). For cross-domain/network errors, check the service address (https vs http) and that `http(s)://<host>/admin` loads.

---

## 🔒 Security & Privacy

- **Zero data exfiltration**: all data (including account credentials, task queues, media files) is persisted locally under `data/` — no third-party telemetry or external relay services.
- **Open-source compliance**: this project is for technical exchange, system automation / ops research, and automated testing only. Do not use it in ways that violate Meta's Terms of Service or any applicable laws.

---

## 🤝 Community Recognition & Links

This project links to and highly endorses the **[LINUX DO Community](https://linux.do/)** — thanks to the community members for discussion, feedback, and support:

- 🌐 **[LINUX DO Community (https://linux.do/)](https://linux.do/)** — a new ideal community (sincere, friendly, united, professional; building a community we can be proud of together)

---

## 👥 Contributors

Thanks to the following developers for code contributions and improvements (in PR merge order):

- 🌟 **[@cpt-kenvie](https://github.com/cpt-kenvie)** (PR [#2](https://github.com/czg86389-hub/muse2api/pull/2)) — fixed Docker Compose reading `.env` variables and sample-config override issue
- 🌟 **[@CarloCPP](https://github.com/CarloCPP)** (PR [#6](https://github.com/czg86389-hub/muse2api/pull/6)) — contributed the Tampermonkey one-click account-import script and auto-keepalive option for disabled accounts
- 🌟 **[@djs-91](https://github.com/djs-91)** (PR [#9](https://github.com/czg86389-hub/muse2api/pull/9)) — fixed Base URL collapse breaking admin-page address resolution when `MUSE2API_PUBLIC_BASE` is unset
- 🌟 **[@toby-bridges](https://github.com/toby-bridges)** (PR [#8](https://github.com/czg86389-hub/muse2api/pull/8)) — adapted to muse.ai's live Chinese UI, fixed attachment-upload confirmation and Stop-state misjudgment, hardened video-result vs. cover selection
- 🌟 **[@LF2023](https://github.com/LF2023)** (PR [#18](https://github.com/czg86389-hub/muse2api/pull/18)) — fixed video generation matching cover stills by tid alone; standardized expected matching and mis-selection guards

PRs and Issues are welcome — let's make the project stronger together!

---

## 📄 License

Released under the [MIT License](LICENSE).


## Media-Selection Regression Tests

Fixes for reference uploads being misclassified as generated results and downloads being hijacked by other page media.
Tests use an isolated temporary Chromium profile and locally synthesized DOM — they never touch Muse, read accounts, or consume generation quota.
With project dependencies and Chromium installed, run from the repo root:

```bash
python tests/test_media_selection.py
```

If the browser is not on PATH, set `MUSE2API_CHROMIUM` to the executable path.
Coverage: upload-preview exclusion, result dedup, historical-attachment exclusion, exact-source download, video-source retention,
no global-download fallback, and abort on reference-read failure. Final image-edit quality still needs acceptance testing against the live API.


## v1.5.2: Long-Running Image Jobs Behind Reverse Proxies / CDNs

The synchronous OpenAI image endpoint remains compatible, but a CDN/client may cut a long request off before generation finishes.
Production clients should use short-submit + polling instead of stretching the HTTP timeout and regenerating:

1. `POST /v1/images/tasks`: same JSON as `/v1/images/generations`; pass image-to-image references via `reference_image`; a stable `Idempotency-Key` header is recommended.
2. Receive HTTP 202 and an `id`, then `GET /v1/images/tasks/{id}` every 3 seconds.
3. On `status=completed`, read `url` or `data[0]`; on `status=failed`, show `error`. On query failure only retry the query — do not re-POST the generation.
4. Same idempotency key + same input returns the original task; same key + different input returns 409; full queue returns 429. One process shares one browser with at most 8 unfinished image tasks.

The original `/v1/images/generations` JSON and `/v1/images/edits` JSON/multipart also accept `async=true` to switch to the same async pipeline. Default sync behavior is unchanged.
`timeout` is the queue + generation wait budget (1–600 s); browser init and fetch-back have their own timeouts; clients should keep polling to the terminal state.
Task metadata is persisted; on process restart, unfinished image tasks are marked failed and never silently regenerated.
The admin page image tester now uses task polling as well.

Regression checks (no real generation quota consumed):

```bash
python tests/test_async_images.py
python tests/test_vm_wait.py engine.py --assert
```

Fixed a race where the shared-browser exception handler reset other tasks after unlocking; page-sidebar leftovers such as
`Connecting...` / `Still sending` are no longer treated as evidence that the current generation failed within 16 seconds.


## v1.5.3: Abnormal Account Status & Self-Hosted Troubleshooting

Keepalive requests originate from **your deployment server's egress IP**, not from the browser that exported the Cookies. The author's server working does not prove another server's network, region, proxy config, or the same account session is fine.

- `/api/session HTTP 401`: upstream rejected auth. Confirm the account can log in at muse.ai, then re-import Cookies.
- `HTTP 403`: access denied — possibly account permissions, server egress, or region/access limits; **not equivalent to expired Cookies**. Inspect the full error and deployment network; don't blindly re-import.
- `HTTP 429`, `5xx`, timeouts, non-JSON, or no `assigned`: this keepalive round is unconfirmed — no longer falsely reported as success and no longer overwriting the last confirmed account status; the note shows the diagnosis. Statuses of "unchecked" or "abnormal" are not forcibly rewritten to "healthy".
- Browser page-load timeouts are no longer treated directly as auth failures; only explicit auth failures mark an account abnormal.
- "Healthy" is the most recent confirmed result and does not guarantee the current network path works; "remaining validity" is a Cookie-time/estimate value, not proof of a valid server-side session. Successful checks no longer extend validity by 48 hours out of thin air — renewal follows actually returned Cookies.

After updating to v1.5.3 and restarting, click "Test" on the account to re-confirm. Previously written anomalies are not unconditionally washed to healthy. Hover the note for the full error; when reporting, include the HTTP status, version, and deployment environment — **never post Cookies, API Keys, or admin URLs containing a key**.

Bare-metal Git deploy: `git pull --ff-only` then restart the service; Docker Compose: `git pull --ff-only && docker compose up -d --build`. Save local customizations first; keep `.env` and `data/`.

Regression tests using no real accounts and no generation quota:

```bash
python tests/test_session_health.py
```
# MUSE2API 1.6.1

## Release Notes (2026-10-13)

- Fixed cross-account quota read mixing: quota queries are bound to the matching account's browser page so different accounts no longer show wrong balances/usage.
- Stale cache is kept when quota reads fail or return no valid data, with an explicit read-failure report, instead of treating invalid results as live quota.
- Fixed false-positive keepalive success: wake requests merely accepted vs. VM actually RUNNING are distinguished — wake success is only reported after the re-check state is RUNNING.
- Admin page shows quota query time and expiry hints; account tests report session validity and quota-read status separately.
- New offline regression tests covering account-quota isolation and VM wake-state confirmation.
