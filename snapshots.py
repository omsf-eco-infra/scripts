#!/usr/bin/env python
"""
This file generates a concatenated snapshot with all of our progress so far.
It requires a Notion integration secret with read access to our Notion
data, as well as GitHub PAT with read access to the relevant repositories.

Note that repositories we're tracking, as well as the Notion database ID of
our external contributions database, are hard-coded.

This requires requests and ghsnap (and for some reason, click, which is
required by ghsnap anyway).
"""

import argparse
import json
import os
import pathlib

import requests

from ghsnap.loaders import RepoLoader, ItemsLoader
from ghsnap.diff import diff
from ghsnap.concat import concat
from ghsnap.priss import make_reference

import click


# TODO: autoselect all repos from omsf-eco-infra?
_REPOS = [
    "omsf-eco-infra/ghsnap",
    "omsf-eco-infra/ticgithub",
]
_NOTION_DBID = "afb96d08-21c9-4c22-aa90-071bf17b271f"

# NOTION STUFF (SEPARATE THIS OUT FOR REUSE)
def extract_contents_from_row(row):
    try:
        return row['properties']['Name']['title'][0]['plain_text']
    except IndexError:
        import warnings
        warnings.warn("Got a row with no Name" + str(row))


def db_contents(db_id, token, extractor=extract_contents_from_row):
    db_id = db_id.replace('-', '')
    q_url = f"databases/{db_id}/query"
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-06-28"

    }
    resp = requests.post(f"https://api.notion.com/v1/{q_url}",
                         headers=headers)
    # TODO: error check resp
    for row in resp.json()['results']:
        if (output := extractor(row)) is not None:
            yield output


def load_notion_tracking_issues(token):
    return list(db_contents(_NOTION_DBID, token))


# CLI AND TOKENS
def get_token(name, paths, envvar, cli_opt):
    if cli_opt is not None:
        return cli_opt
    if (token := os.environ.get(envvar)) is not None:
        return token
    for unexpanded in paths:
        path = unexpanded.expanduser()
        if path.exists():
            with open(path, mode='r') as f:
                token = f.read()

            if token[-1] == "\n":
                token = token[:-1]
            return token

    raise click.BadParameter(f"Missing token for {name}")


def get_tokens(cli_opts):
    github_token = get_token(
        name="GitHub",
        paths=[pathlib.Path("~/.githubtoken")],
        envvar="GITHUB_TOKEN",
        cli_opt=cli_opts.github_token
    )
    notion_token = get_token(
        name="Notion",
        paths=[pathlib.Path("~/.notiontoken"),
               pathlib.Path("./.notiontoken")],
        envvar="NOTION_TOKEN",
        cli_opt=cli_opts.notion_token
    )
    return notion_token, github_token


def main(notion_token, gh_token):
    notion_labels = [
        make_reference(ref)
        for ref in load_notion_tracking_issues(notion_token)
    ]
    if notion_labels:
        notion_loader = ItemsLoader(notion_labels)
        snapshots = [notion_loader(gh_token)]
    else:
        snapshots = []

    for repo in _REPOS:
        owner, repo_name = repo.split('/')
        loader = RepoLoader(owner, repo_name)
        items = loader(gh_token)
        snapshots.append(items)

    total = concat(*snapshots)
    print(json.dumps(total.to_dict()))


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument("--github-token", type=str)
    parser.add_argument("--notion-token", type=str)
    args = parser.parse_args()
    notion_token, github_token = get_tokens(args)
    main(notion_token, github_token)
