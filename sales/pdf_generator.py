import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_LEFT


def generate_deal_pdf(deal):
    """
    Generates a professional PDF Invoice (if Won) or Quotation (if Proposal/New)
    for a Deal record in INR currency. Returns raw bytes.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    
    # Custom Typography Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#1e3a8a') # Deep Brand Blue
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#64748b')
    )

    h2_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=colors.HexColor('#0f172a')
    )

    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#334155')
    )

    right_body = ParagraphStyle(
        'RightBody',
        parent=body_style,
        alignment=TA_RIGHT
    )

    right_bold = ParagraphStyle(
        'RightBold',
        parent=body_style,
        fontName='Helvetica-Bold',
        alignment=TA_RIGHT
    )

    elements = []

    # 1. Header (Company Info & Document Title)
    is_invoice = (deal.stage == 'Won')
    doc_type = "TAX INVOICE" if is_invoice else "COMMERCIAL QUOTATION"
    doc_code = f"INV-{deal.deal_id}" if is_invoice else f"QUO-{deal.deal_id}"

    header_data = [
        [
            Paragraph("<b>SmartCRM Solutions Pvt. Ltd.</b><br/>"
                      "GSTIN: 27AAACS1429B1Z8 | CIN: U72200MH2024PTC123456<br/>"
                      "Plot 42, Tech Cyber Park, Bandra Kurla Complex (BKC)<br/>"
                      "Mumbai, Maharashtra - 400051<br/>"
                      "support@smartcrm.local | +91 99000 11000", body_style),
            Paragraph(f"<font color='#2563eb'><b>{doc_type}</b></font><br/>"
                      f"<b>Doc #:</b> {doc_code}<br/>"
                      f"<b>Date:</b> {datetime.now().strftime('%d-%m-%Y')}<br/>"
                      f"<b>Ref Deal:</b> {deal.deal_id}<br/>"
                      f"<b>Currency:</b> INR (&#8377;)", right_body)
        ]
    ]

    header_table = Table(header_data, colWidths=[300, 220])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 15))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#2563eb'), spaceAfter=15))

    # 2. Bill To & Deal Context Box
    customer = deal.customer
    bill_to_data = [
        [
            Paragraph("<b>BILLED TO / CLIENT DETAILS:</b>", h2_style),
            Paragraph("<b>ACCOUNT & PROJECT SPECIFICATION:</b>", h2_style)
        ],
        [
            Paragraph(f"<b>{customer.full_name}</b><br/>"
                      f"{customer.company_name or 'Independent Enterprise'}<br/>"
                      f"{customer.address or ''}<br/>"
                      f"{customer.city or ''} {customer.state or ''} - {customer.postal_code or ''}<br/>"
                      f"<b>Email:</b> {customer.email}<br/>"
                      f"<b>Phone:</b> {customer.phone}", body_style),
            Paragraph(f"<b>Deal Title:</b> {deal.title}<br/>"
                      f"<b>Stage:</b> {deal.stage}<br/>"
                      f"<b>Account Rep:</b> {deal.assigned_to.display_name}<br/>"
                      f"<b>Target Date:</b> {deal.expected_closing_date.strftime('%d-%m-%Y') if deal.expected_closing_date else 'Immediate'}<br/>"
                      f"<b>Payment Terms:</b> Net 30 Days", body_style)
        ]
    ]
    bill_table = Table(bill_to_data, colWidths=[270, 250])
    bill_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    elements.append(bill_table)
    elements.append(Spacer(1, 20))

    # 3. Itemized Products / Services Table
    deal_val = float(deal.deal_value or 0)
    cgst = deal_val * 0.09
    sgst = deal_val * 0.09
    total_val = deal_val + cgst + sgst

    item_headers = [
        Paragraph("<b>#</b>", body_style),
        Paragraph("<b>Item / Scope Description</b>", body_style),
        Paragraph("<b>SAC/HSN</b>", body_style),
        Paragraph("<b>Qty</b>", body_style),
        Paragraph("<b>Rate (₹)</b>", right_bold),
        Paragraph("<b>Amount (₹)</b>", right_bold),
    ]

    item_row = [
        Paragraph("1", body_style),
        Paragraph(f"<b>{deal.title}</b><br/>"
                  f"<font color='#64748b' size='8'>{deal.notes or 'Enterprise software license, onboarding implementation, configuration, and priority technical support.'}</font>", body_style),
        Paragraph("998313", body_style),
        Paragraph("1", body_style),
        Paragraph(f"{deal_val:,.2f}", right_body),
        Paragraph(f"{deal_val:,.2f}", right_body),
    ]

    items_data = [
        item_headers,
        item_row,
        # Summary Rows
        [Paragraph("", body_style), Paragraph("", body_style), Paragraph("", body_style), Paragraph("", body_style), Paragraph("Taxable Value:", right_bold), Paragraph(f"{deal_val:,.2f}", right_body)],
        [Paragraph("", body_style), Paragraph("", body_style), Paragraph("", body_style), Paragraph("", body_style), Paragraph("CGST (9.0%):", right_bold), Paragraph(f"{cgst:,.2f}", right_body)],
        [Paragraph("", body_style), Paragraph("", body_style), Paragraph("", body_style), Paragraph("", body_style), Paragraph("SGST (9.0%):", right_bold), Paragraph(f"{sgst:,.2f}", right_body)],
        [Paragraph("", body_style), Paragraph("", body_style), Paragraph("", body_style), Paragraph("", body_style), Paragraph("<b>TOTAL (₹):</b>", right_bold), Paragraph(f"<b>{total_val:,.2f}</b>", right_bold)],
    ]

    items_table = Table(items_data, colWidths=[25, 235, 60, 30, 85, 85])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563eb')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, 1), 0.5, colors.HexColor('#e2e8f0')),
        ('LINEBELOW', (0, 1), (-1, 1), 1, colors.HexColor('#cbd5e1')),
        ('BACKGROUND', (4, -1), (5, -1), colors.HexColor('#eff6ff')),
        ('BOX', (4, -1), (5, -1), 1, colors.HexColor('#2563eb')),
    ]))
    # White text for header paragraph elements
    for i in range(len(item_headers)):
        items_table.setStyle(TableStyle([
            ('TEXTCOLOR', (i, 0), (i, 0), colors.white)
        ]))

    elements.append(items_table)
    elements.append(Spacer(1, 20))

    # 4. Bank Account & Authorized Signature
    bank_and_sign_data = [
        [
            Paragraph("<b>PAYMENT INFORMATION:</b><br/>"
                      "Bank: <b>HDFC Bank Ltd.</b><br/>"
                      "Account Name: <b>SmartCRM Solutions Pvt Ltd</b><br/>"
                      "Account No: <b>50200012345678</b><br/>"
                      "IFSC Code: <b>HDFC0001234</b><br/>"
                      "UPI ID: <b>smartcrm@okhdfcbank</b>", body_style),
            Paragraph("<b>FOR SMARTCRM SOLUTIONS PVT LTD</b><br/><br/><br/>"
                      "____________________________________<br/>"
                      "<b>Authorized Signatory</b><br/>"
                      "<font size='8' color='#64748b'>Digitally generated corporate document</font>", right_body)
        ]
    ]

    bank_sign_table = Table(bank_and_sign_data, colWidths=[280, 240])
    bank_sign_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    elements.append(bank_sign_table)
    elements.append(Spacer(1, 25))

    # 5. Bottom Legal Notice
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#e2e8f0'), spaceAfter=8))
    elements.append(Paragraph(
        "<font size='8' color='#94a3b8'>Terms & Conditions: Subject to Mumbai jurisdiction. Payments made after due date attract 18% p.a. interest. This is a computer-generated document and is legally binding under the Information Technology Act, 2000.</font>",
        ParagraphStyle('Disclaimer', parent=styles['Normal'], alignment=TA_CENTER)
    ))

    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf
