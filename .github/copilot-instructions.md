# SESSION MANAGEMENT INSTRUCTIONS
Use session files to track development progress and goals. These files are located in `docs/sessions/` and should be created for each new development session.
Always check current time and date with `date` command before write date related information in session files.
Use the following format for session files:
- **start**: Start a new development session by creating a session file in `docs/sessions/` with the format YYYY-MM-DD-HHMM-{NAME}.md.
The session file should begin with:
1. Session name and timestamp as the title. name should be descriptive of the session's focus.
2. Session overview section with start time
3. Goals section (ask user for goals if not clear)
4. Empty progress section ready for updates
After creating the file, create or update `docs/sessions/.current-session` to track the active session filename.
- **update**: Check if `docs/sessions/.current-session` exists to find the active session. If no active session, start a new one. If session exists, update the session file with progress, challenges, any issues encountered, solutions implemented, and any changes to goals. This should be done regularly during the session. Keep updates concise but comprehensive for future reference.

- **end**: At the end of the session, update the session file with a summary of what was accomplished, any challenges faced, key accomplished, all features implemented, problem and solutions, breaking change, lessons learned, what was not finished, tip for future development, and next steps. The summary should be thorough enough that another developer (or AI) can understand everything that happened without reading the entire session. Then remove the session file from `docs/sessions/.current-session` file (don't remove it, just clear its contents) to mark the session as complete.

# CODE/WORK INSTRUCTIONS
- Use `uv pip ...` for pip operation to ensure the correct Python environment is used.
- Do not run notebook cells. It need to restart the kernel to apply changes, which is not possible in this environment. Instead, write code in `.py` files and run them directly.
