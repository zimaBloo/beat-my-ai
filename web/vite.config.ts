import { defineConfig } from "vite";
import { viteSingleFile } from "vite-plugin-singlefile";

// "single" mode packs the whole page into one HTML file that opens straight from disk, for previews.
export default defineConfig(({ mode }) => ({
  base: "./",
  plugins: mode === "single" ? [viteSingleFile()] : [],
  build: {
    outDir: mode === "single" ? "dist-single" : "dist",
    assetsInlineLimit: mode === "single" ? 100_000_000 : 4096,
  },
}));
