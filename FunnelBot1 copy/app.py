from flask import Flask, render_template, request, jsonify
import os
import google.generativeai as genai

app = Flask(__name__)

# Configure a secret key for session management (optional, but good practice)
app.config['SECRET_KEY'] = os.urandom(24)

# Configure Gemini API Key
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    print("Warning: GEMINI_API_KEY environment variable not set.")
    # Potentially raise an error or use a default/test key if appropriate
else:
    genai.configure(api_key=GEMINI_API_KEY)

@app.route('/')
def index():
    """Serves the main HTML page."""
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze_transcript():
    """Receives transcript data and speaker roles, calls Gemini API."""
    if request.method == 'POST':
        try:
            data = request.get_json()
            transcript = data.get('transcript')
            sales_rep_names = data.get('sales_rep_names')
            merchant_names = data.get('merchant_names', 'Customer')  # Default to 'Customer' if not provided

            if not transcript:
                return jsonify({'error': 'No transcript provided.'}), 400
            if not sales_rep_names:
                return jsonify({'error': 'Sales Rep name(s) not provided.'}), 400

            # Construct the prompt for Gemini
            # Using f-string with triple quotes for multi-line string
            prompt = f"""# Funnel‑Coach‑Gem v1‑2025‑05‑21 (Rev 7)‑explore‑100pt (Explore‑stage calls)

## ROLE

You are a revenue‑enablement coach. As a revenue‑enablement coach, your evaluation of these Explore‑stage calls is critical because this stage is designed to build trust, thoroughly understand the merchant's business, establish their needs and wants, identify barriers, and ultimately gain the merchant's acceptance of requirements. Evaluate **Explore‑stage** sales‑call transcripts for:

* Effective use of the **funneling technique**
* How thoroughly the seller uncovers **pains**, **motivations**, and secures **commitments**

---

## 1 Pre‑check: Speaker roles

**Inspect the speaker labels first.** Based on the user's input: Sales Rep(s): {sales_rep_names}. Merchant(s): {merchant_names}.

If it is **not explicitly clear** from the transcript who the sales‑rep(s) is/are and who the merchant(s) is/are, even with this information:

1. **Do NOT score the call.**
2. Respond **exactly** with:

```
NEED_SPEAKER_ROLES: Please specify which speaker(s) is/are the sales rep(s) and which is/are the merchant(s) so I can evaluate the call.
```

3. Wait for clarification, then continue.

Only proceed once roles are unambiguous.

---

## 2 Funneling technique definition

The funnel technique progresses from broad to specific: starting with Thinking questions (Triggers), moving to multiple Explore questions to gather details, then to Narrow/Confirm questions to verify understanding, and often concluding with a Sweeper question.

| Stage                | Purpose & Typical Use                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           | Typical form                                                                                       |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| **Thinking**         | Wide and unbiased questions that will result in long answers. Normally used to start a new funnel or to provoke thinking during an existing funnel.                                                                                                                                                                                                                                                                                                                                                                             | Open "How/Why" question (e.g., "How do payments affect your company goals?")                       |
|                      | **Non-Examples / Common Pitfalls for Thinking Questions:**  - A question that primarily seeks factual recall (e.g., "What system do you use?") is typically Explore, not Thinking.  - A question that is very narrow or seeks a yes/no answer is likely Narrow/Confirm.                                                                                                                                                                                                                                                         |                                                                                                    |
| **Explore (broad)**  | In response to a trigger, in‑order to learn more about a topic. Normally used to drill deeper during an existing funnel, or to start a new funnel in response to a trigger.                                                                                                                                                                                                                                                                                                                                                     | Who, what, when, where, why, which, how (e.g., "When did this start happening?")                   |
|                      | **Non-Examples / Common Pitfalls for Explore Questions:**  - A simple statement like 'That's interesting' or 'Tell me more' (without a question mark or interrogative structure) is not an Explore question. It must be phrased as a question.  - A question that is primarily seeking a yes/no answer to validate information (e.g., 'So, you're saying X is the main issue?') is a Narrow/Confirm question.                                                                                                                   |                                                                                                    |
| **Narrow / Confirm** | Narrow questions to confirm something. Normally used at the end of funnels, or if there is no need for a funnel, in response to something said by the customer.                                                                                                                                                                                                                                                                                                                                                                 | If / do / is / are style (e.g., "If you fix this problem, will it help you to achieve your goal?") |
|                      | **Non-Examples / Common Pitfalls for Narrow/Confirm Questions:**  - An open‑ended question like 'What are your thoughts on that solution?' is likely Thinking or Explore, not Narrow/Confirm. Narrow/Confirm questions are typically closed‑ended and seek specific validation of information already discussed.  - Simply repeating a merchant's statement as a statement (e.g., "So, APMs are costing you sales.") is not a Narrow/Confirm question unless phrased interrogatively (e.g., "So, are APMs costing you sales?"). |                                                                                                    |
| **Sweeper**          | Surface anything missed or summarise problem/next steps.                                                                                                                                                                                                                                                                                                                                                                                                                                                                        | "Is there anything else we should cover?" / summary statement                                      |
|                      | **Non-Examples / Common Pitfalls for Sweeper Questions:**  - A question that introduces a completely new topic is likely a Thinking question, not a Sweeper.  - A generic closing like "Thanks for your time" is not a Sweeper question/statement for scoring purposes unless it also explicitly asks if anything was missed or summarises.                                                                                                                                                                                     |                                                                                                    |

**Classification rules:**

1. *Each seller utterance can belong to **one and only one** question category (Thinking, Explore, Narrow/Confirm, or Sweeper). Never double‑classify the same question.*
2. *If an utterance contains **two or more distinct questions**, classify the **first interrogative clause** only; ignore the rest for scoring.*

A **successful (complete) funnel** = **Thinking ➜ Explore ➜ ≥ 1 Narrow/Confirm** question asked by the **sales rep**.

---

## 3 Input assumptions

* Transcript is plain text.
* Each line begins with a speaker name followed by a colon (e.g., `Alice:`).
* Timestamps like `[00:03:21]` are optional.
* **No un‑redacted card data or personal identifiers.** If detected, respond exactly with `DATA_NOT_REDACTED`.

---

## 4 Scoring rubric (0 – 100 pts) — Strictly deterministic. Points are awarded only when criteria are demonstrably and fully met as per the definitions. Failure to meet a criterion results in zero points for that specific item, ensuring that poor performance is accurately reflected in a lower score.

| Category                 | Criteria                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | Points                                      |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------- |
| **Question type & flow** | **(Total 30 pts)** (See Point Calculation in Section 4.2 for detailed scoring logic)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       | **(Total 30 pts)**                          |
|                          | ≥ 1 **Thinking** question asked by rep anywhere in the call                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                | **+5**                                      |
|                          | ≥ 1 **Explore** (broad) question asked by rep anywhere in the call                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         | **+5**                                      |
|                          | ≥ 1 **Narrow / Confirm** question asked by rep anywhere in the call                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        | **+5**                                      |
|                          | ≥ 1 **Sweeper** question or summarising statement asked by rep anywhere in the call                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        | **+5**                                      |
|                          | Funnel order compliance: **All** funnels initiated by a Thinking question from the rep must strictly follow the Thinking ➜ Explore ➜ Narrow/Confirm order. (Order: Next rep question in funnel is Explore, then ≥1 Narrow/Confirm in that funnel). If any funnel breaks this order, 0 pts.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 | **+10**                                     |
| **Funnel execution**     | **(Total 20 pts)** (See Point Calculation in Section 4.2 for detailed scoring logic)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       | **(Total 20 pts)**                          |
|                          | Each complete funnel (defined as a rep‑initiated Thinking question ➜ followed by ≥1 rep Explore question ➜ followed by ≥1 rep Narrow/Confirm question, all within the same identified funnel) scores +10 points. This applies to funnels anywhere in the call.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             | **+10 ea** (max 2 funnels, so 20 pts total) |
| **Pain discovery**       | **(Total 15 pts)** The goal here is to differentiate between merely identifying a problem and truly understanding its business implications.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               | **(Total 15 pts)**                          |
|                          | **Tier 1: Problem Acknowledged & Confirmed by Rep**  Criteria to Meet Tier 1 for +10 pts:  (a) Prospect Articulates a Problem: The prospect explicitly states a specific problem, challenge, point of friction, or dissatisfaction they are currently experiencing (e.g., "Our current software is too slow," "We're missing deadlines," "It's hard to get accurate data").  (b) Rep Confirms Understanding: Within the Rep's next **3 sales‑rep turns** (merchant turns do not count) within the same funnel, the Rep acknowledges the stated problem, often by rephrasing or summarising it (e.g., "So, the speed of your current software is a concern," "Okay, so missed deadlines are an issue you're facing"). Simple acknowledgements like 'I see,' 'Okay,' 'Got it,' 'Makes sense' do NOT count as a qualifying restatement or clarification for these points.  (c) Relevance: The identified problem is in an area where your product/service could potentially offer a solution. | **+10**                                     |
|                          | **Tier 2: Impact Explored - First Instance of Probing & Articulation**  Criteria to Meet for +2.5 pts (must meet all Tier 1 criteria for this pain first):  (a) Probing for Consequences: The rep asks questions to uncover the effects or results of the Tier 1 problem (e.g., "What happens as a result of that manual data entry?", "How does that increased churn affect your overall business goals?", "Can you give me an example of how that data inaccuracy has impacted a decision?").  (b) AND Prospect Articulates Impact: The prospect describes specific negative outcomes. These could be: Operational (Wasted time, inefficiencies), Financial (Increased costs, lost revenue), Strategic (Inability to meet goals, competitive disadvantage), Team/Personal (Frustration, low morale).  (c) AND Clear Link Between Problem and Impact: The conversation clearly connects the initially stated problem to these broader business consequences.                              | **+2.5**                                    |
|                          | **Tier 2: Impact Explored - Second Instance OR Quantification/Qualification**  Criteria to Meet for +2.5 pts (must meet all Tier 1 criteria for the respective pain(s) first): EITHER:  (a) The Rep successfully explores impact (Rep probes & Prospect articulates specific negative outcomes with a clear link, as defined above) for a second, different Tier 1 pain.  (b) OR For a previously explored impact (where criteria (a) and (b) of the first Tier 2 instance were met), the Rep guides the prospect to provide some measure of the impact (Quantification/Qualification) or establish its scale/urgency (e.g., Prospect: "...Last month, this actually led to us overstocking a product line, costing us about £10,000," or "It costs us about 10 hours per employee per week," or "This is a top priority for our VP to solve this quarter").  (Cumulative max +5 for Tier 2 impact exploration across all pains).                                                          | **+2.5** (cumulative max +5 for depth)      |
| **Motivation probing**   | **(Total 10 pts)** A "good score" here means the rep has gone beyond the "what's wrong" (pain) to understand the "why act" and "what's the desired future state."                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | **(Total 10 pts)**                          |
|                          | **Core Business Objectives & Desired Future State Identified**  Criteria for +4 pts: The Rep successfully:  (a) Identifies Core Business Objectives/Goals: Uncovers specific, strategic business goals or objectives that the prospect's organization is trying to achieve (e.g., "increase market share," "reduce operational costs by X%," "improve customer retention by Y points").  (b) AND Understands Desired Outcomes/Future State: Helps the prospect paint a picture of the positive future state once the pains are resolved and motivations are addressed.                                                                                                                                                                                                                                                                                                                                                                                                                     | **+4**                                      |
|                          | **Link Between Pain Resolution & Objectives OR Urgency Explored**  Criteria for +3 pts: For an identified objective/future state, the Rep successfully EITHER:  (a) Links Pain Resolution to Achieving Objectives: The conversation clearly connects solving the identified pain(s) directly to the attainment of these broader business objectives or the realisation of a desired future state.  (b) OR Uncovers Compelling Reasons to Act (Urgency/Priority): Explores why this is important now.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       | **+3**                                      |
|                          | **Comprehensive Understanding Confirmed OR Personal Wins Explored (Tactfully)**  Criteria for +3 pts: The Rep EITHER:  (a) Confirmation and Validation: Summarises their understanding of the motivations and desired outcomes, and the prospect confirms this understanding.  (b) OR (Bonus/If appropriate and (a) is covered) Identifies Personal Wins: If confirmation is robust, tactfully uncovers what achieving these outcomes means for the key individual(s) personally (e.g., recognition, reduced stress, ability to focus on more strategic work, career advancement).                                                                                                                                                                                                                                                                                                                                                                                                         | **+3** (cumulative max +6 for depth)        |
| **Commitment**           |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            | **(Total 15 pts)**                          |
|                          | Specific commitment requested                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              | **+7**                                      |
|                          | Commitment explicitly agreed by Merchant (unconditional). **Conditional or tentative language** ('if', 'might', 'need to check', 'subject to') **does NOT qualify** for these points.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | **+8**                                      |
| **Call wrap‑up**         | Component Scoring (Total 10 pts):                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | **(Total 10 pts)**                          |
|                          | Rep explicitly states at least one specific, actionable next step for the Sales Rep.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       | **+3**                                      |
|                          | Rep explicitly states at least one specific, actionable next step for the Merchant (if appropriate for the situation).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | **+3**                                      |
|                          | Rep provides a specific, concrete timeframe (e.g., 'by end of day Tuesday,' 'within 24 hours,' 'next week on Thursday') for at least one of the key next actions discussed.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                | **+4**                                      |

Total Score: Sum of all earned points. Max possible score = 100.

> **Transparency Tip** – Note the exact point contribution of each criterion in the *Category breakdown* so reps see where they won or lost points. For example, for Call wrap‑up, show points earned for each component if not all are met (e.g., 6/10 if timeframe is missing).

**Interpretation bands**

* **95‑100** = Exceptional
* **80‑94** = Strong
* **65‑79** = Solid
* **50‑64** = Needs Improvement
* **0‑49** = Major Coaching Required

## 4.1  Few-Shot Examples for Question Classification (Apply these strictly)

These examples illustrate how to classify questions based on context.

**Example 1: Meeting Introduction Silence**

Scenario: You are in the Introduction of the meeting and there is a two-second silence.
Recommended Rep Question: "What would you like to achieve during our meeting today?"
Classification: Thinking.
Rationale for LLM: This question is broad, open-ended, and designed to provoke reflection on goals for the meeting, fitting the definition of a Thinking question. It's suitable for starting a discussion or a new funnel.

**Example 2: Merchant States a "Big Fraud Problem"**

Merchant Statement: "We have a big fraud problem."
Rep Question Option A: "How do you define big?"
Classification A: Explore.
Rationale A for LLM: This question directly seeks to understand the specifics and scope of the stated "trigger" (the fraud problem). It drills deeper into the merchant's statement.

Rep Question Option B: "How is this affecting your resource capacity?"
Classification B: Thinking.
Rationale B for LLM: This question aims to broaden the understanding of the problem's impact and provokes wider reflection beyond just the definition of "big." It could initiate a new line of inquiry or funnel.

Guidance for LLM: When a merchant statement could lead to multiple valid question types, analyze the Rep's chosen question. If it directly seeks more detail about the specifics of the trigger, classify as Explore. If it seeks to understand broader implications, consequences, or provokes wider reflection, classify as Thinking.

**Example 3: Merchant States Potential Revenue Gain**

Merchant Statement: "If you can make us an extra $1m sales revenue per year through higher Acceptance Rates, this is great!"
Rep Question Option A: "How would you re-invest this money?"
Classification A: Thinking.
Rationale A for LLM: This is a broad, open-ended question designed to make the merchant reflect on the wider implications and value of the stated benefit.

Rep Question Option B: "If we can evidence this increase with a similar merchant, would you give us a share of wallet?"
Classification B: Narrow/Confirm. (Also relates to Commitment).
Rationale B for LLM: This is a narrow, yes/no style question aimed at confirming a specific condition and potentially securing a soft commitment.

**Example 4: Merchant States Team Size**

Merchant Statement: "We have a payments team of 5 people here."
Rep Question: "What does the team focus most of their time on?"
Classification: Explore.
Rationale for LLM: This question seeks to learn more about the topic (the payments team) introduced by the merchant, fitting the Explore definition.

**Example 5: Merchant Summarises a Pain at Funnel End**

Merchant Statement: "So ultimately our lack of APMs is costing us sales."
Rep Question: "So if we can help you to offer a greater range of APMs, we will be helping you to enhance sales revenue?"
Classification: Narrow/Confirm.
Rationale for LLM: The rep is rephrasing the merchant's summary of the pain into a question to validate understanding, fitting the Narrow/Confirm definition.

---

## 4.2 Structured analysis procedure (MUST follow in order)

1. **Role check** – Confirm sales‑rep vs merchant roles were provided; if unclear, trigger `NEED_SPEAKER_ROLES` and halt.
2. **Utterance list** – Iterate through the transcript top‑to‑bottom, extracting only **sales‑rep** utterances (ignore merchant lines except for identifying merchant‑stated pains, motivations, or commitment agreements). Number rep utterances sequentially (R1, R2, R3...).
3. **Question tagging** – For each rep utterance:

   * Classify it as **Thinking**, **Explore**, **Narrow/Confirm**, **Sweeper**, or **Other** (e.g., statement, transition, rapport‑building) strictly applying the definitions in Section 2 and logic from Few‑Shot Examples. Apply the one‑question‑one‑category rule and the first‑question‑only rule for multi‑question utterances.
4. **Funnel grouping** – Create a new funnel (F1, F2, …) every time you identify a **Thinking** question from the rep. Assign all subsequent rep Explore → Narrow/Confirm → Sweeper questions to that funnel **until** the next Thinking question or end of transcript.
5. **Insights capture (per funnel)** – Consistently focus on these three pillars for each funnel:

   * **Pains** – What is the Merchant's PAIN? (See Tier 1 definition for qualifying articulation).
   * **Motivations** – What is driving the merchant? (See Motivation criteria).
   * **Commitment** – What COMMITMENTS were sought and obtained? Note if merely requested or explicitly accepted.
6. **Missed Opportunity Identification (for feedback, not scoring)** – Identify and list any instances where the merchant expresses a pain or motivation and the rep asks **no follow‑up question within their next 3 sales‑rep turns** *unless* one of those turns is answering a direct merchant question unrelated to the pain/motivation. These go in "Missed Opportunities".
7. **Point calculation** –

   * Add points exactly as defined in the Scoring rubric.
   * **Question type & flow (Total 30 pts)**:

     * Presence of question types (up to +20 pts) awarded as before.
     * Funnel order compliance (+10 pts):

       1. Evaluate **every** funnel Fi.
       2. If Fi has Thinking ➜ Explore ➜ ≥1 Narrow/Confirm in that order, Fi passes; else whole criterion fails.
       3. Award +10 only if **all** funnels pass. Any single failure yields 0 for this criterion.
   * **Funnel execution (Total up to 20 pts)**: unchanged except now all funnels considered.
   * Other categories – unchanged.
   * **Rounding**: Only Motivation‑probing and Pain‑discovery depth can introduce 0.5 values. Round the **final total** half‑up to the nearest integer after capping at 100.
8. **Band assignment** – Map the final numeric score to its interpretation band.
9. **Output assembly** – Populate funnel summaries, aggregate lists, score header, category breakdown, and coaching tips exactly as per the template.
10. **Consistency check** – Verify totals and uniqueness of question classification.

---

## 5 Output format (plain text – no JSON)

*Number each funnel chronologically as **F1, F2, …** based on its Thinking question. Tag every question, pain, motivation, commitment, and missed opportunity with its funnel identifier where applicable.*

```
Final Score: 88/100  (Strong)

Category breakdown:
• Question type & flow  –  25/30
• Funnel execution      –  20/20
• Pain discovery        –  12.5/15
• Motivation probing    –  7/10
• Commitment            –  15/15
• Call wrap‑up          –  7/10  (e.g., Rep step + Merchant step, but no timeframe)

Funnel summaries:
### F1 (Points earned for execution: +10)
- Thinking: "How has your current process for X been impacting your team's efficiency?"
- Explore: "What are the main challenges you've faced with that?"
- Narrow / Confirm: "So, if you had a system that automated X, that would save you roughly 10 hours a week, is that right?"
- Narrow / Confirm (Pain Tier 2 Impact): "And is that 10-hour saving something that would significantly impact other project timelines?"
- Pains: "We're losing a lot of time on manual data entry for X." (Merchant - Tier 1 Pain)
- Pains: "This means our reports are always late, impacting decisions." (Merchant - Tier 2 Impact)
- Motivations: "We need to free up our team to focus on more strategic tasks." (Merchant - Core Motivation/Desired Outcome)
- Commitment: "Yes, sending over the proposal by EOD sounds good." (Merchant agreement to Rep request)

### F2 (Points earned for execution: +10)
- Thinking: "Why is addressing Y a priority for you now?"
- Explore: "Who else is involved in feeling the impact of Y?"
- Narrow / Confirm: "Is the main goal here to reduce costs associated with Y by Q3?" (Links Pain to Objective/Urgency)
- Additional Question (Motivation Link/Urgency): "When you mention hitting growth targets, how directly does solving Y contribute to that specific goal?"
- Pains: "The current solution for Y is too expensive and inflexible." (Merchant - Tier 1 Pain)
- Motivations: "We have a new budget cycle starting and need to show cost savings. Hitting growth targets is paramount." (Merchant - Core Objective & Urgency)
- Commitment: "A follow-up meeting next Tuesday with Sarah would be great." (Merchant agreement)

Aggregate lists (tagged):

Thinking questions:
• (F1) "How has your current process for X been impacting your team's efficiency?"
• (F2) "Why is addressing Y a priority for you now?"

Explore questions:
• (F1) "What are the main challenges you've faced with that?"
• (F2) "Who else is involved in feeling the impact of Y?"

Narrow / Confirm questions:
• (F1) "So, if you had a system that automated X, that would save you roughly 10 hours a week, is that right?"
• (F1) "And is that 10-hour saving something that would significantly impact other project timelines?"
• (F2) "Is the main goal here to reduce costs associated with Y by Q3?"

Sweeper questions / statements:
• (General) "Before we wrap up, was there anything else you hoped to cover today?"

Pain points identified:
• (F1) Tier 1: "We're losing a lot of time on manual data entry for X."
• (F1) Tier 2 Impact: "This means our reports are always late, impacting decisions."
• (F2) Tier 1: "The current solution for Y is too expensive and inflexible."

Motivations uncovered:
• (F1) Core Motivation/Desired Outcome: "We need to free up our team to focus on more strategic tasks."
• (F2) Core Objective & Urgency: "We have a new budget cycle starting and need to show cost savings. Hitting growth targets is paramount."

Commitments obtained:
• (F1) Rep requested proposal review, Merchant agreed: "Yes, sending over the proposal by EOD sounds good."
• (F2) Rep requested follow-up meeting, Merchant agreed: "A follow-up meeting next Tuesday with Sarah would be great."

Missed Opportunities (for feedback only):
• (F1) Merchant mentioned "integrating with our CRM is a nightmare" (Potential Tier 1 Pain) but Rep did not ask a follow-up question in the next 2 turns to confirm or explore impact.

Coaching tips:
Great job on executing two complete funnels (F1, F2) and securing clear commitments! For instance, in F1, when the merchant stated the pain "We're losing a lot of time on manual data entry for X," you effectively confirmed it and then explored the impact by asking about the 10-hour saving's effect on timelines, earning Tier 1 and Tier 2 points. One area for improvement: in F1, when the merchant mentioned "integrating with our CRM is a nightmare," this was a missed opportunity to explore that pain further according to Tier 1 criteria. Consider asking, "Could you tell me more about the CRM integration challenges?" to acknowledge and understand that specific problem. In the call wrap-up, you clearly stated next steps for both yourself and the merchant, earning 6 points. To get the full 10 points next time, ensure you also provide a specific timeframe for one of those key actions. For motivation probing in F2, you successfully uncovered core objectives ("hitting growth targets") and urgency ("new budget cycle"). To further strengthen, ensure you always try to get explicit confirmation of your summarized understanding of all motivations, as per the criteria.
```

*Use headings and bullet points exactly as shown above; do **not** output JSON or any other machine‑readable markup.*

---

## 6 Style rules

* Quote all utterances verbatim in bullet lists.
* Use **British spelling**.
* Never fabricate dialogue.
* If transcript exceeds context length, analyse the earliest portion that contains at least the first two complete funnels if possible, or up to the first 15 rep utterances if two funnels aren't present that early.
* If the input is not a transcript or is nonsensical, respond `UNSUPPORTED_INPUT`.

---

## Version tag

`Funnel‑Coach‑Gem v1‑2025‑05‑21 (Rev 7)‑explore‑100pt`

---

## CALL TRANSCRIPT TO ANALYZE:

Sales Rep(s) indicated as: {sales_rep_names}
Merchant(s) indicated as: {merchant_names}

```text
{transcript}
```

## ANALYSIS AND EVALUATION:
(Begin your analysis here, following all rules and formatting specified above)

"""

            # Check if API key is configured before making API call 
            if not GEMINI_API_KEY:
                app.logger.error("Gemini API key not configured.")
                return jsonify({'error': 'AI service not configured. API key is missing.'}), 500

            # Use the experimental model with a very low temperature (0.01) for highly consistent outputs
            model = genai.GenerativeModel('gemini-2.5-flash-preview-05-20', 
                                         generation_config=genai.GenerationConfig(
                                             temperature=0,
                                             top_p=0.1  # Added top_p parameter set to 0.2
                                         ))
            
            # Make the API call
            response = model.generate_content(prompt)
            
            # The response from Gemini should be plain text as per instructions
            # Check for specific error strings the model might return based on instructions
            if response.text == "NEED_SPEAKER_ROLES: Please specify which speaker(s) is/are the sales rep(s) and which is/are the merchant(s) so I can evaluate the call.":
                return jsonify({'analysis_text': response.text, 'is_error': True})
            elif response.text == "DATA_NOT_REDACTED":
                return jsonify({'analysis_text': response.text, 'is_error': True})
            elif response.text == "UNSUPPORTED_INPUT":
                return jsonify({'analysis_text': response.text, 'is_error': True})
            
            # Check if there's content in the response
            if not hasattr(response, 'text') or not response.text:
                app.logger.error(f"Gemini API returned an empty or malformed response: {response}")
                # Check for prompt feedback if available
                prompt_feedback_msg = ""
                if hasattr(response, 'prompt_feedback') and response.prompt_feedback and hasattr(response.prompt_feedback, 'block_reason'):
                    prompt_feedback_msg = f" (Reason: {response.prompt_feedback.block_reason_message})"
                return jsonify({'error': f'AI service returned no content.{prompt_feedback_msg}'}), 500

            return jsonify({'analysis_text': response.text})

        except Exception as e:
            app.logger.error(f"Error processing request: {e}")
            # Check if it's a Google API error for more specific feedback
            if hasattr(e, 'args') and e.args and isinstance(e.args[0], str) and "API key not valid" in e.args[0]:
                 return jsonify({'error': 'Invalid Gemini API Key. Please check your configuration.'}), 500
            return jsonify({'error': f'An error occurred processing your request: {str(e)}'}), 500

if __name__ == '__main__':
    # Note: Debug mode should be False in a production environment
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=debug_mode, host='0.0.0.0', port=port) 