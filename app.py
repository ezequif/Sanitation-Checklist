from flask import Flask, render_template, request, send_file
from flask_wtf import FlaskForm
from wtforms import StringField, DateField, SubmitField, BooleanField
from wtforms.validators import DataRequired
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from flask_mail import Mail, Message
import base64
from io import BytesIO
from reportlab.lib.utils import ImageReader

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'

# Configure Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'ezequif@gmail.com'
app.config['MAIL_PASSWORD'] = 'klph vzak gvme sytl'
app.config['MAIL_DEFAULT_SENDER'] = 'ezequif@gmail.com'


mail = Mail(app)


class SanitationForm(FlaskForm):
    employee_name = StringField('Employee Name', validators=[DataRequired()])
    date = DateField('Date', format='%Y-%m-%d', validators=[DataRequired()])

    # Full Task List
    empty_trash_bins = BooleanField("Empty trash bins")
    items_labeled_properly = BooleanField("Items labeled and put away properly")
    sweep_floor_under_racks = BooleanField("Sweep floor and under racks")
    check_webbing_rollup_doors = BooleanField(
        "Check for webbing under the seal outside roll-up doors (Open The Doors and Check)")
    dusting_cobweb_removal = BooleanField("Dusting and cobweb removal")
    dust_light_fixtures = BooleanField("Dust light fixtures and exit signs (Test Emergency Light Functions)")
    inspect_fans_screens = BooleanField("Visually inspect fans and screens")
    raw_materials_banded = BooleanField(
        "Are all raw materials (level 2 and up “racking”) properly banded/shrink wrapped?")
    materials_proper_place = BooleanField("Are all materials in their proper place? (same RM’s on the same pallet)")
    hazardous_materials_exits = BooleanField(
        "Are any cleaning supplies (Hazardous Materials) being stored by emergency exits or stairs?")
    racking_labeled = BooleanField("Is all racking properly labeled?")
    correct_item_locations = BooleanField("Are the correct items in the correct locations?")
    raw_items_closed = BooleanField("Are all items (Raws) properly closed?")
    pallets_labeled = BooleanField("Are all pallets properly labeled?")
    allergens_designated_area = BooleanField("Are all allergens in designated area?")
    exits_clear = BooleanField("Are all exits clear of obstruction?")
    kosher_items_only = BooleanField("Are there only kosher items in this warehouse?")
    finished_product_condition = BooleanField(
        "Are all finished product containers (Ready to Ship) damaged/unlabeled boxes etc.")
    lights_working = BooleanField("Are all lights working properly?")
    quarantined_items_status = BooleanField("Have quarantined items been disposed of or re-worked?")
    electrical_panels_clear = BooleanField("Are any electrical panels obstructed?")
    fifo_followed = BooleanField(
        "Is FIFO being followed? If not, have you brought this to the attention of management?")
    equipment_turned_off = BooleanField(
        "Is all equipment (Wrapper/Powered Equipment “Lifts”) turned off and plugged in?")

    manager_signature = StringField('Manager Signature (Base64)')
    peer_signature = StringField('Peer Review Signature (Base64)')
    submit = SubmitField('Submit')


@app.route("/", methods=["GET", "POST"])
def index():
    form = SanitationForm()
    if form.validate_on_submit():
        data = {
            "employee_name": form.employee_name.data,
            "date": form.date.data.strftime('%Y-%m-%d'),
            "tasks": {field.label.text: getattr(form, field.name).data for field in form if
                      isinstance(field, BooleanField)},
            "manager_signature": form.manager_signature.data,
            "peer_signature": form.peer_signature.data
        }

        pdf = generate_pdf(data)

        # Send Email
        msg = Message("Sanitation Checklist Submission", recipients=["ezequif@gmail.com"])
        msg.body = f"Sanitation checklist submitted by {data['employee_name']} on {data['date']}"
        msg.attach("sanitation_checklist.pdf", "application/pdf", pdf.read())
        mail.send(msg)

        return "Form submitted successfully!"

    return render_template("form.html", form=form)


def generate_pdf(data):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.setTitle("Sanitation Checklist")

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(200, 750, "Sanitation Checklist")

    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, 720, f"Employee Name: {data['employee_name']}")
    pdf.drawString(50, 700, f"Date: {data['date']}")

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, 670, "Sanitation Tasks:")

    pdf.setFont("Helvetica", 10)
    y = 650  # Start position for tasks
    min_y_position = 200  # Ensure space for footer and signatures

    for task, checked in data['tasks'].items():
        pdf.drawString(70, y, f"[{'X' if checked else ' '}] {task}")
        y -= 20  # Move down

        # Prevent tasks from overlapping signatures
        if y < min_y_position:
            break

    # Adjust position for signatures if needed
    y = max(y, 180)

    # Manager Signature
    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, y - 40, "Manager Signature:")
    if data['manager_signature']:
        signature_data = base64.b64decode(data['manager_signature'].split(',')[1])
        signature_image = ImageReader(BytesIO(signature_data))
        pdf.drawImage(signature_image, 50, y - 90, width=200, height=50)

    # Peer Signature
    pdf.drawString(300, y - 40, "Peer Review Signature:")
    if data['peer_signature']:
        signature_data = base64.b64decode(data['peer_signature'].split(',')[1])
        signature_image = ImageReader(BytesIO(signature_data))
        pdf.drawImage(signature_image, 300, y - 90, width=200, height=50)

    # **Footer (Fixed at the bottom)**
    footer_y_position = 40
    pdf.setFont("Helvetica", 8)
    pdf.drawString(50, footer_y_position, "CONFIDENTIAL: PROPERTY OF BLUE MOUNTAIN FLAVORS")
    pdf.drawString(50, footer_y_position - 15,
                   "Manual 2.2 SOP-Warehousing Form 2.2B-1 Daily Sanitation Checklist for Buildings 1-2")
    pdf.drawString(50, footer_y_position - 30,
                   "Effective Date: 10/15/2018 | Revised: 2023.3.22 (Jon S.) | Reviewed: 2024.12.4 (Jon S.)")

    pdf.save()
    buffer.seek(0)
    return buffer


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

