export interface Testimonial {
  id: string;
  company: string;
  logo: string;
  industry: string;
  project: string;
  quote: string;
  author: string;
  role: string;
}

export type ShowcaseSlide =
  | { type: "testimonial"; data: Testimonial }
  | { type: "pns-interlude" };

export const testimonials: Testimonial[] = [
  {
    id: "yellow-cap-tours",
    company: "Yellow Cap Tours",
    logo: "/images/yellow-cap-tours.png",
    industry: "Tourism & Transportation",
    project: "Tour Operations & Booking Allocation System",
    quote:
      "Pacific North Systems took the time to understand how our business actually operates before building our solution. The system they delivered was designed around how our business really works, not around generic software. It simplified our booking process, reduced manual work, and gave us much better visibility into our daily operations.\n\nCommunication throughout the project was clear, practical, and focused on solving the right problem. I highly recommend Pacific North Systems to businesses looking for custom software built around their operations.",
    author: "Lucio Kniest",
    role: "Owner, Yellow Cap Tours",
  },
];

/** Flat sequence: testimonial → pns-interlude → testimonial → pns-interlude → … */
export function buildShowcaseSequence(): ShowcaseSlide[] {
  if (testimonials.length === 0) return [];
  const seq: ShowcaseSlide[] = [];
  for (const t of testimonials) {
    seq.push({ type: "testimonial", data: t }, { type: "pns-interlude" });
  }
  return seq;
}

/** Map from a testimonial id to its first index in the sequence */
export function getSeqIndexForTestimonial(testimonialId: string): number {
  const seq = buildShowcaseSequence();
  return seq.findIndex((s) => s.type === "testimonial" && s.data.id === testimonialId);
}

