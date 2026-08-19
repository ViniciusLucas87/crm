"use client";

import { useEffect, useState } from "react";

export function BackgroundVideo() {
  const [enabled, setEnabled] = useState(false);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const media = window.matchMedia(
      "(min-width: 768px) and (prefers-reduced-motion: no-preference)",
    );
    const update = () => setEnabled(media.matches);

    update();
    media.addEventListener("change", update);
    return () => media.removeEventListener("change", update);
  }, []);

  if (!enabled) return null;

  return (
    <video
      className={`absolute inset-0 h-full w-full object-cover object-[22%_center] transition-opacity duration-500 ${
        ready ? "opacity-100" : "opacity-0"
      }`}
      autoPlay
      muted
      loop
      playsInline
      preload="auto"
      onLoadedData={() => setReady(true)}
      onCanPlay={() => setReady(true)}
      aria-hidden="true"
      tabIndex={-1}
    >
      <source src="/videos/homepage-background.mp4" type="video/mp4" />
    </video>
  );
}
