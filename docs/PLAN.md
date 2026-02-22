# PLAN: KutOS Settings Advanced Version Management

This plan coordinates multiple specialized agents to implement a version management system for KutOS Settings, including rolling back to older versions and resetting to a default state.

## 🛠️ Agents & Roles

1. **project-planner**: Maintains this plan and ensures architectural consistency.
2. **frontend-specialist**: designs the "Software Update" tab with a version selection dropdown, update status indicators, and the "Reset to Default" button.
3. **backend-specialist**: Implements the version fetching from GitHub, the `version` file management, and the `main.py` self-update/rollback logic.
4. **test-engineer**: Verifies the update/rollback flow and ensures the application restarts correctly.

---

## 📅 Phase 1: Foundation (backend-specialist)

- Define `VERSION`, `REPO_URL`, and `VERSION_URL` constants.
- Implement `_fetch_metadata()` to get available versions and the latest code.
- Implement generic `_apply_version(version_str)` logic that downloads the corresponding `main.py`.

## 📅 Phase 2: User Interface (frontend-specialist)

- Re-add the "Software Update" sidebar item.
- Build the `Updater` page with:
  - Current version display.
  - Version selection dropdown (ComboBox).
  - "Check for Updates" / "Apply Selected Version" button.
  - "Reset to Initial Default" button.

## 📅 Phase 3: Update & Reset Logic (backend-specialist)

- Connect UI buttons to backend logic.
- Implement the atomic file replacement (download `.tmp`, rename to `main.py`).
- Implement `_restart_app()` using `os.execv`.

## 📅 Phase 4: Verification (test-engineer)

- Mock the version file to test upgrade/downgrade.
- Verify that permissions are preserved after update.
- Verify that the app restarts into the correct version.

---

## ⏸️ CHECKPOINT: User Approval Required

Next step: Notify user of this plan and wait for approval to start Implementation.
