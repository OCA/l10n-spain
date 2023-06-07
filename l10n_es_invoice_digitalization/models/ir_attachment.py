# Copyright 2023 Acysos S.L. - Ignacio Ibeas
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.mimetypes import guess_mimetype
from PIL import Image
import base64
from io import BytesIO
import cv2
import numpy as np
from scipy.ndimage import rotate
import pytesseract


MIMETYPES = ["image/jpeg", "image/png", "image/tiff", "application/pdf"]


class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    document_blocked = fields.Boolean(
        string="Document Blocked",
        default=False,
        help="If checked, the document will be blocked for digitalization."
             "You can modify or delete this document one time, after that, "
             "it will be blocked."
    )

    @api.model
    def create(self, vals):
        index_content = False
        if ("document_blocked" in vals and vals["document_blocked"]):
            vals["datas"], index_content = self._convert_document(vals)
        res = super().create(vals)
        if index_content:
            res.with_context(force_update=True).index_content = index_content
        return res

    def write(self, vals):
        if self.document_blocked and not self.env.context.get("force_update"):
            raise UserError("The document is blocked for digitalization")
        if ("document_blocked" in vals and vals["document_blocked"]):
            vals["datas"], vals["index_content"] = self._convert_document(vals)
        return super().write(vals)

    def unlink(self):
        if self.document_blocked:
            raise UserError("The document is blocked for digitalization")
        return super().unlink()

    def _convert_document(self, vals):
        im_bytes = base64.b64decode(vals.get("datas"))
        mimetype = guess_mimetype(im_bytes)
        if mimetype not in MIMETYPES:
            raise UserError(
                "The file is not an valid mimetype for block document")
        if mimetype == "application/pdf":
            datas = vals.get("datas")
            if "index_content" in vals:
                index_content = vals.get("index_content")
            else:
                index_content = ""
            return datas, index_content
        else:
            return self._crop_document(im_bytes)

    def _crop_document(self, image):
        ocr_text = ""
        if image:
            im_arr = np.frombuffer(image, dtype=np.uint8)
            img = cv2.imdecode(im_arr, flags=cv2.IMREAD_COLOR)
            norm_img = np.zeros((img.shape[0], img.shape[1]))
            img = cv2.normalize(img, norm_img, 0, 255, cv2.NORM_MINMAX)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            thresh = cv2.threshold(gray, 190, 255, cv2.THRESH_BINARY)[1]
            kernel = np.ones((7,7), np.uint8)
            morph = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            kernel = np.ones((9,9), np.uint8)
            morph = cv2.morphologyEx(morph, cv2.MORPH_ERODE, kernel)
            contours = cv2.findContours(
                morph, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
            contours = contours[0] if len(contours) == 2 else contours[1]
            area_thresh = 0
            for c in contours:
                area = cv2.contourArea(c)
                if area > area_thresh:
                    area_thresh = area
                    big_contour = c
            x,y,w,h = cv2.boundingRect(big_contour)
            mask = np.zeros_like(gray)
            mask = cv2.merge([mask,mask,mask])
            cv2.drawContours(
                mask, [big_contour], -1, (255, 255, 255), cv2.FILLED)
            result1 = img.copy()
            result1 = cv2.bitwise_and(result1, mask)
            result2 = result1[y:y+h, x:x+w]
            result3 = self._correct_skew(result2)
            ocr_text = pytesseract.image_to_string(result3, lang="spa")
            pil_img = Image.fromarray(result3)
            buff = BytesIO()
            pil_img.save(buff, format="JPEG")
            image = base64.b64encode(buff.getvalue()).decode("utf-8")
        return image, ocr_text

    def _correct_skew(self, image, delta=1, limit=5):
        def determine_score(arr, angle):
            data = rotate(arr, angle, reshape=False, order=0)
            histogram = np.sum(data, axis=1, dtype=float)
            score = np.sum((histogram[1:] - histogram[:-1]) ** 2, dtype=float)
            return histogram, score

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        thresh = cv2.threshold(
            gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

        scores = []
        angles = np.arange(-limit, limit + delta, delta)
        for angle in angles:
            histogram, score = determine_score(thresh, angle)
            scores.append(score)

        best_angle = angles[scores.index(max(scores))]

        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, best_angle, 1.0)
        corrected = cv2.warpAffine(
            image, M, (w, h), flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE)

        return corrected
