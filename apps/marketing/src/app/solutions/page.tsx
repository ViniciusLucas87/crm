import type { Metadata } from "next";
import { Container } from "@/components/ui/container";
import { Button } from "@/components/ui/button";
import { SolutionSection } from "@/components/solutions";
import type { SolutionSectionData } from "@/components/solutions";
import { siteConfig } from "@/lib/site-config";
import {
  Workflow,
  LayoutDashboard,
  Wrench,
  ClipboardCheck,
  BarChart3,
  FileText,
  Users,
  Plug,
  FileSearch,
  Bot,
  Monitor,
  PhoneIncoming,
} from "lucide-react";

export const metadata: Metadata = {
  title: "Business Software and Automation Solutions",
  description:
    "Explore workflow automation, custom software, inspection tools, dashboards, CRM development, integrations, AI document processing, and operational support from Pacific North Systems.",
};

const solutionsData: SolutionSectionData[] = [
  {
    id: "missed-call-lead-recovery",
    icon: PhoneIncoming,
    title: "Missed Call Lead Recovery",
    problem:
      "A missed call often means a customer is ready to talk now. This system responds with care, preserves the contact and gives your team a clear next action before the opportunity goes cold.",
    whenUseful:
      "When owners, dispatchers and service teams cannot answer every call while driving, serving customers, working on site or handling another conversation.",
    whoNeedsIt:
      "Service businesses, trades, clinics, property teams and any company where an unanswered phone call can become lost revenue.",
    useCases: [
      "Detect an unanswered call and capture the caller number",
      "Filter obvious spam before creating sales work",
      "Send a friendly text that confirms your team will call back",
      "Create or update the contact inside your CRM",
      "Add a callback task to the daily sales workspace",
      "Record delivery status and prevent duplicate messages",
    ],
    exampleWorkflow:
      "A customer calls while your team is busy. The call is not answered, so the system records the event, sends a respectful text within moments and creates a callback task. The customer knows they were heard and your team sees exactly who needs attention.",
    typicalFirstVersion:
      "One business number connected to a missed call workflow, automatic text response, CRM lead capture and callback tracking. The wording, working hours and follow up rules are tailored to your business.",
    expectedOutcome:
      "Fewer callers left wondering, faster follow up, a complete record of every opportunity and less dependence on memory at the end of a busy day.",
    relevantIndustries: [
      "Trades",
      "Construction",
      "Property Services",
      "Clinics",
      "Professional Services",
    ],
  },
  {
    id: "workflow-automation",
    icon: Workflow,
    title: "Workflow Automation",
    problem:
      "Workflow automation helps teams with complex operations move requests, approvals, handoffs, and recurring updates without relying on memory, inbox searches, or duplicated spreadsheets.",
    whenUseful:
      "When work moves through a predictable process with repeated handoffs, approvals, scheduling, and status updates that currently depend on email chains and manual follow up.",
    whoNeedsIt:
      "Operations managers, field supervisors, project coordinators, and administrative teams who spend significant time tracking work status and routing information between departments.",
    useCases: [
      "Automated approval routing for change orders, invoices, and purchase requests",
      "Status tracking and notifications for job progression across departments",
      "Automated scheduling and dispatch based on job requirements and availability",
      "Digital handoff checklists between field and office teams",
      "Automated client communication triggers at key project milestones",
    ],
    exampleWorkflow:
      "A construction company receives a change order from the field. The workflow automatically routes it to the project manager for review, then to the client for approval, back to the field team with updated specs, and logs everything for reporting , without anyone chasing emails or updating spreadsheets.",
    typicalFirstVersion:
      "A single automated approval workflow for one high-volume, high-delay process, with role-based routing, status visibility, and notification triggers. Deployed and iterated within 2-3 weeks.",
    expectedOutcome:
      "Reduced approval cycle times, fewer missed handoffs, clear accountability, and a documented process that can be measured and improved over time.",
    relevantIndustries: [
      "Construction",
      "Property Management",
      "Manufacturing",
      "Engineering",
      "Logistics",
    ],
  },
  {
    id: "custom-business-software",
    icon: LayoutDashboard,
    title: "Custom Business Software",
    problem:
      "Custom software is useful when your process, data, or responsibilities do not fit cleanly inside generic tools. Start with the workflow, then build only what the operation needs.",
    whenUseful:
      "When off-the-shelf software forces your team to adapt its process to the tool, when you need multiple systems to complete one workflow, or when your industry has unique compliance, tracking, or reporting requirements.",
    whoNeedsIt:
      "Business owners and operations leaders who have outgrown spreadsheets and generic software but do not need (or cannot justify) a large enterprise platform.",
    useCases: [
      "Custom job management systems that track from estimate to invoice",
      "Industry-specific compliance and safety tracking tools",
      "Client portal development for project visibility and document sharing",
      "Inventory and asset management systems tailored to field operations",
      "Custom scheduling and resource allocation tools",
    ],
    exampleWorkflow:
      "A restoration company needs to track jobs from first call through insurance claim, dispatch, field work, drying monitoring, invoicing, and reconciliation. No single off-the-shelf product handles their specific workflow, so we build a focused system that matches how they actually operate.",
    typicalFirstVersion:
      "A focused application covering one core workflow end-to-end, built with a small set of screens that match how the team already thinks about the work. Deployed within 4-6 weeks.",
    expectedOutcome:
      "A single system that replaces multiple spreadsheets and disconnected tools, reduced data entry, better visibility into job status, and a foundation that can grow with the business.",
    relevantIndustries: [
      "Construction",
      "Restoration",
      "Property Management",
      "Trades",
      "Manufacturing",
    ],
  },
  {
    id: "internal-tools",
    icon: Wrench,
    title: "Internal Tools",
    problem:
      "Internal tools remove repeated work from the processes that make your business run, without forcing every team to change how it thinks about the job.",
    whenUseful:
      "When teams rely on fragile spreadsheets, shared inboxes, and repeated admin work to keep operations moving, and when the people doing the work need tools built around them.",
    whoNeedsIt:
      "Operations teams, administrators, dispatchers, and coordinators who spend hours each week on repetitive data management, lookups, and manual processes.",
    useCases: [
      "Operational dashboards that consolidate information from multiple systems",
      "Admin panels for managing jobs, clients, and resources in one place",
      "Data entry tools that validate and standardize information as it is entered",
      "Bulk operation tools for processing multiple records simultaneously",
      "Internal search tools across operational data, documents, and communications",
    ],
    exampleWorkflow:
      "A dispatch team manually cross-references three systems to assign field crews. We build an internal tool that pulls from all three, shows availability, skills, and location, and lets dispatchers assign crews in one click , cutting dispatch time significantly.",
    typicalFirstVersion:
      "A single-screen tool that consolidates the most frequent operational lookup or data-entry task. Built and deployed within 1-2 weeks.",
    expectedOutcome:
      "Reduced time spent on administrative tasks, fewer errors from manual data handling, and operational staff focused on higher-value work instead of data management.",
    relevantIndustries: [
      "Construction",
      "Logistics",
      "Property Management",
      "Trades",
      "Manufacturing",
    ],
  },
  {
    id: "inspection-software",
    icon: ClipboardCheck,
    title: "Inspection Software",
    problem:
      "Inspection software helps field teams capture checklists, notes, photos, signatures, and exceptions once, then turn that information into a more consistent report.",
    whenUseful:
      "When field inspections currently involve paper forms, photos saved separately, manual report writing after the fact, and inconsistent documentation across different inspectors.",
    whoNeedsIt:
      "Field inspectors, quality control teams, property managers, safety officers, and service technicians who need to document conditions, compliance, and completed work.",
    useCases: [
      "Site inspection checklists with photos, annotations, and digital signatures",
      "Property condition reports for move-in, move-out, and routine inspections",
      "Safety and compliance audits with corrective action tracking",
      "Equipment and asset inspections with maintenance history",
      "Quality control inspections with automated pass/fail and report generation",
    ],
    exampleWorkflow:
      "A field inspector arrives on site, opens the inspection app on their phone, completes the digital checklist with photos and notes, captures a client signature, and submits. A formatted PDF report is generated automatically and sent to the client and office , no paper, no retyping, no delay.",
    typicalFirstVersion:
      "A mobile-friendly inspection form for one inspection type, with photo capture, digital signature, and automated PDF report generation. Deployed within 3-4 weeks.",
    expectedOutcome:
      "Consistent inspection documentation, faster report turnaround, reduced admin time, and a searchable archive of inspection records organized by project, date, and inspector.",
    relevantIndustries: [
      "Construction",
      "Property Management",
      "Restoration",
      "Engineering",
      "Trades",
    ],
  },
  {
    id: "business-dashboards",
    icon: BarChart3,
    title: "Business Dashboards",
    problem:
      "Business dashboards turn recurring operational information into a clearer view of work, exceptions, capacity, and decisions.",
    whenUseful:
      "When leadership decisions rely on manually compiled reports, when operational status is unclear, or when teams lack visibility into capacity, bottlenecks, and performance trends.",
    whoNeedsIt:
      "Business owners, operations managers, and department leads who need to understand work status, resource allocation, and performance without waiting for weekly manual reports.",
    useCases: [
      "Current job status and progress dashboards across all active projects",
      "Capacity and resource utilization tracking for field and office teams",
      "Revenue, cost, and margin dashboards updated from operational data",
      "Exception and bottleneck monitoring with alerts for at-risk work",
      "KPI tracking with trend visualization and automated reporting",
    ],
    exampleWorkflow:
      "A manufacturing operations manager currently receives a Friday spreadsheet with last week's numbers. We build a live dashboard that shows work-in-progress, throughput, delays, and capacity in real time, so decisions can be made during the week, not after it.",
    typicalFirstVersion:
      "A single dashboard with 5-7 key metrics, connected to existing data sources, designed for one operational role. Deployed within 2-3 weeks.",
    expectedOutcome:
      "Faster operational decisions, reduced manual reporting time, better visibility into work status, and the ability to identify and address issues before they become problems.",
    relevantIndustries: [
      "Manufacturing",
      "Construction",
      "Logistics",
      "Property Management",
      "Engineering",
    ],
  },
  {
    id: "reporting-systems",
    icon: FileText,
    title: "Reporting Systems",
    problem:
      "Reporting systems make recurring information more consistent, easier to review, and more useful for the people responsible for operational decisions.",
    whenUseful:
      "When recurring reports consume significant staff time to compile, when report quality varies by who prepares them, or when the information already exists but is not assembled into useful reports.",
    whoNeedsIt:
      "Operations managers, finance teams, compliance officers, and executives who depend on regular reports for decision-making, client communication, and regulatory requirements.",
    useCases: [
      "Automated weekly and monthly operational reports from live data",
      "Client-facing project status and progress reports generated on demand",
      "Compliance and regulatory reporting with audit trails",
      "Financial and operational metric reports with drill-down capability",
      "Custom report builders for ad-hoc operational analysis",
    ],
    exampleWorkflow:
      "A property management company manually compiles monthly owner reports by pulling data from three systems. We connect the data sources and automate the report generation, so owners receive consistent, timely reports and staff reclaim hours each month.",
    typicalFirstVersion:
      "One automated recurring report type, pulling from existing data sources, with consistent formatting and scheduled delivery. Deployed within 2-3 weeks.",
    expectedOutcome:
      "Consistent, timely reports with reduced manual effort, fewer errors, and more time for analysis and action rather than compilation.",
    relevantIndustries: [
      "Property Management",
      "Construction",
      "Manufacturing",
      "Engineering",
      "Logistics",
    ],
  },
  {
    id: "crm-development",
    icon: Users,
    title: "CRM Development",
    problem:
      "A company-owned CRM can reflect the way your team manages relationships, projects, service, budgets, and reporting instead of making the business adapt to a generic pipeline.",
    whenUseful:
      "When generic CRMs do not support your sales process, service workflow, or reporting needs, and when your team needs a system built around client relationships plus operational delivery.",
    whoNeedsIt:
      "Sales teams, account managers, service managers, and business owners who need to track the full client lifecycle , from opportunity through delivery and ongoing service.",
    useCases: [
      "CRM integrated with project and job management for end-to-end visibility",
      "Service and maintenance tracking tied to client accounts and history",
      "Quote-to-invoice workflows with approval routing and client acceptance",
      "Client communication history across sales, service, and support",
      "Pipeline and forecasting dashboards connected to operational capacity",
    ],
    exampleWorkflow:
      "A trades company uses a generic CRM for sales and separate systems for job management and invoicing. We build a CRM owned by the company that tracks each lead through quoting, job execution, invoicing, and service follow up, all in one system that matches the actual process.",
    typicalFirstVersion:
      "A focused CRM covering the core client lifecycle for one service line, with contact management, opportunity tracking, and basic job linking. Deployed within 4-6 weeks.",
    expectedOutcome:
      "A single view of the client relationship from first contact through delivery, reduced duplication between sales and operations systems, and a CRM that supports rather than constrains the team.",
    relevantIndustries: [
      "Construction",
      "Trades",
      "Property Management",
      "Manufacturing",
      "Professional Services",
    ],
  },
  {
    id: "system-integrations",
    icon: Plug,
    title: "System Integrations",
    problem:
      "Integrations connect the tools your team already uses so information can move between customer, operational, financial, and reporting workflows with less re-entry.",
    whenUseful:
      "When your team retypes information between systems, when data exists in one system but is needed in another, or when disconnected tools create inconsistent information across the business.",
    whoNeedsIt:
      "Operations teams, finance departments, and IT managers who manage multiple business systems and need them to work together without manual data transfer.",
    useCases: [
      "Accounting software integration with operational and project management systems",
      "Field data collection tools connected to office reporting and analytics",
      "CRM integration with email, calendar, and communication platforms",
      "Inventory and procurement systems connected to job management",
      "Custom API development for connecting legacy or industry-specific tools",
    ],
    exampleWorkflow:
      "A logistics company enters job details in their operations system and then retypes the same information into their accounting software for invoicing. We build an integration that syncs job data automatically, so information flows from operations to finance without manual entry.",
    typicalFirstVersion:
      "A single integration between two systems, handling the most frequently transferred data type, with error handling and logging. Deployed within 2-4 weeks.",
    expectedOutcome:
      "Eliminated duplicate data entry between systems, reduced errors, consistent information across the business, and workflows that move faster without manual handoffs.",
    relevantIndustries: [
      "Logistics",
      "Manufacturing",
      "Construction",
      "Property Management",
      "Professional Services",
    ],
  },
  {
    id: "ai-document-processing",
    icon: FileSearch,
    title: "AI Document Processing",
    problem:
      "AI document processing can make forms, PDFs, and recurring records easier to search, structure, and review while keeping people responsible for judgement and decisions.",
    whenUseful:
      "When your team spends significant time searching through documents, extracting information from PDFs and forms, or manually structuring unstructured document data.",
    whoNeedsIt:
      "Administrative teams, compliance officers, project managers, and anyone who regularly needs to find, extract, or organize information from business documents.",
    useCases: [
      "Automated data extraction from invoices, purchase orders, and receipts",
      "Document search and retrieval across project files, contracts, and correspondence",
      "Automated document classification and routing for review workflows",
      "Information extraction from inspection reports, field notes, and forms",
      "Document summarization for quick review of lengthy reports and contracts",
    ],
    exampleWorkflow:
      "A property management company receives hundreds of invoices monthly in various formats. We implement AI document processing that extracts vendor, amount, date, and job reference automatically, routes for approval, and feeds into the accounting system , reducing manual data entry significantly.",
    typicalFirstVersion:
      "Document processing for one document type and one extraction workflow, with human review step. Deployed within 3-5 weeks.",
    expectedOutcome:
      "Reduced time spent on document data entry and searching, faster document processing, consistent data extraction, and team members focused on review and decisions rather than manual extraction.",
    relevantIndustries: [
      "Property Management",
      "Construction",
      "Manufacturing",
      "Logistics",
      "Professional Services",
    ],
  },
  {
    id: "ai-assistants",
    icon: Bot,
    title: "AI Assistants",
    problem:
      "Add carefully scoped assistance where records, access controls, and review processes are ready. AI assistants should support decisions, not make them unsupervised.",
    whenUseful:
      "When your team needs help searching operational knowledge, drafting routine communications, or processing information , and when you have structured data, clear access controls, and defined review processes.",
    whoNeedsIt:
      "Operations teams, customer service staff, project managers, and knowledge workers who need faster access to information and assistance with routine cognitive tasks.",
    useCases: [
      "Operational knowledge base search and Q&A for field and office teams",
      "Draft response generation for common client inquiries, reviewed before sending",
      "Data analysis assistance for operational trends and pattern identification",
      "Meeting and conversation summarization tied to project and client records",
      "Intelligent routing and prioritization of incoming requests and tasks",
    ],
    exampleWorkflow:
      "A field supervisor needs to quickly find the warranty terms for a specific product installed at a job site two years ago. An AI assistant searches the project documentation, contract records, and product database to surface the relevant information in seconds instead of hours of manual file searching.",
    typicalFirstVersion:
      "One AI supported workflow scoped to one type of question or task, with clear boundaries, human review, and logging. Deployed within 2 to 4 weeks.",
    expectedOutcome:
      "Faster access to operational information, reduced time spent on routine information retrieval, and AI assistance that supports rather than replaces human judgement.",
    relevantIndustries: [
      "Construction",
      "Property Management",
      "Manufacturing",
      "Professional Services",
      "Engineering",
    ],
  },
  {
    id: "operational-it-support",
    icon: Monitor,
    title: "Operational IT Support",
    problem:
      "Keep the systems reliable, understandable, and useful as the operation changes. Operational IT support ensures the tools you depend on continue to work as your business evolves.",
    whenUseful:
      "When your business depends on custom or integrated systems that need ongoing maintenance, when systems need to adapt as the business grows, or when you need reliable support without a full internal IT team.",
    whoNeedsIt:
      "Business owners and operations managers who rely on software systems for daily operations and need responsive, knowledgeable support to keep things running.",
    useCases: [
      "Ongoing maintenance and bug fixes for custom business applications",
      "System monitoring and proactive issue detection",
      "Database maintenance and performance optimization",
      "User support and training for operational systems",
      "System updates and adaptations as business processes evolve",
    ],
    exampleWorkflow:
      "A construction company's custom job management system needs an update to handle a new service line they have added. We implement the changes, test with the team, deploy during a low-activity window, and provide training , all without disrupting ongoing operations.",
    typicalFirstVersion:
      "A support agreement covering one system with defined response times, regular maintenance windows, and a clear process for requesting changes or reporting issues.",
    expectedOutcome:
      "Reliable systems with minimal downtime, responsive support when issues arise, and the ability to evolve systems as the business grows and changes.",
    relevantIndustries: [
      "Construction",
      "Property Management",
      "Manufacturing",
      "Trades",
      "Logistics",
    ],
  },
];

export default function SolutionsPage() {
  return (
    <main>
      {/* Page header */}
      <section className="bg-pns-dark-hero pt-28 pb-16 lg:pt-32 lg:pb-20">
        <Container>
          <h1 className="text-[clamp(2rem,4vw,3rem)] font-bold text-pns-text-soft-white">
            Software that fits the way your operation works
          </h1>
          <p className="mt-4 text-pns-text-light max-w-2xl leading-relaxed">
            Start with a workflow map, a small first version, and a clear
            measure of operational improvement. If you are not sure where to
            begin, use the Business Automation Assessment or book an Operations
            Audit.
          </p>
          <div className="mt-8 flex flex-col sm:flex-row gap-4">
            <Button
              variant="primary"
              size="default"
              href="/assessment"
              className="bg-white !text-pns-text-primary hover:bg-white/90"
            >
              Take the Assessment
            </Button>
            <Button
              variant="outline"
              size="default"
              href={siteConfig.contact.calendlyAudit}
              external
              className="border-white/30 !text-white hover:bg-white/10"
            >
              Book an Operations Audit
            </Button>
          </div>
        </Container>
      </section>

      {/* Anchor navigation */}
      <section className="bg-white border-b border-pns-text-primary/10 sticky top-[72px] lg:top-[80px] z-[4]">
        <Container>
          <nav
            className="flex overflow-x-auto gap-4 py-3 text-sm"
            aria-label="Solutions quick navigation"
          >
            {solutionsData.map((s) => (
              <a
                key={s.id}
                href={`#${s.id}`}
                className="whitespace-nowrap text-pns-text-muted hover:text-pns-text-primary transition-colors shrink-0"
              >
                {s.title}
              </a>
            ))}
          </nav>
        </Container>
      </section>

      {/* Solution sections */}
      {solutionsData.map((data, index) => (
        <SolutionSection key={data.id} data={data} index={index} />
      ))}

      {/* Final CTA */}
      <section className="bg-pns-dark-footer py-16 lg:py-20">
        <Container>
          <div className="max-w-2xl mx-auto text-center">
            <h2 className="text-2xl lg:text-3xl font-bold text-pns-text-soft-white">
              Ready to improve how your operation works?
            </h2>
            <p className="mt-4 text-pns-text-light leading-relaxed">
              Book a free Operations Audit, and we will review your current
              processes together to identify the best place to start.
            </p>
            <div className="mt-8">
              <Button
                variant="primary"
                size="lg"
                href={siteConfig.contact.calendlyAudit}
                external
                className="bg-white !text-pns-text-primary hover:bg-white/90"
              >
                Book a 30-minute Operations Audit
              </Button>
            </div>
          </div>
        </Container>
      </section>
    </main>
  );
}
