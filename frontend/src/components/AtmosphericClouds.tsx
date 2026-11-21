import React from "react";

export function FloatingCloud({
  className = "",
  variant = "a",
  animation = "animate-cloud-drift-1",
}: {
  className?: string;
  variant?: "a" | "b" | "c" | "megamendung" | "mist" | "puff";
  animation?: string;
}) {
  if (variant === "mist") {
    // Dense billowing mountain fog & mist plume ("kabut tebal padepokan")
    return (
      <div className={`pointer-events-none select-none ${animation} ${className}`} aria-hidden="true">
        <svg
          viewBox="0 0 500 160"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="w-full h-auto filter drop-shadow-[0_16px_32px_rgba(234,88,12,0.12)]"
        >
          <defs>
            <linearGradient id="mistGradMain" x1="0%" y1="100%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#ffffff" stopOpacity="0.98" />
              <stop offset="40%" stopColor="#fffaf5" stopOpacity="0.94" />
              <stop offset="75%" stopColor="#ffedd5" stopOpacity="0.82" />
              <stop offset="100%" stopColor="#fed7aa" stopOpacity="0.5" />
            </linearGradient>
            <linearGradient id="mistGradSoft" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#ffffff" stopOpacity="1" />
              <stop offset="50%" stopColor="#fff7ed" stopOpacity="0.9" />
              <stop offset="100%" stopColor="#fed7aa" stopOpacity="0.6" />
            </linearGradient>
            <filter id="mistBlur" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="3" />
            </filter>
          </defs>
          {/* Base billow */}
          <path
            d="M20 120 C10 90 25 50 65 50 C80 20 120 10 160 20 C190 5 245 5 280 25 C315 15 365 30 380 65 C415 70 445 95 435 125 C415 145 35 150 20 120 Z"
            fill="url(#mistGradMain)"
            filter="url(#mistBlur)"
          />
          {/* Dense upper fog layer */}
          <path
            d="M45 110 C35 85 50 58 85 58 C100 32 135 22 170 32 C198 18 245 18 275 35 C305 28 348 42 360 72 C390 78 415 100 405 122 C385 138 60 135 45 110 Z"
            fill="url(#mistGradSoft)"
          />
          {/* Crest highlight puffs */}
          <ellipse cx="140" cy="55" rx="55" ry="30" fill="#ffffff" fillOpacity="0.9" />
          <ellipse cx="255" cy="50" rx="70" ry="35" fill="#ffffff" fillOpacity="0.95" />
          <ellipse cx="340" cy="75" rx="50" ry="28" fill="#ffffff" fillOpacity="0.85" />
        </svg>
      </div>
    );
  }

  if (variant === "puff") {
    // Dense, high-visibility cumulus silat cloud
    return (
      <div className={`pointer-events-none select-none ${animation} ${className}`} aria-hidden="true">
        <svg
          viewBox="0 0 360 140"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="w-full h-auto filter drop-shadow-[0_14px_28px_rgba(120,40,15,0.10)]"
        >
          <defs>
            <linearGradient id="puffGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#ffffff" stopOpacity="1" />
              <stop offset="50%" stopColor="#fffaf5" stopOpacity="0.95" />
              <stop offset="100%" stopColor="#ffedd5" stopOpacity="0.85" />
            </linearGradient>
          </defs>
          <path
            d="M30 100 C15 72 35 42 70 42 C82 15 125 5 160 18 C185 4 235 4 260 26 C295 18 335 36 340 68 C365 76 375 106 350 125 C320 140 48 135 30 100 Z"
            fill="url(#puffGrad)"
          />
          <circle cx="105" cy="60" r="38" fill="#ffffff" fillOpacity="0.9" />
          <circle cx="195" cy="50" r="48" fill="#ffffff" fillOpacity="0.95" />
          <circle cx="280" cy="65" r="38" fill="#ffffff" fillOpacity="0.88" />
        </svg>
      </div>
    );
  }

  if (variant === "megamendung") {
    // Stylized Megamendung / Nusantara tapered cloud plume (dense & visible)
    return (
      <div className={`pointer-events-none select-none ${animation} ${className}`} aria-hidden="true">
        <svg
          viewBox="0 0 380 140"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="w-full h-auto filter drop-shadow-[0_14px_28px_rgba(234,88,12,0.10)]"
        >
          <defs>
            <linearGradient id="megaGrad" x1="0%" y1="0%" x2="100%" y2="80%">
              <stop offset="0%" stopColor="#ffffff" stopOpacity="1" />
              <stop offset="45%" stopColor="#fffaf5" stopOpacity="0.95" />
              <stop offset="80%" stopColor="#ffedd5" stopOpacity="0.9" />
              <stop offset="100%" stopColor="#fed7aa" stopOpacity="0.7" />
            </linearGradient>
          </defs>
          {/* Tapering sharp decorative cloud tip */}
          <path
            d="M20 70 Q50 30 110 35 Q145 10 200 20 Q240 5 280 25 Q325 15 365 60 C380 90 355 125 315 125 Q275 130 230 120 Q180 135 125 120 Q70 125 35 105 Q15 95 20 70 Z"
            fill="url(#megaGrad)"
          />
          {/* Megamendung step contour strokes */}
          <path
            d="M60 70 Q95 45 140 48 Q175 30 220 38 Q255 25 290 42 Q325 35 350 70"
            stroke="#ffffff"
            strokeWidth="3.5"
            strokeLinecap="round"
            opacity="0.9"
          />
          <path
            d="M90 85 Q125 65 170 68 Q205 50 250 58 Q285 48 320 75"
            stroke="#ffedd5"
            strokeWidth="2.5"
            strokeLinecap="round"
            opacity="0.8"
          />
        </svg>
      </div>
    );
  }

  if (variant === "b") {
    // Broad horizontal billowing bank
    return (
      <div className={`pointer-events-none select-none ${animation} ${className}`} aria-hidden="true">
        <svg
          viewBox="0 0 520 130"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="w-full h-auto filter drop-shadow-[0_12px_24px_rgba(120,40,15,0.08)]"
        >
          <path
            d="M25 95 C10 65 30 35 65 35 C80 12 118 5 150 15 C180 2 225 4 255 20 C285 8 335 12 360 32 C390 18 435 24 455 50 C485 55 510 80 495 108 C475 128 35 125 25 95 Z"
            fill="#ffffff"
            fillOpacity="0.96"
          />
          <path
            d="M55 85 C45 65 60 42 85 42 C100 24 130 18 155 26 C180 15 215 16 240 28 C265 18 305 20 325 36 C350 26 385 30 400 50 C425 55 440 75 430 96 C415 112 65 110 55 85 Z"
            fill="#fff7ed"
            fillOpacity="0.9"
          />
        </svg>
      </div>
    );
  }

  // Default cloud variant A: Solid, crisp white with delicate ivory border
  return (
    <div className={`pointer-events-none select-none ${animation} ${className}`} aria-hidden="true">
      <svg
        viewBox="0 0 420 150"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="w-full h-auto filter drop-shadow-[0_16px_32px_rgba(234,88,12,0.12)]"
      >
        <path
          d="M35 105 C15 75 35 38 75 38 C90 12 135 2 175 16 C205 2 255 4 285 24 C320 12 370 24 385 62 C415 72 425 108 395 132 C360 148 45 142 35 105 Z"
          fill="#ffffff"
          fillOpacity="0.98"
        />
        <circle cx="120" cy="62" r="46" fill="#ffffff" fillOpacity="1" />
        <circle cx="225" cy="52" r="58" fill="#ffffff" fillOpacity="1" />
        <circle cx="320" cy="70" r="44" fill="#ffffff" fillOpacity="0.95" />
      </svg>
    </div>
  );
}

/* =========================================================================
   ATMOSPHERIC SKY TRANSITION (Awan, Angin Hembusan & Burung Melayang Nusantara)
   Ethereal artistic separator replacing cluttered text & badges
   ========================================================================= */
export function AtmosphericSkyTransition({
  className = "",
}: {
  className?: string;
}) {
  return (
    <div
      className={`relative w-full h-28 sm:h-36 overflow-hidden select-none pointer-events-none flex items-center justify-center ${className}`}
      aria-hidden="true"
    >
      {/* Ambient sky gradient blend */}
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-amber-50/30 to-transparent" />

      {/* Billowing Megamendung & Mist Clouds */}
      <div className="absolute -left-10 -top-4 w-64 sm:w-80 opacity-70">
        <FloatingCloud variant="megamendung" animation="animate-cloud-drift-1" />
      </div>
      <div className="absolute -right-10 -bottom-4 w-64 sm:w-80 opacity-70">
        <FloatingCloud variant="mist" animation="animate-cloud-drift-2" />
      </div>
      <div className="absolute left-1/3 top-1 w-44 sm:w-56 opacity-50 hidden sm:block">
        <FloatingCloud variant="puff" animation="animate-cloud-drift-3" />
      </div>

      {/* Stylized Wind Flow Streams */}
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="absolute left-1/4 top-1/3 w-60 h-10 animate-wind-flow-1">
          <svg viewBox="0 0 240 40" fill="none" className="w-full h-full stroke-orange-400/45">
            <path
              d="M0 20 Q60 5 120 20 T240 15"
              strokeWidth="2"
              strokeLinecap="round"
              strokeDasharray="16 8"
            />
          </svg>
        </div>

        <div className="absolute right-1/4 bottom-1/4 w-72 h-12 animate-wind-flow-2">
          <svg viewBox="0 0 300 45" fill="none" className="w-full h-full stroke-amber-500/35">
            <path
              d="M0 25 Q75 40 150 20 T300 25"
              strokeWidth="1.8"
              strokeLinecap="round"
              strokeDasharray="20 10"
            />
          </svg>
        </div>
      </div>

      {/* Soaring Silhouette Birds / Walet Melayang */}
      <div className="absolute inset-0 overflow-hidden">
        {/* Bird 1: Lead Soarer */}
        <div className="absolute top-1/4 animate-bird-glide-1">
          <div className="animate-wing-beat">
            <svg
              viewBox="0 0 60 28"
              fill="currentColor"
              className="w-7 h-4 sm:w-9 sm:h-5 text-amber-950/60 drop-shadow-xs"
            >
              <path d="M0 12 C12 6 22 2 28 8 C30 9 30 9 32 8 C38 2 48 6 60 12 C48 10 38 12 30 18 C22 12 12 10 0 12 Z" />
            </svg>
          </div>
        </div>

        {/* Bird 2: Companion Glider */}
        <div className="absolute top-1/3 animate-bird-glide-2">
          <div className="animate-wing-beat" style={{ animationDelay: "-0.9s" }}>
            <svg
              viewBox="0 0 60 28"
              fill="currentColor"
              className="w-5 h-3 sm:w-7 sm:h-4 text-orange-950/45 drop-shadow-xs"
            >
              <path d="M0 12 C12 6 22 2 28 8 C30 9 30 9 32 8 C38 2 48 6 60 12 C48 10 38 12 30 18 C22 12 12 10 0 12 Z" />
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
}
