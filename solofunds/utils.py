import os
import string
import base64
from datetime import datetime
import requests
from dotenv import load_dotenv

load_dotenv()


def validate_ssn(ssn):
    """
    validate if a given SSN is valid or not by checking
    if it contains 9 numeric digits only
    """

    # account for SSN containing dashes
    ssn = ssn.replace("-", "")

    # SSN must be 9 digits
    if len(ssn) != 9:
        return False

    # SSN can only contain digits
    if len(set(ssn) - set(string.digits)) != 0:
        return False

    return True


def parse_dob(dob):
    try:
        return datetime.strptime(dob, "%d/%m/%Y")
    except:
        return None


def filestorage_to_base64(filestorage):
    return base64.b64encode(filestorage.read())


def accura_ocr(base64_img, country_code="USA", card_code="MRZ"):
    """
    using accurascan.com API for OCR and document scanning
    """

    headers = {
        "Api-Key": os.environ.get("ACCURASCAN_OCR_KEY")
    }
    data = {
        "country_code": country_code,
        "card_code": card_code,
        "scan_image_base64": base64_img
    }
    r = requests.post("https://accurascan.com/api/v4/ocr",
                      data=data, headers=headers)
    return r.json()["data"][f"{card_code}data"]


def accura_face_match(base64_img, base64_id_image):
    """
    using accurascan.com API for face matching
    """

    headers = {
        "Api-Key": os.environ.get("ACCURASCAN_FACE_MATCH_KEY")
    }
    data = {
        "source_image_base64": base64_id_image,
        "target_image_base64": base64_img
    }
    r = requests.post("https://accurascan.com/v2/api/facematch",
                      data=data, headers=headers)
    return r.json()["data"]
