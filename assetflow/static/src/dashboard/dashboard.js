/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, useState } from "@odoo/owl";

export class AssetFlowDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.state = useState({
            data: {
                kpis: {
                    available_assets: 0,
                    allocated_assets: 0,
                    bookable_resources: 0,
                    active_bookings: 0,
                    pending_transfers: 0,
                    upcoming_returns: 0
                },
                overdue: {
                    count: 0,
                    list: []
                },
                activities: []
            }
        });

        onWillStart(async () => {
            await this.loadDashboardData();
        });
    }

    async loadDashboardData() {
        try {
            const data = await this.orm.call("assetflow.asset", "get_dashboard_data", []);
            if (data) {
                this.state.data = data;
            }
        } catch (error) {
            console.error("Failed to load dashboard data:", error);
        }
    }

    // Quick Actions
    registerAsset() {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Register Asset",
            res_model: "assetflow.asset",
            views: [[false, "form"]],
            target: "new"
        });
    }

    bookResource() {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Book Resource",
            res_model: "assetflow.booking",
            views: [[false, "form"]],
            target: "new"
        });
    }

    raiseMaintenance() {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Raise Maintenance Request",
            res_model: "assetflow.maintenance",
            views: [[false, "form"]],
            target: "new"
        });
    }

    // Navigation and Filtering
    filterAssets(filterType) {
        let domain = [];
        if (filterType === 'available') {
            domain = [['state', '=', 'available']];
        } else if (filterType === 'allocated') {
            domain = [['state', '=', 'allocated']];
        } else if (filterType === 'bookable') {
            domain = [['is_bookable', '=', true], ['state', '=', 'available']];
        }
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Assets",
            res_model: "assetflow.asset",
            views: [[false, "list"], [false, "form"]],
            domain: domain,
            target: "current"
        });
    }

    viewBookings() {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Active Bookings",
            res_model: "assetflow.booking",
            views: [[false, "list"], [false, "form"]],
            domain: [['state', 'in', ['upcoming', 'ongoing']]],
            target: "current"
        });
    }

    viewTransfers() {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Pending Transfers",
            res_model: "assetflow.transfer.request",
            views: [[false, "list"], [false, "form"]],
            domain: [['state', '=', 'requested']],
            target: "current"
        });
    }

    viewUpcomingReturns() {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Upcoming Returns",
            res_model: "assetflow.allocation",
            views: [[false, "list"], [false, "form"]],
            domain: [['state', '=', 'active']],
            target: "current"
        });
    }

    viewOverdue() {
        const todayStr = new Date().toISOString().split('T')[0];
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Overdue Allocations",
            res_model: "assetflow.allocation",
            views: [[false, "list"], [false, "form"]],
            domain: [['state', '=', 'active'], ['expected_return_date', '<', todayStr]],
            target: "current"
        });
    }
}

AssetFlowDashboard.template = "assetflow.Dashboard";
registry.category("actions").add("assetflow_dashboard", AssetFlowDashboard);
