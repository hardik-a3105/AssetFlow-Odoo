# AssetFlow — Enterprise Asset & Resource Management

An Odoo 17 module for tracking, allocating, and maintaining physical assets and shared resources.

Built with **Python**, **JavaScript (OWL)**, **XML**, and **CSS** on top of the **Odoo 17 Community Edition** framework.

---

## Prerequisites

Your machine needs **only two things** installed:

1. **Git** — [Download here](https://git-scm.com/downloads)
2. **Docker Desktop** — [Download here](https://www.docker.com/products/docker-desktop/)

> Make sure Docker Desktop is **running** before you proceed.

---

## Setup Instructions (3 Steps)

### Step 1: Clone the Repository

```bash
git clone https://github.com/hardik-a3105/AssetFlow-Odoo.git
cd AssetFlow-Odoo
```

### Step 2: Start the Containers

```bash
docker compose up -d
```

This pulls two Docker images automatically (first run takes 2–3 minutes):
- **`odoo:17.0`** — the Odoo web server
- **`postgres:15`** — the PostgreSQL database

### Step 3: Open in Browser

Wait ~30 seconds for Odoo to finish loading, then open:

```
http://localhost:8069
```

**Login credentials:**
- **Email:** `admin`
- **Password:** `admin`

> On first launch, Odoo will automatically create the database, install the AssetFlow module, and load all demo data.

---

## That's It! 🎉

You should see the AssetFlow dashboard with:
- KPI cards (Available Assets, Active Bookings, etc.)
- Quick Action buttons
- Quick Start Checklist
- Recent Activity feed

Navigate through the left sidebar to explore Assets, Allocations, Bookings, Maintenance, Audits, and Reports.

---

## Stopping & Restarting

```bash
# Stop everything
docker compose down

# Start again (data is preserved)
docker compose up -d

# Full reset (wipes database)
docker compose down -v
docker compose up -d
```

---

## Tech Stack

| Layer | Technology |
|:------|:-----------|
| Platform | Odoo 17.0 Community Edition |
| Backend | Python 3.10 |
| Frontend | JavaScript (OWL Framework) |
| Styling | CSS3 |
| Views | Odoo XML |
| Database | PostgreSQL 15 |
| Container | Docker |

---

## License

MIT License — see [LICENSE](LICENSE) for details.
