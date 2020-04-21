"""Support for Yandex Smart Home."""
import logging
from json import loads

from aiohttp.web import Request, Response

from homeassistant.components.http import HomeAssistantView

from .const import DOMAIN
from .smart_home import async_handle_message

_LOGGER = logging.getLogger(__name__)


class YandexSmartHomeUnauthorizedView(HomeAssistantView):
    """Handle Yandex Smart Home unauthorized requests."""

    url = '/api/yandex_smart_home/v1.0'
    name = 'api:yandex_smart_home:unauthorized'
    requires_auth = False

    @classmethod
    def config(cls, request):
        return request.app['hass'].data.get(DOMAIN)

    async def head(self, request: Request) -> Response:
        """Handle Yandex Smart Home HEAD requests."""
        if not self.config(request):
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
        config = self.config(request)
        if not config:
            return Response(status=404)

        request_body = await request.text()
        message = loads(request_body) if request_body else {}
        _LOGGER.debug("Request: %s (POST data: %s)" % (request.url, message))
        result = await async_handle_message(
            request.app['hass'],
            config,
            request['hass_user'].id,
            request.headers.get('X-Request-Id'),
            request.path.replace(self.url, '', 1),
            message)
        _LOGGER.debug("Response: %s", result)
        return self.json(result)

    async def get(self, request: Request) -> Response:
        """Handle Yandex Smart Home GET requests."""
        config = self.config(request)
        if not config:
            return Response(status=404)

        _LOGGER.debug("Request: %s" % request.url)
        result = await async_handle_message(
            request.app['hass'],
            config,
            request['hass_user'].id,
            request.headers.get('X-Request-Id'),
            request.path.replace(self.url, '', 1),
            {})
        _LOGGER.debug("Response: %s" % result)
        return self.json(result)
