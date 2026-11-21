import Image from "next/image";
import Link from "next/link";
import { ArrowRight, Camera, ChevronDown, Compass, MapPinned, ShieldCheck } from "lucide-react";
import { AtmosphericSkyTransition, FloatingCloud } from "@/components/AtmosphericClouds";
import { MovementCard } from "@/components/knowledge/Bits";
import { SilatPatternKawung, SilatPatternTumpal } from "@/components/SilatMotifs";
import { apiGet } from "@/lib/api";
import type { CharacterManifest } from "@/lib/character";
import type { DirectoryStats } from "@/lib/directory";
import type { MovementItem, ResearchSummary } from "@/lib/research";

const GRAD = "rounded-full bg-gradient-to-r from-[#4a0d0d] via-[#7c1d1d] to-[#c2410c] hover:from-[#3a0808] hover:to-[#9a3412] font-semibold text-white shadow-md shadow-orange-950/20 transition-all hover:-translate-y-0.5 hover:shadow-lg";
const GHOST = "rounded-full border border-slate-300 bg-white font-semibold text-slate-800 shadow-xs transition-all hover:-translate-y-0.5 hover:border-slate-400 hover:bg-slate-50";

const faq = [
  ["Bagaimana pelacakan gerak bekerja tanpa sensor khusus?", "Model deteksi tubuh (MediaPipe) berjalan langsung di peramban Anda dan membaca 33 titik tubuh serta titik-titik jari dari kamera biasa. Anda tidak memerlukan sensor, pakaian, atau perangkat tambahan."],
  ["Apakah video saya direkam atau diunggah?", "Tidak. Gambar kamera diproses di perangkat Anda dan tidak dikirim ke server. Setelah skor dihitung, data gerak dihapus dari memori. Hanya angka ringkasan yang bisa Anda simpan bila Anda masuk dan menyetujuinya."],
  ["Apakah skor itu penilaian resmi perguruan?", "Bukan. Skor menunjukkan seberapa sesuai gerakan Anda dengan panduan gerak di SILATARA, lengkap dengan alasan per kriteria. Teknik yang sebenarnya perlu diperiksa pelatih langsung."],
  ["Apakah saya harus masuk untuk belajar?", "Tidak. Pustaka gerakan, kursus, warisan, dan peta terbuka untuk semua. Masuk hanya diperlukan untuk menyimpan progres dan riwayat skor latihan."],
  ["Seberapa lengkap peta tempat latihannya?", "Peta ini masih bertumbuh dan belum mencakup semua perguruan. Tempat yang alamatnya belum diketahui ditampilkan pada tingkat kabupaten/kota, bukan di titik tebakan. Anda dapat mengirim tempat baru atau koreksi lewat formulir di halaman peta."],
];

export default async function Home() {
  const [sum, mv, ch, pr, dir] = await Promise.all([
    apiGet<ResearchSummary>("/research/summary"),
    apiGet<{ items: MovementItem[] }>("/research/movements"),
    apiGet<CharacterManifest>("/research/character"),
    apiGet<{ items: { movement_id: string; status: string }[] }>("/research/assessment/protocols"),
    apiGet<DirectoryStats>("/directory/stats"),
  ]);
  const featured = mv.ok ? ["kuda-kuda-depan", "kuda-kuda-tengah", "langkah-angkatan", "sikap-pasang-1"].map((s) => mv.data.items.find((m) => m.slug === s)).filter((m): m is MovementItem => !!m) : [];
  const practice = pr.ok ? pr.data.items.find((p) => p.status === "active") : undefined;
  const practiceHref = practice ? `/library/${practice.movement_id.split(".").pop()}/latihan` : "/library";
  const stats = [
    sum.ok && [String(sum.data.provinces.total), "provinsi ditelusuri"],
    sum.ok && [String(sum.data.movements.total), "gerakan diuraikan fase demi fase"],
    ch.ok && [String(ch.data.clips.filter((c) => c.checks_passed).length), "gerakan dengan peraga 3D"],
    dir.ok && [String(dir.data.total_places), "lokasi latihan di peta"],
  ].filter((x): x is string[] => Array.isArray(x));

  return (
    <div data-fullbleed className="space-y-24 pb-16 sm:space-y-32">
      {/* ================= HERO ================= */}
      <section className="relative pt-4 sm:pt-8">
        <div aria-hidden className="pointer-events-none absolute -top-16 left-1/2 -z-10 h-[560px] w-full max-w-5xl -translate-x-1/2 rounded-full bg-gradient-to-tr from-orange-500/15 via-red-600/10 to-amber-700/10 blur-3xl" />
        <SilatPatternKawung opacity={0.035} className="text-[#381a0e]" />
        <div className="relative flex min-h-[76vh] w-full items-center justify-center overflow-hidden px-4 sm:min-h-[82vh] sm:px-6">
          <div className="pointer-events-none absolute -left-14 top-1/2 z-0 hidden w-64 -translate-y-1/2 select-none lg:block xl:-left-10 xl:w-80 2xl:left-0 2xl:w-96">
            <div className="animate-hero-warrior-left h-auto w-full">
              <Image src="/landing/silat-duel-left.png" alt="" width={516} height={670} priority className="h-auto w-full object-contain drop-shadow-[0_25px_35px_rgba(234,88,12,0.22)]" />
            </div>
          </div>
          <div className="relative z-10 mx-auto flex max-w-4xl flex-col items-center justify-center space-y-7 px-4 text-center">
            <h1 className="relative flex select-none items-center justify-center py-2">
              <span className="sr-only">SILATARA — Warisan Gerak, Generasi Bergerak</span>
              <Image src="/brand/silatara-logo-full.png" alt="" width={934} height={245} priority
                className="h-auto w-[280px] object-contain drop-shadow-[0_12px_28px_rgba(90,20,20,0.18)] sm:w-[420px] md:w-[560px] lg:w-[680px] xl:w-[740px]" />
            </h1>
            <p className="mx-auto max-w-3xl text-balance text-base font-medium leading-relaxed text-slate-700 sm:text-lg md:text-xl">
              Kenali kekayaan pencak silat Nusantara, pelajari geraknya dari peraga 3D, dan berlatih di depan kamera dengan skor yang bisa dijelaskan. Semuanya terbuka untuk dibaca siapa saja.
            </p>
            <div className="relative z-30 flex flex-wrap items-center justify-center gap-4 pt-2">
              <Link href="/academy" className={`${GRAD} px-9 py-4 text-sm sm:text-base`}>Mulai Belajar Sekarang</Link>
              <Link href={practiceHref} className={`${GHOST} px-8 py-4 text-sm sm:text-base`}>Coba Latihan Kamera</Link>
            </div>
          </div>
          <div className="pointer-events-none absolute -right-14 top-1/2 z-0 hidden w-64 -translate-y-1/2 select-none lg:block xl:-right-10 xl:w-80 2xl:right-0 2xl:w-[26rem]">
            <div className="animate-hero-warrior-right h-auto w-full">
              <Image src="/landing/silat-duel-right.png" alt="" width={616} height={525} priority className="h-auto w-full object-contain drop-shadow-[0_25px_35px_rgba(234,88,12,0.22)]" />
            </div>
          </div>
        </div>

        <div className="pointer-events-none relative z-10 mx-auto mb-6 mt-4 w-full max-w-6xl select-none overflow-visible sm:mt-8">
          <div aria-hidden className="absolute left-1/2 top-6 h-36 w-full -translate-x-1/2 bg-gradient-to-b from-transparent via-orange-100/30 to-amber-50/15 blur-2xl" />
          <div className="absolute -left-20 top-2 w-80 opacity-95 sm:w-[28rem] md:w-[32rem]"><FloatingCloud variant="mist" animation="animate-cloud-drift-1" /></div>
          <div className="absolute -right-20 top-2 w-80 opacity-95 sm:w-[28rem] md:w-[32rem]"><FloatingCloud variant="puff" animation="animate-cloud-drift-3" /></div>
          <div className="absolute left-1/2 top-10 w-[34rem] -translate-x-1/2 opacity-75 sm:w-[42rem]"><FloatingCloud variant="b" animation="animate-cloud-drift-2" /></div>
        </div>

        <div className="relative mx-auto mt-8 flex max-w-5xl flex-col items-center justify-center overflow-visible rounded-[2.5rem] border border-orange-100/90 bg-gradient-to-b from-[#fff6ee] via-[#fffbf7] to-[#f8fafc] px-4 pb-16 pt-8 shadow-sm sm:mt-12 sm:rounded-[3rem] sm:pb-24">
          <SilatPatternTumpal opacity={0.035} className="rounded-[2.5rem] text-[#4a120b] sm:rounded-[3rem]" />
          <div aria-hidden className="pointer-events-none absolute inset-0 rounded-[2.5rem] opacity-[0.06] [background-image:radial-gradient(#381a0e_1px,transparent_1px)] [background-size:24px_24px] sm:rounded-[3rem]" />
          <div aria-hidden className="pointer-events-none absolute -right-20 -top-20 h-96 w-96 rounded-full bg-orange-400/20 blur-3xl" />
          <div aria-hidden className="pointer-events-none absolute -bottom-20 -left-20 h-96 w-96 rounded-full bg-red-500/10 blur-3xl" />
          <div className="pointer-events-none absolute inset-0 z-0 select-none overflow-hidden rounded-[2.5rem] sm:rounded-[3rem]">
            <div className="absolute -left-14 -top-6 w-72 opacity-90 sm:w-96 md:w-[28rem]"><FloatingCloud variant="puff" animation="animate-cloud-drift-1" /></div>
            <div className="absolute left-1/2 top-4 w-80 -translate-x-1/2 opacity-85 sm:w-[28rem] md:w-[34rem]"><FloatingCloud variant="mist" animation="animate-cloud-drift-2" /></div>
            <div className="absolute -right-14 -top-10 w-72 opacity-90 sm:w-96 md:w-[28rem]"><FloatingCloud variant="megamendung" animation="animate-cloud-drift-3" /></div>
          </div>
          <div className="relative z-10 -mb-12 flex w-full max-w-5xl translate-y-12 items-center justify-center sm:-mb-16 sm:translate-y-20 md:-mb-20 md:translate-y-24">
            <Image src="/landing/silat-masters-perguruan-transparent.png" alt="Ragam sikap dan gerak pendekar pencak silat" width={1376} height={768} priority
              className="h-auto w-full scale-105 select-none object-contain drop-shadow-[0_30px_45px_rgba(74,18,11,0.28)] transition-transform duration-700 hover:scale-[1.12] sm:scale-110" />
          </div>
        </div>
      </section>

      <div className="mx-auto max-w-[1200px] space-y-24 px-5 sm:space-y-32">
        <div className="py-2 sm:py-6"><AtmosphericSkyTransition /></div>

        {/* ================= ANGKA NYATA ================= */}
        {stats.length > 0 && (
          <section aria-label="Cakupan saat ini">
            <dl className="grid grid-cols-2 gap-4 md:grid-cols-4">
              {stats.map(([n, l]) => (
                <div key={l} className="rounded-3xl border border-slate-200/80 bg-white p-6 text-center shadow-xs">
                  <dd className="text-4xl font-extrabold tracking-tight text-[#6d1b11]">{n}</dd>
                  <dt className="mt-1 text-sm text-slate-600">{l}</dt>
                </div>
              ))}
            </dl>
          </section>
        )}

        {/* ================= BENTO ================= */}
        <section className="space-y-10">
          <div className="mx-auto max-w-2xl space-y-3 text-center">
            <h2 className="text-balance text-3xl font-extrabold tracking-tight text-slate-900 sm:text-4xl">Semua yang Anda Butuhkan untuk Mengenal dan Belajar Silat</h2>
            <p className="text-balance text-sm leading-relaxed text-slate-600 sm:text-base">Dari memahami tradisinya, melihat gerakan diperagakan, sampai mencoba sendiri di depan kamera dan menemukan tempat latihan terdekat.</p>
          </div>
          <div className="grid items-stretch gap-6 md:grid-cols-3">
            <Link href="/library" className="card-interactive group flex flex-col justify-between rounded-3xl border border-slate-200/80 bg-white p-8 shadow-xs">
              <div className="space-y-4">
                <span className="text-xs font-bold uppercase tracking-wider text-orange-700">Pustaka Gerakan</span>
                <h3 className="text-balance text-xl font-bold text-slate-900">Peraga 3D, fase demi fase</h3>
                <p className="text-balance text-sm leading-relaxed text-slate-600">Setiap gerakan diperagakan karakter 3D yang bisa dijeda, diperlambat, dan dilihat dari depan, samping, atau diputar 360°, lengkap dengan uraian tiap fasenya.</p>
              </div>
              <div className="mt-8 border-t border-slate-100 pt-4 text-xs font-semibold text-orange-700">Buka Pustaka Gerakan →</div>
            </Link>
            <Link href={practiceHref} className="card-interactive group relative flex flex-col justify-between rounded-3xl border border-orange-500/30 bg-gradient-to-br from-[#2a0606] via-[#48140c] to-[#1f0505] p-8 text-white shadow-xl ring-1 ring-orange-400/20">
              <div aria-hidden className="pointer-events-none absolute inset-0 opacity-[0.06] [background-image:radial-gradient(#ffffff_1px,transparent_1px)] [background-size:20px_20px]" />
              <div className="relative z-10 space-y-4">
                <span className="text-xs font-bold uppercase tracking-wider text-amber-400">Latihan Kamera</span>
                <h3 className="text-balance text-xl font-bold">Skor 0–100 yang bisa dijelaskan</h3>
                <p className="text-balance text-sm leading-relaxed text-slate-200">Kamera membaca tubuh dan jari Anda di perangkat sendiri, membandingkannya dengan panduan gerak, lalu menampilkan skor per kriteria beserta saran perbaikan. Video tidak dikirim ke mana pun.</p>
              </div>
              <div className="relative z-10 mt-8 border-t border-white/10 pt-4 text-xs font-bold text-amber-300">Coba Latihan Sekarang →</div>
            </Link>
            <Link href="/community" className="card-interactive group flex flex-col justify-between rounded-3xl border border-slate-200/80 bg-white p-8 shadow-xs">
              <div className="space-y-4">
                <span className="text-xs font-bold uppercase tracking-wider text-orange-700">Peta Perguruan</span>
                <h3 className="text-balance text-xl font-bold text-slate-900">Temukan tempat latihan</h3>
                <p className="text-balance text-sm leading-relaxed text-slate-600">Cari perguruan, padepokan, dan pusat latihan menurut provinsi, kabupaten/kota, atau lokasi terdekat Anda. Peta bertumbuh seiring kiriman dan koreksi dari pengguna.</p>
              </div>
              <div className="mt-8 border-t border-slate-100 pt-4 text-xs font-semibold text-orange-700">Buka Peta →</div>
            </Link>
          </div>
        </section>

        {/* ================= BANNER GELAP ================= */}
        <section className="relative overflow-hidden rounded-[2.5rem] border border-orange-900/40 bg-gradient-to-br from-[#240606] via-[#3d120a] to-[#1a0404] p-8 text-white shadow-2xl sm:p-14">
          <div aria-hidden className="pointer-events-none absolute inset-0 opacity-[0.05] [background-image:radial-gradient(#ea580c_1px,transparent_1px)] [background-size:24px_24px]" />
          <div aria-hidden className="pointer-events-none absolute -right-24 -top-24 h-96 w-96 rounded-full bg-gradient-to-br from-orange-500/20 to-red-600/10 blur-3xl" />
          <div className="relative z-10 space-y-10">
            <div className="mx-auto max-w-2xl space-y-3 text-center">
              <h2 className="text-balance text-3xl font-extrabold tracking-tight sm:text-4xl">Teknologi yang Menghormati Keragaman Tradisi</h2>
              <p className="text-balance text-sm leading-relaxed text-slate-300">Pencak silat berbeda di tiap daerah dan perguruan. Kami tidak menyeragamkannya menjadi satu standar.</p>
            </div>
            <div className="grid gap-6 md:grid-cols-3">
              {[
                ["01 / DI PERANGKAT", "Privasi sejak awal", "Kamera hanya menyala setelah Anda setuju, dapat dihentikan kapan saja, dan gambar tidak pernah meninggalkan perangkat Anda."],
                ["02 / TERUKUR", "Skor yang transparan", "Setiap skor berasal dari sudut dan posisi tubuh yang benar-benar terukur. Bila tubuh tidak terlihat jelas, kami tidak memberi skor palsu."],
                ["03 / TERBUKA", "Untuk semua orang", "Materi umum dapat dibaca tanpa mendaftar. Latihan kamera ditujukan untuk gerak solo tingkat pemula yang aman dilakukan sendiri."],
              ].map(([k, t, d]) => (
                <div key={k} className="card-interactive space-y-3 rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-md transition-colors hover:bg-white/10">
                  <span className="font-mono text-xs font-bold text-amber-400">{k}</span>
                  <h3 className="text-balance text-lg font-bold">{t}</h3>
                  <p className="text-balance text-xs leading-relaxed text-slate-300">{d}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ================= GERAKAN UNGGULAN ================= */}
        {featured.length > 0 && (
          <section aria-labelledby="gerakan-h" className="space-y-8">
            <div className="flex flex-wrap items-end justify-between gap-3">
              <div>
                <h2 id="gerakan-h" className="text-3xl font-extrabold tracking-tight text-slate-900 sm:text-4xl">Mulai dari Gerakan Dasar</h2>
                <p className="mt-2 text-sm text-slate-600 sm:text-base">Sikap dan kuda-kuda adalah fondasi hampir semua gerak pencak silat.</p>
              </div>
              <Link href="/library" className="inline-flex items-center gap-1 text-sm font-semibold text-orange-700 hover:text-red-900">Lihat semua gerakan <ArrowRight aria-hidden className="h-4 w-4" /></Link>
            </div>
            <ul className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">{featured.map((m) => <li key={m.slug} className="rounded-3xl border border-slate-200/80 bg-white p-4 shadow-xs"><MovementCard m={m} /></li>)}</ul>
          </section>
        )}

        {/* ================= JALUR BELAJAR ================= */}
        <section aria-labelledby="jalur-h" className="space-y-10">
          <div className="mx-auto max-w-2xl space-y-3 text-center">
            <h2 id="jalur-h" className="text-balance text-3xl font-extrabold tracking-tight text-slate-900 sm:text-4xl">Jalur Belajar yang Sederhana</h2>
            <p className="text-balance text-sm text-slate-600 sm:text-base">Tidak perlu mendaftar untuk memulai. Ikuti urutannya, atau lompat ke bagian yang Anda butuhkan.</p>
          </div>
          <ol className="grid gap-6 md:grid-cols-4">
            {[
              [Compass, "Kenali tradisinya", "Telusuri ragam pencak silat dari 38 provinsi.", "/heritage", "Jelajahi Warisan"],
              [ShieldCheck, "Pelajari gerakannya", "Amati peraga 3D dan baca uraian tiap fase.", "/library", "Buka Pustaka"],
              [Camera, "Berlatih di depan kamera", "Dapatkan skor dan saran perbaikan secara pribadi.", practiceHref, "Coba Latihan"],
              [MapPinned, "Temukan tempat latihan", "Lanjutkan bersama pelatih di perguruan terdekat.", "/community", "Buka Peta"],
            ].map(([Icon, t, d, href, cta], i) => {
              const I = Icon as typeof Compass;
              return (
                <li key={t as string} className="card-interactive flex flex-col rounded-3xl border border-slate-200/80 bg-white p-6 shadow-xs">
                  <span className="mb-4 inline-flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br from-[#4a0d0d] to-[#c2410c] text-white"><I aria-hidden className="h-5 w-5" /></span>
                  <p className="text-xs font-bold uppercase tracking-wider text-orange-700">Langkah {i + 1}</p>
                  <h3 className="mt-1 text-lg font-bold text-slate-900">{t as string}</h3>
                  <p className="mt-2 flex-1 text-sm leading-relaxed text-slate-600">{d as string}</p>
                  <Link href={href as string} className="mt-5 text-sm font-semibold text-orange-700 hover:text-red-900">{cta as string} →</Link>
                </li>
              );
            })}
          </ol>
        </section>

        {/* ================= FAQ ================= */}
        <section id="faq" aria-labelledby="faq-h" className="grid gap-10 lg:grid-cols-[1fr_1.6fr]">
          <div className="space-y-4">
            <h2 id="faq-h" className="text-balance text-3xl font-extrabold tracking-tight text-slate-900 sm:text-4xl">Pertanyaan yang Sering Diajukan</h2>
            <p className="text-sm leading-relaxed text-slate-600">Tentang cara kerja pelacakan gerak, privasi kamera, dan peta tempat latihan.</p>
          </div>
          <div className="space-y-3">
            {faq.map(([q, a]) => (
              <details key={q} className="group rounded-2xl border border-slate-200/80 bg-white p-5 shadow-xs open:shadow-sm">
                <summary className="flex cursor-pointer list-none items-center justify-between gap-4 font-semibold text-slate-900 [&::-webkit-details-marker]:hidden">
                  {q}<ChevronDown aria-hidden className="h-5 w-5 shrink-0 text-orange-700 transition-transform group-open:rotate-180" />
                </summary>
                <p className="mt-3 text-sm leading-relaxed text-slate-600">{a}</p>
              </details>
            ))}
          </div>
        </section>

        {/* ================= CTA PENUTUP ================= */}
        <section className="relative overflow-hidden rounded-[2.5rem] border border-orange-100 bg-gradient-to-b from-[#fff6ee] to-white px-6 py-16 text-center sm:px-12">
          <div className="pointer-events-none absolute -bottom-2 left-0 hidden w-48 select-none md:block lg:w-64"><Image src="/landing/silat-cta-left.png" alt="" width={400} height={400} className="h-auto w-full object-contain" /></div>
          <div className="pointer-events-none absolute -bottom-2 right-0 hidden w-48 select-none md:block lg:w-64"><Image src="/landing/silat-cta-right.png" alt="" width={400} height={400} className="h-auto w-full object-contain" /></div>
          <div className="relative z-10 mx-auto max-w-2xl space-y-5">
            <h2 className="text-balance text-3xl font-extrabold tracking-tight text-slate-900 sm:text-4xl">Siap Melangkah ke Gerakan Pertama?</h2>
            <p className="text-balance text-slate-600">Mulai dari kuda-kuda, lihat peragaannya, lalu coba sendiri.</p>
            <div className="flex flex-wrap items-center justify-center gap-4 pt-2">
              <Link href="/library" className={`${GRAD} px-8 py-3.5 text-sm`}>Buka Pustaka Gerakan</Link>
              <Link href="/community" className={`${GHOST} px-8 py-3.5 text-sm`}>Temukan Tempat Latihan</Link>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
