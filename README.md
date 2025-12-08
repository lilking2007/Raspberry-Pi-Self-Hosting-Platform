# Raspberry Pi Self-Hosting Platform

## Introduction

This project is a complete **Platform-as-a-Service (PaaS)** designed specifically for a **Raspberry Pi 5 home-lab**. It allows you to deploy, manage, and expose static websites to the global internet without complex router port forwarding or manual server configuration.

Think of it as your own private "Netlify" or "Vercel" hosted on your Raspberry Pi. You can upload a website (as a `.zip` file) through a beautiful web dashboard, and the platform automatically handles:
- **Unpacking and Validation**: Ensuring your site files are safe and correct.
- **Nginx Configuration**: Automatically creating web server rules for your site.
- **Global Exposure**: Using Cloudflare Tunnels to securely expose your `localhost` sites to the world.
- **Access Control**: Optionally restricting access to your sites via passwords, IP whitelists, or tokens.

## Features

- 🖥️ **Web Dashboard**: A modern React-based UI to manage all your sites.
- 📦 **One-Click Deployment**: Upload a ZIP file, and it's live in seconds.
- 🔒 **Secure by Design**: Uses Cloudflare Tunnels (no open firewall ports required).
- 🔑 **Access Control**: Protect private sites with a password or limit access to specific IP addresses.
- 🐳 **Fully Containerized**: Runs entirely in Docker, keeping your Raspberry Pi clean and organized.
- ⚡ **High Performance**: Uses Nginx for serving static files efficiently.

## Architecture

The platform runs as a set of connected Docker containers:

1.  **Frontend**: The React UI where you interact with the platform.
2.  **Admin API (FastAPI)**: The brain of the operation. It manages users, site metadata, and uploads.
3.  **Worker (Python)**: The muscle. It processes background jobs specifically for unzipping files and generating configurations.
4.  **Nginx**: The web server. It serves your actual website files.
5.  **Database & Queue**: PostgreSQL for storing data and Redis for managing background tasks.
6.  **Cloudflare Tunnel**: The bridge to the internet.

## Prerequisites

Before starting, ensure your host machine (Raspberry Pi or Desktop) has the following installed:

1.  **Docker**: [Install Docker Engine](https://docs.docker.com/engine/install/)
2.  **Docker Compose**: Included with modern Docker Desktop or installed separately on Linux.
3.  **Git**: To download this repository.

*Note: This platform is optimized for Linux/Raspberry Pi OS but runs perfectly on Windows/Mac for development.*

## Installation & Setup Guide

Follow these steps to get your platform running using our recommended Git method or the manual transfer method (useful for SD cards).

### Option 1: Git Clone (Recommended)
Open your terminal and clone this repository:

```bash
git clone <repository-url> self-hosting-platform
cd self-hosting-platform
```

### Option 2: Offline / Manual Transfer (For SD Cards)
If you are transferring files via a USB stick or SD card (e.g., to bypass "too many files" upload limits or wifi issues):

1.  **Download Source**: Download the provided `RPi_Platform_Source.zip` file (which contains all source code but excludes heavy dependencies like `node_modules`).
2.  **Transfer**: Copy this zip file to your Raspberry Pi or into the folder you want via USB/SD card.
3.  **Unzip**: Extract the zip file on the Raspberry Pi.
4.  **Open Terminal**: Navigate into the unzipped folder in your terminal.
5.  **Proceed to Step 2**.

### 2. Configure Environment Variables
The platform needs some secret keys to run securely. We provide a template file for this.

1.  Copy the example file:
    ```bash
    cp .env.example .env
    ```
    *(On Windows PowerShell, use `Copy-Item .env.example .env`)*

2.  Open `.env` in a text editor and fill in the details:
    ```env
    # Database Credentials (can leave defaults for local testing)
    POSTGRES_USER=platform
    POSTGRES_PASSWORD=changeme
    POSTGRES_DB=platform

    # Security
    SECRET_KEY=change_this_to_a_long_random_string

    # Cloudflare Tunnel (Required for public internet access)
    TUNNEL_TOKEN=eyJhIjoi... <paste your token here>
    ```

    *If you don't have a Cloudflare Tunnel Token yet, you can leave it blank, but your sites will only be accessible on your local network/computer.*

### 3. Build and Run
Start the entire system with one command. This will download all necessary services and build the custom application code.

```bash
docker-compose up -d --build
```

- `-d`: Runs the containers in the background (detached mode).
- `--build`: Forces a rebuild of the images to ensure you have the latest code.

Wait a few minutes. You can check the status of the containers with:
```bash
docker-compose ps
```
docker-compose ps
```

### 4. Running with Portainer (Optional)

If you prefer managing this stack via Portainer on your Raspberry Pi:

1.  **Access Portainer**: Log in to your Portainer UI.
2.  **Create Stack**:
    *   Go to **Stacks** -> **Add stack**.
    *   **Name**: `self-hosting-platform`.
    *   **Build method**: Select "Repository" (easiest) or "Upload" (if you have the files locally).
        *   *Repository URL*: Enter the URL of your git repo.
        *   *Compose path*: `docker-compose.yml`.
    *   **Environment variables**: Manually add the variables from your `.env` file here (e.g., `POSTGRES_PASSWORD`, `TUNNEL_TOKEN`).
3.  **Deploy**: Click **Deploy the stack**.

## How to Use

### 1. Access the Dashboard
Open your web browser and navigate to:
**http://localhost:3000**

You will be redirected to the Login screen.

### 2. Login
Since this is a fresh install, you need to create your first user. You can do this via the API (since there is no public registration page for security).

**Option A: Create User via Command Line (CURL)**
```bash
curl -X POST "http://localhost:8000/users" \
     -H "Content-Type: application/json" \
     -d '{"username": "admin", "password": "superpassword", "email": "admin@example.com"}'
```

**Option B: Quick Login**
If you just want to look around, you can create a user using the API docs found at `http://localhost:8000/docs`.
1.  Go to `http://localhost:8000/docs`.
2.  Find `POST /users`.
3.  Click "Try it out" and execute.

Once created, log in on the Dashboard.

### 3. Deploy Your First Website
1.  **Prepare your site**: Zip up your website files.
    *   **Important**: The `index.html` file must be at the root of the zip, or inside a single top-level folder.
    *   Example valid structure:
        ```text
        my-site.zip
        ├── index.html
        ├── css/
        │   └── style.css
        └── js/
            └── app.js
        ```
2.  **Create Site in Dashboard**:
    *   Click **"+ New Site"**.
    *   **Slug**: Enter a unique name (e.g., `my-blog`). This will determine your local URL (`http://my-blog.lan`).
    *   **Display Name**: Friendly name (e.g., "My Personal Blog").
    *   Click **Create**.
3.  **Upload Content**:
    *   In the site card, click "Choose File" and select your `.zip`.
    *   The status will change to **Deploying**... and then **Deployed**.
4.  **View Site**:
    *   Click the "Visit Site" link.
    *   *Note: For local viewing without Cloudflare, you might need to add `127.0.0.1 my-blog.lan` to your computer's `hosts` file.*

## Advanced: Public Internet Access

To make your sites accessible to the world (e.g., `https://blog.yourdomain.com`), you need to set up **Cloudflare Tunnel**.

1.  Go to the [Cloudflare Zero Trust Dashboard](https://one.dash.cloudflare.com/).
2.  Create a new Tunnel and get the **Tunnel Token**.
3.  Paste this token into your `.env` file (`TUNNEL_TOKEN=...`).
4.  Restart the platform: `docker-compose up -d`.
5.  In Cloudflare Dashboard, configure a **Public Hostname**:
    *   **Public hostname**: `blog.yourdomain.com`
    *   **Service**: `HTTP` -> `localhost:80` (Directs traffic to the Nginx container inside the platform).

## Updating

To update the platform to the latest version:
1.  Pull the latest code:
    ```bash
    git pull origin main
    ```
2.  Rebuild the containers:
    ```bash
    docker-compose up -d --build
    ```

## Stopping the Platform

To stop the containers but preserve your data:
```bash
docker-compose stop
```

To stop and remove the containers (data in volumes is still safe):
```bash
docker-compose down
```

## Troubleshooting

- **Containers won't start?**
  Run `docker-compose logs -f` to see real-time error messages.
- **Site says "404 Not Found"?**
  Check the zip structure. Ensure `index.html` is present. Check logs: `docker-compose logs worker`.
- **Database connection error?**
  Ensure the `db` container is healthy. It might take a few seconds to start up initially...
