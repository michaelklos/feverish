# Project Plan: "Feverish" iOS Client

**Goal:** Build a modern, native iOS RSS reader tailored specifically for the self-hosted [Feverish](https://github.com/michaelklos/feverish) backend.
**Target Audience:** Personal use (initially), potentially TestFlight/App Store later.
**Developer Experience:** Beginner (No prior iOS/Swift experience).

---

## 🛠 Prerequisites & Setup

Before starting the first coding session, ensure you have:

1.  **Hardware:** A Mac running macOS Sequoia (or latest supported OS).
2.  **Software:** [Xcode](https://developer.apple.com/xcode/) (Free from Mac App Store).
    *   *Note: It is a large download (10GB+).*
3.  **Account:** An Apple ID (Free).
    *   *Note: A paid Apple Developer Program membership ($99/yr) is ONLY required if you want to distribute to others via TestFlight or the App Store. You can deploy to your own device for free.*

---

## 🏗 Tech Stack Recommendation

We will use the most modern, "Apple-recommended" stack to ensure longevity and ease of learning.

*   **Language:** **Swift 6** (Safe, fast, modern).
*   **UI Framework:** **SwiftUI** (Declarative, less code, live previews).
*   **Architecture:** **MVVM** (Model-View-ViewModel).
    *   *Why:* Separates the "look" (View) from the "data" (Model) and the "logic" (ViewModel).
*   **Networking:** **Async/Await** (Modern concurrency, no "callback hell").
*   **Local Database:** **SwiftData** (New in iOS 17).
    *   *Why:* We need to store articles offline so the app works in the subway/airplane. SwiftData is much easier to learn than Core Data.

---

## 🗺 Development Roadmap

We will build this iteratively. Do not try to build the whole thing at once.

### Phase 1: The "Hello Fever" (Connectivity)
**Goal:** Authenticate with the server and prove we can talk to it.
1.  Create a new Xcode Project (iOS App).
2.  Build a simple Login Screen (Server URL, Email, Password).
3.  Implement the `FeverAPIClient` class.
    *   Logic: Calculate MD5 hash of `email:password`.
    *   Request: `POST /api/?api_key=...`
4.  **Success State:** App prints "Auth Successful: 1" to the console.

### Phase 2: The Data Layer (Models)
**Goal:** Define Swift structures that match our Django models.
1.  Create Swift `structs` that mirror the JSON response:
    *   `FeverGroup` (id, title)
    *   `FeverFeed` (id, title, url, site_url, is_spark)
    *   `FeverItem` (id, title, author, html, is_read, is_saved)
2.  **Crucial Step:** Handle the custom `user_title` logic we added to the backend.
    *   *Swift Logic:* `var displayName: String { return user_title ?? title ?? url }`

### Phase 3: The Feed List (UI)
**Goal:** Display groups and feeds in a sidebar/list.
1.  Fetch `?feeds` and `?groups` from API.
2.  Build `SidebarView`:
    *   Section: "Unread" (Smart list)
    *   Section: "Saved" (Smart list)
    *   Section: Groups (Iterate through groups)
        *   List Feeds inside groups.
3.  **Success State:** You see your actual feeds from the server in a list on your iPhone simulator.

### Phase 4: The Article List & Reader
**Goal:** Read content.
1.  Build `ArticleListView`:
    *   Fetch `?items&feed_ids=...`
    *   Display a list of cards (Title, Preview, Date).
    *   *Note:* We need to convert the Unix Timestamp (`created_on_time`) to a readable Date string.
2.  Build `ArticleDetailView`:
    *   Use `WebView` (WebKit) to render the HTML content.
    *   Apply simple CSS to make it readable (Dark mode support).

### Phase 5: Sync & Persistence (The Hard Part)
**Goal:** Offline support and state syncing.
1.  Integrate **SwiftData**.
2.  **Sync Logic:**
    *   On pull-to-refresh: Fetch *new* items since `last_refreshed_on_time`.
    *   Save them to local database.
    *   UI reads from local database (not directly from network).
3.  **Action Sync:**
    *   When user marks read: Update local DB immediately (UI updates instantly) -> Send API request in background.

---

## 📝 "Instruction Prompt" for Future Session

When you are ready to start, paste this into our chat to kick off the session with full context:

> "I am ready to start building the iOS client for Feverish.
>
> **Context:**
> - Backend: Feverish (Django/Postgres) deployed on Azure.
> - API Endpoint: `https://news.klos.wtf/api/`
> - Auth: MD5(email:password)
> - My Experience: None (Beginner).
> - Tools: Xcode is installed.
>
> **Objective:**
> Let's start with **Phase 1**. Please guide me through creating the Xcode project and building a basic Login View that can successfully authenticate against my live server. Explain the Swift code as we go."

---

## 📚 Key Concepts to Preview (Optional)
If you want to read ahead, look up these terms:
1.  **SwiftUI `State` and `Binding`:** How data moves between views.
2.  **`Codable`:** How Swift converts JSON to Objects (Magic!).
3.  **`URLSession`:** How iOS makes HTTP requests.
