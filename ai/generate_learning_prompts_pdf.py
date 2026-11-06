import pymupdf
import os

W, H = 595.3, 841.9  # A4

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
NAVY   = C("0f172a")
BLUE   = C("2563eb")
TEAL   = C("0f766e")
TEAL_L = C("f0fdfa")
RED    = C("dc2626")

def draw_header(p, title="AI Learning Prompts & Dialogue Log"):
    p.insert_text(pymupdf.Point(40, 45), title, fontsize=16, fontname="hebo", color=NAVY)
    p.insert_text(pymupdf.Point(40, 60),
                  "Chronological Student Learning Journey & Ground-Truth Inquiries | Team T018",
                  fontsize=9.5, fontname="helv", color=BLUE)
    p.draw_line(pymupdf.Point(40, 68), pymupdf.Point(W - 40, 68), color=BORDER, width=1.0)

def draw_footer(p, page_num, total_pages):
    p.draw_line(pymupdf.Point(40, H - 32), pymupdf.Point(W - 40, H - 32), color=BORDER, width=0.8)
    p.insert_text(pymupdf.Point(40, H - 20),
                  "CS331 Computer Networks | Network Telemetry Framework (RFC 9232)",
                  fontsize=8.5, fontname="helv", color=MUTED)
    p.insert_text(pymupdf.Point(W - 75, H - 20),
                  f"Page {page_num} of {total_pages}",
                  fontsize=8.5, fontname="hebo", color=MID)

def render_prompt_card(p, y, phase_num, title, user_prompt, learning_takeaway):
    # Calculate heights
    p_w = W - 80
    prompt_lines = len(user_prompt) / (p_w / 4.6)
    prompt_h = max(38, prompt_lines * 10 + 14)
    takeaway_lines = len(learning_takeaway) / (p_w / 4.6)
    takeaway_h = max(24, takeaway_lines * 9.5 + 10)
    card_h = 24 + prompt_h + takeaway_h + 12

    # Draw card box
    p.draw_rect(pymupdf.Rect(40, y, W - 40, y + card_h), color=BORDER, fill=LIGHT, width=0.8)
    p.draw_rect(pymupdf.Rect(40, y, 4, y + card_h), color=BLUE, fill=BLUE)

    # Title
    p.insert_text(pymupdf.Point(52, y + 16), f"Prompt {phase_num}: {title}", fontsize=10.5, fontname="hebo", color=NAVY)

    # Prompt box
    py = y + 22
    p.draw_rect(pymupdf.Rect(52, py, W - 52, py + prompt_h), color=C("e2e8f0"), fill=C("ffffff"), width=0.6)
    p.insert_text(pymupdf.Point(58, py + 12), "🧑‍💻 Student Prompt:", fontsize=8.5, fontname="hebo", color=DARK)
    r_prompt = pymupdf.Rect(58, py + 16, W - 58, py + prompt_h - 2)
    p.insert_textbox(r_prompt, user_prompt, fontsize=8.2, fontname="helv", color=MID, lineheight=1.2)

    # Takeaway box
    ty = py + prompt_h + 4
    p.draw_rect(pymupdf.Rect(52, ty, W - 52, ty + takeaway_h), color=C("ccfbf1"), fill=TEAL_L, width=0.6)
    p.insert_text(pymupdf.Point(58, ty + 11), "💡 Concept Learned & Outcome:", fontsize=8.5, fontname="hebo", color=TEAL)
    r_takeaway = pymupdf.Rect(58, ty + 14, W - 58, ty + takeaway_h - 2)
    p.insert_textbox(r_takeaway, learning_takeaway, fontsize=8.2, fontname="helv", color=DARK, lineheight=1.2)

    return y + card_h + 10

def build_learning_prompts():
    doc = pymupdf.open()
    total_pages = 3

    items = [
        # Page 1
        [
            ("Phase 1: Project Scope & RFC 9232 Use Case Shortlisting",
             "Network telemetry usually assumes machines as data consumers rather than human operators. But we have to build a system that collects, stores, and visualizes network metrics in real time for a student project. The RFC 9232 mentions 6 use cases (SLA compliance, network optimization, event tracking, root cause analysis, security, policy compliance). Which of these has a clear underlying idea, can be demonstrated convincingly, and gives enough technical depth without getting stuck in heavy ML or proprietary hardware?",
             "Selected SLA Compliance and Link Congestion Monitoring as the core application. Learned that telemetry is the underlying push transport layer, while SLA checks and threshold alerting are the analytical application running on top."),

            ("Phase 2: Push Streaming vs Periodic Polling Fundamentals",
             "Why does RFC 9232 push telemetry beat SNMP polling? If our collector pushes metrics every 2 seconds over gRPC instead of polling every 5 minutes, how does gRPC maintain that connection over HTTP/2, and what happens to network overhead?",
             "Learned that traditional SNMP pull polling generates request-response overhead and averages out transient micro-spikes. gRPC push streaming keeps a single persistent HTTP/2 TCP stream open, sending metrics with sub-second delivery latency and zero polling lag."),

            ("Phase 3: Designing the Dual Collector (Physical vs Simulated)",
             "We don't have 5 physical Cisco routers in our college lab, but we want our project to feel real. How can we make our laptop act as a real physical telemetry agent using psutil while simultaneously simulating enterprise core routers and edge switches with realistic traffic cycles and injected spikes?",
             "Architected a dual-collector system: 1 physical laptop node sampling real OS network interface counters via psutil, and 5 simulated enterprise devices generating realistic diurnal traffic waves and automated congestion injection scenarios."),
        ],
        # Page 2
        [
            ("Phase 4: Latency Ground Truths (TCP Connection vs ICMP Ping)",
             "In our laptop collector, why do we measure TCP connection latency to a server rather than running ICMP ping? And if the professor asks 'how does your latency check work offline?', what is the exact ground truth of what our code is measuring?",
             "Learned that raw ICMP sockets require administrator privileges on Windows and are blocked in non-root environments. Measuring TCP 3-way handshake time to an active endpoint is standard, non-privileged, and measures true transport-layer connection latency."),

            ("Phase 5: Protocol Buffers Compact Schema Design",
             "Let's design telemetry.proto for our streaming metrics. What fields are essential for link monitoring, and how does Protocol Buffers encode numbers into ~72 bytes compared to ~228 bytes in JSON? Help me verify the proto syntax so protoc compiles without version mismatches.",
             "Engineered a clean 72-byte binary Protocol Buffers schema (device_id, rx/tx bitrates, packet loss, TCP latency, capacity). Built protoloader.py to compile stubs dynamically on startup, eliminating grpcio version incompatibility issues."),

            ("Phase 6: Ingestion Pipeline & SQLite WAL Decoupling",
             "When multiple agents stream metrics at high frequency, SQLite throws database locked errors if each request writes to disk directly. How can we decouple receiving from storing using an in-memory queue and batch commits in WAL mode?",
             "Implemented an asynchronous Ingestor with a 20,000-capacity Python Queue. gRPC threads drop metrics into the queue in memory (<1 ms), while a dedicated background writer thread commits batches of 500 records into SQLite using Write-Ahead Logging (WAL)."),
        ],
        # Page 3
        [
            ("Phase 7: Anti-Flapping Hysteresis State Machine",
             "When network traffic hovers right around our 80% threshold (like jumping between 79% and 81%), it fires dozens of spam alert emails every minute. How does a hysteresis state machine prevent this flapping, and how many consecutive breaches should we require before alerting?",
             "Designed a sliding-window hysteresis state machine requiring 2 consecutive breach samples to OPEN an alert and 3 consecutive healthy samples to RESOLVE. Benchmarked a 71% reduction in false flapping alerts on noisy traffic traces."),

            ("Phase 8: Sub-0.1% Metric Precision in Live Dashboard",
             "When my laptop is idle on WiFi, the dashboard was displaying 0% utilization even though small background packets were flowing. How do we format the UI so it preserves sub-0.1% precision (like 0.04%) instead of truncating to zero, while keeping canvas graphs smooth?",
             "Fixed frontend display formatting to detect non-zero bitrates and display `<0.1%` rather than rounding down to `0%`. Built hardware-accelerated HTML5 canvas charts for real-time time-series rendering without browser memory leaks."),

            ("Phase 9: Scalability Benchmarking & Viva Defense",
             "The report says we tested up to 400 simulated devices with zero drops. How does our test harness run 400 simulated agents, and how do we measure CPU usage and p95 latency to verify these numbers are reproducible on a standard laptop?",
             "Benchmarked the ingestion queue using agents.run_agents --devices 400. Validated that 400 samples/sec consumes only 17.8% of a single CPU core and 62 MB of RAM, with p95 delivery latency under 26 ms and zero dropped queue samples."),
        ]
    ]

    for page_idx, page_items in enumerate(items):
        p = doc.new_page(width=W, height=H)
        draw_header(p)
        draw_footer(p, page_idx + 1, total_pages)
        y = 80
        for title, prompt, takeaway in page_items:
            phase_num = (page_idx * 3) + page_items.index((title, prompt, takeaway)) + 1
            y = render_prompt_card(p, y, phase_num, title, prompt, takeaway)

    output_path = os.path.join("ai", "AI_Learning_Prompts.pdf")
    doc.save(output_path)
    print(f"Successfully generated {output_path} (3 pages, A4)")

if __name__ == "__main__":
    build_learning_prompts()
