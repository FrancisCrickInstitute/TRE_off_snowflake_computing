import xmltodict
from okta.client import Client
from okta.utils import format_url
from urllib.parse import urlencode
import okta.api_response


def build_xml_response_with_attributes(self, response_body):
    """
    Converts XML response text into Python dictionary with attributes.

    Args:
        response_body ([type]): [description]
    """
    self._body = xmltodict.parse(response_body, xml_attribs=True)


okta.api_response.OktaAPIResponse.build_xml_response = build_xml_response_with_attributes


class OktaClient(Client):
    """
    The class OktaClient inherits from okta.client from official package.
    Its purpose is to extend client with the new method get_saml_metadata_for_application to obtain SAML app metadata.

    The pull request with this method was submitted to official, but not yet merged.
    """

    async def get_saml_metadata_for_application(self, appId, kid):
        """
        Asynchronous call to endpoint /api/v1/apps/{appId}/sso/saml/metadata.

        Args:
            appId(str): ID of the SAML application
            kid(str): unique identifier for the certificate

        Returns:
            result(dict) : metadata for the application, including Entity ID, ACS and x509 certificate.
            response(OktaAPIResponse): original response from Okta
            error: None if request succeeded, otherwise contains error
        """
        http_method = "get".upper()
        api_url = format_url(f"""
                    {self._base_url}
                    /api/v1/apps/{appId}/sso/saml/metadata
                    """)

        encoded_query_params = urlencode({"kid": kid})
        api_url += f"/?{encoded_query_params}"

        body = {}
        headers = {"Accept": "application/xml"}
        form = {}

        request, error = await self._request_executor.create_request(
            http_method, api_url, body, headers, form
        )

        if error:
            return None, None, error

        request["headers"]["Accept"] = "application/xml"
        request["headers"]["Content-Type"] = "application/xml"
        response, error = await self._request_executor \
            .execute(request)

        if error:
            return None, response, error

        try:
            result = self.form_response_body(response.get_body())

        except Exception as error:
            return None, response, error
        return result, response, None
