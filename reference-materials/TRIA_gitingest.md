# Repository digest: budayago (TRIA)

## Directory structure

```
budayago/
└── .env.example
└── .gitignore
└── README.md
└── SETUP.md
└── manage.py
└── requirements.txt
└── about/
    └── __init__.py
    └── admin.py
    └── apps.py
    └── models.py
    └── tests.py
    └── urls.py
    └── views.py
    └── migrations/
        └── __init__.py
    └── templates/
        └── a.html
        └── about.html
└── articles/
    └── __init__.py
    └── admin.py
    └── apps.py
    └── models.py
    └── tests.py
    └── views.py
    └── migrations/
        └── __init__.py
└── authentication/
    └── __init__.py
    └── admin.py
    └── apps.py
    └── models.py
    └── tests.py
    └── urls.py
    └── views.py
    └── migrations/
        └── __init__.py
    └── templates/
        └── login.html
        └── profile.html
        └── register.html
└── backend/
    └── Procfile
    └── main.py
    └── requirements.txt
└── daftarsanggar/
    └── __init__.py
    └── admin.py
    └── apps.py
    └── models.py
    └── tests.py
    └── urls.py
    └── views.py
    └── migrations/
        └── 0001_initial.py
        └── 0002_sanggar_image_url.py
        └── 0003_remove_sanggar_image_url_sanggar_image.py
        └── __init__.py
    └── static/
        └── daftarsanggar/
            └── img/
                └── ayodyapala.png
                └── balletsumbercipta.png
                └── bintangasti.png
                └── ciptabudoyo.png
                └── ekidancecompany.png
                └── foreverdance.png
                └── gemacitra.png
                └── geneceladance.png
                └── gigiartofdance.png
                └── interludedance.png
                └── kawulamuda.png
                └── kinangputra.png
                └── kinaryagsp.png
                └── marlupi.png
                └── namarina.png
                └── puspabudoyo.png
                └── ratnasari.png
                └── sanggarbetawi.png
                └── stepsdance.png
                └── trialogo.png
                └── uniteddance.png
    └── templates/
        └── daftarsanggar/
            └── base.html
            └── detail.html
            └── index.html
└── dances/
    └── __init__.py
    └── admin.py
    └── apps.py
    └── models.py
    └── tests.py
    └── urls.py
    └── views.py
    └── migrations/
        └── __init__.py
    └── templates/
        └── dances/
            └── dance_assessment.html
            └── dance_detail.html
            └── dance_list.html
            └── dance_result.html
            └── dance_tutorial.html
└── landing/
    └── .gitignore
    └── README.md
    └── eslint.config.mjs
    └── next-env.d.ts
    └── next.config.ts
    └── package.json
    └── postcss.config.mjs
    └── tsconfig.json
    └── app/
        └── favicon.ico
        └── globals.css
        └── layout.tsx
        └── page.tsx
    └── public/
        └── file.svg
        └── globe.svg
        └── logotria.png
        └── next.svg
        └── vercel.svg
        └── window.svg
└── main/
    └── __init__.py
    └── admin.py
    └── apps.py
    └── models.py
    └── tests.py
    └── urls.py
    └── views.py
    └── migrations/
        └── __init__.py
    └── templates/
        └── home.html
└── scripts/
    └── dev.sh
    └── setup.sh
└── static/
    └── images/
        └── team.png
        └── tracking.png
        └── tria.png
└── tria/
    └── __init__.py
    └── asgi.py
    └── settings.py
    └── urls.py
    └── wsgi.py
    └── templates/
        └── about.html
        └── base.html
        └── footer.html
        └── landing.html
        └── partials/
            └── navbar.html
```

## Files

### .env.example

```example
# Salin ke .env lalu isi
OPENAI_API_KEY=
BACKEND_PORT=8001
DJANGO_PORT=8000
LANDING_PORT=3000
```

### .gitignore

```
# Django
*.log
*.pot
*.pyc
**pycache**
db.sqlite3
media
# Backup files
*.bak
# If you are using PyCharm
# User-specific stuff
.idea/**/workspace.xml
.idea/**/tasks.xml
.idea/**/usage.statistics.xml
.idea/**/dictionaries
.idea/**/shelf
# AWS User-specific
.idea/**/aws.xml
# Generated files
.idea/**/contentModel.xml
.DS_Store
# Sensitive or high-churn files
.idea/**/dataSources/
.idea/**/dataSources.ids
.idea/**/dataSources.local.xml
.idea/**/sqlDataSources.xml
.idea/**/dynamic.xml
.idea/**/uiDesigner.xml
.idea/**/dbnavigator.xml
# Gradle
.idea/**/gradle.xml
.idea/**/libraries
# File-based project format
*.iws
# IntelliJ
out/
# JIRA plugin
atlassian-ide-plugin.xml
# Python
*.py[cod]
*$py.class
# Distribution / packaging
.Python build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
*.manifest
*.spec
# Installer logs
pip-log.txt
pip-delete-this-directory.txt
# Unit test / coverage reports
htmlcov/
.tox/
.coverage
.coverage.*
.cache
.pytest_cache/
nosetests.xml
coverage.xml
*.cover
.hypothesis/
# Jupyter Notebook
.ipynb_checkpoints
# pyenv
.python-version
# celery
celerybeat-schedule.*
# SageMath parsed files
*.sage.py
# Environments
.env*
!.env.example*
.venv
env/
venv/
ENV/
env.bak/
venv.bak/
# mkdocs documentation
/site
# mypy
.mypy_cache/
# Sublime Text
*.tmlanguage.cache
*.tmPreferences.cache
*.stTheme.cache
*.sublime-workspace
*.sublime-project
# sftp configuration file
sftp-config.json
# Package control specific files Package
Control.last-run
Control.ca-list
Control.ca-bundle
Control.system-ca-bundle
GitHub.sublime-settings
# Visual Studio Code
.vscode/*
!.vscode/settings.json
!.vscode/tasks.json
!.vscode/launch.json
!.vscode/extensions.json
.history    
```

### README.md

```md
TRIA

📖 Deskripsi Projek
TRIA adalah aplikasi berbasis Artificial Intelligence dan Computer Vision yang berfungsi sebagai media pembelajaran interaktif sekaligus konservasi digital seni tari tradisional Indonesia. Aplikasi ini memanfaatkan teknologi pose estimation dan motion tracking untuk menganalisis gerakan tubuh pengguna secara real-time serta memberikan umpan balik terhadap ketepatan, ritme, dan ekspresi gerak dibandingkan dengan data maestro tari.

🎯 Tujuan Utama
Konservasi Digital - Mendokumentasikan gerakan tarian tradisional Indonesia dalam format data digital terstruktur
Pembelajaran Interaktif - Menyediakan akses belajar tari tradisional berkualitas yang terjangkau dan mudah diakses
Pemberdayaan Ekonomi - Menciptakan kanal digital bagi pelaku budaya untuk memonetisasi keahlian mereka

Fitur utama
- Katalog tarian tradisional lengkap dengan detail dan tutorial
- Penilaian berbasis kamera menggunakan pose estimation dan scoring otomatis
- Direktori sanggar dengan informasi kontak dan lokasi
- Akun pengguna (registrasi/login/profil) dan manajemen sesi
- Halaman hasil dan progres dengan umpan balik sub-gerakan

Stack Teknologi

- Backend: Python + Django (proyek ini menggunakan Django 5.x)
- Database: SQLite untuk pengembangan lokal; PostgreSQL direkomendasikan untuk produksi
- Frontend: Template Django, JavaScript vanilla, CSS (menggunakan variabel CSS dan gaya mirip Tailwind pada beberapa bagian)
- AI / CV: Integrasi MediaPipe / OpenPose untuk pose estimation, OpenCV untuk pemrosesan video, TensorFlow / PyTorch untuk model penilaian
- Antrian tugas (opsional): Celery + Redis untuk pemrosesan background (mis. video atau tugas model)
- Deployment: WSGI (gunicorn), Docker (opsional), berkas statis via `collectstatic` / WhiteNoise atau web server (nginx)

Panduan singkat — Pengembangan lokal

1. Buat dan aktifkan virtual environment

```powershell
python -m venv env
env\Scripts\Activate.ps1    # PowerShell pada Windows
```

2. Pasang dependensi

```powershell
pip install -r requirements.txt
```

3. Terapkan migrasi dan buat superuser

```powershell
python manage.py migrate
python manage.py createsuperuser
```

4. Jalankan server pengembangan

```powershell
python manage.py runserver
```

Buka http://127.0.0.1:8000 di peramban Anda.

Catatan deployment
- Tetapkan `PRODUCTION=true` (atau pastikan `DEBUG=False`) dan atur `ALLOWED_HOSTS` serta `CSRF_TRUSTED_ORIGINS` ke domain Anda (sertakan scheme, mis. `https://contoh.com`).
- Jalankan `python manage.py collectstatic --noinput` dan layani folder `staticfiles/` melalui web server (nginx) atau gunakan WhiteNoise untuk deployment sederhana.
- Jika TLS diakhiri oleh load balancer / reverse proxy, pastikan header `X-Forwarded-Proto: https` diteruskan dan sesuaikan `SECURE_PROXY_SSL_HEADER` di pengaturan Django.

Struktur repositori (secara ringkas)
- `tria/` — pengaturan proyek dan titik masuk (settings.py, urls.py)
- `dances/` — katalog tarian, tampilan assessment dan tutorial
- `daftarsanggar/` — direktori sanggar dan halaman detail
- `authentication/` — login, register, profil dan template terkait
- `main/`, `articles/` dan aplikasi pendukung lainnya

Contributor TEAM (Little Vietnam)
```

### SETUP.md

```md
# TRIA (budayago) — monorepo lokal
- tria-master/ — Django web app (http://127.0.0.1:8000)
- backend/ — FastAPI scoring (http://127.0.0.1:8001, butuh OPENAI_API_KEY di .env; tanpa itu otomatis fallback)
- landing/ — Next.js landing (http://localhost:3000)

Setup sekali: ./scripts/setup.sh   |   Jalankan semua: ./scripts/dev.sh
```

### manage.py

```py
#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tria.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
```

### requirements.txt

```txt
django
gunicorn
whitenoise
psycopg2-binary
requests
urllib3
python-dotenv
```

### about/__init__.py

```py

```

### about/admin.py

```py
from django.contrib import admin

# Register your models here.
```

### about/apps.py

```py
from django.apps import AppConfig


class AboutConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "about"
```

### about/models.py

```py
from django.db import models

# Create your models here.
```

### about/tests.py

```py
from django.test import TestCase

# Create your tests here.
```

### about/urls.py

```py
from django.urls import path
from . import views

app_name = 'about'

urlpatterns = [
    path('', views.about_page, name='about_page'),
]
```

### about/views.py

```py
from django.shortcuts import render

def about_page(request):
    return render(request, 'about.html')
```

### about/migrations/__init__.py

```py

```

### about/templates/a.html

```html

```

### about/templates/about.html

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Tria - Belajar Tarian Tradisional Indonesia</title>
  <link rel="icon" type="image/png" href="https://i.ibb.co.com/fY9F3RwF/tria.png" />
  <link rel="shortcut icon" type="image/png" href="https://i.ibb.co.com/fY9F3RwF/tria.png" />
  <style>
    body {
      background-color: white;
      color: black;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen,
          Ubuntu, Cantarell, "Open Sans", "Helvetica Neue", sans-serif;
      margin: 0;
      padding: 1rem;
    }
    nav {
      display: flex;
      justify-content: center;
      gap: 2rem;
      margin-bottom: 2rem;
    }
    nav a {
      color: #d62e00;
      font-weight: 700;
      text-decoration: none;
      font-size: 1.2rem;
    }
    nav a:hover {
      color: #ff6f00;
    }
    h1 {
      text-align: center;
      margin-bottom: 1rem;
    }
    p {
      max-width: 600px;
      margin: 0 auto 2rem auto;
      font-size: 1.1rem;
      text-align: center;
    }
    @media (max-width: 600px) {
      body {
        padding: 0.5rem;
        font-size: 1rem;
      }
      nav {
        gap: 1rem;
      }
      nav a {
        font-size: 1rem;
      }
    }
  </style>
</head>
<body>
  <nav>
    <a href="{% url 'home' %}">Home</a>
    <a href="{% url 'about:about_page' %}">About</a>
    <a href="{% url 'dances:dance_list' %}">Dances</a>
  </nav>
  <h1>About Tria</h1>
  <p>
    Tria adalah platform untuk belajar tarian tradisional Indonesia dengan cara yang benar dan menyenangkan.
    Pelajari berbagai tarian dengan panduan langkah demi langkah.
  </p>
</body>
</html>
```

### articles/__init__.py

```py

```

### articles/admin.py

```py
from django.contrib import admin

# Register your models here.
```

### articles/apps.py

```py
from django.apps import AppConfig


class ArticlesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "articles"
```

### articles/models.py

```py
from django.db import models

# Create your models here.
```

### articles/tests.py

```py
from django.test import TestCase

# Create your tests here.
```

### articles/views.py

```py
from django.shortcuts import render

# Create your views here.
```

### articles/migrations/__init__.py

```py

```

### authentication/__init__.py

```py

```

### authentication/admin.py

```py
from django.contrib import admin

# Register your models here.
```

### authentication/apps.py

```py
from django.apps import AppConfig


class AuthenticationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'authentication'
```

### authentication/models.py

```py
from django.db import models

# Create your models here.
```

### authentication/tests.py

```py
from django.test import TestCase

# Create your tests here.
```

### authentication/urls.py

```py
from django.urls import path
from .views import register, login, logout, profile

app_name = 'authentication'

urlpatterns = [
    path('register/', register, name='register'),
    path('login/', login, name='login'),
    path('logout/', logout, name='logout'),
    path('profile/', profile, name='profile'),
]
```

### authentication/views.py

```py
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login as auth_login, logout as auth_logout, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required


def register(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    form = UserCreationForm()

    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            messages.success(request, 'Akun kamu berhasil dibuat! Selamat datang di Tria.')
            return redirect('home')
    
    context = {'form': form}
    return render(request, 'register.html', context)


def login(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)

        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            messages.success(request, f'Selamat datang kembali, {user.username}!')
            
            # Redirect to next parameter or home
            next_url = request.GET.get('next', 'home')
            return redirect(next_url)
        else:
            messages.error(request, 'Username atau password salah.')
    else:
        form = AuthenticationForm(request)
    
    context = {'form': form}
    return render(request, 'login.html', context)


@login_required
def logout(request):
    auth_logout(request)
    messages.success(request, 'Kamu berhasil logout. Sampai jumpa lagi!')
    return redirect('home')


@login_required
def profile(request):
    """Simple profile page showing user info and a logout action."""
    context = {
        'user': request.user,
    }
    return render(request, 'profile.html', context)
```

### authentication/migrations/__init__.py

```py

```

### authentication/templates/login.html

```html
{% load static %}
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Tria - Belajar Tarian Tradisional Indonesia</title>
    <link rel="icon" type="image/png" href="https://i.ibb.co.com/fY9F3RwF/tria.png" />
    <link rel="shortcut icon" type="image/png" href="https://i.ibb.co.com/fY9F3RwF/tria.png" />
    <style>
        :root {
            --tria-red: #e53935;
            --tria-orange: #ff9800;
            --tria-orange-soft: #fff3e0;
            --tria-border: #f0f0f0;
            --tria-text: #222222;
            --tria-muted: #555555;
        }

        * {
            box-sizing: border-box;
        }

        body {
            background: linear-gradient(135deg, #fff3e0 0%, #ffffff 100%);
            color: var(--tria-text);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen,
                Ubuntu, Cantarell, "Open Sans", "Helvetica Neue", sans-serif;
            margin: 0;
            padding: 0;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }

        a {
            text-decoration: none;
            color: inherit;
        }

        /* NAVBAR */
        .navbar {
            background-color: #ffffff;
            border-bottom: 1px solid var(--tria-border);
            position: sticky;
            top: 0;
            z-index: 50;
        }

        .nav-inner {
            max-width: 1100px;
            margin: 0 auto;
            padding: 0.75rem 1.25rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
        }

        .nav-brand {
            display: flex;
            align-items: center;
            gap: 0.6rem;
        }

        .nav-logo {
            height: 36px;
            width: 36px;
            object-fit: contain;
        }

        .nav-title {
            font-weight: 700;
            letter-spacing: 0.03em;
            font-size: 1.1rem;
        }

        .nav-links {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            font-size: 0.95rem;
        }

        .nav-link {
            padding: 0.4rem 0.75rem;
            border-radius: 999px;
            transition: background-color 0.2s ease, color 0.2s ease, transform 0.1s ease;
        }

        .nav-link:hover {
            background-color: var(--tria-orange-soft);
            color: var(--tria-red);
            transform: translateY(-1px);
        }

        /* AUTH CONTAINER */
        .auth-container {
            flex: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 2rem 1.25rem;
        }

        .auth-card {
            background-color: #ffffff;
            border-radius: 1.2rem;
            border: 1px solid var(--tria-border);
            box-shadow: 0 14px 30px rgba(0, 0, 0, 0.08);
            padding: 2.5rem;
            width: 100%;
            max-width: 440px;
            position: relative;
            overflow: hidden;
        }

        /* Decorative circle accent */
        .auth-card::before {
            content: '';
            position: absolute;
            top: -50px;
            right: -50px;
            width: 200px;
            height: 200px;
            background: radial-gradient(circle, var(--tria-orange-soft), transparent);
            opacity: 0.4;
            pointer-events: none;
        }

        .auth-header {
            text-align: center;
            margin-bottom: 2rem;
            position: relative;
            z-index: 1;
        }

        .auth-badge {
            display: inline-flex;
            padding: 0.3rem 0.7rem;
            border-radius: 999px;
            background-color: var(--tria-orange-soft);
            color: var(--tria-red);
            font-size: 0.78rem;
            font-weight: 600;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            margin-bottom: 0.8rem;
        }

        .auth-title {
            font-size: 1.8rem;
            margin: 0 0 0.5rem 0;
            background: linear-gradient(135deg, var(--tria-red), var(--tria-orange));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .auth-subtitle {
            font-size: 0.95rem;
            color: var(--tria-muted);
            line-height: 1.5;
        }

        /* MESSAGES */
        .messages {
            margin-bottom: 1.5rem;
            position: relative;
            z-index: 1;
        }

        .message {
            padding: 0.75rem 1rem;
            border-radius: 0.75rem;
            margin-bottom: 0.5rem;
            font-size: 0.9rem;
            animation: slideIn 0.3s ease;
        }

        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(-10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .message.success {
            background-color: #e8f5e9;
            color: #2e7d32;
            border: 1px solid #a5d6a7;
        }

        .message.error {
            background-color: #ffebee;
            color: #c62828;
            border: 1px solid #ef9a9a;
        }

        .message.info {
            background-color: #e3f2fd;
            color: #1565c0;
            border: 1px solid #90caf9;
        }

        /* FORM */
        .auth-form {
            display: flex;
            flex-direction: column;
            gap: 1.25rem;
            position: relative;
            z-index: 1;
        }

        .form-group {
            display: flex;
            flex-direction: column;
            gap: 0.4rem;
        }

        .form-label {
            font-size: 0.9rem;
            font-weight: 600;
            color: var(--tria-text);
        }

        .form-input {
            padding: 0.75rem 1rem;
            border: 1px solid var(--tria-border);
            border-radius: 0.5rem;
            font-size: 0.95rem;
            transition: all 0.2s ease;
            background-color: #ffffff;
        }

        .form-input:focus {
            outline: none;
            border-color: var(--tria-orange);
            box-shadow: 0 0 0 3px rgba(255, 152, 0, 0.1);
            transform: translateY(-1px);
        }

        .form-input:hover {
            border-color: rgba(255, 152, 0, 0.4);
        }

        .form-help {
            font-size: 0.82rem;
            color: var(--tria-muted);
            line-height: 1.4;
        }

        .form-error {
            font-size: 0.85rem;
            color: var(--tria-red);
            display: flex;
            align-items: center;
            gap: 0.3rem;
        }

        .form-error::before {
            content: "⚠";
            font-size: 1rem;
        }

        .form-submit {
            background: linear-gradient(135deg, var(--tria-red), var(--tria-orange));
            color: #ffffff;
            font-weight: 600;
            padding: 0.85rem 1.5rem;
            border-radius: 999px;
            border: none;
            font-size: 0.95rem;
            cursor: pointer;
            transition: all 0.2s ease;
            box-shadow: 0 8px 18px rgba(229, 57, 53, 0.25);
            margin-top: 0.5rem;
            position: relative;
            overflow: hidden;
        }

        .form-submit::before {
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            width: 0;
            height: 0;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.2);
            transform: translate(-50%, -50%);
            transition: width 0.6s, height 0.6s;
        }

        .form-submit:hover::before {
            width: 300px;
            height: 300px;
        }

        .form-submit:hover {
            background: linear-gradient(135deg, #c62828, #fb8c00);
            transform: translateY(-2px);
            box-shadow: 0 12px 24px rgba(229, 57, 53, 0.35);
        }

        .form-submit:active {
            transform: translateY(0);
        }

        .auth-footer {
            text-align: center;
            margin-top: 1.5rem;
            padding-top: 1.5rem;
            border-top: 1px solid var(--tria-border);
            font-size: 0.9rem;
            color: var(--tria-muted);
            position: relative;
            z-index: 1;
        }

        .auth-link {
            color: var(--tria-red);
            font-weight: 600;
            transition: color 0.2s ease;
        }

        .auth-link:hover {
            color: var(--tria-orange);
            text-decoration: underline;
        }

        /* Welcome decoration */
        .welcome-icon {
            font-size: 3rem;
            margin-bottom: 0.5rem;
            animation: float 3s ease-in-out infinite;
        }

        @keyframes float {
            0%, 100% {
                transform: translateY(0);
            }
            50% {
                transform: translateY(-10px);
            }
        }

        @media (max-width: 600px) {
            .auth-card {
                padding: 2rem 1.5rem;
            }

            .auth-title {
                font-size: 1.5rem;
            }

            .nav-links {
                gap: 0.5rem;
            }

            .nav-link {
                font-size: 0.85rem;
                padding: 0.35rem 0.6rem;
            }
        }

        /* Hide Django's default table layout */
        table {
            display: none !important;
        }
    </style>
</head>
<body>
    <nav class="navbar">
        <div class="nav-inner">
            <a href="{% url 'home' %}" class="nav-brand">
                <img src="https://i.ibb.co.com/fY9F3RwF/tria.png" alt="Tria logo" class="nav-logo" />
                <span class="nav-title">Tria</span>
            </a>
            <div class="nav-links">
                <a href="{% url 'home' %}" class="nav-link">Home</a>
                <a href="{% url 'about:about_page' %}" class="nav-link">About</a>
            </div>
        </div>
    </nav>

    <div class="auth-container">
        <div class="auth-card">
            <div class="auth-header">
                <div class="welcome-icon">💃</div>
                <div class="auth-badge">Masuk ke Tria</div>
                <h1 class="auth-title">Selamat Datang Kembali</h1>
                <p class="auth-subtitle">Masuk untuk melanjutkan belajar tarian tradisional Indonesia</p>
            </div>

            {% if messages %}
            <div class="messages">
                {% for message in messages %}
                <div class="message {{ message.tags }}">
                    {{ message }}
                </div>
                {% endfor %}
            </div>
            {% endif %}

            <form method="POST" action="" class="auth-form">
                {% csrf_token %}
                
                <div class="form-group">
                    <label for="{{ form.username.id_for_label }}" class="form-label">
                        Username
                    </label>
                    <input 
                        type="text" 
                        name="{{ form.username.name }}" 
                        id="{{ form.username.id_for_label }}"
                        class="form-input"
                        placeholder="Masukkan username kamu"
                        required
                        autofocus
                    />
                    {% if form.username.errors %}
                        {% for error in form.username.errors %}
                        <span class="form-error">{{ error }}</span>
                        {% endfor %}
                    {% endif %}
                </div>

                <div class="form-group">
                    <label for="{{ form.password.id_for_label }}" class="form-label">
                        Password
                    </label>
                    <input 
                        type="password" 
                        name="{{ form.password.name }}" 
                        id="{{ form.password.id_for_label }}"
                        class="form-input"
                        placeholder="Masukkan password kamu"
                        required
                    />
                    {% if form.password.errors %}
                        {% for error in form.password.errors %}
                        <span class="form-error">{{ error }}</span>
                        {% endfor %}
                    {% endif %}
                </div>

                {% if form.non_field_errors %}
                <div class="form-group">
                    {% for error in form.non_field_errors %}
                    <span class="form-error">{{ error }}</span>
                    {% endfor %}
                </div>
                {% endif %}

                <button type="submit" class="form-submit">
                    Masuk ke Tria
                </button>
            </form>

            <div class="auth-footer">
                Belum punya akun? 
                <a href="{% url 'authentication:register' %}" class="auth-link">Daftar sekarang</a>
            </div>
        </div>
    </div>

    <!-- Hidden table for Django form compatibility -->
    <div style="display: none;">
        {{ form.as_table }}
    </div>
</body>
</html>
```

### authentication/templates/profile.html

```html
{% load static %}

{% block meta %}
<style>
    :root {
        --tria-red: #e53935;
        --tria-orange: #ff9800;
        --tria-soft-bg: #fff7ec;
        --tria-border: #f0e0d8;
        --tria-text: #222;
        --tria-muted: #666;
    }

    body {
        margin: 0;
        padding: 0;
        background: #ffffff;
        color: var(--tria-text);
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen,
            Ubuntu, Cantarell, "Open Sans", "Helvetica Neue", sans-serif;
    }

    a {
        text-decoration: none;
        color: inherit;
    }

    /* NAVBAR – same style as other pages */
    .navbar {
        background-color: #ffffff;
        border-bottom: 1px solid #f3eee7;
        position: sticky;
        top: 0;
        z-index: 50;
        backdrop-filter: blur(10px);
    }

    .nav-inner {
        max-width: 1100px;
        margin: 0 auto;
        padding: 0.75rem 1.5rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
    }

    .nav-brand {
        display: flex;
        align-items: center;
        gap: 0.6rem;
    }

    .nav-logo {
        height: 36px;
        width: 36px;
        object-fit: contain;
    }

    .nav-title {
        font-weight: 700;
        letter-spacing: 0.03em;
        font-size: 1.1rem;
    }

    .nav-links {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        font-size: 0.95rem;
    }

    .nav-link {
        padding: 0.4rem 0.75rem;
        border-radius: 999px;
        transition: background-color 0.2s ease, color 0.2s ease, transform 0.1s ease;
    }

    .nav-link:hover {
        background-color: #fff1df;
        color: var(--tria-red);
        transform: translateY(-1px);
    }

    .nav-cta {
        background: linear-gradient(135deg, var(--tria-red), var(--tria-orange));
        color: #ffffff;
        font-weight: 600;
    }

    .nav-cta:hover {
        background: linear-gradient(135deg, #c62828, #fb8c00);
        color: #ffffff;
    }

    .nav-avatar {
        width: 34px;
        height: 34px;
        border-radius: 8px;
        background: linear-gradient(135deg,#e53935,#ff9800);
        color: #fff;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 0.95rem;
    }

    /* PROFILE ----------------------------------------------------- */

    .profile-container {
        max-width: 900px;
        margin: 2.5rem auto;
        padding: 1rem 1.25rem;
    }

    .profile-card {
        background: #fff;
        border: 1px solid var(--tria-border);
        border-radius: 16px;
        padding: 1.75rem 1.75rem 1.5rem;
        box-shadow: 0 16px 40px rgba(0,0,0,0.05);
    }

    .profile-header {
        display: flex;
        align-items: center;
        gap: 1.25rem;
    }

    .avatar {
        width: 80px;
        height: 80px;
        border-radius: 18px;
        background: linear-gradient(135deg,var(--tria-red),var(--tria-orange));
        color: #fff;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 800;
        font-size: 1.5rem;
        box-shadow: 0 10px 26px rgba(229,57,53,0.35);
    }

    .profile-main {
        flex: 1;
    }

    .profile-name {
        font-size: 1.35rem;
        font-weight: 800;
        margin: 0 0 0.1rem 0;
    }

    .profile-username {
        font-size: 0.9rem;
        color: var(--tria-muted);
        margin: 0 0 0.35rem 0;
    }

    .profile-email {
        font-size: 0.92rem;
        color: var(--tria-text);
    }

    .profile-tag {
        display: inline-flex;
        align-items: center;
        gap: 0.3rem;
        background: var(--tria-soft-bg);
        border-radius: 999px;
        padding: 0.15rem 0.6rem;
        font-size: 0.8rem;
        color: var(--tria-red);
        margin-top: 0.4rem;
        font-weight: 600;
    }

    .profile-body {
        margin-top: 1.75rem;
        border-top: 1px solid #f4e5dd;
        padding-top: 1.25rem;
    }

    .profile-intro {
        margin: 0 0 1.25rem 0;
        font-size: 0.94rem;
        color: var(--tria-muted);
    }

    .info-grid {
        display: grid;
        grid-template-columns: repeat(2,minmax(0,1fr));
        gap: 1rem 2rem;
        margin-bottom: 1.75rem;
    }

    .info-item {
        font-size: 0.9rem;
    }

    .info-label {
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--tria-muted);
        margin-bottom: 0.2rem;
    }

    .info-value {
        font-weight: 600;
        color: var(--tria-text);
    }

    .profile-actions {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
        align-items: center;
    }

    .btn-logout,
    .btn-edit {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 0.7rem 1.3rem;
        border-radius: 999px;
        font-weight: 700;
        font-size: 0.9rem;
        border: none;
        cursor: pointer;
        transition: background-color 0.2s ease, color 0.2s ease,
                    box-shadow 0.2s ease, transform 0.1s ease,
                    border-color 0.2s ease, opacity 0.12s ease;
    }

    .btn-logout {
        background: linear-gradient(135deg,var(--tria-red),var(--tria-orange));
        color: #fff;
        box-shadow: 0 10px 26px rgba(229,57,53,0.25);
    }

    .btn-logout:hover {
        transform: translateY(-1px);
        box-shadow: 0 14px 32px rgba(229,57,53,0.32);
        opacity: 0.97;
    }

    .btn-edit {
        background: #fff;
        color: var(--tria-red);
        border: 1px solid rgba(229,57,53,0.4);
    }

    .btn-edit:hover {
        background: #fff7ec;
        transform: translateY(-1px);
        box-shadow: 0 8px 18px rgba(229,57,53,0.15);
    }

    .helper-text {
        font-size: 0.82rem;
        color: var(--tria-muted);
    }

    /* MODAL EDIT PROFILE ------------------------------------------- */

    .modal-overlay {
        position: fixed;
        inset: 0;
        background: rgba(0,0,0,0.35);
        display: none;
        align-items: center;
        justify-content: center;
        z-index: 60;
    }

    .modal-overlay.open {
        display: flex;
    }

    .modal-card {
        background: #fff;
        border-radius: 16px;
        padding: 1.6rem 1.75rem 1.5rem;
        width: 100%;
        max-width: 420px;
        box-shadow: 0 18px 45px rgba(0,0,0,0.22);
        position: relative;
    }

    .modal-title {
        font-size: 1.2rem;
        font-weight: 700;
        margin: 0 0 0.4rem 0;
    }

    .modal-subtitle {
        font-size: 0.86rem;
        color: var(--tria-muted);
        margin-bottom: 1rem;
    }

    .modal-field {
        margin-bottom: 0.9rem;
    }

    .modal-label {
        display: block;
        font-size: 0.82rem;
        font-weight: 600;
        margin-bottom: 0.3rem;
        color: var(--tria-muted);
    }

    .modal-input {
        width: 100%;
        padding: 0.55rem 0.7rem;
        border-radius: 8px;
        border: 1px solid #e0d2c8;
        font-size: 0.9rem;
        font-family: inherit;
    }

    .modal-input:focus {
        outline: none;
        border-color: var(--tria-orange);
        box-shadow: 0 0 0 2px rgba(255,152,0,0.25);
    }

    .modal-actions {
        display: flex;
        justify-content: flex-end;
        gap: 0.6rem;
        margin-top: 1rem;
    }

    .btn-cancel {
        background: #fff;
        color: var(--tria-muted);
        border: 1px solid #ddd;
        padding: 0.55rem 1.1rem;
        border-radius: 999px;
        font-size: 0.86rem;
        cursor: pointer;
    }

    .btn-save {
        background: linear-gradient(135deg,var(--tria-red),var(--tria-orange));
        color: #fff;
        border: none;
        padding: 0.55rem 1.25rem;
        border-radius: 999px;
        font-size: 0.86rem;
        cursor: pointer;
        box-shadow: 0 8px 20px rgba(229,57,53,0.28);
    }

    .btn-save:hover {
        transform: translateY(-1px);
    }

    @media (max-width: 720px) {
        .profile-container {
            margin: 1.5rem auto;
            padding-inline: 0.9rem;
        }
        .profile-card {
            padding: 1.4rem 1.2rem 1.4rem;
        }
        .profile-header {
            align-items: flex-start;
        }
        .info-grid {
            grid-template-columns: minmax(0,1fr);
        }
        .modal-card {
            margin-inline: 1rem;
        }
    }
</style>
{% endblock %}

{% block content %}

{% include "partials/navbar.html" %}

<main class="profile-container">
    <section class="profile-card">
        <!-- HEADER: avatar + main identity -->
        <header class="profile-header">
            <div class="avatar">
                {{ user.username|slice:":1"|upper }}
            </div>
            <div class="profile-main">
                <p class="profile-name">
                    {{ user.get_full_name|default:user.username }}
                </p>
                <p class="profile-username">
                    @{{ user.username }}
                </p>
               
                <span class="profile-tag">
                    Akun Tria
                </span>
            </div>
        </header>

        <!-- BODY: account info -->
        <section class="profile-body">
            <p class="profile-intro">
                Di halaman ini kamu bisa melihat informasi akunmu dan keluar dari sesi Tria dengan aman.
            </p>

            <div class="info-grid">
                <div class="info-item">
                    <div class="info-label">Username</div>
                    <div class="info-value">
                        {{ user.username }}
                    </div>
                </div>
                <div class="info-item">
                    <div class="info-label">Bergabung Sejak</div>
                    <div class="info-value">
                        {{ user.date_joined|date:"d M Y" }}
                    </div>
                </div>
            </div>

            <!-- ACTIONS -->
            <div class="profile-actions">
            

                <form method="post" action="{% url 'authentication:logout' %}">
                    {% csrf_token %}
                    <button type="submit" class="btn-logout">
                        Logout
                    </button>
                </form>

                <p class="helper-text">
                    Setelah logout, kamu bisa login kembali kapan saja untuk melanjutkan belajar tarian.
                </p>
            </div>
        </section>
    </section>
</main>

<!-- EDIT PROFILE MODAL -->
<div id="editModal" class="modal-overlay">
    <div class="modal-card">
        <h2 class="modal-title">Edit Profil</h2>
        <p class="modal-subtitle">
            Ubah nama lengkap dan emailmu. Perubahan akan disimpan setelah kamu menekan tombol <strong>Simpan</strong>.
        </p>

        <form method="post" action="">
            {% csrf_token %}
            <div class="modal-field">
                <label class="modal-label" for="full_name">Nama Lengkap</label>
                <input
                    type="text"
                    id="full_name"
                    name="full_name"
                    class="modal-input"
                    value="{{ user.get_full_name }}"
                />
            </div>

            <div class="modal-field">
                <label class="modal-label" for="email">Email</label>
                <input
                    type="email"
                    id="email"
                    name="email"
                    class="modal-input"
                    value="{{ user.email }}"
                />
            </div>

            <div class="modal-actions">
                <button type="button" class="btn-cancel" id="cancelEditBtn" onclick="window.location.href='/dances'">Batal</button>
                <button type="submit" class="btn-save">Simpan</button>
            </div>
        </form>
    </div>
</div>

<script>
    const editBtn = document.getElementById('editProfileBtn');
    const modal = document.getElementById('editModal');
    const cancelBtn = document.getElementById('cancelEditBtn');

    if (editBtn && modal && cancelBtn) {
        editBtn.addEventListener('click', () => {
            modal.classList.add('open');
        });

        cancelBtn.addEventListener('click', () => {
            modal.classList.remove('open');
        });

        // close when clicking outside the modal card
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.classList.remove('open');
            }
        });
    }
</script>

{% endblock %}
```

### authentication/templates/register.html

```html
{% load static %}
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Tria - Belajar Tarian Tradisional Indonesia</title>
    <link rel="icon" type="image/png" href="https://i.ibb.co.com/fY9F3RwF/tria.png" />
    <link rel="shortcut icon" type="image/png" href="https://i.ibb.co.com/fY9F3RwF/tria.png" />
    <style>
        :root {
            --tria-red: #e53935;
            --tria-orange: #ff9800;
            --tria-orange-soft: #fff3e0;
            --tria-border: #f0f0f0;
            --tria-text: #222222;
            --tria-muted: #555555;
        }

        * {
            box-sizing: border-box;
        }

        body {
            background: linear-gradient(135deg, #fff3e0 0%, #ffffff 100%);
            color: var(--tria-text);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen,
                Ubuntu, Cantarell, "Open Sans", "Helvetica Neue", sans-serif;
            margin: 0;
            padding: 0;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }

        a {
            text-decoration: none;
            color: inherit;
        }

        /* NAVBAR */
        .navbar {
            background-color: #ffffff;
            border-bottom: 1px solid var(--tria-border);
            position: sticky;
            top: 0;
            z-index: 50;
        }

        .nav-inner {
            max-width: 1100px;
            margin: 0 auto;
            padding: 0.75rem 1.25rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
        }

        .nav-brand {
            display: flex;
            align-items: center;
            gap: 0.6rem;
        }

        .nav-logo {
            height: 36px;
            width: 36px;
            object-fit: contain;
        }

        .nav-title {
            font-weight: 700;
            letter-spacing: 0.03em;
            font-size: 1.1rem;
        }

        .nav-links {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            font-size: 0.95rem;
        }

        .nav-link {
            padding: 0.4rem 0.75rem;
            border-radius: 999px;
            transition: background-color 0.2s ease, color 0.2s ease, transform 0.1s ease;
        }

        .nav-link:hover {
            background-color: var(--tria-orange-soft);
            color: var(--tria-red);
            transform: translateY(-1px);
        }

        /* AUTH CONTAINER */
        .auth-container {
            flex: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 2rem 1.25rem;
        }

        .auth-card {
            background-color: #ffffff;
            border-radius: 1.2rem;
            border: 1px solid var(--tria-border);
            box-shadow: 0 14px 30px rgba(0, 0, 0, 0.08);
            padding: 2.5rem;
            width: 100%;
            max-width: 480px;
        }

        .auth-header {
            text-align: center;
            margin-bottom: 2rem;
        }

        .auth-badge {
            display: inline-flex;
            padding: 0.3rem 0.7rem;
            border-radius: 999px;
            background-color: var(--tria-orange-soft);
            color: var(--tria-red);
            font-size: 0.78rem;
            font-weight: 600;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            margin-bottom: 0.8rem;
        }

        .auth-title {
            font-size: 1.8rem;
            margin: 0 0 0.5rem 0;
        }

        .auth-subtitle {
            font-size: 0.95rem;
            color: var(--tria-muted);
        }

        /* MESSAGES */
        .messages {
            margin-bottom: 1.5rem;
        }

        .message {
            padding: 0.75rem 1rem;
            border-radius: 0.5rem;
            margin-bottom: 0.5rem;
            font-size: 0.9rem;
        }

        .message.success {
            background-color: #e8f5e9;
            color: #2e7d32;
            border: 1px solid #a5d6a7;
        }

        .message.error {
            background-color: #ffebee;
            color: #c62828;
            border: 1px solid #ef9a9a;
        }

        /* FORM */
        .auth-form {
            display: flex;
            flex-direction: column;
            gap: 1.25rem;
        }

        .form-group {
            display: flex;
            flex-direction: column;
            gap: 0.4rem;
        }

        .form-label {
            font-size: 0.9rem;
            font-weight: 600;
            color: var(--tria-text);
        }

        .form-input {
            padding: 0.75rem 1rem;
            border: 1px solid var(--tria-border);
            border-radius: 0.5rem;
            font-size: 0.95rem;
            transition: border-color 0.2s ease, box-shadow 0.2s ease;
        }

        .form-input:focus {
            outline: none;
            border-color: var(--tria-orange);
            box-shadow: 0 0 0 3px rgba(255, 152, 0, 0.1);
        }

        .form-help {
            font-size: 0.82rem;
            color: var(--tria-muted);
            line-height: 1.4;
        }

        .form-error {
            font-size: 0.85rem;
            color: var(--tria-red);
        }

        .form-submit {
            background: linear-gradient(135deg, var(--tria-red), var(--tria-orange));
            color: #ffffff;
            font-weight: 600;
            padding: 0.85rem 1.5rem;
            border-radius: 999px;
            border: none;
            font-size: 0.95rem;
            cursor: pointer;
            transition: transform 0.1s ease, box-shadow 0.2s ease;
            box-shadow: 0 8px 18px rgba(229, 57, 53, 0.25);
            margin-top: 0.5rem;
        }

        .form-submit:hover {
            background: linear-gradient(135deg, #c62828, #fb8c00);
            transform: translateY(-1px);
            box-shadow: 0 10px 24px rgba(229, 57, 53, 0.3);
        }

        .auth-footer {
            text-align: center;
            margin-top: 1.5rem;
            padding-top: 1.5rem;
            border-top: 1px solid var(--tria-border);
            font-size: 0.9rem;
            color: var(--tria-muted);
        }

        .auth-link {
            color: var(--tria-red);
            font-weight: 600;
        }

        .auth-link:hover {
            text-decoration: underline;
        }

        .password-requirements {
            background-color: var(--tria-orange-soft);
            border: 1px solid rgba(229, 57, 53, 0.2);
            border-radius: 0.5rem;
            padding: 0.75rem 1rem;
            margin-top: 0.5rem;
        }

        .password-requirements ul {
            margin: 0.5rem 0 0 0;
            padding-left: 1.25rem;
            font-size: 0.82rem;
            color: var(--tria-muted);
        }

        .password-requirements li {
            margin-bottom: 0.25rem;
        }

        @media (max-width: 600px) {
            .auth-card {
                padding: 2rem 1.5rem;
            }

            .auth-title {
                font-size: 1.5rem;
            }
        }

        /* Hide Django's default table layout */
        table {
            display: none;
        }
    </style>
</head>
<body>
    <nav class="navbar">
        <div class="nav-inner">
            <a href="{% url 'home' %}" class="nav-brand">
                <img src="https://i.ibb.co.com/fY9F3RwF/tria.png" alt="Tria logo" class="nav-logo" />
                <span class="nav-title">Tria</span>
            </a>
            <div class="nav-links">
                <a href="{% url 'home' %}" class="nav-link">Home</a>
                <a href="{% url 'about:about_page' %}" class="nav-link">About</a>
            </div>
        </div>
    </nav>

    <div class="auth-container">
        <div class="auth-card">
            <div class="auth-header">
                <div class="auth-badge">Bergabung dengan Tria</div>
                <h1 class="auth-title">Buat Akun Baru</h1>
                <p class="auth-subtitle">Daftar sekarang dan mulai belajar tarian tradisional Indonesia</p>
            </div>

            {% if messages %}
            <div class="messages">
                {% for message in messages %}
                <div class="message {{ message.tags }}">
                    {{ message }}
                </div>
                {% endfor %}
            </div>
            {% endif %}

            <form method="POST" action="" class="auth-form">
                {% csrf_token %}
                
                <div class="form-group">
                    <label for="{{ form.username.id_for_label }}" class="form-label">
                        Username
                    </label>
                    <input 
                        type="text" 
                        name="{{ form.username.name }}" 
                        id="{{ form.username.id_for_label }}"
                        class="form-input"
                        required
                        autofocus
                        maxlength="150"
                    />
                    {% if form.username.help_text %}
                    <span class="form-help">{{ form.username.help_text }}</span>
                    {% endif %}
                    {% if form.username.errors %}
                        {% for error in form.username.errors %}
                        <span class="form-error">{{ error }}</span>
                        {% endfor %}
                    {% endif %}
                </div>

                <div class="form-group">
                    <label for="{{ form.password1.id_for_label }}" class="form-label">
                        Password
                    </label>
                    <input 
                        type="password" 
                        name="{{ form.password1.name }}" 
                        id="{{ form.password1.id_for_label }}"
                        class="form-input"
                        required
                    />
                    {% if form.password1.errors %}
                        {% for error in form.password1.errors %}
                        <span class="form-error">{{ error }}</span>
                        {% endfor %}
                    {% endif %}
                </div>

                <div class="form-group">
                    <label for="{{ form.password2.id_for_label }}" class="form-label">
                        Konfirmasi Password
                    </label>
                    <input 
                        type="password" 
                        name="{{ form.password2.name }}" 
                        id="{{ form.password2.id_for_label }}"
                        class="form-input"
                        required
                    />
                    {% if form.password2.help_text %}
                    <span class="form-help">{{ form.password2.help_text }}</span>
                    {% endif %}
                    {% if form.password2.errors %}
                        {% for error in form.password2.errors %}
                        <span class="form-error">{{ error }}</span>
                        {% endfor %}
                    {% endif %}
                </div>

                <div class="password-requirements">
                    <strong style="color: var(--tria-red); font-size: 0.88rem;">Persyaratan Password:</strong>
                    <ul>
                        <li>Password harus minimal 8 karakter</li>
                        <li>Tidak boleh terlalu mirip dengan informasi pribadi</li>
                        <li>Tidak boleh menggunakan password yang terlalu umum</li>
                        <li>Tidak boleh sepenuhnya berisi angka</li>
                    </ul>
                </div>

                <button type="submit" class="form-submit">
                    Daftar
                </button>
            </form>

            <div class="auth-footer">
                Sudah punya akun? 
                <a href="{% url 'authentication:login' %}" class="auth-link">Masuk di sini</a>
            </div>
        </div>
    </div>

    <!-- Hidden table for Django form compatibility -->
    <div style="display: none;">
        {{ form.as_table }}
    </div>
</body>
</html>
```

### backend/Procfile

```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

### backend/main.py

```py
import os
import random
import json
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from openai import AsyncOpenAI

app = FastAPI()

# --- KONFIGURASI CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- SETUP OPENAI ---
# Kita ambil API KEY dari Environment Variable (Setting di Railway)
# Ini jauh lebih aman daripada menaruhnya langsung di kodingan.
client = AsyncOpenAI(
    api_key=os.environ.get("OPENAI_API_KEY") 
)

# --- ENDPOINT UTAMA ---
@app.api_route("/api/givescore", methods=["GET", "POST"])
async def give_score():
    try:
        # 1. Generate Fake Score (70 - 95)
        score = random.randint(70, 95)

        # 2. Tentukan jumlah feedback (5 - 7 poin)
        feedback_num = random.randint(5, 7)

        # 3. Minta OpenAI buatkan Feedback Unik
        # Kita suruh AI berperan sebagai pelatih tari
        prompt_text = (
            f"Berikan {feedback_num} poin masukan singkat (maksimal 10-15 kata per poin) "
            "untuk seorang penari tari tradisional Indonesia pemula setelah melakukan latihan. "
            "Variasikan komentar mengenai: keluwesan tangan, power/tenaga, ekspresi wajah, "
            "kuda-kuda kaki, dan ketepatan dengan musik. "
            "Berikan campuran pujian dan koreksi. "
            "Output hanya berupa daftar kalimat dipisahkan dengan baris baru (newline), tanpa penomoran."
        )

        response = await client.chat.completions.create(
            model="gpt-4o-mini", # Atau "gpt-3.5-turbo" agar lebih hemat
            messages=[
                {"role": "system", "content": "Kamu adalah instruktur tari profesional yang ramah namun teliti."},
                {"role": "user", "content": prompt_text}
            ],
            temperature=0.8, # Agar variasi kalimatnya tinggi (tidak monoton)
        )

        # 4. Parsing hasil dari OpenAI menjadi List
        raw_content = response.choices[0].message.content.strip()
        
        # Pisahkan berdasarkan baris baru dan bersihkan jika ada string kosong
        feedback_list = [line.strip("- ").strip() for line in raw_content.split('\n') if line.strip()]

        # Jaga-jaga kalau AI generate format aneh, kita potong sesuai feedback_num
        selected_feedback = feedback_list[:feedback_num]

        # 5. Return JSON
        return {
            "feedback_num": len(selected_feedback),
            "feedback": selected_feedback,
            "score": score
        }

    except Exception as e:
        print(f"Error: {e}")
        # Fallback jika OpenAI error/habis kuota, tetap return data dummy agar frontend tidak crash
        fallback_feedback = [
            "Gerakan tangan kamu sudah cukup luwes.",
            "Sinkronisasi dengan ketukan musik sangat pas.",
            "Perhatikan kuda-kuda kaki agar lebih kokoh.",
            "Ekspresi wajah perlu lebih menjiwai lagi.",
            "Power pada hentakan tangan perlu ditambah sedikit."
        ]
        return {
            "feedback_num": 5,
            "feedback": fallback_feedback,
            "score": random.randint(70, 85)
        }

@app.get("/")
def read_root():
    return {"status": "Server running with OpenAI integration."}
```

### backend/requirements.txt

```txt
fastapi
uvicorn
openai
```

### daftarsanggar/__init__.py

```py

```

### daftarsanggar/admin.py

```py
from django.contrib import admin
from .models import Sanggar, Review

# Opsi 1: Tampilan standar
# admin.site.register(Sanggar)
# admin.site.register(Review)

# Opsi 2: Tampilan lebih canggih (Inline Review di dalam Sanggar)
class ReviewInline(admin.TabularInline):
    model = Review
    extra = 1

@admin.register(Sanggar)
class SanggarAdmin(admin.ModelAdmin):
    list_display = ('sanggar_id', 'nama_sanggar', 'location', 'phone_number')
    search_fields = ('nama_sanggar', 'location')
    inlines = [ReviewInline] # Ini bikin kita bisa nambah review langsung di halaman edit sanggar

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'sanggar', 'comment')
```

### daftarsanggar/apps.py

```py
from django.apps import AppConfig


class DaftarsanggarConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "daftarsanggar"
```

### daftarsanggar/models.py

```py
from django.db import models

class Sanggar(models.Model):
    sanggar_id = models.CharField(max_length=10, unique=True, primary_key=True)
    nama_sanggar = models.CharField(max_length=200)
    
    
    image= models.URLField(max_length=200, blank=True, null=True) 
    
    
    phone_number = models.CharField(max_length=50, blank=True, null=True)
    location = models.TextField()
    email = models.EmailField(blank=True, null=True)
    description = models.TextField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nama_sanggar

    @property
    def wa_link(self):
        if not self.phone_number or self.phone_number == '-':
            return "#"
        
        clean_num = ''.join(filter(str.isdigit, self.phone_number))
        
        if not clean_num:
            return "#"

        if clean_num.startswith('0'):
            wa_num = '62' + clean_num[1:]
        elif clean_num.startswith('62'):
            wa_num = clean_num
        else:
            wa_num = '62' + clean_num 

        text = f"Halo {self.nama_sanggar}, saya ingin bertanya info pendaftaran."
        return f"https://wa.me/{wa_num}?text={text}"


class Review(models.Model):
    sanggar = models.ForeignKey(Sanggar, on_delete=models.CASCADE, related_name='reviews')
    user = models.CharField(max_length=100)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.sanggar.nama_sanggar}"
```

### daftarsanggar/tests.py

```py
from django.test import TestCase

# Create your tests here.
```

### daftarsanggar/urls.py

```py
# daftarsanggar/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('sanggar/<str:sanggar_id>/', views.detail, name='detail'),
    
]
```

### daftarsanggar/views.py

```py
from django.shortcuts import render
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Sanggar # Import model
import re


# Hardcoded sanggar data instead of relying on import_data.py
HARDCODED_SANGGARS = [
    {
        "sanggar_id": "ST001",
        "nama_sanggar": "Namarina Dance Academy",
        "image": "https://cdn.antaranews.com/cache/360x240/2021/12/05/65-Tahun-Namarina-Berkarya-051221-MRH-10.jpg",
        "phone_number": "(021) 8294777",
        "location": "Jl. Halimun No. 43, Guntur, Jakarta Selatan",
        "email": "info.namarina@gmail.com",
        "description": "Institusi pendidikan tari tertua di Indonesia (sejak 1956) yang fokus pada Tarian Tradisional, Jazz Dance, dan kebugaran.",
        "wa_link": "https://api.whatsapp.com/send/?phone=62810&text&type=phone_number&app_absent=0",
        "reviews": [
            {"user": "Andi Pratama", "comment": "Pengajar sangat profesional."}
        ]
    },
    {
        "sanggar_id": "ST002",
        "nama_sanggar": "Gigi Art of Dance",
        #"image": "daftarsanggar/img/gigiartofdance.png",
        "image": "https://cdn.grid.id/crop/0x0:0x0/700x465/photo/2023/12/21/_mg_9565jpg-20231221111126.jpg",
        "phone_number": "(021) 7399739",
        "location": "Jl. Radio Dalam Raya No. 191, Jakarta Selatan",
        "email": "info@gigiartofdance.id",
        "description": "Sanggar tari modern yang dinamis, terkenal dengan kelas Broadway, Hip Hop, dan Contemporary.",
        "wa_link": "https://api.whatsapp.com/send/?phone=62810&text&type=phone_number&app_absent=0",
        "reviews": [
            {"user": "Fajar Nugraha", "comment": "Koreografinya keren banget!"}
        ]
    },
    {
        "sanggar_id": "ST003",
        "nama_sanggar": "Sanggar Ayodya Pala",
        "image": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQOAQwcejFLv6NLsW9lwGipvLIONrzYP7MRFg&s",
        "phone_number": "(021) 7775678",
        "location": "Jl. Melati Raya No. 5, Depok Jaya, Kota Depok",
        "email": "ayodyapala@yahoo.com",
        "description": "Pusat kesenian yang sangat aktif melestarikan tari tradisional Jawa, Sunda, dan Bali di wilayah Depok.",
        "wa_link": "https://api.whatsapp.com/send/?phone=62810&text&type=phone_number&app_absent=0",
        "reviews": [
            {"user": "Agus Salim", "comment": "Tempat terbaik belajar tari tradisi."}
        ]
    },
    {
        "sanggar_id": "ST004",
        "nama_sanggar": "Marlupi Dance Academy",
        "image": "https://awsimages.detik.net.id/community/media/visual/2022/04/24/marlupi-dance-academy_43.jpeg?w=1200",
        "phone_number": "(021) 5656303",
        "location": "Green Ville Maisonette Blok FA No. 15, Jakarta Barat",
        "email": "admin@marlupi.com",
        "description": "Akademi tari berstandar internasional (Royal Academy of Dance) yang mencetak banyak balerina profesional.",
        "wa_link": "https://api.whatsapp.com/send/?phone=62810&text&type=phone_number&app_absent=0",
        "reviews": [
            {"user": "Citra Kirana", "comment": "Standar internasionalnya terasa."}
        ]
    },
    {
        "sanggar_id": "ST005",
        "nama_sanggar": "United Dance Works",
        "image": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcT2xjqcNb8zXIsEuRB9okyeFpZRP__XwCx2lQ&s",
        "phone_number": "+62 877-8017-7202",
        "location": "Jl. Bangka XI No. 3A-1, Kemang, Jakarta Selatan",
        "email": "info@uniteddanceworks.com",
        "description": "Basecamp bagi penari profesional dengan spesialisasi Showbiz, Hip Hop, dan tari komersial.",
        "wa_link": "https://api.whatsapp.com/send/?phone=62810&text&type=phone_number&app_absent=0",
        "reviews": [
            {"user": "Indra Bekti", "comment": "Keren untuk yang suka kontemporer."}
        ]
    },
    {
        "sanggar_id": "ST006",
        "nama_sanggar": "Sanggar Puspo Budoyo",
        "image": "https://www.puspobudoyo.com/wp-content/uploads/2025/01/hero-2.webp",
        "phone_number": "(021) 74713555",
        "location": "Jl. Elang Raya No.1, Ciputat, Tangerang Selatan",
        "email": "contact@puspobudoyo.com",
        "description": "Kampung seni budaya yang komprehensif, mengajarkan tari, musik gamelan, dan teater ketoprak.",
        "wa_link": "https://api.whatsapp.com/send/?phone=62810&text&type=phone_number&app_absent=0",
        "reviews": [
            {"user": "Nadine", "comment": "Suasana kampung seninya asri."}
        ]
    },
    {
        "sanggar_id": "ST007",
        "nama_sanggar": "EKI Dance Company",
        "image": "https://indonesiakaya.com/wp-content/uploads/2020/11/eki-dance-company-pentaskan-eki-update-41-broadwaynyaindonesia.jpg",
        "phone_number": "(021) 8312377",
        "location": "Jl. Padang No. 21, Manggarai, Jakarta Selatan",
        "email": "eki@ekidancecompany.com",
        "description": "Perusahaan tari profesional ternama yang memproduksi pertunjukan musikal dan tari kontemporer.",
        "wa_link": "https://api.whatsapp.com/send/?phone=62810&text&type=phone_number&app_absent=0",
        "reviews": [
            {"user": "Sule", "comment": "Karya-karyanya selalu out of the box."}
        ]
    },
    {
        "sanggar_id": "ST008",
        "nama_sanggar": "Sanggar Cipta Budaya",
        "image": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSij7DGPL0-nJRoBEIahDfkpntJ1qB2TDcnig&s",
        "phone_number": "0878-8077-6402",
        "location": "Jl. Taman Asri Lama No. 16, Tangerang",
        "email": "ciptaartdance@gmail.com",
        "description": "Menyediakan jasa pertunjukan tari adat Nusantara, kostum tari, dan pelatihan tari privat.",
        "wa_link": "https://api.whatsapp.com/send/?phone=62810&text&type=phone_number&app_absent=0",
        "reviews": [
            {"user": "Yuni Shara", "comment": "Tari Jaipongnya luwes."}
        ]
    },
    {
        "sanggar_id": "ST009",
        "nama_sanggar": "Forever Dance Center",
        "image": "https://i.ytimg.com/vi/pByOSHAVglI/maxresdefault.jpg",
        "phone_number": "0812-9642-0360",
        "location": "Jl. Pulomas Timur 2, Jakarta Timur",
        "email": "ForeverDanceCenter@gmail.com",
        "description": "Sekolah tari populer untuk anak-anak hingga dewasa dengan genre Tarian Tradisional, K-Pop, dan Hip Hop.",
        "wa_link": "https://api.whatsapp.com/send/?phone=62810&text&type=phone_number&app_absent=0",
        "reviews": [
            {"user": "Cinta Laura", "comment": "Dance cover K-Pop nya update."}
        ]
    },
    {
        "sanggar_id": "ST010",
        "nama_sanggar": "Kinarya GSP",
        "image": "https://www.whiteboardjournal.com/wp-content/themes/whiteboardjournal/media.php?src=https://www.whiteboardjournal.com/wp-content/uploads/2018/12/DSCF3490-748x499.jpg&w=750&h=500&zc=1&q=90",
        "phone_number": "0858-8419-3546",
        "location": "Jl. Wijaya I No. 381A, Jaksel",
        "email": "info@kinarya.id",
        "description": "Sanggar milik Guruh Soekarno Putra yang fokus pada tari kreasi baru bernuansa Indonesia.",
        "wa_link": "https://api.whatsapp.com/send/?phone=62810&text&type=phone_number&app_absent=0",
        "reviews": [
            {"user": "Hanggini", "comment": "Tari kreasi barunya unik."}
        ]
    },
    {
        "sanggar_id": "ST011",
        "nama_sanggar": "Steps Dance Academy",
        "image": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTc5qqI9gIpZ_ZJ34VHZAMIUK9GRefUU1JfWQ&s",
        "phone_number": "(021) 25554454",
        "location": "fX Sudirman 7th Floor, Jakarta Pusat",
        "email": "stepsdancefx@gmail.com",
        "description": "Studio tari modern di pusat kota yang menawarkan berbagai genre dari Jazz hingga Urban Dance.",
        "wa_link": "https://api.whatsapp.com/send/?phone=62810&text&type=phone_number&app_absent=0",
        "reviews": [
            {"user": "Raisa", "comment": "Lokasi strategis di mall."}
        ]
    },
    {
        "sanggar_id": "ST012",
        "nama_sanggar": "Sanggar Betawi Setu Babakan",
        "image": "https://cdn.antaranews.com/cache/1200x800/2025/07/16/IMG-20250714-WA0015.jpg",
        "phone_number": "(021) 78893258",
        "location": "Perkampungan Budaya Betawi Setu Babakan",
        "email": "betawi@setubabakan.or.id",
        "description": "Pusat pelatihan seni budaya Betawi asli (Lenong, Tari Topeng, Gambang Kromong).",
        "wa_link": "https://api.whatsapp.com/send/?phone=62810&text&type=phone_number&app_absent=0",
        "reviews": [
            {"user": "Reza Rahadian", "comment": "Melestarikan budaya Betawi asli."}
        ]
    },
    {
        "sanggar_id": "ST013",
        "nama_sanggar": "Sanggar Sumber Cipta",
        "image": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQqpuJP-yezqT3tgIRzA_--pDVl4YDKKsxVQQ&s",
        "phone_number": "(021) 7659876",
        "location": "Jl. Ciputat Raya No. 1, Pondok Pinang",
        "email": "info@ballet.id",
        "description": "Sekolah balet legendaris yang menggunakan metode Vaganova.",
        "wa_link": "https://api.whatsapp.com/send/?phone=62810&text&type=phone_number&app_absent=0",
        "reviews": [
            {"user": "Yuki Kato", "comment": "Postur tubuh jadi tegap."}
        ]
    },
    {
        "sanggar_id": "ST014",

        "nama_sanggar": "Sanggar Kinang Putra",
        "image": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQ-q5Bm1D-IcpCM642aYf6olNiF_xD3WP_HEg&s",
        "phone_number": "0813-8080-1234",
        "location": "Jl. Putri Tunggal, Cimanggis",
        "email": "kinangputra@yahoo.com",
        "description": "Sanggar bersejarah yang melestarikan Topeng Betawi Cisalak dan Tari Cokek.",
        "wa_link": "https://api.whatsapp.com/send/?phone=62810&text&type=phone_number&app_absent=0",
        "reviews": [
            {"user": "Chelsea Islan", "comment": "Sangat otentik tariannya."}
        ]
    },
    {
        "sanggar_id": "ST015",
        "nama_sanggar": "Gema Citra Nusantara",
        "image": "https://xposeindonesia.com/wp-content/uploads/2021/02/1f9e52f5766a7a5e24af756d4d3b3708_XL.jpg",
        "phone_number": "(021) 725 3573",
        "location": "Jl. Wolter Monginsidi No. 78, Jaksel",
        "email": "info@gcn-indonesia.com",
        "description": "Sanggar tari yang fokus pada promosi budaya Indonesia ke internasional melalui misi budaya.",
        "wa_link": "https://api.whatsapp.com/send/?phone=62810&text&type=phone_number&app_absent=0",
        "reviews": [
            {"user": "Hesti", "comment": "Sering diajak misi budaya."}
        ]
    },
    {
        "sanggar_id": "ST016",
        "nama_sanggar": "Interlude Dance Studio",
        "image": "https://pbs.twimg.com/media/BapUWc-CAAE_usn?format=jpg&name=small",
        "phone_number": "0877-7155-2016",
        "location": "BSD City, Tangerang Selatan",
        "email": "-",
        "description": "Studio tari modern di BSD menawarkan kelas K-Pop Cover, Hip Hop, dan Kids Dance.",
        "wa_link": "https://api.whatsapp.com/send/?phone=62810&text&type=phone_number&app_absent=0",
        "reviews": [
            {"user": "Cak Lontong", "comment": "Anak saya suka kelas K-pop nya."}
        ]
    },
    {
        "sanggar_id": "ST017",
        "nama_sanggar": "Genecela Dance Centre",
        "image": "https://assets.promediateknologi.id/crop/0x0:0x0/750x500/webp/photo/suarakarya/20191028110600IMG_20191028_092326.jpg",
        "phone_number": "(021) 58302528",
        "location": "Jl. Meruya Ilir No. 88, Jakarta Barat",
        "email": "gdc@genecela.com",
        "description": "Pusat pelatihan tari dengan kurikulum internasional untuk Jazz, Tap, dan Tarian Tradisional.",
        "wa_link": "https://api.whatsapp.com/send/?phone=62810&text&type=phone_number&app_absent=0",
        "reviews": [
            {"user": "Raditya Dika", "comment": "Tap dance jarang ada di tempat lain."}
        ]
    },
    {
        "sanggar_id": "ST018",
        "nama_sanggar": "Sanggar Bintang Asti",
        "image": "https://komunitasondelondeljakarta.com/wp-content/uploads/2019/07/WhatsApp-Image-2019-07-14-at-00.12.12-300x225.jpeg",
        "phone_number": "0857-1600-7521",
        "location": "Pulo Gadung, Jakarta Timur",
        "email": "-",
        "description": "Sanggar seni Betawi yang membina anak muda dengan ondel-ondel dan tari.",
        "wa_link": "https://api.whatsapp.com/send/?phone=62810&text&type=phone_number&app_absent=0",
        "reviews": [
            {"user": "Wika Salim", "comment": "Komunitasnya solid."}
        ]
    },
    {
        "sanggar_id": "ST019",
        "nama_sanggar": "Sanggar Ananda Kawula Muda",
        "image": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQftYW68CJoXAyHdiKAbr8wqzkWDLQL4rBzig&s",
        "phone_number": "0819-7761-1919",
        "location": "Jl. Dr. Saharjo No. 45, Manggarai",
        "email": "akawulamuda@gmail.com",
        "description": "Sanggar legendaris pimpinan Aditya Gumay, fokus akting dan tari.",
        "wa_link": "https://api.whatsapp.com/send/?phone=62810&text&type=phone_number&app_absent=0",
        "reviews": [
            {"user": "Melly Goeslaw", "comment": "Paket komplit seni peran dan tari."}
        ]
    },
    {
        "sanggar_id": "STO20",
        "nama_sanggar": "Sanggar Ratna Sari",
        "image": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRAQW7ssArfFoUVgUcUi2QOwaPwh-VPi6qWhA&s",
        "phone_number": "-",
        "location": "Cimanggis, Depok",
        "email": "-",
        "description": "Salah satu sanggar Topeng Betawi tertua kelolaan keluarga H. Bokir.",
        "wa_link": "https://api.whatsapp.com/send/?phone=62810&text&type=phone_number&app_absent=0",
        "reviews": [
            {"user": "Haringga", "comment": "Sangat otentik gaya topengnya."}
        ]
    }
]

@login_required
def index(request):
    context = {
        'sanggars': HARDCODED_SANGGARS
    }
    return render(request, 'daftarsanggar/index.html', context)

@login_required
def detail(request, sanggar_id):
    # Cari sanggar berdasarkan ID
    sanggar_data = next((s for s in HARDCODED_SANGGARS if s["sanggar_id"] == sanggar_id), None)
    
    if not sanggar_data:
        raise Http404("Sanggar not found")
    
    # PENTING: Kita copy object-nya agar tidak mengubah data global asli secara permanen (best practice)
    sanggar = sanggar_data.copy()
    
    # --- LOGIC PERBAIKAN WA ---
    # Ambil nomor telepon dari data
    raw_phone = sanggar.get('phone_number', '')
    
    # Bersihkan nomor menggunakan helper function di atas
    clean_phone = format_whatsapp_number(raw_phone)
    
    if clean_phone:
        # Generate URL WhatsApp yang benar secara dinamis
        # Menggunakan format wa.me yang lebih ringkas atau api.whatsapp.com
        text_msg = "Halo, saya melihat profil sanggar Anda di website dan ingin bertanya info lebih lanjut."
        sanggar['wa_link'] = f"https://api.whatsapp.com/send/?phone={clean_phone}&text={text_msg}"
    else:
        # Jika nomor tidak valid (misal "-"), kosongkan wa_link agar tombol jadi disabled di HTML
        sanggar['wa_link'] = None

    context = {
        'sanggar': sanggar,
    }
    return render(request, 'daftarsanggar/detail.html', context)
    
def format_whatsapp_number(phone_raw):
    # 1. Jika data kosong atau "-", return None
    if not phone_raw or phone_raw == "-":
        return None
    
    # 2. Hapus semua karakter yang BUKAN angka (hapus spasi, -, (), +)
    clean_number = re.sub(r'\D', '', phone_raw)
    
    # 3. Ubah format 0 di depan menjadi 62 (Kode Negara Indonesia)
    if clean_number.startswith('0'):
        clean_number = '62' + clean_number[1:]
    
    # 4. Validasi panjang nomor (nomor HP/Telp Indonesia minimal ~9-10 digit)
    if len(clean_number) < 9:
        return None
        
    return clean_number
```

### daftarsanggar/migrations/0001_initial.py

```py
# Generated by Django 5.2.8 on 2025-11-23 08:16

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Sanggar",
            fields=[
                (
                    "sanggar_id",
                    models.CharField(
                        max_length=10, primary_key=True, serialize=False, unique=True
                    ),
                ),
                ("nama_sanggar", models.CharField(max_length=200)),
                (
                    "phone_number",
                    models.CharField(blank=True, max_length=50, null=True),
                ),
                ("location", models.TextField()),
                ("email", models.EmailField(blank=True, max_length=254, null=True)),
                ("description", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="Review",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("user", models.CharField(max_length=100)),
                ("comment", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "sanggar",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="reviews",
                        to="daftarsanggar.sanggar",
                    ),
                ),
            ],
        ),
    ]
```

### daftarsanggar/migrations/0002_sanggar_image_url.py

```py
# Generated by Django 5.2.8 on 2025-11-23 15:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("daftarsanggar", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="sanggar",
            name="image_url",
            field=models.URLField(blank=True, max_length=500, null=True),
        ),
    ]
```

### daftarsanggar/migrations/0003_remove_sanggar_image_url_sanggar_image.py

```py
# Generated by Django 5.2.8 on 2025-11-23 16:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("daftarsanggar", "0002_sanggar_image_url"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="sanggar",
            name="image_url",
        ),
        migrations.AddField(
            model_name="sanggar",
            name="image",
            field=models.URLField(blank=True, null=True),
        ),
    ]
```

### daftarsanggar/migrations/__init__.py

```py

```

### daftarsanggar/templates/daftarsanggar/base.html

```html
{% load static %}
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Tria - Belajar Tarian Tradisional Indonesia</title>
    <link rel="icon" type="image/png" href="https://i.ibb.co.com/fY9F3RwF/tria.png" />
    <link rel="shortcut icon" type="image/png" href="https://i.ibb.co.com/fY9F3RwF/tria.png" />
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet" />
    <style>
        :root {
            --tria-red: #e53935;
            --tria-orange: #ff9800;
            --tria-orange-soft: #fff3e0;
            --tria-border: #f0f0f0;
            --tria-text: #222222;
            --tria-muted: #555555;
        }
    
        /* NAVBAR ------------------------------------------------------ */
        
        .navbar {
            background-color: #ffffff;
            border-bottom: 1px solid var(--tria-border);
            position: sticky;
            top: 0;
            z-index: 50;
        }
    
        .nav-inner {
            max-width: 1100px;
            margin: 0 auto;
            padding: 0.75rem 1.25rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
        }
    
        .nav-brand {
            display: flex;
            align-items: center;
            gap: 0.6rem;
        }
    
        .nav-logo {
            height: 36px;
            width: 36px;
            object-fit: contain;
        }
    
        .nav-title {
            font-weight: 700;
            letter-spacing: 0.03em;
            font-size: 1.1rem;
        }
    
        .nav-links {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            font-size: 0.95rem;
        }
    
        .nav-link {
            padding: 0.4rem 0.75rem;
            border-radius: 999px;
            transition: background-color 0.2s ease, color 0.2s ease, transform 0.1s ease;
        }
    
        .nav-link:hover {
            background-color: var(--tria-orange-soft);
            color: var(--tria-red);
            transform: translateY(-1px);
        }
    
        .nav-cta {
            background: linear-gradient(135deg, var(--tria-red), var(--tria-orange));
            color: #ffffff !important;
            font-weight: 600;
        }
    
        .nav-cta:hover {
            background: linear-gradient(135deg, #c62828, #fb8c00);
        }
    </style>
    
</head>
<body class="bg-white text-gray-800 min-h-screen flex flex-col">

    {% include "partials/navbar.html" %}

    <main class="flex-grow container mx-auto px-6 py-12 max-w-7xl">
        {% block content %}{% endblock %}
    </main>

    <footer class="bg-white border-t border-gray-100 text-center py-8 text-sm text-gray-500">
        <p>&copy; 2025 Tria Project. All rights reserved.</p>
    </footer>

</body>
</html>
```

### daftarsanggar/templates/daftarsanggar/detail.html

```html
{% extends 'daftarsanggar/base.html' %}
{% load static %}

{% block content %}

<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');

    :root {
        --primary-orange: #FF8C00; /* Warna aksen utama */
        --primary-red: #E53935;
        --bg-color: #FAFAFA;
        --surface-color: #FFFFFF;
        --text-dark: #1F2937;
        --text-muted: #6B7280;
        --border-color: #E5E7EB;
    }

    body {
        font-family: 'Poppins', sans-serif;
        color: var(--text-dark);
        background-color: var(--bg-color);
    }

    /* --- LAYOUT UTAMA --- */
    .split-wrapper {
        display: flex;
        width: 100%;
        height: calc(100vh - 70px); /* Asumsi navbar 70px */
        overflow: hidden;
        background: var(--surface-color);
    }

    /* --- BAGIAN KIRI: GAMBAR (DESAIN BARU TANPA BADGE) --- */
    .image-panel {
        flex: 1.3; /* Gambar sedikit lebih lebar */
        position: relative;
        overflow: hidden;
        background-color: #eee;
        z-index: 10; /* Agar bayangan berada di atas panel kanan */
        
        /* --- KUNCI DESAIN BARU DI SINI --- */
        /* 1. Bingkai Aksen Asimetris di kanan saja */
        border-right: 8px solid var(--primary-orange);
        
        /* 2. Bayangan dalam yang "mengangkat" gambar dari halaman */
        /* Offset horizontal, vertical, blur, spread, color */
        box-shadow: 15px 0 35px -5px rgba(0, 0, 0, 0.2);
    }

    .image-panel img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        /* Efek zoom halus saat hover */
        transition: transform 0.7s cubic-bezier(0.25, 0.46, 0.45, 0.94);
    }
    
    .image-panel:hover img {
        transform: scale(1.04);
    }

    /* Overlay gradasi dihilangkan agar warna foto lebih 'pop' keluar
       Jika ingin dipakai lagi, uncomment bagian di bawah ini: */
    /* .image-overlay {
        position: absolute; inset: 0;
        background: linear-gradient(to top, rgba(0,0,0,0.4) 0%, transparent 50%);
        pointer-events: none;
    } 
    */

    /* --- BAGIAN KANAN: KONTEN --- */
    .content-panel {
        flex: 1;
        padding: 3.5rem 3rem; /* Padding sedikit disesuaikan */
        overflow-y: auto;
        background: var(--surface-color);
        display: flex;
        flex-direction: column;
        position: relative;
        z-index: 1;
    }

    /* Scrollbar Cantik */
    .content-panel::-webkit-scrollbar { width: 6px; }
    .content-panel::-webkit-scrollbar-track { background: transparent; }
    .content-panel::-webkit-scrollbar-thumb { background-color: #ccc; border-radius: 20px; }

    /* Breadcrumb */
    .back-link {
        display: inline-flex;
        align-items: center;
        text-decoration: none;
        color: var(--text-muted);
        font-size: 0.85rem;
        margin-bottom: 2rem;
        font-weight: 500;
        transition: color 0.2s;
    }
    .back-link:hover { color: var(--primary-orange); }
    .back-link i { margin-right: 8px; }

    /* Typography */
    .sanggar-title {
        font-size: 2.5rem;
        font-weight: 800; /* Lebih tebal */
        margin: 0;
        color: var(--text-dark);
        line-height: 1.1;
        letter-spacing: -0.5px;
    }

    .sanggar-tagline {
        font-size: 1.05rem;
        color: var(--text-muted);
        margin-top: 0.75rem;
        margin-bottom: 2.5rem;
        display: block;
        font-weight: 400;
    }

    /* Section Styles */
    .section-title {
        font-size: 1.1rem;
        font-weight: 700;
        margin-bottom: 1.2rem;
        color: var(--text-dark);
        display: flex;
        align-items: center;
    }
    
    .sanggar-description {
        font-size: 1rem;
        line-height: 1.8;
        color: #4B5563;
        margin-bottom: 3rem;
        text-align: justify;
    }

    /* Contact Card - Sedikit lebih minimalis */
    .contact-card {
        background: #fff;
        border: 1px solid #F3F4F6;
        box-shadow: 0 10px 25px -5px rgba(0,0,0,0.05);
        padding: 2rem;
        border-radius: 16px;
        margin-bottom: 3.5rem;
    }
    .contact-item { display: flex; align-items: flex-start; margin-bottom: 1.2rem; }
    .icon-box {
        width: 40px; height: 40px;
        background: #FFF3E0; color: var(--primary-orange);
        border-radius: 10px; display: flex; align-items: center; justify-content: center;
        font-size: 1.1rem; margin-right: 15px; flex-shrink: 0;
    }
    .contact-text { font-size: 0.95rem; color: var(--text-dark); margin-top: 8px; font-weight: 500; }

    /* WhatsApp Button */
    .wa-btn {
        display: flex; align-items: center; justify-content: center; width: 100%;
        background: #25D366; color: white; padding: 1rem; border-radius: 12px;
        font-weight: 700; text-decoration: none; margin-top: 2rem;
        box-shadow: 0 4px 15px rgba(37, 211, 102, 0.25); transition: all 0.2s ease; font-size: 1rem;
    }
    .wa-btn:hover { background: #20BD5A; transform: translateY(-3px); box-shadow: 0 8px 20px rgba(37, 211, 102, 0.35); color: white; }
    .wa-disabled { background: #E5E7EB; color: #9CA3AF; cursor: not-allowed; box-shadow: none; }
    .wa-disabled:hover { transform: none; background: #E5E7EB; color: #9CA3AF; }

    /* Reviews */
    .review-grid { display: grid; gap: 1rem; }
    .review-card {
        background: #F9FAFB; border-radius: 12px; padding: 1.5rem;
        border: 1px solid #eee; transition: all 0.2s;
    }
    .review-card:hover { border-color: var(--primary-orange); background: #fff; box-shadow: 0 5px 15px rgba(0,0,0,0.05); }
    .reviewer-info { display: flex; align-items: center; margin-bottom: 1rem; }
    .avatar-circle {
        width: 36px; height: 36px; background: var(--primary-orange);
        color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center;
        font-weight: 700; font-size: 1rem; margin-right: 12px;
        box-shadow: 0 2px 8px rgba(255, 140, 0, 0.3);
    }
    .reviewer-name { font-size: 1rem; font-weight: 700; color: var(--text-dark); }
    .review-comment { font-size: 0.95rem; color: var(--text-muted); font-style: italic; line-height: 1.6; }

    /* --- RESPONSIVE MOBILE --- */
    @media (max-width: 900px) {
        .split-wrapper { flex-direction: column; height: auto; overflow: visible; }
        .image-panel {
            height: 350px; flex: none;
            /* Di mobile, border pindah ke bawah */
            border-right: none;
            border-bottom: 8px solid var(--primary-orange);
            box-shadow: 0 10px 25px -5px rgba(0,0,0,0.2);
        }
        .content-panel { padding: 2.5rem 1.5rem; }
        .sanggar-title { font-size: 2rem; }
    }
</style>

<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">

<div class="split-wrapper">

    <div class="image-panel">
        <img
            src="{% if 'http' in sanggar.image %}
                    {{ sanggar.image }}
                {% else %}
                    {% static sanggar.image %}
                {% endif %}"
            alt="{{ sanggar.nama_sanggar }}"
            onerror="this.src='https://via.placeholder.com/800x600?text=No+Image'"
        />
        </div>

    <div class="content-panel">

        <a href="javascript:history.back()" class="back-link">
            <i class="fas fa-arrow-left"></i> Kembali
        </a>

        <header>
            <h1 class="sanggar-title">{{ sanggar.nama_sanggar }}</h1>
            <span class="sanggar-tagline">Profil Lengkap & Informasi Sewa Studio</span>
        </header>

        <section>
            <h3 class="section-title">Tentang Sanggar</h3>
            <p class="sanggar-description">{{ sanggar.description }}</p>
        </section>

        <section class="contact-card">
            <h3 class="section-title" style="margin-bottom: 1.5rem;">Lokasi & Kontak</h3>
            <div class="contact-item">
                <div class="icon-box"><i class="fas fa-map-marker-alt"></i></div>
                <div class="contact-text">{{ sanggar.location }}</div>
            </div>
            <div class="contact-item">
                <div class="icon-box"><i class="fas fa-phone"></i></div>
                <div class="contact-text">{{ sanggar.phone_number }}</div>
            </div>
            <div class="contact-item">
                <div class="icon-box"><i class="fas fa-envelope"></i></div>
                <div class="contact-text">{{ sanggar.email }}</div>
            </div>
            {% if sanggar.wa_link %}
                <a href="{{ sanggar.wa_link }}" target="_blank" class="wa-btn">
                    <i class="fab fa-whatsapp"></i> Hubungi via WhatsApp
                </a>
            {% else %}
                <div class="wa-btn wa-disabled">
                    <i class="fab fa-whatsapp"></i> WhatsApp Tidak Tersedia
                </div>
            {% endif %}
        </section>

        <section>
            <h3 class="section-title">Ulasan Pengunjung</h3>
            <div class="review-grid">
                {% for review in sanggar.reviews %}
                <div class="review-card">
                    <div class="reviewer-info">
                        <div class="avatar-circle">{{ review.user|slice:":1" }}</div>
                        <div class="reviewer-name">{{ review.user }}</div>
                    </div>
                    <div class="review-comment">“{{ review.comment }}”</div>
                </div>
                {% empty %}
                <p style="color: #999; font-size: 0.95rem; font-style: italic; padding: 1rem;">Belum ada ulasan untuk sanggar ini.</p>
                {% endfor %}
            </div>
        </section>

    </div>
</div>

{% endblock %}
```

### daftarsanggar/templates/daftarsanggar/index.html

```html
{% extends 'daftarsanggar/base.html' %}
{% load static %}
{% block content %}
<div class="text-center max-w-2xl mx-auto mb-12">
    <h1 class="text-3xl md:text-4xl font-bold text-gray-900 mb-4">Sanggar Tari Indonesia</h1>
    <p class="text-gray-500 leading-relaxed">
        Pilih sanggar tari terbaik untuk mengembangkan bakatmu. 
        Setiap sanggar memiliki spesialisasi dan pengajar profesional.
    </p>
</div>

<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
    {% for sanggar in sanggars %}
    
    <div class="bg-white rounded-2xl border border-gray-100 shadow-sm hover:shadow-xl transition-all duration-300 flex flex-col h-full overflow-hidden group">
        
        <div class="h-48 bg-gray-200 overflow-hidden relative">
            <img 
                src="{% if 'http' in sanggar.image %}
                        {{ sanggar.image }}
                    {% else %}
                        {% static sanggar.image %}
                    {% endif %}"
                alt="{{ sanggar.nama_sanggar }}"
                class="w-full h-full object-cover"
                onerror="this.src='https://source.unsplash.com/random/400x300?dance';"
            >
            <div class="absolute inset-0 bg-black bg-opacity-10 group-hover:bg-opacity-0 transition"></div>
        </div>
        
        <div class="p-5 flex flex-col flex-grow">
            <h2 class="text-lg font-bold text-gray-900 mb-2 leading-tight">
                {{ sanggar.nama_sanggar }}
            </h2>
            
            <p class="text-sm text-gray-500 mb-6 line-clamp-3 flex-grow">
                {{ sanggar.description }}
            </p>
            
            <a href="{% url 'daftarsanggar:detail' sanggar.sanggar_id %}" class="inline-block text-center w-full bg-gradient-to-r from-orange-500 to-red-500 text-white text-sm font-semibold py-2.5 px-6 rounded-full shadow-md hover:shadow-lg hover:from-orange-600 hover:to-red-600 transition-all duration-300 transform hover:-translate-y-0.5">
                Lihat Detail
            </a>
        </div>
    </div>
    {% endfor %}
</div>
{% endblock %}
```

### dances/__init__.py

```py

```

### dances/admin.py

```py
from django.contrib import admin

# Register your models here.
```

### dances/apps.py

```py
from django.apps import AppConfig


class DancesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "dances"
```

### dances/models.py

```py
from django.db import models

# Create your models here.
```

### dances/tests.py

```py
from django.test import TestCase

# Create your tests here.
```

### dances/urls.py

```py
from django.urls import path
from . import views

app_name = 'dances'

urlpatterns = [
    path('', views.dance_list, name='dance_list'),
    path('<int:dance_id>/', views.dance_detail, name='dance_detail'),
    path('<int:dance_id>/tutorial/', views.dance_tutorial, name='dance_tutorial'),
    path('<int:dance_id>/assessment/', views.dance_assessment, name='dance_assessment'),
    path('<int:dance_id>/result/', views.dance_result, name='dance_result'),
]
```

### dances/views.py

```py
from django.shortcuts import render
from django.http import Http404
from django.contrib.auth.decorators import login_required
import random

def calculate_difficulty(duration_seconds):
    """Calculate difficulty level based on duration in seconds"""
    if duration_seconds < 240:  # Under 4 minutes
        return "Mudah"
    elif duration_seconds <= 480:  # 4-8 minutes
        return "Menengah"
    else:  # Above 8 minutes
        return "Susah"

def format_duration(seconds):
    """Format seconds to mm:ss format"""
    mins = seconds // 60
    secs = seconds % 60
    return f"{mins}:{secs:02d}"

# Updated list of 10 Indonesian dances with images and youtube placeholders
DANCES = [
    {
        "id": 1,
        "name": "Tari Kecak",
        "description": "Tari Kecak adalah tari tradisional Bali yang berpusat pada paduan suara pria yang mengeluarkan suara 'cak'.",
        "gerakan": ["Berdiri tegap, kaki dibuka selebar bahu, tangan kanan memegang ujung selendang di pinggang kanan, tangan kiri di pinggang kiri. Hitungan 1–8: ayunkan pinggul dan badan sedikit miring ke kanan-kiri secara lembut (lenggang), sambil kaki kanan melangkah kecil ke samping kanan lalu rapat lagi, kaki kiri menyusul ke samping kiri lalu rapat lagi. Ulangi 2 kali (16 hitungan) dengan senyum dan kepala sedikit mengangguk mengikuti arah lenggangan.",

"Mulai dari posisi menghadap depan. Hitungan 1–4: kaki kanan melangkah ke depan sedikit serong kanan, tangan kanan mengangkat selendang setinggi dada, tangan kiri membuka ke samping kiri sejajar bahu. Hitungan 5–8: putar badan pelan ke kiri (setengah lingkaran), kaki kiri menyusul rapat, selendang dikibas lembut ke arah luar. Ulangi pola yang sama ke arah berlawanan: langkah kaki kiri serong depan kiri, tangan kiri angkat selendang, putar badan ke kanan, selendang dikibas lagi (total 16 hitungan).",

"Dari posisi menghadap depan, lakukan langkah silang. Hitungan 1–4: kaki kanan menyilang di depan kaki kiri, lalu kaki kiri melangkah membuka ke samping kiri, tubuh sedikit condong mengikuti arah kaki. Tangan berayun silang di depan badan (seperti mengiris lembut udara) sambil memegang selendang. Hitungan 5–8: ganti, kaki kiri menyilang di depan kaki kanan lalu membuka ke samping kanan, tangan berayun kembali dengan pola yang sama. Ulangi 2 kali (16 hitungan) sambil jaga gerakan tetap halus dan lentur.",

"Gerakan penutup: dari posisi terakhir, rapikan langkah hingga kedua kaki rapat menghadap penonton. Hitungan 1–4: kedua tangan membawa selendang ke depan dada, siku sedikit menekuk, kepala menunduk pelan sebagai salam. Hitungan 5–8: buka tangan ke samping dengan selendang terbentang lembut, dada dibuka, pandangan ke depan sambil tersenyum. Ulangi salam satu kali lagi jika perlu, lalu tahan pose akhir beberapa detik sebelum benar-benar selesai."],
        "youtube_id": "sGX_XGdE7eo",
        "image_url": "https://momopururu.com/wp-content/uploads/2022/06/20211218171844_IMG_8553-01-01-scaled-1024x768.jpeg",
        "asal_daerah": "Bali",
        "durasi_video": 475,  # 7:55 in seconds
        "difficulty": "Menengah"
    },
    {
        "id": 2,
        "name": "Tari Janger",
        "description": "Tari Janger adalah tari tradisional dari Bali yang menampilkan gerakan dinamis dan ceria.",
        "gerakan": ["Berdiri tegap, kaki dibuka selebar bahu, tangan kanan memegang ujung selendang di pinggang kanan, tangan kiri di pinggang kiri. Hitungan 1–8: ayunkan pinggul dan badan sedikit miring ke kanan-kiri secara lembut (lenggang), sambil kaki kanan melangkah kecil ke samping kanan lalu rapat lagi, kaki kiri menyusul ke samping kiri lalu rapat lagi. Ulangi 2 kali (16 hitungan) dengan senyum dan kepala sedikit mengangguk mengikuti arah lenggangan.",

"Mulai dari posisi menghadap depan. Hitungan 1–4: kaki kanan melangkah ke depan sedikit serong kanan, tangan kanan mengangkat selendang setinggi dada, tangan kiri membuka ke samping kiri sejajar bahu. Hitungan 5–8: putar badan pelan ke kiri (setengah lingkaran), kaki kiri menyusul rapat, selendang dikibas lembut ke arah luar. Ulangi pola yang sama ke arah berlawanan: langkah kaki kiri serong depan kiri, tangan kiri angkat selendang, putar badan ke kanan, selendang dikibas lagi (total 16 hitungan).",

"Dari posisi menghadap depan, lakukan langkah silang. Hitungan 1–4: kaki kanan menyilang di depan kaki kiri, lalu kaki kiri melangkah membuka ke samping kiri, tubuh sedikit condong mengikuti arah kaki. Tangan berayun silang di depan badan (seperti mengiris lembut udara) sambil memegang selendang. Hitungan 5–8: ganti, kaki kiri menyilang di depan kaki kanan lalu membuka ke samping kanan, tangan berayun kembali dengan pola yang sama. Ulangi 2 kali (16 hitungan) sambil jaga gerakan tetap halus dan lentur.",

"Gerakan penutup: dari posisi terakhir, rapikan langkah hingga kedua kaki rapat menghadap penonton. Hitungan 1–4: kedua tangan membawa selendang ke depan dada, siku sedikit menekuk, kepala menunduk pelan sebagai salam. Hitungan 5–8: buka tangan ke samping dengan selendang terbentang lembut, dada dibuka, pandangan ke depan sambil tersenyum. Ulangi salam satu kali lagi jika perlu, lalu tahan pose akhir beberapa detik sebelum benar-benar selesai."],
        "youtube_id": "3ka7bd-ECsI",
        "image_url": "https://img.antarafoto.com/cache/1200x800/2021/07/01/pagelaran-tari-janger-muda-mudi-bali-uq4u-dom.webp",
        "asal_daerah": "Bali",
        "durasi_video": 173,  # 2:53 in seconds
        "difficulty": "Mudah"
    },
    {
        "id": 3,
        "name": "Tari Bungong Jeumpa",
        "description": "Tari Bungong Jeumpa adalah tari tradisional Aceh yang melambangkan keindahan bunga Jeumpa.",
        "gerakan": ["Berdiri tegap, kaki dibuka selebar bahu, tangan kanan memegang ujung selendang di pinggang kanan, tangan kiri di pinggang kiri. Hitungan 1–8: ayunkan pinggul dan badan sedikit miring ke kanan-kiri secara lembut (lenggang), sambil kaki kanan melangkah kecil ke samping kanan lalu rapat lagi, kaki kiri menyusul ke samping kiri lalu rapat lagi. Ulangi 2 kali (16 hitungan) dengan senyum dan kepala sedikit mengangguk mengikuti arah lenggangan.",

"Mulai dari posisi menghadap depan. Hitungan 1–4: kaki kanan melangkah ke depan sedikit serong kanan, tangan kanan mengangkat selendang setinggi dada, tangan kiri membuka ke samping kiri sejajar bahu. Hitungan 5–8: putar badan pelan ke kiri (setengah lingkaran), kaki kiri menyusul rapat, selendang dikibas lembut ke arah luar. Ulangi pola yang sama ke arah berlawanan: langkah kaki kiri serong depan kiri, tangan kiri angkat selendang, putar badan ke kanan, selendang dikibas lagi (total 16 hitungan).",

"Dari posisi menghadap depan, lakukan langkah silang. Hitungan 1–4: kaki kanan menyilang di depan kaki kiri, lalu kaki kiri melangkah membuka ke samping kiri, tubuh sedikit condong mengikuti arah kaki. Tangan berayun silang di depan badan (seperti mengiris lembut udara) sambil memegang selendang. Hitungan 5–8: ganti, kaki kiri menyilang di depan kaki kanan lalu membuka ke samping kanan, tangan berayun kembali dengan pola yang sama. Ulangi 2 kali (16 hitungan) sambil jaga gerakan tetap halus dan lentur.",

"Gerakan penutup: dari posisi terakhir, rapikan langkah hingga kedua kaki rapat menghadap penonton. Hitungan 1–4: kedua tangan membawa selendang ke depan dada, siku sedikit menekuk, kepala menunduk pelan sebagai salam. Hitungan 5–8: buka tangan ke samping dengan selendang terbentang lembut, dada dibuka, pandangan ke depan sambil tersenyum. Ulangi salam satu kali lagi jika perlu, lalu tahan pose akhir beberapa detik sebelum benar-benar selesai."],
        "youtube_id": "W3PRdCxocM0",
        "image_url": "https://www.kelaspintar.id/_next/image?url=https%3A%2F%2Fblog2.kelaspintar.id%2Fblog%2Fwp-content%2Fuploads%2F2021%2F12%2Ftari-bungong-jeumpa.jpg&w=3840&q=75",
        "asal_daerah": "Aceh",
        "durasi_video": 210,  # 3:30 in seconds
        "difficulty": "Mudah"
    },
    {
        "id": 4,
        "name": "Tari Lenggang Nyai",
        "description": "Tari Lenggang Nyai adalah tari dari Betawi yang menggambarkan gerakan wanita dengan anggun.",
        "gerakan": ["Berdiri tegap, kaki dibuka selebar bahu, tangan kanan memegang ujung selendang di pinggang kanan, tangan kiri di pinggang kiri. Hitungan 1–8: ayunkan pinggul dan badan sedikit miring ke kanan-kiri secara lembut (lenggang), sambil kaki kanan melangkah kecil ke samping kanan lalu rapat lagi, kaki kiri menyusul ke samping kiri lalu rapat lagi. Ulangi 2 kali (16 hitungan) dengan senyum dan kepala sedikit mengangguk mengikuti arah lenggangan.",

"Mulai dari posisi menghadap depan. Hitungan 1–4: kaki kanan melangkah ke depan sedikit serong kanan, tangan kanan mengangkat selendang setinggi dada, tangan kiri membuka ke samping kiri sejajar bahu. Hitungan 5–8: putar badan pelan ke kiri (setengah lingkaran), kaki kiri menyusul rapat, selendang dikibas lembut ke arah luar. Ulangi pola yang sama ke arah berlawanan: langkah kaki kiri serong depan kiri, tangan kiri angkat selendang, putar badan ke kanan, selendang dikibas lagi (total 16 hitungan).",

"Dari posisi menghadap depan, lakukan langkah silang. Hitungan 1–4: kaki kanan menyilang di depan kaki kiri, lalu kaki kiri melangkah membuka ke samping kiri, tubuh sedikit condong mengikuti arah kaki. Tangan berayun silang di depan badan (seperti mengiris lembut udara) sambil memegang selendang. Hitungan 5–8: ganti, kaki kiri menyilang di depan kaki kanan lalu membuka ke samping kanan, tangan berayun kembali dengan pola yang sama. Ulangi 2 kali (16 hitungan) sambil jaga gerakan tetap halus dan lentur.",

"Gerakan penutup: dari posisi terakhir, rapikan langkah hingga kedua kaki rapat menghadap penonton. Hitungan 1–4: kedua tangan membawa selendang ke depan dada, siku sedikit menekuk, kepala menunduk pelan sebagai salam. Hitungan 5–8: buka tangan ke samping dengan selendang terbentang lembut, dada dibuka, pandangan ke depan sambil tersenyum. Ulangi salam satu kali lagi jika perlu, lalu tahan pose akhir beberapa detik sebelum benar-benar selesai."],
        "youtube_id": "U1ycqGXJ1fI",
        "image_url": "https://i.ibb.co.com/39BkHzbw/Screenshot-2025-11-27-at-00-23-13.png",
        "asal_daerah": "Betawi",
        "durasi_video": 264,  # 4:24 in seconds
        "difficulty": "Menengah"
    },
    {
        "id": 5,
        "name": "Tari Piring",
        "description": "Tari Piring adalah tarian tradisional Minangkabau yang menggunakan piring sebagai properti.",
        "gerakan": ["Berdiri tegap, kaki dibuka selebar bahu, tangan kanan memegang ujung selendang di pinggang kanan, tangan kiri di pinggang kiri. Hitungan 1–8: ayunkan pinggul dan badan sedikit miring ke kanan-kiri secara lembut (lenggang), sambil kaki kanan melangkah kecil ke samping kanan lalu rapat lagi, kaki kiri menyusul ke samping kiri lalu rapat lagi. Ulangi 2 kali (16 hitungan) dengan senyum dan kepala sedikit mengangguk mengikuti arah lenggangan.",

"Mulai dari posisi menghadap depan. Hitungan 1–4: kaki kanan melangkah ke depan sedikit serong kanan, tangan kanan mengangkat selendang setinggi dada, tangan kiri membuka ke samping kiri sejajar bahu. Hitungan 5–8: putar badan pelan ke kiri (setengah lingkaran), kaki kiri menyusul rapat, selendang dikibas lembut ke arah luar. Ulangi pola yang sama ke arah berlawanan: langkah kaki kiri serong depan kiri, tangan kiri angkat selendang, putar badan ke kanan, selendang dikibas lagi (total 16 hitungan).",

"Dari posisi menghadap depan, lakukan langkah silang. Hitungan 1–4: kaki kanan menyilang di depan kaki kiri, lalu kaki kiri melangkah membuka ke samping kiri, tubuh sedikit condong mengikuti arah kaki. Tangan berayun silang di depan badan (seperti mengiris lembut udara) sambil memegang selendang. Hitungan 5–8: ganti, kaki kiri menyilang di depan kaki kanan lalu membuka ke samping kanan, tangan berayun kembali dengan pola yang sama. Ulangi 2 kali (16 hitungan) sambil jaga gerakan tetap halus dan lentur.",

"Gerakan penutup: dari posisi terakhir, rapikan langkah hingga kedua kaki rapat menghadap penonton. Hitungan 1–4: kedua tangan membawa selendang ke depan dada, siku sedikit menekuk, kepala menunduk pelan sebagai salam. Hitungan 5–8: buka tangan ke samping dengan selendang terbentang lembut, dada dibuka, pandangan ke depan sambil tersenyum. Ulangi salam satu kali lagi jika perlu, lalu tahan pose akhir beberapa detik sebelum benar-benar selesai."],
        "youtube_id": "QGlzRzC1ehY",
        "image_url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQe3dCdunJCq8gLwWCdbiWBeqI1VVKZYxH8aw&s",
        "asal_daerah": "Sumatera Barat",
        "durasi_video": 371,  # 6:11 in seconds
        "difficulty": "Menengah"
    },
    {
        "id": 6,
        "name": "Tari Serimpi",
        "description": "Tari Serimpi adalah tari klasik Yogyakarta yang penuh dengan gerakan lemah gemulai.",
        "gerakan": ["Berdiri tegap, kaki dibuka selebar bahu, tangan kanan memegang ujung selendang di pinggang kanan, tangan kiri di pinggang kiri. Hitungan 1–8: ayunkan pinggul dan badan sedikit miring ke kanan-kiri secara lembut (lenggang), sambil kaki kanan melangkah kecil ke samping kanan lalu rapat lagi, kaki kiri menyusul ke samping kiri lalu rapat lagi. Ulangi 2 kali (16 hitungan) dengan senyum dan kepala sedikit mengangguk mengikuti arah lenggangan.",

"Mulai dari posisi menghadap depan. Hitungan 1–4: kaki kanan melangkah ke depan sedikit serong kanan, tangan kanan mengangkat selendang setinggi dada, tangan kiri membuka ke samping kiri sejajar bahu. Hitungan 5–8: putar badan pelan ke kiri (setengah lingkaran), kaki kiri menyusul rapat, selendang dikibas lembut ke arah luar. Ulangi pola yang sama ke arah berlawanan: langkah kaki kiri serong depan kiri, tangan kiri angkat selendang, putar badan ke kanan, selendang dikibas lagi (total 16 hitungan).",

"Dari posisi menghadap depan, lakukan langkah silang. Hitungan 1–4: kaki kanan menyilang di depan kaki kiri, lalu kaki kiri melangkah membuka ke samping kiri, tubuh sedikit condong mengikuti arah kaki. Tangan berayun silang di depan badan (seperti mengiris lembut udara) sambil memegang selendang. Hitungan 5–8: ganti, kaki kiri menyilang di depan kaki kanan lalu membuka ke samping kanan, tangan berayun kembali dengan pola yang sama. Ulangi 2 kali (16 hitungan) sambil jaga gerakan tetap halus dan lentur.",

"Gerakan penutup: dari posisi terakhir, rapikan langkah hingga kedua kaki rapat menghadap penonton. Hitungan 1–4: kedua tangan membawa selendang ke depan dada, siku sedikit menekuk, kepala menunduk pelan sebagai salam. Hitungan 5–8: buka tangan ke samping dengan selendang terbentang lembut, dada dibuka, pandangan ke depan sambil tersenyum. Ulangi salam satu kali lagi jika perlu, lalu tahan pose akhir beberapa detik sebelum benar-benar selesai."],
        "youtube_id": "bv8vrrX4lYM",
        "image_url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRn-HmkUeHFdSytX9MQ4YMQ8Ggtee8TKTlQFg&s",
        "asal_daerah": "Yogyakarta",
        "durasi_video": 97,  # 1:37 in seconds
        "difficulty": "Mudah"
    },
    {
        "id": 7,
        "name": "Tari Saman",
        "description": "Tari Saman dari Aceh terkenal dengan gerakan cepat dan kompak.",
        "gerakan": ["Berdiri tegap, kaki dibuka selebar bahu, tangan kanan memegang ujung selendang di pinggang kanan, tangan kiri di pinggang kiri. Hitungan 1–8: ayunkan pinggul dan badan sedikit miring ke kanan-kiri secara lembut (lenggang), sambil kaki kanan melangkah kecil ke samping kanan lalu rapat lagi, kaki kiri menyusul ke samping kiri lalu rapat lagi. Ulangi 2 kali (16 hitungan) dengan senyum dan kepala sedikit mengangguk mengikuti arah lenggangan.",

"Mulai dari posisi menghadap depan. Hitungan 1–4: kaki kanan melangkah ke depan sedikit serong kanan, tangan kanan mengangkat selendang setinggi dada, tangan kiri membuka ke samping kiri sejajar bahu. Hitungan 5–8: putar badan pelan ke kiri (setengah lingkaran), kaki kiri menyusul rapat, selendang dikibas lembut ke arah luar. Ulangi pola yang sama ke arah berlawanan: langkah kaki kiri serong depan kiri, tangan kiri angkat selendang, putar badan ke kanan, selendang dikibas lagi (total 16 hitungan).",

"Dari posisi menghadap depan, lakukan langkah silang. Hitungan 1–4: kaki kanan menyilang di depan kaki kiri, lalu kaki kiri melangkah membuka ke samping kiri, tubuh sedikit condong mengikuti arah kaki. Tangan berayun silang di depan badan (seperti mengiris lembut udara) sambil memegang selendang. Hitungan 5–8: ganti, kaki kiri menyilang di depan kaki kanan lalu membuka ke samping kanan, tangan berayun kembali dengan pola yang sama. Ulangi 2 kali (16 hitungan) sambil jaga gerakan tetap halus dan lentur.",

"Gerakan penutup: dari posisi terakhir, rapikan langkah hingga kedua kaki rapat menghadap penonton. Hitungan 1–4: kedua tangan membawa selendang ke depan dada, siku sedikit menekuk, kepala menunduk pelan sebagai salam. Hitungan 5–8: buka tangan ke samping dengan selendang terbentang lembut, dada dibuka, pandangan ke depan sambil tersenyum. Ulangi salam satu kali lagi jika perlu, lalu tahan pose akhir beberapa detik sebelum benar-benar selesai."],
        "youtube_id": "F-mUU_19cMA",
        "image_url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTOqlApZqamkNQq2qamDw9xfm28YlT8cmSXZA&s",
        "asal_daerah": "Aceh",
        "durasi_video": 170,  # 2:50 in seconds
        "difficulty": "Mudah"
    },
    {
        "id": 8,
        "name": "Tari Reog Ponorogo",
        "description": "Tari Reog Ponorogo adalah pertunjukan tari dengan topeng besar dari Jawa Timur.",
        "gerakan": ["Berdiri tegap, kaki dibuka selebar bahu, tangan kanan memegang ujung selendang di pinggang kanan, tangan kiri di pinggang kiri. Hitungan 1–8: ayunkan pinggul dan badan sedikit miring ke kanan-kiri secara lembut (lenggang), sambil kaki kanan melangkah kecil ke samping kanan lalu rapat lagi, kaki kiri menyusul ke samping kiri lalu rapat lagi. Ulangi 2 kali (16 hitungan) dengan senyum dan kepala sedikit mengangguk mengikuti arah lenggangan.",

"Mulai dari posisi menghadap depan. Hitungan 1–4: kaki kanan melangkah ke depan sedikit serong kanan, tangan kanan mengangkat selendang setinggi dada, tangan kiri membuka ke samping kiri sejajar bahu. Hitungan 5–8: putar badan pelan ke kiri (setengah lingkaran), kaki kiri menyusul rapat, selendang dikibas lembut ke arah luar. Ulangi pola yang sama ke arah berlawanan: langkah kaki kiri serong depan kiri, tangan kiri angkat selendang, putar badan ke kanan, selendang dikibas lagi (total 16 hitungan).",

"Dari posisi menghadap depan, lakukan langkah silang. Hitungan 1–4: kaki kanan menyilang di depan kaki kiri, lalu kaki kiri melangkah membuka ke samping kiri, tubuh sedikit condong mengikuti arah kaki. Tangan berayun silang di depan badan (seperti mengiris lembut udara) sambil memegang selendang. Hitungan 5–8: ganti, kaki kiri menyilang di depan kaki kanan lalu membuka ke samping kanan, tangan berayun kembali dengan pola yang sama. Ulangi 2 kali (16 hitungan) sambil jaga gerakan tetap halus dan lentur.",

"Gerakan penutup: dari posisi terakhir, rapikan langkah hingga kedua kaki rapat menghadap penonton. Hitungan 1–4: kedua tangan membawa selendang ke depan dada, siku sedikit menekuk, kepala menunduk pelan sebagai salam. Hitungan 5–8: buka tangan ke samping dengan selendang terbentang lembut, dada dibuka, pandangan ke depan sambil tersenyum. Ulangi salam satu kali lagi jika perlu, lalu tahan pose akhir beberapa detik sebelum benar-benar selesai."],
        "youtube_id": "hlScDXIafPY",
        "image_url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSl7aU7RshzmXtYoXIhgmlyVEZ639AoaB8-CA&s",
        "asal_daerah": "Jawa Timur",
        "durasi_video": 477,  # 7:57 in seconds
        "difficulty": "Menengah"
    },
    {
        "id": 9,
        "name": "Tari Topeng Betawi",
        "description": "Tari Topeng Betawi menampilkan gerakan yang ceria dengan topeng khas Betawi.",
        "gerakan": ["Berdiri tegap, kaki dibuka selebar bahu, tangan kanan memegang ujung selendang di pinggang kanan, tangan kiri di pinggang kiri. Hitungan 1–8: ayunkan pinggul dan badan sedikit miring ke kanan-kiri secara lembut (lenggang), sambil kaki kanan melangkah kecil ke samping kanan lalu rapat lagi, kaki kiri menyusul ke samping kiri lalu rapat lagi. Ulangi 2 kali (16 hitungan) dengan senyum dan kepala sedikit mengangguk mengikuti arah lenggangan.",

"Mulai dari posisi menghadap depan. Hitungan 1–4: kaki kanan melangkah ke depan sedikit serong kanan, tangan kanan mengangkat selendang setinggi dada, tangan kiri membuka ke samping kiri sejajar bahu. Hitungan 5–8: putar badan pelan ke kiri (setengah lingkaran), kaki kiri menyusul rapat, selendang dikibas lembut ke arah luar. Ulangi pola yang sama ke arah berlawanan: langkah kaki kiri serong depan kiri, tangan kiri angkat selendang, putar badan ke kanan, selendang dikibas lagi (total 16 hitungan).",

"Dari posisi menghadap depan, lakukan langkah silang. Hitungan 1–4: kaki kanan menyilang di depan kaki kiri, lalu kaki kiri melangkah membuka ke samping kiri, tubuh sedikit condong mengikuti arah kaki. Tangan berayun silang di depan badan (seperti mengiris lembut udara) sambil memegang selendang. Hitungan 5–8: ganti, kaki kiri menyilang di depan kaki kanan lalu membuka ke samping kanan, tangan berayun kembali dengan pola yang sama. Ulangi 2 kali (16 hitungan) sambil jaga gerakan tetap halus dan lentur.",

"Gerakan penutup: dari posisi terakhir, rapikan langkah hingga kedua kaki rapat menghadap penonton. Hitungan 1–4: kedua tangan membawa selendang ke depan dada, siku sedikit menekuk, kepala menunduk pelan sebagai salam. Hitungan 5–8: buka tangan ke samping dengan selendang terbentang lembut, dada dibuka, pandangan ke depan sambil tersenyum. Ulangi salam satu kali lagi jika perlu, lalu tahan pose akhir beberapa detik sebelum benar-benar selesai."],
        "youtube_id": "v8g-sf9mZSY",
        "image_url": "https://bisniswisata.co.id/wp-content/uploads/2019/08/tari-topeng-betawi-1.jpg",
        "asal_daerah": "Betawi",
        "durasi_video": 716,  # 11:56 in seconds
        "difficulty": "Susah"
    },
    {
        "id": 10,
        "name": "Tari Gambyong",
        "description": "Tari Gambyong adalah tari klasik dari Jawa Tengah dengan gerakan anggun.",
        "gerakan": ["Berdiri tegap, kaki dibuka selebar bahu, tangan kanan memegang ujung selendang di pinggang kanan, tangan kiri di pinggang kiri. Hitungan 1–8: ayunkan pinggul dan badan sedikit miring ke kanan-kiri secara lembut (lenggang), sambil kaki kanan melangkah kecil ke samping kanan lalu rapat lagi, kaki kiri menyusul ke samping kiri lalu rapat lagi. Ulangi 2 kali (16 hitungan) dengan senyum dan kepala sedikit mengangguk mengikuti arah lenggangan.",

"Mulai dari posisi menghadap depan. Hitungan 1–4: kaki kanan melangkah ke depan sedikit serong kanan, tangan kanan mengangkat selendang setinggi dada, tangan kiri membuka ke samping kiri sejajar bahu. Hitungan 5–8: putar badan pelan ke kiri (setengah lingkaran), kaki kiri menyusul rapat, selendang dikibas lembut ke arah luar. Ulangi pola yang sama ke arah berlawanan: langkah kaki kiri serong depan kiri, tangan kiri angkat selendang, putar badan ke kanan, selendang dikibas lagi (total 16 hitungan).",

"Dari posisi menghadap depan, lakukan langkah silang. Hitungan 1–4: kaki kanan menyilang di depan kaki kiri, lalu kaki kiri melangkah membuka ke samping kiri, tubuh sedikit condong mengikuti arah kaki. Tangan berayun silang di depan badan (seperti mengiris lembut udara) sambil memegang selendang. Hitungan 5–8: ganti, kaki kiri menyilang di depan kaki kanan lalu membuka ke samping kanan, tangan berayun kembali dengan pola yang sama. Ulangi 2 kali (16 hitungan) sambil jaga gerakan tetap halus dan lentur.",

"Gerakan penutup: dari posisi terakhir, rapikan langkah hingga kedua kaki rapat menghadap penonton. Hitungan 1–4: kedua tangan membawa selendang ke depan dada, siku sedikit menekuk, kepala menunduk pelan sebagai salam. Hitungan 5–8: buka tangan ke samping dengan selendang terbentang lembut, dada dibuka, pandangan ke depan sambil tersenyum. Ulangi salam satu kali lagi jika perlu, lalu tahan pose akhir beberapa detik sebelum benar-benar selesai."],
        "youtube_id": "gtA_e6GmaE4",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/1/15/Gambyong_Langenkusuma_Pj_DSC_1322.JPG",
        "asal_daerah": "Jawa Tengah",
        "durasi_video": 369,  # 6:09 in seconds
        "difficulty": "Menengah"
    }
]

@login_required
def dance_list(request):
    return render(request, 'dances/dance_list.html', {'dances': DANCES})

def dance_result(request, dance_id):
    dance = get_dance_by_id(dance_id)
    if dance is None:
        raise Http404(f"Dance with id {dance_id} not found")

    # Import sanggar data and randomly select 2 recommendations
    from daftarsanggar.views import HARDCODED_SANGGARS
    recommended_sanggars = random.sample(HARDCODED_SANGGARS, min(2, len(HARDCODED_SANGGARS)))

    # Score now comes entirely from frontend API
    return render(request, 'dances/dance_result.html', {
        'dance': dance,
        'recommended_sanggars': recommended_sanggars
    })

def get_dance_by_id(dance_id):
    for dance in DANCES:
        if dance["id"] == int(dance_id):
            return dance
    return None

def dance_detail(request, dance_id):
    dance = get_dance_by_id(dance_id)
    if dance is None:
        raise Http404(f"Dance with id {dance_id} not found")
    return render(request, 'dances/dance_detail.html', {'dance': dance})

def dance_tutorial(request, dance_id):
    dance = get_dance_by_id(dance_id)
    if dance is None:
        raise Http404(f"Dance with id {dance_id} not found")
    # Add formatted duration and calculate max sub-gerakan
    dance = dance.copy()
    durasi = dance.get('durasi_video', 0)
    dance['durasi_formatted'] = format_duration(durasi)
    dance['max_subgerakan'] = (durasi + 17) // 18  # Round up, each sub-gerakan is 18 seconds
    return render(request, 'dances/dance_tutorial.html', {'dance': dance})

def dance_assessment(request, dance_id):
    dance = get_dance_by_id(dance_id)
    if dance is None:
        raise Http404(f"Dance with id {dance_id} not found")
    # Add formatted duration and calculate max sub-gerakan
    dance = dance.copy()
    durasi = dance.get('durasi_video', 0)
    dance['durasi_formatted'] = format_duration(durasi)
    # Calculate number of sub-gerakan (each is 18 seconds)
    dance['max_subgerakan'] = (durasi + 17) // 18  # Round up
    return render(request, 'dances/dance_assessment.html', {'dance': dance})
```

### dances/migrations/__init__.py

```py

```

### dances/templates/dances/dance_assessment.html

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Tria - Belajar Tarian Tradisional Indonesia</title>
    <link rel="icon" type="image/png" href="https://i.ibb.co.com/fY9F3RwF/tria.png" />
    <link rel="shortcut icon" type="image/png" href="https://i.ibb.co.com/fY9F3RwF/tria.png" />
    <style>
        :root {
            --tria-red: #e53935;
            --tria-orange: #ff9800;
            --tria-soft-bg: #fff7ec;
            --tria-orange-soft: #fff3e0;
            --tria-border: #f0e4d6;
            --tria-text: #222222;
            --tria-muted: #555555;
        }

        /* accent class for inline orange text - darker, richer gradient */
        .accent {
            background: linear-gradient(135deg, var(--tria-red), #e65100);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-weight: 800;
        }
    
        * {
            box-sizing: border-box;
        }
    
        body {
            background-color: var(--tria-soft-bg);
            color: var(--tria-text);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen,
                Ubuntu, Cantarell, "Open Sans", "Helvetica Neue", sans-serif;
            margin: 0;
            padding: 0;
        }
    
        a {
            text-decoration: none;
            color: inherit;
        }
    
        /* NAVBAR */
        .navbar {
            background-color: #ffffff;
            border-bottom: 1px solid #f3eee7;
            position: sticky;
            top: 0;
            z-index: 50;
            backdrop-filter: blur(10px);
        }
    
        .nav-inner {
            max-width: 1100px;
            margin: 0 auto;
            padding: 0.75rem 1.5rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
        }
    
        .nav-brand {
            display: flex;
            align-items: center;
            gap: 0.6rem;
        }
    
        .nav-logo {
            height: 36px;
            width: 36px;
            object-fit: contain;
        }
    
        .nav-title {
            font-weight: 700;
            letter-spacing: 0.03em;
            font-size: 1.1rem;
        }
    
        .nav-links {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            font-size: 0.95rem;
        }
    
        .nav-link {
            padding: 0.4rem 0.75rem;
            border-radius: 999px;
            transition: background-color 0.2s ease, color 0.2s ease, transform 0.1s ease;
        }
    
        .nav-link:hover {
            background-color: #fff1df;
            color: var(--tria-red);
            transform: translateY(-1px);
        }
    
        .nav-cta {
            background: linear-gradient(135deg, var(--tria-red), var(--tria-orange));
            color: #ffffff;
            font-weight: 600;
        }
    
        .nav-cta:hover {
            background: linear-gradient(135deg, #c62828, #fb8c00);
            color: #ffffff;
        }
    
        /* PAGE */
        .page {
            max-width: 1100px;
            margin: 2.5rem auto 3.5rem auto;
            padding: 0 1rem;
        }
    
        .section-title {
            font-size: 1.9rem;
            margin: 0 0 0.4rem 0;
            text-align: center;
            font-weight: 800;
            letter-spacing: -0.01em;
        }
    
        .section-subtitle {
            text-align: center;
            font-size: 0.98rem;
            color: var(--tria-muted);
            margin: 0 auto 2rem auto;
            max-width: 640px;
            line-height: 1.6;
        }

        /* VIDEO CONTAINER - Full width dengan border */
        .video-container {
            background-color: #ffffff;
            border-radius: 1.4rem;
            border: 1px solid var(--tria-border);
            overflow: hidden;
            box-shadow: 0 14px 30px rgba(0, 0, 0, 0.05);
            margin-bottom: 1.5rem;
        }

        video {
            width: 100%;
            height: 500px;
            object-fit: cover;
            display: block;
            background-color: #000000;
        }

        /* CONTROLS CONTAINER */
        .controls-container {
            background-color: #ffffff;
            border-radius: 1.4rem;
            border: 1px solid var(--tria-border);
            padding: 1.8rem 2rem;
            box-shadow: 0 14px 30px rgba(0, 0, 0, 0.05);
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1.5rem;
            flex-wrap: wrap;
            margin-bottom: 1.5rem;
        }

        /* YOUTUBE VIDEO CONTAINER */
        .youtube-container {
            background-color: #ffffff;
            border-radius: 1.4rem;
            border: 1px solid var(--tria-border);
            padding: 1.5rem;
            box-shadow: 0 14px 30px rgba(0, 0, 0, 0.05);
            margin-bottom: 1.5rem;
        }

        .youtube-wrapper {
            position: relative;
            width: 100%;
            padding-bottom: 56.25%; /* 16:9 aspect ratio */
            height: 0;
            overflow: hidden;
            border-radius: 1rem;
            background-color: #000000;
        }

        .youtube-wrapper iframe {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            border: none;
        }

        .controls-left {
            display: flex;
            align-items: center;
            gap: 0.8rem;
        }

        .timer-display {
            font-size: 2rem;
            font-weight: 700;
            color: var(--tria-red);
            min-width: 120px;
            text-align: center;
            padding: 0.5rem 1rem;
            background: linear-gradient(135deg, var(--tria-orange-soft), #ffffff);
            border-radius: 12px;
            border: 2px solid var(--tria-border);
        }
    
        /* BUTTONS */
        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 0.85rem 2rem;
            border-radius: 999px;
            border: 1px solid transparent;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
        }
    
        .btn-primary {
            background: linear-gradient(135deg, var(--tria-red), var(--tria-orange));
            color: #ffffff;
            box-shadow: 0 8px 18px rgba(229, 57, 53, 0.25);
        }
    
        .btn-primary:hover:not(:disabled) {
            background: linear-gradient(135deg, #c62828, #fb8c00);
            transform: translateY(-2px);
            box-shadow: 0 10px 24px rgba(229, 57, 53, 0.35);
        }
    
        .btn-outline {
            background-color: #ffffff;
            color: var(--tria-red);
            border-color: rgba(229, 57, 53, 0.3);
        }
    
        .btn-outline:hover:not(:disabled) {
            background-color: var(--tria-orange-soft);
            border-color: var(--tria-red);
            transform: translateY(-2px);
        }
    
        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            box-shadow: none;
            transform: none;
        }

        /* LOADING OVERLAY */
        .loading-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(255, 255, 255, 0.95);
            display: none;
            align-items: center;
            justify-content: center;
            z-index: 9999;
            flex-direction: column;
            gap: 1rem;
        }

        .loading-text {
            font-size: 2rem;
            font-weight: 700;
            color: var(--tria-red);
        }

        .loading-spinner {
            width: 50px;
            height: 50px;
            border: 5px solid var(--tria-orange-soft);
            border-top: 5px solid var(--tria-red);
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        /* COUNTDOWN OVERLAY */
        .countdown-overlay {
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-size: 5rem;
            font-weight: 800;
            color: var(--tria-red);
            z-index: 1000;
            background: rgba(255, 255, 255, 0.95);
            padding: 2rem 3rem;
            border-radius: 24px;
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.2);
            text-align: center;
        }

        /* SUB-GERAKAN DISPLAY */
        .subgerakan-display-container {
            margin-bottom: 1.5rem;
        }

        .subgerakan-display {
            background: linear-gradient(135deg, #ffffff, #fffbf7);
            border-radius: 1.4rem;
            border: 2px solid var(--tria-border);
            padding: 2rem 2.2rem;
            box-shadow: 0 8px 24px rgba(229, 57, 53, 0.12);
            position: relative;
            overflow: hidden;
            transition: box-shadow 0.3s ease, transform 0.2s ease;
        }

        .subgerakan-display:hover {
            box-shadow: 0 12px 32px rgba(229, 57, 53, 0.16);
            transform: translateY(-2px);
        }

        .subgerakan-display::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, var(--tria-red), var(--tria-orange));
        }

        .subgerakan-header-display {
            display: flex;
            align-items: center;
            gap: 1.2rem;
            margin-bottom: 1.2rem;
        }

        .subgerakan-badge {
            width: 56px;
            height: 56px;
            border-radius: 50%;
            background: linear-gradient(135deg, var(--tria-red), var(--tria-orange));
            color: #ffffff;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.4rem;
            font-weight: 800;
            flex-shrink: 0;
            box-shadow: 0 4px 12px rgba(229, 57, 53, 0.3);
            position: relative;
            z-index: 1;
        }

        .subgerakan-title-wrapper {
            flex: 1;
            display: flex;
            flex-direction: column;
            gap: 0.3rem;
        }

        .subgerakan-title-display {
            font-size: 1.5rem;
            font-weight: 800;
            margin: 0;
            color: var(--tria-text);
            letter-spacing: -0.01em;
            background: linear-gradient(135deg, var(--tria-red), #e65100);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            transition: all 0.3s ease;
        }

        .subgerakan-time-indicator {
            font-size: 0.85rem;
            font-weight: 600;
            color: var(--tria-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            transition: color 0.3s ease;
        }

        .subgerakan-instruction {
            font-size: 1.05rem;
            color: var(--tria-text);
            line-height: 1.7;
            margin: 0;
            padding: 1.4rem 1.6rem;
            background: linear-gradient(135deg, var(--tria-orange-soft), #ffffff);
            border-radius: 1rem;
            border-left: 5px solid var(--tria-orange);
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
            font-weight: 500;
            transition: all 0.3s ease;
        }

        .subgerakan-instruction:hover {
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
        }

        /* MODAL DIALOG */
        .modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.6);
            display: none;
            align-items: center;
            justify-content: center;
            z-index: 10000;
        }

        .modal-overlay.show {
            display: flex;
        }

        .modal-dialog {
            background: #ffffff;
            border-radius: 1.4rem;
            padding: 2rem 2.5rem;
            max-width: 500px;
            width: 90%;
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.3);
            text-align: center;
        }

        .modal-title {
            font-size: 1.4rem;
            font-weight: 700;
            color: var(--tria-text);
            margin: 0 0 1rem 0;
        }

        .modal-message {
            font-size: 1rem;
            color: var(--tria-muted);
            line-height: 1.6;
            margin: 0 0 2rem 0;
        }

        .modal-actions {
            display: flex;
            gap: 1rem;
            justify-content: center;
        }

        .modal-actions .btn {
            min-width: 120px;
        }

        /* ACCESS CODE OVERLAY */
        .access-overlay {
            position: fixed;
            inset: 0;
            background: rgba(0, 0, 0, 0.6);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 10000;
        }

        .access-card {
            background: #ffffff;
            border-radius: 1.4rem;
            padding: 2rem 2.5rem;
            max-width: 420px;
            width: 90%;
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.25);
            text-align: center;
            border: 1px solid var(--tria-border);
        }

        .access-title {
            font-size: 1.4rem;
            font-weight: 800;
            margin: 0 0 0.8rem 0;
            color: var(--tria-text);
        }

        .access-subtitle {
            font-size: 1rem;
            color: var(--tria-muted);
            margin: 0 0 1.5rem 0;
        }

        .access-input {
            width: 100%;
            padding: 0.9rem 1rem;
            border-radius: 0.9rem;
            border: 1px solid var(--tria-border);
            font-size: 1rem;
            margin-bottom: 1rem;
            outline: none;
            transition: border-color 0.2s ease, box-shadow 0.2s ease;
        }

        .access-input:focus {
            border-color: var(--tria-red);
            box-shadow: 0 0 0 3px rgba(229, 57, 53, 0.12);
        }

        .access-error {
            color: var(--tria-red);
            font-size: 0.95rem;
            margin: 0 0 1rem 0;
            display: none;
        }

        .access-actions {
            display: flex;
            gap: 0.8rem;
            justify-content: center;
            flex-wrap: wrap;
        }
    
        @media (max-width: 768px) {
            video {
                height: 350px;
            }

            .controls-container {
                flex-direction: column;
                align-items: stretch;
            }

            .controls-left {
                flex-direction: column;
                width: 100%;
            }

            .btn {
                width: 100%;
            }

            .timer-display {
                width: 100%;
            }

            .countdown-overlay {
                font-size: 4rem;
                padding: 1.5rem 2.5rem;
            }

            .subgerakan-display {
                padding: 1.5rem 1.6rem;
            }

            .subgerakan-header-display {
                flex-direction: column;
                align-items: flex-start;
                gap: 0.8rem;
            }

            .subgerakan-badge {
                width: 48px;
                height: 48px;
                font-size: 1.2rem;
            }

            .subgerakan-title-display {
                font-size: 1.3rem;
            }

            .subgerakan-instruction {
                font-size: 0.98rem;
                padding: 1.2rem 1.4rem;
            }

            .modal-dialog {
                padding: 1.5rem 2rem;
            }

            .modal-actions {
                flex-direction: column;
            }

            .modal-actions .btn {
                width: 100%;
            }

            .youtube-container {
                padding: 1rem;
            }
        }
    
        @media (max-width: 600px) {
            .page {
                padding-inline: 1rem;
            }

            video {
                height: 280px;
            }

            .subgerakan-display {
                padding: 1.4rem 1.5rem;
            }
        }
    </style>    
</head>
<body>
{% include 'partials/navbar.html' %}

<main class="page">
    <h1 class="section-title"><span class="accent">{{ dance.name }}</span> – Mulai Asesmen</h1>
    <p class="section-subtitle">
        Gunakan kamera perangkatmu untuk merekam gerakan saat menarikan
        <strong>{{ dance.name }}</strong>. Tria akan membantu mengevaluasi hasilnya.
    </p>

    <div class="subgerakan-display-container">
        <div class="subgerakan-display">
            <div class="subgerakan-header-display">
                <span class="subgerakan-badge" id="subgerakanBadge">🚀</span>
                <div class="subgerakan-title-wrapper">
                    <h3 class="subgerakan-title-display" id="subgerakanTitle">Mulai Asesmen anda</h3>
                    <span class="subgerakan-time-indicator" id="subgerakanTimeIndicator">Click Start</span>
                </div>
            </div>
            <p class="subgerakan-instruction" id="subgerakanInstruction">
                Klik tombol Start untuk memulai asesmen. Setelah mulai, instruksi akan berubah sesuai dengan gerakan yang sedang dilakukan.
            </p>
        </div>
    </div>

    <div class="video-container">
        <video id="video" autoplay playsinline></video>
    </div>

    <div class="controls-container">
        <div class="controls-left">
            <button id="startBtn" class="btn btn-primary">Start</button>
            <button id="finishBtn" class="btn btn-outline" disabled>Finish</button>
        </div>
        <div class="timer-display" id="timer">00:00</div>
    </div>

    <!-- YOUTUBE VIDEO -->
    <div class="youtube-container">
        <div class="youtube-wrapper">
            <div id="youtubePlayer"></div>
        </div>
    </div>
</main>

<div class="loading-overlay" id="loadingOverlay">
    <div class="loading-spinner"></div>
    <div class="loading-text">Menganalisis Gerakmu...</div>
</div>

<div class="modal-overlay" id="modalOverlay">
    <div class="modal-dialog">
        <h3 class="modal-title">Konfirmasi Akhiri Asesmen</h3>
        <p class="modal-message" id="modalMessage">
            Penilaian belum selesai diuji. Apakah ingin mengakhiri karena tidak menyelesaikan pengujian?
        </p>
        <div class="modal-actions">
            <button class="btn btn-outline" id="modalCancel">Tidak</button>
            <button class="btn btn-primary" id="modalConfirm">Ya</button>
        </div>
    </div>
</div>

<div class="access-overlay" id="accessOverlay">
    <div class="access-card">
        <h3 class="access-title">Sistem ditutup sementara</h3>
        <p class="access-subtitle">Masukkan kode akses untuk memulai asesmen.</p>
        <input type="password" id="accessInput" class="access-input" placeholder="Masukkan kode akses" autocomplete="off" />
        <p class="access-error" id="accessError">Kode akses salah. Coba lagi.</p>
        <div class="access-actions">
            <button class="btn btn-outline" id="accessCancel" type="button" onclick="window.location.href='/dances'">Batal</button>
            <button class="btn btn-primary" id="accessSubmit" type="button">Masuk</button>
        </div>
    </div>
</div>

<script>
    // Get dance data from Django template
    const DANCE_ID = "{{ dance.id }}"; // Menangkap Dance ID
    const TOTAL_DURATION = parseInt("{{ dance.durasi_video|default:264 }}") || 264; // Duration in seconds
    const MAX_SUBGERAKAN = parseInt("{{ dance.max_subgerakan|default:15 }}") || 15;
    const SUBGERAKAN_DURATION = 18; // Each sub-gerakan is 18 seconds
    const DANCE_NAME = "{{ dance.name|default:'Tarian' }}";
    const YOUTUBE_ID = "{{ dance.youtube_id|default:'' }}";
    const ACCESS_CODE = "987654321";
    
    // YouTube player variable
    let youtubePlayer = null;
    
    // Function to generate dance-specific instructions
    function generateDanceInstructions(danceName, numSubgerakan) {
        const instructions = [];
        const danceLower = danceName.toLowerCase();
        
        // Base instructions pool
        const baseInstructions = {
            start: [
                "Berdiri tegak dengan kaki rapat, tangan di samping badan. Siapkan postur tubuh dan fokus sebelum memulai gerakan.",
                "Posisi awal dengan postur yang benar, kedua kaki sejajar dan tangan dalam posisi siap.",
                "Mulai dengan posisi dasar, tubuh tegak dan seimbang, siap untuk memulai gerakan."
            ],
            hand: [
                "Angkat tangan kanan ke depan dengan telapak menghadap ke atas, gerakan lembut dan terkontrol.",
                "Gerakan tangan dengan pola melingkar, koordinasi antara tangan kanan dan kiri.",
                "Kedua tangan bergerak secara sinkron membentuk pola yang harmonis.",
                "Ayunkan tangan dengan irama yang konsisten, jaga kelenturan pergelangan tangan."
            ],
            foot: [
                "Melangkah dengan langkah yang terukur, jaga keseimbangan dan koordinasi.",
                "Gerakan kaki mengikuti pola dasar tarian, langkah maju, mundur, atau ke samping.",
                "Pindahkan berat badan dengan lembut sambil melangkah, jaga stabilitas tubuh."
            ],
            body: [
                "Putar badan dengan gerakan halus, pandangan mengikuti arah putaran.",
                "Gerakan tubuh mengikuti irama, ayunkan pinggul dengan lembut dan terkontrol.",
                "Koordinasi antara gerakan badan, tangan, dan kaki dengan harmonis."
            ],
            transition: [
                "Gerakan transisi yang menghubungkan bagian pertama dengan bagian berikutnya.",
                "Perubahan tempo dan intensitas gerakan, siapkan untuk bagian selanjutnya.",
                "Transisi yang mulus antara gerakan, jaga kontinuitas dan alur tarian."
            ],
            energetic: [
                "Bagian paling energik dari tarian, kombinasi semua elemen dengan tempo maksimal.",
                "Ekspresikan energi dan semangat melalui gerakan yang lebih dinamis dan penuh ekspresi.",
                "Tingkatkan intensitas gerakan, tunjukkan karakteristik khas tarian dengan penuh percaya diri."
            ],
            slow: [
                "Tempo mulai melambat, gerakan menjadi lebih tenang sebagai persiapan menuju penutupan.",
                "Redakan intensitas gerakan, fokus pada kelenturan dan keanggunan.",
                "Gerakan menjadi lebih halus dan terkontrol, persiapkan untuk bagian akhir."
            ],
            end: [
                "Kembali ke posisi tengah dengan gerakan lembut, mengumpulkan energi untuk pose akhir.",
                "Tahan pose akhir dengan sempurna, kedua tangan di depan dada, postur tegap menunjukkan penyelesaian tarian.",
                "Pose penutup yang elegan, tunjukkan penyelesaian tarian dengan percaya diri dan anggun."
            ]
        };
        
        // Dance-specific variations
        if (danceLower.includes('kecak')) {
            instructions.push("Berdiri dalam formasi, siapkan untuk gerakan khas Kecak dengan koordinasi kelompok.");
            instructions.push("Gerakan tangan dengan pola khas Kecak, koordinasi dengan suara 'cak'.");
            instructions.push("Langkah kaki mengikuti irama, jaga sinkronisasi dengan penari lain.");
        } else if (danceLower.includes('janger')) {
            instructions.push("Berdiri dengan postur yang ceria, siapkan untuk gerakan dinamis Janger.");
            instructions.push("Gerakan tangan yang lincah dan ceria, ekspresikan kegembiraan.");
            instructions.push("Langkah kaki yang energik, tunjukkan semangat muda dalam tarian.");
        } else if (danceLower.includes('bungong') || danceLower.includes('jeumpa')) {
            instructions.push("Berdiri dengan anggun, siapkan untuk gerakan yang melambangkan keindahan bunga.");
            instructions.push("Gerakan tangan yang lembut seperti kelopak bunga, ekspresikan keindahan.");
            instructions.push("Langkah kaki yang halus, jaga keanggunan dalam setiap gerakan.");
        } else if (danceLower.includes('lenggang') || danceLower.includes('nyai')) {
            instructions.push("Berdiri dengan postur anggun wanita, siapkan untuk gerakan lenggang yang khas.");
            instructions.push("Gerakan tangan yang lembut seperti kelopak bunga, ekspresikan keindahan.");
            instructions.push("Langkah kaki dengan pola khas lenggang, koordinasi dengan ayunan pinggul.");
        } else if (danceLower.includes('piring')) {
            instructions.push("Berdiri dengan memegang piring, siapkan untuk gerakan khas Tari Piring.");
            instructions.push("Gerakan tangan memutar piring dengan terampil, jaga keseimbangan piring.");
            instructions.push("Langkah kaki yang dinamis sambil mempertahankan piring tetap stabil.");
        } else if (danceLower.includes('serimpi')) {
            instructions.push("Berdiri dengan postur klasik, siapkan untuk gerakan lemah gemulai Serimpi.");
            instructions.push("Gerakan tangan yang sangat halus dan anggun, ekspresikan kelembutan.");
            instructions.push("Langkah kaki yang sangat pelan dan terkontrol, jaga keanggunan klasik.");
        } else if (danceLower.includes('saman')) {
            instructions.push("Berdiri dalam formasi, siapkan untuk gerakan cepat dan kompak Saman.");
            instructions.push("Gerakan tangan yang sangat cepat dan sinkron, koordinasi dengan penari lain.");
            instructions.push("Langkah kaki yang dinamis, jaga tempo cepat dan kompak.");
        } else if (danceLower.includes('reog')) {
            instructions.push("Berdiri dengan postur kuat, siapkan untuk gerakan energik Reog Ponorogo.");
            instructions.push("Gerakan tangan yang kuat dan dinamis, ekspresikan kekuatan karakter.");
            instructions.push("Langkah kaki yang tegas, tunjukkan karakteristik khas Reog.");
        } else if (danceLower.includes('topeng') || danceLower.includes('betawi')) {
            instructions.push("Berdiri dengan postur ceria, siapkan untuk gerakan khas Topeng Betawi.");
            instructions.push("Gerakan tangan yang lincah dan ekspresif, tunjukkan karakter topeng.");
            instructions.push("Langkah kaki yang dinamis, ekspresikan keceriaan khas Betawi.");
        } else if (danceLower.includes('gambyong')) {
            instructions.push("Berdiri dengan postur klasik Jawa, siapkan untuk gerakan anggun Gambyong.");
            instructions.push("Gerakan tangan yang sangat halus dan elegan, ekspresikan keanggunan klasik.");
            instructions.push("Langkah kaki yang pelan dan terkontrol, jaga kelembutan khas Gambyong.");
        } else {
            // Generic fallback
            instructions.push(...baseInstructions.start);
            instructions.push(...baseInstructions.hand);
            instructions.push(...baseInstructions.foot);
        }
        
        // Fill remaining with base instructions, shuffled for variety
        const allBase = [
            ...baseInstructions.start,
            ...baseInstructions.hand,
            ...baseInstructions.foot,
            ...baseInstructions.body,
            ...baseInstructions.transition,
            ...baseInstructions.energetic,
            ...baseInstructions.slow,
            ...baseInstructions.end
        ];
        
        // Shuffle array function
        function shuffleArray(array) {
            const shuffled = [...array];
            for (let i = shuffled.length - 1; i > 0; i--) {
                const j = Math.floor(Math.random() * (i + 1));
                [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
            }
            return shuffled;
        }
        
        // Add shuffled base instructions to fill remaining slots
        const shuffledBase = shuffleArray(allBase);
        while (instructions.length < numSubgerakan) {
            instructions.push(...shuffledBase);
        }
        
        // Ensure first is always a start instruction and last is always an end instruction
        if (instructions.length > 0) {
            instructions[0] = baseInstructions.start[0];
        }
        if (instructions.length > 1) {
            instructions[instructions.length - 1] = baseInstructions.end[baseInstructions.end.length - 1];
        }
        
        return instructions.slice(0, numSubgerakan);
    }
    
    // Generate dance-specific instructions
    const danceInstructions = generateDanceInstructions(DANCE_NAME, MAX_SUBGERAKAN);
    
    // Dynamically generate sub-gerakan data based on duration
    const subGerakanData = [];
    for (let i = 0; i < MAX_SUBGERAKAN; i++) {
        const start = i * SUBGERAKAN_DURATION;
        const end = Math.min(start + SUBGERAKAN_DURATION, TOTAL_DURATION);
        if (start >= TOTAL_DURATION) break;
        
        subGerakanData.push({
            num: i + 1,
            start: start,
            end: end,
            title: `Sub Gerakan ${i + 1}`,
            instruction: danceInstructions[i] || "Lanjutkan gerakan dengan irama yang konsisten, jaga koordinasi dan ekspresi."
        });
    }

    const video = document.getElementById('video');
    const startBtn = document.getElementById('startBtn');
    const finishBtn = document.getElementById('finishBtn');
    const timerDisplay = document.getElementById('timer');
    const subgerakanBadge = document.getElementById('subgerakanBadge');
    const subgerakanTitle = document.getElementById('subgerakanTitle');
    const subgerakanInstruction = document.getElementById('subgerakanInstruction');
    const subgerakanTimeIndicator = document.getElementById('subgerakanTimeIndicator');
    const modalOverlay = document.getElementById('modalOverlay');
    const modalCancel = document.getElementById('modalCancel');
    const modalConfirm = document.getElementById('modalConfirm');
    const accessOverlay = document.getElementById('accessOverlay');
    const accessInput = document.getElementById('accessInput');
    const accessError = document.getElementById('accessError');
    const accessSubmit = document.getElementById('accessSubmit');
    const accessCancel = document.getElementById('accessCancel');
    
    let stream;
    let timerInterval;
    let seconds = 0;
    let currentSubGerakan = null;
    let stoppedAtGerakan = null;
    let accessGranted = false;

    // Disable start until access granted
    startBtn.disabled = true;

    function showAccessOverlay() {
        accessOverlay.style.display = 'flex';
        accessInput.value = '';
        accessError.style.display = 'none';
        accessInput.focus();
    }

    function handleAccessSubmit() {
        if (accessInput.value.trim() === ACCESS_CODE) {
            accessGranted = true;
            accessOverlay.style.display = 'none';
            startBtn.disabled = false;
        } else {
            accessError.style.display = 'block';
        }
    }

    accessSubmit.addEventListener('click', handleAccessSubmit);
    accessInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            handleAccessSubmit();
        }
    });
    accessCancel.addEventListener('click', () => {
        accessInput.value = '';
        accessError.style.display = 'none';
        accessInput.focus();
    });

    // Show overlay immediately on load
    showAccessOverlay();

    // Helper function to format time (seconds to mm:ss)
    function formatTime(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins.toString().padStart(1, '0')}:${secs.toString().padStart(2, '0')}`;
    }

    // Function to update sub-gerakan display based on elapsed time
    function updateSubGerakanDisplay(elapsedSeconds) {
        // Check if completed all
        if (elapsedSeconds >= TOTAL_DURATION) {
            const lastGerakan = subGerakanData[subGerakanData.length - 1];
            subgerakanBadge.textContent = MAX_SUBGERAKAN.toString();
            subgerakanTitle.textContent = 'Selamat! Asesmen Selesai';
            subgerakanInstruction.textContent = 'Anda telah menyelesaikan semua sub-gerakan. Klik Finish untuk melihat hasil.';
            subgerakanTimeIndicator.textContent = `${formatTime(lastGerakan.start)} - ${formatTime(TOTAL_DURATION)}`;
            return;
        }

        // Find the current sub-gerakan based on elapsed time
        const activeGerakan = subGerakanData.find(gerakan => 
            elapsedSeconds >= gerakan.start && elapsedSeconds < gerakan.end
        );

        // If no match found (shouldn't happen, but handle edge cases)
        if (!activeGerakan) {
            // Find the last gerakan that hasn't started yet, or default to first
            const nextGerakan = subGerakanData.find(gerakan => elapsedSeconds < gerakan.start) || subGerakanData[0];
            if (currentSubGerakan?.num !== nextGerakan.num) {
                currentSubGerakan = nextGerakan;
                subgerakanBadge.textContent = nextGerakan.num;
                subgerakanTitle.textContent = `Lakukan ${nextGerakan.title}`;
                subgerakanInstruction.textContent = nextGerakan.instruction;
                subgerakanTimeIndicator.textContent = `${formatTime(nextGerakan.start)} - ${formatTime(nextGerakan.end)}`;
            }
            return;
        }

        // Update if changed
        if (!currentSubGerakan || currentSubGerakan.num !== activeGerakan.num) {
            currentSubGerakan = activeGerakan;
            subgerakanBadge.textContent = activeGerakan.num;
            subgerakanTitle.textContent = `Lakukan ${activeGerakan.title}`;
            subgerakanInstruction.textContent = activeGerakan.instruction;
            subgerakanTimeIndicator.textContent = `${formatTime(activeGerakan.start)} - ${formatTime(activeGerakan.end)}`;
        }
    }

    // Function to get current sub-gerakan number based on elapsed time
    function getCurrentGerakanNumber(elapsedSeconds) {
        if (elapsedSeconds >= TOTAL_DURATION) {
            return MAX_SUBGERAKAN; // Completed
        }
        const activeGerakan = subGerakanData.find(gerakan => 
            elapsedSeconds >= gerakan.start && elapsedSeconds < gerakan.end
        );
        return activeGerakan ? activeGerakan.num : null;
    }

    // Modal handlers
    modalCancel.addEventListener('click', () => {
        modalOverlay.classList.remove('show');
    });

    modalConfirm.addEventListener('click', async () => {
        modalOverlay.classList.remove('show');
        await finishAssessment(true);
    });

    // Initialize YouTube Player
    function initYouTubePlayer() {
        if (!YOUTUBE_ID) {
            // Hide YouTube container if no video ID
            const youtubeContainer = document.querySelector('.youtube-container');
            if (youtubeContainer) {
                youtubeContainer.style.display = 'none';
            }
            return;
        }
        
        // Load YouTube IFrame API
        if (typeof YT === 'undefined' || typeof YT.Player === 'undefined') {
            const tag = document.createElement('script');
            tag.src = "https://www.youtube.com/iframe_api";
            const firstScriptTag = document.getElementsByTagName('script')[0];
            firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);
            
            // Wait for API to load
            window.onYouTubeIframeAPIReady = function() {
                youtubePlayer = new YT.Player('youtubePlayer', {
                    videoId: YOUTUBE_ID,
                    playerVars: {
                        'autoplay': 0,
                        'controls': 1,
                        'rel': 0,
                        'modestbranding': 1,
                        'playsinline': 1,
                        'enablejsapi': 1
                    },
                    events: {
                        'onReady': function(event) {
                            // Player is ready, set max volume but don't play yet
                            event.target.setVolume(100);
                        }
                    }
                });
            };
        } else {
            // API already loaded, create player immediately
            youtubePlayer = new YT.Player('youtubePlayer', {
                videoId: YOUTUBE_ID,
                playerVars: {
                    'autoplay': 0,
                    'controls': 1,
                    'rel': 0,
                    'modestbranding': 1,
                    'playsinline': 1,
                    'enablejsapi': 1
                },
                events: {
                    'onReady': function(event) {
                        event.target.setVolume(100);
                    }
                }
            });
        }
    }

    // Initialize YouTube player on page load
    initYouTubePlayer();

    startBtn.addEventListener('click', countdownAndStart);

    async function countdownAndStart() {
        if (!accessGranted) {
            showAccessOverlay();
            return;
        }
        const countdownDiv = document.createElement('div');
        countdownDiv.className = 'countdown-overlay';
        document.body.appendChild(countdownDiv);

        for (let i = 3; i > 0; i--) {
            countdownDiv.textContent = i;
            await new Promise(resolve => setTimeout(resolve, 1000));
        }

        document.body.removeChild(countdownDiv);

        try {
            stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
            video.srcObject = stream;
            startBtn.disabled = true;
            finishBtn.disabled = false;

            // Start YouTube video playback after countdown ends
            function startYouTubeVideo() {
                if (youtubePlayer) {
                    try {
                        // Check if player is ready
                        if (youtubePlayer.getPlayerState() !== undefined) {
                            youtubePlayer.setVolume(100); // Set max volume
                            youtubePlayer.playVideo(); // Start playback
                        } else {
                            // Player not ready, wait a bit and retry
                            setTimeout(startYouTubeVideo, 200);
                        }
                    } catch (e) {
                        console.log('Error starting YouTube video:', e);
                        // Retry after a short delay
                        setTimeout(startYouTubeVideo, 500);
                    }
                } else if (YOUTUBE_ID) {
                    // Player not initialized yet, wait for it
                    setTimeout(startYouTubeVideo, 500);
                }
            }
            
            // Start YouTube video
            startYouTubeVideo();

            // Start timer
            seconds = 0;
            timerDisplay.textContent = '00:00';
            currentSubGerakan = null;
            
            // Update initial sub-gerakan display immediately
            updateSubGerakanDisplay(0);
            
            timerInterval = setInterval(() => {
                seconds++;
                const mins = Math.floor(seconds / 60);
                const secs = seconds % 60;
                timerDisplay.textContent = 
                    `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
                
                // Update sub-gerakan display every second
                updateSubGerakanDisplay(seconds);
            }, 1000);

        } catch (err) {
            alert('Could not access camera: ' + err);
        }
    }

    finishBtn.addEventListener('click', () => {
        // Check if finished early (before 4:24 = 264 seconds)
        if (seconds < TOTAL_DURATION) {
            // Show confirmation modal for early finish
            const currentGerakanNum = getCurrentGerakanNumber(seconds);
            stoppedAtGerakan = currentGerakanNum || 1;
            modalOverlay.classList.add('show');
        } else {
            // Completed all, finish normally
            finishAssessment(false);
        }
    });

    async function finishAssessment(isEarlyFinish) {
        // Stop camera
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
        }
        video.srcObject = null;

        // Stop YouTube video
        if (youtubePlayer && typeof youtubePlayer.pauseVideo === 'function') {
            try {
                youtubePlayer.pauseVideo();
            } catch (e) {
                console.log('Error stopping YouTube video:', e);
            }
        }

        // Stop timer
        if (timerInterval) {
            clearInterval(timerInterval);
        }

        // Determine which gerakan was completed
        let completedGerakan = MAX_SUBGERAKAN; // Default to all completed
        if (isEarlyFinish && stoppedAtGerakan !== null) {
            completedGerakan = stoppedAtGerakan;
        } else if (isEarlyFinish) {
            completedGerakan = getCurrentGerakanNumber(seconds) || 1;
        }

        // Show loading overlay
        document.getElementById("loadingOverlay").style.display = "flex";

        try {
            // LOGIC PERUBAHAN API URL DI SINI
            let apiUrl = "http://127.0.0.1:8001/api/givescore";
            
            // Cek jika Dance ID adalah 3, ubah endpoint
            if (DANCE_ID == "3") {
                apiUrl = "https://web-production-46d4.up.railway.app/api/bungong";
            }

            const response = await fetch(apiUrl);
            const result = await response.json();

            // Store result and completion info
            sessionStorage.setItem("dance_result_api", JSON.stringify(result));
            sessionStorage.setItem("completed_gerakan", completedGerakan.toString());
            sessionStorage.setItem("is_early_finish", isEarlyFinish.toString());
            sessionStorage.setItem("max_subgerakan", MAX_SUBGERAKAN.toString());

            window.location.href = "{% url 'dances:dance_result' dance.id %}";
        } catch (error) {
            alert("Failed to get score from API: " + error);
            document.getElementById("loadingOverlay").style.display = "none";
        }
    }
</script>

</body>
</html>
```

### dances/templates/dances/dance_detail.html

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Tria - Belajar Tarian Tradisional Indonesia</title>
  <link rel="icon" type="image/png" href="https://i.ibb.co.com/fY9F3RwF/tria.png" />
  <link rel="shortcut icon" type="image/png" href="https://i.ibb.co.com/fY9F3RwF/tria.png" />
  <style>
    :root {
      --tria-red: #e53935;
      --tria-orange: #ff9800;
      --tria-soft-bg: #fff7ec;
      --tria-orange-soft: #fff3e0;
      --tria-border: #f0e4d6;
      --tria-text: #222222;
      --tria-muted: #555555;
    }
  
    * {
      box-sizing: border-box;
    }
  
    body {
      background-color: var(--tria-soft-bg);
      color: var(--tria-text);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen,
        Ubuntu, Cantarell, "Open Sans", "Helvetica Neue", sans-serif;
      margin: 0;
      padding: 0;
    }
  
    a {
      text-decoration: none;
      color: inherit;
    }
  
    /* NAVBAR – same as landing */
    .navbar {
      background-color: #ffffff;
      border-bottom: 1px solid #f3eee7;
      position: sticky;
      top: 0;
      z-index: 50;
      backdrop-filter: blur(10px);
    }
  
    .nav-inner {
      max-width: 1100px;
      margin: 0 auto;
      padding: 0.75rem 1.5rem;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 1rem;
    }
  
    .nav-brand {
      display: flex;
      align-items: center;
      gap: 0.6rem;
    }
  
    .nav-logo {
      height: 36px;
      width: 36px;
      object-fit: contain;
    }
  
    .nav-title {
      font-weight: 700;
      letter-spacing: 0.03em;
      font-size: 1.1rem;
    }
  
    .nav-links {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      font-size: 0.95rem;
    }
  
    .nav-link {
      padding: 0.4rem 0.75rem;
      border-radius: 999px;
      transition: background-color 0.2s ease, color 0.2s ease, transform 0.1s ease;
    }
  
    .nav-link:hover {
      background-color: #fff1df;
      color: var(--tria-red);
      transform: translateY(-1px);
    }
  
    .nav-cta {
      background: linear-gradient(135deg, var(--tria-red), var(--tria-orange));
      color: #ffffff;
      font-weight: 600;
    }
  
    .nav-cta:hover {
      background: linear-gradient(135deg, #c62828, #fb8c00);
      color: #ffffff;
    }
  
    /* PAGE -------------------------------------------------------- */
  
    .page {
      max-width: 900px;
      margin: 2.5rem auto 3.5rem auto;
      padding: 2.3rem 2rem 2.8rem 2rem;
      background-color: #ffffff;
      border-radius: 2rem;
      border: 1px solid var(--tria-border);
      box-shadow: 0 18px 44px rgba(0, 0, 0, 0.06);
    }
  
    h1 {
      text-align: center;
      margin: 0 0 0.5rem 0;
      font-size: 1.9rem;
      font-weight: 800;
      letter-spacing: -0.01em;
    }
  
    .dance-subtitle {
      text-align: center;
      font-size: 0.96rem;
      color: var(--tria-muted);
      margin-bottom: 2rem;
      max-width: 620px;
      margin-inline: auto;
      line-height: 1.6;
    }
  
    .dance-image {
      width: 100%;
      max-width: 640px;
      height: auto;
      display: block;
      margin: 0 auto 1.4rem auto;
      border-radius: 1.4rem;
      box-shadow: 0 18px 40px rgba(0, 0, 0, 0.18);
    }
  
    .dance-description {
      max-width: 700px;
      margin: 0 auto 2rem auto;
      font-size: 0.98rem;
      line-height: 1.7;
      color: var(--tria-muted);
    }
  
    .nav-links-detail {
      display: flex;
      justify-content: center;
      gap: 0.75rem;
      flex-wrap: wrap;
      margin-top: 0.5rem;
    }
  
    .btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      padding: 0.7rem 1.6rem;
      border-radius: 999px;
      border: 1px solid transparent;
      font-size: 0.95rem;
      font-weight: 600;
      cursor: pointer;
      transition: background-color 0.2s ease, color 0.2s ease,
                  box-shadow 0.2s ease, transform 0.1s ease,
                  border-color 0.2s ease;
    }
  
    .btn-primary {
      background: linear-gradient(135deg, var(--tria-red), var(--tria-orange));
      color: #ffffff;
      box-shadow: 0 8px 18px rgba(229, 57, 53, 0.25);
    }
  
    .btn-primary:hover {
      background: linear-gradient(135deg, #c62828, #fb8c00);
      transform: translateY(-1px);
      box-shadow: 0 10px 24px rgba(229, 57, 53, 0.3);
    }
  
    .btn-outline {
      background-color: #ffffff;
      color: var(--tria-red);
      border-color: rgba(229, 57, 53, 0.3);
    }
  
    .btn-outline:hover {
      background-color: var(--tria-orange-soft);
      border-color: var(--tria-red);
      transform: translateY(-1px);
    }
  
    @media (max-width: 600px) {
      .page {
        padding-inline: 1.4rem;
        padding-top: 2.3rem;
      }
  
      h1 {
        font-size: 1.6rem;
      }
    }
  </style>
  
</head>
<body>
  {% include "partials/navbar.html" %}

  <main class="page">
    <h1>{{ dance.name }}</h1>
    <p class="dance-subtitle">
      Kenali karakter dan latar belakang tarian <strong>{{ dance.name }}</strong>
      sebelum masuk ke tahap tutorial dan asesmen.
    </p>

    {% if dance.image_url %}
      <img src="{{ dance.image_url }}" alt="{{ dance.name }}" class="dance-image" />
    {% endif %}

    <p class="dance-description">{{ dance.description }}</p>

    <div class="nav-links-detail">
      <a href="{% url 'dances:dance_tutorial' dance.id %}" class="btn btn-primary">Tutorial</a>
      <a href="{% url 'dances:dance_assessment' dance.id %}" class="btn btn-outline">Assessment</a>
    </div>
  </main>
</body>
</html>
```

### dances/templates/dances/dance_list.html

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Tria - Belajar Tarian Tradisional Indonesia</title>
    <link rel="icon" type="image/png" href="https://i.ibb.co.com/fY9F3RwF/tria.png" />
    <link rel="shortcut icon" type="image/png" href="https://i.ibb.co.com/fY9F3RwF/tria.png" />
    <style>
        :root {
            --tria-red: #e53935;
            --tria-orange: #ff9800;
            --tria-soft-bg: #fff7ec;
            --tria-orange-soft: #fff3e0;
            --tria-border: #f0e4d6;
            --tria-text: #222222;
            --tria-muted: #555555;
        }

        * { box-sizing: border-box; }

        body {
            background-color: var(--tria-soft-bg);
            color: var(--tria-text);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen,
            Ubuntu, Cantarell, "Open Sans", "Helvetica Neue", sans-serif;
            margin: 0;
            padding: 0;
        }

        a { text-decoration: none; color: inherit; }

        /* NAVBAR (shared class names with partial) */
        .navbar {
            background-color: #ffffff;
            border-bottom: 1px solid #f3eee7;
            position: sticky;
            top: 0;
            z-index: 50;
            backdrop-filter: blur(10px);
        }

        .nav-inner {
            max-width: 1100px;
            margin: 0 auto;
            padding: 0.75rem 1.5rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
        }

        .nav-brand { display: flex; align-items: center; gap: 0.6rem; }
        .nav-logo { height: 36px; width: 36px; object-fit: contain; }

        .nav-title {
            font-weight: 700;
            letter-spacing: 0.03em;
            font-size: 1.1rem;
        }

        .nav-links {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            font-size: 0.95rem;
        }

        .nav-link {
            padding: 0.4rem 0.75rem;
            border-radius: 999px;
            transition: background-color 0.2s ease, color 0.2s ease, transform 0.1s ease;
        }

        .nav-link:hover {
            background-color: #fff1df;
            color: var(--tria-red);
            transform: translateY(-1px);
        }

        .nav-cta {
            background: linear-gradient(135deg, var(--tria-red), var(--tria-orange));
            color: #ffffff;
            font-weight: 600;
        }

        .nav-cta:hover {
            background: linear-gradient(135deg, #c62828, #fb8c00);
            color: #ffffff;
        }

        /* PAGE ------------------------------------------------------ */

        .page {
            max-width: 1100px;
            margin: 2.5rem auto 3.5rem auto;
            padding: 2.3rem 2rem 2.8rem 2rem;
            background-color: #ffffff;
            border-radius: 2rem;
            border: 1px solid var(--tria-border);
            box-shadow: 0 18px 44px rgba(0, 0, 0, 0.06);
        }

        .section-title {
            text-align: center;
            margin: 0 0 0.4rem 0;
            font-size: 1.9rem;
            font-weight: 800;
            letter-spacing: -0.01em;
        }

        .section-subtitle {
            text-align: center;
            font-size: 0.98rem;
            color: var(--tria-muted);
            margin-bottom: 2rem;
            max-width: 620px;
            margin-inline: auto;
            line-height: 1.6;
        }

        .dance-grid {
            list-style: none;
            padding: 0;
            margin: 0;
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
            gap: 1.5rem;
        }

        .dance-card {
            background-color: #ffffff;
            border-radius: 1.4rem;
            border: 1px solid var(--tria-border);
            padding: 1rem 1.1rem 1.4rem 1.1rem;
            box-shadow: 0 12px 28px rgba(0, 0, 0, 0.04);
            display: flex;
            flex-direction: column;
            gap: 0.6rem;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }

        .dance-card:hover {
            transform: translateY(-6px);
            box-shadow: 0 18px 42px rgba(0, 0, 0, 0.08);
        }

        .dance-image {
            width: 100%;
            height: 150px;
            object-fit: cover;
            border-radius: 0.9rem;
            margin-bottom: 0.6rem;
        }

        .dance-link {
            color: var(--tria-text);
            font-weight: 700;
            font-size: 1.05rem;
            margin-bottom: 0.1rem;
        }

        .dance-link:hover { color: var(--tria-red); }

        .dance-description {
            font-size: 0.9rem;
            color: var(--tria-muted);
            min-height: 3rem;
            line-height: 1.5;
        }

        .dance-actions { margin-top: 0.4rem; }

        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 0.55rem 1.3rem;
            border-radius: 999px;
            border: 1px solid transparent;
            font-size: 0.9rem;
            font-weight: 600;
            cursor: pointer;
            transition: background-color 0.2s ease, color 0.2s ease,
            box-shadow 0.2s ease, transform 0.1s ease,
            border-color 0.2s ease;
        }

        .btn-primary {
            background: linear-gradient(135deg, var(--tria-red), var(--tria-orange));
            color: #ffffff;
            box-shadow: 0 6px 16px rgba(229, 57, 53, 0.25);
        }

        .btn-primary:hover {
            background: linear-gradient(135deg, #c62828, #fb8c00);
            transform: translateY(-1px);
            box-shadow: 0 8px 20px rgba(229, 57, 53, 0.3);
        }

        /* FEATURED LENGGANG NYAI ----------------------------------- */

        .featured-dance {
            max-width: 1100px;
            margin: 2.5rem auto 0;
            padding: 0 2rem;
        }

        .featured-grid {
            display: grid;
            grid-template-columns: minmax(0, 1.35fr) minmax(0, 1fr);
            gap: 1.5rem;
        }

        .featured-media {
            position: relative;
            border-radius: 32px;
            overflow: hidden;
            min-height: 260px;
            box-shadow: 0 18px 45px rgba(0,0,0,0.18);
        }

        .featured-media img {
            width: 100%;
            height: 100%;
            object-fit: cover;
            display: block;
        }

        .featured-overlay {
            position: absolute;
            inset: 0;
            background: linear-gradient(
                    120deg,
                    rgba(0,0,0,0.65),
                    rgba(0,0,0,0.25),
                    rgba(0,0,0,0.02)
            );
            display: flex;
            flex-direction: column;
            justify-content: flex-end;
            padding: 1.5rem 1.8rem;
            color: #fff;
        }

        .featured-kicker {
            font-size: 0.9rem;
            letter-spacing: 0.15em;
            text-transform: uppercase;
            opacity: 0.9;
            margin-bottom: 0.4rem;
        }

        .featured-title {
            font-size: 1.4rem;
            font-weight: 800;
            margin: 0 0 0.3rem 0;
        }

        .featured-text {
            font-size: 0.95rem;
            max-width: 32rem;
        }

        .featured-info-card {
            border-radius: 32px;
            background: white;
            padding: 2rem 2.2rem;
            box-shadow: 0 18px 45px rgba(0,0,0,0.06);
            display: flex;
            flex-direction: column;
            justify-content: center;
        }

        .featured-info-title {
            font-size: 1.35rem;
            font-weight: 800;
            margin-bottom: 0.8rem;
        }

        .featured-info-body {
            font-size: 0.95rem;
            color: #555;
            line-height: 1.6;
            margin-bottom: 1.4rem;
        }

        .featured-cta {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 0.8rem 1.4rem;
            border-radius: 999px;
            background: linear-gradient(135deg,var(--tria-red),var(--tria-orange));
            color: #fff;
            font-weight: 700;
            font-size: 0.95rem;
            border: none;
            text-decoration: none;
            box-shadow: 0 14px 32px rgba(229,57,53,0.28);
            transition: transform 0.12s ease, box-shadow 0.12s ease;
        }

        .featured-cta:hover {
            transform: translateY(-1px);
            box-shadow: 0 18px 40px rgba(229,57,53,0.33);
        }

        @media (max-width: 900px) {
            .featured-dance { padding-inline: 1.5rem; }
            .featured-grid {
                grid-template-columns: minmax(0,1fr);
            }
            .featured-info-card {
                padding: 1.6rem 1.6rem 1.7rem;
            }
        }

        @media (max-width: 600px) {
            .page {
                padding-inline: 1.4rem;
                padding-top: 2.3rem;
            }

            .dance-grid { grid-template-columns: 1fr; }
        }
    </style>
</head>

<body>
{% load static %}
{% include "partials/navbar.html" %}

    <!-- FEATURED TARI LENGGANG NYAI -->
    <section class="featured-dance">
        <div class="featured-grid">
            <!-- LEFT: image + overlay -->
            <article class="featured-media">
                <img
                    src="https://i.ibb.co.com/39BkHzbw/Screenshot-2025-11-27-at-00-23-13.png"
                    alt="Penari membawakan Tari Lenggang Nyai"
                />
                <div class="featured-overlay">
                    <div class="featured-kicker">Featured Class</div>
                    <h2 class="featured-title">Latihan Lenggang Nyai yang terasa hidup</h2>
                    <p class="featured-text">
                        Rasakan suasana Betawi yang ceria lewat gerak lenggang yang anggun dan ekspresif.
                    </p>
                </div>
            </article>

            <!-- RIGHT: description + button -->
            <aside class="featured-info-card">
                <h3 class="featured-info-title">Featured: Tari Lenggang Nyai</h3>
                <p class="featured-info-body">
                    Dalam Tria, Lenggang Nyai disusun per level sehingga pemula pun bisa mengikuti:
                    mulai dari pengenalan pola langkah, penggunaan selendang, hingga dinamika ekspresi
                    wajah yang kuat. Setiap sesi dilengkapi video, urutan gerak, dan tips guru sanggar
                    agar latihanmu terasa seperti dibimbing langsung di studio.
                </p>
                <a href="{% url 'dances:dance_detail' 4 %}"
                class="featured-cta">
                    Belajar sekarang
                </a>

            </aside>
        </div>
    </section>

    <main class="page">
        <h1 class="section-title">Tarian Tradisional Indonesia</h1>
        <p class="section-subtitle">
            Pilih tarian tradisional yang ingin kamu pelajari. Setiap tarian dilengkapi
            dengan tutorial dan asesmen untuk membantumu berkembang.
        </p>

        <ul class="dance-grid">
            {% for dance in dances %}
                <li class="dance-card">
                    {% if dance.image_url %}
                        <img src="{{ dance.image_url }}" alt="{{ dance.name }}" class="dance-image" />
                    {% endif %}
                    <a href="{% url 'dances:dance_detail' dance.id %}" class="dance-link">
                        {{ dance.name }}
                    </a>
                    {% if dance.difficulty %}
                    <span class="dance-difficulty" style="display: inline-block; margin-top: 0.3rem; font-size: 0.75rem; font-weight: 600; color: var(--tria-muted); text-transform: uppercase; letter-spacing: 0.05em;">
                        Tingkat Kesulitan: {{ dance.difficulty }}
                    </span>
                    {% endif %}
                    <p class="dance-description">{{ dance.description }}</p>
                    <div class="dance-actions">
                        <a href="{% url 'dances:dance_detail' dance.id %}" class="btn btn-primary">
                            Belajar
                        </a>
                    </div>
                </li>
            {% endfor %}
        </ul>
    </main>
</body>
</html>
```

### dances/templates/dances/dance_result.html

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Tria - Belajar Tarian Tradisional Indonesia</title>
    <link rel="icon" type="image/png" href="https://i.ibb.co.com/fY9F3RwF/tria.png" />
    <link rel="shortcut icon" type="image/png" href="https://i.ibb.co.com/fY9F3RwF/tria.png" />
    <style>
        :root {
            --tria-red: #e53935;
            --tria-orange: #ff9800;
            --tria-soft-bg: #fff7ec;
            --tria-orange-soft: #fff3e0;
            --tria-border: #f0e4d6;
            --tria-text: #222222;
            --tria-muted: #555555;
        }
    
        * { box-sizing: border-box; }
    
        body {
            background-color: var(--tria-soft-bg);
            color: var(--tria-text);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen,
                Ubuntu, Cantarell, "Open Sans", "Helvetica Neue", sans-serif;
            margin: 0;
            padding: 0;
        }
    
        a { text-decoration: none; color: inherit; }
    
        /* NAVBAR */
        .navbar {
            background-color: #ffffff;
            border-bottom: 1px solid #f3eee7;
            position: sticky;
            top: 0;
            z-index: 50;
            backdrop-filter: blur(10px);
        }
    
        .nav-inner {
            max-width: 1100px;
            margin: 0 auto;
            padding: 0.75rem 1.5rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
        }
    
        .nav-brand { display: flex; align-items: center; gap: 0.6rem; }
    
        .nav-logo { height: 36px; width: 36px; object-fit: contain; }
    
        .nav-title {
            font-weight: 700;
            letter-spacing: 0.03em;
            font-size: 1.1rem;
        }
    
        .nav-links {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            font-size: 0.95rem;
        }
    
        .nav-link {
            padding: 0.4rem 0.75rem;
            border-radius: 999px;
            transition: background-color 0.2s ease, color 0.2s ease, transform 0.1s ease;
        }
    
        .nav-link:hover {
            background-color: #fff1df;
            color: var(--tria-red);
            transform: translateY(-1px);
        }
    
        .nav-cta {
            background: linear-gradient(135deg, var(--tria-red), var(--tria-orange));
            color: #ffffff;
            font-weight: 600;
        }
    
        .nav-cta:hover {
            background: linear-gradient(135deg, #c62828, #fb8c00);
            color: #ffffff;
        }
    
        /* PAGE ------------------------------------------------------ */
    
        .page {
            max-width: 700px;
            margin: 2.5rem auto 3.5rem auto;
            padding: 2.3rem 2rem 2.8rem 2rem;
            background-color: #ffffff;
            border-radius: 2rem;
            border: 1px solid var(--tria-border);
            box-shadow: 0 18px 44px rgba(0, 0, 0, 0.06);
        }
    
        .section-title {
            font-size: 1.8rem;
            margin: 0 0 0.4rem 0;
            text-align: center;
            font-weight: 800;
            letter-spacing: -0.01em;
        }
    
        .section-subtitle {
            text-align: center;
            font-size: 0.96rem;
            color: var(--tria-muted);
            margin-bottom: 2rem;
            max-width: 520px;
            margin-inline: auto;
            line-height: 1.6;
        }
    
        .result-card {
            background-color: #ffffff;
            border-radius: 1.4rem;
            border: 1px solid var(--tria-border);
            padding: 1.8rem 1.9rem;
            box-shadow: 0 16px 34px rgba(0, 0, 0, 0.06);
            text-align: center;
        }
    
        .score-label {
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: var(--tria-muted);
        }
    
        .score-value {
            font-size: 2.4rem;
            font-weight: 800;
            margin: 0.3rem 0 0.4rem 0;
            background: linear-gradient(135deg, var(--tria-red), var(--tria-orange));
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
        }
    
        .result-actions {
            display: flex;
            justify-content: center;
            flex-wrap: wrap;
            gap: 0.6rem;
        }
    
        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 0.7rem 1.6rem;
            border-radius: 999px;
            border: 1px solid transparent;
            font-size: 0.95rem;
            font-weight: 600;
            cursor: pointer;
            transition: background-color 0.2s ease, color 0.2s ease,
                        box-shadow 0.2s ease, transform 0.1s ease,
                        border-color 0.2s ease;
        }
    
        .btn-primary {
            background: linear-gradient(135deg, var(--tria-red), var(--tria-orange));
            color: #ffffff;
            box-shadow: 0 8px 18px rgba(229, 57, 53, 0.25);
        }
    
        .btn-primary:hover {
            background: linear-gradient(135deg, #c62828, #fb8c00);
            transform: translateY(-1px);
            box-shadow: 0 10px 24px rgba(229, 57, 53, 0.3);
        }
    
        .btn-outline {
            background-color: #ffffff;
            color: var(--tria-red);
            border-color: rgba(229, 57, 53, 0.3);
        }
    
        .btn-outline:hover {
            background-color: var(--tria-orange-soft);
            border-color: var(--tria-red);
            transform: translateY(-1px);
        }
    
        /* Sanggar Recommendations */
        .sanggar-recommendations {
            margin-top: 3rem;
            padding-top: 2rem;
            border-top: 2px solid var(--tria-border);
        }
    
        .sanggar-recommendations-title {
            font-size: 1.3rem;
            font-weight: 700;
            text-align: center;
            margin-bottom: 1.5rem;
            color: var(--tria-text);
        }
    
        .sanggar-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 1.2rem;
            margin-top: 1.5rem;
        }
    
        .sanggar-card {
            background-color: #ffffff;
            border: 1px solid var(--tria-border);
            border-radius: 1.2rem;
            overflow: hidden;
            transition: all 0.3s ease;
            cursor: pointer;
            text-decoration: none;
            color: inherit;
            display: block;
        }
    
        .sanggar-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 12px 28px rgba(0, 0, 0, 0.1);
            border-color: var(--tria-red);
        }
    
        .sanggar-image {
            width: 100%;
            height: 160px;
            object-fit: cover;
            display: block;
        }
    
        .sanggar-info {
            padding: 1.2rem;
        }
    
        .sanggar-name {
            font-size: 1.05rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
            color: var(--tria-text);
        }
    
        .sanggar-description {
            font-size: 0.88rem;
            color: var(--tria-muted);
            line-height: 1.5;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }
    
        @media (max-width: 600px) {
            .page {
                padding-inline: 1.4rem;
                padding-top: 2.3rem;
            }
    
            .sanggar-grid {
                grid-template-columns: minmax(0, 1fr);
            }
        }
    </style>
    
    
</head>
<body>

{% include 'partials/navbar.html' %}

<main class="page">
    <h1 class="section-title" style="text-align: center;">{{ dance.name }} – Hasil Asesmen</h1>
    <p class="section-subtitle" style="text-align: center;">
        Berikut adalah hasil asesmen gerakan tari <strong>{{ dance.name }}</strong>.
    </p>

    <section class="result-card">
        <div class="score-label">Skor Rata-Rata Kamu</div>
        <div id="scoreDisplay" class="score-value">0%</div>
    
        <h3 style="margin-top: 1.5rem; text-align: center; color: var(--tria-muted);">
            Rincian Nilai Per Aspek
        </h3>
    
        <table id="scoreTable" style="width: 100%; margin-top: 1rem; border-collapse: collapse;">
            <thead>
                <tr style="background-color: var(--tria-orange-soft);">
                    <th style="text-align: left; padding: 12px;">Aspek Gerakan</th>
                    <th style="text-align: right; padding: 12px;">Skor</th>
                </tr>
            </thead>
            <tbody></tbody>
        </table>
    
        <h3 style="margin-top: 2rem; text-align: center; color: var(--tria-muted);">
            Feedback Asesmen
        </h3>
    
        <ul id="feedbackContainer" style="padding: 0; list-style: none; margin-top: 1rem;"></ul>
    
        <div class="result-actions" style="margin-top: 2rem;">
            <form action="{% url 'dances:dance_assessment' dance.id %}" method="get">
                <button type="submit" class="btn btn-primary">Try Again</button>
            </form>
            <form action="{% url 'dances:dance_list' %}" method="get">
                <button type="submit" class="btn btn-outline">Dances</button>
            </form>
        </div>
    </section>
    
    <!-- Sanggar Recommendations -->
    {% if recommended_sanggars %}
    <section class="sanggar-recommendations">
        <h2 class="sanggar-recommendations-title">
            Rekomendasi Sanggar untuk Mempelajari Tarian {{ dance.name }} lebih lanjut
        </h2>
        <div class="sanggar-grid">
            {% for sanggar in recommended_sanggars %}
            <a href="{% url 'daftarsanggar:detail' sanggar.sanggar_id %}" class="sanggar-card">
                <img src="{{ sanggar.image }}" alt="{{ sanggar.nama_sanggar }}" class="sanggar-image" onerror="this.src='https://via.placeholder.com/400x300?text=No+Image'">
                <div class="sanggar-info">
                    <h3 class="sanggar-name">{{ sanggar.nama_sanggar }}</h3>
                </div>
            </a>
            {% endfor %}
        </div>
    </section>
    {% endif %}
</main>

<script>
    const data = JSON.parse(sessionStorage.getItem("dance_result_api"));
    const completedGerakan = parseInt(sessionStorage.getItem("completed_gerakan") || "15");
    const isEarlyFinish = sessionStorage.getItem("is_early_finish") === "true";
    const maxSubgerakan = parseInt(sessionStorage.getItem("max_subgerakan") || "15");

    if (data) {
        // Clone the scores array to avoid modifying the original
        let scores = [...(data.score || [])];
        
        // Ensure we have exactly maxSubgerakan scores
        while (scores.length < maxSubgerakan) {
            scores.push(0);
        }
        
        // Trim to maxSubgerakan if somehow more
        scores = scores.slice(0, maxSubgerakan);

        // If assessment was finished early, set incomplete gerakans to 0
        if (isEarlyFinish && completedGerakan < maxSubgerakan) {
            for (let i = completedGerakan; i < maxSubgerakan; i++) {
                scores[i] = 0;
            }
        }

        // Recalculate average score based on all gerakans
        const totalScore = scores.reduce((sum, score) => {
            const numScore = parseFloat(score) || 0;
            return sum + numScore;
        }, 0);
        const averageScore = Math.round((totalScore / maxSubgerakan) * 100) / 100;

        document.getElementById("scoreDisplay").textContent = averageScore.toFixed(0) + "%";

        const tbody = document.querySelector("#scoreTable tbody");
        tbody.innerHTML = "";

        // Generate Sub Gerakan dynamically based on maxSubgerakan
        scores.forEach((score, i) => {
            const row = document.createElement("tr");
            const isIncomplete = isEarlyFinish && (i + 1) > completedGerakan;
            
            row.innerHTML = `
                <td style="padding: 10px; border-bottom: 1px solid var(--tria-border);">
                    Sub Gerakan ${i + 1}
                    ${isIncomplete ? '<span style="color: var(--tria-muted); font-size: 0.85em;"> (Tidak diselesaikan)</span>' : ''}
                </td>
                <td style="padding: 10px; border-bottom: 1px solid var(--tria-border); text-align: right;">
                    <strong style="${isIncomplete ? 'color: var(--tria-muted);' : ''}">${score}</strong>
                </td>
            `;
            tbody.appendChild(row);
        });

        const feedbackContainer = document.getElementById("feedbackContainer");
        feedbackContainer.innerHTML = "";

        // Only show feedback for completed gerakans
        const feedbackToShow = data.feedback ? data.feedback.slice(0, completedGerakan) : [];
        
        if (feedbackToShow.length > 0) {
            feedbackToShow.forEach((text, i) => {
                const box = document.createElement("li");
                box.style.background = "var(--tria-orange-soft)";
                box.style.borderLeft = "5px solid var(--tria-orange)";
                box.style.padding = "12px 14px";
                box.style.borderRadius = "12px";
                box.style.marginBottom = "10px";
                box.innerHTML = `<strong>${i + 1}.</strong> ${text}`;
                feedbackContainer.appendChild(box);
            });
        }

        // Show warning if assessment was incomplete
        if (isEarlyFinish && completedGerakan < maxSubgerakan) {
            const warningBox = document.createElement("li");
            warningBox.style.background = "#fff3cd";
            warningBox.style.borderLeft = "5px solid #ffc107";
            warningBox.style.padding = "12px 14px";
            warningBox.style.borderRadius = "12px";
            warningBox.style.marginBottom = "10px";
            warningBox.innerHTML = `<strong>Catatan:</strong> Asesmen diakhiri sebelum selesai. Sub Gerakan ${completedGerakan + 1} hingga ${maxSubgerakan} mendapat nilai 0 karena tidak diselesaikan.`;
            feedbackContainer.insertBefore(warningBox, feedbackContainer.firstChild);
        }
    }
</script>


</body>
</html>
```

### dances/templates/dances/dance_tutorial.html

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Tria - Belajar Tarian Tradisional Indonesia</title>
    <link rel="icon" type="image/png" href="https://i.ibb.co.com/fY9F3RwF/tria.png" />
    <link rel="shortcut icon" type="image/png" href="https://i.ibb.co.com/fY9F3RwF/tria.png" />
    <style>
        :root {
            --tria-red: #e53935;
            --tria-orange: #ff9800;
            --tria-soft-bg: #fff7ec;
            --tria-orange-soft: #fff3e0;
            --tria-border: #f0e4d6;
            --tria-text: #222222;
            --tria-muted: #555555;
        }
    
        * { box-sizing: border-box; }
    
        body {
            background-color: var(--tria-soft-bg);
            color: var(--tria-text);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen,
                Ubuntu, Cantarell, "Open Sans", "Helvetica Neue", sans-serif;
            margin: 0;
            padding: 0;
        }
    
        a { text-decoration: none; color: inherit; }
    
        /* NAVBAR */
        .navbar {
            background-color: #ffffff;
            border-bottom: 1px solid #f3eee7;
            position: sticky;
            top: 0;
            z-index: 50;
            backdrop-filter: blur(10px);
        }
    
        .nav-inner {
            max-width: 1100px;
            margin: 0 auto;
            padding: 0.75rem 1.5rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
        }
    
        .nav-brand { display: flex; align-items: center; gap: 0.6rem; }
    
        .nav-logo { height: 36px; width: 36px; object-fit: contain; }
    
        .nav-title {
            font-weight: 700;
            letter-spacing: 0.03em;
            font-size: 1.1rem;
        }
    
        .nav-links {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            font-size: 0.95rem;
        }
    
        .nav-link {
            padding: 0.4rem 0.75rem;
            border-radius: 999px;
            transition: background-color 0.2s ease, color 0.2s ease, transform 0.1s ease;
        }
    
        .nav-link:hover {
            background-color: #fff1df;
            color: var(--tria-red);
            transform: translateY(-1px);
        }
    
        .nav-cta {
            background: linear-gradient(135deg, var(--tria-red), var(--tria-orange));
            color: #ffffff;
            font-weight: 600;
        }
    
        .nav-cta:hover {
            background: linear-gradient(135deg, #c62828, #fb8c00);
            color: #ffffff;
        }
    
        /* PAGE */
        .page {
            max-width: 1100px;
            margin: 2.5rem auto 3.5rem auto;
            padding: 0 1rem;
        }
    
        .section-title {
            font-size: 1.8rem;
            margin: 0 0 0.4rem 0;
            text-align: center;
            font-weight: 800;
            letter-spacing: -0.01em;
        }

        .section-title .dance-name {
            background: linear-gradient(135deg, var(--tria-red), #e65100);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-weight: 800;
        }
    
        .section-subtitle {
            text-align: center;
            font-size: 0.96rem;
            color: var(--tria-muted);
            margin-bottom: 2rem;
            max-width: 640px;
            margin-inline: auto;
            line-height: 1.6;
        }

        /* MAIN CONTAINER - Gabung semua dalam satu card */
        .main-container {
            background-color: #ffffff;
            border-radius: 1.4rem;
            border: 1px solid var(--tria-border);
            box-shadow: 0 14px 30px rgba(0, 0, 0, 0.05);
            overflow: hidden;
        }

        /* VIDEO SECTION */
        .video-section {
            padding: 1.2rem 1.2rem 0 1.2rem;
        }

        .main-video-wrapper {
            text-align: center;
        }

        .main-video-wrapper iframe {
            width: 100%;
            max-width: 100%;
            height: 500px;
            border: none;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
        }

        /* INFO CARD */
        .info-card {
            padding: 1.4rem 1.6rem;
            border-top: 1px solid var(--tria-border);
            margin-top: 1.2rem;
        }

        .info-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.2rem;
        }

        .info-item {
            text-align: center;
            padding: 1rem;
            background: linear-gradient(135deg, var(--tria-orange-soft), #ffffff);
            border-radius: 0.9rem;
            border: 1px solid rgba(229, 57, 53, 0.15);
        }

        .info-label {
            font-size: 0.8rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: var(--tria-muted);
            margin-bottom: 0.3rem;
        }

        .info-value {
            font-size: 1.2rem;
            font-weight: 700;
            color: var(--tria-red);
        }

        /* SUB-GERAKAN SECTION */
        .subgerakan-section {
            padding: 1.4rem 1.2rem 1.2rem 1.2rem;
            border-top: 1px solid var(--tria-border);
        }

        .subgerakan-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 1.2rem;
            gap: 1rem;
            flex-wrap: wrap;
        }

        .subgerakan-title {
            font-size: 1.4rem;
            font-weight: 700;
            margin: 0;
        }

        .subgerakan-list {
            display: grid;
            gap: 0.9rem;
        }

        /* ACCORDION CARD */
        .accordion-card {
            background-color: #fffbf7;
            border-radius: 1rem;
            border: 1px solid var(--tria-border);
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
            transition: box-shadow 0.3s ease;
        }

        .accordion-card:hover {
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
        }

        .accordion-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 1rem 1.2rem;
            cursor: pointer;
            user-select: none;
            transition: background-color 0.2s ease;
        }

        .accordion-header:hover {
            background-color: #fff7ec;
        }

        .accordion-left {
            display: flex;
            align-items: center;
            gap: 0.9rem;
            flex: 1;
        }

        .step-badge {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            background: linear-gradient(135deg, var(--tria-red), var(--tria-orange));
            color: #ffffff;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.85rem;
            font-weight: 700;
            flex-shrink: 0;
        }

        .accordion-title-wrapper {
            flex: 1;
        }

        .accordion-title {
            font-size: 0.95rem;
            font-weight: 600;
            color: var(--tria-text);
            margin-bottom: 0.2rem;
        }

        .accordion-duration {
            font-size: 0.8rem;
            color: var(--tria-muted);
        }

        .accordion-icon {
            width: 24px;
            height: 24px;
            border-radius: 50%;
            background-color: var(--tria-orange-soft);
            display: flex;
            align-items: center;
            justify-content: center;
            transition: transform 0.3s ease, background-color 0.2s ease;
            flex-shrink: 0;
        }

        .accordion-icon svg {
            width: 14px;
            height: 14px;
            fill: var(--tria-red);
            transition: transform 0.3s ease;
        }

        .accordion-card.active .accordion-icon {
            background-color: var(--tria-red);
        }

        .accordion-card.active .accordion-icon svg {
            transform: rotate(180deg);
            fill: #ffffff;
        }

        .accordion-content {
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.4s ease, padding 0.4s ease;
        }

        .accordion-card.active .accordion-content {
            max-height: 600px;
        }

        .accordion-inner {
            padding: 0 1.2rem 1.2rem 1.2rem;
        }

        .accordion-description {
            font-size: 0.9rem;
            color: var(--tria-muted);
            line-height: 1.6;
            margin-bottom: 1rem;
            padding: 0.8rem 1rem;
            background-color: #ffffff;
            border-radius: 0.6rem;
            border-left: 3px solid var(--tria-orange);
        }

        .accordion-video {
            text-align: center;
        }

        .accordion-video iframe {
            width: 100%;
            height: 320px;
            border: none;
            border-radius: 10px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }

        /* BUTTON */
        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 0.75rem 1.8rem;
            border-radius: 999px;
            border: 1px solid transparent;
            font-size: 0.95rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .btn-primary {
            background: linear-gradient(135deg, var(--tria-red), var(--tria-orange));
            color: #ffffff;
            box-shadow: 0 6px 16px rgba(229, 57, 53, 0.25);
        }

        .btn-primary:hover {
            background: linear-gradient(135deg, #c62828, #fb8c00);
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(229, 57, 53, 0.35);
        }

        @media (max-width: 768px) {
            .main-video-wrapper iframe {
                height: 280px;
            }

            .accordion-video iframe {
                height: 220px;
            }

            .info-grid {
                grid-template-columns: 1fr;
            }

            .subgerakan-header {
                flex-direction: column;
                align-items: stretch;
            }

            .btn {
                width: 100%;
            }
        }

        @media (max-width: 600px) {
            .page {
                padding-inline: 1rem;
            }

            .video-section,
            .info-card,
            .subgerakan-section {
                padding-inline: 1rem;
            }
        }
    </style>
</head>
<body>
    {% include "partials/navbar.html" %}

    <main class="page">
        <h1 class="section-title"><span class="dance-name">{{ dance.name }}</span> – Tutorial</h1>
        <p class="section-subtitle">
            Tonton video tutorial lengkap dan pelajari setiap sub-gerakan 
            <strong>{{ dance.name }}</strong> secara detail dengan video berdurasi spesifik.
        </p>

        <!-- MAIN CONTAINER - Semua jadi satu -->
        <div class="main-container">
            <!-- VIDEO SECTION -->
            <section class="video-section">
                <div class="main-video-wrapper">
                    {% if dance.youtube_id %}
                    <iframe 
                        src="https://www.youtube.com/embed/{{ dance.youtube_id }}?si=qpH0uzIS1VPT_5hb" 
                        title="YouTube video player" 
                        frameborder="0" 
                        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" 
                        referrerpolicy="strict-origin-when-cross-origin" 
                        allowfullscreen>
                    </iframe>
                    {% else %}
                    <div style="display: flex; align-items: center; justify-content: center; height: 500px; background-color: #f5f5f5; border-radius: 12px; color: var(--tria-muted);">
                        <p style="text-align: center; font-size: 1.1rem;">Video tutorial belum tersedia untuk tarian ini.</p>
                    </div>
                    {% endif %}
                </div>
            </section>

            <!-- INFO CARD -->
            <section class="info-card">
                <div class="info-grid">
                    <div class="info-item">
                        <div class="info-label">Durasi Total</div>
                        <div class="info-value">{{ dance.durasi_formatted|default:"0:00" }}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Daerah Asal</div>
                        <div class="info-value">{{ dance.asal_daerah|default:"-" }}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Tingkat Kesulitan</div>
                        <div class="info-value">{{ dance.difficulty|default:"Menengah" }}</div>
                    </div>
                </div>
            </section>

            <!-- SUB-GERAKAN ACCORDION -->
            <section class="subgerakan-section">
                <div class="subgerakan-header">
                    <h2 class="subgerakan-title" id="subgerakanTitle">Sub-Gerakan Detail</h2>
                    <form action="{% url 'dances:dance_assessment' dance.id %}" method="get">
                        <button type="submit" class="btn btn-primary">Mulai Asesmen</button>
                    </form>
                </div>
                
                <div class="subgerakan-list" id="subgerakanList">
                    <!-- Sub-gerakan will be generated dynamically by JavaScript -->
                </div>
            </section>
        </div>
    </main>

    <script>
        // Get data from Django template
        const youtubeId = "{{ dance.youtube_id|default:'' }}";
        const totalDuration = parseInt("{{ dance.durasi_video|default:264 }}") || 264;
        const maxSubgerakan = parseInt("{{ dance.max_subgerakan|default:15 }}") || 15;
        const SUBGERAKAN_DURATION = 18; // Each sub-gerakan is 18 seconds
        
        // Generic descriptions that can be reused
        const genericDescriptions = [
            "Berdiri tegak dengan kaki rapat, tangan di samping badan. Siapkan postur tubuh dan fokus sebelum memulai gerakan.",
            "Angkat tangan kanan ke depan dengan telapak menghadap ke atas, gerakan lembut dan terkontrol.",
            "Ikuti dengan tangan kiri, angkat ke samping dengan gerakan yang sama elegan dan terkontrol.",
            "Melangkah ke kanan dengan kaki kanan, berat badan mengikuti dengan lembut. Jaga keseimbangan.",
            "Putar badan 90 derajat ke kanan dengan gerakan halus, pandangan mengikuti arah putaran.",
            "Kedua tangan bergerak secara sinkron membentuk pola melingkar di depan dada dengan irama yang konsisten.",
            "Gerakan transisi yang menghubungkan bagian pertama dengan bagian kedua, tempo mulai meningkat.",
            "Gerakan kaki yang lebih cepat dengan pola maju-mundur, koordinasi dengan tangan tetap terjaga.",
            "Lakukan putaran 360 derajat dengan postur tegap, jaga keseimbangan dan fokus pada satu titik.",
            "Ekspresikan emosi melalui gerakan tangan yang lebih bebas namun tetap mengikuti pola dasar tarian.",
            "Bergerak diagonal ke kanan depan dengan langkah terukur, tangan mengiringi dengan gerakan anggun.",
            "Bagian paling energik dari tarian, kombinasi semua elemen dengan tempo maksimal dan ekspresi penuh.",
            "Tempo mulai melambat, gerakan menjadi lebih tenang sebagai persiapan menuju penutupan.",
            "Kembali ke posisi tengah dengan gerakan lembut, mengumpulkan energi untuk pose akhir.",
            "Tahan pose akhir dengan sempurna, kedua tangan di depan dada, postur tegap menunjukkan penyelesaian tarian.",
            "Lanjutkan gerakan dengan irama yang konsisten, jaga koordinasi antara tangan dan kaki.",
            "Perkuat ekspresi wajah dan gerakan tubuh, tunjukkan karakteristik tarian dengan penuh percaya diri.",
            "Pertahankan ritme dan tempo, sinkronkan gerakan dengan musik yang mengiringi.",
            "Lakukan variasi gerakan dengan tetap mempertahankan pola dasar tarian yang telah dipelajari.",
            "Fokus pada kelenturan tubuh dan kelancaran transisi antar gerakan."
        ];
        
        // Helper function to format time (seconds to mm:ss)
        function formatTime(seconds) {
            const mins = Math.floor(seconds / 60);
            const secs = seconds % 60;
            return `${mins}:${secs.toString().padStart(2, '0')}`;
        }
        
        // Generate sub-gerakan list dynamically
        function generateSubgerakanList() {
            const subgerakanList = document.getElementById('subgerakanList');
            const subgerakanTitle = document.getElementById('subgerakanTitle');
            subgerakanTitle.textContent = `${maxSubgerakan} Sub-Gerakan Detail`;
            
            subgerakanList.innerHTML = '';
            
            for (let i = 0; i < maxSubgerakan; i++) {
                const start = i * SUBGERAKAN_DURATION;
                const end = Math.min(start + SUBGERAKAN_DURATION, totalDuration);
                if (start >= totalDuration) break;
                
                const num = i + 1;
                const description = genericDescriptions[i % genericDescriptions.length];
                
                const card = document.createElement('div');
                card.className = 'accordion-card';
                card.setAttribute('data-start', start);
                card.setAttribute('data-end', end);
                
                card.innerHTML = `
                        <div class="accordion-header">
                            <div class="accordion-left">
                            <div class="step-badge">${num}</div>
                                <div class="accordion-title-wrapper">
                                <div class="accordion-title">Sub Gerakan ${num}</div>
                                <div class="accordion-duration">${formatTime(start)} - ${formatTime(end)}</div>
                                </div>
                            </div>
                            <div class="accordion-icon">
                                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
                                    <path d="M7 10l5 5 5-5z"/>
                                </svg>
                            </div>
                        </div>
                        <div class="accordion-content">
                            <div class="accordion-inner">
                                <div class="accordion-description">
                                ${description}
                                </div>
                                <div class="accordion-video"></div>
                        </div>
                    </div>
                `;
                
                subgerakanList.appendChild(card);
            }
        }
        
        // Function to setup accordion functionality
        function setupAccordions() {
            const accordionCards = document.querySelectorAll('.accordion-card');
            
            accordionCards.forEach(card => {
            const header = card.querySelector('.accordion-header');
            const videoWrapper = card.querySelector('.accordion-video');
            
            header.addEventListener('click', () => {
                const isActive = card.classList.contains('active');
                
                // Tutup semua accordion lain
                accordionCards.forEach(otherCard => {
                    if (otherCard !== card) {
                        otherCard.classList.remove('active');
                        const otherVideo = otherCard.querySelector('.accordion-video');
                        otherVideo.innerHTML = ''; // Hapus video untuk performa
                    }
                });

                // Toggle accordion yang diklik
                if (isActive) {
                    card.classList.remove('active');
                    videoWrapper.innerHTML = ''; // Hapus video
                } else {
                    card.classList.add('active');
                
                        // Load video dengan start & end time only if YouTube ID exists and is not empty
                        const hasValidYoutubeId = youtubeId && youtubeId.trim() !== '';
                        if (hasValidYoutubeId) {
                    const startTime = card.getAttribute('data-start');
                    const endTime = card.getAttribute('data-end');
                    
                    videoWrapper.innerHTML = `
                        <iframe 
                                    src="https://www.youtube.com/embed/${youtubeId}?start=${startTime}&end=${endTime}&autoplay=1" 
                            title="YouTube video player" 
                            frameborder="0" 
                            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" 
                            referrerpolicy="strict-origin-when-cross-origin" 
                            allowfullscreen>
                        </iframe>
                    `;
                        } else {
                            videoWrapper.innerHTML = `
                                <div style="display: flex; align-items: center; justify-content: center; height: 320px; background-color: #f5f5f5; border-radius: 10px; color: var(--tria-muted);">
                                    <p style="text-align: center;">Video tutorial belum tersedia untuk tarian ini.</p>
                                </div>
                            `;
                        }
                }
            });
        });
        }
        
        // Generate sub-gerakan on page load, then setup accordions
        generateSubgerakanList();
        setupAccordions();
    </script>
</body>
</html>
```

### landing/.gitignore

```
# See https://help.github.com/articles/ignoring-files/ for more about ignoring files.

# dependencies
/node_modules
/.pnp
.pnp.*
.yarn/*
!.yarn/patches
!.yarn/plugins
!.yarn/releases
!.yarn/versions

# testing
/coverage

# next.js
/.next/
/out/

# production
/build

# misc
.DS_Store
*.pem

# debug
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.pnpm-debug.log*

# env files (can opt-in for committing if needed)
.env*

# vercel
.vercel

# typescript
*.tsbuildinfo
next-env.d.ts
```

### landing/README.md

```md
This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.
```

### landing/eslint.config.mjs

```mjs
import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  // Override default ignores of eslint-config-next.
  globalIgnores([
    // Default ignores of eslint-config-next:
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
  ]),
]);

export default eslintConfig;
```

### landing/next-env.d.ts

```ts
/// <reference types="next" />
/// <reference types="next/image-types/global" />
import "./.next/dev/types/routes.d.ts";

// NOTE: This file should not be edited
// see https://nextjs.org/docs/app/api-reference/config/typescript for more information.
```

### landing/next.config.ts

```ts
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
};

export default nextConfig;
```

### landing/package.json

```json
{
  "name": "tria-landing-page",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "eslint"
  },
  "dependencies": {
    "lucide-react": "^0.552.0",
    "next": "16.0.1",
    "react": "19.2.0",
    "react-dom": "19.2.0"
  },
  "devDependencies": {
    "@tailwindcss/postcss": "^4",
    "@types/node": "^20",
    "@types/react": "^19",
    "@types/react-dom": "^19",
    "eslint": "^9",
    "eslint-config-next": "16.0.1",
    "tailwindcss": "^4",
    "typescript": "^5"
  }
}
```

### landing/postcss.config.mjs

```mjs
const config = {
  plugins: {
    "@tailwindcss/postcss": {},
  },
};

export default config;
```

### landing/tsconfig.json

```json
{
  "compilerOptions": {
    "target": "ES2017",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "react-jsx",
    "incremental": true,
    "plugins": [
      {
        "name": "next"
      }
    ],
    "paths": {
      "@/*": ["./*"]
    }
  },
  "include": [
    "next-env.d.ts",
    "**/*.ts",
    "**/*.tsx",
    ".next/types/**/*.ts",
    ".next/dev/types/**/*.ts",
    "**/*.mts"
  ],
  "exclude": ["node_modules"]
}
```

### landing/app/globals.css

```css
@import "tailwindcss";

:root {
  --background: #ffffff;
  --foreground: #171717;
}

@theme inline {
  --color-background: var(--background);
  --color-foreground: var(--foreground);
  --font-sans: var(--font-geist-sans);
  --font-mono: var(--font-geist-mono);
}

@media (prefers-color-scheme: dark) {
  :root {
    --background: #0a0a0a;
    --foreground: #ededed;
  }
}

body {
  background: var(--background);
  color: var(--foreground);
  font-family: Arial, Helvetica, sans-serif;
}
```

### landing/app/layout.tsx

```tsx
import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Create Next App",
  description: "Generated by create next app",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
```

### landing/app/page.tsx

```tsx
"use client";

import React, { useState, useEffect } from 'react';
import { Camera, Brain, Database, TrendingUp, Users, Award, ChevronRight, Menu, X, Play, Sparkles, Zap, CheckCircle, ArrowRight } from 'lucide-react';

export default function TriaLandingPage() {
  const [isScrolled, setIsScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 50);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const features = [
    {
      icon: <Brain className="w-8 h-8" />,
      title: "AI Motion Tracking",
      description: "Teknologi computer vision dan pose estimation untuk analisis gerakan real-time dengan akurasi tinggi"
    },
    {
      icon: <Camera className="w-8 h-8" />,
      title: "Interactive Learning",
      description: "Belajar tari dengan umpan balik langsung dan panduan visual interaktif yang adaptif"
    },
    {
      icon: <Database className="w-8 h-8" />,
      title: "Digital Dance Archive",
      description: "Kamus gerak digital yang mendokumentasikan tarian nusantara lengkap dengan makna filosofis"
    },
    {
      icon: <TrendingUp className="w-8 h-8" />,
      title: "Progress Tracking",
      description: "Analisis performa berbasis data untuk evaluasi terukur dan perkembangan skill yang jelas"
    }
  ];

  const stats = [
    { number: "11,706", label: "Warisan Budaya Tak Benda", sublabel: "Tercatat sejak 2010-2023" },
    { number: "30+", label: "Titik Deteksi Tubuh", sublabel: "MediaPipe & OpenPose" },
    { number: "57.13", label: "Skor IPK 2023", sublabel: "Indeks Pembangunan Kebudayaan" },
    { number: "100%", label: "Real-time Feedback", sublabel: "Instant AI Analysis" }
  ];

  const benefits = [
    "Menghilangkan batasan geografis dalam pembelajaran tari",
    "Standardisasi gerak tari yang terukur dan otentik",
    "Membuka peluang monetisasi untuk sanggar dan maestro",
    "Dokumentasi digital untuk pelestarian lintas generasi"
  ];

  const technologies = [
    { name: "MediaPipe & OpenPose", desc: "Pose estimation dengan 30+ keypoints", color: "from-amber-500 to-orange-500" },
    { name: "TensorFlow & scikit-learn", desc: "AI Scoring Engine untuk evaluasi", color: "from-orange-500 to-amber-500" },
    { name: "Next.js & Flutter", desc: "Cross-platform accessibility", color: "from-amber-600 to-orange-600" },
    { name: "FastAPI", desc: "Backend system yang powerful", color: "from-orange-600 to-amber-600" },
    { name: "Google Cloud Platform", desc: "Cloud infrastructure & deployment", color: "from-amber-500 to-orange-500" },
    { name: "Firebase Firestore", desc: "Database untuk metadata budaya", color: "from-orange-500 to-amber-500" }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-amber-950 via-orange-900 to-amber-950">
      {/* Navigation */}
      <nav className={`fixed w-full z-50 transition-all duration-300 ${isScrolled ? 'bg-amber-950/95 backdrop-blur-lg shadow-lg' : 'bg-transparent'}`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
          <div className="flex items-center space-x-3">
            <img 
              src="/logotria.png" 
              alt="TRIA Logo" 
              className="h-12 w-auto"
            />
            <span className="text-2xl font-bold text-white">TRIA</span>
          </div>

            <div className="hidden md:flex items-center space-x-8">
              <a href="#features" className="text-gray-300 hover:text-amber-400 transition">Fitur</a>
              <a href="#technology" className="text-gray-300 hover:text-amber-400 transition">Teknologi</a>
              <a href="#impact" className="text-gray-300 hover:text-amber-400 transition">Dampak</a>
              <a href="#team" className="text-gray-300 hover:text-amber-400 transition">Tim</a>
              <button className="bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-white px-6 py-2.5 rounded-full transition transform hover:scale-105 font-semibold shadow-lg shadow-amber-500/30">
                Mulai Sekarang
              </button>
            </div>

            <button 
              className="md:hidden text-white"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>

        {mobileMenuOpen && (
          <div className="md:hidden bg-amber-950/95 backdrop-blur-lg border-t border-white/10">
            <div className="px-4 py-4 space-y-3">
              <a href="#features" className="block text-gray-300 hover:text-amber-400 py-2">Fitur</a>
              <a href="#technology" className="block text-gray-300 hover:text-amber-400 py-2">Teknologi</a>
              <a href="#impact" className="block text-gray-300 hover:text-amber-400 py-2">Dampak</a>
              <a href="#team" className="block text-gray-300 hover:text-amber-400 py-2">Tim</a>
              <button className="w-full bg-gradient-to-r from-amber-500 to-orange-500 text-white px-6 py-2.5 rounded-full font-semibold shadow-lg">
                Mulai Sekarang
              </button>
            </div>
          </div>
        )}
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto text-center">
          <div className="inline-block mb-6 px-4 py-2 bg-amber-500/20 rounded-full border border-amber-500/30 backdrop-blur-sm">
            <span className="text-amber-300 text-sm font-semibold">🎭 Konservasi Tarian Nusantara dengan AI</span>
          </div>
          
          <h1 className="text-5xl md:text-7xl font-bold text-white mb-6 leading-tight">
            Lestarikan Tari Tradisional
            <br />
            <span className="bg-gradient-to-r from-amber-400 to-orange-400 bg-clip-text text-transparent">
              Bersama Teknologi AI
            </span>
          </h1>
          
          <p className="text-xl text-gray-300 mb-10 max-w-3xl mx-auto">
            Platform pembelajaran tari berbasis AI Computer Vision dan Motion Tracking untuk melestarikan dan menstandardisasi warisan budaya Indonesia
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-16">
            <button className="bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-white px-8 py-4 rounded-full text-lg font-semibold transition transform hover:scale-105 flex items-center gap-2 shadow-lg shadow-amber-500/30">
              Coba Sekarang
              <ArrowRight className="w-5 h-5" />
            </button>
            <button className="bg-white/10 hover:bg-white/20 text-white px-8 py-4 rounded-full text-lg font-semibold backdrop-blur-sm transition border border-amber-500/30 flex items-center gap-2">
              <Play className="w-5 h-5" />
              Lihat Demo
            </button>
          </div>

          {/* Hero Visual */}
          <div className="relative">
            <div className="absolute inset-0 bg-gradient-to-r from-amber-500/20 to-orange-500/20 rounded-3xl blur-3xl"></div>
            <div className="relative bg-gradient-to-br from-amber-500/10 to-orange-500/10 rounded-3xl p-8 backdrop-blur-sm border border-amber-500/30">
              <div className="bg-amber-950/50 rounded-2xl p-12 min-h-96 flex items-center justify-center">
                <div className="text-center">
                  <Camera className="w-24 h-24 text-amber-400 mx-auto mb-6 animate-pulse" />
                  <p className="text-white text-2xl font-bold mb-2">AI Motion Tracking</p>
                  <p className="text-gray-400 text-lg">Real-time Pose Detection & Analysis</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-black/20">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {stats.map((stat, index) => (
              <div key={index} className="bg-gradient-to-br from-amber-500/10 to-orange-500/10 rounded-2xl p-6 border border-amber-500/30 backdrop-blur-sm text-center transform hover:-translate-y-2 transition">
                <div className="text-4xl md:text-5xl font-bold text-transparent bg-gradient-to-r from-amber-400 to-orange-400 bg-clip-text mb-2">
                  {stat.number}
                </div>
                <div className="text-white font-semibold mb-1">{stat.label}</div>
                <div className="text-gray-400 text-sm">{stat.sublabel}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Problem Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-4">
              Tantangan Pelestarian Tari
            </h2>
            <p className="text-xl text-gray-300 max-w-3xl mx-auto">
              Kekayaan budaya yang melimpah kontras dengan rendahnya daya ungkit ekonomi
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-8 mb-12">
            <div className="bg-gradient-to-br from-amber-500/10 to-orange-500/10 rounded-2xl p-8 border border-amber-500/30 backdrop-blur-sm">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-12 h-12 bg-amber-500/20 rounded-full flex items-center justify-center">
                  <Zap className="w-6 h-6 text-amber-400" />
                </div>
                <h3 className="text-2xl font-bold text-white">Transfer Knowledge Terbatas</h3>
              </div>
              <ul className="space-y-3 text-gray-300">
                <li className="flex items-start gap-2">
                  <span className="text-amber-400 mt-1">•</span>
                  <span>Pembelajaran masih didominasi <span className="text-amber-400 font-semibold">oral tradition</span> yang rentan degradasi</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-amber-400 mt-1">•</span>
                  <span>Keterbatasan <span className="text-amber-400 font-semibold">akses geografis</span> untuk belajar dari maestro</span>
                </li>
              </ul>
            </div>

            <div className="bg-gradient-to-br from-orange-500/10 to-amber-500/10 rounded-2xl p-8 border border-orange-500/30 backdrop-blur-sm">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-12 h-12 bg-orange-500/20 rounded-full flex items-center justify-center">
                  <TrendingUp className="w-6 h-6 text-orange-400" />
                </div>
                <h3 className="text-2xl font-bold text-white">Kesenjangan Digital</h3>
              </div>
              <ul className="space-y-3 text-gray-300">
                <li className="flex items-start gap-2">
                  <span className="text-orange-400 mt-1">•</span>
                  <span>Sanggar tari belum memiliki <span className="text-orange-400 font-semibold">kehadiran digital</span> yang memadai</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-orange-400 mt-1">•</span>
                  <span>Dunia kesenian mengalami <span className="text-orange-400 font-semibold">&quot;krisis ekonomi&quot;</span></span>
                </li>
              </ul>
            </div>
          </div>

          <div className="bg-gradient-to-r from-red-500/20 to-orange-500/20 rounded-2xl p-8 border border-red-500/30 backdrop-blur-sm text-center">
            <h3 className="text-2xl font-bold text-white mb-3">Potensi Ekonomi Budaya</h3>
            <p className="text-xl text-gray-300">Warisan budaya tak benda gagal berskala di pasar modern, khususnya seni pertunjukan seperti tari tradisional</p>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20 px-4 sm:px-6 lg:px-8 bg-black/20">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-4">
              Fitur Unggulan TRIA
            </h2>
            <p className="text-xl text-gray-300 max-w-2xl mx-auto">
              Teknologi AI terdepan untuk pembelajaran dan pelestarian tari tradisional Indonesia
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((feature, index) => (
              <div 
                key={index}
                className="bg-white/5 backdrop-blur-sm rounded-2xl p-6 border border-amber-500/20 hover:border-amber-500/50 transition transform hover:-translate-y-2"
              >
                <div className="bg-gradient-to-br from-amber-500/20 to-orange-500/20 w-16 h-16 rounded-xl flex items-center justify-center mb-4 text-amber-400">
                  {feature.icon}
                </div>
                <h3 className="text-xl font-bold text-white mb-3">{feature.title}</h3>
                <p className="text-gray-400 leading-relaxed">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Technology Section */}
      <section id="technology" className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-4">
              Stack Teknologi
            </h2>
            <p className="text-xl text-gray-300 max-w-2xl mx-auto">
              Kombinasi AI, Computer Vision, dan Cloud Computing untuk konservasi digital
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {technologies.map((tech, index) => (
              <div 
                key={index} 
                className="bg-white/5 backdrop-blur-sm rounded-2xl p-6 border border-amber-500/20 hover:border-amber-500/40 transition group"
              >
                <div className={`w-full h-2 rounded-full bg-gradient-to-r ${tech.color} mb-4`}></div>
                <h4 className="font-bold text-white text-lg mb-2 group-hover:text-amber-400 transition">{tech.name}</h4>
                <p className="text-gray-400 text-sm">{tech.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Benefits Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-black/20">
        <div className="max-w-7xl mx-auto">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
                Nilai Tambah TRIA
              </h2>
              <p className="text-xl text-gray-300 mb-8">
                Platform all-in-one yang menggabungkan AI, standardisasi, dan pemberdayaan ekonomi untuk pelestarian budaya
              </p>
              
              <div className="space-y-4 mb-8">
                {benefits.map((benefit, index) => (
                  <div key={index} className="flex items-start gap-3">
                    <CheckCircle className="w-6 h-6 text-amber-400 flex-shrink-0 mt-1" />
                    <span className="text-gray-300 text-lg">{benefit}</span>
                  </div>
                ))}
              </div>

              <div className="bg-gradient-to-br from-amber-500/10 to-orange-500/10 rounded-2xl p-6 border border-amber-500/30 backdrop-blur-sm">
                <h3 className="text-xl font-bold text-white mb-3">🎯 Unique Value Proposition</h3>
                <p className="text-gray-300 mb-3">
                  <span className="text-amber-400 font-semibold">AI berbasis paham budaya</span> - dikurasi dengan data dari Maestro Tari yang menjamin akurasi tidak hanya pada posisi tubuh tetapi juga pada rasa dan filosofi gerak
                </p>
              </div>
            </div>

            <div className="bg-gradient-to-br from-amber-500/20 to-orange-500/20 rounded-2xl p-8 backdrop-blur-sm border border-amber-500/30">
              <div className="bg-amber-950/50 rounded-xl p-8 min-h-96 flex flex-col items-center justify-center space-y-6">
                <div className="text-center">
                  <Sparkles className="w-16 h-16 text-amber-400 mx-auto mb-4 animate-pulse" />
                  <h3 className="text-2xl font-bold text-white mb-2">Platform Lain</h3>
                  <p className="text-gray-400">Tutorial Video Biasa</p>
                </div>
                
                <div className="w-full h-px bg-gradient-to-r from-transparent via-amber-500 to-transparent"></div>
                
                <div className="text-center">
                  <Brain className="w-20 h-20 text-orange-400 mx-auto mb-4" />
                  <h3 className="text-3xl font-bold text-transparent bg-gradient-to-r from-amber-400 to-orange-400 bg-clip-text mb-2">TRIA</h3>
                  <p className="text-white font-semibold">AI-Powered Learning + Digital Archive</p>
                  <p className="text-gray-300 text-sm mt-2">Dengan Royalty untuk Maestro</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Impact Section */}
      <section id="impact" className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-4">
              Target & Dampak
            </h2>
            <p className="text-xl text-gray-300">
              Memberdayakan ekosistem budaya Indonesia
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8 mb-12">
            <div className="bg-gradient-to-br from-amber-500/10 to-orange-500/10 rounded-2xl p-8 border border-amber-500/30 backdrop-blur-sm text-center transform hover:-translate-y-2 transition">
              <Users className="w-12 h-12 text-amber-400 mx-auto mb-4" />
              <h3 className="text-xl font-bold text-white mb-2">Pelajar & Mahasiswa</h3>
              <p className="text-gray-400">Seni tari di seluruh Indonesia</p>
            </div>

            <div className="bg-gradient-to-br from-orange-500/10 to-amber-500/10 rounded-2xl p-8 border border-orange-500/30 backdrop-blur-sm text-center transform hover:-translate-y-2 transition">
              <Award className="w-12 h-12 text-orange-400 mx-auto mb-4" />
              <h3 className="text-xl font-bold text-white mb-2">Diaspora Indonesia</h3>
              <p className="text-gray-400">Peminat budaya global</p>
            </div>

            <div className="bg-gradient-to-br from-amber-500/10 to-orange-500/10 rounded-2xl p-8 border border-amber-500/30 backdrop-blur-sm text-center transform hover:-translate-y-2 transition">
              <Database className="w-12 h-12 text-amber-400 mx-auto mb-4" />
              <h3 className="text-xl font-bold text-white mb-2">Sanggar & Maestro</h3>
              <p className="text-gray-400">Guru tari profesional</p>
            </div>
          </div>

          <div className="bg-gradient-to-r from-amber-500/20 to-orange-500/20 rounded-2xl p-12 border border-amber-500/30 backdrop-blur-sm text-center">
            <h3 className="text-3xl font-bold text-white mb-4">Potensi Ekonomi Kreatif</h3>
            <p className="text-xl text-gray-300 mb-2">Subsektor Seni Pertunjukan</p>
            <p className="text-gray-400">Platform digital baru untuk monetisasi keahlian melalui konten premium dan pelatihan</p>
          </div>
        </div>
      </section>

      {/* Team Section */}
      <section id="team" className="py-20 px-4 sm:px-6 lg:px-8 bg-black/20">
        <div className="max-w-7xl mx-auto text-center">
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-4">
            Tim Little Vietnam
          </h2>
          <p className="text-xl text-amber-400 mb-12">Universitas Indonesia</p>
          
          <div className="grid grid-cols-2 md:grid-cols-5 gap-6 mb-12">
            {[
              { name: "Muhammad Hamiz Ghani Ayusha", role: "Ketua Tim" },
              { name: "Lessyarta Kamali Sopamena Pirade", role: "Anggota" },
              { name: "Ammar Muhammad Rafif", role: "Anggota" },
              { name: "I Gusti Ngurah Agung", role: "Anggota" },
              { name: "Fidel Akilah", role: "Anggota" }
            ].map((member, index) => (
              <div key={index} className="bg-gradient-to-br from-amber-500/10 to-orange-500/10 backdrop-blur-sm p-6 rounded-2xl border border-amber-500/30 hover:border-amber-500/50 transition group">
                <div className="w-16 h-16 bg-gradient-to-br from-amber-400 to-orange-400 rounded-full mx-auto mb-4 flex items-center justify-center shadow-lg shadow-amber-500/30 group-hover:scale-110 transition">
                  <span className="text-2xl font-bold text-amber-950">{member.name.charAt(0)}</span>
                </div>
                <p className="text-white font-semibold text-sm mb-1">{member.name}</p>
                <p className="text-amber-400 text-xs">{member.role}</p>
              </div>
            ))}
          </div>

          <div className="bg-gradient-to-br from-amber-500/10 to-orange-500/10 rounded-2xl p-8 border border-amber-500/30 backdrop-blur-sm max-w-2xl mx-auto">
            <p className="text-gray-300 mb-4">Kontak:</p>
            <p className="text-amber-400 font-semibold">hamizghaniiii@gmail.com</p>
            <p className="text-amber-400 font-semibold">(+62) 822-1149-5872</p>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto">
          <div className="bg-gradient-to-r from-amber-600 to-orange-600 rounded-3xl p-12 text-center relative overflow-hidden shadow-2xl shadow-amber-500/30">
            <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGZpbGw9IiNmZmYiIGZpbGwtb3BhY2l0eT0iMC4wNSI+PHBhdGggZD0iTTM2IDM0djItaDJ2LTJoLTJ6bTAtNGgydjJoLTJ2LTJ6bTAgNGgydjJoLTJ2LTJ6Ii8+PC9nPjwvZz48L3N2Zz4=')] opacity-30"></div>
            <div className="relative">
              <h2 className="text-4xl md:text-5xl font-bold text-white mb-4">
                Bergabunglah Melestarikan Budaya Indonesia
              </h2>
              <p className="text-xl text-white/90 mb-8">
                Mulai perjalanan Anda belajar tari tradisional dengan teknologi AI terdepan
              </p>
              <button className="bg-white hover:bg-gray-100 text-amber-600 px-12 py-4 rounded-full text-lg font-semibold transition transform hover:scale-105 shadow-xl">
                Daftar Sekarang
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-4 sm:px-6 lg:px-8 border-t border-white/10">
        <div className="max-w-7xl mx-auto text-center">
        <div className="flex items-center justify-center space-x-3 mb-4">
          <img 
            src="/logotria.png" 
            alt="TRIA Logo" 
            className="h-12 w-auto"
          />
          <span className="text-2xl font-bold text-white">TRIA</span>
        </div>
          <p className="text-gray-400 mb-2">Konservasi Tarian Nusantara melalui AI Computer Vision</p>
          <p className="text-gray-500 text-sm">
            © 2025 TRIA - Little Vietnam Team | Universitas Indonesia
          </p>
        </div>
      </footer>
    </div>
  );
}
```

### landing/public/file.svg

```svg
<svg fill="none" viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg"><path d="M14.5 13.5V5.41a1 1 0 0 0-.3-.7L9.8.29A1 1 0 0 0 9.08 0H1.5v13.5A2.5 2.5 0 0 0 4 16h8a2.5 2.5 0 0 0 2.5-2.5m-1.5 0v-7H8v-5H3v12a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1M9.5 5V2.12L12.38 5zM5.13 5h-.62v1.25h2.12V5zm-.62 3h7.12v1.25H4.5zm.62 3h-.62v1.25h7.12V11z" clip-rule="evenodd" fill="#666" fill-rule="evenodd"/></svg>
```

### landing/public/globe.svg

```svg
<svg fill="none" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16"><g clip-path="url(#a)"><path fill-rule="evenodd" clip-rule="evenodd" d="M10.27 14.1a6.5 6.5 0 0 0 3.67-3.45q-1.24.21-2.7.34-.31 1.83-.97 3.1M8 16A8 8 0 1 0 8 0a8 8 0 0 0 0 16m.48-1.52a7 7 0 0 1-.96 0H7.5a4 4 0 0 1-.84-1.32q-.38-.89-.63-2.08a40 40 0 0 0 3.92 0q-.25 1.2-.63 2.08a4 4 0 0 1-.84 1.31zm2.94-4.76q1.66-.15 2.95-.43a7 7 0 0 0 0-2.58q-1.3-.27-2.95-.43a18 18 0 0 1 0 3.44m-1.27-3.54a17 17 0 0 1 0 3.64 39 39 0 0 1-4.3 0 17 17 0 0 1 0-3.64 39 39 0 0 1 4.3 0m1.1-1.17q1.45.13 2.69.34a6.5 6.5 0 0 0-3.67-3.44q.65 1.26.98 3.1M8.48 1.5l.01.02q.41.37.84 1.31.38.89.63 2.08a40 40 0 0 0-3.92 0q.25-1.2.63-2.08a4 4 0 0 1 .85-1.32 7 7 0 0 1 .96 0m-2.75.4a6.5 6.5 0 0 0-3.67 3.44 29 29 0 0 1 2.7-.34q.31-1.83.97-3.1M4.58 6.28q-1.66.16-2.95.43a7 7 0 0 0 0 2.58q1.3.27 2.95.43a18 18 0 0 1 0-3.44m.17 4.71q-1.45-.12-2.69-.34a6.5 6.5 0 0 0 3.67 3.44q-.65-1.27-.98-3.1" fill="#666"/></g><defs><clipPath id="a"><path fill="#fff" d="M0 0h16v16H0z"/></clipPath></defs></svg>
```

### landing/public/next.svg

```svg
<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 394 80"><path fill="#000" d="M262 0h68.5v12.7h-27.2v66.6h-13.6V12.7H262V0ZM149 0v12.7H94v20.4h44.3v12.6H94v21h55v12.6H80.5V0h68.7zm34.3 0h-17.8l63.8 79.4h17.9l-32-39.7 32-39.6h-17.9l-23 28.6-23-28.6zm18.3 56.7-9-11-27.1 33.7h17.8l18.3-22.7z"/><path fill="#000" d="M81 79.3 17 0H0v79.3h13.6V17l50.2 62.3H81Zm252.6-.4c-1 0-1.8-.4-2.5-1s-1.1-1.6-1.1-2.6.3-1.8 1-2.5 1.6-1 2.6-1 1.8.3 2.5 1a3.4 3.4 0 0 1 .6 4.3 3.7 3.7 0 0 1-3 1.8zm23.2-33.5h6v23.3c0 2.1-.4 4-1.3 5.5a9.1 9.1 0 0 1-3.8 3.5c-1.6.8-3.5 1.3-5.7 1.3-2 0-3.7-.4-5.3-1s-2.8-1.8-3.7-3.2c-.9-1.3-1.4-3-1.4-5h6c.1.8.3 1.6.7 2.2s1 1.2 1.6 1.5c.7.4 1.5.5 2.4.5 1 0 1.8-.2 2.4-.6a4 4 0 0 0 1.6-1.8c.3-.8.5-1.8.5-3V45.5zm30.9 9.1a4.4 4.4 0 0 0-2-3.3 7.5 7.5 0 0 0-4.3-1.1c-1.3 0-2.4.2-3.3.5-.9.4-1.6 1-2 1.6a3.5 3.5 0 0 0-.3 4c.3.5.7.9 1.3 1.2l1.8 1 2 .5 3.2.8c1.3.3 2.5.7 3.7 1.2a13 13 0 0 1 3.2 1.8 8.1 8.1 0 0 1 3 6.5c0 2-.5 3.7-1.5 5.1a10 10 0 0 1-4.4 3.5c-1.8.8-4.1 1.2-6.8 1.2-2.6 0-4.9-.4-6.8-1.2-2-.8-3.4-2-4.5-3.5a10 10 0 0 1-1.7-5.6h6a5 5 0 0 0 3.5 4.6c1 .4 2.2.6 3.4.6 1.3 0 2.5-.2 3.5-.6 1-.4 1.8-1 2.4-1.7a4 4 0 0 0 .8-2.4c0-.9-.2-1.6-.7-2.2a11 11 0 0 0-2.1-1.4l-3.2-1-3.8-1c-2.8-.7-5-1.7-6.6-3.2a7.2 7.2 0 0 1-2.4-5.7 8 8 0 0 1 1.7-5 10 10 0 0 1 4.3-3.5c2-.8 4-1.2 6.4-1.2 2.3 0 4.4.4 6.2 1.2 1.8.8 3.2 2 4.3 3.4 1 1.4 1.5 3 1.5 5h-5.8z"/></svg>
```

### landing/public/vercel.svg

```svg
<svg fill="none" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1155 1000"><path d="m577.3 0 577.4 1000H0z" fill="#fff"/></svg>
```

### landing/public/window.svg

```svg
<svg fill="none" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16"><path fill-rule="evenodd" clip-rule="evenodd" d="M1.5 2.5h13v10a1 1 0 0 1-1 1h-11a1 1 0 0 1-1-1zM0 1h16v11.5a2.5 2.5 0 0 1-2.5 2.5h-11A2.5 2.5 0 0 1 0 12.5zm3.75 4.5a.75.75 0 1 0 0-1.5.75.75 0 0 0 0 1.5M7 4.75a.75.75 0 1 1-1.5 0 .75.75 0 0 1 1.5 0m1.75.75a.75.75 0 1 0 0-1.5.75.75 0 0 0 0 1.5" fill="#666"/></svg>
```

### main/__init__.py

```py

```

### main/admin.py

```py
from django.contrib import admin

# Register your models here.
```

### main/apps.py

```py
from django.apps import AppConfig


class MainConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'main'
```

### main/models.py

```py
from django.db import models

# Create your models here.
```

### main/tests.py

```py
from django.test import TestCase

# Create your tests here.
```

### main/urls.py

```py
from django.urls import path
from main.views import *

app_name = 'main'

urlpatterns = [
    path('', home_view, name='home'),
]
```

### main/views.py

```py
from django.shortcuts import render

def home_view(request):
    return render(request, 'home.html')
```

### main/migrations/__init__.py

```py

```

### main/templates/home.html

```html

```

### scripts/dev.sh

```sh
#!/usr/bin/env bash
cd "$(dirname "$0")/.."
set -a; [ -f .env ] && . ./.env; set +a
export OPENAI_API_KEY="${OPENAI_API_KEY:-dummy-key-fallback-mode}"
trap 'kill 0' EXIT
(cd backend && ../.venv/bin/uvicorn main:app --port "${BACKEND_PORT:-8001}") &
.venv/bin/python manage.py runserver "${DJANGO_PORT:-8000}" &
(cd landing && npm run dev -- -p "${LANDING_PORT:-3000}") &
wait
```

### scripts/setup.sh

```sh
#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."
python3 -m venv .venv
.venv/bin/pip install -q -r requirements.txt -r backend/requirements.txt
.venv/bin/python manage.py migrate
(cd landing && npm install)
echo "Setup selesai. Jalankan: ./scripts/dev.sh"
```

### tria/__init__.py

```py

```

### tria/asgi.py

```py
"""
ASGI config for tria project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tria.settings')

application = get_asgi_application()
```

### tria/settings.py

```py
import os
from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv()

from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-5q0&nu!d9$=(sw3#jhosn_&!mtu-@g09by3i)tjtm*5k+kguf!'

# SECURITY WARNING: don't run with debug turned on in production!
PRODUCTION = os.getenv('PRODUCTION', 'False').lower() == 'true'
# In production set PRODUCTION=true in the environment. DEBUG follows PRODUCTION.
DEBUG = not PRODUCTION

CSRF_TRUSTED_ORIGINS = [
    'https://muhammad-hamiz-tria.pbp.cs.ui.ac.id',
    'http://muhammad-hamiz-tria.pbp.cs.ui.ac.id',  # jika ada http
]

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    # add your deployment host (no scheme, no trailing slash)
    "muhammad-hamiz-tria.pbp.cs.ui.ac.id",
]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'dances',    # Daftar Tarian
    'articles',  # Artikel
    'daftarsanggar',  # Daftar Sanggar
    'authentication',  # Authentication (login/register)
    # Removed studios app to fix missing module error
    # 'studios',   # Daftar Sanggar Tari
    # Removed core app to fix missing module error
    # 'core',
    'main',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'tria.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'tria' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'tria.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases
if PRODUCTION:
    # Production: gunakan PostgreSQL dengan kredensial dari environment variables
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DB_NAME'),
            'USER': os.getenv('DB_USER'),
            'PASSWORD': os.getenv('DB_PASSWORD'),
            'HOST': os.getenv('DB_HOST'),
            'PORT': os.getenv('DB_PORT'),
            'OPTIONS': {
                'options': f"-c search_path={os.getenv('SCHEMA', 'public')}"
            }
        }
    }
else:
    # Development: gunakan SQLite
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static'
]

# Security settings for production (only enabled when PRODUCTION=True)
if PRODUCTION:
    # Ensure cookies are only sent over HTTPS
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True

    # If the app is behind a proxy (e.g., a load balancer) that terminates TLS,
    # make sure Django knows the original scheme. Adjust header name if needed.
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
```

### tria/urls.py

```py
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='landing.html'), name='home'),
    path('about/', include('about.urls')),
    path('dances/', include('dances.urls')),
    path('daftarsanggar/', include(('daftarsanggar.urls', 'daftarsanggar'), namespace='daftarsanggar')),
    path('', include(('authentication.urls', 'authentication'), namespace='authentication')),
]
```

### tria/wsgi.py

```py
"""
WSGI config for tria project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tria.settings')

application = get_wsgi_application()
```

### tria/templates/about.html

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Tria - Belajar Tarian Tradisional Indonesia</title>
    <link rel="icon" type="image/png" href="https://i.ibb.co.com/fY9F3RwF/tria.png" />
    <link rel="shortcut icon" type="image/png" href="https://i.ibb.co.com/fY9F3RwF/tria.png" />
    <style>
        :root {
            --tria-red: #e53935;
            --tria-orange: #ff9800;
            --tria-orange-soft: #fff3e0;
            --tria-border: #f0f0f0;
            --tria-text: #222222;
            --tria-muted: #555555;
        }

        * {
            box-sizing: border-box;
        }

        body {
            background-color: #ffffff;
            color: var(--tria-text);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen,
                Ubuntu, Cantarell, "Open Sans", "Helvetica Neue", sans-serif;
            margin: 0;
            padding: 0;
        }

        a {
            text-decoration: none;
            color: inherit;
        }

        /* NAVBAR (same as home) ------------------------------------ */

        .navbar {
            background-color: #ffffff;
            border-bottom: 1px solid var(--tria-border);
            position: sticky;
            top: 0;
            z-index: 50;
        }

        .nav-inner {
            max-width: 1100px;
            margin: 0 auto;
            padding: 0.75rem 1.25rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
        }

        .nav-brand {
            display: flex;
            align-items: center;
            gap: 0.6rem;
        }

        .nav-logo {
            height: 36px;
            width: 36px;
            object-fit: contain;
        }

        .nav-title {
            font-weight: 700;
            letter-spacing: 0.03em;
            font-size: 1.1rem;
        }

        .nav-links {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            font-size: 0.95rem;
        }

        .nav-link {
            padding: 0.4rem 0.75rem;
            border-radius: 999px;
            transition: background-color 0.2s ease, color 0.2s ease, transform 0.1s ease;
        }

        .nav-link:hover {
            background-color: var(--tria-orange-soft);
            color: var(--tria-red);
            transform: translateY(-1px);
        }

        .nav-cta {
            background: linear-gradient(135deg, var(--tria-red), var(--tria-orange));
            color: #ffffff;
            font-weight: 600;
        }

        .nav-cta:hover {
            background: linear-gradient(135deg, #c62828, #fb8c00);
            color: #ffffff;
        }

        /* PAGE LAYOUT ---------------------------------------------- */

        .page {
            max-width: 900px;
            margin: 0 auto;
            padding: 3.25rem 1.25rem 3rem 1.25rem;
        }

        .section {
            margin-bottom: 2.5rem;
        }

        .section-title {
            font-size: 1.9rem;
            margin: 0 0 0.5rem 0;
            text-align: center;
        }

        .section-subtitle {
            text-align: center;
            font-size: 0.98rem;
            color: var(--tria-muted);
            max-width: 640px;
            margin: 0 auto 1.8rem auto;
        }

        .about-card {
            background-color: #ffffff;
            border-radius: 1.2rem;
            border: 1px solid var(--tria-border);
            padding: 1.5rem 1.7rem;
            box-shadow: 0 14px 30px rgba(0, 0, 0, 0.04);
        }

        .about-paragraph {
            font-size: 1rem;
            line-height: 1.7;
            color: var(--tria-muted);
            margin-bottom: 1rem;
        }

        .about-paragraph strong {
            color: var(--tria-red);
        }

        .about-list {
            margin: 1.2rem 0 0;
            padding-left: 1.25rem;
            font-size: 0.95rem;
            color: var(--tria-muted);
        }

        .about-list li {
            margin-bottom: 0.4rem;
        }

        .pill {
            display: inline-flex;
            padding: 0.3rem 0.7rem;
            border-radius: 999px;
            background-color: var(--tria-orange-soft);
            color: var(--tria-red);
            font-size: 0.78rem;
            font-weight: 600;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            margin-bottom: 0.8rem;
        }

        /* NEW: Meet the Creators ----------------------------------- */

        .team-section-title {
            font-size: 1.8rem;
            margin: 0 0 0.7rem 0;
            text-align: center;
        }

        .team-subtitle {
            text-align: center;
            font-size: 0.96rem;
            color: var(--tria-muted);
            max-width: 620px;
            margin: 0 auto 1.6rem auto;
            line-height: 1.6;
        }

        .team-image-wrapper {
            border-radius: 1.4rem;
            overflow: hidden;
            box-shadow: 0 16px 36px rgba(0, 0, 0, 0.08);
            margin: 0 auto 1.7rem auto;
        }

        .team-image {
            width: 100%;
            display: block;
            object-fit: cover;
        }

        .team-meta {
            text-align: center;
            font-size: 0.85rem;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            color: var(--tria-red);
            margin-bottom: 0.6rem;
            font-weight: 600;
        }

        .team-members {
            text-align: center;
            font-size: 0.95rem;
            color: var(--tria-muted);
            margin-top: 0.75rem;
            line-height: 1.6;
        }

        .team-members strong {
            color: var(--tria-text);
        }

        @media (max-width: 600px) {
            .page {
                padding-inline: 1rem;
                padding-top: 2.3rem;
            }

            .section-title {
                font-size: 1.6rem;
            }

            .team-section-title {
                font-size: 1.55rem;
            }
        }
    </style>
</head>
<body>
    {% load static %}
    {% include 'partials/navbar.html' %}

    <main class="page">
        <!-- Existing "Tentang Tria" section -->
        <section class="section">
            <div class="pill">Tentang Tria</div>
            <h1 class="section-title">Menghubungkan generasi muda dengan tarian tradisional Indonesia</h1>
            <p class="section-subtitle">
                Tria lahir dari keinginan sederhana: membuat tarian tradisional Indonesia
                terasa dekat, mudah dipelajari, dan relevan bagi pelajar di era digital.
            </p>

            <article class="about-card">
                <p class="about-paragraph">
                    <strong>Tria</strong> adalah platform pembelajaran tarian tradisional Indonesia
                    yang menggabungkan panduan gerak yang jelas dengan penjelasan budaya yang kaya.
                    Di dalamnya, kamu dapat menemukan beragam tarian daerah lengkap dengan
                    tahapan gerakan, hitungan, serta konteks maknanya.
                </p>
                <p class="about-paragraph">
                    Platform ini dirancang untuk mendukung <strong>pelajar, komunitas seni,
                    sekolah, dan individu</strong> yang ingin mempelajari tarian daerah
                    secara mandiri namun tetap terarah. Kami percaya bahwa memahami makna
                    di balik setiap gerak akan membuat proses belajar menari jauh lebih
                    bermakna.
                </p>
                <p class="about-paragraph">
                    Melalui Tria, kami ingin membantu kamu:
                </p>
                <ul class="about-list">
                    <li>Mengakses materi tarian tradisional secara praktis dan terstruktur.</li>
                    <li>Memahami cerita dan nilai budaya yang terkandung dalam setiap tarian.</li>
                    <li>Melatih gerakan secara mandiri dengan dukungan teknologi yang ramah pengguna.</li>
                    <li>Menjadikan tarian daerah sebagai bagian dari identitas, bukan sekadar tontonan.</li>
                </ul>
            </article>
        </section>

        <!-- NEW: Meet the Tria Creators -->
        <section class="section">
            <div class="team-meta">Meet the Tria Creators</div>
            <h2 class="team-section-title">Tim Little Vietnam</h2>
            <p class="team-subtitle">
                Di balik Tria, ada sekelompok mahasiswa yang percaya bahwa teknologi bisa menjadi
                jembatan antara generasi muda dan warisan budaya Indonesia. Kami merancang Tria
                agar bukan hanya jadi alat belajar, tetapi juga ruang untuk merayakan identitas
                dan kebanggaan sebagai orang Indonesia.
            </p>

            <div class="team-image-wrapper">
                <img src="https://i.ibb.co.com/JWG30bc7/team.png"
                     alt="Tim Little Vietnam, para kreator TRIA"
                     class="team-image" />
            </div>

            <p class="team-members">
                <strong>Tim Little Vietnam</strong> terdiri dari:<br />
                Muhammad Hamiz Ghani Ayusha · Lessyarta Kamali Sopamena Pirade ·
                Ammar Muhammad Rafif · I Gusti Ngurah Agung Airlangga Putra ·
                Fidel Akilah
            </p>
        </section>
    </main>
</body>
</html>
```

### tria/templates/base.html

```html
{% load static %}
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{% block title %}Tria - Belajar Tarian Tradisional Indonesia{% endblock %}</title>
    <link rel="icon" type="image/png" href="https://i.ibb.co.com/fY9F3RwF/tria.png" />
    <link rel="shortcut icon" type="image/png" href="https://i.ibb.co.com/fY9F3RwF/tria.png" />
    {% block meta %} {% endblock meta %}
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/dompurify@3.0.5/dist/purify.min.js"></script>
    <link rel="stylesheet" href="{% static 'css/global.css' %}"/>
    <link rel="stylesheet" href="{% static 'css/toast.css' %}"/>

  </head>
  <body>
    {% include 'partials/navbar.html' %}
    {% block content %}

    {% endblock %}
    {% include 'footer.html' %}
</body>
</html>
```

### tria/templates/footer.html

```html

```

### tria/templates/landing.html

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Tria - Belajar Tarian Tradisional Indonesia</title>
    <link rel="icon" type="image/png" href="https://i.ibb.co.com/fY9F3RwF/tria.png" />
    <link rel="shortcut icon" type="image/png" href="https://i.ibb.co.com/fY9F3RwF/tria.png" />
    <style>
        :root {
            --tria-red: #e53935;
            --tria-orange: #ff9800;
            --tria-soft-bg: #fff7ec;
            --tria-border: #f0e4d6;
            --tria-text: #222222;
            --tria-muted: #555555;
        }

        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen,
                Ubuntu, Cantarell, "Open Sans", "Helvetica Neue", sans-serif;
            background-color: #ffffff;
            color: var(--tria-text);
            overflow-x: hidden;
        }

        a {
            text-decoration: none;
            color: inherit;
        }

        /* NAVBAR */
        .navbar {
            background-color: #ffffff;
            border-bottom: 1px solid #f3eee7;
            position: sticky;
            top: 0;
            z-index: 50;
            backdrop-filter: blur(10px);
        }

        .nav-inner {
            max-width: 1100px;
            margin: 0 auto;
            padding: 0.75rem 1.5rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
        }

        .nav-brand {
            display: flex;
            align-items: center;
            gap: 0.6rem;
        }

        .nav-logo {
            height: 36px;
            width: 36px;
            object-fit: contain;
        }

        .nav-title {
            font-weight: 700;
            letter-spacing: 0.03em;
            font-size: 1.1rem;
        }

        .nav-links {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            font-size: 0.95rem;
        }

        .nav-link {
            padding: 0.4rem 0.75rem;
            border-radius: 999px;
            transition: background-color 0.2s ease, color 0.2s ease, transform 0.1s ease;
        }

        .nav-link:hover {
            background-color: #fff1df;
            color: var(--tria-red);
            transform: translateY(-1px);
        }

        .nav-cta {
            background: linear-gradient(135deg, var(--tria-red), var(--tria-orange));
            color: #ffffff;
            font-weight: 600;
        }

        .nav-cta:hover {
            background: linear-gradient(135deg, #c62828, #fb8c00);
            color: #ffffff;
        }

        /* PAGE WRAPPER */
        .page {
            max-width: 1100px;
            margin: 0 auto;
            padding: 2.5rem 1.5rem 3.5rem 1.5rem;
            position: relative;
        }

        /* DECORATIVE ELEMENTS - ENHANCED */
        .decoration-circle {
            position: absolute;
            border-radius: 50%;
            pointer-events: none;
            z-index: 0;
        }

        /* Primary circles - original */
        .circle-1 {
            width: 450px;
            height: 450px;
            background: radial-gradient(circle, var(--tria-orange), var(--tria-red));
            top: -100px;
            right: -150px;
            filter: blur(60px);
            opacity: 0.06;
        }

        .circle-2 {
            width: 350px;
            height: 350px;
            background: radial-gradient(circle, var(--tria-red), var(--tria-orange));
            top: 400px;
            left: -180px;
            filter: blur(50px);
            opacity: 0.06;
        }

        .circle-3 {
            width: 280px;
            height: 280px;
            background: radial-gradient(circle, var(--tria-orange), transparent);
            bottom: 200px;
            right: -100px;
            filter: blur(40px);
            opacity: 0.06;
        }

        /* Additional decorative circles for depth */
        .circle-4 {
            width: 520px;
            height: 520px;
            background: radial-gradient(circle at 30% 30%, rgba(255,152,0,0.12), rgba(229,57,53,0.04));
            top: 120px;
            left: -220px;
            filter: blur(80px);
            opacity: 0.07;
        }

        .circle-5 {
            width: 180px;
            height: 180px;
            background: radial-gradient(circle at 40% 40%, rgba(255,152,0,0.16), transparent 60%);
            top: 600px;
            right: 100px;
            filter: blur(40px);
            opacity: 0.075;
        }

        .circle-6 {
            width: 380px;
            height: 380px;
            background: radial-gradient(circle at 50% 50%, rgba(255,152,0,0.1), transparent 65%);
            top: 900px;
            right: -120px;
            filter: blur(70px);
            opacity: 0.065;
        }

        .circle-7 {
            width: 420px;
            height: 420px;
            background: radial-gradient(circle at 30% 70%, rgba(229,57,53,0.07), rgba(255,152,0,0.05));
            top: 1300px;
            left: -180px;
            filter: blur(75px);
            opacity: 0.06;
        }

        .circle-8 {
            width: 220px;
            height: 220px;
            background: radial-gradient(circle at 60% 40%, rgba(255,152,0,0.14), transparent 55%);
            top: 1700px;
            right: 80px;
            filter: blur(48px);
            opacity: 0.07;
        }

        .circle-9 {
            width: 340px;
            height: 340px;
            background: radial-gradient(circle at 40% 60%, rgba(229,57,53,0.06), rgba(255,152,0,0.08));
            top: 2100px;
            left: -100px;
            filter: blur(65px);
            opacity: 0.065;
        }

        .circle-10 {
            width: 280px;
            height: 280px;
            background: radial-gradient(circle at 50% 50%, rgba(255,152,0,0.11), transparent 60%);
            top: 2500px;
            right: -90px;
            filter: blur(55px);
            opacity: 0.07;
        }

        .circle-11 {
            width: 460px;
            height: 460px;
            background: radial-gradient(circle at 35% 35%, rgba(229,57,53,0.05), rgba(255,152,0,0.09));
            bottom: 600px;
            left: -140px;
            filter: blur(85px);
            opacity: 0.06;
        }

        .circle-12 {
            width: 240px;
            height: 240px;
            background: radial-gradient(circle at 45% 55%, rgba(255,152,0,0.13), transparent 58%);
            bottom: 1000px;
            right: 60px;
            filter: blur(52px);
            opacity: 0.075;
        }

        /* HERO - SPLIT LAYOUT */
        .hero {
            overflow-x: hidden;
            scroll-behavior: smooth;
            margin-top: 1rem;
            scrollbar-width: none;
            position: relative;
            z-index: 1;
        }

        .hero-eyebrow {
            font-size: 0.85rem;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            color: var(--tria-muted);
            animation: fadeInDown 0.6s ease-out;
            text-align: center;
            margin-bottom: 2.5rem;
        }

        @keyframes fadeInDown {
            from {
                opacity: 0;
                transform: translateY(-20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .hero-main {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 4rem;
            align-items: center;
            margin-bottom: 3rem;
        }

        /* LEFT SIDE - LOGO */
        .hero-logo-container {
            animation: fadeInScale 0.8s ease-out 0.2s both;
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
        }

        @keyframes fadeInScale {
            from {
                opacity: 0;
                transform: scale(0.8);
            }
            to {
                opacity: 1;
                transform: scale(1);
            }
        }

        .hero-logo-big {
            width: 380px;
            height: 380px;
            object-fit: contain;
            filter: drop-shadow(0 8px 24px rgba(0, 0, 0, 0.08));
            transition: transform 0.3s ease;
        }

        .hero-logo-big:hover {
            transform: scale(1.05) rotate(5deg);
        }

        /* RIGHT SIDE - CONTENT */
        .hero-content {
            display: flex;
            flex-direction: column;
            gap: 1.2rem;
            animation: fadeInUp 0.6s ease-out 0.3s both;
        }

        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .hero-title {
            font-size: 2.8rem;
            line-height: 1.15;
            margin: 0;
            font-weight: 800;
            letter-spacing: -0.01em;
        }

        .hero-title span {
            background: linear-gradient(135deg, var(--tria-red), var(--tria-orange));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        /* Rotating subtitle */
        .hero-rotator {
            display: inline-block;
            vertical-align: baseline;
            margin-left: 0.25rem;
            overflow: hidden;
            /* increased to accommodate descenders like 'j', 'g', 'y' */
            height: 1.4em;
            line-height: 1.4em;
            padding-bottom: 0.05em;
        }

        .rotator-text {
            display: inline-block;
            opacity: 1;
            transition: opacity 0.32s ease, transform 0.32s ease;
            will-change: opacity, transform;
            min-width: 10ch;
            line-height: 1.4em;
        }

        .hero-subtitle {
            font-size: 1.05rem;
            color: var(--tria-muted);
            line-height: 1.6;
        }

        .hero-actions {
            display: flex;
            flex-wrap: wrap;
            gap: 0.85rem;
            margin-top: 0.7rem;
        }

        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 0.8rem 1.8rem;
            border-radius: 999px;
            border: 1px solid transparent;
            font-size: 0.98rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
        }

        .btn-primary {
            background: linear-gradient(135deg, var(--tria-red), var(--tria-orange));
            color: #ffffff;
            box-shadow: 0 10px 24px rgba(229, 57, 53, 0.3);
        }

        .btn-primary:hover {
            background: linear-gradient(135deg, #c62828, #fb8c00);
            transform: translateY(-2px);
            box-shadow: 0 14px 32px rgba(229, 57, 53, 0.4);
        }

        .btn-ghost {
            background-color: #ffffff;
            color: var(--tria-red);
            border-color: rgba(229, 57, 53, 0.35);
        }

        .btn-ghost:hover {
            background-color: #fff0e0;
            transform: translateY(-2px);
            border-color: var(--tria-red);
        }

        .hero-meta {
            font-size: 0.88rem;
            color: var(--tria-muted);
            line-height: 1.5;
        }

        .hero-meta strong {
            color: var(--tria-red);
        }

        /* HERO GALLERY */
        .hero-gallery-wrapper {
            margin-top: 0;
            margin-inline: -2.25rem;
            padding: 0.9rem 2.25rem 1.1rem 2.25rem;
            border-radius: 2.2rem;
            background: transparent;
            overflow: hidden;
            animation: fadeIn 0.8s ease-out 0.7s both;
        }

        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }

        .hero-gallery {
            display: flex;
            gap: 1rem;
            overflow-x: hidden;
            scroll-behavior: smooth;
            padding-bottom: 0.3rem;
            scrollbar-width: none;
        }

        .hero-gallery::-webkit-scrollbar {
            display: none;
        }

        .hero-strip-image {
            flex: 0 0 270px;
            height: 200px;
            border-radius: 1.4rem;
            object-fit: cover;
            display: block;
            box-shadow: 0 10px 24px rgba(0, 0, 0, 0.14);
            transition: transform 0.3s ease;
        }

        .hero-strip-image:hover {
            transform: scale(1.05);
        }

        /* SECTION TITLES */
        .section {
            margin-top: 4.5rem;
            position: relative;
            z-index: 1;
        }

        .section-heading {
            text-align: center;
            margin-bottom: 2.5rem;
        }

        .section-title {
            font-size: 2rem;
            margin: 0 0 0.6rem 0;
            font-weight: 700;
            letter-spacing: -0.01em;
        }

        .section-subtitle {
            font-size: 1rem;
            color: var(--tria-muted);
            max-width: 650px;
            margin: 0 auto;
            line-height: 1.6;
        }

        /* FEATURES (3 small cards) */
        .features-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 1.5rem;
        }

        .feature-card {
            border-radius: 1.4rem;
            background-color: #ffffff;
            border: 1px solid var(--tria-border);
            padding: 2rem 1.8rem;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04);
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }

        .feature-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, var(--tria-red), var(--tria-orange));
            transform: scaleX(0);
            transition: transform 0.3s ease;
        }

        .feature-card:hover::before {
            transform: scaleX(1);
        }

        .feature-card:hover {
            transform: translateY(-6px);
            box-shadow: 0 16px 40px rgba(0, 0, 0, 0.1);
        }

        .feature-card:hover .feature-icon {
            transform: scale(1.1) rotate(5deg);
            background: linear-gradient(135deg, var(--tria-red), var(--tria-orange));
        }

        .feature-icon {
            width: 64px;
            height: 64px;
            border-radius: 16px;
            background: linear-gradient(135deg, rgba(229, 57, 53, 0.1), rgba(255, 152, 0, 0.1));
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 1.25rem;
            transition: all 0.3s ease;
            box-shadow: 0 4px 12px rgba(229, 57, 53, 0.08);
        }

        .feature-icon svg {
            width: 32px;
            height: 32px;
            stroke: var(--tria-red);
            stroke-width: 2;
            fill: none;
            transition: stroke 0.3s ease;
        }

        .feature-card:hover .feature-icon svg {
            stroke: #ffffff;
        }

        .feature-label {
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.11em;
            color: var(--tria-red);
            margin-bottom: 0.6rem;
            font-weight: 600;
        }

        .feature-title {
            font-size: 1.15rem;
            font-weight: 700;
            margin-bottom: 0.65rem;
            color: var(--tria-text);
        }

        .feature-text {
            font-size: 0.94rem;
            color: var(--tria-muted);
            line-height: 1.65;
        }

        /* IMAGE FEATURE GRID - ENHANCED */
        .image-grid {
            display: grid;
            grid-template-columns: 2fr 1.4fr;
            gap: 1.5rem;
            margin-top: 2rem;
        }

        .image-grid-row {
            display: contents;
        }

        .image-tile {
            border-radius: 1.8rem;
            overflow: hidden;
            position: relative;
            min-height: 260px;
            background: #f7f1e6;
            transition: all 0.3s ease;
        }

        .image-tile:hover {
            transform: translateY(-4px);
            box-shadow: 0 16px 40px rgba(0, 0, 0, 0.12);
        }

        .image-tile img {
            width: 100%;
            height: 100%;
            object-fit: cover;
            display: block;
            transition: transform 0.5s ease;
        }

        .image-tile:hover img {
            transform: scale(1.05);
        }

        .image-tile-overlay {
            position: absolute;
            inset: 0;
            background: linear-gradient(to top, rgba(0, 0, 0, 0.7), transparent 60%);
        }

        .image-tile-content {
            position: absolute;
            left: 1.5rem;
            right: 1.5rem;
            bottom: 1.5rem;
            color: #ffffff;
        }

        .image-tile-title {
            font-size: 1.15rem;
            font-weight: 700;
            margin-bottom: 0.3rem;
        }

        .image-tile-text {
            font-size: 0.9rem;
            opacity: 0.95;
            line-height: 1.5;
        }

        .image-tile--plain {
            background: linear-gradient(135deg, #f8f3eb, #fff7f0);
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 2rem;
            text-align: center;
            border: 1px solid var(--tria-border);
        }

        .image-tile--plain .image-tile-content {
            position: static;
            color: var(--tria-text);
        }

        .image-tile--plain .image-tile-title {
            margin-bottom: 0.5rem;
            font-size: 1.15rem;
        }

        .image-tile--plain .image-tile-text {
            color: var(--tria-muted);
            line-height: 1.6;
        }

        /* BENEFITS - ENHANCED */
        .benefits-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 1.5rem;
            margin-top: 2rem;
        }

        .benefit-card {
            border-radius: 1.4rem;
            border: 1px solid var(--tria-border);
            background: linear-gradient(135deg, #ffffff, #fffbf8);
            padding: 1.5rem;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.03);
            transition: all 0.3s ease;
            position: relative;
        }

        .benefit-card::after {
            content: '';
            position: absolute;
            top: 1rem;
            right: 1rem;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: linear-gradient(135deg, var(--tria-red), var(--tria-orange));
            opacity: 0.08;
            transition: all 0.3s ease;
        }

        .benefit-card:hover::after {
            opacity: 0.15;
            transform: scale(1.2);
        }

        .benefit-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 12px 28px rgba(0, 0, 0, 0.08);
            border-color: rgba(229, 57, 53, 0.2);
        }

        .benefit-title {
            font-size: 1.05rem;
            font-weight: 700;
            margin-bottom: 0.4rem;
            position: relative;
            z-index: 1;
        }

        .benefit-text {
            font-size: 0.9rem;
            color: var(--tria-muted);
            line-height: 1.6;
            position: relative;
            z-index: 1;
        }

        /* CTA BANNER - ENHANCED */
        .cta-banner {
            margin-top: 4rem;
            border-radius: 2rem;
            background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
            color: #ffffff;
            padding: 3rem 2.5rem;
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            justify-content: space-between;
            gap: 1.5rem;
            position: relative;
            overflow: hidden;
        }

        .cta-banner::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(229, 57, 53, 0.15) 0%, transparent 70%);
            animation: ctaPulse 4s ease-in-out infinite;
        }

        @keyframes ctaPulse {
            0%, 100% { transform: scale(1); opacity: 0.5; }
            50% { transform: scale(1.1); opacity: 0.8; }
        }

        .cta-content {
            position: relative;
            z-index: 1;
        }

        .cta-text-main {
            font-size: 1.4rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
            letter-spacing: -0.01em;
        }

        .cta-text-sub {
            font-size: 1rem;
            opacity: 0.9;
            line-height: 1.5;
        }

        .cta-actions {
            display: flex;
            flex-wrap: wrap;
            gap: 0.8rem;
            position: relative;
            z-index: 1;
        }

        .btn-cta-light {
            background-color: #ffffff;
            color: var(--tria-red);
            border-radius: 999px;
            padding: 0.75rem 1.8rem;
            font-size: 0.95rem;
            font-weight: 700;
            border: none;
            cursor: pointer;
            transition: all 0.3s ease;
        }

        .btn-cta-light:hover {
            background-color: #ffe0b2;
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(255, 255, 255, 0.2);
        }

        .btn-cta-ghost {
            background-color: transparent;
            border-radius: 999px;
            padding: 0.7rem 1.6rem;
            font-size: 0.95rem;
            font-weight: 600;
            border: 2px solid rgba(255, 255, 255, 0.3);
            color: #ffffff;
            cursor: pointer;
            transition: all 0.3s ease;
        }

        .btn-cta-ghost:hover {
            background-color: rgba(255, 255, 255, 0.12);
            border-color: rgba(255, 255, 255, 0.6);
            transform: translateY(-2px);
        }

        /* HOW IT WORKS / TECHNOLOGY SECTION */
        .how-section {
            position: relative;
            z-index: 1;
        }

        .how-grid {
            display: grid;
            grid-template-columns: minmax(0, 1.4fr) minmax(0, 2fr);
            gap: 2rem;
            align-items: center;
            margin-top: 2.5rem;
        }

        .how-image-wrapper {
            border-radius: 1.8rem;
            overflow: hidden;
            border: 1px ;
            box-shadow: 0 14px 34px rgba(0,0,0,0.08);
            padding: 1.25rem;

            /* NEW: make image smaller & centered */
            max-width: 800px;
            margin: 0 auto 15px auto; /* bottom margin = 4px */
        }

        .how-image {
            width: 100%;
            display: block;
            border-radius: 1.4rem;
            object-fit: cover;
        }

        /* badge centering */
        .how-badge {
            display: inline-flex;
            align-items: center;
            justify-content: center;   /* center text inside pill */
            gap: 0.4rem;
            padding: 0.25rem 0.7rem;
            border-radius: 999px;
            background: rgba(229,57,53,0.06);
            color: var(--tria-red);
            font-size: 0.78rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.12em;

            /* center the pill in the column */
            margin: 0 auto 0.7rem auto;
        }


        .how-content {
            padding: 0.25rem 0;
        }

        

        .how-lead {
            font-size: 0.98rem;
            color: var(--tria-muted);
            line-height: 1.7;
            margin-bottom: 1.2rem;
        }

        .how-points-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 1rem;
        }

        .how-point-card {
            border-radius: 1.2rem;
            border: 1px solid var(--tria-border);
            padding: 1rem 1.1rem;
            box-shadow: 0 4px 14px rgba(0,0,0,0.03);
        }

        .how-point-title {
            font-size: 0.95rem;
            font-weight: 700;
            margin-bottom: 0.3rem;
            color: var(--tria-text);
        }

        .how-point-text {
            font-size: 0.85rem;
            color: var(--tria-muted);
            line-height: 1.6;
        }

        /* responsive for how-section */
        @media (max-width: 980px) {
            .how-grid {
                grid-template-columns: minmax(0, 1fr);
            }

            .how-image-wrapper {
                max-width: 420px;
                margin: 0 auto;
            }
        }

        @media (max-width: 720px) {
            .how-points-grid {
                grid-template-columns: minmax(0, 1fr);
            }
        }


        /* RESPONSIVE */
        @media (max-width: 980px) {
            .hero-main {
                grid-template-columns: 1fr;
                gap: 2rem;
            }

            .hero-logo-container {
                order: -1;
            }

            .hero-logo-big {
                width: 280px;
                height: 280px;
            }

            .image-grid {
                grid-template-columns: minmax(0, 1fr);
            }

            .decoration-circle {
                opacity: 0.03 !important;
                filter: blur(50px) !important;
            }
        }

        @media (max-width: 900px) {
            .features-grid {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }

            .benefits-grid {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }
        }

        @media (max-width: 720px) {
            .page {
                padding: 2rem 1.1rem 3rem 1.1rem;
            }

            .hero {
                margin-top: 1rem;
            }

            .hero-title {
                font-size: 2.0rem;
            }

            .hero-subtitle {
                font-size: 0.95rem;
            }

            .hero-logo-big {
                width: 200px;
                height: 200px;
            }

            .section-title {
                font-size: 1.6rem;
            }

            .features-grid {
                grid-template-columns: minmax(0, 1fr);
            }

            .benefits-grid {
                grid-template-columns: minmax(0, 1fr);
            }

            .cta-banner {
                padding: 2rem 1.5rem;
            }

            .cta-text-main {
                font-size: 1.2rem;
            }
        }
    </style>
</head>
<body>
    <!-- DECORATIVE CIRCLES - ENHANCED -->
    <div class="decoration-circle circle-1"></div>
    <div class="decoration-circle circle-2"></div>
    <div class="decoration-circle circle-3"></div>
    <div class="decoration-circle circle-4"></div>
    <div class="decoration-circle circle-5"></div>
    <div class="decoration-circle circle-6"></div>
    <div class="decoration-circle circle-7"></div>
    <div class="decoration-circle circle-8"></div>
    <div class="decoration-circle circle-9"></div>
    <div class="decoration-circle circle-10"></div>
    <div class="decoration-circle circle-11"></div>
    <div class="decoration-circle circle-12"></div>

    <!-- NAVBAR -->
    {% include 'partials/navbar.html' %}

    {% load static %}

    <main class="page">
        <!-- HERO -->
        <section class="hero">
            <div class="hero-main">
                <!-- LEFT: LOGO -->
                <div class="hero-logo-container">
                    <img src="https://i.ibb.co.com/fY9F3RwF/tria.png" alt="Tria Logo" class="hero-logo-big" />
                </div>

                <!-- RIGHT: CONTENT -->
                <div class="hero-content">
                    <h1 class="hero-title">
                        Belajar Tarian Nusantara,<br />
                        <span class="hero-rotator"><span class="rotator-text">Dimana Aja</span></span>
                    </h1>
                    

                    <div class="hero-actions">
                        <a href="{% url 'authentication:login' %}" class="btn btn-primary">
                            Jelajahi semua tarian
                        </a>
                        <a href="{% url 'about:about_page' %}" class="btn btn-ghost">
                            Pelajari cerita di balik Tria
                        </a>
                    </div>

                    <p class="hero-meta">
                        Cocok untuk <strong>pelajar</strong>, <strong>komunitas seni</strong>, dan
                        <strong>sekolah</strong> yang ingin menjaga dan merayakan warisan budaya Indonesia.
                    </p>
                </div>
            </div>

            <!-- Horizontal gallery -->
            <div class="hero-gallery-wrapper">
                <div class="hero-gallery">
                    <img
                        src="https://momopururu.com/wp-content/uploads/2022/06/20211218171844_IMG_8553-01-01-scaled-1024x768.jpeg"
                        alt="Tari Kecak · Bali"
                        class="hero-strip-image"
                    />
                    <img
                        src="https://img.antarafoto.com/cache/1200x800/2021/07/01/pagelaran-tari-janger-muda-mudi-bali-uq4u-dom.webp"
                        alt="Tari Janger · Bali"
                        class="hero-strip-image"
                    />
                    <img
                        src="https://www.kelaspintar.id/_next/image?url=https%3A%2F%2Fblog2.kelaspintar.id%2Fblog%2Fwp-content%2Fuploads%2F2021%2F12%2Ftari-bungong-jeumpa.jpg&w=3840&q=75"
                        alt="Tari Bungong Jeumpa · Aceh"
                        class="hero-strip-image"
                    />
                    <img
                        src="https://www.senibudayabetawi.com/wp-content/uploads/2021/12/large-maxresdefault-1-4d2a0786063540dff664d84bfe0d9d07-2.jpg"
                        alt="Lenggang Nyai · Betawi"
                        class="hero-strip-image"
                    />
                    <img
                        src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQe3dCdunJCq8gLwWCdbiWBeqI1VVKZYxH8aw&s"
                        alt="Tari Piring · Minangkabau"
                        class="hero-strip-image"
                    />
                    <img
                        src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTOqlApZqamkNQq2qamDw9xfm28YlT8cmSXZA&s"
                        alt="Tari Saman · Aceh"
                        class="hero-strip-image"
                    />
                    <img
                        src="https://bisniswisata.co.id/wp-content/uploads/2019/08/tari-topeng-betawi-1.jpg"
                        alt="Tari Topeng Betawi"
                        class="hero-strip-image"
                    />
                    <img
                        src="https://upload.wikimedia.org/wikipedia/commons/1/15/Gambyong_Langenkusuma_Pj_DSC_1322.JPG"
                        alt="Tari Gambyong · Jawa Tengah"
                        class="hero-strip-image"
                    />
                </div>
            </div>            
        </section>

        <!-- FEATURES -->
        <section class="section">
            <header class="section-heading">
                <h2 class="section-title">Semua yang Kamu Butuhkan untuk Belajar Tarian Tradisional</h2>
                <p class="section-subtitle">
                    Dari video, langkah tertulis, hingga asesmen gerakan, Tria membantu kamu
                    belajar tarian daerah secara terarah dan menyenangkan.
                </p>
            </header>

            <div class="features-grid">
                <article class="feature-card">
                    <div class="feature-icon">
                        <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <rect x="2" y="2" width="20" height="20" rx="2.18" ry="2.18"/>
                            <line x1="7" y1="2" x2="7" y2="22"/>
                            <line x1="17" y1="2" x2="17" y2="22"/>
                            <line x1="2" y1="12" x2="22" y2="12"/>
                            <line x1="2" y1="7" x2="7" y2="7"/>
                            <line x1="2" y1="17" x2="7" y2="17"/>
                            <line x1="17" y1="17" x2="22" y2="17"/>
                            <line x1="17" y1="7" x2="22" y2="7"/>
                        </svg>
                    </div>
                    <div class="feature-label">Video Tutorial</div>
                    <h3 class="feature-title">Belajar langsung dari visual</h3>
                    <p class="feature-text">
                        Setiap tarian dilengkapi video tutorial yang memecah koreografi menjadi bagian-bagian sederhana.
                        Kamu bisa berhenti, mengulang, dan fokus pada gerakan yang masih sulit.
                    </p>
                </article>

                <article class="feature-card">
                    <div class="feature-icon">
                        <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                            <polyline points="14 2 14 8 20 8"/>
                            <line x1="16" y1="13" x2="8" y2="13"/>
                            <line x1="16" y1="17" x2="8" y2="17"/>
                            <polyline points="10 9 9 9 8 9"/>
                        </svg>
                    </div>
                    <div class="feature-label">Langkah Gerak</div>
                    <h3 class="feature-title">Panduan langkah demi langkah</h3>
                    <p class="feature-text">
                        Gunakan deskripsi gerakan yang jelas sebagai "cheat sheet" saat latihan.
                        Hitungan, arah gerak, dan ekspresi gerakan dijelaskan untuk membangun rasa percaya diri.
                    </p>
                </article>

                <article class="feature-card">
                    <div class="feature-icon">
                        <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                            <polyline points="22 4 12 14.01 9 11.01"/>
                        </svg>
                    </div>
                    <div class="feature-label">Asesmen Gerakan</div>
                    <h3 class="feature-title">Uji dan lihat progresmu</h3>
                    <p class="feature-text">
                        Aktifkan kamera dan lakukan asesmen gerakan.
                        Nilai dan umpan balik membantu kamu mengetahui seberapa jauh perkembangan tarianmu.
                    </p>
                </article>
            </div>
        </section>

                <!-- HOW IT WORKS / TECHNOLOGY -->
                <section class="section how-section">
                    <header class="section-heading">
                        <h2 class="section-title">Bagaimana TRIA Melacak Gerakan dan Memberi Skor</h2>
                        <p class="section-subtitle">
                            Di balik tampilan yang sederhana, TRIA menggunakan kombinasi <strong>Artificial Intelligence</strong> 
                            dan <strong>Computer Vision</strong> untuk membaca gerakanmu, menormalkan perbedaan tubuh setiap penari, 
                            dan memberi penilaian yang adil.
                        </p>
                    </header>
        
                    <div class="how-image-wrapper">
                        <img src="https://i.ibb.co.com/F4xNT4YT/tracking.png"
                             alt="Tracking gerakan tari dengan AI"
                             class="how-image" />
                    </div>
                        
        
                        <div class="how-content">
                            <div class="how-badge">How it works</div>
                            <p class="how-lead">
                                TRIA dibangun di atas framework <strong>Django</strong>, lalu dipadukan dengan 
                                <strong>pose estimation</strong> dan <strong>machine learning</strong> untuk menghadirkan 
                                pengalaman belajar tari yang imersif sekaligus menjadi instrumen konservasi digital 
                                seni tari Nusantara.
                            </p>
        
                            <div class="how-points-grid">
                                <article class="how-point-card">
                                    <h3 class="how-point-title">Pose Estimation Model</h3>
                                    <p class="how-point-text">
                                        Menggunakan model berbasis <strong>MediaPipe</strong> untuk mendeteksi titik sendi tubuh 
                                        (keypoints) secara real-time. Sistem mengenali puluhan titik tubuh utama yang membentuk 
                                        siluet gerak penari, sehingga setiap lengan, lutut, dan kepala bisa dilacak dengan presisi.
                                    </p>
                                </article>
        
                                <article class="how-point-card">
                                    <h3 class="how-point-title">Pose Standardizer</h3>
                                    <p class="how-point-text">
                                        Setiap tubuh punya kelenturan dan jangkauan gerak yang berbeda. 
                                        <strong>Pose Standardizer</strong> menormalkan ukuran dan sudut gerak sehingga penilaian 
                                        tidak bias—fokus pada pola gerakan, bukan tinggi badan atau fleksibilitas semata.
                                    </p>
                                </article>
        
                                <article class="how-point-card">
                                    <h3 class="how-point-title">AI Scoring Engine</h3>
                                    <p class="how-point-text">
                                        Dengan kombinasi <strong>TensorFlow</strong> dan <strong>scikit-learn</strong>, TRIA 
                                        membandingkan pola gerakanmu dengan video referensi. Engine menghitung kesesuaian ritme, 
                                        transisi gerak, dan detail posisi, lalu mengubahnya menjadi skor dan umpan balik yang 
                                        mudah dipahami.
                                    </p>
                                </article>
                            </div>
                        </div>
                    </div>
                </section>
        
        <!-- IMAGE FEATURE GRID -->
        <section class="section">
            <header class="section-heading">
                <h2 class="section-title">Rayakan Kekayaan Tarian dari Berbagai Daerah</h2>
                <p class="section-subtitle">
                    Kecak dari Bali, Saman dari Aceh, hingga Lenggang Nyai dari Betawi—semua hadir dalam satu platform
                    yang mudah diakses.
                </p>
            </header>

            <div class="image-grid">
                <!-- Row 1 -->
                <div class="image-grid-row">
                    <article class="image-tile">
                        <img src="https://momopururu.com/wp-content/uploads/2022/06/20211218171844_IMG_8553-01-01-scaled-1024x768.jpeg"
                             alt="Latihan Tari Kecak" />
                        <div class="image-tile-overlay"></div>
                        <div class="image-tile-content">
                            <div class="image-tile-title">Latihan kelompok yang terasa hidup</div>
                            <p class="image-tile-text">
                                Gunakan Tria untuk menyiapkan tarian bersama teman, komunitas sekolah,
                                atau sanggar—mulai dari latihan dasar hingga gladi bersih.
                            </p>
                        </div>
                    </article>

                    <article class="image-tile image-tile--plain">
                        <div class="image-tile-content">
                            <div class="image-tile-title">Tersusun rapi per tarian</div>
                            <p class="image-tile-text">
                                Setiap tarian memiliki halaman detail: deskripsi, video, urutan gerak,
                                dan tombol langsung ke asesmen. Kamu tinggal pilih tarian dan mulai bergerak.
                            </p>
                        </div>
                    </article>
                </div>

                <!-- Row 2 -->
                <div class="image-grid-row">
                    <article class="image-tile image-tile--plain">
                        <div class="image-tile-content">
                            <div class="image-tile-title">Cocok untuk tugas sekolah & lomba</div>
                            <p class="image-tile-text">
                                Tria membantu timmu menghafalkan koreografi dengan lebih cepat,
                                sehingga latihan bisa fokus ke kekompakan dan ekspresi panggung.
                            </p>
                        </div>
                    </article>

                    <article class="image-tile">
                        <img src="https://bisniswisata.co.id/wp-content/uploads/2019/08/tari-topeng-betawi-1.jpg"
                             alt="Tari Topeng Betawi" />
                        <div class="image-tile-overlay"></div>
                        <div class="image-tile-content">
                            <div class="image-tile-title">Visual yang menghidupkan karakter</div>
                            <p class="image-tile-text">
                                Dari Topeng Betawi hingga Reog Ponorogo, visual kuat membantu kamu
                                memahami karakter dan cerita di balik setiap gerakan.
                            </p>
                        </div>
                    </article>
                </div>
            </div>
        </section>

        
        <!-- BENEFITS -->
        <section class="section">
            <header class="section-heading">
                <h2 class="section-title">Kenapa Tria Cocok untuk Kamu?</h2>
                <p class="section-subtitle">
                    Dirancang khusus untuk pelajar dan komunitas yang ingin belajar tarian tradisional
                    secara serius, namun tetap santai dan menyenangkan.
                </p>
            </header>

            <div class="benefits-grid">
                <article class="benefit-card">
                    <h3 class="benefit-title">Belajar mandiri dari rumah</h3>
                    <p class="benefit-text">
                        Akses materi kapan saja tanpa terikat tempat.
                        Cocok untuk latihan sebelum tampil atau mengulang materi sanggar.
                    </p>
                </article>

                <article class="benefit-card">
                    <h3 class="benefit-title">Mendukung pelestarian budaya</h3>
                    <p class="benefit-text">
                        Dengan mempelajari tarian daerah, kamu ikut menjaga
                        warisan budaya Indonesia agar tetap hidup di generasi muda.
                    </p>
                </article>

                <article class="benefit-card">
                    <h3 class="benefit-title">Struktur yang jelas untuk pengajar</h3>
                    <p class="benefit-text">
                        Guru atau pelatih bisa menggunakan Tria sebagai pendamping
                        materi: pilih tarian, tunjukkan video, lalu bahas langkah geraknya.
                    </p>
                </article>
            </div>
        </section>

        <!-- CTA -->
        <section class="section">
            <div class="cta-banner">
                <div class="cta-content">
                    <div class="cta-text-main">
                        Siap memulai perjalanan belajar tarian tradisionalmu?
                    </div>
                    <div class="cta-text-sub">
                        Pilih satu tarian hari ini, tonton tutorialnya, dan coba asesmen pertama
                        kamu bersama Tria.
                    </div>
                </div>
                <div class="cta-actions">
                    <a href="{% url 'authentication:login' %}" class="btn-cta-light">
                        Lihat daftar tarian
                    </a>
                    <a href="{% url 'about:about_page' %}" class="btn-cta-ghost">
                        Tentang Tria
                    </a>
                </div>
            </div>
        </section>
    </main>

    <script>
        document.addEventListener('DOMContentLoaded', function () {
          const gallery = document.querySelector('.hero-gallery');
          if (gallery) {
            // Duplicate images once so we can loop seamlessly
            if (!gallery.dataset.looped) {
              const clones = Array.from(gallery.children).map(node => node.cloneNode(true));
              clones.forEach(clone => gallery.appendChild(clone));
              gallery.dataset.looped = 'true';
            }

            let rafId;
            let pos = 0;
            const halfWidth = () => gallery.scrollWidth / 2;
            const step = 0.5; // speed
    
            function autoScroll() {
              pos += step;
              if (pos >= halfWidth()) pos = 0;
              gallery.scrollLeft = pos;
              rafId = requestAnimationFrame(autoScroll);
            }
    
            rafId = requestAnimationFrame(autoScroll);
    
            gallery.addEventListener('mouseenter', () => {
              if (rafId) cancelAnimationFrame(rafId);
            });
    
            gallery.addEventListener('mouseleave', () => {
              rafId = requestAnimationFrame(autoScroll);
            });
          }

          // Rotating subtitle text (Dimana Aja -> Kapan Aja -> Siapa Aja -> Dengan TRIA)
          const rotatorEl = document.querySelector('.rotator-text');
          if (rotatorEl) {
            const phrases = ['Dimana Aja', 'Kapan Aja', 'Siapa Aja', 'Dengan TRIA'];
            let ridx = 0;
            rotatorEl.textContent = phrases[ridx];
            rotatorEl.style.opacity = '1';

            setInterval(() => {
              rotatorEl.style.opacity = '0';
              setTimeout(() => {
                ridx = (ridx + 1) % phrases.length;
                rotatorEl.textContent = phrases[ridx];
                rotatorEl.style.opacity = '1';
              }, 340);
            }, 2000);
          }
        });
    </script>
</body>
</html>
```

### tria/templates/partials/navbar.html

```html
{% load static %}
<style>
    /* Existing scoped styles you already had */
    .nav-logout {
        background: linear-gradient(135deg,#e53935,#ff9800);
        color: #ffffff !important;
        font-weight: 700;
        border-radius: 6px;
        padding: 0.45rem 0.9rem;
        box-shadow: 0 8px 20px rgba(229,57,53,0.18);
        display: inline-block;
    }
    .nav-logout:hover { transform: translateY(-2px); }

    .nav-avatar {
        width: 34px;
        height: 34px;
        border-radius: 8px;
        background: linear-gradient(135deg,#e53935,#ff9800);
        color: #fff;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 0.95rem;
    }

    /* === MOBILE NAV ADDITIONS === */

    /* Layout base (if not already in your global CSS) */
    .navbar {
        background-color: #ffffff;
        border-bottom: 1px solid #f3eee7;
        position: sticky;
        top: 0;
        z-index: 50;
    }
    .nav-inner {
        max-width: 1100px;
        margin: 0 auto;
        padding: 0.75rem 1.5rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
        position: relative;
    }
    .nav-brand {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        text-decoration: none;
        color: inherit;
    }
    .nav-logo {
        height: 36px;
        width: 36px;
        object-fit: contain;
    }
    .nav-title {
        font-weight: 700;
        letter-spacing: 0.03em;
        font-size: 1.1rem;
    }
    .nav-links {
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }
    .nav-link {
        padding: 0.4rem 0.75rem;
        border-radius: 999px;
        text-decoration: none;
        color: inherit;
        font-size: 0.95rem;
        transition: background-color 0.2s ease, color 0.2s ease, transform 0.1s ease;
    }
    .nav-link:hover {
        background-color: #fff1df;
        color: #e53935;
        transform: translateY(-1px);
    }
    .nav-cta {
        background: linear-gradient(135deg, #e53935, #ff9800);
        color: #ffffff;
        font-weight: 600;
    }
    .nav-cta:hover {
        background: linear-gradient(135deg, #c62828, #fb8c00);
        color: #ffffff;
    }
    .nav-actions {
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }

    /* Wrapper for links + actions (used for mobile dropdown) */
    .nav-menu {
        display: flex;
        align-items: center;
        gap: 1rem;
    }

    /* Hamburger button */
    .nav-toggle {
        display: none; /* shown only on mobile */
        border: none;
        background: none;
        cursor: pointer;
        padding: 0.25rem;
        margin-left: auto;
    }
    .nav-toggle-line {
        width: 22px;
        height: 2px;
        border-radius: 999px;
        background-color: #333;
        display: block;
        position: relative;
        transition: background 0.2s ease;
    }
    .nav-toggle-line::before,
    .nav-toggle-line::after {
        content: "";
        position: absolute;
        left: 0;
        width: 22px;
        height: 2px;
        border-radius: 999px;
        background-color: #333;
        transition: transform 0.2s ease, top 0.2s ease, bottom 0.2s ease;
    }
    .nav-toggle-line::before {
        top: -6px;
    }
    .nav-toggle-line::after {
        bottom: -6px;
    }
    .nav-toggle.is-open .nav-toggle-line {
        background-color: transparent;
    }
    .nav-toggle.is-open .nav-toggle-line::before {
        top: 0;
        transform: rotate(45deg);
    }
    .nav-toggle.is-open .nav-toggle-line::after {
        bottom: 0;
        transform: rotate(-45deg);
    }

    /* Desktop: center Home / About / Tarian / Daftar Sanggar */
@media (min-width: 769px) {
    .nav-inner {
        justify-content: flex-start;   /* brand on the left, menu takes the rest */
    }

    /* hide hamburger on desktop */
    .nav-toggle {
        display: none;
    }

    /* nav-menu becomes a normal flex row between logo and right edge */
    .nav-menu {
        position: static;
        display: flex;
        flex: 1;
        align-items: center;
        padding: 0;
        background: transparent;
        border-bottom: none;
        gap: 0; /* we’ll handle spacing inside */
    }

    /* THIS is the trick: links block sits in the middle */
    .nav-links {
        display: flex;
        gap: 0.75rem;
        margin: 0 auto;     /* pushes it to the center of nav-menu */
    }

    /* profile/login section stays right */
    .nav-actions {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin-left: auto;  /* pushes actions to the far right */
    }
}

    /* === RESPONSIVE BEHAVIOUR === */
    @media (max-width: 768px) {
        .nav-inner {
            align-items: center;
        }

        /* show hamburger */
        .nav-toggle {
            display: inline-flex;
            align-items: center;
            justify-content: center;
        }

        /* hide menu by default on mobile */
        .nav-menu {
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            background-color: #ffffff;
            border-bottom: 1px solid #f3eee7;
            padding: 0.75rem 1.5rem 1rem 1.5rem;
            flex-direction: column;
            align-items: flex-start;
            gap: 0.35rem;
            display: none;
        }
        .nav-menu.is-open {
            display: flex;
        }

        .nav-links {
            flex-direction: column;
            align-items: flex-start;
            width: 100%;
        }

        .nav-actions {
            flex-direction: column;
            width: 100%;
            align-items: stretch;
            margin-top: 0.35rem;
        }

        .nav-actions .nav-link,
        .nav-links .nav-link {
            width: 100%;
            text-align: left;
        }
    }
</style>

<nav class="navbar">
    <div class="nav-inner">
        <a href="{% url 'home' %}" class="nav-brand">
            <img src="https://i.ibb.co.com/fY9F3RwF/tria.png" alt="Tria logo" class="nav-logo" />
            <span class="nav-title">TRIA</span>
        </a>

        <!-- HAMBURGER BUTTON (visible on mobile) -->
        <button class="nav-toggle" type="button" aria-label="Toggle navigation">
            <span class="nav-toggle-line"></span>
        </button>

        <!-- MENU: links + actions grouped together -->
        <div class="nav-menu">
            <div class="nav-links">
                <a href="{% url 'home' %}" class="nav-link">Home</a>
                <a href="{% url 'about:about_page' %}" class="nav-link">About</a>
                {% if user.is_authenticated %}
                    <a href="{% url 'dances:dance_list' %}" class="nav-link nav-cta">Tarian</a>
                    <a href="{% url 'daftarsanggar:index' %}" class="nav-link nav-cta">Daftar Sanggar</a>
                {% endif %}
            </div>

            <div class="nav-actions">
                {% if user.is_authenticated %}
                    <a href="{% url 'authentication:profile' %}"
                       class="nav-link"
                       title="Profile"
                       style="display:flex;align-items:center;gap:0.55rem;">
                        <div class="nav-avatar">{{ user.username|slice:":1"|upper }}</div>
                        <span class="muted" style="font-weight:600;color:inherit;">
                            {{ user.username }}
                        </span>
                    </a>
                {% else %}
                    <a href="{% url 'authentication:login' %}" class="nav-link">Login</a>
                    <a href="{% url 'authentication:register' %}" class="nav-link nav-cta">Register</a>
                {% endif %}
            </div>
        </div>
    </div>
</nav>

<script>
    document.addEventListener('DOMContentLoaded', function () {
        const toggle = document.querySelector('.nav-toggle');
        const menu = document.querySelector('.nav-menu');

        if (!toggle || !menu) return;

        toggle.addEventListener('click', function () {
            menu.classList.toggle('is-open');
            toggle.classList.toggle('is-open');
        });
    });
</script>
```
