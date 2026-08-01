"use client";

import { useState, useCallback, useEffect, useRef, useMemo } from "react";
import Image from "next/image";
import { AnimatePresence, motion } from "framer-motion";
import {
  testimonials,
  buildShowcaseSequence,
  getSeqIndexForTestimonial,
} from "@/data/customer-showcase";

const TESTIMONIAL_DURATION = 4000;
const INTERLUDE_DURATION = 1000;
const RESUME_DELAY = 12000;

/* -------------------------------------------------------------------------- */
/*  Main component                                                            */
/* -------------------------------------------------------------------------- */

export function CustomerShowcase() {
  const slides = useMemo(() => buildShowcaseSequence(), []);
  const [activeIndex, setActiveIndex] = useState(0);
  const [isPaused, setIsPaused] = useState(false);
  const [reduceMotion, setReduceMotion] = useState(false);
  const resumeTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const rotationRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const totalSlides = slides.length;
  const active = slides[activeIndex];

  // Find current testimonial index (for dots / selector highlighting)
  const activeTestimonialIdx = useMemo(() => {
    if (active?.type === "testimonial") {
      return testimonials.findIndex((t) => t.id === active.data.id);
    }
    // During interlude, show the NEXT testimonial's dot (or previous if at end)
    const nextIdx = (activeIndex + 1) % totalSlides;
    const next = slides[nextIdx];
    if (next?.type === "testimonial") {
      return testimonials.findIndex((t) => t.id === next.data.id);
    }
    return 0;
  }, [active, activeIndex, totalSlides, slides]);

  useEffect(() => {
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    setReduceMotion(mq.matches);
    const handler = (e: MediaQueryListEvent) => setReduceMotion(e.matches);
    mq.addEventListener("change", handler);
    return () => mq.removeEventListener("change", handler);
  }, []);

  // Auto-rotation with variable duration
  useEffect(() => {
    if (isPaused || totalSlides <= 1) return;

    const duration =
      slides[activeIndex]?.type === "pns-interlude"
        ? INTERLUDE_DURATION
        : TESTIMONIAL_DURATION;

    rotationRef.current = setTimeout(() => {
      setActiveIndex((prev) => (prev + 1) % totalSlides);
    }, duration);

    return () => {
      if (rotationRef.current) clearTimeout(rotationRef.current);
    };
  }, [activeIndex, isPaused, totalSlides, slides]);

  const goToTestimonial = useCallback(
    (testimonialIdx: number) => {
      const t = testimonials[testimonialIdx];
      if (!t) return;
      const seqIdx = getSeqIndexForTestimonial(t.id);
      if (seqIdx >= 0) {
        setActiveIndex(seqIdx);
        setIsPaused(true);
        if (resumeTimer.current) clearTimeout(resumeTimer.current);
        resumeTimer.current = setTimeout(() => setIsPaused(false), RESUME_DELAY);
      }
    },
    [],
  );

  const handlePrev = useCallback(() => {
    const prevIdx =
      (activeTestimonialIdx - 1 + testimonials.length) % testimonials.length;
    goToTestimonial(prevIdx);
  }, [activeTestimonialIdx, goToTestimonial]);

  const handleNext = useCallback(() => {
    const nextIdx = (activeTestimonialIdx + 1) % testimonials.length;
    goToTestimonial(nextIdx);
  }, [activeTestimonialIdx, goToTestimonial]);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "ArrowLeft") {
        e.preventDefault();
        handlePrev();
      }
      if (e.key === "ArrowRight") {
        e.preventDefault();
        handleNext();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [handlePrev, handleNext]);

  useEffect(() => {
    return () => {
      if (resumeTimer.current) clearTimeout(resumeTimer.current);
      if (rotationRef.current) clearTimeout(rotationRef.current);
    };
  }, []);

  const transition = reduceMotion
    ? { duration: 0.15 }
    : { duration: 0.3, ease: [0.25, 0.1, 0.25, 1] as [number, number, number, number] };

  return (
    <section
      className="py-16 sm:py-20 bg-pns-bg relative overflow-hidden"
      aria-labelledby="showcase-heading"
      id="customer-success"
      onMouseEnter={() => setIsPaused(true)}
      onMouseLeave={() => setIsPaused(false)}
      onFocus={() => setIsPaused(true)}
      onBlur={() => setIsPaused(false)}
    >
      <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-pns-text-primary/10 to-transparent" />

      <div className="max-w-[1280px] mx-auto px-6 sm:px-8 lg:px-12">
        {/* Header */}
        <div className="mb-8">
          <p className="text-xs font-semibold uppercase tracking-widest text-pns-text-muted mb-2">
            Trusted by businesses across British Columbia
          </p>
          <h2
            id="showcase-heading"
            className="text-[clamp(1.75rem,4vw,2.5rem)] font-bold text-pns-text-primary tracking-[-0.015em]"
          >
            Software That Solves Real Problems
          </h2>
        </div>

        {/* Desktop */}
        <div className="hidden lg:grid lg:grid-cols-[260px_1fr] gap-10 items-start">
          {/* Selector (real clients only) */}
          <div className="space-y-3" role="tablist" aria-label="Client testimonials">
            {testimonials.map((t) => {
              const idx = testimonials.indexOf(t);
              const isActive = idx === activeTestimonialIdx;
              return (
                <button
                  key={t.id}
                  role="tab"
                  aria-selected={isActive}
                  onClick={() => goToTestimonial(idx)}
                  className={`
                    w-full flex items-center gap-3 px-4 py-3 rounded-[14px] border-2
                    transition-all duration-300 ease-out cursor-pointer text-left
                    focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-pns-text-primary
                    ${
                      isActive
                        ? "bg-white border-pns-text-primary shadow-md"
                        : "bg-white/50 border-transparent hover:bg-white hover:border-pns-text-primary/15 hover:shadow-sm"
                    }
                  `}
                >
                  <Image
                    src={t.logo}
                    alt={t.company}
                    width={192}
                    height={192}
                    className={`w-24 h-24 object-contain rounded transition-all duration-300 ${
                      isActive ? "" : "grayscale opacity-60"
                    }`}
                  />
                  <span
                    className={`text-[13px] font-semibold transition-colors ${
                      isActive ? "text-pns-text-primary" : "text-pns-text-muted"
                    }`}
                  >
                    {t.company}
                  </span>
                </button>
              );
            })}
          </div>

          {/* Content */}
          <div className="min-h-[380px] relative" aria-live={reduceMotion ? "off" : "polite"}>
            <AnimatePresence mode="wait">
              {active?.type === "testimonial" ? (
                <TestimonialCard key={active.data.id} data={active.data} transition={transition} />
              ) : (
                <PNSInterlude key="pns" transition={transition} reduceMotion={reduceMotion} />
              )}
            </AnimatePresence>
          </div>
        </div>

        {/* Mobile / Tablet */}
        <div className="lg:hidden">
          {/* Horizontal selector */}
          <div
            className="flex gap-3 overflow-x-auto pb-3 snap-x snap-mandatory scrollbar-none -mx-2 px-2 mb-6"
            role="tablist"
            aria-label="Client testimonials"
          >
            {testimonials.map((t) => {
              const idx = testimonials.indexOf(t);
              const isActive = idx === activeTestimonialIdx;
              return (
                <button
                  key={t.id}
                  role="tab"
                  aria-selected={isActive}
                  onClick={() => goToTestimonial(idx)}
                  className={`
                    shrink-0 snap-start flex items-center gap-2.5 px-4 py-2.5 rounded-[12px] border-2
                    transition-all duration-300 cursor-pointer
                    ${
                      isActive
                        ? "bg-white border-pns-text-primary shadow-md"
                        : "bg-white/50 border-transparent hover:bg-white hover:border-pns-text-primary/15"
                    }
                  `}
                >
                  <Image
                    src={t.logo}
                    alt={t.company}
                    width={144}
                    height={144}
                    className={`w-[72px] h-[72px] object-contain rounded transition-all duration-300 ${
                      isActive ? "" : "grayscale opacity-60"
                    }`}
                  />
                  <span
                    className={`text-[12px] font-semibold whitespace-nowrap ${
                      isActive ? "text-pns-text-primary" : "text-pns-text-muted"
                    }`}
                  >
                    {t.company}
                  </span>
                </button>
              );
            })}
          </div>

          {/* Content */}
          <div className="min-h-[340px] relative" aria-live={reduceMotion ? "off" : "polite"}>
            <AnimatePresence mode="wait">
              {active?.type === "testimonial" ? (
                <TestimonialCard key={active.data.id} data={active.data} transition={transition} />
              ) : (
                <PNSInterlude key="pns" transition={transition} reduceMotion={reduceMotion} />
              )}
            </AnimatePresence>
          </div>
        </div>

        {/* Controls , dots represent testimonials only */}
        {testimonials.length > 1 && (
          <div className="flex items-center justify-center gap-4 mt-8">
            <button
              onClick={handlePrev}
              aria-label="Previous testimonial"
              className="w-8 h-8 rounded-full border border-pns-text-primary/15 bg-white flex items-center justify-center text-pns-text-primary hover:border-pns-text-primary/40 hover:bg-pns-soft-blue transition-all"
            >
              <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
                <path d="M10 12L6 8l4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </button>

            <div className="flex gap-1.5" role="tablist" aria-label="Testimonials">
              {testimonials.map((t, i) => (
                <button
                  key={t.id}
                  role="tab"
                  aria-selected={i === activeTestimonialIdx}
                  aria-label={`${t.company} testimonial`}
                  onClick={() => goToTestimonial(i)}
                  className="h-1.5 rounded-full bg-pns-text-primary/10 overflow-hidden w-5 cursor-pointer hover:bg-pns-text-primary/20 transition-colors"
                >
                  <div
                    className="h-full rounded-full bg-pns-text-primary transition-colors"
                    style={{ width: i === activeTestimonialIdx ? "100%" : "0%" }}
                  />
                </button>
              ))}
            </div>

            <button
              onClick={handleNext}
              aria-label="Next testimonial"
              className="w-8 h-8 rounded-full border border-pns-text-primary/15 bg-white flex items-center justify-center text-pns-text-primary hover:border-pns-text-primary/40 hover:bg-pns-soft-blue transition-all"
            >
              <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
                <path d="M6 4l4 4-4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </button>
          </div>
        )}
      </div>
    </section>
  );
}

/* -------------------------------------------------------------------------- */
/*  Testimonial card                                                          */
/* -------------------------------------------------------------------------- */

function TestimonialCard({
  data,
  transition,
}: {
  data: {
    company: string;
    logo: string;
    industry: string;
    project: string;
    quote: string;
    author: string;
    role: string;
  };
  transition: object;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={transition}
      className="bg-white rounded-[20px] border border-pns-text-primary/8 shadow-sm p-6 sm:p-10 h-full"
    >
      <div className="flex items-center gap-4 mb-5">
        <Image
          src={data.logo}
          alt={data.company}
          width={1440}
          height={360}
          className="h-[216px] sm:h-[264px] lg:h-[312px] w-auto object-contain"
          style={{ width: "auto" }}
        />
        <span className="text-[11px] font-semibold uppercase tracking-wider text-pns-text-muted bg-pns-soft-blue px-2.5 py-1 rounded-full shrink-0">
          {data.industry}
        </span>
      </div>

      <blockquote className="text-[clamp(1rem,1.4vw,1.2rem)] text-pns-text-primary leading-[1.65] font-medium mb-5 whitespace-pre-line">
        &ldquo;{data.quote}&rdquo;
      </blockquote>

      <div className="flex items-center gap-3 pt-5 border-t border-pns-text-primary/8">
        <div>
          <p className="text-sm font-semibold text-pns-text-primary">{data.author}</p>
          <p className="text-xs text-pns-text-muted">{data.role}</p>
        </div>
      </div>
    </motion.div>
  );
}

/* -------------------------------------------------------------------------- */
/*  PNS logo interlude , centered, decorative, not a content slide            */
/* -------------------------------------------------------------------------- */

function PNSInterlude({
  transition,
  reduceMotion,
}: {
  transition: object;
  reduceMotion: boolean;
}) {
  return (
    <motion.div
      initial={
        reduceMotion
          ? { opacity: 0 }
          : { opacity: 0, scale: 0.96, filter: "blur(3px)" }
      }
      animate={
        reduceMotion
          ? { opacity: 1 }
          : { opacity: 1, scale: 1, filter: "blur(0px)" }
      }
      exit={{ opacity: 0, scale: 0.98 }}
      transition={{ ...transition, duration: 0.3 }}
      className="h-full flex flex-col items-center justify-center bg-white rounded-[20px] border border-pns-text-primary/8 shadow-sm"
      aria-hidden="true"
    >
      <Image
        src="/images/logo.png"
        alt=""
        width={240}
        height={52}
        className="h-[44px] sm:h-[52px] lg:h-[58px] w-auto object-contain brightness-0"
        style={{ width: "auto" }}
      />
      <p className="mt-3 text-[12px] text-pns-text-muted text-center">
        Software built around how your business actually works.
      </p>
    </motion.div>
  );
}


