SchedulAll
==========

SchedulAll is a multi-user application for tracking people's time on projects. Complete documentation is available on `Read The Docs <http://SchedulAll.readthedocs.org>`_.

Features
--------

 * A simple CRM with projects and businesses
 * User dashboards with budgeted hours based on project contracts
 * Time sheets with daily, weekly, and monthly summaries
 * Verified, approved, and invoiced time sheet workflows
 * Gantt Chart integration and PDF export
 * Monthly payroll reporting with overtime, paid leave, and vacation summaries
 * Project invoicing with hourly summaries

Requirements
------------

SchedulAll is compatible with Python 2.{6,7}, Django 1.{3,4}, and PostgreSQL. PostgreSQL is the only offically supported database backend and, therefore, requires `psycopg2 <http://initd.org/psycopg/>`_. SchedulAll also depends on the following Django apps:

 * `python-dateutil <http://labix.org/python-dateutil>`_
 * `django-selectable <http://pypi.python.org/pypi/django-selectable>`_
 * `django-pagination <http://pypi.python.org/pypi/django-pagination>`_
 * `django-compressor <https://github.com/jezdez/django_compressor>`_
 * `django-bootstrap-toolkit <https://github.com/dyve/django-bootstrap-toolkit>`_

SchedulAll uses Sphinx and RST for documentation. You can use Sphinx to build the documentation:

 * `docutils <http://docutils.sourceforge.net/>`_
 * `Sphinx <http://sphinx.pocoo.org/>`_

A makefile is included with the documentation so you can run `make html` in the `doc/` directory to build the documentation.

Installation
------------

#. Ensure that `less <http://lesscss.org>`_ is installed on your machine::

    # Install node.js and npm:
    $ sudo apt-get install python-software-properties
    $ sudo add-apt-repository ppa:chris-lea/node.js
    $ sudo apt-get update
    $ sudo apt-get install nodejs npm

    # Use npm to install less:
    $ npm install less -g

#. If you are starting from the included example project, copy the example local settings file at `example_project/settings/local.py.example` to `example_project/settings/local.py`.

   If you are using an existing project, you will need to make the following changes to your settings:

    - Add `schedulall` and its dependencies to ``INSTALLED_APPS``::

        INSTALLED_APPS = (
            ...
            'bootstrap_toolkit',
            'compressor',
            'pagination',
            'selectable',
            'schedulall',
            ...
        )

    - Add `django.core.context_processors.request` and SchedulAll context processors to ``TEMPLATE_CONTEXT_PROCESSORS``::

        TEMPLATE_CONTEXT_PROCESSORS = (
            "django.contrib.auth.context_processors.auth",
            "django.core.context_processors.debug",
            "django.core.context_processors.i18n",
            "django.core.context_processors.media",
            "django.contrib.messages.context_processors.messages",
            "django.core.context_processors.request",           # <----
            "schedulall.context_processors.extra_nav",           # <----
            "schedulall.context_processors.active_entries",      # <----
            "schedulall.context_processors.timepiece_settings",  # <----
            "schedulall.context_processors.quick_search",        # <----
        )

    - Configure compressor settings::

        COMPRESS_PRECOMPILERS = (
            ('text/less', 'lessc {infile} {outfile}'),
        )
        COMPRESS_ROOT = '%s/static/' % PROJECT_PATH

#. Run ``syncdb``.

#. Add URLs for SchedulAll and selectable to `urls.py`, e.g.::

    urlpatterns = patterns('',
        ...
        (r'^selectable/', include('selectable.urls')),
        (r'', include('schedulall.urls')),
        ...
    )

#. Add the ``django.contrib.auth`` URLs to `urls.py`, e.g.::

    urlpatterns = patterns('',
        ...
        url(r'^accounts/login/$', 'django.contrib.auth.views.login',
            name='auth_login'),
        url(r'^accounts/logout/$', 'django.contrib.auth.views.logout_then_login',
            name='auth_logout'),
        url(r'^accounts/password-change/$',
            'django.contrib.auth.views.password_change',
            name='change_password'),
        url(r'^accounts/password-change/done/$',
            'django.contrib.auth.views.password_change_done'),
        url(r'^accounts/password-reset/$',
            'django.contrib.auth.views.password_reset',
            name='reset_password'),
        url(r'^accounts/password-reset/done/$',
            'django.contrib.auth.views.password_reset_done'),
        url(r'^accounts/reset/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$',
            'django.contrib.auth.views.password_reset_confirm'),
        url(r'^accounts/reset/done/$',
            'django.contrib.auth.views.password_reset_complete'),
        ...
    )

#. Create registration templates. For examples, see the registration templates in `example_project/templates/registration`. Ensure that your project's template directory is added to ``TEMPLATE_DIRS``::

    TEMPLATE_DIRS = (
        ...
        '%s/templates' % PROJECT_PATH,
        ...
    )
