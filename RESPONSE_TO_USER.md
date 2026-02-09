Fixed! I have replaced the `find_decision_maker` logic with the corrected version.

**The Fix:**
-   **Problem**: The bot was searching for `site:linkedin.com/in/ "https://jackfruit365.com"`, which confuses Google.
-   **Solution**: Added a cleaner utility specifically for this module.
    -   It strips `https://`, `http://`, `www.`, and the TLD (`.com`).
    -   It transforms `https://www.jackfruit365.com` -> `jackfruit365`.
    -   **New Query**: `site:linkedin.com/in/ "jackfruit365" ("CEO" OR "Founder")`.

**Verified**:
-   Replaced code in `modules/harvester.py`.
-   Verified syntax stability.
-   Ready for immediate testing.
