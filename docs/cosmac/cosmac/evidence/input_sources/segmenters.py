"""Stdlib-only PROTOTYPE extractors, to estimate what a segment-based
intermediate representation buys. Not production quality: no real CSS
cascade, no JS, no charset sniffing. Each returns a list of
{"kind": str, "hidden": bool, "text": str}.
"""
import email
import email.policy
import io
import json
import re
import tokenize
import xml.etree.ElementTree as ET
from email.header import decode_header, make_header
from html.parser import HTMLParser

HIDDEN_STYLE = re.compile(
    r"display\s*:\s*none|visibility\s*:\s*hidden|font-size\s*:\s*0|opacity\s*:\s*0(?:\.0+)?\s*(?:;|$)"
    r"|(?:left|top|text-indent)\s*:\s*-\d{3,}|color\s*:\s*(?:#fff(?:fff)?|white)\b",
    re.I)
TEXT_ATTRS = ("alt", "title", "aria-label", "placeholder", "value", "content", "summary")
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
MIN = 12  # ignore tiny fragments


class _H(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.segs = []
        self.stack = []  # (tag, hidden)
        self.visible = []
        self.skip = None

    def _hidden(self):
        return any(h for _, h in self.stack)

    def handle_starttag(self, tag, attrs):
        a = dict((k, v or "") for k, v in attrs)
        hid = bool(HIDDEN_STYLE.search(a.get("style", ""))) or "hidden" in a or a.get("aria-hidden") == "true" \
            or (tag == "input" and a.get("type") == "hidden")
        for k, v in a.items():
            if (k in TEXT_ATTRS or k.startswith("data-")) and len(v) >= MIN:
                self.segs.append(dict(kind="html.attr:" + k, hidden=True, text=v))
        if tag in ("script", "style"):
            self.skip = tag
        if tag not in VOID:
            self.stack.append((tag, hid))

    def handle_endtag(self, tag):
        if self.skip == tag:
            self.skip = None
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break

    def handle_data(self, data):
        if self.skip or not data.strip():
            return
        if self._hidden():
            self.segs.append(dict(kind="html.hidden_text", hidden=True, text=data.strip()))
        else:
            self.visible.append(data.strip())

    def handle_comment(self, data):
        if len(data.strip()) >= MIN:
            self.segs.append(dict(kind="html.comment", hidden=True, text=data.strip()))


def seg_html(text, prefix=""):
    h = _H()
    h.feed(text)
    h.close()
    out = []
    vis = " ".join(h.visible)
    if vis.strip():
        out.append(dict(kind=prefix + "html.visible_text", hidden=False, text=vis))
    for s in h.segs:
        s["kind"] = prefix + s["kind"]
        out.append(s)
    return out


MD_LINK_TITLE = re.compile(r"\]\(\s*\S+\s+\"([^\"]{%d,})\"\s*\)" % MIN)
MD_REF_TITLE = re.compile(r"^\s*\[[^\]]+\]:\s*\S+\s+\"([^\"]{%d,})\"" % MIN, re.M)
MD_IMG_ALT = re.compile(r"!\[([^\]]{%d,})\]\(" % MIN)


def seg_markdown(text):
    out = []
    for m in MD_LINK_TITLE.finditer(text):
        out.append(dict(kind="md.link_title", hidden=True, text=m.group(1)))
    for m in MD_REF_TITLE.finditer(text):
        out.append(dict(kind="md.ref_title", hidden=True, text=m.group(1)))
    for m in MD_IMG_ALT.finditer(text):
        out.append(dict(kind="md.image_alt", hidden=True, text=m.group(1)))
    html_segs = seg_html(text, prefix="md.")
    # visible prose = markdown with link targets / titles / images removed
    prose = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text)
    prose = re.sub(r"\]\([^)]*\)", "]", prose)
    prose = re.sub(r"^\s*\[[^\]]+\]:.*$", " ", prose, flags=re.M)
    prose = re.sub(r"<!--.*?-->", " ", prose, flags=re.S)
    prose = re.sub(r"<[^>]+>", " ", prose)
    out.insert(0, dict(kind="md.visible_text", hidden=False, text=prose))
    out.extend(s for s in html_segs if s["hidden"])
    return out


def seg_email(text):
    msg = email.message_from_string(text, policy=email.policy.default)
    out = []
    for h in ("Subject", "From", "Reply-To"):
        v = msg.get(h)
        if v:
            try:
                v = str(make_header(decode_header(str(v))))
            except Exception:  # noqa: BLE001
                v = str(v)
            out.append(dict(kind="email.header:" + h.lower(), hidden=False, text=v))
    for part in msg.walk():
        if part.is_multipart():
            continue
        ctype = part.get_content_type()
        try:
            body = part.get_content()
        except Exception:  # noqa: BLE001
            continue
        if not isinstance(body, str):
            continue
        if ctype == "text/html":
            out.extend(seg_html(body, prefix="email."))
        else:
            fresh, quoted = [], []
            for line in body.splitlines():
                (quoted if line.lstrip().startswith(">") else fresh).append(line.lstrip("> "))
            if "".join(fresh).strip():
                out.append(dict(kind="email.body_text", hidden=False, text="\n".join(fresh)))
            if "".join(quoted).strip():
                out.append(dict(kind="email.quoted_reply", hidden=False, text="\n".join(quoted)))
    return out


def _walk(o, path, out):
    if isinstance(o, dict):
        for k, v in o.items():
            if len(str(k)) >= 24:
                out.append(dict(kind="json.key@" + path, hidden=False, text=str(k)))
            _walk(v, path + "." + str(k)[:20], out)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            _walk(v, path + "[%d]" % i, out)
    elif isinstance(o, str) and len(o) >= MIN:
        out.append(dict(kind="json.string@" + path, hidden=False, text=o))


def seg_api(text):
    out = []
    t = text.lstrip()
    if t.startswith(("{", "[")):
        try:
            _walk(json.loads(text), "$", out)
            return out
        except ValueError:
            pass
    if t.startswith("<"):
        try:
            root = ET.fromstring(text)  # prototype only; production must use defusedxml
            for el in root.iter():
                for chunk in (el.text, el.tail):
                    if chunk and len(chunk.strip()) >= MIN:
                        out.append(dict(kind="xml.text:" + el.tag, hidden=False, text=chunk.strip()))
                for k, v in el.attrib.items():
                    if len(v) >= MIN:
                        out.append(dict(kind="xml.attr:" + k, hidden=False, text=v))
            return out
        except ET.ParseError:
            pass
    return [dict(kind="text", hidden=False, text=text)]


BIDI = re.compile("[‪-‮⁦-⁩​-‏⁠﻿]")
C_COMMENT = re.compile(r"//[^\n]*|/\*.*?\*/|(?m:^\s*#[^\n]*)", re.S)
C_STRING = re.compile(r"\"((?:[^\"\\\n]|\\.){%d,})\"|'((?:[^'\\\n]|\\.){%d,})'|`((?:[^`\\]|\\.){%d,})`" % (MIN, MIN, MIN))


def seg_code(text):
    out = []
    had_bidi = bool(BIDI.search(text))
    clean = BIDI.sub("", text)
    t = clean.lstrip()
    if t.startswith("{"):
        try:
            _walk(json.loads(clean), "$", out)
            return out
        except ValueError:
            pass
    done = False
    try:  # Python: exact comments / strings via tokenize
        compile(clean, "<s>", "exec")
        comments, strings = [], []
        for tok in tokenize.generate_tokens(io.StringIO(clean).readline):
            if tok.type == tokenize.COMMENT:
                comments.append(tok.string.lstrip("# "))
            elif tok.type == tokenize.STRING and len(tok.string) >= MIN:
                strings.append(tok.string.strip("\"'rbfu \n"))
        if comments:
            out.append(dict(kind="code.comments", hidden=had_bidi, text="\n".join(comments)))
        for s in strings:
            out.append(dict(kind="code.string", hidden=False, text=s))
        done = True
    except (SyntaxError, tokenize.TokenError, ValueError):
        pass
    if not done:  # generic fallback for JS / shell / YAML
        comments = [re.sub(r"^\s*(//|/\*|\*/|#!?)\s*", "", m.group()) for m in C_COMMENT.finditer(clean)]
        if comments:
            out.append(dict(kind="code.comments", hidden=had_bidi, text="\n".join(comments)))
        for m in C_STRING.finditer(clean):
            out.append(dict(kind="code.string", hidden=False, text=next(g for g in m.groups() if g)))
    return out


OCR_MAP = str.maketrans({"0": "o", "1": "l", "5": "s", "$": "s", "@": "a", "|": "l", "3": "e", "4": "a"})


def seg_ocr(text):
    """OCR repair prototype: de-hyphenate line breaks, collapse letter-spacing,
    undo common glyph confusions (digit<->letter, rn->m, vv->w)."""
    out = [dict(kind="ocr.raw", hidden=False, text=text)]
    t = re.sub(r"(\w)-\n\s*(\w)", r"\1\2", text)
    t = re.sub(r"(?<![A-Za-z])((?:[A-Za-z'.@] ){4,}[A-Za-z.])(?![A-Za-z])",
               lambda m: m.group(1).replace(" ", ""), t)
    t = re.sub(r" {2,}", " ", t)
    # digits inside words -> letters
    t = re.sub(r"\b(?=\w*[A-Za-z])(?=\w*[0-9])\w+\b", lambda m: m.group().translate(OCR_MAP), t)
    t2 = t.replace("rn", "m").replace("vv", "w")
    out.append(dict(kind="ocr.repaired", hidden=False, text=t))
    out.append(dict(kind="ocr.repaired+rn_m", hidden=False, text=t2))
    return out


def segment(source, text):
    if source in ("web_page", "html"):
        return seg_html(text)
    if source == "markdown":
        return seg_markdown(text)
    if source == "email":
        return seg_email(text)
    if source == "api_response":
        return seg_api(text)
    if source == "source_code":
        return seg_code(text)
    if source == "ocr_text":
        return seg_ocr(text)
    return [dict(kind="text", hidden=False, text=text)]
