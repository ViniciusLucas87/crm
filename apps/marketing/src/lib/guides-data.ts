export interface GuideData {
  slug: string;
  title: string;
  description: string;
  category: string;
  readTime: string;
  content: {
    heading: string;
    body: string;
  }[];
  linkedTool?: { label: string; href: string };
  linkedGuides?: string[];
  faq?: { question: string; answer: string }[];
}

export const guides: Record<string, GuideData> = {
  "what-should-i-automate-first": {
    slug: "what-should-i-automate-first",
    title: "What Should I Automate First in My Business?",
    description:
      "A practical framework for identifying which business process to automate first — based on volume, rework, employee impact, and customer impact.",
    category: "Automation",
    readTime: "6 min",
    linkedTool: {
      label: "Manual Work Cost Calculator",
      href: "/free-tools/manual-work-cost-calculator",
    },
    linkedGuides: ["manual-paperwork-cost"],
    faq: [
      { question: "How do I know which process to automate first?", answer: "Start with the process that has the highest combination of volume, error rate, and employee frustration. Our free manual work cost calculator can help you put numbers to these factors." },
      { question: "Is automation expensive for a small business?", answer: "It depends on the process, systems, security requirements, and support model. Start by measuring the current task cost, then compare vendor quotes against a conservative, testable pilot target." },
    ],
    content: [
      { heading: "The Automation Priority Framework", body: "Every operations-heavy business has dozens of manual processes. Choosing the wrong one to automate first can waste time and money — or worse, make your team skeptical of automation altogether. The key is picking a process where automation delivers measurable, visible improvement within weeks, not months." },
      { heading: "1. Volume: How Many Times Per Week?", body: "Count how many times the process runs each week and how many people touch it. A frequent task is usually a stronger candidate than an occasional one, but measure your own workflow before estimating value." },
      { heading: "2. Rework: How Often Does It Go Wrong?", body: "Track corrections caused by copying data, missing fields, duplicate records, and unclear ownership. Record both the original task time and the time spent finding, fixing, and communicating each correction." },
      { heading: "3. Employee Impact: Frustration and Turnover", body: "Repetitive data entry and paperwork are consistently cited as top sources of workplace dissatisfaction. When skilled employees spend hours on tasks a computer could handle, they disengage. Automating their least favourite tasks often improves retention and frees them for higher-value work like customer relationships and problem-solving." },
      { heading: "4. Customer Impact: Does It Affect Service?", body: "Prioritize processes that affect response time, quoting, scheduling, follow-up, invoicing, or service quality. Define one customer-facing measure before a pilot so the result can be verified rather than assumed." },
      { heading: "The One-Week Audit Method", body: "Before investing, have each team member track repetitive tasks for one representative week: what the task is, how long it takes, how often it happens, which tools are used, and how much rework occurs. Use the observed total as your baseline." },
      { heading: "What Not to Automate First", body: "Avoid starting with processes that: (1) change frequently — you'll be rebuilding automation constantly; (2) involve complex human judgment that can't be reduced to rules; (3) are used by only one person — the training and maintenance cost may exceed the benefit; or (4) touch too many systems simultaneously — start with a single-system integration and expand." },
      { heading: "After Your First Automation Win", body: "Compare the pilot with the baseline, document what worked and what did not, and share the measured result with the team. Expand only after the process is reliable, secure, and supported." },
    ],
  },

  "manual-paperwork-cost": {
    slug: "manual-paperwork-cost",
    title: "How Much Is Manual Paperwork Costing My Company?",
    description:
      "Learn how to estimate the true loaded cost of manual data entry, paper-based workflows, and rekeying — and when automation pays for itself.",
    category: "Operations",
    readTime: "5 min",
    linkedTool: {
      label: "Manual Work Cost Calculator",
      href: "/free-tools/manual-work-cost-calculator",
    },
    linkedGuides: ["what-should-i-automate-first"],
    content: [
      { heading: "The Hidden Cost of Paper and Manual Entry", body: "Most Canadian SMB owners underestimate what manual paperwork actually costs. They see the paper, the printer toner, and maybe the filing cabinets — but the real cost is in employee time. Every hour a skilled worker spends on data entry, filing, or rekeying information between systems is an hour they're not spending on revenue-generating work." },
      { heading: "Loaded Cost: More Than Just Wages", body: "A loaded hourly cost can include wages, employer payroll contributions, benefits, equipment, facilities, and relevant overhead. Use figures from your payroll and accounting records; the correct components differ by organization and jurisdiction." },
      { heading: "The Compound Effect of Small Tasks", body: "Consider this common scenario: a team of five people each spends 20 minutes per day entering data from emails into a shared spreadsheet. That's 1.67 hours per day, or 8.3 hours per week — essentially one full day of paid work each week just on data entry. Over a year, at $35/hour loaded cost, that's over $15,000 in labour alone — not counting errors and rework." },
      { heading: "Measure Error and Rework Costs", body: "For a representative period, count corrections and record the time spent detecting, investigating, correcting, and communicating them. Multiply those observed hours by your organization’s loaded hourly cost instead of relying on a generic error-rate benchmark." },
      { heading: "Measure Paper Handling", body: "For paper purchase orders, invoices, and forms, record every touchpoint: receiving, scanning, transcription, approval, filing, and retrieval. Your own handling time and document volume create a defensible estimate." },
      { heading: "When Automation Pays for Itself", body: "Ask vendors for complete implementation and recurring costs. Compare those costs with your observed annual task and rework cost, using a conservative pilot result rather than assuming that all manual work disappears. Our calculator shows the formula and lets you supply each assumption." },
    ],
  },

  "ai-without-replacing-employees": {
    slug: "ai-without-replacing-employees",
    title: "Can AI Help My Business Without Replacing Employees?",
    description:
      "How Canadian SMBs are using AI for document processing, data extraction, and workflow assistance — augmenting their teams rather than replacing them.",
    category: "AI",
    readTime: "7 min",
    linkedTool: {
      label: "Automation ROI Calculator",
      href: "/free-tools/automation-roi-calculator",
    },
    linkedGuides: ["ai-secure-customer-information"],
    content: [
      { heading: "AI as an Assistant, Not a Replacement", body: "The most successful AI implementations in Canadian SMBs don't replace people — they handle the parts of the job that people dislike. This includes: reading and sorting emails, extracting data from documents, drafting routine responses, flagging urgent items, and organizing information. The employee still makes the decisions; AI just reduces the busywork." },
      { heading: "Candidate Workflows to Evaluate", body: "Examples worth testing include highlighting clauses for human review, extracting receipt fields for staff verification, and matching invoices to purchase orders while routing exceptions to an employee. These are workflow patterns, not claimed customer case studies or guaranteed outcomes." },
      { heading: "The Augmentation Mindset", body: "Think of AI as giving every employee a very fast, very thorough assistant who never gets tired of reading. The assistant handles: 'Read these 50 emails and tell me which five need my attention.' 'Look at this 40-page contract and highlight anything unusual.' 'Take this 2-hour meeting transcript and pull out the action items.' The human still exercises judgment, makes decisions, and maintains relationships." },
      { heading: "What AI Cannot Do (and Shouldn't Try)", body: "Current AI is poor at: understanding nuanced context without being explicitly told, making ethical judgments, building genuine human relationships, and handling situations it hasn't seen before. These limitations are precisely why AI augments rather than replaces — the uniquely human skills remain essential." },
      { heading: "Starting Small with AI", body: "Choose a narrow, reversible workflow such as document classification, field extraction, or email triage. Keep human review in place, measure accuracy and time saved, and expand only after the pilot meets an agreed threshold." },
      { heading: "Cost Reality Check", body: "Request a scoped estimate that separates discovery, implementation, integrations, model usage, monitoring, support, and change management. Document variety, data quality, security, and the number of connected systems are major cost drivers." },
    ],
  },

  "stop-leads-falling-through-cracks": {
    slug: "stop-leads-falling-through-cracks",
    title: "How Do I Stop Leads from Falling Through the Cracks?",
    description:
      "Five practical steps to ensure every lead gets a timely response, clear ownership, and consistent follow-up — even when your team is busy.",
    category: "Sales",
    readTime: "6 min",
    linkedTool: {
      label: "CRM Readiness Assessment",
      href: "/free-tools/crm-readiness-assessment",
    },
    linkedGuides: ["do-i-need-a-crm"],
    content: [
      { heading: "The Lead Leakage Problem", body: "Leads arrive through email, phone, web forms, social media, and conversations. Without a shared queue, clear ownership, and dated next actions, it is difficult to know which inquiries still need attention. Measure your own unanswered and overdue leads before choosing a solution." },
      { heading: "Step 1: Centralize Lead Capture", body: "Every lead, regardless of source, must land in one place. This doesn't require expensive software — a shared spreadsheet is better than scattered inboxes. But ideally, you want a CRM or lead-management tool that automatically captures web form submissions, email inquiries, and phone notes in one database. The key requirement: anyone on your team can see every open lead in under 10 seconds." },
      { heading: "Step 2: Assign Clear Ownership Immediately", body: "Every lead needs an owner within minutes of arrival — not hours or days. The owner is responsible for first contact, qualification, and follow-up. Without clear ownership, leads become 'everyone's responsibility' which means 'nobody's responsibility.' Even a simple rule like 'whoever is available checks the lead queue at 9am, noon, and 3pm' dramatically reduces leakage." },
      { heading: "Step 3: Define Your Pipeline Stages", body: "At minimum, you need: New → Contacted → Qualified → Proposal → Won/Lost. Every lead sits in exactly one stage. This lets you answer the two most important sales questions: 'How many leads are in each stage?' and 'How long have they been there?' Leads that sit in one stage for too long are your early warning system." },
      { heading: "Step 4: Automate Follow-Up Reminders", body: "Even the most diligent salesperson forgets to follow up when they're busy. Automated reminders — based on time since last contact, not 'I'll remember to check tomorrow' — are the single highest-impact change most SMBs can make. Set rules: if no contact in 3 days, flag it. If a proposal is outstanding for 7 days, trigger a reminder." },
      { heading: "Step 5: Measure and Improve", body: "Track total leads received, median first-response time, overdue next actions, and conversion rate by source. Compare each month with your own baseline and investigate exceptions instead of assuming a standard improvement rate." },
    ],
  },

  "do-i-need-a-crm": {
    slug: "do-i-need-a-crm",
    title: "Do I Need a CRM for My Small Business?",
    description:
      "When a shared inbox or spreadsheet stops working and a CRM becomes worth the investment — a decision guide for Canadian SMB owners.",
    category: "CRM",
    readTime: "5 min",
    linkedTool: {
      label: "CRM Readiness Assessment",
      href: "/free-tools/crm-readiness-assessment",
    },
    linkedGuides: ["stop-leads-falling-through-cracks"],
    content: [
      { heading: "The Spreadsheet Tipping Point", body: "A spreadsheet can be enough for a simple, low-volume sales process. Consider a CRM when you cannot quickly reconstruct customer history, records diverge, follow-ups lack owners, access controls are insufficient, or reporting requires manual cleanup." },
      { heading: "The Real Cost of Not Having a CRM", body: "Estimate the cost from your own missed follow-ups, duplicate work, slow response, reporting time, and lost context. Compare that baseline with the full cost of licensing, setup, migration, training, integrations, and ongoing administration." },
      { heading: "When You Don't Need a CRM (Yet)", body: "You may be able to wait if one owner can reliably manage a small contact list, every next action is visible, the sales cycle is simple, and access or reporting needs are limited. Reassess when those conditions change." },
      { heading: "CRM vs. Spreadsheet: A Quick Comparison", body: "Spreadsheets: free or cheap, flexible, familiar. But: no automated reminders, no activity history per contact, no pipeline view, no integration with email or calendar, easy to accidentally overwrite or delete data. CRMs: purpose-built for managing relationships, automated follow-up, activity timelines, pipeline management, email integration, access controls. The question isn't whether a CRM costs money — it's whether the spreadsheet is costing you more in lost opportunities." },
      { heading: "Choosing the Right CRM for a Canadian SMB", body: "Look for: Canadian data residency if privacy is a concern, email integration (Gmail/Outlook), mobile access for field staff, simple pipeline management (not enterprise complexity), and an API or integration options for your accounting and quoting tools. Popular options for Canadian SMBs include HubSpot, Zoho, Pipedrive, and custom CRM solutions built on platforms like Airtable or low-code tools. Our free CRM readiness assessment can help you identify your specific needs." },
    ],
  },

  "connect-accounting-email-quoting-scheduling": {
    slug: "connect-accounting-email-quoting-scheduling",
    title: "How Can I Connect Accounting, Email, Quoting, and Scheduling?",
    description:
      "A practical guide to integrating the four most common SMB tools — accounting software, email, quoting, and scheduling — to eliminate double-entry.",
    category: "Integrations",
    readTime: "7 min",
    linkedTool: {
      label: "Automation ROI Calculator",
      href: "/free-tools/automation-roi-calculator",
    },
    content: [
      { heading: "The Multi-Tool Problem", body: "Accounting, email, quoting, scheduling, and customer-management tools often hold overlapping records. When integrations are absent or incomplete, teams may re-enter the same customer or job information and updates may not propagate." },
      { heading: "The Double-Entry Audit", body: "Track how many times a single piece of customer information gets manually entered across your tools. A typical SMB workflow: prospect books a call (scheduler) → contact info manually added to spreadsheet → quote manually created (quoting tool) → when accepted, manually entered in accounting → invoice manually sent via email. That's four manual handoffs for one customer — each with a risk of error." },
      { heading: "Native Integrations: The Starting Point", body: "Check the current integration catalog and API documentation for each tool you already use. Test field mapping, error handling, permissions, and synchronization behaviour before buying middleware or commissioning custom work." },
      { heading: "When Native Integrations Aren't Enough", body: "Native integrations work for standard workflows but break down when you need: custom fields that don't map cleanly between tools, approval workflows before data moves between systems, real-time synchronization (not the 15-minute delay common with Zapier-style integrations), or Canadian-specific requirements like bilingual invoicing or provincial tax handling. At this point, a custom integration or middleware solution becomes necessary." },
      { heading: "The Middleware Option", body: "Middleware platforms and custom API bridges can move data between systems and apply business rules. Price the initial build, exception handling, monitoring, vendor changes, and ongoing support; the software subscription alone is not the total cost." },
      { heading: "Measuring the Payback", body: "Record current double-entry and correction time, multiply it by your loaded hourly cost, and compare the result with complete implementation and recurring costs. Use observed pilot performance in the calculation and treat error reduction as a separate measured outcome." },
    ],
  },

  "build-vs-buy-software": {
    slug: "build-vs-buy-software",
    title: "Should I Build Custom Software or Buy Another Subscription?",
    description:
      "A cost-comparison framework for Canadian SMBs deciding between another SaaS subscription and custom-built software tailored to their workflow.",
    category: "Strategy",
    readTime: "8 min",
    linkedTool: {
      label: "Automation ROI Calculator",
      href: "/free-tools/automation-roi-calculator",
    },
    content: [
      { heading: "The Real Cost of SaaS Subscriptions", body: "Inventory every subscription, paid seat, usage charge, integration add-on, administration hour, and manual workaround. Use current invoices and renewal terms rather than a generic per-user estimate." },
      { heading: "When SaaS Is the Right Choice", body: "Buy off-the-shelf when: the process is standard across most businesses (accounting, email, basic scheduling), you need something running today, you have fewer than 5 people using it, and customization isn't critical to your competitive advantage. SaaS excels at generic business functions." },
      { heading: "When Custom Software Makes Sense", body: "Evaluate custom software when the workflow differentiates the business, existing tools create material measured workarounds, or integration and control matter more than any single product’s feature list. A business case must include delivery risk, maintenance, security, hosting, ownership, and exit options." },
      { heading: "Build Your Own Multi-Year Comparison", body: "For each option, list implementation, licenses, usage, integrations, migration, training, administration, support, maintenance, and expected replacement costs over the same time horizon. Document assumptions and run a downside scenario before deciding." },
      { heading: "The Hybrid Approach", body: "Many Canadian SMBs take a hybrid approach: keep best-in-class SaaS for accounting and email, and build custom software for the workflows that are unique to their business — quoting, project tracking, field service management, or client portals. This gives you the reliability of established tools where they excel, and the efficiency of custom software where you need differentiation." },
      { heading: "Questions to Ask Before Building", body: "1) Is this process a core part of how we serve customers? 2) Do we spend more than 10 hours/week working around our current tools? 3) Would custom software let us serve more customers with the same team? 4) Do we plan to be in business and using this process in 3+ years? If you answered yes to three or more, custom software is worth serious evaluation." },
    ],
  },

  "ai-secure-customer-information": {
    slug: "ai-secure-customer-information",
    title: "How Can I Use AI Securely with Customer Information?",
    description:
      "Practical privacy and security considerations for Canadian businesses using AI tools with customer data — PIPEDA basics, data isolation, and safe defaults.",
    category: "AI",
    readTime: "7 min",
    linkedGuides: ["ai-without-replacing-employees"],
    content: [
      { heading: "PIPEDA and AI: What Canadian Businesses Need to Know", body: "PIPEDA (Personal Information Protection and Electronic Documents Act) governs how Canadian businesses collect, use, and disclose personal information. It applies to most commercial activities across Canada. Key principles relevant to AI: data minimization (only collect what you need), purpose limitation (only use data for the purpose it was collected), and safeguards (protect data proportional to its sensitivity)." },
      { heading: "Data Residency and Service Providers", body: "Map where information is processed, stored, backed up, logged, and accessed, including subprocessors and support personnel. Canadian privacy obligations vary by organization, province, sector, contract, and data type; hosting in Canada is not a substitute for a full privacy and security assessment. Consult qualified counsel when needed." },
      { heading: "Safe Defaults for AI with Customer Data", body: "1) Never send full customer databases to AI tools — send only the specific documents or records needed for the current task. 2) Strip or mask personal identifiers where possible (names, email addresses, phone numbers) before sending to AI for non-customer-facing analysis. 3) Use API-based AI services rather than public chatbot interfaces — APIs typically have stronger data processing agreements. 4) Turn off data sharing/improvement settings in your AI provider's dashboard. 5) Document which AI tools process what types of customer data for your privacy policy." },
      { heading: "The On-Premise and Private Cloud Option", body: "Private-cloud or self-hosted models may provide more control, but hosting location alone does not eliminate privacy or security risk. Evaluate logs, backups, subprocessors, remote support, access controls, monitoring, patching, and model governance with qualified privacy and security professionals." },
      { heading: "Transparency with Customers", body: "Canadian consumers increasingly expect to know when AI is involved in processing their information. Be upfront in your privacy policy: what AI tools you use, for what purpose, and what data is processed. Most customers are comfortable with AI that helps serve them better (faster responses, fewer errors) but uncomfortable with AI that makes decisions about them without human oversight." },
    ],
  },

  "automation-hours-saved": {
    slug: "automation-hours-saved",
    title: "How Many Hours Could Automation Save My Company?",
    description:
      "A step-by-step method to audit your team's repetitive tasks and estimate realistic automation time savings.",
    category: "Automation",
    readTime: "6 min",
    linkedTool: {
      label: "Manual Work Cost Calculator",
      href: "/free-tools/manual-work-cost-calculator",
    },
    linkedGuides: ["what-should-i-automate-first", "manual-paperwork-cost"],
    content: [
      { heading: "The One-Week Task Audit", body: "The most accurate way to estimate automation savings is a one-week audit. Give every team member a simple log: for each repetitive task, record what it was, how long it took, what tools they used, and how many times they did it. At the end of the week, categorize the tasks: data entry, report generation, email processing, scheduling, file management, and other." },
      { heading: "Use an Observed Recovery Rate", body: "Automation rarely removes every minute of a task because exceptions, review, and maintenance remain. Measure a pilot: divide verified hours removed by baseline hours, record the observation period, and keep a conservative allowance for oversight and failures." },
      { heading: "Worked Planning Example", body: "Hypothetical only: if a team records 12 weekly hours on a repetitive task and a pilot verifies that 3 hours are removed without shifting work elsewhere, the observed recovery rate is 25%. Apply that measured rate to an appropriate annual period and the organization’s actual loaded cost; it is not a promise of future savings." },
      { heading: "What Automation Cannot Recover", body: "Be realistic: automation doesn't eliminate the need for human judgment, relationship-building, creative problem-solving, or handling unusual situations. Tasks that require these skills will still need human time — automation just frees people to spend more time on them by handling the repetitive parts. A good rule of thumb: if you can write down exact instructions for the task in under 10 bullet points, it's probably automatable." },
      { heading: "From Audit to Action", body: "Once you have your audit results, prioritize by: highest total weekly hours × highest recovery rate. This gives you the tasks where automation will have the biggest absolute impact. Start with the top 1-2 tasks, implement automation, measure the actual savings, and use that success to build momentum for the next ones." },
    ],
  },

  "employees-entering-same-information": {
    slug: "employees-entering-same-information",
    title: "Why Are Employees Entering the Same Information Multiple Times?",
    description:
      "The root causes of double-entry in Canadian SMBs — disconnected tools, manual handoffs, and paper-based workflows — and how to fix it systematically.",
    category: "Operations",
    readTime: "5 min",
    linkedTool: {
      label: "Automation ROI Calculator",
      href: "/free-tools/automation-roi-calculator",
    },
    linkedGuides: ["connect-accounting-email-quoting-scheduling"],
    content: [
      { heading: "The Three Root Causes of Double-Entry", body: "Double-entry — entering the same customer, order, or invoice information into multiple systems — has three root causes in Canadian SMBs. First: tools that don't integrate. Second: processes that cross departmental boundaries without data handoff. Third: paper documents that must be digitized before they enter any system. Most businesses have all three." },
      { heading: "Cause 1: Disconnected Tools", body: "Your accounting software doesn't know about your CRM. Your quoting tool doesn't update your project management system. Your email doesn't feed into your support ticket tracker. Each tool is an island, and the only bridge between them is a person typing the same information again. This is the most common cause and also the most fixable with modern integration tools." },
      { heading: "Cause 2: Departmental Handoffs", body: "Sales captures lead information. Operations needs it for project setup. Accounting needs it for invoicing. Support needs it for tickets. Each handoff is a potential double-entry point. The fix: a single source of truth — typically a CRM or custom platform — that all departments access for customer information, with each department adding their layer of data rather than recreating the base record." },
      { heading: "Cause 3: Paper in a Digital World", body: "Paper purchase orders, invoices, and forms often require manual entry. Digital forms, supplier portals, and OCR with human verification can reduce rekeying, but measure accuracy, exception handling, and total time in your own workflow." },
      { heading: "The Single Source of Truth", body: "The long-term solution to double-entry is establishing a single source of truth for each type of data: one place where customer information lives, one place where orders/projects live, one place where financial data lives. Tools connect to these sources rather than maintaining their own copies. This is the architectural principle behind most successful SMB automation projects." },
      { heading: "What to Do This Month", body: "1) Identify the information entered more than once. 2) Choose the authoritative system for each field. 3) Check current native integrations and API access. 4) Pilot one controlled handoff with logging and a rollback path. Compare the measured result with your baseline before expanding." },
    ],
  },
};
