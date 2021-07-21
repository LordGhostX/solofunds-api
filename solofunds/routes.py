from flask import jsonify, request
from solofunds import app, db
from solofunds.models import User, VerificationBasicInfo, VerificationDocument, VerificationImage
from solofunds.utils import *


@app.route("/kyc/step-one/", methods=["POST"])
def kyc_step_one():
    """
    This phase of the KYC process takes the user firstname, lastname, dob, ssn
    then validates the information provided matches the SSN provided.

    Due to lack of an actual SSN data source, this phase only verifies if all information
    are supplied and the SSN is in correct format (9 digits).

    PS: A user identifier must be passed in this phase
    """

    user_id = request.form.get("user_id")
    ssn = request.form.get("ssn")
    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")
    dob = request.form.get("dob")

    # parameters data validations
    if None in [user_id, ssn, first_name, last_name, dob]:
        return jsonify({
            "msg": "form fields are incomplete",
            "data": None
        }), 400

    # check if user has done this validation before
    user = User.query.get(user_id)
    if user is None:
        # if the user has no data at all, create a profile
        user = User(id=user_id)
        db.session.add(user)
        db.session.commit()
    # verify if you're allowed to attempt this verification phase
    if user.verification_level != 0:
        return jsonify({
            "msg": "user is not allowed to attempt this verification phase",
            "data": None
        }), 403
    # check if verification progress is above current level
    if user.verification_level >= 1:
        return jsonify({
            "msg": "this user has completed this verification already",
            "data": None
        }), 409

    # validate the provided SSN
    if not validate_ssn(ssn):
        return jsonify({
            "msg": "you have provided an invalid SSN",
            "data": None
        }), 400
    # validate the provided dob
    dob = parse_dob(dob)
    if dob is None:
        return jsonify({
            "msg": "you have provided an invalid DOB",
            "data": None
        }), 400

    # update the user verification level and save info gotten
    user.verification_level = 1
    db.session.add(VerificationBasicInfo(
        user_id=user.id,
        ssn=ssn,
        first_name=first_name,
        last_name=last_name,
        dob=dob
    ))
    db.session.commit()

    return jsonify({
        "msg": "the SSN provided matches the data provided",
        "data": None
    }), 200


@app.route("/kyc/step-two/", methods=["POST"])
def kyc_step_two():
    """
    This phase of the KYC process takes the user uploaded document, scans the
    information in the document to confirm their legal name and extract their photo.

    Using accurascan.com API for OCR and document scanning

    PS: A user identifier must be passed in this phase
    """

    user_id = request.form.get("user_id")
    document_type = request.form.get("document_type")
    document = request.files.get("document")

    # parameters data validations
    if None in [user_id, document_type, document]:
        return jsonify({
            "msg": "form fields are incomplete",
            "data": None
        }), 400
    if document_type not in ["passport", "national ID", "driver's license"]:
        return jsonify({
            "msg": "an invalid document type was provided",
            "data": None
        }), 400

    # check if user has done this validation before
    user = User.query.get(user_id)
    if user is None or user.verification_level != 1:
        # if the user has no data at all, return an error message
        return jsonify({
            "msg": "user is not allowed to attempt this verification phase",
            "data": None
        }), 403
    # check if verification progress is above current level
    if user.verification_level >= 2:
        return jsonify({
            "msg": "this user has completed this verification already",
            "data": None
        }), 409

    # extract info from the document with accurascan
    document_base64 = filestorage_to_base64(document)
    card_code = "PDF417" if document_type == "driver's license" else "MRZ"
    document_info = accura_ocr(document_base64, card_code=card_code)

    # validate information we already know
    basic_info = VerificationBasicInfo.query.filter_by(user_id=user.id).first()
    is_firstname_valid = basic_info.first_name.lower(
    ) == document_info.get("first_name", "").lower()
    is_lastname_valid = basic_info.last_name.lower(
    ) == document_info.get("last_name", "").lower()

    # check if a face was detected in the document
    is_face_present = document_info.get("face_image") is not None
    if not (is_firstname_valid and is_lastname_valid and is_face_present):
        return jsonify({
            "msg": "the ID submitted does not pass verification",
            "data": None
        }), 400

    # update the user verification level and save info gotten
    user.verification_level = 2
    db.session.add(VerificationDocument(
        user_id=user.id,
        document_type=document_type,
        document_base64=document_base64,
        face_image=document_info.get("face_image")
    ))
    db.session.commit()

    return jsonify({
        "msg": "the ID submitted passes verification",
        "data": None
    }), 200


@app.route("/kyc/step-three/", methods=["POST"])
def kyc_step_three():
    """
    This phase of the KYC process takes the current picture of the user, compares
    it with the image extracted from their ID to confirm they are the same person.

    Using accurascan.com API for face matching

    PS: A user identifier must be passed in this phase
    """

    user_id = request.form.get("user_id")
    picture = request.files.get("picture")

    # parameters data validations
    if None in [user_id, picture]:
        return jsonify({
            "msg": "form fields are incomplete",
            "data": None
        }), 400

    # check if user has done this validation before
    user = User.query.get(user_id)
    if user is None or user.verification_level != 2:
        # if the user has no data at all, return an error message
        return jsonify({
            "msg": "user is not allowed to attempt this verification phase",
            "data": None
        }), 403
    # check if verification progress is above current level
    if user.verification_level >= 3:
        return jsonify({
            "msg": "this user has completed this verification already",
            "data": None
        }), 409

    # extract info from the document with accurascan
    picture_base64 = filestorage_to_base64(picture)
    verification_doc = VerificationDocument.query.filter_by(
        user_id=user.id).first()
    matching_info = accura_face_match(
        picture_base64, verification_doc.face_image)

    # validate the faces match each other by checking if similarity is greater than 50%
    if matching_info["score"] < 0.5:
        return jsonify({
            "msg": "the image submitted does not pass verification",
            "data": None
        }), 400

    # update the user verification level and save info gotten
    user.verification_level = 3
    db.session.add(VerificationImage(
        user_id=user.id,
        picture_base64=picture_base64
    ))
    db.session.commit()

    return jsonify({
        "msg": "the image submitted passes verification",
        "data": None
    }), 200
