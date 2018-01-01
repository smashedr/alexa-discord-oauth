from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from home.models import TokenDatabase
import logging
import random
import requests
import string
import urllib.parse

logger = logging.getLogger('app')
config = settings.CONFIG


def has_error(request):
    """
    # View  /error
    """
    return render(request, 'error.html')


@require_http_methods(['GET'])
def do_authorize(request):
    """
    # View  /authorize
    """
    log_req(request)
    try:
        if 'client_id' in request.GET:
            request.session['client_id'] = request.GET.get('client_id')
        if 'redirect_uri' in request.GET:
            request.session['redirect_uri'] = request.GET.get('redirect_uri')
        if 'response_type' in request.GET:
            request.session['response_type'] = request.GET.get('response_type')
        if 'state' in request.GET:
            request.session['state'] = request.GET.get('state')

        if request.session['client_id'] != config.get('Amazon', 'client_id'):
            raise ValueError('Inivalid client_id')
        if request.session['redirect_uri'] not in \
                config.get('Amazon', 'redirect_uris', raw=True).split(' '):
            raise ValueError('Inivalid redirect_uri')
        if request.session['response_type'] != 'code':
            raise ValueError('Inivalid response_type')
        if not request.session['state']:
            raise ValueError('Inivalid state')

        return gen_redirect()
    except Exception as error:
        logger.exception(error)
        return redirect_err(request, 'Error: {}'.format(error))


@require_http_methods(['GET'])
def oauth_redirect(request):
    """
    # View  /redirect
    """
    try:
        if request.GET['error'] == 'access_denied':
            logger.info('access_denied')
            return redirect_err(
                request, 'Request was not Authorized by you or Discord.'
            )
    except Exception as error:
        logger.info(error)
        pass

    try:
        request.session['code'] = request.GET['code']
        oauth = get_token(request.session['code'])
        logger.info(oauth)
        token_id = ''.format(
            oauth['webhook']['id'], oauth['webhook']['token']
        )

        try:
            td = TokenDatabase.objects.get(code=request.session['code'])
            td.delete()
        except:
            pass

        code = ''.join(
            random.choice(
                string.ascii_uppercase + string.digits
            ) for _ in range(20)
        )

        td = TokenDatabase(
            code=code,
            token=token_id,
        )
        td.save()

        params = {
            'code': code, 'state': request.session['state']
        }
        url = request.session['redirect_uri']
        uri = url + '?' + urllib.parse.urlencode(params)
        logger.info(uri)
        return redirect(uri)
    except Exception as error:
        logger.exception(error)
        return redirect_err(request, 'Error: {}'.format(error))


@csrf_exempt
@require_http_methods(['POST'])
def give_token(request):
    """
    # View  /token
    """
    log_req(request)
    try:
        _code = request.POST.get('code')
        _client_id = request.POST.get('client_id')
        _client_secret = request.POST.get('client_secret')
        logger.info('client_secret: {}'.format(_client_secret))

        if _client_id != config.get('Amazon', 'client_id'):
            logger.info('invalid_client_id')
            return JsonResponse(
                json_err('invalid_client', 'ClientId is Invalid'), status=400
            )

        try:
            if _code:
                td = TokenDatabase.objects.get(code=_code)
                token = td.token
            else:
                raise ValueError('code null')
        except Exception as error:
            logger.exception(error)
            return JsonResponse(
                json_err('invalid_code', 'Code is Invalid'), status=400
            )

        token_resp = {
            'access_token': token,
            'token_type': 'bearer',
        }
        return JsonResponse(token_resp)
    except Exception as error:
        logger.exception(error)
        return JsonResponse(
            json_err('unknown_error', 'Unknown Error'), status=400
        )


def get_token(oauth_code):
    """
    Send Oauth to Provider
    """
    data = {
        "client_id": config.get('Provider', 'client_id'),
        "client_secret": config.get('Provider', 'client_secret'),
        "code": oauth_code,
        'redirect_uri': config.get('Provider', 'redirect_uri'),
        'grant_type': 'authorization_code',
    }
    url = '{}/oauth2/token'.format(config.get('Provider', 'token_uri'))
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    r = requests.post(url, data, headers=headers)
    # r.raise_for_status()
    return r.json()


def gen_redirect():
    """
    Redirects to Provider Oauth
    """
    url = config.get('Provider', 'authorize_uri', raw=True)
    params = {
        'client_id': config.get('Provider', 'client_id'),
        'redirect_uri': config.get('Provider', 'redirect_uri'),
        'scope': config.get('Provider', 'oauth_scopes'),
    }
    uri = '{}/?{}'.format(url, urllib.parse.urlencode(params))
    return HttpResponseRedirect(uri)


def json_err(error_code, error_msg):
    resp = {'ErrorCode': error_code, 'Error': error_msg}
    return resp


def redirect_err(request, error='Unknown Error', name='error', tags='danger'):
    messages.add_message(
        request, messages.WARNING,
        error,
        extra_tags=tags,
    )
    return redirect(name)


def log_req(request):
    """
    DEBUGGING ONLY
    """
    data = ''
    if request.method == 'GET':
        logger.debug('GET')
        for key, value in request.GET.items():
            data += '"%s": "%s", ' % (key, value)
    if request.method == 'POST':
        logger.debug('POST')
        for key, value in request.POST.items():
            data += '"%s": "%s", ' % (key, value)
    data = data.strip(', ')
    logger.debug(data)
    json_string = '{%s}' % data
    return json_string
