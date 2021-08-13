# Copyright 2021 Studio73 - Ethan Hildick <ethan@studio73.es>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
import logging
import os

from odoo import _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

try:
    from suds.client import Client
    from suds.sax.text import Raw
    from suds.sudsobject import asdict
except (ImportError, IOError) as err:
    _logger.debug(err)


DBSCHENKER_REQUEST_TYPES = [
    ("Land", "Land"),
    ("Air", "Air"),
    ("OceanFCL", "Ocean FCL"),
    ("OceanLCL", "Ocean LCL"),
]

DBSCHENKER_PRODUCT_CODES = [
    # Air
    ("f", "DB SCHENKER jetcargo first"),
    ("s", "DB SCHENKER jetcargo special"),
    ("b", "DB SCHENKER jetcargo business"),
    ("e", "DB SCHENKER jetcargo economy"),
    ("eagd", "DB SCHENKER jetexpress gold"),
    ("easv", "DB SCHENKER jetexpress silver"),
    # Ocean
    ("fcl", "DB SCHENKER complete - FCL"),
    ("lcl", "DB SCHENKER combine - LCL"),
    # Land
    ("CON", "DB Schenker concepts"),
    ("DIR", "DB Schenker directs"),
    ("LPA", "DB Schenker parcel Logistics Parcel"),
    ("PAL", "DB Schenker pallets"),
    ("auc0", "Austro express PUNKT 10"),
    ("auc2", "Austro express PUNKT 12"),
    ("auc8", "Austro express PUNKT 8"),
    ("aucc", "Austro express PUNKT 17"),
    ("auco", "Austro cargo"),
    ("escp", "DB SCHENKER system-plus"),
    ("ect1", "DB SCHENKER speed 10"),
    ("ect2", "DB SCHENKER speed 12"),
    ("sch2", "DB SCHENKER top 12"),
    ("schs", "DB SCHENKER system international"),
    ("sysd", "DB SCHENKER system domestic"),
    ("scht", "DB SCHENKER top"),
    ("schx", "DB SCHENKER system fix"),
    ("ecpa", "DB SCHENKER parcel"),
    ("ect8", "DB SCHENKER speed 8"),
    ("ectn", "DB SCHENKER speed"),
    ("40", "DB SCHENKER system classic"),
    ("41", "DB SCHENKER system speed"),
    ("42", "DB SCHENKER system fixday"),
    ("43", "DB Schenker System"),
    ("44", "DB Schenker System Premium"),
    ("71", "DB SCHENKER direct"),
]

DBSCHENKER_SERVICE_TYPES = [
    ("D2D", "Door-to-Door"),
    ("D2P", "Door-to-Port"),
    ("P2D", "Port-to-Door"),
    ("D2A", "Door-to-Airport"),
    ("A2D", "Airport-to-Door"),
    ("A2A", "Airport-to-Airport"),
]

# LAND
DBSCHENKER_MEASURE_UNIT = [
    ("VOLUME", "VOLUME"),
    ("LOADING_METERS", "LOADING_METERS"),
    ("PIECES", "PIECES"),
    ("PALLET_SPACE", "PALLET_SPACE"),
]

# SHIPPING (LAND, AIR, OCEANLCL)
DBSCHENKER_PACKAGE_TYPE = [
    ("CI", "Canister(s)"),
    ("CT", "Carton(s)"),
    ("CS", "Case(s)"),
    ("CO", "Colli(s)"),
    ("CH", "Crate(s)"),
    ("GP", "Skeleton box pallet(s)"),
    ("NE", "Unpacked Skid(s)"),
    ("BG", "Bag(s)"),
    ("BL", "Bale(s)"),
    ("DR", "Barrel(s)"),
    ("BX", "Box(es)"),
    ("BY", "Bundle(s)"),
    ("TR", "Drum(s)"),
    ("EP", "Europallet(s)"),
    ("FR", "Frame(s)"),
    ("HO", "Hobbock(s)"),
    ("OP", "One-way pallet(s)"),
    ("PK", "Package(s)"),
    ("XP", "Pallet(s)"),
    ("PZ", "Pipe(s)"),
    ("RO", "Roll(s)"),
    ("SK", "Sack(s)"),
    ("ZZ", "Other(s)"),
]

# OCEAN
DBSCHENKER_CONTAINER_TYPE = [
    ("22BU", "20' BB (Bulk Container)"),
    ("22UP", "20' HT (Hard Top)"),
    ("20G2", "20' OS (Open Sided Container)"),
    ("22UT", "20' OT (Open Top Container)"),
    ("22PC", "20' PL (Platform Container)"),
    ("22RE", "20' RE (Reefer Container)"),
    ("22GP", "20' DC (Standard /Dry Container)"),
    ("22TN", "20' TC (Tank Container)"),
    ("42BU", "40' BB (Bulk Container)"),
    ("42P1", "40' FR (Flat Rack Container)"),
    ("42UP", "40' HT (Hard Top)"),
    ("45GP", "40' HQ (High-Cube Standard / Dry Container)"),
    ("42PS", "40' OS (Open Sided Container)"),
    ("42UT", "40' OT (Open Top Container)"),
    ("42PL", "40' PL (Platform Container)"),
    ("42RE", "40' RE (Reefer Container)"),
    ("42GP", "40' DC (Standard /Dry Container)"),
    ("42TN", "40' TC (Tank Container)"),
    ("LEG0", "45' HW (High Cube Palletwide)"),
    ("L5RE", "45' HR (Reefer High Cube Container)"),
    ("P6GP", "45' DC (Standard /Dry Container, High Cube)"),
    ("22DC", "20' GH (Garments on Hanger)"),
    ("25GP", "20' HQ (High Cube Container)"),
    ("22VH", "20' VC (Ventilated Container)"),
    ("40DC", "40' GH (Garmentson Hanger)"),
    ("45BK", "40' HB (Bulk High Cube Container)"),
    ("45PC", "40' HF (Flat Rack High Cube Container)"),
    ("45UT", "40' HO (Open Top High Cube Container)"),
    ("45RE", "40' HR (Reefer High Cube Container)"),
    ("4EG0", "40' HW (High CubePalletwide)"),
    ("49PL", "40' MA (Mafi Trailer)"),
    ("42VH", "40' VC (Ventilated Container)"),
    ("L5VH", "45' HV (Ventilated High Cube Container)"),
    ("P6GP", "53' DC (Standard /Dry Container)"),
    ("22P1", "20' FR (Flat Rack Container)"),
]

DBSCHENKER_POSITIONING_TYPE = [
    ("CONTAINER_POS_BY_CUSTOMER", "CONTAINER_POS_BY_CUSTOMER"),
    ("CONTAINER_POS_BY_SCHENKER", "CONTAINER_POS_BY_SCHENKER"),
]

# AIR + OCEANLCL

DBSCHENKER_PRECARRIAGE_TYPE = [
    ("PICKUP_REQUEST", "PICKUP_REQUEST"),
    ("OWN_DELIVERY", "OWN_DELIVERY"),
]

DBSCHENKER_CONSIGNEE_DATE_TYPE = [
    ("LATEST", "Latest"),
    ("EARLIEST", "Earliest"),
    ("TIME", "Specific time"),
]


class DBSchenkerRequest(object):
    """Interface between DB Schenker API and Odoo recordset
    Abstract DB Schenker API Operations to connect them with Odoo
    """

    def __init__(self, carrier):
        self.endpoint = (
            "https://eschenker.dbschenker.com/webservice/bookingWebServiceV1_1"
            if carrier.prod_environment
            else "https://eschenker-fat.dbschenker.com/webservice/bookingWebServiceV1_1"
        )
        self.carrier = carrier
        wsdl_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            (
                "../api/bookingWebServiceV1_1_PROD.wsdl"
                if carrier.prod_environment
                else "../api/bookingWebServiceV1_1.wsdl"
            ),
        )
        self.client = Client("file:{}".format(wsdl_path))

    def _recursive_asdict(self, suds_object):
        """As suds response is an special object, we convert it into
        a more usable python dict. Taken form:
        https://stackoverflow.com/a/15678861
        """
        out = {}
        for k, v in asdict(suds_object).items():
            if hasattr(v, "__keylist__"):
                out[k] = self._recursive_asdict(v)
            elif isinstance(v, list):
                out[k] = []
                for item in v:
                    if hasattr(item, "__keylist__"):
                        out[k].append(self._recursive_asdict(item))
                    else:
                        out[k].append(item)
            else:
                out[k] = v
        return out

    def _prepare_addresses(self, addresses):
        """Creates XML for addresses
        Each booking should have at least 2 addresses, with types: SHIPPER and CONSIGNEE
        :param addresses - List of Dict
            [{...},{...}]
        :returns string
        """
        xml = ""
        for address in addresses:
            xml += """
                <address>
                    {name1_xml}
                    {name2_xml}
                    {cust_address_xml}
                    {email_xml}
                    {fax_xml}
                    {industry_xml}
                    {location_xml}
                    {mobile_xml}
                    {person_type_xml}
                    {phone_xml}
                    {po_box_xml}
                    {postal_code_xml}
                    {state_code_xml}
                    {lang_xml}
                    {street_xml}
                    {street2_xml}
                    {city_xml}
                    {country_xml}
                    {type_xml}
                </address>
            """
            address.update(
                {
                    "name1_xml": "<name1>{name}</name1>".format(
                        name=address.get("name")
                    ),
                    "name2_xml": (
                        "<name2>{name2}</name2>".format(name2=address.get("name2"))
                        if address.get("name2", False)
                        else ""
                    ),
                    "cust_address_xml": (
                        """
                        <customerAddressIdentifier>{addr}</customerAddressIdentifier>
                        """.format(
                            addr=address.get("cust_address")
                        )
                        if address.get("cust_address", False)
                        else ""
                    ),
                    "email_xml": "<email>{email}</email>".format(
                        email=address.get("email").split(";")[0]
                        if address.get("email", False)
                        else ""
                    ),
                    "fax_xml": (
                        "<fax>{fax}</fax>".format(fax=address.get("fax"))
                        if address.get("fax", False)
                        else ""
                    ),
                    "industry_xml": (
                        "<industry>{industry}</industry>".format(
                            industry=address.get("industry")
                        )
                        if address.get("industry", False)
                        else ""
                    ),
                    "mobile_xml": (
                        "<mobilePhone>{mobile}</mobilePhone>".format(
                            mobile=address.get("mobile")
                        )
                        if address.get("mobile", False)
                        else ""
                    ),
                    "po_box_xml": (
                        "<poBox>{po_box}</poBox>".format(po_box=address.get("po_box"))
                        if address.get("po_box", False)
                        else ""
                    ),
                    "phone_xml": (
                        "<phone>{phone}</phone>".format(phone=address.get("phone"))
                        if address.get("phone", False)
                        else ""
                    ),
                    "state_code_xml": (
                        "<stateCode>{state_code}</stateCode>".format(
                            state_code=address.get("state_code")
                        )
                        if address.get("state_code", False)
                        else ""
                    ),
                    "street2_xml": (
                        "<street2>{street2}</street2>".format(
                            street2=address.get("street2")
                        )
                        if address.get("street2", False)
                        else ""
                    ),
                    "location_xml": "<locationType>{location}</locationType>".format(
                        location=address.get("location")
                    ),
                    "person_type_xml": "<personType>{person_type}</personType>".format(
                        person_type=address.get("person_type")
                    ),
                    "postal_code_xml": "<postalCode>{postal_code}</postalCode>".format(
                        postal_code=address.get("postal_code")
                    ),
                    "lang_xml": "<preferredLanguage>{lang}</preferredLanguage>".format(
                        lang=address.get("lang")
                    ),
                    "street_xml": "<street>{street}</street>".format(
                        street=address.get("street")
                    ),
                    "city_xml": "<city>{city}</city>".format(city=address.get("city")),
                    "country_xml": "<countryCode>{country}</countryCode>".format(
                        country=address.get("country")
                    ),
                    "type_xml": "<type>{type}</type>".format(type=address.get("type")),
                }
            )
            xml = xml.format(**address)
        return xml

    def _prepare_application_area(self, vals):
        xml = """
                <applicationArea>
                    {access_key_xml}
                    {group_id_xml}
                    {request_id_xml}
                    {user_id_xml}
                    {group_name_xml}
                </applicationArea>
            """
        vals.update(
            {
                "access_key_xml": "<accessKey>{access_key}</accessKey>".format(
                    access_key=vals.get("access_key")
                ),
                "group_id_xml": (
                    "<groupId>{group_id}</groupId>".format(
                        group_id=vals.get("group_id")
                    )
                    if vals.get("group_id")
                    else ""
                ),
                "request_id_xml": (
                    "<requestID>{request_id}</requestID>".format(
                        request_id=vals.get("request_id")
                    )
                    if vals.get("request_id")
                    else ""
                ),
                "user_id_xml": (
                    "<userId>{user_id}</userId>".format(user_id=vals.get("user_id"))
                    if vals.get("user_id")
                    else ""
                ),
                "group_name_xml": (
                    "<groupName>{group_name}</groupName>".format(
                        group_name=vals.get("group_name")
                    )
                    if vals.get("group_name")
                    else ""
                ),
            }
        )
        return xml.format(**vals)

    def _prepare_pickup_dates(self, dates):
        """Creates XML for pickupDates
        :param dates - List of Dict with date_from and date_to keys
            [{"date_from": "2015-08-30T09:30:10-06:00", "date_to": ...}]
            Dates must be in this format, timezone included
        :returns string
        """
        return "".join(
            """
            <pickupDates>
                <pickUpDateFrom>{date_from}</pickUpDateFrom>
                <pickUpDateTo>{date_to}</pickUpDateTo>
            </pickupDates>
            """.format(
                date_from=date["date_from"], date_to=date["date_to"]
            )
            for date in dates
        )

    def _prepare_references(self, references):
        """Creates XML for reference
        :param references - List of Dict with number and id keys
            [{"number": "", "id": "SHIPPER_REFERENCE_NUMBER"}]
            ID must be one of the valid types
        :returns string
        """
        return "".join(
            """
            <reference>
                <number>{number}</number>
                <id>{id}</id>
            </reference>
            """.format(
                number=reference["number"], id=reference["id"]
            )
            for reference in references
        )

    def _prepare_shipment_position(self, vals):
        """Creates XML for land bookings
        :param vals - Dict with keys
            {
                "dgr": "false",               # Mandatory
                "cargo_description": "",      # Mandatory
                "shipping_volume": "",        # Mandatory
                "shipping_gross_weight": "",  # Mandatory
                "shipping_package_type": "",  # Mandatory
                "shipping_pieces": "",        # Mandatory
                "shipping_stackable": "",     # Mandatory
                "shipping_length": "",
                "shipping_width": "",
                "shipping_height": "",
            },
            shipping_package_type must be one of the types in DBSCHENKER_PACKAGE_TYPE
        :returns string
        """
        xml = """
            <shipmentPosition>
                {dgr_xml}
                {cargo_description_xml}
                {shipping_length_xml}
                {shipping_width_xml}
                {shipping_height_xml}
                {shipping_volume_xml}
                {shipping_gross_weight_xml}
                {shipping_package_type_xml}
                {shipping_pieces_xml}
                {shipping_stackable_xml}
            </shipmentPosition>
        """
        vals.update(
            {
                "dgr_xml": "<dgr>{dgr}</dgr>".format(dgr=vals.get("dgr")),
                "cargo_description_xml": (
                    "<cargoDesc>{cargo_description}</cargoDesc>".format(
                        cargo_description=vals.get("cargo_description")
                    )
                ),
                "shipping_volume_xml": "<volume>{shipping_volume}</volume>".format(
                    shipping_volume=vals.get("shipping_volume")
                ),
                "shipping_gross_weight_xml": (
                    "<grossWeight>{shipping_gross_weight}</grossWeight>".format(
                        shipping_gross_weight=vals.get("shipping_gross_weight")
                    )
                ),
                "shipping_package_type_xml": (
                    "<packageType>{shipping_package_type}</packageType>".format(
                        shipping_package_type=vals.get("shipping_package_type")
                    )
                ),
                "shipping_pieces_xml": "<pieces>{shipping_pieces}</pieces>".format(
                    shipping_pieces=vals.get("shipping_pieces")
                ),
                "shipping_stackable_xml": (
                    "<stackable>{shipping_stackable}</stackable>".format(
                        shipping_stackable=vals.get("shipping_stackable")
                    )
                ),
                "shipping_length_xml": (
                    "<length>{shipping_length}</length>".format(
                        shipping_length=vals.get("shipping_length")
                    )
                    if vals.get("shipping_length")
                    else ""
                ),
                "shipping_width_xml": (
                    "<width>{shipping_width}</width>".format(
                        shipping_width=vals.get("shipping_width")
                    )
                    if vals.get("shipping_width")
                    else ""
                ),
                "shipping_height_xml": (
                    "<height>{shipping_height}</height>".format(
                        shipping_height=vals.get("shipping_height")
                    )
                    if vals.get("shipping_height")
                    else ""
                ),
            }
        )
        return xml.format(**vals)

    def _prepare_consignee_date(self, vals):
        """Creates XML for consignee delivery date info
        :param vals - Dict with keys
            {
                "date_type": "",          # Mandatory
                "delivery_date": "",      # Mandatory
                "time_from": "",          # Mandatory if date_type = TIME
                "time_to": "",            # Mandatory if date_type = TIME
            },
            date_type must be one of the types in DBSCHENKER_CONSIGNEE_DATE_TYPE
        :returns string
        """
        if not vals:
            return ""
        xml = """
            <deliveryDateConsignee>
                {delivery_date_xml}
                {date_type_xml}
                {time_from_xml}
                {time_to_xml}
            </deliveryDateConsignee>
        """
        vals.update(
            {
                "date_type_xml": (
                    "<deliveryType>{type}</deliveryType>".format(
                        type=vals.get("date_type")
                    )
                ),
                "delivery_date_xml": (
                    "<deliveryDate>{delivery_date}</deliveryDate>".format(
                        delivery_date=vals.get("delivery_date")
                    )
                ),
                "time_from_xml": (
                    "<timeFrom>{time_from}</timeFrom>".format(
                        time_from=vals.get("time_from")
                    )
                    if vals.get("time_from") and vals.get("date_type") == "TIME"
                    else ""
                ),
                "time_to_xml": (
                    "<timeTo>{time_to}</timeTo>".format(time_to=vals.get("time_to"))
                    if vals.get("time_to") and vals.get("date_type") == "TIME"
                    else ""
                ),
            }
        )
        return xml.format(**vals)

    def _prepare_container(self, vals):
        """Creates XML for land bookings
        :param vals - Dict with keys
            {
                "container_type": "22BU",       # Mandatory
                "container_number": "1234ADSD",
                "positioning_date": "",
                "positioning_address": "",
                "seal_number": "",
            },
            container_type must be one of the types in DBSCHENKER_CONTAINER_TYPE
        :returns string
        """
        xml = """
            <containerType>
                {container_type_xml}
                {container_number_xml}
                {positioning_date_xml}
                {positioning_address_xml}
                {seal_number_xml}
            </containerType>
        """
        vals.update(
            {
                "container_type_xml": (
                    "<containerType>{container_type}</containerType>".format(
                        container_type=vals.get("container_type")
                    )
                ),
                "container_number_xml": (
                    "<containerNo>{container_number}</containerNo>".format(
                        container_number=vals.get("container_number")
                    )
                ),
                "positioning_date_xml": (
                    "<positioningDate>{positioning_date}</positioningDate>".format(
                        positioning_date=vals.get("positioning_date")
                    )
                ),
                "positioning_address_xml": (
                    """<positioningAddress>{positioning_address}</positioningAddress>
                    """.format(
                        positioning_address=vals.get("positioning_address")
                    )
                ),
                "seal_number_xml": (
                    "<sealNumber>{seal_number}</sealNumber>".format(
                        seal_number=vals.get("seal_number")
                    )
                ),
            }
        )
        return xml.format(**vals)

    def _prepare_land_xml(self, vals):
        """Creates XML for land bookings
        :param vals - Dict with keys
            {
                "shipping_position_vals": {},  # Mandatory
                "consignee_date_vals": {},
                "weight": "",                  # Mandatory
                "volume": "",                  # Mandatory
                "express": "",                 # Mandatory
                "food": "",                    # Mandatory
                "heated_transport": "",        # Mandatory
                "home_delivery": "",           # Mandatory
                "measure_unit": "",            # Mandatory
                "measure_value": "",           # Mandatory
                "own_pickup": "",              # Mandatory
                "pharmaceuticals": "",         # Mandatory
            },
            measure_unit must be one of the valid types in DBSCHENKER_MEASURE_UNIT
        :returns string
        """
        unit = vals.get("measure_unit", False)
        if unit == "LOADING_METERS":
            vals.update(
                {
                    "measure_unit_type": (
                        "<measureUnitLoading>{value}</measureUnitLoading>".format(
                            value=vals.get("measure_value", "")
                        )
                    )
                }
            )
        elif unit == "PALLET_SPACE":
            vals.update(
                {
                    "measure_unit_type": (
                        "<measureUnitPalletSpace>{v}</measureUnitPalletSpace>".format(
                            v=vals.get("measure_value", "")
                        )
                    )
                }
            )
        elif unit == "PIECES":
            vals.update(
                {
                    "measure_unit_type": (
                        "<measureUnitPieces>{measure_value}</measureUnitPieces>".format(
                            measure_value=vals.get("measure_value", "")
                        )
                    )
                }
            )
        elif unit == "VOLUME":
            vals.update(
                {
                    "measure_unit_type": (
                        "<measureUnitVolume>{measure_value}</measureUnitVolume>".format(
                            measure_value=vals.get("measure_value", "")
                        )
                    )
                }
            )
        vals.update(
            {
                "shipping_position": self._prepare_shipment_position(
                    vals.get("shipping_position_vals", {})
                ),
                "consignee_date_xml": self._prepare_consignee_date(
                    vals.get("consignee_date_vals", {})
                ),
            }
        )
        return """
            <shippingInformation>
                {shipping_position}
                <grossWeight>{weight}</grossWeight>
                <volume>{volume}</volume>
            </shippingInformation>
            {consignee_date_xml}
            <express>{express}</express>
            <foodRelated>{food}</foodRelated>
            <heatedTransport>{heated_transport}</heatedTransport>
            <homeDelivery>{home_delivery}</homeDelivery>
            <measureUnit>{measure_unit}</measureUnit>
            {measure_unit_type}
            <ownPickup>{own_pickup}</ownPickup>
            <pharmaceuticals>{pharmaceuticals}</pharmaceuticals>
        """.format(
            **vals
        )

    def _prepare_air_xml(self, vals):
        """Creates XML for Air bookings
        :param vals - Dict with keys
            {
                "shipping_position_vals": {},  # Mandatory
                "air_business": "",
                "departure_airport": "",  # Mandatory if A2D/A2A
                "destination_airport": "",  # Mandatory if D2A/A2A
                "precarriage_type": "PICKUP_REQUEST",  # Mandatory
            },
        :returns string
        """
        vals.update(
            {
                "shipping_position": self._prepare_shipment_position(
                    vals.get("shipping_position_vals", {})
                )
            }
        )
        xml = """
            <shippingInformation>
                {shipping_position}
                <grossWeight>{weight}</grossWeight>
                <volume>{volume}</volume>
            </shippingInformation>
            <departureAirport>{departure_airport}</departureAirport>
            <destinationAirport>{destination_airport}</destinationAirport>
            <precarriageType>{precarriage_type}</precarriageType>
        """
        if vals.get("air_business", False):
            xml += "<myAirBusiness>{air_business}</myAirBusiness>"
        return xml.format(**vals)

    def _prepare_oceanfcl_xml(self, vals):
        """Creates XML for Ocean FCL bookings
        :param vals - Dict with keys
            {
                "ocean_business": "",
                "loading_port": "",  # Mandatory if P2D/P2P
                "discharge_port": "",  # Mandatory if D2P/P2P
                "container_vals": {
                    "container_type": "22BU",  # Mandatory
                    "container_number": "1234ADSD",
                    "positioning_date": "",
                    "positioning_address": "",
                    "seal_number": "",
                },
            },
        :returns string
        """
        vals.update(
            {"container": self._prepare_container(vals.get("container_vals", {}))}
        )
        xml = """
            <portLoading>{loading_port}</portLoading>
            <portDischarge>{discharge_port}</portDischarge>
            {container}
        """
        if vals.get("ocean_business", False):
            xml += "<myOceanBusiness>{ocean_business}</myOceanBusiness>"
        return xml.format(**vals)

    def _prepare_oceanlcl_xml(self, vals):
        """Creates XML for Ocean LCL bookings
        :param vals - Dict with keys
            {
                "shipping_position_vals": {},       # Mandatory
                "weight": "",                       # Mandatory
                "volume": "",                       # Mandatory
                "ocean_business": "",
                "loading_port": "",                 # Mandatory if P2D/P2P
                "discharge_port": "",               # Mandatory if D2P/P2P
                "precarriage_type": "PICKUP_TYPE",  # Mandatory
            },
        :returns string
        """
        vals.update(
            {
                "shipping_position": self._prepare_shipment_position(
                    vals.get("shipping_position_vals", {})
                )
            }
        )
        xml = """
            <shippingInformation>
                {shipping_position}
                <grossWeight>{weight}</grossWeight>
                <volume>{volume}</volume>
            </shippingInformation>
            <precarriageType>{precarriage_type}</precarriageType>
        """
        if vals.get("ocean_business", False):
            xml += "<myOceanBusiness>{ocean_business}</myOceanBusiness>"
        if vals.get("loading_port", False):
            xml += "<portLoading>{loading_port}</portLoading>"
        if vals.get("discharge_port", False):
            xml += "<portDischarge>{discharge_port}</portDischarge>"
        return xml.format(**vals)

    def _prepare_specific_fields(self, booking_type, vals):
        if booking_type == "Land":
            return self._prepare_land_xml(vals)
        elif booking_type == "Air":
            return self._prepare_air_xml(vals)
        elif booking_type == "OceanFCL":
            return self._prepare_oceanfcl_xml(vals)
        elif booking_type == "OceanLCL":
            return self._prepare_oceanlcl_xml(vals)
        raise NotImplementedError(
            _("Booking requests of type {} are not implemented.", booking_type)
        )

    def _prepare_booking(self, vals):
        xml = """
            {application_area}
            <booking{type} submitBooking="true">
                {barcode_xml}
                {addresses}
                {incoterm_xml}
                {incoterm_location_xml}
                {product_code_xml}
                {measurement_xml}
                {cargo_description_xml}
                {customs_clearance_xml}
                {weight_xml}
                {indoor_delivery_xml}
                {pickup_dates}
                {references}
                {handling_xml}
                {neutral_shipping_xml}
                {special_cargo_xml}
                {special_cargo_desc_xml}
                {value_of_goods_xml}
                {waybill_number_xml}
                {incoterm_dest_xml}
                {service_xml}
                {type_specific}
            </booking{type}>
        """
        vals.update(
            {
                "incoterm_xml": (
                    "<incoterm>{incoterm}</incoterm>".format(
                        incoterm=vals.get("incoterm")
                    )
                ),
                "incoterm_location_xml": (
                    "<incotermLocation>{incoterm_location}</incotermLocation>".format(
                        incoterm_location=vals.get("incoterm_location")
                    )
                ),
                "product_code_xml": (
                    "<productCode>{product_code}</productCode>".format(
                        product_code=vals.get("product_code")
                    )
                ),
                "measurement_xml": (
                    "<measurementType>{measurement}</measurementType>".format(
                        measurement=vals.get("measurement")
                    )
                ),
                "customs_clearance_xml": (
                    "<customsClearance>{customs_clearance}</customsClearance>".format(
                        customs_clearance=vals.get("customs_clearance")
                    )
                ),
                "weight_xml": (
                    "<grossWeight>{weight}</grossWeight>".format(
                        weight=vals.get("weight")
                    )
                ),
                "indoor_delivery_xml": (
                    "<indoorDelivery>{indoor_delivery}</indoorDelivery>".format(
                        indoor_delivery=vals.get("indoor_delivery")
                    )
                ),
                "neutral_shipping_xml": (
                    "<neutralShipping>{neutral_shipping}</neutralShipping>".format(
                        neutral_shipping=vals.get("neutral_shipping")
                    )
                ),
                "special_cargo_xml": (
                    "<specialCargo>{special_cargo}</specialCargo>".format(
                        special_cargo=vals.get("special_cargo")
                    )
                ),
                "barcode_xml": (
                    """<barcodeRequest start_pos="1">{barcode_size}</barcodeRequest>
                    """.format(
                        barcode_size=vals.get("barcode_size")
                    )
                    if vals.get("barcode_size", False)
                    else ""
                ),
                "cargo_description_xml": (
                    "<cargoDescription>{cargo_description}</cargoDescription>".format(
                        cargo_description=vals.get("cargo_description")
                    )
                    if vals.get("cargo_description", False)
                    else ""
                ),
                "handling_xml": (
                    "<handlingInstructions>{handling}</handlingInstructions>".format(
                        handling=vals.get("handling")
                    )
                    if vals.get("handling", False)
                    else ""
                ),
                "special_cargo_desc_xml": (
                    """<specialCargoDescription>{desc}</specialCargoDescription>
                    """.format(
                        desc=vals.get("special_cargo_desc")
                    )
                    if vals.get("special_cargo_desc", False)
                    else ""
                ),
                "value_of_goods_xml": (
                    """
                        <valueOfGoods>
                            <value>{value}</value>
                            <currency>{currency}</currency>
                        </valueOfGoods>
                    """.format(
                        value=vals.get("value"), currency=vals.get("currency")
                    )
                    if vals.get("value", False) and vals.get("currency", False)
                    else ""
                ),
                "waybill_number_xml": (
                    "<wayBillNumber>{waybill_number}</wayBillNumber>".format(
                        waybill_number=vals.get("waybill_number")
                    )
                    if vals.get("waybill_number", False)
                    else ""
                ),
                "incoterm_dest_xml": (
                    """<incotermDestinationType>{dest}</incotermDestinationType>
                    """.format(
                        dest=vals.get("incoterm_dest")
                    )
                    if vals.get("incoterm_dest", False)
                    else ""
                ),
                "service_xml": (
                    "<serviceType>{service}</serviceType>".format(
                        service=vals.get("service")
                    )
                    if vals.get("service", False)
                    else ""
                ),
            }
        )
        return xml.format(**vals)

    def _do_booking_request(self, booking_type, xml):
        if booking_type == "Land":
            return self.client.service.getBookingRequestLand(xml)
        elif booking_type == "Air":
            return self.client.service.getBookingRequestAir(xml)
        elif booking_type == "OceanFCL":
            return self.client.service.getBookingRequestOceanFCL(xml)
        elif booking_type == "OceanLCL":
            return self.client.service.getBookingRequestOceanLCL(xml)
        raise NotImplementedError(
            _("Booking requests of type {} are not implemented.", booking_type)
        )

    def _prepare_cancel_shipment(self, vals):
        return """
            {application_area}
            <cancelRequest>
                <bookingId>{booking_id}</bookingId>
            </cancelRequest>
        """.format(
            **vals
        )

    def _prepare_barcode_label(self, vals):
        """Creates XML for barcode label requests
        :param vals - Dict with keys
            {
                "application_area": {},  # Mandatory
                "format": "",  # Mandatory
                "reference": "",  # Mandatory
            },
        :returns string
        """
        return """
            {application_area}
            <barcodeRequest>
                <format>{format}</format>
                <bookingId>{reference}</bookingId>
            </barcodeRequest>
        """.format(
            **vals
        )

    def _send_shipping(self, vals):
        """Create new shipment
        :params vals dict of needed values
        :returns dict with DB Schenker response containing the booking ID and label
        """
        vals.update(
            {
                "application_area": self._prepare_application_area(
                    vals["applicationarea_vals"]
                ),
                "addresses": self._prepare_addresses(vals["address_vals"]),
                "pickup_dates": self._prepare_pickup_dates(vals["pickup_date_vals"]),
                "references": self._prepare_references(vals["reference_vals"]),
                "type_specific": self._prepare_specific_fields(
                    vals["type"], vals["type_fields"]
                ),
            }
        )
        xml = Raw(self._prepare_booking(vals))
        _logger.debug(xml)
        try:
            res = self._do_booking_request(vals["type"], xml)
        except Exception as e:
            raise UserError(
                _(
                    "No response from server recording DB Schenker delivery.\n"
                    "Traceback:\n{}"
                ).format(e)
            )
        # Convert result suds object to dict
        res = self._recursive_asdict(res)
        _logger.debug(res)
        return res

    def _print_shipment_label(self, vals):
        """Get shipping label for the given ref
        :param str vals -- public shipping reference
        :returns: base64 with pdf label or False
        """
        vals.update(
            {
                "application_area": self._prepare_application_area(
                    vals["applicationarea_vals"]
                )
            }
        )
        xml = Raw(self._prepare_barcode_label(vals))
        try:
            res = self.client.service.getBookingBarcodeRequest(xml)
            _logger.debug(res)
        except Exception as e:
            raise UserError(
                _(
                    "DB Schenker: No response from server printing label with ref {}.\n"
                    "Traceback:\n{}"
                ).format(vals.get("reference"), e)
            )
        res = self._recursive_asdict(res)
        label = res.get("document")
        return label

    def _cancel_shipping(self, vals):
        """Cancel shipment for a given reference
        :param vals dict of needed values
        :returns: dict -- result of operation with format
        {
            'applicationarea_vals': dict - user info,
            'booking_id': str - reference
        }
        """
        vals.update(
            {
                "application_area": self._prepare_application_area(
                    vals["applicationarea_vals"]
                )
            }
        )
        xml = Raw(self._prepare_cancel_shipment(vals))
        _logger.debug(xml)
        try:
            response = self.client.service.getBookingCancelRequest(xml)
            _logger.debug(response)
        except Exception as e:
            _logger.error(
                "No response from server canceling DB Schenker ref {}.\n"
                "Traceback:\n{}".format(vals.get("booking_id"), e)
            )
            return {}
        response = self._recursive_asdict(response)
        return response
