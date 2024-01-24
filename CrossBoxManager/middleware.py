from django.http import HttpResponseRedirect
from django.conf import settings
from re import compile
from django.db import connection
from django.utils.deprecation import MiddlewareMixin
import os

EXEMPT_URLS = [compile(settings.LOGIN_URL.lstrip('/'))]
if hasattr(settings, 'LOGIN_EXEMPT_URLS'):
    EXEMPT_URLS += [compile(expr) for expr in settings.LOGIN_EXEMPT_URLS]

def terminal_width():
    """
    Function to compute the terminal width.
    WARNING: This is not my code, but I've been using it previous projects and
    I don't remember where it came from.
    """
    width = 0
    try:
        import struct, fcntl, termios
        s = struct.pack('HHHH', 0, 0, 0, 0)
        x = fcntl.ioctl(1, termios.TIOCGWINSZ, s)
        width = struct.unpack('HHHH', x)[1]
    except:
        pass
    if width <= 0:
        try:
            width = int(os.environ['COLUMNS'])
        except:
            pass
    if width <= 0:
        width = 80
    return width


class LoginRequiredMiddleware(object):
    """
    Middleware that requires a user to be authenticated to view any page other
    than LOGIN_URL. Exemptions to this requirement can optionally be specified
    in settings via a list of regular expressions in LOGIN_EXEMPT_URLS (which
    you can copy from your urls.py).

    Requires authentication middleware and template context processors to be
    loaded. You'll get an error if they aren't.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        assert hasattr(request, 'user'), "The Login Required middleware\
         requires authentication middleware to be installed. Edit your\
         MIDDLEWARE_CLASSES setting to insert\
         'django.contrib.auth.middlware.AuthenticationMiddleware'. If that doesn't\
         work, ensure your TEMPLATE_CONTEXT_PROCESSORS setting includes\
         'django.core.context_processors.auth'."
        if not request.user.is_authenticated:
            path = request.path_info.lstrip('/')
            if not any(m.match(path) for m in EXEMPT_URLS):
                return HttpResponseRedirect(settings.LOGIN_URL)
        return self.get_response(request)


class SqlPrintingMiddleware(MiddlewareMixin):
    """
    Middleware which prints out a list of all SQL queries done
    for each view that is processed.  This is only useful for debugging.
    In production envrionment this middleware is commented in settings.py MIDDLEWARE tuple
    """

    def process_response(self, request, response):
        indentation = 2
        if len(connection.queries) > 0 and settings.DEBUG:
            width = terminal_width()
            total_time = 0.0
            for query in connection.queries:
                nice_sql = query['sql'].replace('"', '').replace(',',', ')
                sql = "\033[1;31m[%s]\033[0m %s" % (query['time'], nice_sql)
                total_time = total_time + float(query['time'])
                while len(sql) > width-indentation:
                    print ("%s%s" % (" "*indentation, sql[:width-indentation]))
                    sql = sql[width-indentation:]
                print ("%s%s\n" % (" "*indentation, sql))
            replace_tuple = (" "*indentation, str(total_time))
            print ("%s\033[1;32m[TOTAL TIME: %s seconds]\033[0m" % replace_tuple)
        return response