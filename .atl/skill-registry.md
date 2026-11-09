# Skill Registry

**Delegator use only.** Any agent that launches sub-agents reads this registry to resolve compact rules, then injects them directly into sub-agent prompts. Sub-agents do NOT read this registry or individual SKILL.md files.

See `_shared/skill-resolver.md` for the full resolution protocol.

## User Skills

| Trigger | Skill | Path |
|---------|-------|------|
| testing semantic HTML, ARIA labels, focus states, keyboard navigation, tap targets, and color contrast | a11y-debugging | C:\Users\maxim\.gemini\config\plugins\chrome-devtools-plugin\skills\a11y-debugging\SKILL.md |
| /active-orchestrator:init, /active-orchestrator:kb, /active-orchestrator:rules, /active-orchestrator:discovery, /active-orchestrator:openspec, /active-orchestrator:devops, /active-orchestrator:find-skill — or when starting an SDD project from scratch | active-orchestrator | C:\Users\maxim\.claude\skills\active-orchestrator\SKILL.md |
| cuando el usuario pide crear/generar/actualizar AGENTS.md o CLAUDE.md, "armar las reglas del proyecto", "instrucciones para los agentes", "generar claude.md", o tras correr kb-creator + roadmap-generator | agents-md-generator | C:\Users\maxim\.claude\skills\agent-instruction\SKILL.md |
| implementing auth systems, securing APIs, or debugging security issues | auth-implementation-patterns | C:\Users\maxim\.agents\skills\auth-implementation-patterns\SKILL.md |
| debugging web pages, automating browser interactions, analyzing performance, or inspecting network requests | chrome-devtools | C:\Users\maxim\.gemini\config\plugins\chrome-devtools-plugin\skills\chrome-devtools\SKILL.md |
| mentions of 'Chrome extension', 'browser extension', 'manifest.json', 'content script', 'service worker' (in browser context), 'popup', 'side panel', or Chrome Extensions API | chrome-extensions | C:\Users\maxim\.gemini\config\plugins\modern-web-guidance-plugin\skills\chrome-extensions\SKILL.md |
| diagnosing 401/403 errors, authentication redirects, session expiration, Cookie/Set-Cookie header issues, cookie banner consent conformance, or third-party cookie/SameSite/Partitioned cookie warnings | cookie-debugging | C:\Users\maxim\.gemini\config\plugins\chrome-devtools-plugin\skills\cookie-debugging\SKILL.md |
| the user mentions "largest contentful paint", "page load speed", "CWV", or wants to improve how fast their hero image or main content renders | debug-optimize-lcp | C:\Users\maxim\.gemini\config\plugins\chrome-devtools-plugin\skills\debug-optimize-lcp\SKILL.md |
| jr-orchestrator despache la fase discovery del flujo de fundacion, o cuando el usuario quiera investigar el mercado/pensar que construir antes de tener claridad | discovery-research | C:\Users\maxim\.claude\skills\discovery-research\SKILL.md |
| creating, modifying, or debugging Docker Compose configurations, wiring services together, adding a database, or setting up local dev environment | docker-compose-patterns | C:\Users\maxim\.agents\skills\docker-compose-patterns\SKILL.md |
| realizar un Code Review de un endpoint o controlador de API de backend | endpoint-code-review | C:\Users\maxim\.gemini\skills\endpoint-code-review\SKILL.md |
| converting an installed Firebase Extension into a standalone Cloud Functions codebase | extension-to-functions-codebase | C:\Users\maxim\.gemini\config\plugins\firebase\skills\extension_to_functions_codebase\SKILL.md |
| working with FastAPI APIs, Pydantic models, dependencies, streaming responses including Server-Sent Events (SSE), and serving frontend apps | fastapi | C:\Users\maxim\.agents\skills\fastapi\SKILL.md |
| building new FastAPI applications or setting up backend API projects | fastapi-templates | C:\Users\maxim\.agents\skills\fastapi-templates\SKILL.md |
| discover and install agent skills when asking "how do I do X", "find a skill for X", or extending capabilities | find-skills | C:\Users\maxim\.claude\skills\find-skill\SKILL.md |
| integrating Firebase AI Logic (Gemini API) into web applications | firebase-ai-logic-basics | C:\Users\maxim\.gemini\config\plugins\firebase\skills\firebase_ai_logic_basics\SKILL.md |
| deploying and managing full-stack web applications (Next.js, Angular) with SSR using Firebase App Hosting | firebase-app-hosting-basics | C:\Users\maxim\.gemini\config\plugins\firebase\skills\firebase_app_hosting_basics\SKILL.md |
| the user's app requires user sign-in, user management, or secure data access using auth rules | firebase-auth-basics | C:\Users\maxim\.gemini\config\plugins\firebase\skills\firebase_auth_basics\SKILL.md |
| CLI login, project creation/switching (`firebase use`), or downloading app config files (`google-services.json`, `GoogleService-Info.plist`) | firebase-basics | C:\Users\maxim\.gemini\config\plugins\firebase\skills\firebase_basics\SKILL.md |
| setting up Crashlytics, adding crash reporting, or using the Crashlytics SDK | firebase-crashlytics | C:\Users\maxim\.gemini\config\plugins\firebase\skills\firebase_crashlytics\SKILL.md |
| designing schemas with tables and relations, writing authorized queries and mutations, configuring real-time data updates, or generating type-safe SDKs | firebase-data-connect | C:\Users\maxim\.gemini\config\plugins\firebase\skills\firebase_data_connect_basics\SKILL.md |
| creating/listing Firestore databases, defining data models/indexes, writing SDK queries, or integrating Firestore SDKs | firebase-firestore | C:\Users\maxim\.gemini\config\plugins\firebase\skills\firebase_firestore\SKILL.md |
| deploying static sites/SPAs, setting up custom domains, configuring firebase.json hosting settings, or managing preview channels | firebase-hosting-basics | C:\Users\maxim\.gemini\config\plugins\firebase\skills\firebase_hosting_basics\SKILL.md |
| downloading/deploying remoteconfig JSON templates, managing version history/feature flags, setting in-app defaults, fetchAndActivate(), or real-time listeners | firebase-remote-config-basics | C:\Users\maxim\.gemini\config\plugins\firebase\skills\firebase_remote_config_basics\SKILL.md |
| auditing/reviewing rules, running red-team rule assessments, or scoring against auditor checklists | firebase-security-rules-auditor | C:\Users\maxim\.gemini\config\plugins\firebase\skills\firebase_security_rules_auditor\SKILL.md |
| designing, authoring, refactoring, and hardening production-grade Cloud Firestore Security Rules (firestore.rules) | firestore-rules-creation | C:\Users\maxim\.gemini\config\plugins\firebase\skills\firestore_rules_creation\SKILL.md |
| writing code that calls the Gemini API for text generation, multi-turn chat, multimodal understanding, image/video generation, TTS, streaming, function calling, or structured output | gemini-api-dev | C:\Users\maxim\.gemini\config\plugins\gemini-api\skills\gemini-api-dev\SKILL.md |
| building real-time, bidirectional streaming applications with the Gemini Live API, or migrating legacy Live models to Gemini 3.8 Live | gemini-live-api-dev | C:\Users\maxim\.gemini\config\plugins\gemini-api\skills\gemini-live-api-dev\SKILL.md |
| generative video editing, text-to-video, image-referenced video generation, first-and-last-frame transitions, and video extensions using Gemini Omni 1.1 Flash | gemini-omni-flash-api | C:\Users\maxim\.gemini\config\plugins\gemini-api\skills\gemini-omni-flash-api\SKILL.md |
| design, implement, and debug autonomous AI agents and multi-agent systems using the Google Antigravity (AGY) SDK | google-antigravity-sdk | C:\Users\maxim\.gemini\config\plugins\google-antigravity-sdk\skills\google-antigravity-sdk\SKILL.md |
| user asks to create, build, or generate a knowledge base for a project, document a project from source documents, or "armar base de conocimiento" / "crear KB" | kb-creator | C:\Users\maxim\.claude\skills\kb-creator\SKILL.md |
| user reports high memory usage, OOM errors, or wants to capture, compare, or inspect heap snapshots with Chrome DevTools MCP memory tools | memory-leak-debugging | C:\Users\maxim\.gemini\config\plugins\chrome-devtools-plugin\skills\memory-leak-debugging\SKILL.md |
| MANDATORY FIRST for all HTML/CSS and client-side JS tasks; modals, tables, dark mode, positioning, container queries, view transitions, web components, CWV | modern-web-guidance | C:\Users\maxim\.gemini\config\plugins\modern-web-guidance-plugin\skills\modern-web-guidance\SKILL.md |
| designing or reviewing a PostgreSQL-specific schema, choosing column types, keys, constraints, or indexes | postgresql-table-design | C:\Users\maxim\.agents\skills\postgresql-table-design\SKILL.md |
| user asks to create, build, regenerate, or update CHANGES.md, roadmap, change map, implementation plan | roadmap-generator | C:\Users\maxim\.claude\skills\roadmap-generator\SKILL.md |
| create a skill from scratch, edit or optimize an existing skill, run evals, benchmark performance, or optimize trigger description | skill-creator | C:\Users\maxim\.claude\skills\skill-creator\SKILL.md |
| list_pages, new_page, or navigate_page fail, or Chrome DevTools MCP server initialization fails | troubleshooting | C:\Users\maxim\.gemini\config\plugins\chrome-devtools-plugin\skills\troubleshooting\SKILL.md |
| investigar competidores o soluciones existentes a partir de una URL | web-scraper | C:\Users\maxim\.claude\skills\web-scraper\SKILL.md |
| iOS project needs dependencies installed (e.g. Firebase, Alamofire), modifying Xcode projects (.pbxproj) safely | xcode-project-setup | C:\Users\maxim\.gemini\config\plugins\firebase\skills\xcode_project_setup\SKILL.md |

## Compact Rules

Pre-digested rules per skill. Delegators copy matching blocks into sub-agent prompts as `## Project Standards (auto-resolved)`.

### a11y-debugging
- Page-scoped tools (`take_snapshot`, `list_console_messages`, `evaluate_script`) require `pageId` from `list_pages` or `new_page`.
- Use `take_snapshot` (accessibility tree) to inspect what assistive tech actually sees; CSS `opacity: 0` is not hidden from screen readers, use `display: none` or `aria-hidden="true"`.
- Prefer native semantic HTML elements (`<button>`, `<dialog>`, `<nav>`) over ARIA roles on `<div>` elements.
- Verify interactive elements are keyboard focusable (`tabindex="0"`, not negative) with visible `:focus-visible` styles.
- Tap targets must be at least 48x48px on touch viewports (`touch-action: manipulation`).
- Color contrast must meet WCAG AA minimums (4.5:1 for normal text, 3:1 for large text).
- Always pair non-text media and icon buttons with descriptive `alt` text or `aria-label`.

### active-orchestrator
- Thin orchestrator: only owns `.active-orchestrator-state.json` and the `step` field; does not make architectural decisions directly.
- Strict phase order (§4.2): `openspec init` -> `[discovery-research]` -> `kb-creator` -> `roadmap-generator` -> `find-skill` -> `skill-registry` -> `agent-instruction`.
- Hold mandatory human checkpoint (*Continuar / Ajustar / Parar acá*) at every phase boundary; never chain phases automatically without user confirmation.
- Phase degradation: if a sub-skill is missing, fall back to inline execution or ask user to install.
- Never write `openspec/` scaffolding by hand; rely on `openspec init` and openspec CLI.

### agents-md-generator
- Generates canonical `AGENTS.md` and symlink/copy `CLAUDE.md` from `knowledge-base/` and `CHANGES.md`.
- Read `.atl/skill-registry.md` as single source of truth for available skills; do NOT re-scan filesystem.
- DRY: Never copy compact rules into `AGENTS.md`; only map skills to agent roles and link to `.atl/skill-registry.md`.
- Hard rules section is interactive: confirm stack-specific hard rules with user before finalizing.
- Do not repeat global instructions already present in global agent configuration.

### auth-implementation-patterns
- Never store plaintext passwords; hash with bcrypt or Argon2id outside event loops (use threadpool or executor).
- Short-lived access tokens (15-30 min max); store in `httpOnly`, `secure`, `sameSite="lax"|"strict"` cookies, never in localStorage.
- Enforce server-side authorization checks on every request; never trust client-side role or permission assertions.
- Apply strict rate-limiting on authentication endpoints (e.g. 5 failures per 60s) returning HTTP 429 and `Retry-After`.
- Constant-time password verification and identical error messages for failed logins to prevent user enumeration.
- Always rotate secrets and sign JWTs with asymmetric keys (RS256) or strong cryptographic secrets (HS256 with 256+ bits).
- Validate all incoming token claims (`exp`, `nbf`, `iss`, `aud`) on every protected endpoint.

### chrome-devtools
- Always pass `pageId` parameter to page-scoped tools (`list_pages`, `new_page`, `navigate_page`).
- Browser profile persists across tool calls; configure options via CLI arguments when launching MCP.
- Use `--categoryExtensions` flag for extension inspection, `--memoryDebugging` flag for heap snapshots.
- Wait for network idle or DOM stabilization after `navigate_page` before capturing snapshots.
- Use `evaluate_script` for DOM inspection and `take_snapshot` for accessibility/semantic validation.

### chrome-extensions
- Manifest V3 required: `manifest_version: 3`; no remote code execution allowed (no `eval()`, inline scripts, or remote scripts).
- Background scripts run as ephemeral Service Workers; never use persistent global in-memory state (use `chrome.storage.local` or `session`).
- Use `declarativeNetRequest` instead of blocking `webRequest` API for network interception and rule-based modifications.
- Declare minimal permissions; prefer optional permissions requested at runtime via `chrome.permissions.request()`.
- Content scripts run in isolated worlds: communicate with page context via `window.postMessage()` and with background via `chrome.runtime.sendMessage()`.
- Use `action` key instead of legacy `browser_action` or `page_action`.
- Always handle `chrome.runtime.lastError` in callbacks or use Promise-based APIs.

### cookie-debugging
- Verify cookie security flags: `HttpOnly` (blocks JS access/XSS), `Secure` (requires HTTPS), `SameSite=Lax|Strict` (mitigates CSRF).
- Partitioned cookies (`SameSite=None; Secure; Partitioned`) required for cross-site third-party contexts (CHIPS).
- Diagnose 401/403 redirects by checking domain/path scope match and cookie expiration timestamps (`Expires` / `Max-Age`).
- Check `Set-Cookie` response headers for syntax issues or overwriting collisions across subdomains.
- Confirm cookie consent banner integration complies before persisting non-essential cookies.

### debug-optimize-lcp
- Identify LCP element using DevTools MCP performance trace or Lighthouse audit (`take_snapshot` / `lighthouse_audit`).
- Preload the LCP hero image with `<link rel="preload" as="image" fetchpriority="high">` in `<head>`.
- Never lazy-load the LCP image (`loading="lazy"` on LCP is an antipattern; use `loading="eager"`).
- Optimize LCP image formats: serve modern AVIF or WebP with responsive `srcset` and proper `sizes`.
- Eliminate render-blocking resources: defer or async non-critical CSS/JS above the fold.
- Ensure CDN caching and fast TTFB (<800ms) with HTTP/2 or HTTP/3 server push/early hints.

### discovery-research
- Investigates project requirements before building Knowledge Base; reads input docs and scrapes competitor URLs.
- Guides structured Q&A across the full checklist: problem, users, use cases, necessary/optional features, business rules, integrations, constraints, risks, open questions.
- Produces `discovery/discovery.md` and updates `state.discovery` in `.active-orchestrator-state.json`.
- Never writes production code or builds the final Knowledge Base directly (hands off to `kb-creator`).

### docker-compose-patterns
- Use canonical `compose.yaml` naming (never legacy `docker-compose.yml`).
- Pin exact image tags; never use `latest` or omit tag in production/test configurations.
- Use `depends_on` with `condition: service_healthy`; every depended service must declare a `healthcheck`.
- Health checks must use native client tools (`pg_isready`, `redis-cli ping`, `mysqladmin ping`).
- For distroless/scratch images without shells, use a curl sidecar (`network_mode: "service:<name>"`).
- Store persistent data in top-level named `volumes`; bind mounts only in `compose.override.yaml` for dev.
- Never hardcode secrets in Compose; use `env_file:` or environment variable substitution with fallbacks `${VAR:-default}`.
- NEVER run destructive volume pruning (`docker compose down -v`, `volume rm`) without explicit user confirmation.

### endpoint-code-review
- Strict input validation: validate, type, and sanitize all parameters (body, query, headers) before domain execution.
- Safe error handling: catch exceptions and return appropriate HTTP status codes (400, 401, 403, 404, 409, 500) without leaking stack traces or internal DB schema.
- Explicit auth checks: verify caller identity and role/permissions explicitly against database or token claims.
- Report any security vulnerability or missing check under the mandatory section header: `🚨 Hallazgos de Seguridad`.

### extension-to-functions-codebase
- Converts installed Firebase Extensions into standalone Cloud Functions codebases.
- Upgrade triggers from Cloud Functions v1 to v2 (`firebase-functions/v2`) for improved concurrency and scaling.
- Replace extension param templates with `params.defineString()`, `params.defineSecret()` in v2.
- Configure declarative security and IAM permissions with minimum required role assignment.

### fastapi
- Always use `typing.Annotated` for parameters and dependencies (`Annotated[int, Path()]`, `Annotated[Session, Depends(get_db)]`).
- Create reusable type aliases for common dependencies (e.g., `CurrentUserDep = Annotated[User, Depends(get_current_user)]`).
- Never use Ellipsis (`...`) as default for required Pydantic fields or path parameters.
- Avoid deprecated `ORJSONResponse` or `UJSONResponse`; declare return types or `response_model` for Rust-based serialization.
- Set prefix, tags, and dependencies at `APIRouter` declaration, not in `app.include_router()`.
- Use regular `def` for blocking synchronous I/O (runs in threadpool); use `async def` ONLY for pure async/await non-blocking code.
- Never use Pydantic `RootModel`; use `Annotated[list[T], Field(...), Body()]` with FastAPI's automatic `TypeAdapter`.
- One HTTP operation per function; never combine multiple verbs in a single endpoint.
- For SSE streaming, use `response_class=EventSourceResponse` and `yield ServerSentEvent(...)`.

### fastapi-templates
- Layered architecture: Router (`api/v1/`) -> Service (`services/`) -> Repository (`repositories/`) -> Model (`models/`).
- Database session management via `Depends(get_db)` with async context manager and automatic cleanup.
- Async SQLAlchemy 2.0+ engine with `asyncpg` (`postgresql+asyncpg://...`), `AsyncSessionLocal = sessionmaker(class_=AsyncSession, expire_on_commit=False)`.
- Repositories perform CRUD without committing; commit ownership belongs to Unit of Work or service boundary.
- For pytest async tests, use `ASGITransport(app=app)` with `httpx.AsyncClient(transport=transport, base_url="http://test")`.
- In-memory SQLite async testing with `sqlite+aiosqlite:///:memory:` and `app.dependency_overrides[get_db]`.

### find-skills
- Discovers and installs agent skills from verified repositories and registries.
- Evaluate skill quality: check install count, maintenance status, and specific match to tech stack.
- Install skills globally or in project using `npx skills add <repo>@<skill>` or local skill placement.
- After installing or updating skills, trigger `skill-registry` to update the project registry.

### firebase-ai-logic-basics
- Integrate Gemini models into Firebase apps using official Firebase AI Logic SDKs.
- Always enforce Firebase App Check to prevent unauthorized API quota abuse and endpoint scraping.
- Enforce structured outputs by passing JSON schema to `generationConfig.responseMimeType = "application/json"`.
- Never expose Gemini API keys in client-side code; use Firebase Genkit or Cloud Functions backend proxies.

### firebase-app-hosting-basics
- Configures and deploys full-stack SSR web applications (Next.js, Angular) with Firebase App Hosting.
- App Hosting configuration lives in `apphosting.yaml`; specify runtime environment, CPU/memory limits, and concurrency.
- Store sensitive secrets (API keys, DB credentials) using Google Cloud Secret Manager, referenced in `apphosting.yaml`.
- Set up automatic GitHub CI/CD integration using Firebase CLI; requires Blaze billing plan.

### firebase-auth-basics
- Configure Firebase Authentication for email/password, OAuth providers, and anonymous sign-in.
- On client, persist auth state using `indexedDBLocalPersistence` or `browserLocalPersistence`.
- On server/API endpoints, verify ID tokens using `firebase-admin` `auth.verifyIdToken(token)`.
- Use custom claims (`setCustomUserClaims`) for lightweight role flags, keeping payload under 1000 bytes.
- Pair with Firestore Security Rules using `request.auth.uid` and `request.auth.token`.

### firebase-basics
- Foundational Firebase CLI workflows: install `firebase-tools`, login with `firebase login --no-localhost`.
- Select active project with `firebase use <project-id>` or `firebase use --add`.
- Download config files: `google-services.json` (Android) and `GoogleService-Info.plist` (iOS).
- Never use this skill for Firestore rules, App Hosting SSR, or Cloud Functions deployment.

### firebase-crashlytics
- Provisions and configures Firebase Crashlytics SDK for mobile and desktop applications.
- Initialize Crashlytics at application entry point before any other asynchronous initialization.
- Log non-fatal errors with `recordError()` including relevant custom keys and user identifiers.
- Strip PII (passwords, emails, credit card data) before logging keys or custom exception traces.
- Ensure dSYM/mapping files are uploaded to Firebase console during production release builds.

### firebase-data-connect
- Builds and deploys Firebase SQL Connect (PostgreSQL backend) with GraphQL-like schema and operations.
- Define relational schema in `.gql` files with `@table`, `@col`, and `@ref` directives.
- Queries and mutations must be pre-declared in connector `.gql` files; dynamic ad-hoc client queries are not allowed.
- Authorize operations with `@auth` directives: `level: USER | PUBLIC | NO_ACCESS`.
- Generate type-safe client SDKs using `firebase dataconnect:sdk:generate`.

### firebase-firestore
- Document and collection data modeling: keep documents <= 1MB; avoid high-frequency writes (>1 write/sec) to a single document.
- Composite queries with multiple inequality/sort fields require explicit composite indexes declared in `firestore.indexes.json`.
- Pagination: use `limit()` with `startAfter(lastVisibleDocument)` cursor pagination; never offset large result sets.
- Use batched writes (`batch.commit()`) or transactions (`runTransaction()`) for atomic multi-document mutations.
- Security rules: always validate schema, types, and permissions in `firestore.rules`.

### firebase-hosting-basics
- Deploys static sites and single-page applications via classic Firebase Hosting.
- Configure `firebase.json`: define `public` directory, headers, redirects, and SPA rewrites (`"source": "**", "destination": "/index.html"`).
- Manage preview channels with `firebase hosting:channel:deploy <channel-name>`.
- Configure custom caching headers (`Cache-Control: max-age=...`) for static assets vs mutable HTML.

### firebase-remote-config-basics
- Manage Remote Config parameters, conditions, and percentage rollouts via JSON templates.
- Define in-app default values in client code before fetching remote configurations.
- Use `fetchAndActivate()` with reasonable minimum fetch intervals (start with 12 hours in production, 0 in development).
- Add real-time config listeners (`addOnConfigUpdateListener`) for instant feature flag toggles without app restarts.

### firebase-security-rules-auditor
- Audit `firestore.rules` and `storage.rules` against privilege escalation, role bypasses, and data leaks.
- Ensure `read` rules do not leak unowned documents; check `resource.data` ownership on every collection.
- Separate `create` and `update` rules: verify immutable fields (`createdAt`, `id`, `ownerId`) cannot be altered on update.
- Enforce strict type, size, and schema checking on `request.resource.data` using helper functions.
- Disallow open read/write access (`allow read, write: if true;` is a critical security failure).

### firestore-rules-creation
- Author production-grade `firestore.rules` with granular helper functions.
- Structure rules into: `isAuthenticated()`, `isOwner(userId)`, `hasRole(role)`, `isValidSchema()`.
- Use `request.resource.data.diff(resource.data).affectedKeys()` to protect immutable fields.
- Always write rules for `get`, `list`, `create`, `update`, and `delete` separately instead of blanket `write`.
- Verify rule changes with `@firebase/rules-unit-testing` local emulator suite.

### gemini-api-dev
- Use official `google-genai` SDK (`from google import genai` in Python, `@google/genai` in TS); never use deprecated `google-generativeai`.
- Initialize client with `client = genai.Client()`; reads `GEMINI_API_KEY` from environment automatically.
- Model naming: use current recommended models (`gemini-2.5-flash`, `gemini-2.5-pro`).
- For structured outputs, pass Pydantic model to `config=types.GenerateContentConfig(response_mime_type="application/json", response_schema=MyModel)`.
- Use `client.models.generate_content_stream()` for streaming responses.
- Implement exponential backoff for HTTP 429 / resource exhausted errors.

### gemini-live-api-dev
- Real-time bidirectional audio/video/text streaming over WebSockets using Gemini Live API.
- Use `client.aio.live.connect(model="gemini-2.0-flash-exp")` for WebSocket sessions.
- Audio format: PCM 16-bit, 16kHz or 24kHz mono little-endian.
- Support Voice Activity Detection (VAD) and client-side audio interruption handling.
- Asynchronous function calling: handle tool call responses and stream results back over the live session.

### gemini-omni-flash-api
- Generative video editing and text-to-video using Gemini Omni Flash (`gemini-omni-1.1-flash`).
- Pre-process source videos with `ffmpeg` to match resolution and framerate constraints before uploading.
- Strip original audio tracks before processing if full sound regeneration or background score is needed.
- Support first-and-last-frame transitions and turn-by-turn video extension pipelines.

### google-antigravity-sdk
- Design autonomous multi-agent systems and tools using the Google Antigravity SDK.
- Configure agents with distinct persona scopes, explicit input parameters, and structured outputs.
- Sub-agent delegation: pass pre-resolved compact rules and stack conventions in launch prompts.
- Maintain persistent agent memories and state files across multi-turn interactions.

### kb-creator
- Generates 10 canonical markdown files in `knowledge-base/` from source documents or interactive discovery.
- Strict canonical structure: `01_vision_y_objetivos.md` through `10_preguntas_abiertas.md` plus `README.md`.
- Ingest mode: silent generation from `docs/`; never invents domain facts, flags uncertainties in `10_preguntas_abiertas.md`.
- Encodes all business rules with unique identifiers (`RN-01`, `RN-02`, etc.) in `05_reglas_de_negocio.md`.
- Updates `state.kb` in `.active-orchestrator-state.json` upon completion.

### memory-leak-debugging
- Diagnose high memory and OOM issues using Chrome DevTools MCP memory profiling tools.
- Capture baseline heap snapshot (`take_snapshot`), execute suspected leak scenario, capture second snapshot, and compare.
- Identify detached DOM trees, uncleared event listeners, dangling timers (`setInterval`), and unbounded closures.
- Inspect allocation timelines to identify objects retaining memory in the retainer graph.

### modern-web-guidance
- MANDATORY: Consult before writing frontend HTML/CSS and client-side JS; modern web standards supersede outdated patterns.
- Use native HTML elements (`<dialog>`, `<popover>`, `<details>`) instead of custom JS modal/dropdown libraries.
- Prefer CSS modern layout features: Container Queries (`@container`), Subgrid, Anchor Positioning, CSS `@starting-style`.
- Use native View Transitions API (`document.startViewTransition()`) for fluid page and state animations.
- Optimize Core Web Vitals: `fetchpriority="high"` on LCP, `content-visibility: auto` on off-screen content, zero layout shifts (CLS).

### postgresql-table-design
- Primary keys: prefer `BIGINT GENERATED ALWAYS AS IDENTITY`; use `UUID` only when distributed uniqueness is required.
- PostgreSQL does NOT auto-index foreign key columns: manually create an index on every FK referencing column!
- Always use `snake_case` identifiers; avoid unquoted mixed-case names (PostgreSQL folds unquoted identifiers to lowercase).
- Strings: use `TEXT` with optional `CHECK (LENGTH(col) <= N)`; avoid legacy `VARCHAR(N)` or `CHAR(N)`.
- Money/decimals: use `NUMERIC(p, s)`; never use `FLOAT`, `DOUBLE`, or legacy `MONEY`.
- Timestamps: use `TIMESTAMPTZ`; avoid `TIMESTAMP` (without timezone) or `TIMETZ`.
- Soft deletes: enforce partial unique index `CREATE UNIQUE INDEX ... WHERE borrado_en IS NULL`.
- JSONB: use `JSONB` (not `JSON`) and index with GIN (`jsonb_path_ops`); extract frequently filtered scalars into generated columns.

### roadmap-generator
- Generates `CHANGES.md` from `knowledge-base/`: operational roadmap of all OpenSpec changes with dependency graph.
- Calculates critical path, parallelism gates, and phase groupings.
- For each change, defines: Change ID (`C-01`), scope, governance level, dependencies, and "Leer antes" KB file pointers.
- Strictly deterministic and fire-and-forget; updates `state.roadmap` in `.active-orchestrator-state.json`.

### skill-creator
- Authors, tests, and optimizes agent skills following the standard SKILL.md format.
- Frontmatter must include `name` (kebab-case) and `description` with explicit `Trigger:` phrasing.
- Body structure: When to Use, Core Concepts / Rules, Detailed Patterns, Best Practices, Pitfalls.
- Measure skill trigger accuracy and optimize descriptions to prevent false positives or missed invocations.

### troubleshooting
- Diagnose Chrome DevTools MCP connection, browser target, and session failure issues.
- Verify CDP WebSocket port availability and remote debugging flags (`--remote-debugging-port`).
- Handle target crashes or page navigations by re-listing active targets via `list_pages`.
- Ensure clean teardown of stale browser processes before re-initializing connection.

### web-scraper
- Investigates competitor products and public URLs without external API keys or extra costs.
- Extracts structured notes: problem solved, target users, features, pricing model, and positioning.
- Writes markdown notes into `discovery/` directory for consumption by `discovery-research` and `kb-creator`.
- Not designed for heavy SPA crawling or anti-bot bypass; focuses on content extraction from static/read-accessible pages.

### xcode-project-setup
- Safely modifies Xcode project files (`.pbxproj`) to add Swift Package Manager (SPM) dependencies.
- Never manually edit `.pbxproj` strings without parsing the PBX objects graph.
- Ensure package dependencies and framework build phases are correctly linked to target schemes.
- Verify target compatibility and build settings before committing modifications.

## Project Conventions

| File | Path | Notes |
|------|------|-------|
| `CHANGES.md` | `CHANGES.md` | Roadmap de 10 changes de implementación, camino crítico y dependencias |

Read the convention files listed above for project-specific patterns and rules. All referenced paths have been extracted — no need to read index files to discover more.
