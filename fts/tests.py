import pytest
from selenium import webdriver
import time
import os


@pytest.fixture(scope="module")
def browser(request):
    browser = webdriver.Firefox()
    browser.implicitly_wait(3)
    request.addfinalizer(lambda: browser.quit())
    return browser


@pytest.fixture(scope="module")
def server_url(request, live_server):
    if 'CUSTOM_SERVER_URL' in os.environ:
        return os.environ['CUSTOM_SERVER_URL']
    else:
        return live_server.url


def test_index_page_ocds(server_url, browser):
    browser.get(server_url + '/ocds/')
    assert 'Open Contracting Data Tool' in browser.find_element_by_tag_name('body').text
    assert 'How to use the Open Contracting Data Tool' in browser.find_element_by_tag_name('body').text
    assert 'What happens to the data I provide to this site?' in browser.find_element_by_tag_name('body').text
    assert 'Why do you delete data after 7 days?' in browser.find_element_by_tag_name('body').text
    assert 'Why provide converted versions?' in browser.find_element_by_tag_name('body').text


def test_index_page_360(server_url, browser):
    browser.get(server_url + '/360/')
    assert '360 Giving Data Tool' in browser.find_element_by_tag_name('body').text
    assert 'How to use the 360 Giving Data Tool' in browser.find_element_by_tag_name('body').text
    assert 'What happens to the data I provide to this site?' in browser.find_element_by_tag_name('body').text
    assert 'Why do you delete data after 7 days?' in browser.find_element_by_tag_name('body').text
    assert 'Why provide converted versions?' in browser.find_element_by_tag_name('body').text


@pytest.mark.parametrize('prefix', ['/ocds/', '/360/'])
def test_accordion(server_url, browser, prefix):
    browser.get(server_url + prefix)

    def buttons():
        return [b.is_displayed() for b in browser.find_elements_by_tag_name('button')]

    time.sleep(0.5)
    assert buttons() == [True, False, False]
    browser.find_element_by_partial_link_text('Link').click()
    browser.implicitly_wait(1)
    time.sleep(0.5)
    assert buttons() == [False, True, False]
    browser.find_element_by_partial_link_text('Paste').click()
    time.sleep(0.5)
    assert buttons() == [False, False, True]
    # Now test that the whole banner is clickable
    browser.find_element_by_id('headingOne').click()
    time.sleep(0.5)
    assert buttons() == [True, False, False]
    browser.find_element_by_id('headingTwo').click()
    time.sleep(0.5)
    assert buttons() == [False, True, False]
    browser.find_element_by_id('headingThree').click()
    time.sleep(0.5)
    assert buttons() == [False, False, True]


@pytest.mark.parametrize(('prefix', 'source_filename', 'expected_text'), [
    ('/ocds/', 'tenders_releases_2_releases.json', 'Download Files'),
    # Conversion should still work for files that don't validate against the schema
    ('/ocds/', 'tenders_releases_2_releases_invalid.json', 'Download Files'),
    # But we expect to see an error message if a file is not well formed JSON at all
    ('/ocds/', 'tenders_releases_2_releases_not_json.json', 'not well formed JSON'),
    ('/ocds/', 'tenders_releases_2_releases.xlsx', 'Download Files'),
    ('/360/', 'WellcomeTrust-grants_fixed_2_grants.json', 'Download Files'),
    ])
def test_URL_input_json(server_url, browser, httpserver, source_filename, prefix, expected_text):
    with open(os.path.join('cove', 'fixtures', source_filename), 'rb') as fp:
        httpserver.serve_content(fp.read())
    source_url = httpserver.url + '/' + source_filename

    browser.get(server_url + prefix)
    browser.find_element_by_partial_link_text('Link').click()
    time.sleep(0.5)
    browser.find_element_by_id('id_source_url').send_keys(source_url)
    browser.find_element_by_css_selector("#fetchURL > div.form-group > button.btn.btn-primary").click()
    assert expected_text in browser.find_element_by_tag_name('body').text
    
    # We should still be in the correct app
    if prefix == 'ocds':
        assert 'Open Contracting Data Tool' in browser.find_element_by_tag_name('body').text
        # Look for Release Table
        assert 'Release Table' in browser.find_element_by_tag_name('body').text
    elif prefix == '360':
        assert '360 Giving Data Tool' in browser.find_element_by_tag_name('body').text
