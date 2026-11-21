from functools import lru_cache

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=None, extra="ignore")

    app_env: str = "development"
    app_name: str = "SILATARA API"
    app_version: str = "0.1.0"

    postgres_user: str = "silatara"
    postgres_password: str = "change-me-dev-only"
    postgres_db: str = "silatara"
    postgres_host: str = "db"
    postgres_port: int = 5432

    # Daftar origin dipisah koma. Jangan pernah memakai "*" bersama credentials.
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    # Sesi & cookie (lihat docs/adr/0002-authentication.md)
    session_ttl_hours: int = 168
    session_idle_hours: int = 24
    cookie_secure: bool | None = None  # None -> aktif otomatis bila bukan development
    session_cookie_name: str = "silatara_session"
    csrf_cookie_name: str = "silatara_csrf"
    login_max_failures: int = 5
    login_lock_minutes: int = 15

    # Email (lihat docs/adr/0003-auth-hardening.md). Produksi WAJIB smtp; dev_sink hanya untuk development.
    mail_provider: str = "dev_sink"  # dev_sink | smtp | none
    mail_from: str = "SILATARA <no-reply@localhost>"
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_starttls: bool = True
    public_base_url: str = "http://localhost:3000"  # origin frontend untuk tautan di email
    verify_token_ttl_hours: int = 48
    reset_token_ttl_minutes: int = 30

    # Proxy tepercaya untuk membaca IP klien dari X-Forwarded-For.
    # X-Forwarded-For HANYA dipercaya bila peer langsung ada di CIDR ini, dan IP klien diambil
    # dari entri ke-`trusted_proxy_hops` dari KANAN (entri kiri dapat dipalsukan klien).
    trusted_proxy_cidrs: str = ""
    trusted_proxy_hops: int = 1

    # Rate limit (jumlah / detik jendela). Disimpan di PostgreSQL (aman untuk multi-worker).
    rate_limit_enabled: bool = True
    rl_login_ip: tuple[int, int] = (30, 900)
    rl_register_ip: tuple[int, int] = (10, 3600)
    rl_reset_ip: tuple[int, int] = (10, 3600)
    rl_reset_email: tuple[int, int] = (3, 3600)
    rl_verify_ip: tuple[int, int] = (20, 3600)
    rl_resend_email: tuple[int, int] = (3, 3600)
    rl_admin_user: tuple[int, int] = (60, 60)

    # Penyimpanan file privat (media referensi + dokumen persetujuan mitra). TIDAK pernah disajikan sebagai file statis.
    media_dir: str = "/data/media"
    media_max_video_mb: int = 100
    media_max_image_mb: int = 10
    partner_doc_max_mb: int = 10

    # Pemindai malware (ClamAV via clamd). `disabled` = TIDAK ada pemindaian: berkas ditandai `not_scanned`, tidak pernah publik.
    scan_provider: str = "disabled"  # disabled | clamav
    scan_host: str = "clamav"
    scan_port: int = 3310
    scan_timeout_s: int = 60

    # Koneksi DB & observabilitas load test
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_timeout_s: int = 30
    debug_query_stats: bool = False

    # Outbox notifikasi (lihat docs/PILOT_OPERATIONS_RUNBOOK.md)
    outbox_batch_size: int = 20
    outbox_lease_seconds: int = 120
    outbox_max_attempts: int = 6
    outbox_backoff_base_s: int = 30
    outbox_backoff_cap_s: int = 3600
    outbox_undeliverable_max_hours: int = 72
    outbox_purge_sent_days: int = 30
    outbox_purge_dead_days: int = 180
    smtp_timeout_s: int = 15
    retention_auto_enabled: bool = True
    retention_interval_hours: int = 24
    media_purge_enabled: bool = True

    # Pilot & retensi
    pilot_min_respondents: int = 5
    pilot_retention_days: int = 365
    pilot_policy_version: str = "2026-11"
    worker_interval_s: int = 60

    # Hanya dibaca untuk guard produksi (nilai tidak dipakai langsung di sini)
    demo_user_password: str | None = None
    seed_demo_data: bool = False
    # Login demo sekali klik (tanpa kata sandi) untuk akun [DEMO] yang di-seed. HANYA pengembangan/presentasi lokal;
    # selalu mati di produksi (lihat demo_login_active + production_problems).
    demo_login_enabled: bool = False
    # Basis pengetahuan publik dari berkas content/ & research/ (ADR-0008: public-first). Matikan hanya bila berkas
    # tidak tersedia di lingkungan tersebut.
    research_preview_enabled: bool = True
    research_repo_dir: str = "/repo"

    # Data DEMO hanya boleh tampil di API saat true (default: hanya di development).
    expose_demo_data: bool = Field(default=True)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def use_secure_cookies(self) -> bool:
        if self.cookie_secure is not None:
            return self.cookie_secure
        return self.app_env != "development"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def mail_configured(self) -> bool:
        if self.mail_provider == "dev_sink":
            return self.app_env == "development"  # sink dev TIDAK boleh aktif di luar development
        if self.mail_provider == "smtp":
            return bool(self.smtp_host and self.mail_from)
        return False

    def production_problems(self) -> list[str]:
        """Pelanggaran konfigurasi yang TIDAK boleh ada di produksi (dievaluasi tanpa memandang APP_ENV; dipakai doctor)."""
        problems = []
        if not self.use_secure_cookies:
            problems.append("COOKIE_SECURE harus true di produksi")
        if self.expose_demo_data:
            problems.append("EXPOSE_DEMO_DATA harus false di produksi")
        if self.postgres_password == "silatara_dev_password" or len(self.postgres_password) < 16:
            problems.append("POSTGRES_PASSWORD default/lemah tidak boleh dipakai di produksi")
        if self.mail_provider == "dev_sink":
            problems.append("MAIL_PROVIDER=dev_sink tidak boleh dipakai di produksi")
        if self.demo_user_password:
            problems.append("DEMO_USER_PASSWORD tidak boleh diset di produksi (kredensial demo)")
        if self.seed_demo_data:
            problems.append("SEED_DEMO_DATA tidak boleh true di produksi")
        if self.demo_login_enabled:
            problems.append("DEMO_LOGIN_ENABLED tidak boleh true di produksi (login tanpa kata sandi)")
        if self.scan_provider != "clamav":
            problems.append("SCAN_PROVIDER harus clamav di produksi (berkas unggahan wajib dipindai)")
        return sorted(set(problems), key=problems.index)

    @property
    def demo_login_active(self) -> bool:
        """Login demo hanya aktif bila diizinkan eksplisit dan BUKAN produksi. Tidak bergantung pada EXPOSE_DEMO_DATA:
        akun uji boleh dipakai di dev walau konten contoh disembunyikan dari halaman publik (ADR-0008)."""
        return self.demo_login_enabled and not self.is_production

    def validate_runtime(self) -> None:
        """Gagal cepat (fail closed) untuk konfigurasi tidak aman di produksi."""
        if not self.is_production:
            return
        problems = self.production_problems()
        if problems:
            raise RuntimeError("Konfigurasi produksi tidak aman: " + "; ".join(problems))

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip() and o.strip() != "*"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
