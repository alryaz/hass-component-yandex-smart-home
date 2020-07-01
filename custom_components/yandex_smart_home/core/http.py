"""Support for Yandex Smart Home."""
import logging
from json import JSONDecodeError
from types import SimpleNamespace
from typing import TYPE_CHECKING, Tuple, Union, Optional
from uuid import uuid4

from aiohttp.web import Request, Response
from aiohttp.web_exceptions import HTTPUnauthorized, HTTPBadRequest, HTTPNotFound
from homeassistant.components.http import HomeAssistantView

from ..const import DOMAIN
from ..core.smart_home import async_handle_message

if TYPE_CHECKING:
    from homeassistant.auth.models import User
    from ..core.helpers import Config

_LOGGER = logging.getLogger(__name__)


class YandexSmartHomeUnauthorizedView(HomeAssistantView):
    """Handle Yandex Smart Home unauthorized requests."""

    url = '/api/yandex_smart_home/v1.0'
    name = 'api:yandex_smart_home:unauthorized'
    requires_auth = False

    @classmethod
    def config(cls, request: Request) -> 'Config':
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
    requires_auth = False  # this is handled manually within `_process_auth` method

    def _process_auth(self, request: Request) -> Tuple['Config', Union[SimpleNamespace, 'User'], Optional[str]]:
        config = self.config(request)
        if not config:
            raise HTTPNotFound()

        hass_user = request.get('hass_user')
        request_id = request.headers.get('X-Request-Id')
        if config.diagnostics_mode:
            # Facilitate the use of diagnostics mode by adding dummy data to the request
            if not hass_user:
                hass_user = SimpleNamespace(id=999999)
            if not request_id:
                request_id = str(uuid4()).upper()
        elif not hass_user:
            raise HTTPUnauthorized()
        elif not request_id:
            raise HTTPBadRequest()
        
        return config, hass_user, request_id

    async def post(self, request: Request) -> Response:
        """Handle Yandex Smart Home POST requests."""
        config, hass_user, request_id = self._process_auth(request)

        try:
            message = await request.json()
            _LOGGER.debug("Request: %s (JSON data: %s)" % (request.url, message))
        except JSONDecodeError:
            message = {}
            _LOGGER.debug("Request: %s (POST data: %s)" % (request.url, await request.text()))

        result = await async_handle_message(
            request.app['hass'],
            config,
            hass_user.id,
            request_id,
            request.path.replace(self.url, '', 1),
            message)

        _LOGGER.debug("Response: %s", result)
        return self.json(result)

    async def get(self, request: Request) -> Response:
        """Handle Yandex Smart Home GET requests."""
        config, hass_user, request_id = self._process_auth(request)

        _LOGGER.debug("Request: %s" % request.url)
        result = await async_handle_message(
            request.app['hass'],
            config,
            hass_user.id,
            request_id,
            request.path.replace(self.url, '', 1),
            {})

        _LOGGER.debug("Response: %s" % result)
        return self.json(result)
