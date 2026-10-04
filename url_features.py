"""Turns a web address into the 30 features the phishing model was trained on.

Values follow the dataset: 1 = legitimate, 0 = unsure, -1 = phishing.
Anything that cannot be measured is set to 0 and reported in `unknown`.
"""
import ipaddress
import re
import socket
from datetime import datetime
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

try:
    import whois  # pip install python-whois (optional: domain age and expiry)
except Exception:
    whois = None


class ScanError(Exception):
    pass


SHORTENERS = ("bit.ly", "goo.gl", "tinyurl.com", "t.co", "ow.ly", "is.gd", "buff.ly",
              "adf.ly", "cutt.ly", "rb.gy", "shorturl.at", "tiny.cc", "bl.ink", "rebrand.ly", "t.ly")
SLD = {"co", "com", "org", "net", "gov", "edu", "ac"}
HEADERS = {"User-Agent": "Mozilla/5.0 (student phishing-check project)"}
UNMEASURABLE = ["web_traffic", "Page_Rank", "Google_Index", "Links_pointing_to_page", "Statistical_report"]
PAGE_FEATURES = ["Favicon", "Request_URL", "URL_of_Anchor", "Links_in_tags", "SFH",
                 "Submitting_to_email", "on_mouseover", "RightClick", "popUpWidnow", "Iframe", "Redirect"]


def base_domain(host):
    p = host.lower().split(".")
    if len(p) >= 3 and len(p[-1]) == 2 and p[-2] in SLD:
        return ".".join(p[-3:])
    return ".".join(p[-2:])


def is_ip(host):
    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        return False


def resolves(host):
    """True if the host resolves. Refuses private/internal addresses."""
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        return False
    for info in infos:
        if not ipaddress.ip_address(info[4][0].split("%")[0]).is_global:
            raise ScanError("That address points to a private or internal network, so it was not scanned.")
    return True


def fetch(url):
    """Follow redirects by hand (checking every hop). Returns (final_url, html, hops, ssl_ok)."""
    verify, ssl_ok, hops = True, True, 0
    while True:
        if not resolves(urlparse(url).hostname or ""):
            return None, None, hops, ssl_ok
        try:
            r = requests.get(url, headers=HEADERS, timeout=6, allow_redirects=False, stream=True, verify=verify)
        except requests.exceptions.SSLError:
            if not verify:
                return None, None, hops, False
            verify, ssl_ok = False, False
            continue
        except requests.RequestException:
            return None, None, hops, ssl_ok
        if r.is_redirect and hops < 10 and r.headers.get("location"):
            url = urljoin(url, r.headers["location"])
            hops += 1
            r.close()
            continue
        html = r.raw.read(2_000_000, decode_content=True).decode(r.encoding or "utf-8", errors="replace")
        r.close()
        return url, html, hops, ssl_ok


def _date(v):
    if isinstance(v, list) and v:
        v = v[0]
    return v.replace(tzinfo=None) if isinstance(v, datetime) else None


def extract(raw):
    raw = (raw or "").strip()
    if not raw or " " in raw:
        raise ScanError("Enter a web address such as https://example.com")
    url = raw if "://" in raw else "https://" + raw
    p = urlparse(url)
    try:
        port = p.port
    except ValueError:
        raise ScanError("That web address has an invalid port.")
    host = (p.hostname or "").lower()
    if p.scheme not in ("http", "https") or not host:
        raise ScanError("Enter a web address such as https://example.com")

    f, unknown, notes = {}, set(), []
    f["having_IP_Address"] = -1 if is_ip(host) else 1
    f["URL_Length"] = 1 if len(url) < 54 else (0 if len(url) <= 75 else -1)
    f["Shortining_Service"] = -1 if any(host == s or host.endswith("." + s) for s in SHORTENERS) else 1
    f["having_At_Symbol"] = -1 if "@" in url else 1
    f["double_slash_redirecting"] = -1 if url.rfind("//") > 7 else 1
    f["Prefix_Suffix"] = -1 if "-" in host else 1
    h = host[4:] if host.startswith("www.") else host
    dots = h.count(".") - (1 if base_domain(h).count(".") == 2 else 0)
    f["having_Sub_Domain"] = 1 if dots <= 1 else (0 if dots == 2 else -1)
    f["port"] = 1 if port in (None, 80, 443) else -1
    f["HTTPS_token"] = -1 if "https" in host else 1

    dns_ok = resolves(host)
    f["DNSRecord"] = 1 if dns_ok else -1
    final_url = html = None
    hops, ssl_ok = 0, True
    if dns_ok:
        final_url, html, hops, ssl_ok = fetch(url)
        if html is None:
            notes.append("The page could not be loaded, so its content checks were skipped.")

    if p.scheme != "https":
        f["SSLfinal_State"] = -1
    elif html is None:
        f["SSLfinal_State"] = 0
        unknown.add("SSLfinal_State")
    else:
        f["SSLfinal_State"] = 1 if ssl_ok else 0

    # Domain registration data (WHOIS)
    created = expires = None
    whois_ran = registered = False
    if whois and dns_ok and not is_ip(host):
        try:
            w = whois.whois(base_domain(host))
            created, expires, registered, whois_ran = _date(w.creation_date), _date(w.expiration_date), bool(w.domain_name), True
        except Exception:
            pass
    elif not whois:
        notes.append("Domain age checks are off. Run: pip install python-whois")
    now = datetime.utcnow()
    f["age_of_domain"] = (1 if (now - created).days >= 180 else -1) if created else 0
    f["Domain_registeration_length"] = (-1 if (expires - now).days <= 365 else 1) if expires else 0
    f["Abnormal_URL"] = (1 if registered else -1) if whois_ran else 0
    for name, val in (("age_of_domain", created), ("Domain_registeration_length", expires)):
        if val is None:
            unknown.add(name)
    if not whois_ran:
        unknown.add("Abnormal_URL")

    # Page content
    if html is None:
        for name in PAGE_FEATURES:
            f[name] = 0
            unknown.add(name)
    else:
        soup = BeautifulSoup(html, "html.parser")
        base = base_domain(urlparse(final_url).hostname or host)
        low = html.lower()

        def external(src):
            hh = urlparse(urljoin(final_url, src)).hostname or ""
            return bool(hh) and base_domain(hh) != base

        def share(srcs):
            return 100 * sum(external(s) for s in srcs) / len(srcs)

        def rate(srcs, low_cut, high_cut):
            if not srcs:
                return 1
            r = share(srcs)
            return 1 if r < low_cut else (0 if r <= high_cut else -1)

        f["Request_URL"] = rate([t["src"] for t in soup.find_all(["img", "audio", "video", "embed", "source"]) if t.get("src")], 22, 61)
        f["Links_in_tags"] = rate([t["src"] for t in soup.find_all("script") if t.get("src")] +
                                  [t["href"] for t in soup.find_all("link") if t.get("href")], 17, 81)
        hrefs = [(a.get("href") or "").strip() for a in soup.find_all("a")]
        if hrefs:
            bad = sum(1 for x in hrefs if not x or x.startswith(("#", "javascript", "mailto")) or external(x))
            r = 100 * bad / len(hrefs)
            f["URL_of_Anchor"] = 1 if r < 31 else (0 if r <= 67 else -1)
        else:
            f["URL_of_Anchor"] = 1
        icons = soup.find_all("link", rel=lambda v: v and "icon" in (" ".join(v) if isinstance(v, list) else v).lower())
        f["Favicon"] = -1 if any(external(i.get("href", "")) for i in icons if i.get("href")) else 1
        actions = [(fm.get("action") or "").strip().lower() for fm in soup.find_all("form")]
        if any(a in ("", "about:blank") for a in actions):
            f["SFH"] = -1
        else:
            f["SFH"] = 0 if any(external(a) for a in actions) else 1
        f["Submitting_to_email"] = -1 if any(a.startswith("mailto:") for a in actions) or "mail(" in low else 1
        f["on_mouseover"] = -1 if "onmouseover" in low and "window.status" in low else 1
        f["RightClick"] = -1 if re.search(r"event\.button\s*==\s*2|oncontextmenu\s*=\s*[\"']?\s*return\s+false", low) else 1
        f["popUpWidnow"] = -1 if re.search(r"\bprompt\(", low) else (0 if "window.open(" in low else 1)
        hidden = [t for t in soup.find_all("iframe")
                  if t.get("frameborder") == "0" or "display:none" in (t.get("style") or "").replace(" ", "").lower()
                  or t.get("width") == "0" or t.get("height") == "0"]
        f["Iframe"] = -1 if hidden else 1
        f["Redirect"] = 1 if hops <= 1 else (0 if hops < 4 else -1)

    for name in UNMEASURABLE:  # need paid or discontinued data sources
        f[name] = 0
        unknown.add(name)
    return {"features": f, "unknown": sorted(unknown), "notes": notes, "final_url": final_url or url}
