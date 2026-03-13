import sqlite3
import csv
import json
import os
import networkx as nx
import matplotlib.pyplot as plt
from openpyxl import Workbook

class Exporter:
    def __init__(self, db_path="rs_omni_extractor.db"):
        self.db_path = db_path
    
    def generar_grafo(self, target_id, output_path):
        """Generate a visual OSINT relationship graph."""
        with sqlite3.connect(self.db_path) as conn:
            target_data = conn.execute("SELECT input_raw FROM targets WHERE id=?", (target_id,)).fetchone()
            if not target_data: return
            target = target_data[0]
            
            results = conn.execute("SELECT campo, valor FROM results WHERE target_id=?", (target_id,)).fetchall()
            
            G = nx.DiGraph()
            G.add_node(target, label=target, type="root")
            
            # Group by type to limit nodes if too many
            for r_type, r_val in results:
                node_id = f"{r_type}:{r_val}"
                G.add_node(node_id, label=r_val, type=r_type)
                G.add_edge(target, node_id, label=r_type)

            plt.figure(figsize=(12, 8))
            pos = nx.spring_layout(G)
            
            # Draw nodes with colors based on type
            node_colors = []
            for node, data in G.nodes(data=True):
                if data.get('type') == 'root': node_colors.append('red')
                elif 'Emails' in str(data.get('type')): node_colors.append('skyblue')
                elif 'SUBDOMAIN' in str(data.get('type')): node_colors.append('lightgreen')
                else: node_colors.append('orange')
            
            nx.draw(G, pos, with_labels=False, node_color=node_colors, node_size=1500, alpha=0.8)
            
            # Add labels
            labels = nx.get_node_attributes(G, 'label')
            nx.draw_networkx_labels(G, pos, labels, font_size=8)
            
            plt.title(f"OSINT Graph for {target}")
            plt.savefig(output_path)
            plt.close()

    def a_csv(self, target_id, output_path):
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT campo, valor, fuente FROM results WHERE target_id=?",
                (target_id,)
            ).fetchall()
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["campo", "valor", "fuente"])
                writer.writerows(rows)
    
    def a_json(self, target_id, output_path):
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT campo, valor, fuente, confianza FROM results WHERE target_id=?",
                (target_id,)
            ).fetchall()
            data = [{"campo": r[0], "valor": r[1], "fuente": r[2], "confianza": r[3]} for r in rows]
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
    
    def a_excel(self, target_id, output_path):
        wb = Workbook()
        ws = wb.active
        ws.append(["Campo", "Valor", "Fuente", "Confianza"])
        with sqlite3.connect(self.db_path) as conn:
            for row in conn.execute(
                "SELECT campo, valor, fuente, confianza FROM results WHERE target_id=?",
                (target_id,)
            ):
                ws.append(list(row))
        wb.save(output_path)

    def generar_reporte_texto(self, target_id, output_path):
        """Generate an executive OSINT summary report."""
        with sqlite3.connect(self.db_path) as conn:
            # Get target info
            target = conn.execute("SELECT input_raw, fecha, tipo FROM targets WHERE id=?", (target_id,)).fetchone()
            if not target: return
            
            # Get results grouped by type
            results = conn.execute("SELECT campo, valor FROM results WHERE target_id=?", (target_id,)).fetchall()
            
            report = []
            report.append(f"TARGET: {target[0]}")
            report.append(f"FECHA: {target[1]}")
            report.append("─" * 40)
            
            # Infrastructure section
            infra_types = ['DNS_A', 'DNS_MX', 'DNS_TXT', 'SUBDOMAIN', 'IP Addresses']
            report.append("INFRAESTRUCTURA")
            for r_type, r_val in results:
                if r_type in infra_types:
                    report.append(f"  {r_type.replace('DNS_', '')}: {r_val}")
            
            # Technologies
            tech_types = ['TECH_SERVER', 'TECH_PLATFORM', 'TECH_GENERATOR', 'TECH_CMS']
            techs = [f"{r_type.replace('TECH_', '')}: {r_val}" for r_type, r_val in results if r_type in tech_types]
            if techs:
                report.append(f"  Tech: {', '.join(techs)}")
            
            report.append("")
            
            # Contacts
            report.append("CONTACTOS ENCONTRADOS")
            contacts = [r_val for r_type, r_val in results if r_type == 'Emails']
            for contact in contacts:
                report.append(f"  {contact} (confianza: alta)")
            
            report.append("")
            
            # Exposure/Warnings (Simulated logic for now)
            report.append("EXPOSICIÓN")
            for r_type, r_val in results:
                if r_type == 'SUBDOMAIN' and ('dev' in r_val or 'test' in r_val or 'staging' in r_val):
                    report.append(f"  ⚠️  Subdominio sensible detectado: {r_val}")
            
            report.append("─" * 40)
            report.append(f"DATOS CRUDOS: {len(results)} registros en DB")
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(report))

