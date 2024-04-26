from .bapi import BAPI
from ..partialkeydict import PartialKeyDict
import collections

import logging
_logger = logging.getLogger(__name__)


class Notion(BAPI):
    BASE_URL = "https://api.notion.com/v1"
    def _headers(self, header_kwargs):
        headers = super()._headers(header_kwargs)
        headers["Notion-Version"] = "2022-06-28"
        return headers

    @staticmethod
    def _clean_id(input_id):
        out_id = input_id.replace('-', '')
        return out_id

    def find_database_by_title(self, title):
        data = {
            "query": title,
            "filter": {
                "value": "database",
                "property": "object",
            }
        }
        databases = self.post("search", json=data)['results']
        if (count := len(databases)) != 1:
            raise RuntimeError("Expected to find 1 database called "
                               f"'{title}': found {count}.")
        return databases[0]

    def db_contents(self, db_id, extractor=None):
        if extractor is None:
            extractor = lambda x: x

        db_id = self._clean_id(db_id)
        q_url = f"databases/{db_id}/query"
        for row in self.post(q_url)['results']:
            if (output := extractor(row)) is not None:
                yield output


def get_blocks_by_heading(notion: Notion, page_id: str):
    """Extract the blocks for each heading in the page"""
    blocks_endpoint = f"blocks/{page_id}/children"
    blocks = notion.get(blocks_endpoint)['results']

    def extract_heading(block):
        return block[block['type']]['rich_text'][0]['plain_text']

    structured = collecctions.defaultdict(list)
    for block in blocks:
        if block['type'] == "heading_1":
            heading = extract_heading(block)
        else:
            structured[heading].append(block)

    d = PartialKeyDict(structured)
    return d


def get_nested_bulleted_list_item(block, indent_level=0):
    def textify(block):
        return "".join(t['plain_text'] for t in block['bulleted_list_item']['rich_text'])

    yield indent_level, textify(block)

    if block['has_children']:
        block_id = block['id']
        children = notion.get(f"blocks/{block_id}/children")['results']
        for child in children:
            yield from get_nested_bulleted_list_item(child, indent_level+1)


def get_id_from_meeting_name(inp, notion, meetings_dbid):
    _logger.debug(f"Attempting to parse '{inp}' as a meeting name (title)")
    filt = {
        "property": "Name",
        "rich_text": {
            "contains": inp,
        }
    }
    matches = notion.post(f"databases/{meetings_dbid}/query", json={"filter": filt})['results']
    if len(matches) == 0:
        return None
    elif len(matches) > 1:
        return None
    else:
        return matches[0]['id']

def get_id_from_notion_url(inp):
    _logger.debug(f"Attempting to parse '{inp}' as a Notion URL")
    if not inp.startswith("https://www.notion.so/"):
        return None

    url_and_params = inp.split("?")
    if len(url_and_params) > 2:
        ... # error

    url = url_and_params[0]
    pageid = url.split('-')[-1]
    return pageid

def get_id_from_notion(inp, notion, meetings_dbid):
    if notion_id := get_id_from_meeting_name(inp, notion, meetings_dbid):
        return notion_id
    elif notion_id := get_id_from_notion_url(inp):
        return notion_id
    else:
        raise ValueError(f"Can't regcognize '{inp}' as a meeting in our database")

def get_blocks_by_heading(notion: Notion, page_id: str):
    """Extract the blocks for each heading in the page"""
    blocks_endpoint = f"blocks/{page_id}/children"
    blocks = notion.get(blocks_endpoint)['results']

    def extract_heading(block):
        return block[block['type']]['rich_text'][0]['plain_text']

    structured = collections.defaultdict(list)
    for block in blocks:
        if block['type'] == "heading_1":
            heading = extract_heading(block)
        else:
            structured[heading].append(block)

    d = PartialKeyDict(structured)
    return d
