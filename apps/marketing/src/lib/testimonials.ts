import type { StaticImageData } from "next/image";

export interface TestimonialData {
  quote: string;
  shortQuote: string;
  clientName: string;
  clientRole: string;
  companyName: string;
  companyLogo: string | StaticImageData;
  companyLogoAlt: string;
  projectLabel?: string;
  projectUrl?: string;
}

export const testimonials: TestimonialData[] = [
  {
    quote: `Pacific North Systems took the time to understand how our business actually operates before building our solution. We manage bookings from multiple tourism platforms and needed a better way to organize passengers, schedules, and vehicle capacity without relying on manual processes.

The system they delivered was designed around how our business really works, not around generic software. It has simplified our booking process, reduced manual work, and given us much better visibility into our daily operations.

Throughout the project, communication was clear, practical, and focused on solving real business problems. We now have a solution that saves our team time, improves how we organize our tours, and gives us confidence as we continue to grow. I highly recommend Pacific North Systems to any business looking for custom software built around their operations.`,
    shortQuote: `Pacific North Systems built a solution around how our business really works , not generic software. It simplified our booking process, reduced manual work, and gave us better visibility into daily operations. Communication was clear and focused on real problems. We highly recommend them for custom software built around your operations.`,
    clientName: "Lucio Kniest",
    clientRole: "Owner",
    companyName: "Yellow Cap Tours",
    companyLogo: "/images/yellow-cap-tours.png",
    companyLogoAlt: "Yellow Cap Tours",
    projectLabel: "Tour Operations & Booking Allocation System",
    projectUrl: "/solutions#custom-business-software",
  },
];
