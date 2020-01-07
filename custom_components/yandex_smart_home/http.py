"""Support for Yandex Smart Home."""
import logging

from aiohttp.web import Request, Response
# Typing imports
from homeassistant.components.http import HomeAssistantView

from .const import DOMAIN
from .smart_home import async_handle_message

_LOGGER = logging.getLogger(__name__)


class YandexSmartHomeUnauthorizedView(HomeAssistantView):
    """Handle Yandex Smart Home unauthorized requests."""

    url = '/api/yandex_smart_home/v1.0'
    name = 'api:yandex_smart_home:unauthorized'
    requires_auth = False

    def config(self, request):
        return request.app['hass'].data.get(DOMAIN)

    async def head(self, request: Request) -> Response:
        """Handle Yandex Smart Home HEAD requests."""
        if self.config(request) is None:
            return Response(status=404)

        _LOGGER.debug("Request: %s (HEAD)" % request.url)
        return Response(status=200)


class YandexSmartHomeView(YandexSmartHomeUnauthorizedView):
    """Handle Yandex Smart Home requests."""

    url = '/api/yandex_smart_home/v1.0'
    extra_urls = [
        url + '/user/unlink',
        url + '/user/devices',
        url + '/user/devices/query',
        url + '/user/devices/action',
    ]
    name = 'api:yandex_smart_home'
    requires_auth = True

    async def post(self, request: Request) -> Response:
        """Handle Yandex Smart Home POST requests."""
        if self.config(request) is None:
            return Response(status=404)

        message = await request.json()  # type: dict
        _LOGGER.debug("Request: %s (POST data: %s)" % (request.url, message))
        result = await async_handle_message(
            request.app['hass'],
            self.config(request),
            request['hass_user'].id,
            request.headers.get('X-Request-Id'),
            request.path.replace(self.url, '', 1),
            message)
        _LOGGER.debug("Response: %s", result)
        return self.json(result)

    async def get(self, request: Request) -> Response:
        """Handle Yandex Smart Home GET requests."""
        if self.config(request) is None:
            return Response(status=404)

        _LOGGER.debug("Request: %s" % request.url)
        result = await async_handle_message(
            request.app['hass'],
            self.config(request),
            request['hass_user'].id,
            request.headers.get('X-Request-Id'),
            request.path.replace(self.url, '', 1),
            {})
        _LOGGER.debug("Response: %s" % result)
        return self.json(result)
