
import warnings

from django.conf.urls import include, patterns, url
from django.utils import six
from django.utils.functional import cached_property
from leonardo.utils.settings import (get_conf_from_module,
                                     get_leonardo_modules, get_loaded_modules,
                                     is_leonardo_module, merge)
from django.utils.importlib import import_module  # noqa
from django.utils.module_loading import module_has_submodule  # noqa
from leonardo.decorators import require_auth, _decorate_urlconf


class Default(object):

    core = ['web', 'nav', 'media', 'search', 'devel', 'leonardo_auth']

    @property
    def middlewares(self):
        MIDDLEWARE_CLASSES = [
            'django.middleware.common.CommonMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.middleware.http.ConditionalGetMiddleware',
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.middleware.clickjacking.XFrameOptionsMiddleware',
            'django.middleware.locale.LocaleMiddleware',
            'django.contrib.sites.middleware.CurrentSiteMiddleware',

        ]
        import django
        if django.VERSION >= (1, 8, 0):
            MIDDLEWARE_CLASSES += [
                'django.contrib.auth.middleware.SessionAuthenticationMiddleware']
        else:
            MIDDLEWARE_CLASSES += ['django.middleware.doc.XViewMiddleware']

        try:
            import debug_toolbar
            MIDDLEWARE_CLASSES += ['debug_toolbar.middleware.DebugToolbarMiddleware']
        except ImportError:
            pass

        return MIDDLEWARE_CLASSES

    @property
    def apps(self):
        return [
            'django',

            'django_extensions',
            'django.contrib.contenttypes',
            'django.contrib.auth',
            'django.contrib.sessions',
            'django.contrib.sites',
            'django.contrib.staticfiles',
            'django.contrib.sitemaps',

            'rest_framework',
            'dbtemplates',

            'django_select2',

            'reversion',
            'compressor',

            'horizon',
            'horizon_contrib',

            'leonardo',

            'constance',
            'constance.backends.database',

        ]

    @property
    def context_processors(self):
        """return CORE Conent Type Processors
        """
        cp = [
            'django.contrib.auth.context_processors.auth',
            'horizon.context_processors.horizon',
            'django.contrib.messages.context_processors.messages',

            'constance.context_processors.config',
        ]
        import django

        if django.VERSION[:2] < (1, 8):

            cp += [
                'django.core.context_processors.debug',
                'django.core.context_processors.i18n',
                'django.core.context_processors.media',
                'django.core.context_processors.request',
                'django.core.context_processors.static',
            ]

        else:
            cp += [
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.request',
                'django.template.context_processors.static',
            ]

        return cp

default = Default()


class Leonardo(object):

    default = default

    MODULES_AUTOLOAD = True

    def load_modules(self):
        """find all leonardo modules from environment"""
        if self.MODULES_AUTOLOAD:
            self.add_modules(get_leonardo_modules())
        return self.modules

    @property
    def modules(self):
        """loaded modules
        auto populated if is not present
        """
        return self._modules

    def set_modules(self, modules):
        """setter for modules"""
        self._modules = modules

    def add_modules(self, modules):
        """Merge new modules to loaded modules"""
        merged_modules = merge(modules, self.modules)
        self.set_modules(merged_modules)

    def get_modules(self, modules=None):
        """load configuration for all modules"""
        if not hasattr(self, "loaded_modules"):
            self.loaded_modules = get_loaded_modules(modules or self.modules)
        return self.loaded_modules

    def get_modules_as_list(self):
        return [module_cfg for mod, module_cfg in self.get_modules()]

    def get_app_modules(self, apps):
        """return array of imported leonardo modules for apps
        """
        modules = getattr(self, "_modules", [])

        if not modules:
            from django.utils.importlib import import_module
            from django.utils.module_loading import module_has_submodule

            # Try importing a modules from the module package
            package_string = '.'.join(['leonardo', 'module'])

            for app in apps:
                try:
                    # check if is not full app
                    _app = import_module(app)
                except ImportError:
                    _app = False
                if not _app:
                    # obsolete part
                    try:
                        # check if is not leonardo_module
                        _app = import_module('leonardo_module_{}'.format(app))
                    except ImportError:
                        _app = False

                if module_has_submodule(import_module(package_string), app) or _app:
                    if _app:
                        mod = _app
                    else:
                        mod = import_module('.{0}'.format(app), package_string)
                    modules.append(mod)
                else:
                    warnings.warn('%s was skipped because app was '
                                  'not found in PYTHONPATH' % app,
                                  ImportWarning)
            self._modules = modules
        return self._modules

    @cached_property
    def urlpatterns(self):
        '''load and decorate urls from all modules
        then store it as cached property for less loading
        '''
        urlpatterns = []
        # load all urls
        # support .urls file and urls_conf = 'elephantblog.urls' on default module
        # decorate all url patterns if is not explicitly excluded
        for mod in leonardo.modules:
            # TODO this not work
            if is_leonardo_module(mod):

                conf = get_conf_from_module(mod)

                if module_has_submodule(mod, 'urls'):
                    urls_mod = import_module('.urls', mod.__name__)
                    if hasattr(urls_mod, 'urlpatterns'):
                        # if not public decorate all

                        if conf['public']:
                            urlpatterns += urls_mod.urlpatterns
                        else:
                            _decorate_urlconf(urls_mod.urlpatterns,
                                              require_auth)
                            urlpatterns += urls_mod.urlpatterns
        # avoid circural dependency
        # TODO use our loaded modules instead this property
        from django.conf import settings
        for urls_conf, conf in six.iteritems(getattr(settings, 'MODULE_URLS', {})):
            # is public ?
            try:
                if conf['is_public']:
                    urlpatterns += \
                        patterns('',
                                 url(r'', include(urls_conf)),
                                 )
                else:
                    _decorate_urlconf(
                        url(r'', include(urls_conf)),
                        require_auth)
                    urlpatterns += patterns('',
                                            url(r'', include(urls_conf)))
            except Exception as e:
                raise Exception('raised %s during loading %s' % (str(e), urls_conf))
        return urlpatterns

    _instance = None

    def __new__(cls, *args, **kwargs):
        """A singleton implementation of Leonardo. There can be only one.
        """
        if not cls._instance:
            cls._instance = super(Leonardo, cls).__new__(cls, *args, **kwargs)
        return cls._instance

leonardo = Leonardo()
