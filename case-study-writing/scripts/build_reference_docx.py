#!/usr/bin/env python3
"""Build the pandoc reference.docx from the Lincoln Loop Case Study Template.

The template (a Google Docs export) only defines Word's built-in styles
(Normal, Heading 1-6, Title, Subtitle, TableNormal). Pandoc additionally
looks up its own named styles; when absent, pandoc injects defaults that
ignore the template's branding. This script clones the template and adds
those missing styles, derived from the template's own Normal style, so the
generated .docx stays fully branded and imports cleanly into Google Docs.

Usage:
    python3 scripts/build_reference_docx.py <template.docx> <reference.docx>

Stdlib only; no third-party dependencies.
"""

import re
import shutil
import sys
import zipfile

# Each entry: (styleId, xml). Only added if the styleId is not already defined.
EXTRA_STYLES = [
    (
        "BodyText",
        '<w:style w:type="paragraph" w:styleId="BodyText">'
        '<w:name w:val="Body Text"/><w:basedOn w:val="Normal"/>'
        '<w:pPr><w:spacing w:after="120"/></w:pPr></w:style>',
    ),
    (
        "FirstParagraph",
        '<w:style w:type="paragraph" w:styleId="FirstParagraph">'
        '<w:name w:val="First Paragraph"/><w:basedOn w:val="BodyText"/></w:style>',
    ),
    (
        "Compact",
        '<w:style w:type="paragraph" w:styleId="Compact">'
        '<w:name w:val="Compact"/><w:basedOn w:val="BodyText"/>'
        '<w:pPr><w:spacing w:before="36" w:after="36"/></w:pPr></w:style>',
    ),
    (
        "BlockText",
        '<w:style w:type="paragraph" w:styleId="BlockText">'
        '<w:name w:val="Block Text"/><w:basedOn w:val="BodyText"/>'
        '<w:pPr><w:ind w:left="720" w:right="720"/>'
        '<w:spacing w:before="120" w:after="120"/></w:pPr>'
        "<w:rPr><w:i/></w:rPr></w:style>",
    ),
    (
        "ImageCaption",
        '<w:style w:type="paragraph" w:styleId="ImageCaption">'
        '<w:name w:val="Image Caption"/><w:basedOn w:val="Normal"/>'
        '<w:pPr><w:jc w:val="center"/><w:spacing w:after="240"/></w:pPr>'
        '<w:rPr><w:sz w:val="18"/><w:color w:val="666666"/></w:rPr></w:style>',
    ),
    (
        "CaptionedFigure",
        '<w:style w:type="paragraph" w:styleId="CaptionedFigure">'
        '<w:name w:val="Captioned Figure"/><w:basedOn w:val="Normal"/>'
        '<w:pPr><w:keepNext/><w:jc w:val="center"/>'
        '<w:spacing w:before="120"/></w:pPr></w:style>',
    ),
    (
        "Figure",
        '<w:style w:type="paragraph" w:styleId="Figure">'
        '<w:name w:val="Figure"/><w:basedOn w:val="Normal"/>'
        '<w:pPr><w:jc w:val="center"/><w:spacing w:before="120" w:after="120"/>'
        "</w:pPr></w:style>",
    ),
    (
        "TableCaption",
        '<w:style w:type="paragraph" w:styleId="TableCaption">'
        '<w:name w:val="Table Caption"/><w:basedOn w:val="ImageCaption"/></w:style>',
    ),
    (
        "SourceCode",
        '<w:style w:type="paragraph" w:styleId="SourceCode">'
        '<w:name w:val="Source Code"/><w:basedOn w:val="Normal"/>'
        '<w:rPr><w:rFonts w:ascii="Courier New" w:hAnsi="Courier New"/>'
        '<w:sz w:val="20"/></w:rPr></w:style>',
    ),
    (
        "FootnoteText",
        '<w:style w:type="paragraph" w:styleId="FootnoteText">'
        '<w:name w:val="footnote text"/><w:basedOn w:val="Normal"/>'
        '<w:rPr><w:sz w:val="20"/></w:rPr></w:style>',
    ),
    (
        "Hyperlink",
        '<w:style w:type="character" w:styleId="Hyperlink">'
        '<w:name w:val="Hyperlink"/>'
        '<w:rPr><w:color w:val="1155CC"/><w:u w:val="single"/></w:rPr></w:style>',
    ),
    (
        "VerbatimChar",
        '<w:style w:type="character" w:styleId="VerbatimChar">'
        '<w:name w:val="Verbatim Char"/>'
        '<w:rPr><w:rFonts w:ascii="Courier New" w:hAnsi="Courier New"/>'
        '<w:sz w:val="20"/></w:rPr></w:style>',
    ),
    (
        "Table",
        '<w:style w:type="table" w:styleId="Table">'
        '<w:name w:val="Table"/><w:basedOn w:val="TableNormal"/>'
        "<w:tblPr><w:tblBorders>"
        '<w:top w:val="single" w:sz="4" w:color="CCCCCC"/>'
        '<w:bottom w:val="single" w:sz="4" w:color="CCCCCC"/>'
        '<w:insideH w:val="single" w:sz="4" w:color="CCCCCC"/>'
        "</w:tblBorders></w:tblPr></w:style>",
    ),
]


def build(template_path: str, output_path: str) -> None:
    shutil.copyfile(template_path, output_path)

    with zipfile.ZipFile(template_path) as zin:
        styles_xml = zin.read("word/styles.xml").decode("utf-8")
        other_items = [
            (item, zin.read(item.filename))
            for item in zin.infolist()
            if item.filename != "word/styles.xml"
        ]

    existing_ids = set(re.findall(r'w:styleId="([^"]+)"', styles_xml))
    additions = "".join(
        xml for style_id, xml in EXTRA_STYLES if style_id not in existing_ids
    )
    added = [s for s, _ in EXTRA_STYLES if s not in existing_ids]
    new_styles_xml = styles_xml.replace("</w:styles>", additions + "</w:styles>")

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zout:
        for item, data in other_items:
            zout.writestr(item, data)
        zout.writestr("word/styles.xml", new_styles_xml)

    print(f"Wrote {output_path}")
    print(f"Added styles: {', '.join(added) if added else '(none, all present)'}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    build(sys.argv[1], sys.argv[2])
