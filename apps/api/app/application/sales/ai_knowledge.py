"""
AI Knowledge Base Architecture.

Prepares the internal knowledge system for future AI consumption.
Currently defines the data model and API contracts.
Vector search will be added in a future sprint.
"""

from pydantic import BaseModel


class KnowledgeCategory(BaseModel):
    id: str
    name: str
    description: str
    item_count: int
    status: str  # "populated", "ready", "planned"


class KnowledgeBaseOverview(BaseModel):
    categories: list[KnowledgeCategory]
    total_items: int
    ready_for_ai: bool
    message: str


class KnowledgeBaseArchitecture:
    """
    Knowledge Base Architecture — prepared for future AI consumption.

    Categories:
    1. Services — Pacific North Systems service offerings
    2. Pricing — Pricing models and tiers
    3. Projects — Past project case studies
    4. Case Studies — Industry-specific success stories
    5. Proposal Templates — Reusable proposal structures
    6. Implementation Guides — Technical documentation
    7. FAQs — Common questions and answers
    8. Sales Methodology — Best practices and frameworks
    """

    CATEGORIES: list[dict[str, str]] = [
        {"id": "company", "name": "About PNS", "description": "Who we help, what we solve, and how to explain our value", "status": "populated"},
        {"id": "services", "name": "Services", "description": "Solutions, outcomes, timelines, and fit", "status": "populated"},
        {"id": "sales_process", "name": "How Sales Works", "description": "The lead-to-client workflow in simple steps", "status": "populated"},
        {"id": "scripts", "name": "Selling Scripts", "description": "Email, call, voicemail, and follow-up templates", "status": "populated"},
        {"id": "discovery", "name": "Discovery Calls", "description": "Questions, qualification, and next steps", "status": "populated"},
        {"id": "objections", "name": "Objection Handling", "description": "Helpful responses to common prospect concerns", "status": "populated"},
        {"id": "never_miss", "name": "Never Miss Sales", "description": "Who to call, how to pitch, qualify, demonstrate, and follow up", "status": "populated"},
        {"id": "pricing", "name": "Pricing Guidance", "description": "Internal ranges and how to discuss investment", "status": "populated"},
        {"id": "technical", "name": "Technical Reference", "description": "Security, integrations, hosting, and implementation notes", "status": "populated"},
    ]

    PLAYBOOK: list[dict[str, str]] = [
        {"category": "company", "title": "Our simple positioning", "summary": "Pacific North Systems helps growing operational businesses replace spreadsheets, disconnected tools, and repetitive admin with practical software and automation.", "content": "Lead with the business problem, not technology. We help teams save time, reduce mistakes, improve visibility, and serve customers more consistently. Our strongest fit is a company with real operational pain, a motivated decision maker, and a process valuable enough to improve."},
        {"category": "services", "title": "What we can deliver", "summary": "Custom CRM, client portals, inspection platforms, workflow and document automation, dashboards, reporting, mobile workforce tools, and business intelligence.", "content": "Match the service to the problem. Do not sell a large platform when a focused automation can prove value first. Typical delivery ranges from one to five months depending on scope. Confirm requirements before promising features, dates, or outcomes."},
        {"category": "sales_process", "title": "How the CRM works", "summary": "Discover → Research → Review → Contact → Qualify → Propose → Close → Deliver.", "content": "Discover finds candidate companies. Research reads public information and looks for fit, signals, and decision makers. A human reviews the evidence before outreach. Contact begins a conversation; it is not a hard sell. Qualified needs become an opportunity and proposal. Record meaningful interactions so the system can recommend the next step."},
        {"category": "sales_process", "title": "Safe automation rule", "summary": "The system may research and draft, but a person approves communication before it is sent.", "content": "Check names, facts, tone, offer, and contact details. Never present an estimate as a guarantee. Never claim a client result or relationship we cannot verify. Record corrections so future messages improve."},
        {"category": "scripts", "title": "First cold email", "summary": "Short, specific, helpful, and easy to answer.", "content": "Subject: Quick question about [Company]'s [process]\n\nHi [First name], I noticed [specific verified observation]. We help [industry] teams reduce the manual work around [relevant process] with practical software and automation. Is improving that area a priority for [Company] this year? If useful, I can share two or three ideas in a 15-minute call.\n\nBest,\nVinicius\nPacific North Systems"},
        {"category": "scripts", "title": "Cold-call opening", "summary": "Ask permission, explain relevance, and invite a real conversation.", "content": "Hi [First name], this is Vinicius from Pacific North Systems. I know this is a cold call—can I take 30 seconds to explain why I called, and you can tell me if it is relevant? We help [industry] companies reduce manual work in [process]. I noticed [verified signal] at [Company]. How are you handling that today?"},
        {"category": "scripts", "title": "Voicemail", "summary": "Give one reason to respond and keep it under 25 seconds.", "content": "Hi [First name], Vinicius from Pacific North Systems. I am reaching out because we help [industry] teams simplify [process], and I noticed [brief verified reason]. I will send a short email with context. If this is a priority, I would be glad to compare notes. My number is [number]."},
        {"category": "scripts", "title": "Follow-up after no reply", "summary": "Add value instead of asking whether they saw the last email.", "content": "Hi [First name], one additional thought: teams handling [process] manually often lose time in [specific consequence]. A focused first step can usually test the opportunity without replacing every system. Worth a short conversation, or should I close the loop for now?"},
        {"category": "discovery", "title": "Discovery-call structure", "summary": "Understand the current process, impact, urgency, decision, and next step.", "content": "Start with their goals. Ask: How does the process work today? Where does it slow down or create errors? Who is affected? What does the problem cost in time, revenue, risk, or customer experience? Why address it now? Who else should be involved? What would success look like? Summarize what you heard and agree on one concrete next step."},
        {"category": "discovery", "title": "Qualification guide", "summary": "Prioritize pain, impact, urgency, access, and fit—not company size alone.", "content": "A strong opportunity has a clear operational problem, measurable impact, an owner who wants change, access to the decision process, and a realistic path to investment. If evidence is weak, keep researching or nurture the relationship rather than forcing a proposal."},
        {"category": "objections", "title": "We already have software", "summary": "Do not attack their current system; explore the gaps around it.", "content": "That makes sense—we rarely assume the existing platform needs replacing. Where do people still rely on spreadsheets, duplicate entry, manual follow-up, or workarounds? A useful project may be an integration or focused automation rather than a replacement."},
        {"category": "objections", "title": "It is too expensive", "summary": "Clarify the comparison and reduce risk before defending price.", "content": "I understand. Is the concern the total investment, timing, or uncertainty about the return? We can define a smaller first phase tied to one measurable outcome. If the expected value does not justify the investment, we should say that early."},
        {"category": "objections", "title": "Send me information", "summary": "Agree, then earn enough context to send something useful.", "content": "Absolutely. To avoid sending a generic brochure, which area matters most right now: reducing admin, improving field operations, customer communication, or management visibility? I will send a concise note focused on that."},
        {"category": "pricing", "title": "Internal pricing reference", "summary": "Use ranges for qualification; final pricing follows discovery and scope.", "content": "Essentials: approximately $5k–$10k setup plus $400–$800 monthly. Professional: $10k–$25k setup plus $800–$2k monthly. Enterprise: $25k–$50k setup plus $2k–$5k monthly. These are planning ranges, not quotes. Price around outcomes, risk, scope, support, and complexity."},
        {"category": "technical", "title": "Technical conversation guide", "summary": "Explain architecture only when the buyer needs it, using clear outcomes first.", "content": "We build secure web-based systems with role-based access, managed databases, encrypted connections, backups, monitoring, and integrations where appropriate. Technical discovery confirms data migration, permissions, integrations, compliance, uptime, and recovery needs. Never promise zero data-loss risk; explain the controls and recovery plan instead."},
        {"category": "never_miss", "title": "Best Never Miss prospects", "summary": "Call local owner-operated service businesses where one missed call can represent a real job.", "content": "Prioritize plumbers, electricians, HVAC contractors, roofers, restoration companies, locksmiths, appliance repair, garage-door services, landscapers, cleaners, mobile mechanics, pest control, and other appointment or emergency-oriented trades. The strongest prospect advertises a mobile number, depends on inbound calls, works in the field, has no receptionist, and has recent reviews mentioning slow callbacks or difficulty reaching the company. Avoid businesses that receive few phone leads, already use a mature answering service, or cannot legally use automated SMS for their workflow."},
        {"category": "never_miss", "title": "Never Miss cold-call opening", "summary": "Lead with the missed-call problem and ask one question before explaining the product.", "content": "Hi, is this the owner? My name is Vinicius with Pacific North Systems in Vancouver. Quick question: when you are on a job and cannot answer a new customer call, what normally happens to that lead? [Listen.] We built a simple service called Never Miss. Your number stays the same. When a call goes unanswered, the caller gets a polite text from your business asking what they need, and the callback is organized for you. Would recovering even one extra job a month make that useful enough to test?"},
        {"category": "never_miss", "title": "Thirty-second Never Miss pitch", "summary": "Explain the outcome, proof, and low-risk next step without technical language.", "content": "Contractors often cannot answer while driving, using tools, or speaking with a customer. Never Miss keeps the business number they already advertise. If a call is not answered, it sends the caller a customized text, captures the reply, and puts the callback in one place. Answered calls work normally. We set up the first test together, the customer can cancel anytime, and the founding pilot is $19.99 per month while we learn with our first customers."},
        {"category": "never_miss", "title": "Never Miss discovery questions", "summary": "Use five questions to decide whether the product can create measurable value.", "content": "Ask: About how many new-customer calls do you receive in a normal week? How often are you unable to answer? What happens today when the caller reaches voicemail? Do callers usually leave a message, call a competitor, or try again? What is a normal first job worth? Who returns missed calls, and how quickly? Do you need voicemail to remain part of the workflow? Which mobile carrier and phone setup do you use? A strong pilot candidate misses at least a few valuable calls, can configure unanswered-call forwarding, and will complete a short weekly feedback check."},
        {"category": "never_miss", "title": "Never Miss qualification and value", "summary": "Calculate value from the prospect's own numbers instead of promising revenue.", "content": "Estimate monthly missed opportunities as weekly inbound leads multiplied by four multiplied by the percentage not answered. Ask the owner for their approximate close rate and average first-job value. Present a scenario, not a guarantee. Example: if four missed callers per month would normally disappear and one becomes a $250 job, the service has paid for many months. Mark the lead qualified when call volume, missed-call frequency, job value, carrier compatibility, owner interest, and willingness to test are all clear."},
        {"category": "never_miss", "title": "Never Miss demonstration", "summary": "A live call is more convincing than a feature list.", "content": "Ask permission to demonstrate. Have the owner call the demo business number and let it ring unanswered. Let them receive or observe the automatic text, reply with a sample request, and show the callback appearing in the CRM. Explain that their own business number stays public and only unanswered calls are forwarded. Be transparent that carrier setup and voicemail behaviour must be confirmed during onboarding."},
        {"category": "never_miss", "title": "Never Miss objection: I already have voicemail", "summary": "Position the product as faster and easier for callers, while being honest about carrier behaviour.", "content": "That makes sense. The difference is that many callers do not leave voicemail, while a text lets them explain what they need in seconds. We do need to test how unanswered-call forwarding interacts with voicemail on your carrier. If voicemail is essential and the two cannot coexist cleanly, we should not force the setup."},
        {"category": "never_miss", "title": "Never Miss objection: customers can just call back", "summary": "Focus on response speed and competitive calls without using fear.", "content": "Some will, but a new customer with an urgent job may call the next company instead. Never Miss gives them an immediate, professional acknowledgement while you keep working. The pilot should measure whether your callers actually reply and whether those replies become useful callbacks."},
        {"category": "never_miss", "title": "Never Miss objection: I do not want another phone number", "summary": "Clarify that the existing number remains the advertised customer number.", "content": "You keep your existing business number. The private routing number works behind the scenes only for calls you do not answer. Customers continue calling the number they already know. We never ask you to replace signs, listings, cards, or advertising."},
        {"category": "never_miss", "title": "Never Miss follow-up text", "summary": "Send a short recap only when the prospect expects it.", "content": "Hi [First name], this is Vinicius from Pacific North Systems. Never Miss keeps your current business number and sends a customized text only after an unanswered call, so you can see what the customer needs and call back. The founding pilot is $19.99 per month and can be cancelled anytime. Here is the simple overview: https://www.pacificnorthsystems.com/never-miss Reply here if you want me to walk through a test with you."},
        {"category": "never_miss", "title": "Never Miss call outcome and next step", "summary": "Record the real outcome so the CRM recommends the correct follow-up.", "content": "Use one outcome: qualified for pilot, interested later, not a fit, already solved, carrier or voicemail concern, requested demonstration, or no contact. For a qualified pilot, record estimated weekly inbound calls, estimated missed calls, average first-job value, carrier, voicemail requirement, decision maker, demonstration date, and agreed next action. Never schedule repeated follow-ups after a clear no or opt-out."},
    ]

    def get_overview(self) -> KnowledgeBaseOverview:
        categories = [
            KnowledgeCategory(
                id=c["id"], name=c["name"], description=c["description"],
                item_count=sum(1 for item in self.PLAYBOOK if item["category"] == c["id"]), status=c["status"],
            )
            for c in self.CATEGORIES
        ]
        return KnowledgeBaseOverview(
            categories=categories,
            total_items=len(self.PLAYBOOK),
            ready_for_ai=True,
            message="Your PNS sales playbook is ready. It teaches the team and gives AI assistants approved guidance for services, outreach, discovery, objections, pricing, and safe system use.",
        )

    def get_playbook(self) -> list[dict[str, str]]:
        return self.PLAYBOOK

    def get_mcp_context_schema(self) -> dict:
        """Returns the MCP context schema for future AI agent integration."""
        return {
            "version": "1.0",
            "contexts": {
                "company_context": {"source": "CRM", "fields": ["name", "industry", "employees", "opportunity_score", "contacts", "activities"]},
                "proposal_context": {"source": "AI Proposal Builder", "fields": ["company", "recommended_services", "estimated_value", "timeline"]},
                "meeting_context": {"source": "AI Meeting Prep", "fields": ["company", "timeline", "contacts", "opportunities", "talking_points"]},
                "opportunity_context": {"source": "CRM + Scoring Engine", "fields": ["score", "confidence", "breakdown", "signals", "services"]},
                "timeline_context": {"source": "CRM Timeline", "fields": ["activities", "calls", "emails", "meetings", "tasks"]},
                "knowledge_context": {"source": "PNS Sales Playbook", "fields": ["company", "services", "sales_process", "scripts", "discovery", "objections", "never_miss", "pricing", "technical"], "status": "populated"},
            },
        }
