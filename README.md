# App 11: The "Hold-for-Me" Travel Concierge (Voice)

## Concept
A consumer-facing agent that calls airlines or hotels on behalf of a user, waits on hold, and only calls the user back when a live representative is ready.

## Workflow
1.  **Request:** User asks via app or SMS: "Change my flight from Monday to Tuesday."
2.  **Outbound Call:** Agent calls the airline's customer service number.
3.  **IVR Navigation:** Uses an LLM to navigate the "Press 1 for Support" menus.
4.  **Hold Management:** Listens to the hold music and detects when a human agent answers (silence detection + "Hello" detection).
5.  **User Callback:** Immediately calls the user back and bridges the two calls so the user can speak directly to the airline representative.

## Tech Stack
- **Language:** Python
- **LLM Library:** Microsoft AutoGen
- **Telephony:** MessageBird
- **Audio Intelligence:** AssemblyAI (LeMUR for reasoning)
- **TTS:** Microsoft Azure Cognitive Services (Neural Voice)
- **Browser Automation:** Playwright (for flight search backup)
