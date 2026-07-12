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

## Demonstration & Recording Workflow

To test or record a demo of the role-based workflows and security, use the role accounts below.

### Demo Credentials

| Role | Name | Login Email | Password |
| :--- | :--- | :--- | :--- |
| **Employee** | John Doe | `john@example.com` | `john` *(or `admin`)* |
| **Department Head** | Jane Smith | `jane@example.com` | `jane` *(or `admin`)* |
| **Asset Manager** | Alice Johnson | `alice@example.com` | `alice` *(or `admin`)* |
| **Admin** | Bob Miller | `bob@example.com` | `bob` *(or `admin`)* |

### Suggested Video Recording Walkthrough (3 Minutes)

1. **Employee Workspace (John Doe)**:
   - Log in using `john@example.com` (password: `john`).
   - Notice the restricted sidebar (**Organization Setup**, **Asset Audit**, and **Reports & Analytics** are hidden).
   - Go to **Resource Booking** and reserve a slot. Show conflict checking by trying to book a overlapping slot.
   - Click **Switch Account/Role** in the sidebar to lock the workspace.
2. **Department Head (Jane Smith)**:
   - Log in using `jane@example.com` (password: `jane`).
   - Notice department assets access and initiate a custodian transfer under **Allocations & Transfers**.
3. **Administrator Workspace (Bob Miller)**:
   - Log in using `bob@example.com` (password: `bob` or `admin`).
   - Notice all tabs are fully visible, including **Organization Setup** and **Reports & Analytics**.
   - Go to the **Maintenance Kanban** and advance a ticket (Approve, Assign, Start, Resolve).
   - Switch to Odoo's native backend view via the grid icon, open any asset, click **Print**, and select **Asset Labels** to show the printable tag sticker PDF with its **dynamic QR Code**.

---

## Running Backend Unit Tests

Run the automated test suite directly inside the Docker container:

```bash
docker exec -it assetflow-odoo odoo -d assetflow -i assetflow --db_host=db --db_user=odoo --db_password=odoo --test-enable --stop-after-init
```

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
