"""Configuration for admission-letter generation.

Everything the letter needs to know lives in this file. If any value
changes (school name, bank details, threshold, emails, etc.), edit it
here — you do not need to touch admission_letter.py.
"""
# ── Default body text — used when no template row exists ─────────────
DEFAULT_INTRO_TEMPLATE = (
    "The Management of {letterhead} is pleased to inform you that your "
    "child/ward <b>{student_name}</b>, having passed our entrance examination "
    "is hereby offered a conditional admission into <b>{class_label}</b> for "
    "the {session_name} academic session."
)

DEFAULT_DEPOSIT_TEMPLATE = (
    "Paying a deposit of {deposit_words} ({deposit_display}) into the school "
    "account at {bank_branch_hint} {bank_name}., {bank_account_name} "
    "(A/C No: {bank_account}) before <b>{payment_deadline}</b>. Returning the "
    "teller showing evidence of payment to the accounts section for issuance "
    "of receipt and other required document. The deposit forms part of the "
    "school fees. You will also be given breakdown of the balance and other "
    "joining instructions. The balance of the fees is expected to be paid "
    "before the child resume for the session on <b>{resume_date}</b>."
)

DEFAULT_NOTES_TEMPLATE = (
    "School fees should always be paid in advance. You are encouraged to pay "
    "for the whole year if you are willing and able to do so.\n"
    "The return of the attached slip plus evidence of payment will reserve a "
    "place for your child. Complete and submit the enclosed acceptance form "
    "to the Admin office. (You may also scan the acceptance form, bank teller "
    "and email them to {acceptance_email_1} or {acceptance_email_2}.) Failure "
    "to do so on or before <b>{acceptance_deadline}</b> will imply that you "
    "do not wish to accept this offer and your child's/ward's space will be "
    "offered to other applicants.\n"
    "In the event of a change of mind two weeks after acceptance and payment "
    "of school fees, parent forfeits 50% of the fees paid.\n"
    "There is no refund of any fees if a student is expelled from the School, "
    "except for caution fee.\n"
    "The School Account Unit will need at least two weeks to process the refund."
)

DEFAULT_CLOSING_LINE   = "ACCEPT OUR CONGRATULATIONS."
DEFAULT_SIGNATURE_TITLE = "Principal"

# ── Session and source / destination schools ──────────────────────────
SESSION_NAME          = '2025-2026'
ENTRANCE_EXAM_SCHOOL  = 'Esteem Entrance Exam'    # where Result rows live
LETTER_ISSUING_SCHOOL = 'Esteem Boys College'     # whose letterhead is used

# ── Letterhead text (matches the school's letterhead) ─────────────────
LETTERHEAD_SCHOOL_LINE = "Esteem Learning Center, The Boys' College"

# ── Pass thresholds & class labels ────────────────────────────────────
# JSS1/2/3 → average of Math + English + Basic Science
# SS1/SS2   → average of every entrance-exam subject the student sat
PASS_THRESHOLD = {
    'JSS1': 50,
    'JSS2': 50,
    'JSS3': 50,
    'SS1':  55,
    'SS2':  60,
}

# What the letter actually prints (matches the docx, not the course titles)
CLASS_LABELS = {
    'JSS1': 'JS1',
    'JSS2': 'JS2',
    'JSS3': 'JS3',
    'SS1':  'SS1',
    'SS2':  'SS2',
}

# ── Deposit / fee details ─────────────────────────────────────────────
DEPOSIT_AMOUNT         = 750_000                                    # integer, for DB
DEPOSIT_AMOUNT_DISPLAY = 'N750,000'                                 # shown in body
DEPOSIT_AMOUNT_WORDS   = 'Seven Hundred Fifty Thousand Naira only'  # words in body

BANK_NAME         = 'GTB'
BANK_BRANCH_HINT  = 'any branch of'
BANK_ACCOUNT      = '0176923351'
BANK_ACCOUNT_NAME = 'Esteem International School Lokogoma'

# ── Payment window & acceptance emails ────────────────────────────────
# Deadline is calculated as: letter_date + PAYMENT_WINDOW_DAYS
# Days from letter date until deposit is due. Matches docx pattern
# from mid-2025 onward (~14 days). Change to 30 if you want the
# earlier pattern.
# Letter date = the day the letter record was created.
# Payment deadline = letter date + PAYMENT_WINDOW_DAYS.
# Acceptance deadline = payment deadline + ACCEPTANCE_WINDOW_DAYS.
PAYMENT_WINDOW_DAYS    = 15
ACCEPTANCE_WINDOW_DAYS = 15

ACCEPTANCE_EMAIL_1 = 'esteem.acct@gmail.com'
ACCEPTANCE_EMAIL_2 = 'esteemboyscollegeabuja@gmail.com'

# ── Defaults (overridden by School model fields when present) ─────────
DEFAULT_PRINCIPAL_NAME = 'Abubakar Ilani'
DEFAULT_RESUME_DATE    = (2025, 9, 7)   # y, m, d — used if School.next_term_date is empty