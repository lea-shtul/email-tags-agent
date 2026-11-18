"""Made-up emails (no real names or data) with the expected label, or "none".

Only emails that reach the model: no rule-only labels here.
Borderline cases are marked with a comment.
"""
DATASET_NAME = "email-labels-v2"

# (sender, subject, snippet, expected label)
# v1: exactly as uploaded to email-labels-v1 (experiment baseline-631edd60). Do not edit.
EMAILS_V1 = [
    # --- טכנולוגיה ---
    ("AI Weekly <news@aiweekly.example>", "This week: smaller models, faster agents",
     "Top stories: a new open-weights model beats last year's benchmarks; how to cut LLM latency in half; 3 tools for testing agents.",
     "טכנולוגיה"),
    ("DevTools Digest <digest@devtools.example>", "גרסה 4.0 של ספריית הבדיקות שלנו שוחררה",
     "מה חדש: הרצה מקבילית של טסטים, תמיכה ב-Python 3.14 ודוח כיסוי משופר. מדריך שדרוג בפנים.",
     "טכנולוגיה"),
    ("CloudBox Developers <dev-updates@cloudbox.example>", "API v3 is now generally available",
     "Starting today the v3 endpoints support streaming responses and batch requests. v2 will be deprecated in six months.",
     "טכנולוגיה"),
    ("קהילת קוד פתוח <hello@opencode-il.example>", "מיטאפ: בניית סוכני AI עם גרפים",
     "ביום שלישי הקרוב נארח הרצאה על סוכנים, גרפים ו-human-in-the-loop. ההרשמה בקישור.",
     "טכנולוגיה"),
    # borderline: product update that is also marketing
    ("PixelCraft <updates@pixelcraft.example>", "New in PixelCraft: export animations as code",
     "We just shipped a plugin that turns your animations into React components. Try it in your next project.",
     "טכנולוגיה"),

    # --- פרסומות ---
    ("ShopNova <deals@shopnova.example>", "פרסומת | 70% הנחה רק היום",
     "מבצע בזק על אלפי מוצרים, משלוח חינם בהזמנה מעל 99 ש\"ח. ההצעה בתוקף עד חצות.",
     "פרסומות"),
    ("RunFast <news@runfast.example>", "BLACK FRIDAY starts now",
     "Up to 50% off running shoes and apparel. Members get early access to the best deals.",
     "פרסומות"),
    # empty subject
    ("ShopNova <deals@shopnova.example>", "",
     "נשארו לך 3 קופונים שעומדים לפוג. השתמשי בהם לפני סוף השבוע וקבלי 20 ש\"ח הנחה.",
     "פרסומות"),
    # borderline: software product, but the email is a discount offer
    ("PDF Studio <mail@pdfstudio.example>", "Sign documents faster - 40% off Pro",
     "Upgrade to PDF Studio Pro this week and save 40%. Edit, sign and share PDFs from any device.",
     "פרסומות"),
    ("סופר השכונה <club@superhood.example>", "המבצעים של סוף השבוע במועדון",
     "1+1 על מוצרי ניקיון ו-15% הנחה על פירות וירקות לחברי המועדון.",
     "פרסומות"),

    # --- אבטחה וחשבונות ---
    ("SecureMail <no-reply@securemail.example>", "התראת אבטחה: כניסה חדשה לחשבון",
     "זיהינו כניסה לחשבון שלך ממכשיר Windows חדש. אם זו לא את, אפסי את הסיסמה.",
     "אבטחה וחשבונות"),
    ("CloudBox <account@cloudbox.example>", "Verify your email address",
     "Please confirm your email to finish creating your CloudBox account. This link expires in 24 hours.",
     "אבטחה וחשבונות"),
    ("SecureMail <no-reply@securemail.example>", "אפליקציה קיבלה גישה לחשבון שלך",
     "הענקת לאפליקציה NoteSync הרשאה לקרוא את אנשי הקשר שלך. אפשר לבטל את הגישה בהגדרות.",
     "אבטחה וחשבונות"),
    # borderline: the "Welcome to LangSmith" overlap (developer tool vs. welcome email)
    ("TraceLab <hello@tracelab.example>", "Welcome to TraceLab!",
     "Thanks for signing up. Your workspace is ready: create your first project and start tracing your LLM apps.",
     "אבטחה וחשבונות"),
    ("FamilyGuard <no-reply@familyguard.example>", "Action required: confirm your account",
     "Confirm your account to keep receiving the daily activity report for your family.",
     "אבטחה וחשבונות"),

    # --- none ---
    ("מיכל <michal.friend42@example.com>", "Re:",
     "בטח, נדבר מחר בערב. תזכירי לי להביא את הספרים.",
     "none"),
    ("יוסי <yossi.d77@example.com>", "",
     "היי, צירפתי את התמונות מהטיול. תגידי אם הגיעו.",
     "none"),
    ("Daily News IL <daily@news-il.example>", "סקירה יומית: הכותרות של הבוקר",
     "מזג אוויר, תחבורה ופוליטיקה - כל מה שצריך לדעת היום בחמש דקות קריאה.",
     "none"),
    ("PinBoard <recommendations@pinboard.example>", "רעיונות חדשים עבורך",
     "מצאנו 12 פינים שאולי תאהבי: עיצוב מטבח, מתכונים לחורף ועוד.",
     "none"),
    ("StartHub <info@starthub.example>", "Want to join a product team that could become a startup?",
     "We're recruiting developers for a 3-month program building real products with mentors.",
     "none"),
]

# v2 = all v1 emails + hard cases. The new label רשתות חברתיות changes one v1 answer
# (1-based position in EMAILS_V1 -> new expected label).
V2_EXPECTED_CHANGES = {19: "רשתות חברתיות"}  # PinBoard (Pinterest-like) is named in the new description

V2_NEW = [
    # --- social vs. technology boundary ---
    ("ProLink <notifications@prolink.example>", "יש לך 5 צפיות חדשות בפרופיל השבוע",
     "גלי מי צפה בפרופיל שלך, וגם: 3 משרות חדשות שמתאימות לך ועדכונים מהרשת שלך.",
     "רשתות חברתיות"),
    ("ProLink <notifications@prolink.example>", "Your post about React hooks got 23 reactions",
     "People in your network are engaging with your post. See who reacted and reply to 4 new comments.",
     "רשתות חברתיות"),  # tech topic, but a social-network notification
    ("CodeAnswers <digest@codeanswers.example>", "Top questions this week in #python",
     "The most upvoted questions from the community: async generators, typing Protocols, packaging with uv.",
     "רשתות חברתיות"),  # online tech community digest
    ("PyWeekly IL <hello@pyweekly-il.example>", "ניוזלטר: 5 כלים חדשים למפתחי Python",
     "השבוע: ספריית ולידציה מהירה, כלי פרופיילינג חדש ומדריך למעבר לגרסה האחרונה של השפה.",
     "טכנולוגיה"),  # tech newsletter, not a network
    ("ProLink <security@prolink.example>", "כניסה חדשה לחשבון ProLink שלך",
     "זיהינו כניסה מדפדפן חדש בתל אביב. אם זו לא את, שני את הסיסמה עכשיו.",
     "אבטחה וחשבונות"),  # social-network sender, but security content

    # --- sponsored content: a sponsored newsletter stays "none", a sponsored community digest is social ---
    ("המקומון היומי <daily@local-daily.example>", "סקירה יומית 18/11 (נתמך ע\"י פרסומות)",
     "הכתבות הבולטות של היום: עבודות בכביש הראשי, מזג האוויר לסוף השבוע. בחסות: רשת מרפאות שיניים.",
     "none"),
    ("מרכז הקהילה <info@community-center.example>", "תקציר יומי מהקהילה שלך | חסות: חופשה מול הים",
     "פוסטים חדשים בפורום ההורים, הרצאה ביום חמישי במתנ\"ס, ומבצע חסות: נופש זוגי ב-20% הנחה.",
     "רשתות חברתיות"),  # sponsored, but a community digest

    # --- other hard cases ---
    ("ShopNova <orders@shopnova.example>", "אישור הזמנה #48213",
     "תודה על ההזמנה! ההזמנה התקבלה ותישלח תוך 3-5 ימי עסקים. סה\"כ לתשלום: 149 ש\"ח.",
     "none"),  # a receipt is not an ad
    ("קודבוקס <welcome@codebox.example>", "ברוכה הבאה לקודבוקס!",
     "החשבון שלך נוצר. אפשר להתחיל ליצור פרויקט ראשון ולחבר את המאגר שלך מ-GitHub.",
     "אבטחה וחשבונות"),  # welcome email from a developer tool

    # ===== v2 round 2: harder cases (fake-30 .. fake-39) =====
    # sponsored newsletters with promotional wording -> none
    ("Morning Brief <brief@morningbrief.example>", "הבוקר: 5 דברים שצריך לדעת + 30% הנחה על מנוי",
     "סיכום חדשות הבוקר בשלוש דקות. בחסות קפה אורו: הקוד BRIEF30 נותן 30% הנחה על המנוי הראשון.",
     "none"),
    ("Weekend Reads <hello@weekendreads.example>", "Sponsored: the 10 best stories of the week",
     "This issue is brought to you by TravelNow - book by Sunday and save 25%. Plus: our editors' picks for the weekend.",
     "none"),
    # tech topic, but the source is a community or social network -> רשתות חברתיות (like #23)
    ("DevForum IL <digest@devforum-il.example>", "הדיונים החמים השבוע בקהילה",
     "שאלות פופולריות: Docker על Windows, מעבר מ-REST ל-GraphQL, ו-12 תגובות חדשות בשרשור שעקבת אחריו.",
     "רשתות חברתיות"),
    ("ProLink <groups@prolink.example>", "פוסטים חדשים בקבוצה 'מפתחי AI בישראל'",
     "3 פוסטים חדשים: השוואת מודלים מקומיים, משרת ML בחיפה, ושאלה על RAG עם 15 תגובות.",
     "רשתות חברתיות"),
    ("Chatter <digest@chatter.example>", "Top posts this week in c/LocalLLMs",
     "The community's most upvoted posts: running a 7B model on a laptop, quantization explained, and a benchmark thread.",
     "רשתות חברתיות"),
    # order receipts -> none
    ("RunFast <orders@runfast.example>", "Your order has shipped!",
     "Good news: order #RF-55120 is on its way. Track your package. Need help? Reply to this email.",
     "none"),
    ("קפה השכונה <receipts@cafehood.example>", "קבלה על התשלום שלך",
     "תודה שקנית אצלנו! סה\"כ 42 ש\"ח. צברת 8 נקודות במועדון - בקנייה הבאה מחכה לך קרוואסון במתנה.",
     "none"),  # receipt with a small promotional hook
    # welcome emails -> אבטחה וחשבונות
    ("ProLink <welcome@prolink.example>", "ברוכה הבאה ל-ProLink, בואי נשלים את הפרופיל",
     "החשבון שלך נוצר. הוסיפי תמונה ותחומי עניין כדי למצוא אנשים מהתחום שלך.",
     "אבטחה וחשבונות"),  # welcome from a social network
    ("PromptLab <hello@promptlab.example>", "Welcome! Your API key is ready",
     "Your account is active. Create your first API key in the dashboard and try the quickstart.",
     "אבטחה וחשבונות"),  # welcome from a developer tool
    # event invitation about tech content -> טכנולוגיה (same rule as #4)
    ("קהילת Data IL <meetup@datail.example>", "הרשמה נפתחה: ערב הרצאות על LLMs בפרודקשן",
     "שלוש הרצאות על הטמעת מודלי שפה במוצר: ניטור, עלויות והערכה. מספר המקומות מוגבל.",
     "טכנולוגיה"),
]

EMAILS = [
    (s, subj, snip, V2_EXPECTED_CHANGES.get(n, label))
    for n, (s, subj, snip, label) in enumerate(EMAILS_V1, 1)
] + V2_NEW


def examples() -> list[dict]:
    return [
        {
            "inputs": {"email_id": f"fake-{n:02d}", "sender": s, "subject": subj, "snippet": snip},
            "outputs": {"label": label},
        }
        for n, (s, subj, snip, label) in enumerate(EMAILS, 1)
    ]


def upload(client) -> None:
    """Create the dataset in LangSmith, or add the examples whose email_id is not there yet.
    Existing examples are never changed, so experiments keep running on the same answers."""
    if client.has_dataset(dataset_name=DATASET_NAME):
        ds = client.read_dataset(dataset_name=DATASET_NAME)
        existing = {ex.inputs["email_id"] for ex in client.list_examples(dataset_id=ds.id)}
    else:
        ds = client.create_dataset(DATASET_NAME, description="Made-up emails with the expected label (or none).")
        existing = set()
    new = [ex for ex in examples() if ex["inputs"]["email_id"] not in existing]
    if new:
        client.create_examples(dataset_id=ds.id, examples=new)
        print(f"Added {len(new)} example(s) to dataset '{DATASET_NAME}' (now {len(existing) + len(new)}).")
