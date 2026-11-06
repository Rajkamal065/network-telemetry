"""
Generate native PowerPoint presentation (.pptx)
Academic Submittable 6-Slide Deck (Zero AI/prep markers)
Requirements: pip install python-pptx
Run: python generate_pptx.py
"""
import sys, os

try:
    from pptx import Presentation
    from pptx.util import Inches, Pt
    from pptx.dml.color import RGBColor
    from pptx.enum.text import PP_ALIGN
    from pptx.enum.shapes import MSO_SHAPE
except ImportError:
    print("python-pptx is not installed yet.")
    print("To generate the native .pptx file, run:")
    print("    pip install python-pptx")
    print("    python generate_pptx.py")
    sys.exit(0)

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
blank_layout = prs.slide_layouts[6]

NAVY = RGBColor(11, 47, 100)
RED = RGBColor(185, 28, 28)
BLUE = RGBColor(2, 132, 199)
GREEN = RGBColor(21, 128, 61)
PURPLE = RGBColor(124, 58, 237)
DARK = RGBColor(30, 41, 59)
MUTED = RGBColor(100, 116, 139)

def add_header(slide, title, page_num):
    txBox = slide.shapes.add_textbox(Inches(0.6), Inches(0.4), Inches(12.1), Inches(0.8))
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(26)
    p.font.bold = True
    p.font.color.rgb = NAVY

    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.6), Inches(1.15), Inches(12.1), Inches(0.03))
    line.fill.solid()
    line.fill.fore_color.rgb = NAVY
    line.line.color.rgb = NAVY

    footerBox = slide.shapes.add_textbox(Inches(0.6), Inches(6.9), Inches(10), Inches(0.4))
    p = footerBox.text_frame.paragraphs[0]
    p.text = "CS331 Computer Networks  |  Team T018  |  Network Telemetry Framework (RFC 9232)"
    p.font.size = Pt(9.5)
    p.font.color.rgb = MUTED

    numBox = slide.shapes.add_textbox(Inches(12.0), Inches(6.9), Inches(0.8), Inches(0.4))
    p = numBox.text_frame.paragraphs[0]
    p.text = f"{page_num}/6"
    p.font.size = Pt(10)
    p.font.color.rgb = MUTED

# ==========================================
# SLIDE 1: Title
# ==========================================
s1 = prs.slides.add_slide(blank_layout)
bg1 = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
bg1.fill.solid()
bg1.fill.fore_color.rgb = NAVY
bg1.line.color.rgb = NAVY

tbox = s1.shapes.add_textbox(Inches(1.0), Inches(1.4), Inches(11.3), Inches(2.5))
tf = tbox.text_frame
tf.word_wrap = True

p1 = tf.paragraphs[0]
p1.text = "Network Telemetry Framework"
p1.alignment = PP_ALIGN.CENTER
p1.font.size = Pt(40)
p1.font.bold = True
p1.font.color.rgb = RGBColor(255, 255, 255)

p2 = tf.add_paragraph()
p2.text = "Real-Time Network Performance Monitoring  |  RFC 9232"
p2.alignment = PP_ALIGN.CENTER
p2.font.size = Pt(17)
p2.font.color.rgb = RGBColor(147, 197, 253)

p3 = tf.add_paragraph()
p3.text = "\nCS331 Computer Networks  |  Final Project Presentation"
p3.alignment = PP_ALIGN.CENTER
p3.font.size = Pt(13)
p3.font.color.rgb = RGBColor(203, 213, 225)

members = [
    ("Avinash Reddy", "23110123"),
    ("Gella Jayarama Krishna", "23110115"),
    ("Sowpati Raj Kamal", "23110319"),
    ("Jangam Sanjay", "23110144"),
    ("Pulakurthi Manohar", "23110259"),
    ("Yalla Sai Teja", "23110366"),
]
for i, (name, roll) in enumerate(members):
    col, row = i % 3, i // 3
    bx = Inches(1.8 + col * 3.3)
    by = Inches(4.2 + row * 1.1)
    card = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, bx, by, Inches(3.1), Inches(0.85))
    card.fill.solid()
    card.fill.fore_color.rgb = RGBColor(15, 42, 82)
    card.line.color.rgb = RGBColor(30, 58, 110)
    ctf = card.text_frame
    ctf.word_wrap = True
    cp1 = ctf.paragraphs[0]
    cp1.text = name
    cp1.alignment = PP_ALIGN.CENTER
    cp1.font.size = Pt(11)
    cp1.font.bold = True
    cp1.font.color.rgb = RGBColor(255, 255, 255)
    cp2 = ctf.add_paragraph()
    cp2.text = roll
    cp2.alignment = PP_ALIGN.CENTER
    cp2.font.size = Pt(10)
    cp2.font.color.rgb = RGBColor(125, 211, 252)

# ==========================================
# SLIDE 2: Project Motivation & Approach
# ==========================================
s2 = prs.slides.add_slide(blank_layout)
add_header(s2, "Project Motivation & Technical Approach", 2)

leftBox = s2.shapes.add_textbox(Inches(0.6), Inches(1.3), Inches(5.8), Inches(5.4))
tf = leftBox.text_frame
tf.word_wrap = True

p = tf.paragraphs[0]
p.text = "The Challenge: Periodic SNMP Polling"
p.font.size = Pt(15)
p.font.bold = True
p.font.color.rgb = RED

p = tf.add_paragraph()
p.text = "- Traditional monitoring tools poll network devices on fixed multi-minute intervals (e.g., 5 min).\n- Transient congestion bursts and micro-spikes are smoothed out in long averages.\n- Centralized polling introduces CPU load and management overhead as network size scales.\n"
p.font.size = Pt(10.5)
p.font.color.rgb = DARK

p = tf.add_paragraph()
p.text = "The Solution: Continuous Push Telemetry (RFC 9232)"
p.font.size = Pt(15)
p.font.bold = True
p.font.color.rgb = GREEN

p = tf.add_paragraph()
p.text = "- Edge devices stream performance measurements proactively over persistent gRPC channels.\n- High-frequency telemetry generation (2 s interval) exposes transient anomalies in seconds.\n- Push model eliminates polling latency and reduces device CPU overhead.\n"
p.font.size = Pt(10.5)
p.font.color.rgb = DARK

p = tf.add_paragraph()
p.text = "Target Performance Metrics:"
p.font.size = Pt(13)
p.font.bold = True
p.font.color.rgb = NAVY

p = tf.add_paragraph()
p.text = "1. Bandwidth Utilization: Real-time link capacity consumption (0% to 100%)\n2. Throughput Rates: Ingress and egress bitrates in Mbit/s\n3. TCP Connection Latency: Time required to establish a TCP connection to a configured remote server\n4. Interface Health: Monitoring packet errors, discards, and dropped frames"
p.font.size = Pt(10)
p.font.color.rgb = DARK

rightBox = s2.shapes.add_textbox(Inches(6.8), Inches(1.3), Inches(5.9), Inches(5.4))
tf = rightBox.text_frame
tf.word_wrap = True

p = tf.paragraphs[0]
p.text = "Tools & Core Technologies"
p.font.size = Pt(15)
p.font.bold = True
p.font.color.rgb = BLUE

tools = [
    "Python 3.12: Core runtime powering backend services, agents, and test harness.",
    "gRPC & Protobuf: Streaming transport encoding metrics in compact 72-byte payloads.",
    "FastAPI & Uvicorn: Asynchronous REST backend serving real-time API queries.",
    "SQLite Database: Embedded persistence layer with Write-Ahead Logging (WAL) mode.",
    "psutil: Operating-system interface sampling physical host network statistics.",
    "HTML5 Canvas: Hardware-accelerated browser rendering for real-time charts."
]
for t in tools:
    p = tf.add_paragraph()
    p.text = "• " + t
    p.font.size = Pt(10.5)
    p.font.color.rgb = DARK

p = tf.add_paragraph()
p.text = "\nKey Project Deliverables:"
p.font.size = Pt(14)
p.font.bold = True
p.font.color.rgb = NAVY

delivs = [
    "1. Distributed edge agents supporting physical host and simulated network nodes",
    "2. Asynchronous backend ingestion pipeline with decoupled storage queue",
    "3. Threshold-based alerting engine with anti-flapping hysteresis logic",
    "4. Real-time web dashboard, REST query APIs, and CSV/JSON export capability",
    "5. Automated unit and integration tests covering ingestion, alert logic, APIs and agent behavior"
]
for d in delivs:
    p = tf.add_paragraph()
    p.text = "• " + d
    p.font.size = Pt(10)
    p.font.color.rgb = DARK

# ==========================================
# SLIDE 3: System Architecture
# ==========================================
s3 = prs.slides.add_slide(blank_layout)
add_header(s3, "System Architecture & Functional Pipeline", 3)

if os.path.exists("report_p2_img1.png"):
    s3.shapes.add_picture("report_p2_img1.png", Inches(0.6), Inches(1.4), width=Inches(6.8))

archBox = s3.shapes.add_textbox(Inches(7.7), Inches(1.4), Inches(5.0), Inches(5.2))
tf = archBox.text_frame
tf.word_wrap = True
p = tf.paragraphs[0]
p.text = "Architectural Highlights:"
p.font.size = Pt(15)
p.font.bold = True
p.font.color.rgb = NAVY

steps = [
    "1. Data Collection Layer:\nDual-collector design: physical host network stats via psutil and TCP latency probing, combined with 5 simulated routers and switches modeling enterprise loads.\n",
    "2. Transport Layer (gRPC):\nPersistent HTTP/2 client stream (Telemetry.Stream). Telemetry messages are encoded in compact Protocol Buffers (~72 bytes) and streamed at 2-second intervals.\n",
    "3. Ingestion & Storage Layer:\nAn in-memory queue (capacity 20,000) decouples network reception from disk. SQLite persists telemetry in 500-record batches using Write-Ahead Logging (WAL).\n",
    "4. Alerting & Visualization Layer:\nHysteresis state machine evaluates thresholds, triggering alerts after 2 breach cycles. Real-time HTML5 canvas dashboard and REST APIs expose telemetry."
]
for s in steps:
    p = tf.add_paragraph()
    p.text = s
    p.font.size = Pt(10.5)
    p.font.color.rgb = DARK

# ==========================================
# SLIDE 4: Dashboard
# ==========================================
s4 = prs.slides.add_slide(blank_layout)
add_header(s4, "Real-Time Telemetry Dashboard", 4)

if os.path.exists("report_p5_img2.jpeg"):
    s4.shapes.add_picture("report_p5_img2.jpeg", Inches(0.6), Inches(1.4), width=Inches(7.0))

dashBox = s4.shapes.add_textbox(Inches(7.9), Inches(1.4), Inches(4.8), Inches(5.2))
tf = dashBox.text_frame
tf.word_wrap = True
p = tf.paragraphs[0]
p.text = "Dashboard Capabilities:"
p.font.size = Pt(15)
p.font.bold = True
p.font.color.rgb = BLUE

dash_items = [
    "KPI Health Overview:\nInstant summary cards displaying reachable device count, active alerts, aggregated live bitrates, and round-trip latency.\n",
    "Interface Utilization Table:\nTabular monitoring of routers, switches, and hosts with live bitrates, latency, packet loss, and animated utilization gauges.\n",
    "Dynamic Sub-0.1% Precision:\nCorrectly preserves sub-0.1% utilization on idle links rather than rounding down to zero, maintaining telemetry continuity.\n",
    "Canvas Trend Visualizations:\nHardware-accelerated HTML5 canvas line graphs plotting Bandwidth Usage, Latency, and Throughput with smooth 2-second updates.\n",
    "Historical Data Export:\nOne-click CSV export engine generating comprehensive, audit-ready telemetry logs for offline analysis."
]
for item in dash_items:
    p = tf.add_paragraph()
    p.text = "• " + item
    p.font.size = Pt(10)
    p.font.color.rgb = DARK

topoBox = s4.shapes.add_textbox(Inches(0.6), Inches(5.6), Inches(7.0), Inches(1.4))
ttf = topoBox.text_frame
ttf.word_wrap = True
tp1 = ttf.paragraphs[0]
tp1.text = "Experimental Testbed Topology:"
tp1.font.size = Pt(11)
tp1.font.bold = True
tp1.font.color.rgb = GREEN
tp2 = ttf.add_paragraph()
tp2.text = "• 1 Physical Host Node: Live OS network counters sampled via psutil with active TCP connection probing\n• 5 Simulated Network Nodes: 2 core routers, 2 edge switches, 1 branch router with scripted congestion cycles\n• Sampling Cadence: Agents sample every 2 seconds by default (1 second in scalability experiments); dashboard refreshes every 2 seconds"
tp2.font.size = Pt(9.5)
tp2.font.color.rgb = DARK

# ==========================================
# SLIDE 5: Testing & Results
# ==========================================
s5 = prs.slides.add_slide(blank_layout)
add_header(s5, "Experimental Evaluation & Results", 5)

cards = [
    ("400 Devices", "0 Samples Dropped", "400 simulated devices benchmarked with zero telemetry samples dropped by the pipeline.", BLUE),
    ("2.8 Seconds", "Mean Alert Time", "Injected congestion incidents were detected and alerted in an average of 2.8 seconds.", RED),
    ("71% Reduction", "Flapping Suppression", "Hysteresis state machine eliminated transient noise, cutting false alerts from 101/hr to 29.6/hr.", GREEN),
    ("Pytest Suite", "Automated Tests", "Unit and integration tests covering ingestion, alert logic, APIs and agent behavior.", PURPLE),
]
for i, (bignum, label, desc, col) in enumerate(cards):
    card = s5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.6 + i * 3.1), Inches(1.3), Inches(2.85), Inches(1.2))
    card.fill.solid()
    card.fill.fore_color.rgb = RGBColor(248, 250, 252)
    card.line.color.rgb = RGBColor(203, 213, 225)
    ctf = card.text_frame
    ctf.word_wrap = True
    cp1 = ctf.paragraphs[0]
    cp1.text = bignum
    cp1.font.size = Pt(20)
    cp1.font.bold = True
    cp1.font.color.rgb = col
    cp2 = ctf.add_paragraph()
    cp2.text = label + "\n" + desc
    cp2.font.size = Pt(9.5)
    cp2.font.color.rgb = DARK

if os.path.exists("report_p5_img1.png"):
    s5.shapes.add_picture("report_p5_img1.png", Inches(0.6), Inches(2.7), width=Inches(5.8))

if os.path.exists("report_p6_img1.png"):
    s5.shapes.add_picture("report_p6_img1.png", Inches(6.8), Inches(2.7), width=Inches(5.9))

sumBox = s5.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.6), Inches(5.8), Inches(12.1), Inches(0.9))
sumBox.fill.solid()
sumBox.fill.fore_color.rgb = NAVY
sumBox.line.color.rgb = NAVY
stf = sumBox.text_frame
stf.word_wrap = True
p = stf.paragraphs[0]
p.text = "Summary of Experimental Findings:"
p.font.size = Pt(12)
p.font.bold = True
p.font.color.rgb = RGBColor(255, 255, 255)
p2 = stf.add_paragraph()
p2.text = "1. High Throughput & Zero Loss: The decoupled queue architecture sustains 400 samples/s with zero dropped telemetry samples and p95 latency under 26 ms.\n2. Alert Reliability: Hysteresis evaluation accurately isolates sustained congestion from transient noise, resolving automatically post-recovery."
p2.font.size = Pt(9.5)
p2.font.color.rgb = RGBColor(147, 197, 253)

# ==========================================
# SLIDE 6: Summary & Conclusion
# ==========================================
s6 = prs.slides.add_slide(blank_layout)
bg6 = s6.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
bg6.fill.solid()
bg6.fill.fore_color.rgb = NAVY
bg6.line.color.rgb = NAVY

leftBox6 = s6.shapes.add_textbox(Inches(0.6), Inches(0.8), Inches(5.8), Inches(6.0))
tf = leftBox6.text_frame
tf.word_wrap = True
p = tf.paragraphs[0]
p.text = "Summary & Conclusions"
p.font.size = Pt(22)
p.font.bold = True
p.font.color.rgb = RGBColor(255, 255, 255)

concs = [
    "Delivered Pipeline: A modular network telemetry framework implementing RFC 9232 principles to collect, transport, store, and visualize performance metrics in real time.",
    "High-Speed Streaming: Replaces legacy SNMP pull polling with lightweight gRPC HTTP/2 push streaming using compact Protocol Buffers (~72 bytes/sample).",
    "Empirically Validated: Validated through comprehensive Pytest test suite, 400-device scalability benchmarking, and scripted fault-injection scenarios.",
    "Scope & System Boundaries: Implemented as an educational prototype using physical laptop OS metrics (psutil) and simulated enterprise switches/routers without proprietary ASIC hardware."
]
for item in concs:
    p = tf.add_paragraph()
    p.text = "• " + item
    p.font.size = Pt(10)
    p.font.color.rgb = RGBColor(203, 213, 225)

p = tf.add_paragraph()
p.text = "\nCore Contribution:"
p.font.size = Pt(12)
p.font.bold = True
p.font.color.rgb = RGBColor(252, 165, 165)

p = tf.add_paragraph()
p.text = "Demonstrates near-real-time network monitoring with 2-second telemetry sampling and low-latency gRPC delivery."
p.font.size = Pt(10)
p.font.color.rgb = RGBColor(203, 213, 225)

p = tf.add_paragraph()
p.text = "\nFuture Work:"
p.font.size = Pt(12)
p.font.bold = True
p.font.color.rgb = RGBColor(125, 211, 252)

futures = [
    "- Integration with physical network switching hardware (Cisco / Juniper)",
    "- Standard gNMI (gRPC Network Management Interface) schema support",
    "- Mutual TLS (mTLS) transport encryption and token authentication",
    "- Scalable time-series storage backend (TimescaleDB / InfluxDB)"
]
for f in futures:
    p = tf.add_paragraph()
    p.text = f
    p.font.size = Pt(9.5)
    p.font.color.rgb = RGBColor(148, 163, 184)

rightBox6 = s6.shapes.add_textbox(Inches(7.0), Inches(0.8), Inches(5.7), Inches(6.0))
tf = rightBox6.text_frame
tf.word_wrap = True
p = tf.paragraphs[0]
p.text = "Thank You!"
p.font.size = Pt(36)
p.font.bold = True
p.font.color.rgb = RGBColor(255, 255, 255)

p = tf.add_paragraph()
p.text = "Questions & Discussion\n"
p.font.size = Pt(14)
p.font.color.rgb = RGBColor(147, 197, 253)

p = tf.add_paragraph()
p.text = "Project Code & Reproducibility:"
p.font.size = Pt(12)
p.font.bold = True
p.font.color.rgb = RGBColor(125, 211, 252)

p = tf.add_paragraph()
p.text = "Repository: https://github.com/Rajkamal065/network-telemetry"
p.font.size = Pt(11)
p.font.color.rgb = RGBColor(255, 255, 255)

p = tf.add_paragraph()
p.text = "Automated Test Suite: python -m pytest tests/ -v (verified unit & integration tests)\n"
p.font.size = Pt(10)
p.font.color.rgb = RGBColor(74, 222, 128)

p = tf.add_paragraph()
p.text = "Team T018  |  CS331 Computer Networks:"
p.font.size = Pt(12)
p.font.bold = True
p.font.color.rgb = RGBColor(148, 163, 184)

for name, roll in members:
    p = tf.add_paragraph()
    p.text = f"• {name} ({roll})"
    p.font.size = Pt(10.5)
    p.font.color.rgb = RGBColor(255, 255, 255)

prs.save("Network_Telemetry_Presentation.pptx")
print("Successfully generated Network_Telemetry_Presentation.pptx with 6 submittable slides!")
