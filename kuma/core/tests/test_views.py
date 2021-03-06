import logging
from pyquery import PyQuery as pq
from soapbox.models import Message

import pytest
from django.core import mail
from django.test import override_settings
from django.utils.log import AdminEmailHandler

from kuma.core.tests import KumaTestCase, eq_, ok_

from ..urlresolvers import reverse


@pytest.fixture()
def sitemaps(db, settings, tmpdir):
    media_dir = tmpdir.mkdir('media')
    locale_dir = media_dir.mkdir('sitemaps').mkdir('en-US')
    sitemap_file = media_dir.join('sitemap.xml')
    locale_file = locale_dir.join('sitemap.xml')
    sitemap_file.write_text(u"""
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap>
    <loc>https://localhost:8000/sitemaps/en-US/sitemap.xml</loc>
    <lastmod>2017-09-06T23:24:37+00:00</lastmod>
  </sitemap>
</sitemapindex>""", 'utf8')
    locale_file.write_text(u"""
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://example.com/en-US/docs/foobar</loc>
    <lastmod>2013-06-06</lastmod>
   </url>
</urlset>""", 'utf8')
    return {
        'tmpdir': media_dir,
        'index': sitemap_file.read_text('utf8'),
        'locales': {
            'en-US': locale_file.read_text('utf8')
        }
    }


@override_settings(
    DEBUG=False,
    DEBUG_PROPAGATE_EXCEPTIONS=False,
    ADMINS=(('admin', 'admin@example.com'),))
class LoggingTests(KumaTestCase):
    urls = 'kuma.core.tests.logging_urls'
    logger = logging.getLogger('django.security')
    suspicous_path = '/en-US/suspicious/'

    def setUp(self):
        super(LoggingTests, self).setUp()
        self.old_handlers = self.logger.handlers[:]

    def tearDown(self):
        super(LoggingTests, self).tearDown()
        self.logger.handlers = self.old_handlers

    def test_no_mail_handler(self):
        self.logger.handlers = [logging.NullHandler()]
        response = self.client.get(self.suspicous_path)
        eq_(response.status_code, 400)
        eq_(0, len(mail.outbox))

    def test_mail_handler(self):
        self.logger.handlers = [AdminEmailHandler()]
        response = self.client.get(self.suspicous_path)
        eq_(response.status_code, 400)
        eq_(1, len(mail.outbox))
        ok_('admin@example.com' in mail.outbox[0].to)
        ok_(self.suspicous_path in mail.outbox[0].body)


class SoapboxViewsTest(KumaTestCase):

    def test_global_home(self):
        m = Message(message='Global', is_global=True, is_active=True, url='/')
        m.save()

        url = reverse('home')
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)

        doc = pq(r.content)
        eq_(m.message, doc.find('div.global-notice').text())

    def test_subsection(self):
        m = Message(message='Search', is_global=False, is_active=True,
                    url='/search/')
        m.save()

        url = reverse('search')
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)

        doc = pq(r.content)
        eq_(m.message, doc.find('div.global-notice').text())

        url = reverse('home')
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)

        doc = pq(r.content)
        eq_([], doc.find('div.global-notice'))

    def test_inactive(self):
        m = Message(message='Search', is_global=False, is_active=False,
                    url='/search/')
        m.save()

        url = reverse('search')
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)

        doc = pq(r.content)
        eq_([], doc.find('div.global-notice'))


class EventsRedirectTest(KumaTestCase):

    def test_redirect_to_mozilla_org(self):
        url = '/en-US/events'
        response = self.client.get(url)
        eq_(302, response.status_code)
        eq_('https://mozilla.org/contribute/events', response['Location'])


@pytest.mark.parametrize('method', ['get', 'head'])
def test_sitemap(client, settings, sitemaps, db, method):
    settings.MEDIA_ROOT = sitemaps['tmpdir'].realpath()
    response = getattr(client, method)(reverse('sitemap'))
    assert response.status_code == 200
    assert response['Content-Type'] == 'application/xml'
    if method == 'get':
        assert ''.join(response.streaming_content) == sitemaps['index']


@pytest.mark.parametrize(
    'method',
    ['post', 'put', 'delete', 'options', 'patch']
)
def test_sitemap_405s(client, db, method):
    response = getattr(client, method)(reverse('sitemap'))
    assert response.status_code == 405


@pytest.mark.parametrize('method', ['get', 'head'])
def test_sitemaps(client, settings, sitemaps, db, method):
    settings.MEDIA_ROOT = sitemaps['tmpdir'].realpath()
    response = getattr(client, method)(
        reverse(
            'sitemaps',
            kwargs={'path': 'sitemaps/en-US/sitemap.xml'}
        )
    )
    assert response.status_code == 200
    assert response['Content-Type'] == 'application/xml'
    if method == 'get':
        assert (''.join(response.streaming_content) ==
                sitemaps['locales']['en-US'])


@pytest.mark.parametrize(
    'method',
    ['post', 'put', 'delete', 'options', 'patch']
)
def test_sitemaps_405s(client, db, method):
    response = getattr(client, method)(
        reverse(
            'sitemaps',
            kwargs={'path': 'sitemaps/en-US/sitemap.xml'}
        )
    )
    assert response.status_code == 405
