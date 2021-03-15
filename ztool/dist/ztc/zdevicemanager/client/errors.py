import requests


class ZdmException(Exception):
    """
     A base class from which all other exceptions inherit.

     To catch all errors that the ZDM SDK might raise,
     catch this base exception.
     """


def create_api_error_from_http_exception(e):
    """
    Create a suitable APIError from requests.exceptions.HTTPError.
    """
    response = e.response
    try:
        # TODO: use err_code, err_title and err_mesage of the ZDM API
        data = response.json()
        err_message = data['message']
        err_code = data["code"]
        err_title = data["title"]
    except ValueError:
        err_message = (response.content or '').strip()
        err_code = None
        err_title= None
    cls = APIError
    if response.status_code == 403:
        cls = ForbiddenError
    if response.status_code == 404:
        # if explanation and ('No such image' in str(explanation) or
        #                     'not found: does not exist or no pull access'
        #                     in str(explanation) or
        #                     'repository does not exist' in str(explanation)):
        #     cls = ImageNotFound
        # else:
        cls = NotFoundError
    raise cls(e, response=response, err_code=err_code, err_title=err_title, err_message=err_message)


class APIError(requests.exceptions.HTTPError, ZdmException):
    """
    An HTTP error from the API.
    """

    def __init__(self, message, response=None, err_code=None, err_title=None, err_message=None):
        # requests 1.2 supports response as a keyword argument, but
        # requests 1.1 doesn't
        super(APIError, self).__init__(message)
        self.response = response
        self.err_title = err_title
        self.err_code = err_code
        self.err_message = err_message

    def __str__(self):
        message = super(APIError, self).__str__()

        if self.is_client_error():
            message = '{0} Client Error: {1}'.format(
                self.response.status_code, self.response.reason)

        elif self.is_server_error():
            message = '{0} Server Error: {1}'.format(
                self.response.status_code, self.response.reason)

        if self.err_message:
            message = '{0} ("{1}")'.format(message, self.err_message)

        return message

    @property
    def status_code(self):
        if self.response is not None:
            return self.response.status_code

    @property
    def code(self):
        # Status code of the errore returned by the  ZDM API (not the HTTP method)
        if self.err_code is not None:
            return self.err_code

    @property
    def title(self):
        # Title of the error returned by the  ZDM API
        if self.err_title is not None:
            return self.err_title

    @property
    def msg(self):
        # Message of the error returned by the  ZDM API
        if self.err_message is not None:
            return self.err_message

    def is_error(self):
        return self.is_client_error() or self.is_server_error()

    def is_client_error(self):
        if self.status_code is None:
            return False
        return 400 <= self.status_code < 500

    def is_server_error(self):
        if self.status_code is None:
            return False
        return 500 <= self.status_code < 600


class ForbiddenError(APIError):
    pass


class NotFoundError(APIError):
    """Raised when a resource is not found
    """
    pass

