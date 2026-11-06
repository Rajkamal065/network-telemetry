# Project Report

This folder contains the complete, final IEEE 2-column project report for the **Real-Time Network Telemetry Framework** (CS331 Computer Networks, Project 2).

## File Details
- **Report Document**: [`Network_Telemetry_Report.pdf`](./Network_Telemetry_Report.pdf) (9 Pages, PDF format)
- **Title**: *Real-Time Network Telemetry Framework: Collecting, Streaming and Visualizing Bandwidth and Latency*
- **Team**: T018 (Department of Computer Science & Engineering)
- **Authors**:
  - Avinash Reddy (23110123)
  - Gella Jayarama Krishna (23110115)
  - Sowpati Raj Kamal (23110319)
  - Jangam Sanjay (23110144)
  - Pulakurthi Manohar (23110259)
  - Yalla Sai Teja (23110366)

## Sections Covered in Report
1. **Introduction**: Limitations of traditional SNMP pull polling and the motivation for RFC 9232 push telemetry.
2. **System Architecture**: Dual-collector layer (psutil + simulated nodes), HTTP/2 gRPC streaming transport, buffered SQLite ingestion pipeline, hysteresis alerting engine, and REST/Canvas presentation.
3. **Implementation Details**: Protocol Buffers message schemas, multithreaded collector design, WAL database persistence, and FastAPI asynchronous backend.
4. **Experimental Setup & Testbed**: 1 physical host + 5 simulated enterprise routers and switches, parameterized traffic patterns, and scripted congestion injection.
5. **Evaluation & Results**:
   - Experiment E1: Scalability under load (tested up to 400 devices with zero packet drops).
   - Experiment E2: Metric resolution and sub-0.1% bandwidth fidelity.
   - Experiment E3: Congestion detection and hysteresis recovery timing (2.8s mean detection latency).
   - Experiment E4: Storage footprint and downsampling efficiency.
6. **Related Work & RFC 9232 Alignment**: Comparison with SNMP, NetFlow/IPFIX, and standard gNMI.
7. **Conclusion & Future Directions**: Summary of findings and roadmap for physical hardware and mTLS.

