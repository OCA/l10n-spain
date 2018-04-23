odoo.define('l10n_es_aeat.aeat_report_widget', function
(require) {
'use strict';

var core = require('web.core');
var Widget = require('web.Widget');

var QWeb = core.qweb;

var _t = core._t;

var aeatReportWidget = Widget.extend({
    events: {
        'click .o_aeat_reports_web_action': 'boundLink',
    },
    init: function(parent) {
        this._super.apply(this, arguments);
    },
    start: function() {
        return this._super.apply(this, arguments);
    },
    boundLink: function(e) {
        var res_model = $(e.currentTarget).data('res-model');
        var res_id = $(e.currentTarget).data('active-id');
        return this.do_action({
            type: 'ir.actions.act_window',
            res_model: res_model,
            res_id: res_id,
            views: [[false, 'form']],
            target: 'current'
        });
    },
});

return aeatReportWidget;

});
