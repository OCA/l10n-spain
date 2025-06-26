###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
VIAXPRESS_CONFIG = {
    "client": {
        "id_cliente": "",  # res_company configuration
        "usuario": "",  # res_company configuration
        "password": "",  # res_company configuration
    },
    "technical": {
        "host": "",  # res_company configuration
        "port": "",  # res_company configuration
        "url": "",  # autogenerate
        "content_type": "text/xml; charset=utf-8",
        "wsdl_file": "ServicioVxClientes.asmx",
        "wsdl_url": "",  # autogenerate
        "post": "/ServicioVxClientes.asmx HTTP/1.1",
        "xml_schema": "http://www.w3.org/2001/XMLSchema",
    },
}


class ViaxpressBaseException(Exception):
    error_messages = {}

    def __init__(self, error_type, **kwargs):
        self.title = kwargs.get("title", "ViaXpress Exception")
        self.error_type = kwargs.get("error_type", error_type)

        raw_message = kwargs.get("message", self.error_messages[error_type])
        self.message = raw_message.format(**kwargs)

    def __str__(self):
        message = f"{self.title}:\n{self.message}"
        return message


class ViaxpressTechnicalException(ViaxpressBaseException):
    error_messages = {
        "InvalidHeaderType": """
            The method type is not in 'valid_header_types'.
            Please, add or check the name of the type:

            '{type}'
        """,
        "InvalidServiceType": """
            The requested service is not a ViaXpress Service.
            Please, check the name of the service:

            '{type}'
        """,
    }

    def __init__(self, error_type, **kwargs):
        if error_type not in self.error_messages:
            raise ValueError(f"Invalid error type: {error_type}")

        super().__init__(
            title="ViaXpress Technical Exception",
            error_type=error_type,
            message_errors=self.error_messages,
            **kwargs,
        )


class ViaxpressUserException(ViaxpressBaseException):
    error_messages = {
        "InvalidCredentials": """
            The credentials are not valid.
            Please, check the user, password and client id.
        """,
        "ResponseError": """
            Please, check the response of ViaXpress API:

            '{response}'
        """,
    }

    def __init__(self, error_type, **kwargs):
        if error_type not in self.error_messages:
            raise ValueError(f"Invalid error type: {error_type}")

        super().__init__(
            title="ViaXpress User Exception",
            error_type=error_type,
            message_errors=self.error_messages,
            **kwargs,
        )
