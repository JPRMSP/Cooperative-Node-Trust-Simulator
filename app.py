import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
import random
import time
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime

# Streamlit setup
st.set_page_config(page_title="CNT-Sim++", layout="wide")

st.title("🛰️ Cooperative Node Trust Simulator ++ (CNT-Sim++)")
st.markdown("#### Real-time Detection of Selfish & Malicious Nodes in Ad-Hoc Networks with PDF Reporting")

# Sidebar
num_nodes = st.sidebar.slider("Number of Nodes", 5, 20, 10)
speed = st.sidebar.slider("Simulation Speed (seconds per step)", 0.2, 2.0, 1.0)
run_sim = st.sidebar.button("Start Simulation")

# Initialize graph and parameters
G = nx.erdos_renyi_graph(num_nodes, 0.4)
roles = {}
trust_scores = {}
energy = {}
packets_sent = {}
packets_received = {}
packets_dropped = {}

for node in G.nodes:
    roles[node] = random.choice(["Honest", "Selfish", "Malicious"])
    trust_scores[node] = 1.0
    energy[node] = 100.0
    packets_sent[node] = 0
    packets_received[node] = 0
    packets_dropped[node] = 0

placeholder = st.empty()

def update_trust_energy(sender, success):
    if success:
        trust_scores[sender] = min(1.0, trust_scores[sender] + 0.05)
    else:
        trust_scores[sender] = max(0.0, trust_scores[sender] - 0.1)
    energy[sender] = max(0.0, energy[sender] - random.uniform(0.5, 2.0))

def simulate_step():
    sender = random.choice(list(G.nodes))
    neighbors = list(G.neighbors(sender))
    if not neighbors:
        return
    receiver = random.choice(neighbors)
    behavior = roles[sender]

    if behavior == "Honest":
        success = True
    elif behavior == "Selfish":
        success = random.random() > 0.4
    else:
        success = random.random() > 0.8

    packets_sent[sender] += 1
    if success:
        packets_received[receiver] += 1
    else:
        packets_dropped[sender] += 1

    update_trust_energy(sender, success)
    return sender, receiver, success

def get_node_color(node):
    t = trust_scores[node]
    if t > 0.75:
        return "#00b300"
    elif t > 0.5:
        return "#ffaa00"
    elif t > 0.25:
        return "#ff6600"
    else:
        return "#ff0000"

# PDF report generator
def generate_pdf_report():
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"CNT_Sim_Report_{timestamp}.pdf"
    pdf = canvas.Canvas(filename, pagesize=A4)
    width, height = A4

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(150, height - 60, "Cooperative Node Trust Simulator ++ Report")

    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, height - 100, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    pdf.drawString(50, height - 120, f"Total Nodes: {len(G.nodes)}")

    y = height - 160
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y, "Node | Role | Trust | Energy | Sent | Received | Dropped")
    pdf.setFont("Helvetica", 11)
    y -= 20
    for n in G.nodes:
        pdf.drawString(50, y, f"{n:<4} | {roles[n]:<9} | {trust_scores[n]:.2f} | {energy[n]:.1f}% | {packets_sent[n]} | {packets_received[n]} | {packets_dropped[n]}")
        y -= 15
        if y < 100:
            pdf.showPage()
            y = height - 100

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y - 20, "Summary:")
    pdf.setFont("Helvetica", 11)
    y -= 40
    detected = [n for n, t in trust_scores.items() if t < 0.4]
    pdf.drawString(50, y, f"Detected Suspicious Nodes: {detected if detected else 'None'}")
    y -= 20
    pdf.drawString(50, y, f"Total Packets Sent: {sum(packets_sent.values())}")
    y -= 20
    pdf.drawString(50, y, f"Total Packets Received: {sum(packets_received.values())}")
    y -= 20
    pdf.drawString(50, y, f"Total Packets Dropped: {sum(packets_dropped.values())}")
    pdf.save()
    return filename

# Simulation and visualization
if run_sim:
    st.sidebar.success("Simulation Running...")
    for step in range(50):
        result = simulate_step()
        if not result:
            continue
        sender, receiver, success = result

        fig, ax = plt.subplots(figsize=(6, 4))
        pos = nx.spring_layout(G, seed=42)

        nx.draw(G, pos, with_labels=True,
                node_color=[get_node_color(n) for n in G.nodes],
                node_size=[energy[n]*6 for n in G.nodes],
                font_color="white", ax=ax)

        edge_color = "lime" if success else "red"
        nx.draw_networkx_edges(G, pos, edgelist=[(sender, receiver)],
                               width=3, edge_color=edge_color,
                               arrows=True, arrowsize=20, connectionstyle="arc3,rad=0.1")

        ax.set_title(f"Step {step+1}: Node {sender} → Node {receiver} ({'Success' if success else 'Failed'})")

        with placeholder.container():
            col1, col2, col3 = st.columns([2.5, 1.2, 1])
            with col1:
                st.pyplot(fig)
            with col2:
                st.subheader("📊 Node Status")
                table_data = []
                for n in G.nodes:
                    table_data.append({
                        "Node": n,
                        "Role": roles[n],
                        "Trust": round(trust_scores[n], 2),
                        "Energy": f"{energy[n]:.1f}%",
                    })
                st.dataframe(table_data, hide_index=True)
            with col3:
                st.subheader("📦 Packet Metrics")
                st.metric("Sent", sum(packets_sent.values()))
                st.metric("Received", sum(packets_received.values()))
                st.metric("Dropped", sum(packets_dropped.values()))
                detected = [n for n, t in trust_scores.items() if t < 0.4]
                if detected:
                    st.error(f"⚠️ Suspicious Nodes: {detected}")
                else:
                    st.success("✅ Network Stable")

        time.sleep(speed)

    st.sidebar.info("Simulation Completed ✅")

    if st.button("📄 Generate PDF Report"):
        pdf_file = generate_pdf_report()
        with open(pdf_file, "rb") as f:
            st.download_button("⬇️ Download PDF Report", data=f, file_name=pdf_file, mime="application/pdf")

else:
    st.info("Click **Start Simulation** to begin real-time trust monitoring.")
