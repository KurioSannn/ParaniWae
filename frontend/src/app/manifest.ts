import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "SILATARA", short_name: "SILATARA", lang: "id", start_url: "/", display: "standalone",
    description: "Platform belajar dan pelestarian pencak silat.", background_color: "#4a0d0d", theme_color: "#4a0d0d",
    icons: [{ src: "/icon.png", sizes: "512x512", type: "image/png" }, { src: "/apple-icon.png", sizes: "180x180", type: "image/png" }],
  };
}
