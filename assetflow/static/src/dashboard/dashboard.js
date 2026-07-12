/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, useState } from "@odoo/owl";

import { session } from "@web/session";

export class AssetFlowDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.notification = useService("notification");

        // Comprehensive state to drive all 10 screens
        this.state = useState({
            currentScreen: "dashboard", // 'login' | 'dashboard' | 'org_setup' | 'assets' | 'allocation_transfer' | 'resource_booking' | 'maintenance' | 'audit' | 'reports' | 'notifications'
            isLoggedIn: true,
            loginEmail: "",
            loginPassword: "",
            loading: false,

            // Current logged-in user role information
            currentUserRole: "employee", // 'employee' | 'dept_head' | 'manager' | 'admin'
            currentUserId: null,

            // Raw record arrays from Odoo
            dashboardData: {
                kpis: {
                    available_assets: 0,
                    allocated_assets: 0,
                    bookable_resources: 0,
                    active_bookings: 0,
                    pending_transfers: 0,
                    upcoming_returns: 0
                },
                checklist: {
                    has_assets: false,
                    has_bookings: false,
                    has_maintenances: false
                },
                overdue: {
                    count: 0,
                    list: []
                },
                activities: []
            },
            assets: [],
            departments: [],
            categories: [],
            employees: [],
            bookings: [],
            maintenanceTickets: [],
            allocations: [],
            auditCycles: [],
            auditLines: [],

            // Selections & Filters
            selectedAssetId: "",
            selectedAsset: null, // holds detailed data for allocation check
            assetHistory: [], // allocations for selected asset
            bookingResource: "",
            bookingDate: new Date().toISOString().split("T")[0],
            selectedAuditCycleId: null,

            // Form inputs
            transferForm: {
                to_employee_id: "",
                reason: ""
            },
            bookingForm: {
                employee_id: "",
                start_time: "09:00",
                end_time: "10:00"
            },
            newAssetForm: {
                name: "",
                category_id: "",
                serial_no: "",
                acquisition_date: new Date().toISOString().split("T")[0],
                acquisition_cost: 100,
                condition: "good",
                location: "",
                is_bookable: false,
                department_id: ""
            },
            newDeptForm: {
                name: "",
                code: "",
                head_id: "",
                parent_id: ""
            },
            newCatForm: {
                name: "",
                warranty_period: 12,
                maintenance_interval: 6
            },

            // Modal visibility toggles
            showModal: null, // 'register_asset' | 'add_department' | 'add_category' | 'book_slot'
            activeTabOrg: "departments", // 'departments' | 'categories' | 'employees'
            searchQuery: "",
            filterCategory: "",
            filterStatus: "",
            filterDepartment: "",
            logFilter: "all" // 'all' | 'alerts' | 'approvals' | 'bookings'
        });

        onWillStart(async () => {
            this.state.currentUserId = session.uid;
            await this.loadAllData();
            this.determineUserRole();
        });
    }

    // Load everything from Odoo
    async loadAllData() {
        this.state.loading = true;
        try {
            // 1. Load KPI, overdue, and activity feed
            const dashData = await this.orm.call("assetflow.asset", "get_dashboard_data", []);
            if (dashData) {
                this.state.dashboardData = dashData;
            }

            // 2. Load Assets
            this.state.assets = await this.orm.searchRead(
                "assetflow.asset",
                [],
                ["name", "tag", "category_id", "serial_no", "acquisition_date", "acquisition_cost", "condition", "location", "is_bookable", "department_id", "state"]
            );

            // 3. Load Departments
            this.state.departments = await this.orm.searchRead(
                "assetflow.department",
                [],
                ["name", "code", "head_id", "parent_id", "status"]
            );

            // 4. Load Categories
            this.state.categories = await this.orm.searchRead(
                "assetflow.category",
                [],
                ["name", "warranty_period", "maintenance_interval"]
            );

            // 5. Load Employees (internal users)
            this.state.employees = await this.orm.searchRead(
                "res.users",
                [["share", "=", false]],
                ["name", "login", "department_id", "role", "active"]
            );

            // 6. Load Bookings
            this.state.bookings = await this.orm.searchRead(
                "assetflow.booking",
                [],
                ["resource_id", "employee_id", "start_datetime", "end_datetime", "state"]
            );

            // 7. Load Maintenance Tickets
            this.state.maintenanceTickets = await this.orm.searchRead(
                "assetflow.maintenance",
                [],
                ["asset_id", "issue", "priority", "technician_id", "state", "create_uid"]
            );

            // 8. Load Allocations
            this.state.allocations = await this.orm.searchRead(
                "assetflow.allocation",
                [],
                ["asset_id", "employee_id", "department_id", "expected_return_date", "actual_return_date", "state"]
            );

            // 9. Load Audits
            this.state.auditCycles = await this.orm.searchRead(
                "assetflow.audit.cycle",
                [],
                ["name", "department_id", "date_from", "date_to", "auditor_ids", "state", "discrepancy_summary"]
            );

            // Set default audit cycle if empty
            if (this.state.auditCycles.length > 0 && !this.state.selectedAuditCycleId) {
                this.state.selectedAuditCycleId = this.state.auditCycles[0].id;
            }

            if (this.state.selectedAuditCycleId) {
                await this.loadAuditLines(this.state.selectedAuditCycleId);
            }

            // Set default resource for booking if empty
            const bookables = this.state.assets.filter(a => a.is_bookable);
            if (bookables.length > 0 && !this.state.bookingResource) {
                this.state.bookingResource = bookables[0].id.toString();
            }

        } catch (error) {
            console.error("Failed to load Odoo data:", error);
        } finally {
            this.state.loading = false;
        }
    }

    async loadAuditLines(cycleId) {
        try {
            this.state.auditLines = await this.orm.searchRead(
                "assetflow.audit.line",
                [["cycle_id", "=", parseInt(cycleId)]],
                ["cycle_id", "asset_id", "expected_location", "result"]
            );
        } catch (error) {
            console.error("Failed to load audit lines:", error);
        }
    }

    determineUserRole() {
        if (!this.state.currentUserId || this.state.employees.length === 0) return;
        const currentUser = this.state.employees.find(e => e.id === this.state.currentUserId);
        if (currentUser && currentUser.role) {
            this.state.currentUserRole = currentUser.role;
        } else {
            this.state.currentUserRole = "employee";
        }
    }

    // Screen switching
    switchScreen(screenName) {
        this.state.currentScreen = screenName;
        // Auto load on switch to clean any selections
        if (screenName === 'allocation_transfer') {
            this.state.selectedAssetId = "";
            this.state.selectedAsset = null;
            this.state.assetHistory = [];
        }
    }

    switchSimulatedRole(role) {
        this.state.currentUserRole = role;
        this.notification.add(`Simulated role updated to ${role.replace('_', ' ').toUpperCase()}`, { type: "info" });
    }

    // Mock Login/Lock screen
    handleLogin() {
        if (!this.state.loginEmail || !this.state.loginPassword) {
            this.notification.add("Please fill in email and password.", { type: "danger" });
            return;
        }
        const matchedUser = this.state.employees.find(e => e.login === this.state.loginEmail);
        if (!matchedUser) {
            this.notification.add("Invalid login credentials.", { type: "danger" });
            return;
        }
        // Validate password (matches username prefix or 'admin')
        const expectedPassword = matchedUser.login.split('@')[0];
        if (this.state.loginPassword !== expectedPassword && this.state.loginPassword !== 'admin') {
            this.notification.add(`Invalid password. (Hint: use password '${expectedPassword}')`, { type: "danger" });
            return;
        }
        this.state.currentUserRole = matchedUser.role || "employee";
        this.state.currentUserId = matchedUser.id;
        this.state.isLoggedIn = true;
        this.state.currentScreen = "dashboard";
        this.notification.add(`Logged in as ${matchedUser.name}!`, { type: "success" });
    }

    handleLogout() {
        this.state.isLoggedIn = false;
        this.state.currentScreen = "login";
        this.state.loginEmail = "";
        this.state.loginPassword = "";
        this.state.currentUserId = null;
    }

    // Screen 3: Org Setup actions
    setOrgTab(tab) {
        this.state.activeTabOrg = tab;
    }

    async toggleDeptStatus(deptId, currentStatus) {
        if (this.state.currentUserRole !== 'admin') {
            this.notification.add("Admin privileges required.", { type: "danger" });
            return;
        }
        const nextStatus = currentStatus === 'active' ? 'inactive' : 'active';
        await this.orm.write("assetflow.department", [deptId], { status: nextStatus });
        await this.loadAllData();
        this.notification.add(`Department status updated to ${nextStatus}`, { type: "success" });
    }

    async promoteEmployee(empId, actionType) {
        if (this.state.currentUserRole !== 'admin') {
            this.notification.add("Admin privileges required.", { type: "danger" });
            return;
        }
        if (actionType === 'manager') {
            await this.orm.call("res.users", "action_promote_manager", [empId]);
            this.notification.add("Employee promoted to Asset Manager", { type: "success" });
        } else if (actionType === 'head') {
            await this.orm.call("res.users", "action_promote_dept_head", [empId]);
            this.notification.add("Employee promoted to Department Head", { type: "success" });
        }
        await this.loadAllData();
        this.determineUserRole();
    }

    async submitNewDept() {
        if (this.state.currentUserRole !== 'admin') {
            this.notification.add("Admin privileges required.", { type: "danger" });
            return;
        }
        if (!this.state.newDeptForm.name) {
            this.notification.add("Department name is required.", { type: "danger" });
            return;
        }
        const vals = {
            name: this.state.newDeptForm.name,
            code: this.state.newDeptForm.code
        };
        if (this.state.newDeptForm.head_id) vals.head_id = parseInt(this.state.newDeptForm.head_id);
        if (this.state.newDeptForm.parent_id) vals.parent_id = parseInt(this.state.newDeptForm.parent_id);

        await this.orm.create("assetflow.department", [vals]);
        this.state.showModal = null;
        this.state.newDeptForm = { name: "", code: "", head_id: "", parent_id: "" };
        await this.loadAllData();
        this.notification.add("Department added successfully!", { type: "success" });
    }

    async submitNewCategory() {
        if (this.state.currentUserRole !== 'admin') {
            this.notification.add("Admin privileges required.", { type: "danger" });
            return;
        }
        if (!this.state.newCatForm.name) {
            this.notification.add("Category name is required.", { type: "danger" });
            return;
        }
        const vals = {
            name: this.state.newCatForm.name,
            warranty_period: parseInt(this.state.newCatForm.warranty_period),
            maintenance_interval: parseInt(this.state.newCatForm.maintenance_interval)
        };
        await this.orm.create("assetflow.category", [vals]);
        this.state.showModal = null;
        this.state.newCatForm = { name: "", warranty_period: 12, maintenance_interval: 6 };
        await this.loadAllData();
        this.notification.add("Category added successfully!", { type: "success" });
    }

    // Screen 4: Assets directory
    getFilteredAssets() {
        const currentUserId = this.state.currentUserId;
        const currentUserRole = this.state.currentUserRole;
        const currentUser = this.state.employees.find(e => e.id === currentUserId);
        const userDeptId = currentUser && currentUser.department_id ? currentUser.department_id[0] : null;

        return this.state.assets.filter(asset => {
            // Role-based visibility logic
            if (currentUserRole !== 'admin' && currentUserRole !== 'manager') {
                const isBookable = asset.is_bookable;
                
                let isAllocatedToMe = false;
                const activeAlloc = this.state.allocations.find(alloc => 
                    alloc.asset_id[0] === asset.id && 
                    alloc.state === 'active' && 
                    alloc.employee_id[0] === currentUserId
                );
                if (activeAlloc) isAllocatedToMe = true;

                let isDeptAsset = false;
                if (currentUserRole === 'dept_head' && userDeptId && asset.department_id && asset.department_id[0] === userDeptId) {
                    isDeptAsset = true;
                }

                if (!isBookable && !isAllocatedToMe && !isDeptAsset) {
                    return false;
                }
            }

            const matchesSearch = !this.state.searchQuery || 
                asset.name.toLowerCase().includes(this.state.searchQuery.toLowerCase()) ||
                (asset.tag && asset.tag.toLowerCase().includes(this.state.searchQuery.toLowerCase())) ||
                (asset.serial_no && asset.serial_no.toLowerCase().includes(this.state.searchQuery.toLowerCase()));
            
            const matchesCategory = !this.state.filterCategory || asset.category_id[0] === parseInt(this.state.filterCategory);
            const matchesStatus = !this.state.filterStatus || asset.state === this.state.filterStatus;
            const matchesDept = !this.state.filterDepartment || asset.department_id[0] === parseInt(this.state.filterDepartment);

            return matchesSearch && matchesCategory && matchesStatus && matchesDept;
        });
    }

    async submitRegisterAsset() {
        if (this.state.currentUserRole === 'employee') {
            this.notification.add("Manager or Admin status required to register assets.", { type: "danger" });
            return;
        }
        if (!this.state.newAssetForm.name || !this.state.newAssetForm.category_id) {
            this.notification.add("Asset Name and Category are required.", { type: "danger" });
            return;
        }
        const vals = {
            name: this.state.newAssetForm.name,
            category_id: parseInt(this.state.newAssetForm.category_id),
            serial_no: this.state.newAssetForm.serial_no,
            acquisition_date: this.state.newAssetForm.acquisition_date,
            acquisition_cost: parseFloat(this.state.newAssetForm.acquisition_cost),
            condition: this.state.newAssetForm.condition,
            location: this.state.newAssetForm.location,
            is_bookable: this.state.newAssetForm.is_bookable
        };
        if (this.state.newAssetForm.department_id) {
            vals.department_id = parseInt(this.state.newAssetForm.department_id);
        }

        await this.orm.create("assetflow.asset", [vals]);
        this.state.showModal = null;
        this.state.newAssetForm = {
            name: "",
            category_id: "",
            serial_no: "",
            acquisition_date: new Date().toISOString().split("T")[0],
            acquisition_cost: 100,
            condition: "good",
            location: "",
            is_bookable: false,
            department_id: ""
        };
        await this.loadAllData();
        this.notification.add("Asset registered successfully!", { type: "success" });
    }

    // Screen 5: Allocation & Double-allocation checks
    async handleAssetSelect(assetId) {
        this.state.selectedAssetId = assetId;
        if (!assetId) {
            this.state.selectedAsset = null;
            this.state.assetHistory = [];
            return;
        }

        const idNum = parseInt(assetId);
        this.state.selectedAsset = this.state.assets.find(a => a.id === idNum);

        // Fetch asset history (previous allocations)
        this.state.assetHistory = this.state.allocations.filter(alloc => alloc.asset_id[0] === idNum);

        // Populate From Employee if it's already allocated
        if (this.state.selectedAsset && this.state.selectedAsset.state === 'allocated') {
            const activeAlloc = this.state.allocations.find(a => a.asset_id[0] === idNum && a.state === 'active');
            if (activeAlloc) {
                this.state.transferForm.from_employee_name = activeAlloc.employee_id[1];
                this.state.transferForm.from_employee_id = activeAlloc.employee_id[0];
            } else {
                this.state.transferForm.from_employee_name = "N/A";
                this.state.transferForm.from_employee_id = "";
            }
        }
    }

    async submitTransferRequest() {
        if (!this.state.selectedAssetId || !this.state.transferForm.to_employee_id) {
            this.notification.add("Please select an Asset and a Target Employee.", { type: "danger" });
            return;
        }
        const vals = {
            asset_id: parseInt(this.state.selectedAssetId),
            to_employee_id: parseInt(this.state.transferForm.to_employee_id),
            reason: this.state.transferForm.reason
        };

        await this.orm.create("assetflow.transfer.request", [vals]);
        this.state.transferForm = { to_employee_id: "", reason: "" };
        this.state.selectedAssetId = "";
        this.state.selectedAsset = null;
        this.state.assetHistory = [];
        await this.loadAllData();
        this.notification.add("Transfer request submitted successfully!", { type: "success" });
    }

    // Screen 6: Resource Bookings
    getBookableResources() {
        return this.state.assets.filter(a => a.is_bookable);
    }

    getBookingsForResource() {
        if (!this.state.bookingResource) return [];
        const resId = parseInt(this.state.bookingResource);
        const selDate = this.state.bookingDate; // format: 'YYYY-MM-DD'
        
        return this.state.bookings.filter(b => {
            if (b.resource_id[0] !== resId || b.state === 'cancelled') return false;
            
            // Check if start_datetime contains the selected date string
            // Odoo returns UTC times e.g. "2026-07-12 04:00:00"
            const bDate = b.start_datetime.split(" ")[0];
            return bDate === selDate;
        }).map(b => {
            // Convert to human hours
            const startHour = b.start_datetime.split(" ")[1].substring(0, 5);
            const endHour = b.end_datetime.split(" ")[1].substring(0, 5);
            return {
                id: b.id,
                employee: b.employee_id[1],
                start: startHour,
                end: endHour,
                label: `Booked - ${b.employee_id[1]} - ${startHour} to ${endHour}`
            };
        });
    }

    async submitBooking() {
        if (!this.state.bookingResource || !this.state.bookingForm.employee_id || !this.state.bookingForm.start_time || !this.state.bookingForm.end_time) {
            this.notification.add("Please fill in all booking fields.", { type: "danger" });
            return;
        }

        const startStr = `${this.state.bookingDate} ${this.state.bookingForm.start_time}:00`;
        const endStr = `${this.state.bookingDate} ${this.state.bookingForm.end_time}:00`;

        if (this.state.bookingForm.end_time <= this.state.bookingForm.start_time) {
            this.notification.add("End time must be after start time.", { type: "danger" });
            return;
        }

        // Local overlap validation
        const existing = this.getBookingsForResource();
        const hasConflict = existing.some(b => {
            return (this.state.bookingForm.start_time < b.end && this.state.bookingForm.end_time > b.start);
        });

        if (hasConflict) {
            this.notification.add("Conflict detected — this time slot is already booked!", { type: "danger" });
            return;
        }

        try {
            await this.orm.create("assetflow.booking", [{
                resource_id: parseInt(this.state.bookingResource),
                employee_id: parseInt(this.state.bookingForm.employee_id),
                start_datetime: startStr,
                end_datetime: endStr,
                state: 'upcoming'
            }]);

            this.state.showModal = null;
            this.state.bookingForm.employee_id = "";
            await this.loadAllData();
            this.notification.add("Slot booked successfully!", { type: "success" });
        } catch (err) {
            this.notification.add(err.message || "Failed to book slot.", { type: "danger" });
        }
    }

    // Screen 7: Maintenance Kanban Workflow
    getTicketsByState(stateName) {
        const currentUserId = this.state.currentUserId;
        const currentUserRole = this.state.currentUserRole;
        const currentUser = this.state.employees.find(e => e.id === currentUserId);
        const userDeptId = currentUser && currentUser.department_id ? currentUser.department_id[0] : null;

        return this.state.maintenanceTickets.filter(t => {
            if (t.state !== stateName) return false;
            
            if (currentUserRole !== 'admin' && currentUserRole !== 'manager') {
                const isCreator = t.create_uid && t.create_uid[0] === currentUserId;
                const isTech = t.technician_id && t.technician_id[0] === currentUserId;
                
                let isDeptMaint = false;
                if (currentUserRole === 'dept_head' && userDeptId) {
                    const asset = this.state.assets.find(a => a.id === t.asset_id[0]);
                    if (asset && asset.department_id && asset.department_id[0] === userDeptId) {
                        isDeptMaint = true;
                    }
                }

                if (!isCreator && !isTech && !isDeptMaint) {
                    return false;
                }
            }
            return true;
        });
    }

    async advanceTicket(ticketId, currentState) {
        if (currentState === 'pending' || currentState === 'approved') {
            if (this.state.currentUserRole !== 'admin' && this.state.currentUserRole !== 'manager') {
                this.notification.add("Manager or Admin status required to approve or assign maintenance requests.", { type: "danger" });
                return;
            }
        }
        if (currentState === 'pending') {
            await this.orm.call("assetflow.maintenance", "action_approve", [ticketId]);
            this.notification.add("Maintenance request approved — Asset marked under maintenance.", { type: "success" });
        } else if (currentState === 'approved') {
            const adminUser = this.state.employees.find(e => e.role === 'admin' || e.role === 'manager') || this.state.employees[0];
            await this.orm.write("assetflow.maintenance", [ticketId], { 
                state: 'assigned',
                technician_id: adminUser ? adminUser.id : false
            });
            this.notification.add(`Technician assigned.`, { type: "success" });
        } else if (currentState === 'assigned') {
            await this.orm.call("assetflow.maintenance", "action_start", [ticketId]);
            this.notification.add("Maintenance work started.", { type: "success" });
        } else if (currentState === 'in_progress') {
            await this.orm.call("assetflow.maintenance", "action_resolve", [ticketId]);
            this.notification.add("Maintenance resolved — Asset returned to available status.", { type: "success" });
        }
        await this.loadAllData();
    }

    async rejectTicket(ticketId) {
        if (this.state.currentUserRole === 'employee') {
            this.notification.add("Department Head, Manager, or Admin status required to reject tickets.", { type: "danger" });
            return;
        }
        await this.orm.call("assetflow.maintenance", "action_reject", [ticketId]);
        this.notification.add("Maintenance request rejected.", { type: "warning" });
        await this.loadAllData();
    }

    async submitMaintenanceRequest() {
        const assetSelect = document.getElementById("maint_asset_select");
        const issueText = document.getElementById("maint_issue_textarea");
        const prioSelect = document.getElementById("maint_prio_select");

        if (!assetSelect || !assetSelect.value || !issueText || !issueText.value) {
            this.notification.add("Please select an asset and write an issue description.", { type: "danger" });
            return;
        }

        await this.orm.create("assetflow.maintenance", [{
            asset_id: parseInt(assetSelect.value),
            issue: issueText.value,
            priority: prioSelect ? prioSelect.value : 'medium',
            state: 'pending'
        }]);

        this.state.showModal = null;
        await this.loadAllData();
        this.notification.add("Maintenance request raised successfully!", { type: "success" });
    }

    // Screen 8: Auditing
    async handleAuditSelect(cycleId) {
        this.state.selectedAuditCycleId = cycleId;
        await this.loadAuditLines(cycleId);
    }

    async verifyAuditLine(lineId, resultType) {
        if (this.state.currentUserRole === 'employee') {
            this.notification.add("Manager or Admin privileges required to audit assets.", { type: "danger" });
            return;
        }
        // resultType: 'verified' | 'missing' | 'damaged'
        let method = "action_set_verified";
        if (resultType === 'missing') method = "action_set_missing";
        else if (resultType === 'damaged') method = "action_set_damaged";

        await this.orm.call("assetflow.audit.line", method, [lineId]);
        await this.loadAllData();
        this.notification.add(`Audit line updated to ${resultType}.`, { type: "success" });
    }

    async closeAuditCycle() {
        if (this.state.currentUserRole !== 'admin' && this.state.currentUserRole !== 'manager') {
            this.notification.add("Manager or Admin privileges required to close audit cycle.", { type: "danger" });
            return;
        }
        if (!this.state.selectedAuditCycleId) return;
        await this.orm.call("assetflow.audit.cycle", "action_close", [parseInt(this.state.selectedAuditCycleId)]);
        await this.loadAllData();
        this.notification.add("Audit cycle closed successfully. Missing items marked as lost.", { type: "success" });
    }

    // Screen 9: Reports aggregates
    getDepartmentChartData() {
        // Group assets by department and return coordinate lists for SVG bars
        const counts = {};
        this.state.assets.forEach(a => {
            const deptName = a.department_id ? a.department_id[1] : "Unassigned";
            counts[deptName] = (counts[deptName] || 0) + 1;
        });

        const keys = Object.keys(counts);
        const maxVal = Math.max(...Object.values(counts), 5);
        
        return keys.map((key, i) => {
            const height = (counts[key] / maxVal) * 120; // max SVG height 120
            return {
                label: key.substring(0, 10),
                value: counts[key],
                x: 40 + i * 70,
                y: 140 - height,
                height: height
            };
        });
    }

    getCategoryChartData() {
        const counts = {};
        this.state.assets.forEach(a => {
            const catName = a.category_id ? a.category_id[1] : "Other";
            counts[catName] = (counts[catName] || 0) + 1;
        });
        
        const keys = Object.keys(counts);
        const maxVal = Math.max(...Object.values(counts), 5);

        // Draw coordinate string for SVG polyline
        let points = "";
        const pointsList = keys.map((key, i) => {
            const x = 50 + i * 80;
            const y = 140 - (counts[key] / maxVal) * 100;
            points += `${x},${y} `;
            return { label: key.substring(0, 10), value: counts[key], x, y };
        });

        return { points, pointsList };
    }

    exportReport() {
        this.notification.add("Exporting report... Download will begin shortly.", { type: "success" });
    }

    // Screen 10: Activity logs
    getFilteredActivities() {
        const filter = this.state.logFilter;
        return this.state.dashboardData.activities.filter(act => {
            if (filter === 'all') return true;
            if (filter === 'alerts') return act.model_name === 'assetflow.allocation' && act.body.includes("overdue");
            if (filter === 'approvals') return act.model_name === 'assetflow.maintenance' || act.model_name === 'assetflow.transfer.request';
            if (filter === 'bookings') return act.model_name === 'assetflow.booking';
            return true;
        });
    }
}

AssetFlowDashboard.template = "assetflow.Dashboard";
registry.category("actions").add("assetflow_dashboard", AssetFlowDashboard);
