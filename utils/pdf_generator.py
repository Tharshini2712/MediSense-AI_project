from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def generate_report(
    filepath,
    patient_type,
    gender,
    age,
    care_level,
    intensity,
    symptoms,
    diseases
    ):

    c = canvas.Canvas(
        filepath,
        pagesize=letter
    )

    y = 750

    c.setFont(
        "Helvetica-Bold",
        18
    )

    c.drawString(
        50,
        y,
        "MediSense AI Health Report"
    )

    y -= 40

    c.setFont(
        "Helvetica",
        12
    )

    c.drawString(
        50,
        y,
        f"Patient Type: {patient_type}"
    )

    y -= 20

    c.drawString(
        50,
        y,
        f"Gender: {gender}"
    )

    y -= 20

    c.drawString(
        50,
        y,
        f"Age: {age}"
    )

    y -= 20

    c.drawString(
        50,
        y,
        f"Care Level: {care_level}"
    )

    y -= 20

    c.drawString(
        50,
        y,
        f"Intensity: {intensity}"
    )

    y -= 40

    c.setFont(
        "Helvetica-Bold",
        14
    )

    c.drawString(
        50,
        y,
        "Symptoms"
    )

    y -= 25

    c.setFont(
        "Helvetica",
        12
    )

    for symptom in symptoms:
        c.drawString(
            70,
            y,
            f"• {symptom}"
        )
        y -= 20

    y -= 10

    c.setFont(
        "Helvetica-Bold",
        14
    )

    c.drawString(
        50,
        y,
        "Predicted Diseases"
    )

    y -= 25

    c.setFont(
        "Helvetica",
        12
    )

    for disease, confidence in diseases:
        c.drawString(
            70,
            y,
            f"{disease} ({confidence}%)"
        )
        y -= 20

    y -= 20

    c.setFont(
        "Helvetica-Bold",
        14
    )

    c.drawString(
        50,
        y,
        "Recommendation"
    )

    y -= 25

    c.setFont(
        "Helvetica",
        12
    )

    c.drawString(
        70,
        y,
        "Consult a healthcare professional for proper diagnosis."
    )

    c.save()
