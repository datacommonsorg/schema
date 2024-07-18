# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Validates schema urls."""
import csv
import os
import pathlib
import re
import urllib

from absl import app
from absl import flags
import git
import requests

FLAGS = flags.FLAGS
flags.DEFINE_boolean("update_allowlist", False,
                     "If set, regenerates url_allowlist.csv.")

API_ERROR = "An HTTP {} code was returned by the autopush API. Please ensure that DC_API_KEY is set to the autopush API key."
API_PREFIX = "https://autopush.api.datacommons.org/v2/node?key="
MANIFEST = "MANIFEST"
URL_ALLOWLIST = "url_allowlist.csv"
URL_PROPS = ["license", "url"]

# Using regex in https://www.geeksforgeeks.org/python-check-url-string/.
URL_REGEX = (
    r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
)


def get_status(url):
  """Gets the status for invalid url.

  Args:
    url: Url to check.

  Returns:
    status: Status code and reason.
    message: Optional message providing additional details about response.
  """
  try:
    resp = requests.get(url, timeout=30)

    # Redirect.
    if resp.history:
      initial_resp = resp.history[0]
      return str(initial_resp.status_code
                ) + " " + initial_resp.reason if initial_resp.reason else str(
                    initial_resp.status_code), "Redirected to " + resp.url

    return str(resp.status_code) + " " + resp.reason if resp.reason else str(
        resp.status_code), ""

  except Exception as e:
    return "ERROR", str(e)


def get_modified_files():
  """Returns list of locally modified MCF files in the current branch.

  Returns:
    List of modified files.
  """
  repo = git.Repo('.', search_parent_directories=True)
  return [
      "../" + file for file in sorted(
          filter(
              lambda x: x.endswith(".mcf"),
              list(item.a_path for item in repo.index.diff(None)) +
              list(repo.untracked_files)))
  ]


def find_invalid_manifest_urls(allowlisted_urls):
  """Finds invalid urls from manifest using the DC API.

  Args:
    allowlisted_urls: Set of urls to skip checking.

  Returns:
    Map of ("MANIFEST", <url>) -> (<status>, <message>) for invalid urls.
  """
  dc_api_key = os.environ.get('DC_API_KEY', '')

  nextToken = ""
  dcids = []
  while True:
    resp = requests.get(
        API_PREFIX + dc_api_key +
        "&nodes=Provenance&nodes=Dataset&nodes=Source&property=<-typeOf&nextToken="
        + nextToken)
    if resp.status_code != 200:
      raise ValueError(API_ERROR.format(resp.status_code))

    for _, data in resp.json()["data"].items():
      if not data:
        continue
      for node in data["arcs"]["typeOf"]["nodes"]:
        dcids.append(node["dcid"])

    if "nextToken" in resp.json():
      nextToken = urllib.parse.quote(resp.json()["nextToken"], safe="")
    else:
      break

  nextToken = ""
  urls = set()
  while True:
    resp = requests.get(API_PREFIX + dc_api_key +
                        "".join(["&nodes=" + dcid for dcid in dcids]) +
                        "&property=->[" + ",".join(URL_PROPS) + "]&nextToken=" +
                        nextToken)
    if resp.status_code != 200:
      raise ValueError(API_ERROR.format(resp.status_code))

    for _, data in resp.json()["data"].items():
      if "arcs" not in data:
        continue
      for _, nodes in data["arcs"].items():
        for node in nodes["nodes"]:
          if (MANIFEST, node["value"]) not in allowlisted_urls:
            urls.add(node["value"])

    if "nextToken" in resp.json():
      nextToken = urllib.parse.quote(resp.json()["nextToken"], safe="")
    else:
      break

  invalid_urls = {}
  for url in sorted(urls):
    print("Checking", url)
    status, message = get_status(url)
    if not status.startswith("200"):
      invalid_urls[(MANIFEST, url)] = (status, message)


def find_invalid_schema_urls(allowlisted_urls, files):
  """Finds invalid urls from schema files using the DC API.

  Args:
    allowlisted_urls: Set of urls to skip checking.

  Returns:
    Map of (<file>, <url>) -> (<status>, <message>) for invalid urls.
  """
  invalid_urls = {}
  all_urls = set()
  for file in files:
    with open(file) as f_in:
      print("\n*** Processing", file, "***\n")
      text = f_in.read()
      for match in re.findall(URL_REGEX, text):
        url = match[0]
        if (file, url) in allowlisted_urls or (file, url) in all_urls:
          continue

        print("Checking", url)
        status, message = get_status(url)
        all_urls.add((file, url))
        if not status.startswith("200"):
          invalid_urls[(file, url)] = (status, message)

  return invalid_urls


def find_invalid_urls(allowlisted_urls, files):
  """Finds all invalid urls.

  Args:
    allowlisted_urls: Set of urls to skip checking.

  Returns:
    Map of (<file>, <url>) -> (<status>, <message>) for invalid urls.
  """
  schema_urls = find_invalid_schema_urls(allowlisted_urls, files)
  manifest_urls = find_invalid_manifest_urls(allowlisted_urls)
  return dict(schema_urls | manifest_urls)


def update_allowlist():
  """Updates url_allowlist.csv by re-checking all urls."""
  with open(URL_ALLOWLIST, "w") as f_out:
    writer = csv.DictWriter(f=f_out,
                            fieldnames=["file", "url", "status", "message"])
    writer.writeheader()

    invalid_urls = find_invalid_urls({},
                                     sorted(pathlib.Path("../").rglob("*.mcf")))

    for (file, url), (status, message) in sorted(invalid_urls.items()):
      writer.writerow({
          "file": file,
          "url": url,
          "status": status,
          "message": message,
      })


def check_modified_files():
  """Checks urls from modified files and prints invalid urls."""
  allowlisted_urls = set()
  with open(URL_ALLOWLIST) as f:
    reader = csv.DictReader(f)
    for row in reader:
      allowlisted_urls.add((row["file"], row["url"]))

  # Currently only check modified schema files (i.e. not manifest urls).
  # TODO: Get modified manifest files from g3.
  invalid_urls = find_invalid_schema_urls(allowlisted_urls,
                                          get_modified_files())

  if invalid_urls:
    print(
        "\nFound new invalid urls! Please fix the urls below or add to url_allowlist.csv: \n"
    )
    for (file, url), (status, message) in sorted(invalid_urls.items()):
      print("File:", file, "\nUrl:", url, "\nStatus:", status)
      if message:
        print("Message:", message, "\n")
  else:
    print("\nAll new urls pass! :)")


def main(argv):
  if len(argv) > 1:
    raise app.UsageError("Too many command-line arguments.")

  if FLAGS.update_allowlist:
    update_allowlist()

  # Default to only check modified files.
  else:
    check_modified_files()


if __name__ == '__main__':
  app.run(main)
