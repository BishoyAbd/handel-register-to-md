
HOME_URL = "https://www.handelsregister.de/"
DOWNLOADS_DIR = "downloads"

# Timeouts (in milliseconds)
DEFAULT_TIMEOUT = 30000
NAVIGATION_TIMEOUT = 10000
DOWNLOAD_TIMEOUT = 45000
RESULTS_TIMEOUT = 30000

# Selectors
SEARCH_PAGE_LINK = '#naviForm\\:normaleSucheLink'
SEARCH_INPUT = '#form\\:schlagwoerter'
SEARCH_BUTTON = '#form\\:btnSuche'
RESULTS_FORM_SELECTOR = 'form#ergebnissForm'
RESULTS_ANCHOR_SELECTOR = 'form#ergebnissForm a[id^="ergebnissForm:selectedSuchErgebnisFormTable"]'
RESULTS_TABLE_ROW_SELECTOR = 'form#ergebnissForm table tr'
DOCUMENT_LINK_TABLE_SELECTOR = 'table'
DOCUMENT_LINK_SELECTOR = 'a'
COMPANY_ROW_SELECTOR = 'tr'
COMPANY_CELL_SELECTOR = 'td'
ERROR_MESSAGE_SELECTORS = ['.ui-messages', '.ui-message', '.error', '.warning', '.info']

# User Agent
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
