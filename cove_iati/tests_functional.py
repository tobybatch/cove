import os
import time
import pytest
from selenium import webdriver

BROWSER = os.environ.get('BROWSER', 'Firefox')


@pytest.fixture(scope="module")
def browser(request):
    browser = getattr(webdriver, BROWSER)()
    browser.implicitly_wait(3)
    request.addfinalizer(lambda: browser.quit())
    return browser


@pytest.fixture(scope="module")
def server_url(request, live_server):
    if 'CUSTOM_SERVER_URL' in os.environ:
        return os.environ['CUSTOM_SERVER_URL']
    else:
        return live_server.url


def test_accordion(server_url, browser):
    browser.get(server_url)

    def buttons():
        return [b.is_displayed() for b in browser.find_elements_by_tag_name('button')]

    time.sleep(0.5)
    assert buttons() == [True, False, False]
    assert 'Upload a file (.csv, .xlsx, .xml)' in browser.find_elements_by_tag_name('label')[0].text
    browser.find_element_by_partial_link_text('Link').click()
    browser.implicitly_wait(1)
    time.sleep(0.5)
    assert buttons() == [False, True, False]
    browser.find_element_by_partial_link_text('Paste').click()
    time.sleep(0.5)
    assert buttons() == [False, False, True]
    assert 'Paste (XML only)' in browser.find_elements_by_tag_name('label')[2].text

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


@pytest.mark.parametrize(('source_filename', 'expected_text', 'conversion_successful'), [
    ('basic_iati_unordered_valid.xlsx', ['Valid against Schema'], True),
    ('basic_iati_unordered_invalid_iso_dates.xlsx', ['Invalid against Schema'], True),
    ('bad.xml', ['We think you tried to upload a XML file'], False),
    ('bad_spaces.csv', ['Converted to XML 2 Errors'], True),
    # We should not server error when there's fields not in the schema
    ('not_iati.csv', ['Data Supplied', 'Invalid against Schema'], True),
])
def test_explore_iati_url_input(server_url, browser, httpserver, source_filename, expected_text, conversion_successful):
    with open(os.path.join('cove_iati', 'fixtures', source_filename), 'rb') as fp:
        httpserver.serve_content(fp.read())
    if 'CUSTOM_SERVER_URL' in os.environ:
        # Use urls pointing to GitHub if we have a custom (probably non local) server URL
        source_url = 'https://raw.githubusercontent.com/OpenDataServices/cove/master/cove_iati/fixtures/' + source_filename
    else:
        source_url = httpserver.url + '/' + source_filename

    browser.get(server_url)
    browser.find_element_by_partial_link_text('Link').click()
    time.sleep(0.5)
    browser.find_element_by_id('id_source_url').send_keys(source_url)
    browser.find_element_by_css_selector("#fetchURL > div.form-group > button.btn.btn-primary").click()

    data_url = browser.current_url

    # Click and un-collapse all explore sections
    all_sections = browser.find_elements_by_class_name('panel-heading')
    for section in all_sections:
        if section.get_attribute('data-toggle') == "collapse" and section.get_attribute('aria-expanded') != 'true':
            section.click()
        time.sleep(0.5)

    # Do the assertions
    check_url_input_result_page(server_url, browser, httpserver, source_filename, expected_text, conversion_successful)

    #refresh page to now check if tests still work after caching some data
    browser.get(data_url)

    return

    if conversion_successful:
        # Expand all sections with the expand all button this time
        browser.find_element_by_link_text('Expand all').click()
        time.sleep(0.5)

    # Do the assertions again
    check_url_input_result_page(server_url, browser, httpserver, source_filename, expected_text, conversion_successful)


def check_url_input_result_page(server_url, browser, httpserver, source_filename, expected_text, conversion_successful):
    body_text = browser.find_element_by_tag_name('body').text
    if isinstance(expected_text, str):
        expected_text = [expected_text]

    for text in expected_text:
        assert text in body_text

    if conversion_successful:
        assert 'Converted to XML' in body_text
