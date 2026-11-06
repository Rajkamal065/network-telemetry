"""
Network Telemetry Framework (RFC 9232)
Final 6-Slide Submittable Academic Presentation Deck
Clean, formal academic tone suitable for direct submission to professors.
Features:
- Embeds Figures 1, 2, 4 and Dashboard Screenshot from Network_Telemetry_Report_(4).pdf
- Full Team T018 roster with Roll numbers matching project report
- Exactly 6 slides, strictly professional terminology, zero AI/prep markers
Run: python generate_presentation_pdf.py
"""
import pymupdf, os

def C(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) / 255.0 for i in (0, 2, 4))

NAVY    = C("0b2f64")
RED     = C("b91c1c")
RED_L   = C("fee2e2")
BLUE    = C("0284c7")
BLUE_L  = C("e0f2fe")
GREEN   = C("15803d")
GREEN_L = C("dcfce7")
PURPLE  = C("6d28d9")
PURP_L  = C("ede9fe")
AMBER   = C("b45309")
DARK    = C("1e293b")
MID     = C("475569")
MUTED   = C("94a3b8")
WHITE   = (1.0, 1.0, 1.0)
OFFWHT  = C("f8fafc")
BORDER  = C("cbd5e1")

W, H = 1000, 562  # 16:9 widescreen layout

def rr(p, x, y, w, h, fill, border=None, bw=1):
    r = pymupdf.Rect(x, y, x + w, y + h)
    p.draw_rect(r, color=border or fill, fill=fill, width=bw, radius=0.08)

def line(p, x1, y1, x2, y2, color=BORDER, w=1):
    p.draw_line(pymupdf.Point(x1, y1), pymupdf.Point(x2, y2), color=color, width=w)

def txt(p, x, y, s, fs=12, fn="helv", color=DARK):
    p.insert_text((x, y), s, fontsize=fs, fontname=fn, color=color)

def tbox(p, x, y, w, h, s, fs=11, fn="helv", color=DARK, lh=1.3, align=0):
    return p.insert_textbox(pymupdf.Rect(x, y, x + w, y + h), s,
                            fontsize=fs, fontname=fn, color=color,
                            lineheight=lh, align=align)

def tw(s, fn="helv", fs=12):
    return pymupdf.get_text_length(s, fontname=fn, fontsize=fs)

def centered_txt(p, cx, y, s, fs=12, fn="helv", color=DARK):
    x = cx - tw(s, fn, fs) / 2
    txt(p, x, y, s, fs, fn, color)

def bg(p, full_navy=False):
    if full_navy:
        rr(p, 0, 0, W, H, NAVY)
    else:
        rr(p, 0, 0, W, H, WHITE)
        rr(p, 0, 0, 7, H, NAVY)

def slide_header(p, title, subtitle=None):
    txt(p, 28, 42, title, fs=26, fn="hebo", color=NAVY)
    if subtitle:
        txt(p, 28, 60, subtitle, fs=11.5, fn="helv", color=MUTED)
    line(p, 28, 68, W - 28, 68, color=BORDER, w=1.5)

def slide_footer(p, n, total=6):
    line(p, 28, H - 26, W - 28, H - 26, color=BORDER, w=0.8)
    txt(p, 28, H - 13, "CS331 Computer Networks  |  Team T018  |  Network Telemetry Framework (RFC 9232)",
        fs=8.5, fn="helv", color=MUTED)
    txt(p, W - 45, H - 13, f"{n}/{total}", fs=9.5, fn="hebo", color=MID)

def new_page(doc):
    p = doc.new_page(width=W, height=H)
    bg(p)
    return p

def pill(p, x, y, label, bg_col, tx_col):
    pw = tw(label, "hebo", 9.5) + 16
    rr(p, x, y - 9, pw, 15, bg_col, border=bg_col)
    txt(p, x + 8, y + 2, label, fs=9, fn="hebo", color=tx_col)
    return pw

def bullet_item(p, x, y, w, bold_title, body_text, dot_color=NAVY, title_color=DARK, body_color=MID, title_fs=11, body_fs=9.5, step=46):
    p.draw_circle(pymupdf.Point(x - 8, y - 3.5), 2.5, color=dot_color, fill=dot_color)
    txt(p, x, y, bold_title, fs=title_fs, fn="hebo", color=title_color)
    r = pymupdf.Rect(x, y + 3, x + w, y + 55)
    p.insert_textbox(r, body_text, fontsize=body_fs, fontname="helv", color=body_color, lineheight=1.25)
    return y + step

# =============================================================================
# SLIDE 1: Title Slide
# =============================================================================
def slide1(doc):
    p = doc.new_page(width=W, height=H)
    rr(p, 0, 0, W, H, NAVY)
    rr(p, 0, 0, W, 6, RED)

    t1 = "Network Telemetry Framework"
    centered_txt(p, W / 2, 115, t1, fs=42, fn="hebo", color=WHITE)
    tw1 = tw(t1, "hebo", 42)
    lx = (W - tw1) / 2
    line(p, lx, 124, lx + tw1, 124, RED, 3)

    centered_txt(p, W / 2, 152,
                 "Real-Time Network Performance Monitoring  |  RFC 9232",
                 fs=16, fn="helv", color=C("93c5fd"))

    cw = tw("CS331 Computer Networks  |  Final Project Presentation", "hebo", 12) + 28
    rr(p, (W - cw) / 2, 172, cw, 24, C("1e3a5f"), border=C("3b5998"))
    centered_txt(p, W / 2, 188,
                 "CS331 Computer Networks  |  Final Project Presentation",
                 fs=11.5, fn="hebo", color=C("cbd5e1"))

    members = [
        ("Avinash Reddy",          "23110123"),
        ("Gella Jayarama Krishna", "23110115"),
        ("Sowpati Raj Kamal",      "23110319"),
        ("Jangam Sanjay",          "23110144"),
        ("Pulakurthi Manohar",     "23110259"),
        ("Yalla Sai Teja",         "23110366"),
    ]
    cw2, ch2, cgap = 158, 54, 12
    total_w = 3 * cw2 + 2 * cgap
    x0 = (W - total_w) / 2
    for i, (name, roll) in enumerate(members):
        col, row = i % 3, i // 3
        cx = x0 + col * (cw2 + cgap)
        cy = 225 + row * (ch2 + 10)
        rr(p, cx, cy, cw2, ch2, C("0f2a52"), border=C("1e3a6e"))
        fs_name = 11 if len(name) <= 18 else 10
        nw2 = tw(name, "hebo", fs_name)
        txt(p, cx + (cw2 - nw2) / 2, cy + 22, name, fs=fs_name, fn="hebo", color=WHITE)
        rw2 = tw(roll, "helv", 10)
        txt(p, cx + (cw2 - rw2) / 2, cy + 38, roll, fs=10, fn="helv", color=C("7dd3fc"))

    centered_txt(p, W / 2, 360,
                 "Department of Computer Science & Engineering",
                 fs=12, fn="helv", color=C("94a3b8"))

    rr(p, W - 145, H - 40, 120, 22, C("1e3a5f"), border=C("3b5998"))
    txt(p, W - 138, H - 25, "RFC 9232  |  Team T018", fs=9.5, fn="hebo", color=C("7dd3fc"))

# =============================================================================
# SLIDE 2: Motivation & Project Overview
# =============================================================================
def slide2(doc):
    p = new_page(doc)
    slide_header(p, "Project Motivation & Technical Approach", "Limitations of periodic polling vs. continuous push-based streaming")
    slide_footer(p, 2)

    txt(p, 28, 94, "The Challenge: Periodic SNMP Polling", fs=13.5, fn="hebo", color=RED)
    rr(p, 28, 102, 430, 85, RED_L, border=C("fecaca"))
    tbox(p, 40, 110, 405, 75,
         "- Traditional monitoring polls network devices on fixed multi-minute intervals (e.g., 5 min).\n"
         "- Transient congestion bursts and micro-spikes are smoothed out in long averages.\n"
         "- Centralized polling introduces CPU load and management overhead as network size scales.",
         fs=10, color=DARK, lh=1.3)

    txt(p, 28, 206, "The Solution: Continuous Push Telemetry (RFC 9232)", fs=13.5, fn="hebo", color=GREEN)
    rr(p, 28, 214, 430, 105, GREEN_L, border=C("bbf7d0"))
    tbox(p, 40, 222, 405, 95,
         "- Edge devices stream performance measurements proactively over persistent gRPC channels.\n"
         "- High-frequency telemetry generation (2 s interval) exposes transient anomalies in seconds.\n"
         "- Push model eliminates polling latency and reduces device CPU overhead.\n"
         "- Operates continuously, transporting compact binary Protocol Buffer payloads.",
         fs=10, color=DARK, lh=1.3)

    txt(p, 28, 338, "Target Performance Metrics:", fs=13, fn="hebo", color=NAVY)
    txt(p, 40, 358, "1. Bandwidth Utilization: Real-time link capacity consumption (0% to 100%)", fs=10, fn="helv", color=DARK)
    txt(p, 40, 376, "2. Throughput Rates: Ingress and egress bitrates in Mbit/s", fs=10, fn="helv", color=DARK)
    txt(p, 40, 394, "3. Round-Trip Latency: End-to-end TCP connection response time in milliseconds", fs=10, fn="helv", color=DARK)
    txt(p, 40, 412, "4. Interface Health: Monitoring packet errors, discards, and dropped frames", fs=10, fn="helv", color=DARK)

    line(p, 480, 78, 480, 510, color=BORDER)

    txt(p, 505, 94, "Tools & Core Technologies", fs=13.5, fn="hebo", color=BLUE)

    tools = [
        ("Python 3.12", "Core runtime powering backend services, agents, and test harness."),
        ("gRPC & Protobuf", "High-performance streaming transport encoding metrics in 72-byte payloads."),
        ("FastAPI & Uvicorn", "Asynchronous REST backend serving real-time API queries and dashboard."),
        ("SQLite Database", "Embedded persistence layer with Write-Ahead Logging (WAL) mode."),
        ("psutil", "Operating-system interface sampling physical host network statistics."),
        ("HTML5 Canvas", "Hardware-accelerated browser rendering for real-time time-series charts."),
    ]
    ty = 118
    for name, desc in tools:
        p.draw_circle(pymupdf.Point(515, ty - 3.5), 2.5, color=BLUE, fill=BLUE)
        txt(p, 524, ty, name + ":", fs=10.5, fn="hebo", color=DARK)
        tw_name = tw(name + ":", "hebo", 10.5) + 4
        txt(p, 524 + tw_name, ty, desc, fs=9.5, fn="helv", color=MID)
        ty += 26

    rr(p, 505, 290, W - 28 - 505, 175, OFFWHT, BORDER)
    rr(p, 505, 290, 5, 175, NAVY, NAVY)
    txt(p, 520, 312, "Key Project Deliverables", fs=13, fn="hebo", color=NAVY)
    delivs = [
        "1. Distributed edge agents supporting physical host and simulated network nodes",
        "2. Asynchronous backend ingestion pipeline with decoupled storage queue",
        "3. Threshold-based alerting engine with anti-flapping hysteresis logic",
        "4. Real-time web dashboard, REST query APIs, and CSV/JSON export capability",
        "5. Automated test suite with 30 passing unit and integration test cases",
    ]
    dy = 334
    for d in delivs:
        p.draw_circle(pymupdf.Point(525, dy - 3.5), 2.2, color=NAVY, fill=NAVY)
        txt(p, 534, dy, d, fs=10, fn="helv", color=DARK)
        dy += 24

# =============================================================================
# SLIDE 3: System Architecture
# =============================================================================
def slide3(doc):
    p = new_page(doc)
    slide_header(p, "System Architecture & Functional Pipeline", "End-to-end telemetry architecture mapping to RFC 9232")
    slide_footer(p, 3)

    img_file = "report_p2_img1.png"
    if os.path.exists(img_file):
        rr(p, 26, 83, 525, 355, OFFWHT, BORDER, bw=1.5)
        p.insert_image(pymupdf.Rect(30, 87, 545, 433), filename=img_file)
        txt(p, 130, 452, "Figure 1: End-to-end system architecture from project report",
            fs=10, fn="hebo", color=MID)

    txt(p, 570, 94, "Architectural Highlights:", fs=14, fn="hebo", color=NAVY)

    steps = [
        ("1. Data Collection Layer:",
         "Dual-collector design: physical host network stats via psutil and TCP latency probing, combined with 5 simulated routers and switches modeling enterprise loads.",
         GREEN),
        ("2. Transport Layer (gRPC):",
         "Persistent HTTP/2 client stream (Telemetry.Stream). Telemetry messages are encoded in compact Protocol Buffers (~72 bytes) and streamed at 2-second intervals.",
         BLUE),
        ("3. Ingestion & Storage Layer:",
         "An in-memory queue (capacity 20,000) decouples network reception from disk. SQLite persists telemetry in 500-record batches using Write-Ahead Logging (WAL).",
         RED),
        ("4. Alerting & Visualization Layer:",
         "Hysteresis state machine evaluates thresholds, triggering alerts after 2 breach cycles. Real-time HTML5 canvas dashboard and REST APIs expose telemetry.",
         PURPLE),
    ]
    sy = 118
    for title, desc, col in steps:
        sy = bullet_item(p, 580, sy, 390, title, desc, dot_color=col, step=58)

    rr(p, 570, 430, W - 28 - 570, 44, C("eff6ff"), border=C("bfdbfe"))
    txt(p, 582, 456,
        "RFC 9232 Mapping: Data Generation -> Push Export -> Storage -> Analysis & Visualization",
        fs=9.5, fn="hebo", color=NAVY)

# =============================================================================
# SLIDE 4: Dashboard
# =============================================================================
def slide4(doc):
    p = new_page(doc)
    slide_header(p, "Real-Time Telemetry Dashboard", "Live performance visualization, link capacity tracking, and incident management")
    slide_footer(p, 4)

    img_file = "report_p5_img2.jpeg"
    if os.path.exists(img_file):
        rr(p, 26, 83, 565, 275, OFFWHT, BORDER, bw=1.5)
        p.insert_image(pymupdf.Rect(28, 85, 585, 355), filename=img_file)
        txt(p, 160, 372, "Live Web Dashboard running at http://localhost:8000",
            fs=10, fn="hebo", color=MID)

    txt(p, 615, 94, "Dashboard Capabilities:", fs=14, fn="hebo", color=BLUE)

    dash_bullets = [
        ("KPI Health Overview:",
         "Instant summary cards displaying reachable device count (6/6), active alert counts, total throughput (1.65 Gbit/s), and average latency."),
        ("Interface Utilization Table:",
         "Tabular monitoring of routers, switches, and hosts with live bitrates, round-trip latency, packet loss, and animated utilization gauges."),
        ("Dynamic Sub-0.1% Precision:",
         "Correctly preserves sub-0.1% utilization on idle links rather than rounding down to zero, maintaining telemetry continuity."),
        ("Canvas Trend Visualizations:",
         "Hardware-accelerated HTML5 canvas line graphs plotting Bandwidth Usage, Latency, and Throughput with smooth 2-second updates."),
        ("Historical Data Export:",
         "One-click CSV export engine generating comprehensive, audit-ready telemetry logs for offline analysis in under 0.6 seconds."),
    ]
    dy = 118
    for title, desc in dash_bullets:
        dy = bullet_item(p, 625, dy, 345, title, desc, dot_color=BLUE, step=52)

    rr(p, 26, 395, 560, 85, OFFWHT, BORDER)
    rr(p, 26, 395, 5, 85, GREEN, GREEN)
    txt(p, 38, 415, "Experimental Testbed Topology:", fs=11.5, fn="hebo", color=GREEN)
    txt(p, 38, 434, "- 1 Physical Host Node: Live OS network counters sampled via psutil with active TCP connection probing", fs=9.5, fn="helv", color=DARK)
    txt(p, 38, 452, "- 5 Simulated Network Nodes: 2 core routers, 2 edge switches, 1 branch router with scripted congestion cycles", fs=9.5, fn="helv", color=DARK)
    txt(p, 38, 470, "- Update Cadence: 1-second continuous gRPC push stream; dashboard refreshes every 2 seconds via REST polling", fs=9.5, fn="helv", color=DARK)

# =============================================================================
# SLIDE 5: Testing & Results
# =============================================================================
def slide5(doc):
    p = new_page(doc)
    slide_header(p, "Experimental Evaluation & Results", "Empirical performance benchmarks from the project report (Section VII)")
    slide_footer(p, 5)

    cards = [
        ("400 Devices", "0 Dropped Packets", "Tested with 400 concurrent simulated devices at 1 sample/s with zero data loss.", BLUE),
        ("2.8 Seconds", "Mean Alert Time", "Injected congestion incidents were detected and alerted in an average of 2.8 seconds.", RED),
        ("71% Reduction", "Flapping Suppression", "Hysteresis state machine eliminated transient noise, cutting false alerts from 101/hr to 29.6/hr.", GREEN),
        ("30 / 30 Passed", "Automated Tests", "100% test pass rate across Protobuf schemas, database queues, alert logic, and REST APIs.", PURPLE),
    ]
    card_w = (W - 56 - 3 * 14) / 4
    for i, (bignum, title, desc, col) in enumerate(cards):
        cx = 28 + i * (card_w + 14)
        rr(p, cx, 80, card_w, 98, OFFWHT, BORDER)
        rr(p, cx, 80, card_w, 4, col, col)
        txt(p, cx + 12, 114, bignum, fs=22, fn="hebo", color=col)
        txt(p, cx + 12, 130, title, fs=11, fn="hebo", color=DARK)
        tbox(p, cx + 12, 134, card_w - 20, 42, desc, fs=9.5, fn="helv", color=MID, lh=1.2)

    txt(p, 28, 202, "Experiment E1: Scalability & Throughput (Up to 400 Devices)", fs=11.5, fn="hebo", color=NAVY)
    img_e1 = "report_p5_img1.png"
    if os.path.exists(img_e1):
        rr(p, 26, 208, 465, 175, OFFWHT, BORDER, bw=1)
        p.insert_image(pymupdf.Rect(28, 210, 485, 380), filename=img_e1)
        txt(p, 60, 396, "Figure 2: Offered vs stored throughput, CPU & memory usage, and p95 latency", fs=9, fn="hebo", color=MID)

    txt(p, 508, 202, "Experiment E3: Congestion Alert Detection & Recovery", fs=11.5, fn="hebo", color=NAVY)
    img_e3 = "report_p6_img1.png"
    if os.path.exists(img_e3):
        rr(p, 506, 208, 465, 175, OFFWHT, BORDER, bw=1)
        p.insert_image(pymupdf.Rect(508, 210, 968, 380), filename=img_e3)
        txt(p, 540, 396, "Figure 4: Injected incidents on edge-switch-1 with alert opening windows", fs=9, fn="hebo", color=MID)

    rr(p, 28, 416, W - 56, 62, NAVY, NAVY)
    txt(p, 40, 436, "Summary of Experimental Findings:", fs=11.5, fn="hebo", color=WHITE)
    txt(p, 40, 455, "1. High Throughput & Zero Loss: The decoupled queue architecture sustains 400 samples/s with zero dropped packets and p95 latency under 26 ms.", fs=9.5, fn="helv", color=C("93c5fd"))
    txt(p, 40, 470, "2. Alert Reliability: Hysteresis evaluation accurately isolates sustained congestion from transient noise, resolving automatically post-recovery.", fs=9.5, fn="helv", color=C("93c5fd"))

# =============================================================================
# SLIDE 6: Summary & Conclusion
# =============================================================================
def slide6(doc):
    p = doc.new_page(width=W, height=H)
    rr(p, 0, 0, W, H, NAVY)
    rr(p, 0, 0, W, 6, RED)

    txt(p, 36, 68, "Summary & Conclusions", fs=24, fn="hebo", color=WHITE)
    line(p, 36, 76, 440, 76, RED, 2.5)

    concs = [
        ("Delivered Pipeline:",
         "A modular network telemetry framework implementing RFC 9232 principles to collect, transport, store, and visualize performance metrics in real time."),
        ("High-Speed Streaming:",
         "Replaces legacy SNMP pull polling with lightweight gRPC HTTP/2 push streaming using compact Protocol Buffers (~72 bytes/sample)."),
        ("Empirically Validated:",
         "Validated through 30 automated Pytest tests, 400-device scalability benchmarking, and scripted fault-injection scenarios confirming zero data drops."),
        ("Scope & System Boundaries:",
         "Implemented as an educational prototype using physical laptop OS metrics (psutil) and simulated enterprise switches/routers without proprietary ASIC hardware."),
    ]
    sy = 96
    for title, desc in concs:
        p.draw_circle(pymupdf.Point(44, sy - 3.5), 2.5, color=RED, fill=RED)
        txt(p, 54, sy, title, fs=11.5, fn="hebo", color=C("fca5a5"))
        r = pymupdf.Rect(54, sy + 3, 440, sy + 45)
        p.insert_textbox(r, desc, fontsize=9.5, fontname="helv", color=C("cbd5e1"), lineheight=1.25)
        sy += 48

    txt(p, 36, 305, "Future Work:", fs=13, fn="hebo", color=C("7dd3fc"))
    futures = [
        "- Integration with physical network switching hardware (Cisco / Juniper)",
        "- Standard gNMI (gRPC Network Management Interface) schema support",
        "- Mutual TLS (mTLS) transport encryption and token authentication",
        "- Scalable time-series storage backend (TimescaleDB / InfluxDB)",
    ]
    fy = 328
    for f in futures:
        txt(p, 54, fy, f, fs=10, fn="helv", color=C("94a3b8"))
        fy += 22

    rr(p, 36, 425, 410, 52, C("0f2a52"), border=C("1e3a6e"))
    txt(p, 48, 445, "Core Architectural Contribution:", fs=10.5, fn="hebo", color=C("fca5a5"))
    txt(p, 48, 463, "Demonstrates high-resolution, sub-second network observability via push streaming.",
        fs=10, fn="helv", color=C("cbd5e1"))

    line(p, 480, 50, 480, H - 30, C("1e3a5f"), 1.5)

    txt(p, 515, 75, "Thank You!", fs=38, fn="hebo", color=WHITE)
    line(p, 515, 86, 900, 86, RED, 2.5)

    txt(p, 515, 115, "Questions & Discussion", fs=14, fn="helv", color=C("93c5fd"))

    rr(p, 515, 145, 445, 85, C("0f2a52"), border=C("1e3a6e"))
    txt(p, 530, 168, "Project Code & Reproducibility", fs=11.5, fn="hebo", color=C("7dd3fc"))
    txt(p, 530, 188, "https://github.com/Rajkamal065/network-telemetry", fs=11, fn="helv", color=WHITE)
    txt(p, 530, 210, "Automated Test Suite:  python -m pytest tests/ -v  (30/30 passed)", fs=10, fn="helv", color=C("4ade80"))

    txt(p, 515, 258, "Team T018  |  CS331 Computer Networks", fs=11.5, fn="hebo", color=C("94a3b8"))
    members = [
        ("Avinash Reddy",          "23110123"),
        ("Gella Jayarama Krishna", "23110115"),
        ("Sowpati Raj Kamal",      "23110319"),
        ("Jangam Sanjay",          "23110144"),
        ("Pulakurthi Manohar",     "23110259"),
        ("Yalla Sai Teja",         "23110366"),
    ]
    my = 282
    for i, (name, roll) in enumerate(members):
        col2 = i % 2
        row2 = i // 2
        mx2 = 515 + col2 * 225
        my2 = my + row2 * 36
        txt(p, mx2, my2, name, fs=11, fn="hebo", color=WHITE)
        txt(p, mx2, my2 + 15, roll, fs=9.5, fn="helv", color=C("7dd3fc"))

    txt(p, 515, H - 28, "Department of Computer Science & Engineering",
        fs=9.5, fn="helv", color=C("64748b"))

# =============================================================================
# Main
# =============================================================================
def build():
    doc = pymupdf.open()
    slide1(doc)
    slide2(doc)
    slide3(doc)
    slide4(doc)
    slide5(doc)
    slide6(doc)

    out_file = "Network_Telemetry_Presentation.pdf"
    doc.save(out_file)
    doc.close()
    print(f"Successfully generated {out_file} with exactly 6 submittable slides!")

if __name__ == '__main__':
    build()
