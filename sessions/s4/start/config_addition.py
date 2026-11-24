# --- Fixed replies (ours, never written by the model) ---
HUBS_PAGE = next((line[5:].strip() for line in (KNOWLEDGE / "hub-contacts.md").read_text(encoding="utf-8").splitlines() if line.startswith("URL: ")), "")   # the council page with the hub addresses
OFF_TOPIC_REPLY = ("Sorry, I can only help with information from the Family Hub web pages, for example "
                   "family hub activities, support for families, parenting programmes, SEND and registering a birth.")
CRISIS_REPLY = ("If you or someone else is in danger right now, call 999. "
                "You can call the National Domestic Abuse Helpline free, day or night, on 0808 2000 247, "
                "and Samaritans on 116 123.")
FALLBACK_REPLY = ("Sorry, I can't answer that here. Please contact your local family hub "
                  f"([phone numbers and addresses]({HUBS_PAGE})).")
