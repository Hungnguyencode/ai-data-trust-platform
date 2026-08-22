from __future__ import annotations

import re

EMAIL_PATTERN = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)

PHONE_PATTERN = re.compile(
    r"(?<!\d)(?:\+84|84|0)(?:\s|\.)?(?:3|5|7|8|9)\d(?:\s|\.)?\d{3}(?:\s|\.)?\d{3}(?!\d)"
)

CITIZEN_ID_PATTERN = re.compile(
    r"(?<!\d)(?:\d{9}|\d{12})(?!\d)"
)

ADDRESS_KEYWORDS = [
    "street",
    "road",
    "avenue",
    "district",
    "ward",
    "province",
    "ngõ",
    "ngo",
    "ngách",
    "đường",
    "duong",
    "phố",
    "pho",
    "quận",
    "quan",
    "huyện",
    "huyen",
    "phường",
    "phuong",
    "tỉnh",
    "tinh",
    "thành phố",
]

ADDRESS_REGEX_PATTERN = re.compile(
    r"(?:\b\d{1,5}\s+[A-Za-zÀ-ỹ]+)|"
    r"(?:\b(?:street|road|avenue|district|ward|province)\b)|"
    r"(?:\b(?:ngõ|ngo|ngách|đường|duong|phố|pho|quận|quan|huyện|huyen|phường|phuong|tỉnh|tinh|thành phố)\b)",
    re.IGNORECASE,
)

NAME_COLUMN_KEYWORDS = [
    "name",
    "full_name",
    "fullname",
    "customer_name",
    "user_name",
    "ho_ten",
    "hoten",
    "họ tên",
    "ten",
]

EMAIL_COLUMN_KEYWORDS = [
    "email",
    "mail",
    "e_mail",
]

PHONE_COLUMN_KEYWORDS = [
    "phone",
    "mobile",
    "tel",
    "telephone",
    "sdt",
    "so_dien_thoai",
    "số điện thoại",
]

ADDRESS_COLUMN_KEYWORDS = [
    "address",
    "dia_chi",
    "địa chỉ",
    "home_address",
    "billing_address",
    "shipping_address",
]

CITIZEN_ID_COLUMN_KEYWORDS = [
    "citizen_id",
    "national_id",
    "identity",
    "id_card",
    "cccd",
    "cmnd",
    "passport",
]