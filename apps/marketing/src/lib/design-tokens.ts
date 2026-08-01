export const tokens = {
  colors: {
    // Backgrounds
    bg: {
      homepage: "#F7FAFC",
      white: "#FFFFFF",
      darkHero: "#071B33",
      darkHeroSecondary: "#0A223D",
      darkFooter: "#061426",
      softBlue: "#EAF3FA",
    },
    // Text
    text: {
      primary: "#0B1526",
      primaryAlt: "#10243C",
      muted: "rgb(82, 99, 114)",
      lightOnDark: "rgb(198, 213, 227)",
      softWhite: "rgb(238, 247, 255)",
      footerMuted: "rgb(155, 175, 193)",
    },
    // Accent
    accent: {
      lightBlue: "#DCE6F7",
    },
    // Assessment
    assessment: {
      errorText: "#9A1D1D",
      inputBg: "#F5F5F5",
      inputBorder: "#DDDDDD",
      panel: "#EAF0F7",
    },
  },

  typography: {
    fonts: {
      heading: ["General Sans", "sans-serif"],
      body: ["General Sans", "sans-serif"],
      assessment: ["Inter", "sans-serif"],
    },
    sizes: {
      heroHeading: "clamp(2.25rem, 5vw, 3.75rem)",
      heroBody: "1.1875rem", // 19px
      sectionHeading: "clamp(1.75rem, 4vw, 2.5rem)",
      cardHeading: "1.125rem",
      body: "1rem",
      bodySmall: "0.875rem",
      nav: "0.875rem",
      assessmentHeading: "2rem",
      assessmentBody: "0.9375rem",
    },
    weights: {
      heroHeading: "700",
      heroBody: "400",
      nav: "500",
      cta: "700",
      assessmentHeading: "600",
      assessmentBody: "500",
    },
  },

  layout: {
    breakpoints: {
      desktop: 1200,
      tablet: 810,
      phone: 390,
    },
    maxWidths: {
      content: "1440px",
      articleList: "920px",
      articleBody: "720px",
      assessment: "960px",
    },
    spacing: {
      desktopSection: "5.5rem 0", // ~88-96px
      phoneSection: "4.5rem 0", // ~72px
      desktopPadding: "2rem", // 32px
      tabletPadding: "1.5rem", // 24px
      phonePadding: "1.125rem", // 18px
    },
    assessment: {
      borderRadius: "16px",
      inputRadius: "10px",
      inputMinHeight: "44px",
      gridMinColumn: "280px",
    },
  },

  header: {
    blur: "12px",
    zIndex: 5,
  },

  motion: {
    pageTransition: "spring-physics 500 60 1 0s",
    standaloneTransition: "spring-duration 0.4s 0.2 0s",
  },
} as const;

export type Tokens = typeof tokens;
