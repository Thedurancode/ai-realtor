/**
 * Shared font configuration for all Remotion compositions.
 *
 * Uses @remotion/google-fonts for professional typography:
 * - Headings: Playfair Display (elegant serif — perfect for real estate luxury feel)
 * - Body/UI: Inter (clean sans-serif — excellent readability on video)
 * - Accent: Montserrat (bold geometric sans — CTAs, badges, prices)
 */

// @ts-ignore — @remotion/google-fonts sub-path exports have type resolution issues with bundler moduleResolution
import { loadFont as loadPlayfairDisplay } from "@remotion/google-fonts/PlayfairDisplay";
// @ts-ignore
import { loadFont as loadInter } from "@remotion/google-fonts/Inter";
// @ts-ignore
import { loadFont as loadMontserrat } from "@remotion/google-fonts/Montserrat";

const playfair = loadPlayfairDisplay();
const inter = loadInter();
const montserrat = loadMontserrat();

export const FONTS = {
  heading: playfair.fontFamily as string,     // Playfair Display — elegant headings
  body: inter.fontFamily as string,           // Inter — clean body text
  accent: montserrat.fontFamily as string,    // Montserrat — CTAs, prices, badges
} as const;
