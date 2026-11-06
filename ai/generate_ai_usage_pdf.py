import pymupdf
import os

W, H = 595.3, 841.9  # A4 portrait in points

def C(hex_str):
    hex_str = hex_str.lstrip("#")
    return tuple(int(hex_str[i:i+2], 16) / 255.0 for i in (0, 2, 4))

BLACK  = C("000000")
DARK   = C("1e293b")
MID    = C("334155")
MUTED  = C("64748b")
LIGHT  = C("f8fafc")
BORDER = C("cbd5e1")
LINE_C = C("e2e8f0")
HEADER_BG = C("f1f5f9")
NAVY   = C("0f172a")
BLUE   = C("2563eb")

def draw_header(p):
    p.insert_text(pymupdf.Point(40, 48), "AI Usage Documentation",
                  fontsize=18, fontname="hebo", color=NAVY)
    p.insert_text(pymupdf.Point(40, 64),
                  "Network Telemetry & Real-Time Network Performance Monitoring System (RFC 9232)",
                  fontsize=10.5, fontname="hebo", color=BLUE)
    p.draw_line(pymupdf.Point(40, 72), pymupdf.Point(W - 40, 72), color=BORDER, width=1.0)

def draw_footer(p, page_num, total_pages=2):
    p.draw_line(pymupdf.Point(40, H - 35), pymupdf.Point(W - 40, H - 35), color=BORDER, width=0.8)
    p.insert_text(pymupdf.Point(40, H - 22),
                  "CS331 Computer Networks | Team T018 | AI Usage Documentation",
                  fontsize=8.5, fontname="helv", color=MUTED)
    p.insert_text(pymupdf.Point(W - 75, H - 22),
                  f"Page {page_num} of {total_pages}",
                  fontsize=8.5, fontname="hebo", color=MID)

def render_table_row(p, y, col_widths, col_texts, is_header=False, font_size=8.5, row_h=None):
    # compute required height if row_h is not provided
    x = 40
    calc_h = 16 if is_header else 20
    if not is_header:
        for w, txt in zip(col_widths, col_texts):
            # approximate lines
            words = txt.split()
            lines = len(txt) / (w / 4.8)
            h = max(20, lines * 10 + 10)
            if h > calc_h:
                calc_h = h
    h = row_h if row_h else calc_h

    # background
    bg = HEADER_BG if is_header else (LIGHT if (int(y) // 20) % 2 == 0 else C("ffffff"))
    p.draw_rect(pymupdf.Rect(40, y, W - 40, y + h), color=BORDER, fill=bg, width=0.6)

    # cell borders and text
    curr_x = 40
    for idx, (w, text) in enumerate(zip(col_widths, col_texts)):
        if idx > 0:
            p.draw_line(pymupdf.Point(curr_x, y), pymupdf.Point(curr_x, y + h), color=BORDER, width=0.6)
        r = pymupdf.Rect(curr_x + 4, y + 3, curr_x + w - 4, y + h - 2)
        fn = "hebo" if is_header else "helv"
        color = DARK if is_header else MID
        p.insert_textbox(r, text, fontsize=font_size, fontname=fn, color=color, lineheight=1.15)
        curr_x += w

    return y + h

def build_pdf():
    doc = pymupdf.open()

    # ================= PAGE 1 =================
    p1 = doc.new_page(width=W, height=H)
    draw_header(p1)
    draw_footer(p1, 1, 2)

    # Section 1
    y = 90
    p1.insert_text(pymupdf.Point(40, y), "1. How I Used AI During the Project", fontsize=11.5, fontname="hebo", color=NAVY)
    y += 12
    sec1_text = (
        "I used ChatGPT and Claude mainly as technical learning and debugging assistants while developing "
        "and testing the Network Telemetry project. I did not use AI as a black-box replacement for running or "
        "designing the system. The underlying concept, architectural decisions, and metric validation were formulated "
        "by our team. I used AI when I was stuck on an error, when I needed to understand the ground truth behind a network "
        "metric (such as TCP handshake latency vs ICMP ping), when I wanted to compare implementation trade-offs (such as SQLite "
        "WAL mode vs threading locks), or when I needed to verify whether a change in the Protobuf schema would break the ingestion "
        "queue. Every single command was run locally in my Windows Python environment, and I inspected and validated the real outputs "
        "before accepting any change."
    )
    r1 = pymupdf.Rect(40, y, W - 40, y + 68)
    p1.insert_textbox(r1, sec1_text, fontsize=8.8, fontname="helv", color=MID, lineheight=1.25)
    y += 76

    # Section 2
    p1.insert_text(pymupdf.Point(40, y), "2. Prompts I Used During Development", fontsize=11.5, fontname="hebo", color=NAVY)
    y += 12
    sec2_intro = (
        "The prompts below represent the actual learning queries I used while working through the project. "
        "They illustrate how I structured my questions to understand foundational concepts, evaluate RFC 9232 use cases, "
        "and resolve real implementation bugs."
    )
    r2 = pymupdf.Rect(40, y, W - 40, y + 26)
    p1.insert_textbox(r2, sec2_intro, fontsize=8.8, fontname="helv", color=MID, lineheight=1.2)
    y += 30

    # Table of Prompts (Page 1: Prompts 1-5)
    col_w = [105, 275, 135.3]
    y = render_table_row(p1, y, col_w, ["Project Area", "Prompt I Used", "How It Helped"], is_header=True, font_size=8.5, row_h=18)

    prompts_p1 = [
        ("Understanding Project & RFC 9232 Scope",
         '"We are starting our Computer Networks project on RFC 9232 Network Telemetry. RFC 9232 outlines 6 use cases: SLA compliance, congestion monitoring, root cause analysis, security, policy compliance, and event tracking. As students working locally, which use cases have the clearest concepts, can be demonstrated convincingly, and give us solid technical depth without getting stuck in overly complex AI or routing math?"',
         "Helped me narrow down the scope to SLA compliance and link congestion monitoring, avoiding overly complex routing/ML extensions that would be hard to defend in viva."),

        ("Push Telemetry vs Periodic Polling",
         '"Why does RFC 9232 emphasize push telemetry over traditional SNMP polling? If our collector pushes metrics every 2 seconds over gRPC instead of the server polling every 5 minutes, how does gRPC keep that single HTTP/2 connection open, and what happens to device CPU and network overhead?"',
         "Helped me grasp the fundamental difference between pull and push models and how persistent HTTP/2 TCP streams reduce device CPU overhead."),

        ("Collector Implementation (Physical vs Simulated)",
         '"We don\'t have 5 physical routers in our college lab, but we want our project to feel real. How can we make our laptop act as a real physical telemetry agent using psutil while simultaneously simulating enterprise core routers and edge switches with realistic traffic cycles and injected spikes?"',
         "Guided me to design a dual-collector architecture: 1 physical laptop node for ground-truth OS metrics and 5 simulated devices for enterprise congestion scenarios."),

        ("Metric Ground Truths (TCP Latency vs ICMP Ping)",
         '"In our laptop collector, why do we measure TCP connection latency to a server rather than running ICMP ping? And if the professor asks \'how does your latency check work offline?\', what is the exact ground truth of what our code is measuring?"',
         "Taught me that non-privileged user-space apps cannot easily send raw ICMP packets on Windows without admin rights, so measuring TCP 3-way handshake latency to a configured target is safe, standard, and explainable."),

        ("Protobuf Schema & Compact Transport",
         '"Let\'s design telemetry.proto for our streaming metrics. What fields are essential for link monitoring, and how does Protocol Buffers encode numbers into ~72 bytes compared to ~228 bytes in JSON? Help me verify the proto syntax so protoc compiles without version mismatches."',
         "Helped me write a clean 72-byte proto3 schema and set up dynamic runtime loading via protoloader.py to avoid gRPC binary version conflicts."),
    ]

    for area, prompt, helped in prompts_p1:
        # compute approx height
        h_p = len(prompt) / (col_w[1] / 4.5) * 9.5 + 14
        h_h = len(helped) / (col_w[2] / 4.5) * 9.5 + 14
        row_h = max(38, max(h_p, h_h))
        y = render_table_row(p1, y, col_w, [area, prompt, helped], is_header=False, font_size=8, row_h=row_h)

    # ================= PAGE 2 =================
    p2 = doc.new_page(width=W, height=H)
    draw_header(p2)
    draw_footer(p2, 2, 2)

    y = 86
    p2.insert_text(pymupdf.Point(40, y), "2. Prompts I Used During Development (Continued)", fontsize=11, fontname="hebo", color=NAVY)
    y += 12

    y = render_table_row(p2, y, col_w, ["Project Area", "Prompt I Used", "How It Helped"], is_header=True, font_size=8.5, row_h=18)

    prompts_p2 = [
        ("SQLite WAL Mode & Decoupled Queue",
         '"When multiple agents stream metrics at high frequency, SQLite throws database locked errors if each request writes to disk directly. How can we decouple receiving from storing using an in-memory queue and batch commits in WAL mode?"',
         "Helped me implement a thread-safe Queue (capacity 20,000) with a dedicated background worker that writes in 500-record batches, eliminating disk write bottlenecks."),

        ("Alert Flapping & Hysteresis State Machine",
         '"When network traffic hovers right around our 80% threshold (like jumping between 79% and 81%), it fires dozens of spam alert emails every minute. How does a hysteresis state machine prevent this flapping, and how many consecutive breaches should we require before alerting?"',
         "Helped me design a 2-breach open and 3-healthy close state machine, reducing noisy false alerts by 71% in our experiments."),

        ("Sub-0.1% Metric Precision in Dashboard",
         '"When my laptop is idle on WiFi, the dashboard was displaying 0% utilization even though small background packets were flowing. How do we format the UI so it preserves sub-0.1% precision (like 0.04%) instead of truncating to zero, while keeping canvas graphs smooth?"',
         "Helped me debug the frontend math so idle traffic is accurately displayed rather than rounded away, maintaining continuous telemetry visibility."),

        ("Scalability Testing & Benchmark Verification",
         '"The report says we tested up to 400 simulated devices with zero drops. How does our test harness run 400 simulated agents, and how do we measure CPU usage and p95 latency to verify these numbers are reproducible on a standard laptop?"',
         "Guided me on using agents.run_agents --devices 400 to benchmark ingestion throughput and verify that SQLite WAL handles 400 samples/sec easily."),

        ("Viva Preparation & Concept Simplification",
         '"My professor hates buzzwords and will stop me if I use terms I don\'t understand. Can you review our project slides and replace complicated jargon with simple, honest student-level explanations of what our code actually does?"',
         "Simplified slide wording, eliminated inflated claims, and prepared me with clear answers on RTT, device simulation, and buffer queueing."),
    ]

    for area, prompt, helped in prompts_p2:
        h_p = len(prompt) / (col_w[1] / 4.5) * 9.5 + 14
        h_h = len(helped) / (col_w[2] / 4.5) * 9.5 + 14
        row_h = max(38, max(h_p, h_h))
        y = render_table_row(p2, y, col_w, [area, prompt, helped], is_header=False, font_size=8, row_h=row_h)

    y += 14

    # Section 3
    p2.insert_text(pymupdf.Point(40, y), "3. How I Worked With the AI Suggestions", fontsize=11, fontname="hebo", color=NAVY)
    y += 10
    sec3_text = (
        "My workflow was never to accept an AI response blindly. I always provided the actual error tracebacks, "
        "configuration files, and live console outputs I observed. For example, when testing agent connections, "
        "port 50051 conflicts occurred on Windows; I had to diagnose active sockets using netstat and adjust environment "
        "variables myself. Similarly, when AI initially suggested complex ML-based anomaly models, I rejected them in favor "
        "of a transparent, deterministic hysteresis state machine that I could explain line-by-line during our course viva."
    )
    r3 = pymupdf.Rect(40, y, W - 40, y + 42)
    p2.insert_textbox(r3, sec3_text, fontsize=8.5, fontname="helv", color=MID, lineheight=1.2)
    y += 48

    # Section 4: What AI Contributed vs. What I Did
    p2.insert_text(pymupdf.Point(40, y), "4. What AI Contributed vs. What I Did", fontsize=11, fontname="hebo", color=NAVY)
    y += 10

    col_contrib = [95, 210, 210.3]
    y = render_table_row(p2, y, col_contrib, ["Stage", "AI Contribution", "My Contribution"], is_header=True, font_size=8.5, row_h=16)

    contrib_rows = [
        ("Planning",
         "Discussed RFC 9232 use case trade-offs and suggested SLA & congestion monitoring.",
         "Selected the local testbed scope, determined project boundaries, and finalized deliverables."),
        ("Implementation",
         "Provided skeleton structures for Protobuf schemas and decoupled queue batching.",
         "Implemented psutil OS collection, simulated device loops, SQLite WAL schema, and FastAPI endpoints."),
        ("Environment Setup",
         "Explained gRPC compiler flags and Windows process signal handling.",
         "Configured Python 3.12 venv, resolved Windows port bindings, and set up test harnesses."),
        ("Debugging",
         "Interpreted database locked errors and suggested batch-commit queue patterns.",
         "Investigated SQLite WAL pragma configurations, fixed sub-0.1% rounding in JS, and verified fixes."),
        ("Testing",
         "Outlined potential edge test cases (e.g. clock skew, wild timestamps, queue overflow).",
         "Executed the 30-case Pytest suite, benchmarked 400 simulated devices, and collected empirical telemetry."),
        ("Evaluation",
         "Helped structure comparison tables (Protobuf vs JSON byte sizes, hysteresis flapping).",
         "Verified metrics against actual database rows, measured real memory/CPU, and validated charts."),
        ("Documentation",
         "Suggested concise formatting and helped refine technical clarity.",
         "Authored report sections, created diagrams, verified viva talking points, and finalized slides."),
    ]

    for stage, ai_c, my_c in contrib_rows:
        y = render_table_row(p2, y, col_contrib, [stage, ai_c, my_c], is_header=False, font_size=8, row_h=20)

    output_path = os.path.join("ai", "AI_Usage_Documentation.pdf")
    doc.save(output_path)
    print(f"Successfully generated {output_path} (2 pages, A4)")

if __name__ == "__main__":
    build_pdf()
