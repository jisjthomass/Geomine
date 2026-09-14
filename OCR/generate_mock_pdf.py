from fpdf import FPDF

pdf = FPDF()
pdf.add_page()
pdf.set_font("Arial", size=12)

report_text = """
DAILY DRILLING & INCIDENT REPORT
Date: 2024-10-14
Operator: GeoMind Energy Corp
--------------------------------------------------
Well Information
Well ID: GEO-DEEP-09
Latitude: 28.5356
Longitude: 77.1242
Current Depth: 3250.5 m
Target Formation: Lower Barail Sandstone

--------------------------------------------------
Incident Details
Event Type: Severe Mud Loss
Time of Incident: 14:30 hrs
Event Depth: 3110.0 m
Formation: Fractured Limestone

Description of Event:
While drilling ahead at 3110.0m, the rig experienced a total loss of mud circulation. 
Suspect encountered a highly fractured limestone zone. Pumped 100 bbls of Loss Circulation 
Material (LCM) pill. Waited on LCM to cure. Circulation partially regained after 4 hours.

NPT (Non-Productive Time) Tracking
NPT Duration: 240 mins
NPT Category: Fluid Loss

--------------------------------------------------
Underground Infrastructure Survey
Warning: Seismic scans indicate a pre-existing high-pressure water Aquifer nearby.
Infrastructure ID: AQ-774-B
Infrastructure Lat: 28.5360
Infrastructure Long: 77.1250
Depth: 3150.0 m
Type: Aquifer
"""

for line in report_text.split('\n'):
    pdf.cell(200, 7, txt=line, ln=True, align='L')

pdf.output("OCR/mock_incident_report.pdf")
print("Successfully generated OCR/mock_incident_report.pdf")
