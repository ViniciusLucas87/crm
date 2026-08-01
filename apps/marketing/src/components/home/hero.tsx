import Image from "next/image";
import { Button } from "@/components/ui/button";
import { CheckCircle } from "lucide-react";

export function Hero() {
  const trustSignals = ["Founder-led", "Based in BC", "Fast delivery"];

  return (
    <section
      className="relative min-h-screen lg:min-h-[820px] overflow-hidden bg-[#051226]"
      id="home"
    >
      {/* ── Right side: Vancouver image (55% width) ── */}
      <div className="absolute inset-y-0 right-0 w-full lg:w-[55%]">
        <Image
          src="/images/hero-bg.png"
          alt=""
          fill
          priority
          className="object-cover lg:object-[65%_center]"
          sizes="(max-width: 1024px) 100vw, 55vw"
          style={{
            filter: "brightness(.82) contrast(.88) saturate(.82)",
          }}
        />
      </div>

      {/* ── Gradient overlay: solid navy left → fades into image right ── */}
      <div
        className="absolute inset-0"
        aria-hidden="true"
        style={{
          background:
            "linear-gradient(90deg, #051226 0%, #051226 38%, rgba(5,18,38,.92) 50%, rgba(5,18,38,.72) 65%, rgba(5,18,38,.35) 82%, rgba(5,18,38,.12) 100%)",
        }}
      />

      {/* ── Content: left column (45%) ── */}
      <div className="relative z-10 flex min-h-screen lg:min-h-[820px] items-center">
        <div className="w-full max-w-[1440px] pl-6 sm:pl-8 lg:pl-16 xl:pl-20 pr-6 sm:pr-8 lg:pr-12 xl:pr-16">
          <div className="max-w-[680px] pt-28 pb-16 lg:pt-0 lg:pb-0">
            {/* Trust signals , subtle */}
            <div className="flex flex-wrap items-center gap-x-6 gap-y-2 mb-10">
              {trustSignals.map((signal) => (
                <span
                  key={signal}
                  className="inline-flex items-center gap-2 text-xs font-medium uppercase tracking-widest text-white/50"
                >
                  <CheckCircle
                    className="w-3.5 h-3.5 text-emerald-400/80"
                    aria-hidden="true"
                  />
                  {signal}
                </span>
              ))}
            </div>

            {/* Headline */}
            <h1 className="text-[clamp(2.75rem,6vw,4.5rem)] font-bold leading-[1.05] tracking-[-0.02em] text-white">
              Find out where your business is losing time.
            </h1>

            {/* Body */}
            <p className="mt-8 text-[1.0625rem] leading-[1.7] text-white/65 max-w-[32rem]">
              We build custom software, workflow automation, and AI‑powered
              operational systems for businesses across British Columbia.
            </p>

            {/* CTAs */}
            <div className="mt-10 flex flex-col sm:flex-row items-start gap-3">
              <Button
                variant="primary"
                size="lg"
                href="/assessment"
                className="bg-white !text-[#051226] hover:bg-white/90 !text-[15px] !px-8 !py-3.5 !rounded-xl !font-semibold"
              >
                Take the 2-Minute Assessment
              </Button>
              <Button
                variant="ghost"
                size="lg"
                href="/#demo-systems"
                className="!text-white/70 hover:!text-white !text-[15px] !font-medium"
              >
                Explore Demo Systems &rarr;
              </Button>
            </div>

            {/* Value bullets */}
            <div className="mt-8 flex flex-wrap gap-x-6 gap-y-1.5">
              {[
                "Your Automation Score",
                "Estimated Time Savings",
                "Biggest Bottlenecks",
                "Personalized Recommendations",
              ].map((item) => (
                <span
                  key={item}
                  className="inline-flex items-center gap-1.5 text-[13px] text-white/45"
                >
                  <span className="w-1 h-1 rounded-full bg-white/30" />
                  {item}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
