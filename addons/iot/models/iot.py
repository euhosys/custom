import base64

from odoo import api, fields, models, exceptions
from odoo.models import AbstractModel

# ----------------------------------------------------------
# Models for client
# ----------------------------------------------------------
class IotBox(models.Model):
    _name = 'iot.box'
    _description = 'IoT Box'

    name = fields.Char('Name', readonly=True)
    identifier = fields.Char(string='Identifier (Mac Address)', readonly=True)
    device_ids = fields.One2many('iot.device', 'iot_id', string="Devices", readonly=True)
    ip = fields.Char('IP Address', readonly=True)
    ip_url = fields.Char('IoT Box Home Page', readonly=True, compute='_compute_ip_url')
    screen_url = fields.Char('Screen URL', help="Url of the page that will be displayed by hdmi port of the box.")

    def _compute_ip_url(self):
        for box in self:
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            if base_url[:5] == 'https':
                box.ip_url = 'https://' + box.ip
            else:
                box.ip_url = 'http://' + box.ip + ':8069'


class IotTrigger(models.Model):
    _name = 'iot.trigger'
    _description = 'IOT Trigger'
    _order = 'sequence'

    sequence = fields.Integer(default=1)
    device_id = fields.Many2one('iot.device', 'Device', required=True)
    key = fields.Char('Key')
    action = fields.Selection([('pass', 'Pass'),
                               ('fail', 'Fail'),
                               ('measure', 'Take Measure'),
                               ('picture', 'Take Picture'),
                               ('skip', 'Skip'),
                               ('pause', 'Pause'),
                               ('prev', 'Previous'),
                               ('next', 'Next'),
                               ('validate', 'Validate'),
                               ('cloMO', 'Close MO'),
                               ('cloWO', 'Close WO'),
                               ('finish', 'Finish'),
                               ('record', 'Record Production'),
                               ('cancel', 'Cancel'),
                               ('print-op', 'Print Operation'),
                               ('print-slip', 'Print Delivery Slip'),
                               ('print', 'Print Labels'),
                               ('pack', 'Pack'),
                               ('scrap', 'Scrap'),])


class IotDevice(models.Model):
    _name = 'iot.device'
    _description = 'IOT Device'

    iot_id = fields.Many2one('iot.box', string='IoT Box', required = True)
    name = fields.Char('Name')
    identifier = fields.Char(string='Identifier', readonly=True)
    type = fields.Selection([
        ('printer', 'Printer'),
        ('camera', 'Camera'),
        ('device', 'Device'),
        ], readonly=True, default='device', string='Type',
        help="Type of device.")
    connection = fields.Selection([
        ('network', 'Network'),
        ('direct', 'USB'),
        ('bluetooth', 'Bluetooth')
        ], readonly=True, string="Connection",
        help="Type of connection.")
    report_ids = fields.One2many('ir.actions.report', 'device_id', string='Reports')

    def name_get(self):
        return [(i.id, "[" + i.iot_id.name +"] " + i.name) for i in self]


class IrActionReport(models.Model):
    _inherit = 'ir.actions.report'

    device_id = fields.Many2one('iot.device', string='IoT Device', domain="[('type', '=', 'printer')]",
                                help='When setting a device here, the report will be printed through this device on the IoT Box')

    def iot_render(self, res_ids, data=None):
        if self.mapped('device_id'):
            device = self.mapped('device_id')[0]
        else:
            device = self.env['iot.device'].browse(data['device_id'])
        composite_url = device.iot_id.ip_url + "/hw_drivers/driveraction/" + device.identifier
        datas = self.render(res_ids, data=data)
        type = datas[1]
        data_bytes = datas[0]
        data_base64 = base64.b64encode(data_bytes)
        return composite_url, type, data_base64

class PublisherWarrantyContract(models.AbstractModel):
    _inherit = "publisher_warranty.contract"
    _description = 'Publisher Warranty Contract For IoT Box'

    @api.model
    def _get_message(self):
        msg = super(PublisherWarrantyContract, self)._get_message()
        msg['IoTBox'] = self.env['iot.box'].search_count([])
        return msg