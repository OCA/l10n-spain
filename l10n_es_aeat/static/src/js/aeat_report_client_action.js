odoo.define('l10n_es_aeat.aeat_report_client_action', function (require) {
'use strict';

var core = require('web.core');
var Widget = require('web.Widget');
var ControlPanelMixin = require('web.ControlPanelMixin');
var session = require('web.session');
var ReportWidget = require('l10n_es_aeat.aeat_report_widget');
var framework = require('web.framework');
var crash_manager = require('web.crash_manager');
var QWeb = core.qweb;

var report_client_action = Widget.extend(ControlPanelMixin, {
    // Stores all the parameters of the action.
    init: function(parent, action) {
        this.actionManager = parent;
        this.given_context = {};
        this.odoo_context = action.context;
        this.controller_url = action.context.url;
        if (action.context.context) {
            this.given_context = action.context.context;
        }
        this.given_context.active_id = action.context.active_id || action.params.active_id;
        this.given_context.model = action.context.active_model || false;
        this.given_context.ttype = action.context.ttype || false;
        this.given_context.template_name = action.params.template_name;
        return this._super.apply(this, arguments);
    },

    willStart: function() {
        return this.get_html();
    },

    set_html: function() {
        var self = this;
        var def = $.when();
        if (!this.report_widget) {
            this.report_widget = new ReportWidget(this, this.given_context);
            def = this.report_widget.appendTo(this.$el);
        }
        def.then(function () {
            self.report_widget.$el.html(self.html);
        });
    },

    start: function() {
        this.set_html();
        return this._super();
    },
    // Fetches the html and is previous report.context if any, else create it
    get_html: function() {
        var self = this;
        var defs = [];
        return this._rpc({
            model: this.given_context.model,
            method: 'get_html',
            context: this.given_context,
            })
            .then(function(result){
                self.html = result.html;
                defs.push(self.update_cp());
                return $.when.apply($, defs);
        });
    },
    // Updates the control panel and render the elements that have yet to be rendered
    update_cp: function() {
        var status = {
            breadcrumbs: this.actionManager.get_breadcrumbs(),
            cp_content: {$buttons: this.$buttons},
        };
        return this.update_control_panel(status);
    },
    do_show: function() {
        this._super();
        this.update_cp();
    },
});

core.action_registry.add("aeat_report_client_action", report_client_action);
return report_client_action;
});
