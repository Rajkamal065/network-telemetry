# Presentation Slides

This folder contains the presentation slides for the **Real-Time Network Telemetry Framework** (CS331 Computer Networks, Project 2).

## Slide Files
- **PowerPoint Slides**: [`Network_Telemetry_Presentation.pptx`](./Network_Telemetry_Presentation.pptx) (Microsoft PowerPoint format, 16:9 widescreen)
- **PDF Slides**: [`Network_Telemetry_Presentation.pdf`](./Network_Telemetry_Presentation.pdf) (High-resolution PDF presentation format, 16:9 widescreen)
- **Interactive HTML Slides**: [`presentation_slides.html`](./presentation_slides.html) (Stand-alone browser presentation)

## Slide Outline (6 Slides Total)
1. **Slide 1 - Title Slide**: Project title, subtitle (RFC 9232), course details (CS331), Team ID (T018), and all 6 team members with roll numbers.
2. **Slide 2 - Project Motivation & Technical Approach**: Limitations of legacy periodic SNMP polling, advantages of continuous push telemetry (RFC 9232), target metrics (bandwidth utilization, bitrates, latency, drops), tools & technologies, and key deliverables.
3. **Slide 3 - System Architecture & Functional Pipeline**: Complete end-to-end telemetry architecture diagram from the project report, covering Data Collection, Transport (gRPC/Protobuf), Ingestion & Storage (SQLite WAL), and Alerting & Visualization layers.
4. **Slide 4 - Real-Time Telemetry Dashboard**: Dashboard screenshot and capabilities, KPI cards, interface utilization table, sub-0.1% precision preservation, HTML5 canvas graphs, and CSV data export.
5. **Slide 5 - Experimental Evaluation & Results**: Four highlighted quantitative metrics (400 devices tested with 0 packet drops, 2.8s mean alert time, 71% flapping reduction via hysteresis, 30/30 automated tests passed), plus Experiment E1 (scalability) and E3 (congestion alert recovery) graph figures.
6. **Slide 6 - Summary & Conclusions**: Pipeline summary, high-speed streaming benefits, empirical validation, scope & boundaries, future work roadmap, and thank-you acknowledgments.

## How to Re-generate Slides
If needed, both presentations can be re-compiled using the included Python scripts:
```bash
# Generate PDF slides
python generate_presentation_pdf.py

# Generate PPTX slides
python generate_pptx.py
```
*(Dependencies: `pymupdf`, `python-pptx`, `Pillow`)*
