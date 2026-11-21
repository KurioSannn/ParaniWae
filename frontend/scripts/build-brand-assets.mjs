// Menurunkan aset brand dari maskot ASLI (brand-source/silatara-mascot.png = salinan "Faceted Pencak Silat Warrior.png" di root).
// Tidak menggambar ulang karakter: hanya (1) menghapus latar hitam menjadi alpha, (2) memotong persegi, (3) mengubah ukuran.
// Jalankan: docker compose exec -T frontend node scripts/build-brand-assets.mjs
import sharp from "sharp";
import { writeFileSync } from "node:fs";

const SRC = "brand-source/silatara-mascot.png";
const { data, info } = await sharp(SRC).ensureAlpha().raw().toBuffer({ resolveWithObject: true });
const { width: W, height: H } = info;
// Matte hitam -> alpha lembut (tepi anti-alias tetap halus), warna di-unpremultiply agar tidak ada halo gelap.
const LO = 12, HI = 46;
for (let i = 0; i < data.length; i += 4) {
  const m = Math.max(data[i], data[i + 1], data[i + 2]);
  const a = Math.min(1, Math.max(0, (m - LO) / (HI - LO)));
  data[i + 3] = Math.round(a * 255);
  if (a > 0 && a < 1) for (let k = 0; k < 3; k++) data[i + k] = Math.min(255, Math.round(data[i + k] / a));
}
const full = sharp(data, { raw: { width: W, height: H, channels: 4 } });
await full.clone().png({ compressionLevel: 9 }).toFile("public/brand/silatara-mascot.png");

// Ikon persegi: kepala berikat kepala + lengan terangkat (bagian paling mudah dikenali), tanpa mengubah karakter.
const crop = { left: 560, top: 80, width: 500, height: 500 };
const markBuf = await full.clone().extract(crop).png().toBuffer();
await sharp(markBuf).resize(512, 512).png({ compressionLevel: 9 }).toFile("public/brand/silatara-mark.png");
// pad kecil agar tidak menyentuh tepi pada ukuran favicon
await sharp(markBuf).resize(460, 460).extend({ top: 26, bottom: 26, left: 26, right: 26, background: { r: 0, g: 0, b: 0, alpha: 0 } }).png().toFile("src/app/icon.png");
// Apple touch icon: iOS tidak mendukung transparansi -> latar gelap warna brand.
const BG = { r: 15, g: 21, b: 18, alpha: 1 };
const apple = await sharp(markBuf).resize(150, 150).png().toBuffer();
await sharp({ create: { width: 180, height: 180, channels: 4, background: BG } }).composite([{ input: apple, gravity: "centre" }]).png().toFile("src/app/apple-icon.png");
// favicon.ico (PNG tertanam 16/32/48)
const sizes = [16, 32, 48];
const pngs = await Promise.all(sizes.map((s) => sharp(markBuf).resize(s, s).png().toBuffer()));
const head = Buffer.alloc(6); head.writeUInt16LE(1, 2); head.writeUInt16LE(sizes.length, 4);
let offset = 6 + 16 * sizes.length; const dirs = [];
sizes.forEach((s, i) => { const d = Buffer.alloc(16); d[0] = s; d[1] = s; d.writeUInt16LE(1, 4); d.writeUInt16LE(32, 6); d.writeUInt32LE(pngs[i].length, 8); d.writeUInt32LE(offset, 12); offset += pngs[i].length; dirs.push(d); });
writeFileSync("src/app/favicon.ico", Buffer.concat([head, ...dirs, ...pngs]));
// Detail ornamen (kain/ikat pinggang) sebagai tekstur pendukung — potongan dari aset asli.
await full.clone().extract({ left: 470, top: 590, width: 420, height: 380 }).resize(630, 570).png().toFile("public/brand/silatara-ornament.png");
console.log("OK", W, H);
