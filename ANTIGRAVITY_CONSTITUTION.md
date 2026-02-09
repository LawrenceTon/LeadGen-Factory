# 📜 THE ANTIGRAVITY CONSTITUTION (Immutable Laws)

This document establishes the verified protocols for the LeadGen Factory. Failure to adhere to these 5 rules is a critical system failure.

## 1. THE VACUUM PROTOCOL (Selector Agnosticism)
**"Grab everything, filter later."**
*   Never rely on specific CSS selectors (like `div.g` or `span.email`).
*   **Action:** Always fetch **ALL** links (`a[href]`) and **ALL** body text, then filter locally using Python logic.

## 2. THE NORDIC TRANSFORMATION (Data Sanitization)
**"Computers struggle with international characters; we do not."**
*   **Action:** Before any matching logic, strictly normalize inputs using a custom transliteration map (e.g., `Ø` → `o`, `Å` → `a`, `Ü` → `u`).

## 3. PREDICTIVE DORKING (Answer-Based Search)
**"Do not ask questions. Search for answers."**
*   Do not query: "Who is the CEO of Company X?"
*   **Action:** Calculate the likely answer first (e.g., `covregaard@gmail.com` or `"John Doe" @company.com`) and search for that specific string to bypass privacy filters.

## 4. PARALLEL HUNTING (Dual-Track Architecture)
**"A target has two lives: Corporate and Personal."**
*   **Action:** Always execute simultaneous searches for `@{company_domain}` and `@gmail` / `@outlook`. Finding one does **NOT** stop the hunt for the other.

## 5. SNIPPET SNIPING (Pre-Click Analysis)
**"The truth is often in the preview."**
*   Data is often visible in the search preview but hidden behind login walls on the site.
*   **Action:** Always regex-scan the raw HTML of the search results page (`res.inner_text()`) **before** navigating away.

---

# 🛠️ OPERATIONAL GUIDELINES

## Syntax Strictness
*   **Async/Await:** When writing Python `async` functions, **NEVER** put `try: await ... except:` on a single line. It causes syntax errors. Always use multi-line blocks.

## Visual Logic
*   **"Blind or Lazy"**: If a strategy fails, assume the bot was "blind" (selector issue) or "lazy" (didn't scroll/click).
*   **Remedy:** Fix it by making the bot act more human (scrolling, clicking internal links).

## Verification Protocol
*   **Trust Nothing:** Never assume an email is correct unless it passes the **"Pattern Match"** (Name/Initials match the email string).
*   **Labeling:** If unverified, strictily label it **"Unverified Guess"**.
