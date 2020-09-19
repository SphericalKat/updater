from flask import Blueprint, jsonify, request

from api_common import get_oems, get_device_builds, get_device_data, get_device_versions
from caching import cache
from changelog import GerritServer, get_changes
from config import Config

api = Blueprint('api_v2', __name__)

gerrit = GerritServer(Config.GERRIT_URL)


@api.route('/oems')
@cache.cached()
def api_v2_oems():
    oems = get_oems()
    response = []

    for oem, devices_data in oems.items():
        response_oem = {
            'name': oem,
            'devices': []
        }

        for device_data in devices_data:
            response_oem['devices'].append({
                'model': device_data['model'],
                'name': device_data['name'],
            })

        response.append(response_oem)

    return jsonify(response)


@api.route('/devices/<string:device>')
@cache.cached()
def api_v2_device_builds(device):
    device_data = get_device_data(device)
    builds = get_device_builds(device)

    def get_download_url(build):
        return Config.DOWNLOAD_BASE_URL + build['filepath']

    for build in builds:
        build['url'] = get_download_url(build)
        if 'recovery' in build:
            build['recovery']['url'] = get_download_url(build['recovery'])

    return jsonify({
        'name': device_data['name'],
        'model': device_data['model'],
        'oem': device_data['oem'],
        'info_url': Config.WIKI_INFO_URL.format(device=device),
        'install_url': Config.WIKI_INSTALL_URL.format(device=device),
        'builds': builds,
    })


@api.route('/changes')
@cache.cached()
def api_v2_changes():
    args = request.args.to_dict(False)
    device = args.get('device', None, str)
    before = args.get('before', -1, int)

    versions = request.args.get('version')
    if not versions:
        versions = get_device_versions(device)
    elif type(versions) != list:
        if type(versions) != str:
            raise ValueError('Version is not a string')

        versions = [versions]

    return jsonify(get_changes(gerrit, device, before, versions, Config.STATUS_URL))
